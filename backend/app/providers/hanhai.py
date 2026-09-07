"""鲸海数据 Provider — 注册即送 1000 次免费额度（全平台通用）。

认证: Header X-Jinghai-App-Id + X-Jinghai-Api-Key
Base: https://www.kqdaas.com
接口:
  - 企业模糊搜索: /DataService/api/v3/company/search    (需在数据市场开通)
  - 企业详情   : /DataService/api/v3/company/detail/:keyword?queryType=1/2/3  (已可用)

注：注册后需先到「数据市场」开通接口，免费额度 1000 次全平台通用。
"""
import os
import time
import urllib.parse
import httpx

from .base import EnterpriseProvider


class HanhaiProvider(EnterpriseProvider):
    name = "hanhai"
    label = "鲸海数据"
    free_tier = "trial"
    note = "注册送 1000 次，需去数据市场开通接口"

    BASE_URL = os.getenv("HANHAI_BASE_URL", "https://www.kqdaas.com")

    def __init__(self):
        self.app_id = os.getenv("JINGHAI_APP_ID", os.getenv("HANHAI_APPID", ""))
        self.api_key = os.getenv("JINGHAI_API_KEY", os.getenv("HANHAI_APP_SECRET", ""))
        self._last_call_ts = 0.0

    def _headers(self) -> dict:
        return {
            "X-Jinghai-App-Id": self.app_id,
            "X-Jinghai-Api-Key": self.api_key,
            "Accept": "application/json",
        }

    def _rate_limit(self):
        elapsed = (time.time() - self._last_call_ts) * 1000
        if elapsed < 150:
            time.sleep((150 - elapsed) / 1000)
        self._last_call_ts = time.time()

    def is_available(self) -> bool:
        return bool(self.app_id and self.api_key)

    def test_connection(self) -> dict:
        if not self.is_available():
            return {"auth_ok": False, "quota_ok": False, "detail": "未配置 JINGHAI_APP_ID / JINGHAI_API_KEY"}
        try:
            self._rate_limit()
            # 用详情接口测试鉴权和额度（已知可用）
            cc = urllib.parse.quote("91440300708461136T")  # 腾讯
            resp = httpx.get(
                f"{self.BASE_URL}/DataService/api/v3/company/detail/{cc}",
                params={"queryType": 2},
                headers=self._headers(),
                timeout=15, verify=False,
            )
            data = resp.json()
            if data.get("status") == 200 and data.get("data"):
                return {"auth_ok": True, "quota_ok": True, "detail": "正常，详情接口可用"}
            return {"auth_ok": False, "quota_ok": False, "detail": f"status={data.get('status')}: {data.get('message', '')}"}
        except Exception as e:
            return {"auth_ok": False, "quota_ok": False, "detail": str(e)}

    def _search(self, keyword: str, page: int = 1, size: int = 5) -> list[dict]:
        """企业模糊搜索（需在鲸海数据市场开通接口）。"""
        self._rate_limit()
        kw = urllib.parse.quote(keyword)
        resp = httpx.get(
            f"{self.BASE_URL}/DataService/api/v3/company/search",
            params={"keyword": kw, "pageIndex": page, "pageSize": size},
            headers=self._headers(),
            timeout=15, verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == 200:
            items = (data.get("data") or {}).get("list") or []
            return items
        # 可能是 errcode 格式
        if data.get("success"):
            items = (data.get("data") or {}).get("list") or []
            return items
        raise RuntimeError(f"搜索接口不可用: {data.get('errmsg') or data.get('message') or data}")

    def _detail(self, query: str, query_type: int = 2) -> dict:
        """企业详情。queryType: 1=企业名称, 2=统一社会信用代码, 3=企业ID。"""
        self._rate_limit()
        q = urllib.parse.quote(query)
        resp = httpx.get(
            f"{self.BASE_URL}/DataService/api/v3/company/detail/{q}",
            params={"queryType": query_type},
            headers=self._headers(),
            timeout=15, verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == 200 or data.get("success"):
            return data.get("data") or {}
        raise RuntimeError(f"详情接口错误: {data.get('message') or data.get('errmsg')}")

    def collect_leads(self, keyword: str, count: int = 20) -> list[dict]:
        """采集线索：优先搜索接口，不可用时用种子名单。"""
        if not self.is_available():
            raise RuntimeError("未配置鲸海凭证")

        names_to_query: list[str] = []

        # 方式1: 试试搜索接口（可能未开通）
        try:
            raw = self._search(keyword, page=1, size=5)
            if raw:
                # 搜索接口可用，翻页拉取
                pages_needed = (count + 4) // 5
                for page in range(1, pages_needed + 1):
                    items = self._search(keyword, page=page)
                    if not items:
                        break
                    for it in items:
                        n = it.get("companyName") or it.get("name") or ""
                        if n:
                            names_to_query.append(n)
                    if len(names_to_query) >= count:
                        break
                names_to_query = names_to_query[:count]
        except Exception:
            # 搜索接口不可用 → 用种子名单
            pass

        # 方式2: 种子名单兜底
        if not names_to_query:
            from ..seed_companies import search_seeds
            names_to_query = search_seeds(keyword, count)

        if not names_to_query:
            raise RuntimeError(f"未找到匹配「{keyword}」的企业")

        # 批量拉详情（queryType=1 企业名称）
        leads = []
        for name in names_to_query:
            try:
                detail = self._detail(name, query_type=1)
                if detail:
                    leads.append(self._map({}, detail))
            except Exception:
                continue
        return leads

    def _map(self, basic: dict, detail: dict) -> dict:
        """鲸海返回字段 → 统一 Lead 字典。"""
        d = detail or {}
        return self.map_to_lead(
            name=d.get("companyName") or basic.get("companyName") or basic.get("name") or "",
            credit_code=d.get("creditNumber") or d.get("creditCode") or basic.get("creditCode") or basic.get("uscc"),
            legal_rep=d.get("juridicalPerson") or basic.get("juridicalPerson") or "",
            reg_capital=d.get("registeredCapital") or "",
            paid_capital=d.get("contributedCapital") or "",
            address=d.get("regitAddress") or d.get("address") or "",
            scope=d.get("businessScope") or "",
            establish_date=d.get("establishTime") or basic.get("establishTime") or "",
            status=d.get("businessStatus") or "",
            industry=d.get("companyIndustry") or "",
            phone="",  # 鲸海基础接口不返回电话，需用更深层接口
            email="",
            website="",
            is_small_micro=False,
            scale="",
            insurance_count=int(d.get("socialSecurityNum") or 0),
            is_listed=False,
            stock_code="",
            longitude="",
            latitude="",
            key_no=d.get("id") or basic.get("id") or "",
            data_source="hanhai",
        )
