"""数据源抽象层（Provider 接口）。

所有数据源（企查查/CNBizAPI/瀚海/Mock）实现同一接口，
由 providers/__init__.py 的 get_available_providers() 按优先级路由。
"""
from abc import ABC, abstractmethod
from typing import Optional


class EnterpriseProvider(ABC):
    """企业数据提供者抽象接口。"""

    name: str = "base"
    label: str = "基础"
    # 此提供者的模糊搜索是否免费（永久免费 / 有限免费 / 付费）
    free_tier: str = "paid"  # free / trial / paid
    # 简短说明
    note: str = ""

    @abstractmethod
    def is_available(self) -> bool:
        """此提供者是否可用（凭证是否配置、接口是否可用）。"""
        ...

    @abstractmethod
    def collect_leads(self, keyword: str, count: int = 20) -> list[dict]:
        """采集线索：模糊搜索 + 详情，返回统一格式的 Lead 字典列表。"""
        ...

    @abstractmethod
    def test_connection(self) -> dict:
        """测试连接状态，返回 {auth_ok, quota_ok, detail, ...}。"""
        ...

    # ---- 辅助：统一字段映射 ----
    @staticmethod
    def map_to_lead(
        name: str = "", credit_code: Optional[str] = None,
        legal_rep: Optional[str] = None, reg_capital: Optional[str] = None,
        paid_capital: Optional[str] = None, address: Optional[str] = None,
        scope: Optional[str] = None, establish_date: Optional[str] = None,
        status: Optional[str] = None, industry: Optional[str] = None,
        phone: Optional[str] = None, email: Optional[str] = None,
        website: Optional[str] = None, is_small_micro: bool = False,
        scale: Optional[str] = None, insurance_count: int = 0,
        is_listed: bool = False, stock_code: Optional[str] = None,
        longitude: Optional[str] = None, latitude: Optional[str] = None,
        key_no: Optional[str] = None, data_source: str = "",
    ) -> dict:
        """将原始字段映射到统一 Lead 字典（供评分模型消费）。"""
        return {
            "company_name": name,
            "credit_code": credit_code,
            "legal_representative": legal_rep,
            "registered_capital": reg_capital,
            "paid_in_capital": paid_capital,
            "registered_address": address,
            "business_scope": scope,
            "establish_date": establish_date,
            "enterprise_status": status,
            "industry": industry,
            "phone": phone,
            "email": email,
            "website": website,
            "is_small_micro": is_small_micro,
            "enterprise_scale": scale,
            "insurance_count": insurance_count,
            "is_listed": is_listed,
            "stock_code": stock_code,
            "longitude": longitude,
            "latitude": latitude,
            "key_no": key_no,
            "data_source": data_source,
        }
