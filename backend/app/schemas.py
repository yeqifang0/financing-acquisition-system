"""Pydantic schemas：请求/响应数据模型。"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LeadOut(BaseModel):
    id: int
    company_name: str
    credit_code: Optional[str] = None
    legal_representative: Optional[str] = None
    registered_capital: Optional[str] = None
    registered_address: Optional[str] = None
    business_scope: Optional[str] = None
    establish_date: Optional[str] = None
    enterprise_status: Optional[str] = None
    industry: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    is_small_micro: Optional[bool] = None
    enterprise_scale: Optional[str] = None
    insurance_count: Optional[int] = None
    is_listed: Optional[bool] = None
    score: float
    intention_level: str
    score_dimensions: Optional[dict] = None
    data_source: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户自然语言指令")


class ScheduledJobCreate(BaseModel):
    name: str
    cron_expr: str = "0 9 * * 1-5"
    keyword: str = ""
    region: str = ""
    count: int = 20
    enabled: bool = True


class ScheduledJobOut(ScheduledJobCreate):
    id: int
    last_run_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CrawlTaskOut(BaseModel):
    id: int
    keyword: str
    region: Optional[str] = None
    status: str
    total: int
    processed: int
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total_leads: int
    high_intention: int
    mid_intention: int
    low_intention: int
    with_phone: int
    avg_score: float
