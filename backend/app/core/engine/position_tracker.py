"""
持仓跟踪器 - 从 sim_position_tracker.py 迁移

简化版核心功能：
1. 记录开仓/平仓
2. 计算盈亏
3. 跟踪权益
"""
import logging
from datetime import date
from typing import List, Dict, Any

log = logging.getLogger(__name__)


class PositionTracker:
    """
    持仓跟踪器
    
    管理：
    - 现金余额
    - 持仓列表
    - 已平仓交易记录
    """
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.open_positions: List[Dict] = []
        self.closed_trades: List[Dict] = []
        
    def open_position(
        self,
        entry_date: date,
        entry_price: float,
        legs: List[Dict],
        combo_fill: float
    ) -> Dict:
        """
        开仓
        
        Args:
            entry_date: 开仓日期
            entry_price: 标的价格
            legs: 各腿详情
            combo_fill: 组合成交价
        
        Returns:
            持仓记录
        """
        # 计算成本
        entry_cost = abs(combo_fill) * 100  # 每手100股
        
        # 检查资金
        if entry_cost > self.cash:
            log.warning(f"Insufficient cash: ${self.cash:,.0f} < ${entry_cost:,.0f}")
            return None
        
        # 扣减现金
        self.cash -= entry_cost
        
        position = {
            'id': len(self.open_positions),
            'entry_date': entry_date,
            'entry_stock_price': entry_price,
            'legs': legs,
            'entry_cost': entry_cost,
            'combo_fill': combo_fill,
        }
        
        self.open_positions.append(position)
        
        log.info(f"Opened position on {entry_date}: ${entry_cost:,.0f}, remaining cash: ${self.cash:,.0f}")
        
        return position
    
    def close_position(
        self,
        position: Dict,
        exit_date: date,
        exit_price: float,
        close_value: float,
        pnl: float,
        close_type: str
    ):
        """平仓"""
        # 返还现金
        self.cash += close_value
        
        # 从持仓列表移除
        if position in self.open_positions:
            self.open_positions.remove(position)
        
        # 记录已平仓交易
        trade = {
            'entry_date': position['entry_date'],
            'exit_date': exit_date,
            'entry_price': position['entry_stock_price'],
            'exit_price': exit_price,
            'entry_cost': position['entry_cost'],
            'close_value': close_value,
            'pnl': pnl,
            'pnl_pct': pnl / position['entry_cost'] if position['entry_cost'] > 0 else 0,
            'legs': position['legs'],
            'close_type': close_type,
        }
        
        self.closed_trades.append(trade)
        
        log.info(f"Closed position on {exit_date}: PnL=${pnl:,.0f} ({trade['pnl_pct']:+.1%}), type={close_type}")
        
        return trade
    
    def get_total_equity(self, positions_mtm: float = 0) -> float:
        """获取总权益 = 现金 + 持仓市值"""
        return self.cash + positions_mtm
    
    def get_position_count(self) -> int:
        """获取当前持仓数量"""
        return len(self.open_positions)
