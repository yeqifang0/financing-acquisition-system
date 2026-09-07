"""企查查开放平台 API 客户端。

认证: Token = MD5(AppKey + Timespan + SecretKey).toUpperCase()
接口:
  - FuzzySearch/GetList: 企业模糊搜索，每页最多5条
  - EnterpriseInfo/Verify (2001): 企业信息核验，返回50+字段
"""
import hashlib
import time
import httpx

from .config import QCC_APP_KEY, QCC_SECRET_KEY, QCC_BASE_URL, QCC_RATE_LIMIT_MS, has_credentials


class QccNotPurchasedError(RuntimeError):
    """企查查接口未购买（Status=214），凭证有效但需购买 API 套餐。"""
    pass


class QccQuotaExhaustedError(RuntimeError):
    """企查查接口额度不足/已过期（Status=112），免费试用额度已用完。"""
    pass


class QccClient:
    def __init__(self):
        self.base_url = QCC_BASE_URL
        self.app_key = QCC_APP_KEY
        self.secret_key = QCC_SECRET_KEY
        self._last_call_ts = 0.0

    def _gen_auth(self) -> dict:
        """生成认证 header。"""
        timespan = str(int(time.time()))
        raw = f"{self.app_key}{timespan}{self.secret_key}"
        token = hashlib.md5(raw.encode()).hexdigest().upper()
        return {"Token": token, "Timespan": timespan}

    def _rate_limit(self):
        """合规限速。"""
        elapsed = (time.time() - self._last_call_ts) * 1000
        if elapsed < QCC_RATE_LIMIT_MS:
            time.sleep((QCC_RATE_LIMIT_MS - elapsed) / 1000)
        self._last_call_ts = time.time()

    def fuzzy_search(self, search_key: str, page_index: int = 1, page_size: int = 5) -> list[dict]:
        """企业模糊搜索，返回企业列表（Name/CreditCode/OperName/Status 等）。"""
        self._rate_limit()
        headers = self._gen_auth()
        params = {
            "key": self.app_key,
            "searchKey": search_key,
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        resp = httpx.get(
            f"{self.base_url}/FuzzySearch/GetList",
            headers=headers, params=params, timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        status = str(data.get("Status"))
        if status == "200":
            return data.get("Result", []) or []
        if status == "214":
            raise QccNotPurchasedError(data.get("Message", "接口未购买"))
        if status == "112":
            raise QccQuotaExhaustedError(data.get("Message", "账号剩余使用量已不足或已过期"))
        raise RuntimeError(f"企查查返回异常 Status={status}: {data.get('Message')}")

    def verify_enterprise(self, search_key: str) -> dict:
        """企业信息核验(2001)，返回详细企业信息（含电话/规模/参保人数等）。"""
        self._rate_limit()
        headers = self._gen_auth()
        params = {"key": self.app_key, "searchKey": search_key}
        resp = httpx.get(
            f"{self.base_url}/EnterpriseInfo/Verify",
            headers=headers, params=params, timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        status = str(data.get("Status"))
        if status == "200":
            return data.get("Result") or {}
        if status == "214":
            raise QccNotPurchasedError(data.get("Message", "接口未购买"))
        if status == "112":
            raise QccQuotaExhaustedError(data.get("Message", "账号剩余使用量已不足或已过期"))
        raise RuntimeError(f"企查查返回异常 Status={status}: {data.get('Message')}")

    def test_connection(self) -> dict:
        """测试连接状态，返回 {auth_ok, fuzzy_ok, verify_ok, quota_ok, detail}。"""
        result = {
            "auth_ok": False,
            "fuzzy_ok": False,
            "verify_ok": False,
            "quota_ok": False,
            "detail": "",
            "status_code": None,
        }
        try:
            self.fuzzy_search("科技", page_index=1)
            result["auth_ok"] = True
            result["fuzzy_ok"] = True
            result["quota_ok"] = True
        except QccNotPurchasedError as e:
            result["auth_ok"] = True
            result["detail"] = f"接口未购买: {e}"
            result["status_code"] = 214
        except QccQuotaExhaustedError as e:
            result["auth_ok"] = True
            result["detail"] = f"免费额度已用完或过期: {e}"
            result["status_code"] = 112
        except Exception as e:
            result["detail"] = f"连接失败: {e}"
            return result
        try:
            self.verify_enterprise("科技")
            result["verify_ok"] = True
        except (QccNotPurchasedError, QccQuotaExhaustedError) as e:
            if not result["detail"]:
                result["detail"] = f"核验接口: {e}"
        except Exception:
            pass
        return result

    def collect_leads(self, keyword: str, count: int = 20) -> list[dict]:
        """采集线索：先模糊搜索拿名单，再逐条核验拿详情。"""
        if not has_credentials():
            raise RuntimeError(
                "未配置企查查凭证。请设置环境变量 QCC_APP_KEY 和 QCC_SECRET_KEY，"
                "或用 QICHACHA_USE_MOCK=1 启用模拟数据降级。"
            )

        # 1) 模糊搜索：每页5条，翻页直到达到 count
        raw_companies = []
        pages_needed = (count + 4) // 5
        for page in range(1, pages_needed + 1):
            results = self.fuzzy_search(keyword, page_index=page)
            if not results:
                break
            raw_companies.extend(results)
            if len(raw_companies) >= count:
                break
        raw_companies = raw_companies[:count]

        # 2) 逐条核验拿详情
        leads = []
        for c in raw_companies:
            name = c.get("Name") or ""
            credit = c.get("CreditCode") or ""
            search_key = credit or name
            if not search_key:
                continue
            detail = self.verify_enterprise(search_key)
            if not detail:
                detail = {}
            lead = _map_qcc_to_lead(c, detail)
            leads.append(lead)
        return leads


def _to_int(val, default=0) -> int:
    try:
        return int(str(val).strip()) if val else default
    except (ValueError, TypeError):
        return default


def _map_qcc_to_lead(basic: dict, detail: dict) -> dict:
    """将企查查返回映射到 Lead 字典（供评分模型消费）。"""
    name = detail.get("Name") or basic.get("Name") or ""
    credit = detail.get("CreditCode") or basic.get("CreditCode") or ""

    contact = detail.get("ContactInfo") or {}
    phone = contact.get("PhoneNumber") or contact.get("Telephone") or ""
    email = contact.get("Email") or ""
    website = contact.get("WebSite") or contact.get("Website") or ""

    geo = detail.get("Geocoding") or {}
    lon = str(geo.get("Longitude") or "")
    lat = str(geo.get("Latitude") or "")

    return {
        "company_name": name,
        "credit_code": credit,
        "legal_representative": detail.get("OperName") or basic.get("OperName") or "",
        "registered_capital": detail.get("RegCapital") or "",
        "paid_in_capital": detail.get("RealCapital") or detail.get("PaidInCapital") or "",
        "registered_address": detail.get("Address") or basic.get("Address") or "",
        "business_scope": detail.get("Scope") or "",
        "establish_date": detail.get("StartDate") or basic.get("StartDate") or "",
        "enterprise_status": detail.get("Status") or basic.get("Status") or "",
        "industry": detail.get("Industry") or detail.get("IndustryType") or "",
        "phone": phone,
        "email": email,
        "website": website,
        "is_small_micro": bool(detail.get("IsMicroEnt") or detail.get("IsSmallMicro")),
        "enterprise_scale": detail.get("EnterpriseScale") or detail.get("Scale") or "",
        "insurance_count": _to_int(detail.get("SocialSecurity") or {}).get("InsuranceCount") if isinstance(detail.get("SocialSecurity"), dict) else _to_int(detail.get("InsuranceCount")),
        "is_listed": bool(detail.get("StockNumber") or detail.get("StockType")),
        "stock_code": detail.get("StockNumber") or "",
        "longitude": lon,
        "latitude": lat,
        "key_no": detail.get("KeyNo") or basic.get("KeyNo") or "",
        "data_source": "qichacha",
    }


client = QccClient() if has_credentials() else None
