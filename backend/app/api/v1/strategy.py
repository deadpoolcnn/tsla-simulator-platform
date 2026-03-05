"""
策略配置 API
"""
from fastapi import APIRouter
from typing import Dict, Any

from app.models.backtest import StrategyConfig, StrategyTemplate

router = APIRouter()


@router.get("/strategies/templates")
async def get_strategy_templates():
    """获取策略模板列表"""
    return [
        {
            "id": "A",
            "name": "Put-Skew Calendar",
            "description": "利用 Put 偏斜的日历价差策略",
            "enabled": False
        },
        {
            "id": "C", 
            "name": "通用平衡看多",
            "description": "5腿组合策略，主推荐策略",
            "enabled": True
        },
        {
            "id": "D",
            "name": "Call-Skew Calendar", 
            "description": "利用 Call 偏斜的日历价差策略",
            "enabled": False
        }
    ]


@router.get("/strategies/config-schema")
async def get_config_schema():
    """获取策略配置的 JSON Schema"""
    return {
        "template": {
            "type": "string",
            "enum": ["A", "C", "D"],
            "default": "C",
            "description": "策略模板"
        },
        "initial_capital": {
            "type": "number",
            "minimum": 10000,
            "default": 100000,
            "description": "初始资金"
        },
        "signal_min_conditions": {
            "type": "integer",
            "minimum": 1,
            "maximum": 7,
            "default": 4,
            "description": "7选4条件的最小满足数"
        },
        "rolling_profit_enabled": {
            "type": "boolean",
            "default": True,
            "description": "启用滚动获利"
        },
        "rolling_profit_start_pct": {
            "type": "number",
            "default": 0.07,
            "description": "滚动获利起始涨幅"
        },
        "rolling_profit_step_pct": {
            "type": "number", 
            "default": 0.03,
            "description": "滚动获利步进涨幅"
        },
        "rolling_profit_final_pct": {
            "type": "number",
            "default": 0.80,
            "description": "完全平仓涨幅"
        },
        "iv_rank_min": {
            "type": "number",
            "default": 20,
            "description": "IV Rank 下限"
        },
        "iv_rank_max": {
            "type": "number",
            "default": 80,
            "description": "IV Rank 上限"
        }
    }


@router.get("/strategies/default-config")
async def get_default_config():
    """获取默认策略配置"""
    return StrategyConfig().dict()
