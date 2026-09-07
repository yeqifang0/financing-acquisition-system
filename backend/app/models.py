"""数据模型：leads（线索）/ crawl_tasks（采集任务）/ scheduled_jobs（定时任务）。"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Float, Boolean,
    DateTime, JSON, Index,
)

# SQLite 下 BigInteger 主键不自动递增，用 Integer 变体兼容
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")

from .database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(BigIntPK, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, index=True)
    credit_code = Column(String(64), unique=True, index=True)
    legal_representative = Column(String(128))
    registered_capital = Column(String(64))
    paid_in_capital = Column(String(64))
    registered_address = Column(Text)
    business_scope = Column(Text)
    establish_date = Column(String(32))
    enterprise_status = Column(String(32))
    industry = Column(String(128))
    phone = Column(String(64))
    email = Column(String(128))
    website = Column(String(255))
    is_small_micro = Column(Boolean, default=False)
    enterprise_scale = Column(String(32))
    insurance_count = Column(Integer, default=0)
    is_listed = Column(Boolean, default=False)
    stock_code = Column(String(32))
    longitude = Column(String(32))
    latitude = Column(String(32))
    key_no = Column(String(64))

    # 评分
    score = Column(Float, default=0)
    intention_level = Column(String(16), default="low")
    score_dimensions = Column(JSON)

    # 合规
    data_source = Column(String(32), default="qichacha")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_leads_intention", "intention_level"),
        Index("idx_leads_score", "score"),
    )


class CrawlTask(Base):
    __tablename__ = "crawl_tasks"

    id = Column(BigIntPK, primary_key=True, autoincrement=True)
    keyword = Column(String(255), nullable=False)
    region = Column(String(64))
    status = Column(String(32), default="pending")  # pending/running/completed/failed
    total = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    params = Column(JSON)
    error = Column(Text)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(BigIntPK, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    cron_expr = Column(String(64), default="0 9 * * 1-5")
    keyword = Column(String(255))
    region = Column(String(64))
    count = Column(Integer, default=20)
    enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
