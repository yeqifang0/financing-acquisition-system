"""企查查 Provider — 已开通接口但免费试用额度可能用完。

认证: Token = MD5(AppKey + Timespan + SecretKey).toUpperCase()
Status:
  200 = 成功
  214 = 接口未购买
  112 = 额度不足/过期
"""
import os
import hashlib
import time
import httpx

from .base import EnterpriseProvider
from ..config import QCC_APP_KEY, QCC_SECRET_KEY, QCC_BASE_URL, has_credentials


class QichachaProvider(EnterpriseProvider):
    name = "qichacha"
    label = "企查查"
    free_tier = "trial"
    note = "20 次免费试用/接口，充值后恢复"

    BASE_URL = QCC_BASE_URL

    def __init__(self):
        self.app_key = os.getenv("QCC_APP_KEY", QCC_APP_KEY)
        self.secret_key = os.getenv("QCC_SECRET_KEY", QCC_SECRET_KEY)
        self._last_call_ts = 0.0

    def _gen_auth(self) -> dict:
        timespan = str(int(time.time()))
        token = hashlib.md5(f"{self.app_key}{timespan}{self.secret_key}".encode()).hexdigest().upper()
        return {"Token": token, "Timespan": timespan}

    def _rate_limit(self):
        elapsed = (time.time() - self._last_call_ts) * 1000
        if elapsed < 300:
            time.sleep((300 - elapsed) / 1000)
        self._last_call_ts = time.time()

    def is_available(self) -> bool:
        return has_credentials()

    def test_connection(self) -> dict:
        if not has_credentials():
            return {"auth_ok": False, "quota_ok": False, "detail": "未配置企查查凭证"}
        try:
            self._rate_limit()
            headers = self._gen_auth()
            resp = httpx.get(
                f"{self.BASE_URL}/FuzzySearch/GetList",
                headers=headers,
                params={"key": self.app_key, "searchKey": "科技", "pageIndex": 1, "pageSize": 5},
                timeout=10,
            )
            data = resp.json()
            status = str(data.get("Status"))
            if status == "200":
                return {"auth_ok": True, "quota_ok": True, "detail": f"正常"}
            if status == "214":
                return {"auth_ok": True, "quota_ok": False, "detail": "接口未开通，请在 openapi.qcc.com 开通"}
            if status == "112":
                return {"auth_ok": True, "quota_ok": False, "detail": "免费额度已用完，请充值或换用其他数据源"}
            return {"auth_ok": True, "quota_ok": False, "detail": f"Status={status}: {data.get('Message')}"}
        except Exception as e:
            return {"auth_ok": False, "quota_ok": False, "detail": str(e)}

    def _fuzzy_search(self, keyword: str, page: int = 1, size: int = 5) -> list[dict]:
        self._rate_limit()
        resp = httpx.get(
            f"{self.BASE_URL}/FuzzySearch/GetList",
            headers=self._gen_auth(),
            params={"key": self.app_key, "searchKey": keyword, "pageIndex": page, "pageSize": size},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if str(data.get("Status")) != "200":
            raise RuntimeError(f"企查查 Status={data.get('Status')}: {data.get('Message')}")
        return data.get("Result") or []

    def _verify(self, search_key: str) -> dict:
        self._rate_limit()
        resp = httpx.get(
            f"{self.BASE_URL}/EnterpriseInfo/Verify",
            headers=self._gen_auth(),
            params={"key": self.app_key, "searchKey": search_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if str(data.get("Status")) != "200":
            raise RuntimeError(f"企查查 Status={data.get('Status')}: {data.get('Message')}")
        return data.get("Result") or {}

    def collect_leads(self, keyword: str, count: int = 20) -> list[dict]:
        if not self.is_available():
            raise RuntimeError("未配置企查查凭证")

        # 检查额度
        test = self.test_connection()
        if test.get("quota_ok") is False:
            raise RuntimeError(test.get("detail", "企查查不可用"))

        raw = []
        pages_needed = (count + 4) // 5
        for page in range(1, pages_needed + 1):
            results = self._fuzzy_search(keyword, page=page)
            if not results:
                break
            raw.extend(results)
            if len(raw) >= count:
                break
        raw = raw[:count]

        leads = []
        for c in raw:
            credit = c.get("CreditCode") or ""
            try:
                detail = self._verify(credit or c.get("Name", ""))
            except Exception:
                detail = {}
            leads.append(self._map(c, detail))
        return leads

    def _map(self, basic: dict, detail: dict) -> dict:
        name = detail.get("Name") or basic.get("Name") or ""
        credit = detail.get("CreditCode") or basic.get("CreditCode") or ""
        contact = detail.get("ContactInfo") or {}
        phone = contact.get("PhoneNumber") or contact.get("Telephone") or ""
        email = contact.get("Email") or ""
        website = contact.get("WebSite") or ""
        geo = detail.get("Geocoding") or {}
        return self.map_to_lead(
            name=name,
            credit_code=credit,
            legal_rep=detail.get("OperName") or basic.get("OperName") or "",
            reg_capital=detail.get("RegCapital") or "",
            paid_capital=detail.get("RealCapital") or "",
            address=detail.get("Address") or basic.get("Address") or "",
            scope=detail.get("Scope") or "",
            establish_date=detail.get("StartDate") or basic.get("StartDate") or "",
            status=detail.get("Status") or basic.get("Status") or "",
            industry=detail.get("Industry") or "",
            phone=phone,
            email=email,
            website=website,
            is_small_micro=bool(detail.get("IsMicroEnt") or detail.get("IsSmallMicro")),
            scale=detail.get("EnterpriseScale") or "",
            insurance_count=int(detail.get("InsuranceCount") or 0),
            is_listed=bool(detail.get("StockNumber") or detail.get("StockType")),
            stock_code=detail.get("StockNumber") or "",
            longitude=str(geo.get("Longitude") or ""),
            latitude=str(geo.get("Latitude") or ""),
            key_no=detail.get("KeyNo") or basic.get("KeyNo") or "",
            data_source="qichacha",
        )
