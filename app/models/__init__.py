"""
SQLAlchemy 数据库模型
"""
from sqlalchemy import Column, String, DateTime, Float, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.database import Base


def _utcnow():
    """UTC 时间，兼容 Python 3.12+"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Backtest(Base):
    __tablename__ = "backtests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    
    # 配置
    symbols = Column(JSON, default=["TSLA"])
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    strategy_config = Column(JSON, nullable=False)
    initial_capital = Column(Float, default=100000)
    
    # 结果摘要
    total_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    avg_trade_return = Column(Float)
    profit_factor = Column(Float)
    calmar_ratio = Column(Float)
    
    # 权益曲线数据 (JSON 数组，用于快速展示)
    equity_curve = Column(JSON)
    
    # 时间戳
    created_at = Column(DateTime, default=_utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 错误信息
    error_message = Column(String(1000))
    
    # 关联
    trades = relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")


class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtests.id"), nullable=False)
    
    # 交易信息
    entry_date = Column(DateTime, nullable=False)
    exit_date = Column(DateTime)
    entry_price = Column(Float)
    exit_price = Column(Float)
    
    # PnL
    pnl = Column(Float)
    pnl_pct = Column(Float)
    
    # 持仓详情
    legs = Column(JSON)  # [{type, strike, dte, pos, delta, iv, expiry}]
    
    # 关闭类型
    close_type = Column(String(20))  # trigger, expire, manual
    
    # 额外元数据（列名保留 "metadata"，Python 属性用 extra_data 避免与 SQLAlchemy 保留字冲突）
    extra_data = Column("metadata", JSON)

    backtest = relationship("Backtest", back_populates="trades")
