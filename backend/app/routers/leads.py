"""Leads 路由：线索看板 CRUD + 筛选 + CSV 导出。"""
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Lead
from ..schemas import LeadOut, StatsOut

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadOut])
def list_leads(
    db: Session = Depends(get_db),
    keyword: str = Query("", description="企业名/信用代码模糊搜索"),
    intention: str = Query("", description="high/mid/low"),
    min_score: float = Query(0, description="最低评分"),
    has_phone: bool = Query(False, description="仅有电话"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = db.query(Lead)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(Lead.company_name.ilike(kw) | Lead.credit_code.ilike(kw))
    if intention:
        q = q.filter(Lead.intention_level == intention)
    if min_score > 0:
        q = q.filter(Lead.score >= min_score)
    if has_phone:
        q = q.filter(Lead.phone != None, Lead.phone != "")
    q = q.order_by(desc(Lead.score))
    offset = (page - 1) * page_size
    return q.offset(offset).limit(page_size).all()


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Lead.id)).scalar() or 0
    high = db.query(func.count(Lead.id)).filter(Lead.intention_level == "high").scalar() or 0
    mid = db.query(func.count(Lead.id)).filter(Lead.intention_level == "mid").scalar() or 0
    low = db.query(func.count(Lead.id)).filter(Lead.intention_level == "low").scalar() or 0
    with_phone = db.query(func.count(Lead.id)).filter(Lead.phone != None, Lead.phone != "").scalar() or 0
    avg = db.query(func.avg(Lead.score)).scalar() or 0
    return StatsOut(total_leads=total, high_intention=high, mid_intention=mid, low_intention=low, with_phone=with_phone, avg_score=round(float(avg), 1))


@router.get("/export")
def export_csv(db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(desc(Lead.score)).all()
    output = io.StringIO()
    output.write("\ufeff")  # BOM for Excel
    writer = csv.writer(output)
    writer.writerow(["企业名称", "信用代码", "法定代表人", "注册资本", "行业", "联系电话", "意向等级", "评分", "数据来源", "创建时间"])
    for l in leads:
        writer.writerow([
            l.company_name, l.credit_code, l.legal_representative, l.registered_capital,
            l.industry, l.phone, l.intention_level, l.score, l.data_source,
            l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=leads_{datetime.now().strftime('%Y%m%d%H%M')}.csv"},
    )


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return {"ok": False, "error": "not found"}
    db.delete(lead)
    db.commit()
    return {"ok": True}
