"""Schedules 路由：定时任务 CRUD。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ScheduledJob
from ..schemas import ScheduledJobCreate, ScheduledJobOut

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduledJobOut])
def list_schedules(db: Session = Depends(get_db)):
    return db.query(ScheduledJob).order_by(ScheduledJob.id.desc()).all()


@router.post("", response_model=ScheduledJobOut)
def create_schedule(job: ScheduledJobCreate, db: Session = Depends(get_db)):
    obj = ScheduledJob(**job.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{job_id}", response_model=ScheduledJobOut)
def update_schedule(job_id: int, job: ScheduledJobCreate, db: Session = Depends(get_db)):
    obj = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not obj:
        raise HTTPException(404, "not found")
    for k, v in job.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{job_id}")
def delete_schedule(job_id: int, db: Session = Depends(get_db)):
    obj = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not obj:
        raise HTTPException(404, "not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}
