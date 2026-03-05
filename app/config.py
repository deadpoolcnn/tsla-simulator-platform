"""
配置管理 - 所有环境变量由 .env 统一管理
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import json
import os


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # 数据路径
    DATA_DIR: str = "./data"

    # 安全
    SECRET_KEY: str = "change-me"

    # 应用
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """CORS_ORIGINS 支持 JSON 数组字符串和列表两种格式"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return [s.strip() for s in v.split(",") if s.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
