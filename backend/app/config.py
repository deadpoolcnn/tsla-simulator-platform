"""
配置管理
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "postgresql://tsla_user:tsla_pass@localhost:5432/tsla_simulator"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # 数据路径
    DATA_DIR: str = "/app/data"
    
    class Config:
        env_file = ".env"


settings = Settings()
