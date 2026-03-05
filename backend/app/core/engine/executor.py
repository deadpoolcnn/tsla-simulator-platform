"""
交易执行 - 从 sim_executor.py 迁移

职责：
1. 模拟买入执行
2. 模拟卖出执行
3. 持仓盯市估值 (MTM)
"""
import logging
from datetime import date
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

from app.core.engine.config import SimulationConfig
from app.core.data.loader import DataStore

log = logging.getLogger(__name__)


def execute_buy(
    data_store: DataStore,
    sim_date: date,
    strategy_result,
    config: SimulationConfig
) -> Dict[str, Any]:
    """
    模拟买入执行
    
    Args:
        data_store: 数据存储
        sim_date: 模拟日期
        strategy_result: 策略评估结果 (包含 best_legs)
        config: 策略配置
    
    Returns:
        {
            'success': bool,
            'combo_mid': float,
            'combo_fill': float,
            'legs_detail': List[Dict]
        }
    """
    if not strategy_result or not strategy_result.best_legs:
        return {'success': False, 'combo_mid': 0, 'combo_fill': 0, 'legs_detail': []}
    
    legs = strategy_result.best_legs
    combo_mid = 0.0
    legs_detail = []
    
    for leg in legs:
        price = leg.get('initial_price', 0)
        pos = leg['pos']
        combo_mid += price * pos
        
        legs_detail.append({
            'type': leg['type'],
            'strike': leg['K'],
            'dte': leg['T'],
            'pos': pos,
            'mid': price,
            'bid': leg.get('bid', 0),
            'ask': leg.get('ask', 0),
            'delta': leg.get('delta', 0),
            'iv': leg.get('iv', 0),
            'expiry': leg.get('expiry', ''),
        })
    
    # 模拟滑点
    n_legs = len(legs)
    if combo_mid >= 0:
        combo_fill = combo_mid + n_legs * config.slippage
    else:
        combo_fill = combo_mid - n_legs * config.slippage
    
    return {
        'success': True,
        'combo_mid': round(combo_mid, 2),
        'combo_fill': round(combo_fill, 2),
        'legs_detail': legs_detail,
    }


def execute_sell(
    data_store: DataStore,
    sim_date: date,
    position: Dict,
    spot: float,
    close_type: str,
    config: SimulationConfig
) -> Dict[str, Any]:
    """
    模拟卖出执行
    
    Args:
        data_store: 数据存储
        sim_date: 模拟日期
        position: 持仓信息
        spot: 标的价格
        close_type: 平仓类型 (trigger_tp, trigger_sl, expire)
        config: 策略配置
    
    Returns:
        {
            'success': bool,
            'close_value': float,
            'pnl': float
        }
    """
    legs = position.get('legs', [])
    if not legs:
        return {'success': False, 'close_value': 0, 'pnl': 0}
    
    # 简化的平仓逻辑：根据 close_type 使用不同定价
    close_value = 0.0
    
    for leg in legs:
        # 从当日期权数据查找该腿的价格
        # 简化：使用 leg 中存储的 mid 价格
        leg_mid = leg.get('mid', 0)
        leg_pos = leg.get('pos', 0)
        close_value += leg_mid * leg_pos
    
    # 考虑滑点
    n_legs = len(legs)
    if close_value >= 0:
        close_value -= n_legs * config.slippage
    else:
        close_value += n_legs * config.slippage
    
    # 计算 PnL
    entry_cost = position.get('entry_cost', 0)
    # 对于期权组合，close_value 是平仓收入，PnL = close_value - entry_cost
    # 但需要注意正负号（credit spread 的情况）
    pnl = close_value * 100 - entry_cost  # 每手100股
    
    return {
        'success': True,
        'close_value': close_value * 100,
        'pnl': pnl,
    }


def price_position_mtm(
    data_store: DataStore,
    sim_date: date,
    position: Dict,
    spot: float,
    config: SimulationConfig
) -> float:
    """
    持仓盯市估值 (Mark-to-Market)
    
    Args:
        data_store: 数据存储
        sim_date: 模拟日期
        position: 持仓信息
        spot: 当前标的价格
        config: 策略配置
    
    Returns:
        持仓市值
    """
    legs = position.get('legs', [])
    if not legs:
        return 0.0
    
    total_mtm = 0.0
    
    for leg in legs:
        # 从当日期权数据查找该腿的最新价格
        # 简化：尝试从 options 数据查找
        leg_mid = leg.get('mid', 0)  # 简化版，实际应该查询当日数据
        leg_pos = leg.get('pos', 0)
        total_mtm += leg_mid * leg_pos * 100  # 每手100股
    
    return total_mtm
