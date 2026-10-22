import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.router import api
from app.api.routes import assets
from app.core.config import settings
from app.core.ratelimit import limiter
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title=settings.app_name, docs_url="/api/docs", openapi_url="/api/openapi.json")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,          # 前后端分离 + cookie 认证必须开
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api)
app.include_router(assets.router)   # /media/... 不走 /api/v1，nginx 可以直接发文件


@app.get("/healthz", tags=["meta"])
async def healthz() -> dict[str, str]:
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}
