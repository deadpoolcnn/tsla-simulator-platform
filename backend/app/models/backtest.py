"""
Pydantic 模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from uuid import UUID


# ========== 回测相关 ==========

class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StrategyTemplate(str, Enum):
    TEMPLATE_A = "A"
    TEMPLATE_C = "C"
    TEMPLATE_D = "D"


class LegConfig(BaseModel):
    enabled: bool = True
    delta_min: Optional[float] = None
    delta_max: Optional[float] = None
    dte_min: Optional[int] = None
    dte_max: Optional[int] = None


class StrategyConfig(BaseModel):
    template: StrategyTemplate = StrategyTemplate.TEMPLATE_C
    initial_capital: float = Field(default=100000, gt=0)
    
    # Template C 配置
    leg1_call: LegConfig = LegConfig(enabled=True, delta_min=0.65, delta_max=0.75, dte_min=20, dte_max=27)
    leg2_mid_buy: LegConfig = LegConfig(enabled=True, delta_min=-0.45, delta_max=-0.40, dte_min=20, dte_max=30)
    leg3_mid_sell: LegConfig = LegConfig(enabled=True, delta_min=-0.20, delta_max=-0.15, dte_min=150, dte_max=210)
    leg4_far_buy: LegConfig = LegConfig(enabled=True, delta_min=-0.35, delta_max=-0.25, dte_min=30, dte_max=45)
    leg5_far_sell: LegConfig = LegConfig(enabled=True, delta_min=-0.15, delta_max=-0.10, dte_min=150, dte_max=210)
    
    # 滚动获利
    rolling_profit_enabled: bool = True
    rolling_profit_start_pct: float = 0.07
    rolling_profit_step_pct: float = 0.03
    rolling_profit_final_pct: float = 0.80
    
    # 信号条件
    signal_min_conditions: int = Field(default=4, ge=1, le=7)
    price_move_threshold: float = 0.018
    
    # IV 筛选
    iv_rank_min: float = 20
    iv_rank_max: float = 80
    iv_percentile_min: float = 30
    iv_percentile_max: float = 70


class BacktestCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    symbols: List[str] = Field(default=["TSLA"])
    start_date: date
    end_date: date
    strategy_config: StrategyConfig


class BacktestResponse(BaseModel):
    id: UUID
    name: str
    status: BacktestStatus
    symbols: List[str]
    start_date: date
    end_date: date
    strategy_config: Dict[str, Any]
    
    # 结果
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: Optional[int] = None
    
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BacktestProgress(BaseModel):
    backtest_id: UUID
    status: BacktestStatus
    progress: float = Field(..., ge=0, le=100)
    current_date: Optional[date] = None
    current_capital: Optional[float] = None
    open_positions: int = 0
    message: Optional[str] = None


# ========== 交易记录 ==========

class TradeResponse(BaseModel):
    id: UUID
    entry_date: datetime
    exit_date: Optional[datetime] = None
    entry_price: float
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    legs: List[Dict[str, Any]]
    close_type: Optional[str] = None
    
    class Config:
        from_attributes = True


# ========== 报告相关 ==========

class BacktestSummary(BaseModel):
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    avg_trade_return: float
    profit_factor: Optional[float] = None
    calmar_ratio: Optional[float] = None


class EquityCurvePoint(BaseModel):
    date: date
    equity: float
    drawdown: float
    cash: float
    positions_value: float


class MonthlyReturns(BaseModel):
    year: int
    month: int
    return_pct: float
