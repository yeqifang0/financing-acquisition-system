"""Mock 数据源 — 兜底降级，模拟生成企业线索（无真实数据但字段完整）。"""
import random
from .base import EnterpriseProvider
from ..mock_data import generate_leads as raw_generate


class MockProvider(EnterpriseProvider):
    name = "mock"
    label = "模拟数据"
    free_tier = "free"
    note = "本地模拟数据，字段完整但非真实企业"

    def is_available(self) -> bool:
        return True  # 永远可用

    def test_connection(self) -> dict:
        return {"auth_ok": True, "quota_ok": True, "detail": "本地模拟数据，无需联网"}

    def collect_leads(self, keyword: str, count: int = 20) -> list[dict]:
        raw = raw_generate(keyword, count)
        leads = []
        for r in raw:
            leads.append(self.map_to_lead(
                name=r["company_name"],
                credit_code=r["credit_code"],
                legal_rep=r["legal_representative"],
                reg_capital=r["registered_capital"],
                paid_capital=r["paid_in_capital"],
                address=r["registered_address"],
                scope=r["business_scope"],
                establish_date=r["establish_date"],
                status=r["enterprise_status"],
                industry=r["industry"],
                phone=r["phone"],
                email=r["email"],
                website=r["website"],
                is_small_micro=r["is_small_micro"],
                scale=r["enterprise_scale"],
                insurance_count=r["insurance_count"],
                is_listed=r["is_listed"],
                stock_code=r["stock_code"],
                longitude=r["longitude"],
                latitude=r["latitude"],
                key_no=r["key_no"],
                data_source="mock",
            ))
        return leads
