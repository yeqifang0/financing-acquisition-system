"""CNBizAPI — 永久免费的企业数据 API。

特点：
  - 注册即送 200 次/月免费额度（search/basic/verify 永久免费，不计入额度）
  - 7700万+ 企业数据，每日更新
  - REST API + Bearer Token 鉴权
  - 数据来源：国家市场监督管理总局（SAMR）

注册：https://api.cnbizapi.com/v1/auth/register
API Key 格式：cbz_xxxxxxxxx
"""
import os
import time
import httpx

from .base import EnterpriseProvider


class CNBizAPIProvider(EnterpriseProvider):
    name = "cnbizapi"
    label = "CNBizAPI"
    free_tier = "free"
    note = "永久免费（search_company / get_company_basic / verify_company 不计额度）"

    BASE_URL = "https://api.cnbizapi.com/v1"

    def __init__(self):
        self.api_key = os.getenv("CNBIZ_API_KEY", "")
        self._last_call_ts = 0.0

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _rate_limit(self):
        elapsed = (time.time() - self._last_call_ts) * 1000
        if elapsed < 200:
            time.sleep((200 - elapsed) / 1000)
        self._last_call_ts = time.time()

    def is_available(self) -> bool:
        return bool(self.api_key)

    def test_connection(self) -> dict:
        if not self.api_key:
            return {"auth_ok": False, "quota_ok": False, "detail": "未配置 CNBIZ_API_KEY"}
        try:
            self._rate_limit()
            resp = httpx.get(
                f"{self.BASE_URL}/company/search",
                headers=self._headers(),
                params={"keyword": "科技", "page": 1, "size": 5},
                timeout=10, verify=False,
            )
            if resp.status_code == 401:
                return {"auth_ok": False, "quota_ok": False, "detail": "API Key 无效或已过期"}
            resp.raise_for_status()
            data = resp.json()
            return {"auth_ok": True, "quota_ok": True, "detail": f"正常，返回 {len(data.get('results', []))} 条"}
        except httpx.HTTPStatusError as e:
            return {"auth_ok": False, "quota_ok": False, "detail": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            return {"auth_ok": False, "quota_ok": False, "detail": str(e)}

    def _search(self, keyword: str, page: int = 1, size: int = 5) -> list[dict]:
        """企业模糊搜索（永久免费，不计额度）。"""
        self._rate_limit()
        resp = httpx.get(
            f"{self.BASE_URL}/company/search",
            headers=self._headers(),
            params={"keyword": keyword, "page": page, "size": size},
            timeout=10, verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("results") or []

    def _get_basic(self, query: str) -> dict:
        """企业基本信息（永久免费，不计额度）。query = 信用代码或企业名。"""
        self._rate_limit()
        resp = httpx.get(
            f"{self.BASE_URL}/company/basic",
            headers=self._headers(),
            params={"q": query},
            timeout=10, verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("result") or {}

    def collect_leads(self, keyword: str, count: int = 20) -> list[dict]:
        """采集线索：搜索 + 批量获取基本信息。"""
        if not self.api_key:
            raise RuntimeError("未配置 CNBIZ_API_KEY，请在 https://api.cnbizapi.com/v1/auth/register 注册获取")

        # 1) 模糊搜索（翻页）
        raw_companies = []
        pages_needed = (count + 4) // 5
        for page in range(1, pages_needed + 1):
            results = self._search(keyword, page=page)
            if not results:
                break
            raw_companies.extend(results)
            if len(raw_companies) >= count:
                break
        raw_companies = raw_companies[:count]

        # 2) 逐条获取基本信息（也免费）
        leads = []
        for c in raw_companies:
            try:
                detail = self._get_basic(c.get("uscc") or c.get("name") or "")
            except Exception:
                detail = {}
            lead = self._map(c, detail)
            leads.append(lead)
        return leads

    def _map(self, basic: dict, detail: dict) -> dict:
        """CNBizAPI 返回字段 → 统一 Lead 字典。"""
        name = detail.get("name") or basic.get("name") or ""
        credit = detail.get("uscc") or basic.get("uscc") or ""

        contact = detail.get("contact") or {}
        phone = contact.get("phone") or detail.get("phone") or ""
        email = contact.get("email") or detail.get("email") or ""
        website = detail.get("website") or ""

        return self.map_to_lead(
            name=name,
            credit_code=credit,
            legal_rep=detail.get("legal_representative") or basic.get("legal_representative") or "",
            reg_capital=detail.get("registered_capital") or "",
            paid_capital=detail.get("paid_in_capital") or "",
            address=detail.get("registered_address") or basic.get("registered_address") or "",
            scope=detail.get("business_scope") or "",
            establish_date=detail.get("establish_date") or basic.get("establish_date") or "",
            status=detail.get("status") or basic.get("status") or "",
            industry=detail.get("industry") or "",
            phone=phone,
            email=email,
            website=website,
            is_small_micro=bool(detail.get("is_small_micro")),
            scale=detail.get("enterprise_scale") or "",
            insurance_count=int(detail.get("insurance_count") or 0),
            is_listed=bool(detail.get("is_listed")),
            stock_code=detail.get("stock_code") or "",
            longitude=str(detail.get("longitude") or ""),
            latitude=str(detail.get("latitude") or ""),
            key_no=detail.get("key_no") or basic.get("key_no") or "",
            data_source="cnbizapi",
        )
