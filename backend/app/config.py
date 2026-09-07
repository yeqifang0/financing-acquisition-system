"""配置模块：企查查 API 凭证、数据库、数据源模式。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---- 企查查开放平台凭证 ----
QCC_APP_KEY = os.getenv("QCC_APP_KEY", "")
QCC_SECRET_KEY = os.getenv("QCC_SECRET_KEY", "")
QCC_BASE_URL = os.getenv("QCC_BASE_URL", "https://api.qichacha.com")

# 数据源模式：默认走企查查真实 API；QICHACHA_USE_MOCK=1 时降级 mock
USE_MOCK = os.getenv("QICHACHA_USE_MOCK", "0") == "1"

# ---- 数据库 ----
DB_PATH = BASE_DIR / "data" / "acquisition.db"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DB_PATH}",
)

# ---- 限速（合规：避免高频调用）----
QCC_RATE_LIMIT_MS = int(os.getenv("QCC_RATE_LIMIT_MS", "300"))  # 请求间隔毫秒
QCC_MAX_DETAIL_PER_RUN = int(os.getenv("QCC_MAX_DETAIL_PER_RUN", "50"))


def has_credentials() -> bool:
    """检查是否配置了企查查凭证。"""
    return bool(QCC_APP_KEY and QCC_SECRET_KEY)


def data_source_label() -> str:
    """返回当前数据源标签（供前端展示）。"""
    if USE_MOCK:
        return "mock"
    if has_credentials():
        return "qichacha"
    return "none"
