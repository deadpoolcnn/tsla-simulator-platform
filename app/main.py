"""
FastAPI 主入口
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.api.v1 import backtest, strategy, data, report
from app.config import settings

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时尝试创建数据库表，DB 不可达时仅警告不崩溃
    try:
        Base.metadata.create_all(bind=engine)
        log.info("Database tables ready")
    except Exception as e:
        log.warning(f"Database not available at startup: {e}")
        log.warning("Endpoints requiring DB will fail until the database is reachable.")
    yield
    # 关闭时清理


app = FastAPI(
    title="TSLA Simulator API",
    description="期权回测平台后端 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(backtest.router, prefix="/api/v1", tags=["回测"])
app.include_router(strategy.router, prefix="/api/v1", tags=["策略"])
app.include_router(data.router, prefix="/api/v1", tags=["数据"])
app.include_router(report.router, prefix="/api/v1", tags=["报告"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
