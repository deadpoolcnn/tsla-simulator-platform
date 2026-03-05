"""
报告服务
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models import Backtest, Trade
from app.models.backtest import BacktestSummary, EquityCurvePoint


class ReportService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_summary(self, backtest_id: UUID) -> Optional[BacktestSummary]:
        """获取回测摘要"""
        backtest = self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if not backtest or backtest.status != "completed":
            return None
        
        return BacktestSummary(
            total_return=backtest.total_return or 0,
            sharpe_ratio=backtest.sharpe_ratio or 0,
            max_drawdown=backtest.max_drawdown or 0,
            win_rate=backtest.win_rate or 0,
            total_trades=backtest.total_trades or 0,
            avg_trade_return=backtest.avg_trade_return or 0,
            profit_factor=backtest.profit_factor,
            calmar_ratio=backtest.calmar_ratio
        )
    
    def get_equity_curve(self, backtest_id: UUID) -> List[EquityCurvePoint]:
        """获取权益曲线"""
        backtest = self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if not backtest or not backtest.equity_curve:
            return []
        
        # equity_curve 是 JSON 格式存储
        return [EquityCurvePoint(**point) for point in backtest.equity_curve]
    
    def get_trades(self, backtest_id: UUID, skip: int = 0, limit: int = 100) -> List[Trade]:
        """获取交易记录"""
        return self.db.query(Trade).filter(
            Trade.backtest_id == backtest_id
        ).order_by(Trade.entry_date.desc()).offset(skip).limit(limit).all()
