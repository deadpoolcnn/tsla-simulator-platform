"""
回测业务服务
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models import Backtest, Trade
from app.models.backtest import BacktestCreate, BacktestStatus


class BacktestService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_backtest(self, data: BacktestCreate) -> Backtest:
        """创建回测记录"""
        backtest = Backtest(
            name=data.name,
            status=BacktestStatus.PENDING,
            symbols=data.symbols,
            start_date=data.start_date,
            end_date=data.end_date,
            strategy_config=data.strategy_config.model_dump(),
            initial_capital=data.strategy_config.initial_capital
        )
        self.db.add(backtest)
        self.db.commit()
        self.db.refresh(backtest)
        return backtest
    
    def get_backtest(self, backtest_id: UUID) -> Optional[Backtest]:
        """获取回测详情"""
        return self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
    
    def list_backtests(self, skip: int = 0, limit: int = 20) -> List[Backtest]:
        """获取回测列表"""
        return self.db.query(Backtest).order_by(Backtest.created_at.desc()).offset(skip).limit(limit).all()
    
    def delete_backtest(self, backtest_id: UUID) -> bool:
        """删除回测"""
        backtest = self.get_backtest(backtest_id)
        if not backtest:
            return False
        self.db.delete(backtest)
        self.db.commit()
        return True
    
    def update_status(self, backtest_id: UUID, status: BacktestStatus, **kwargs):
        """更新回测状态"""
        backtest = self.get_backtest(backtest_id)
        if backtest:
            backtest.status = status
            for key, value in kwargs.items():
                setattr(backtest, key, value)
            self.db.commit()
