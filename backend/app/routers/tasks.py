"""Tasks 路由：采集任务查询。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CrawlTask
from ..schemas import CrawlTaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[CrawlTaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = db.query(CrawlTask).order_by(CrawlTask.id.desc())
    offset = (page - 1) * page_size
    return q.offset(offset).limit(page_size).all()
