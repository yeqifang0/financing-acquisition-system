"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import chat, leads, schedules, tasks
from .scoring import DIMENSIONS


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="企业融资智能获客系统", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(leads.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")


@app.get("/api/health")
def health():
    from .providers import get_provider_status
    providers = get_provider_status()
    active = next((p for p in providers if p.get("quota_ok")), None)
    return {
        "status": "ok",
        "active_provider": active["name"] if active else "mock",
        "providers": [{"name": p["name"], "free_tier": p["free_tier"], "auth_ok": p.get("auth_ok", False), "quota_ok": p.get("quota_ok", False)} for p in providers],
    }


@app.get("/api/config")
def get_config():
    from .providers import get_provider_status
    return {
        "scoring_dimensions": DIMENSIONS,
        "providers": get_provider_status(),
    }


@app.get("/api/providers")
def list_providers():
    """列出所有数据源及其连接状态。"""
    from .providers import get_provider_status
    return get_provider_status()
