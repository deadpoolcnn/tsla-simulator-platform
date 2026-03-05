"""
API 路由入口
"""
from fastapi import APIRouter

from app.api.v1 import backtest, strategy, data, report

# 可以在这里添加版本前缀或认证
