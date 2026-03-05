"""
期权评估 - 从 sim_option_eval.py 迁移 (简化版框架)

职责：
1. 搜索符合条件的期权组合
2. 评估各组合的收益风险
3. 选择最优组合
"""
import logging
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

from app.core.engine.config import SimulationConfig
from app.core.data.loader import DataStore

log = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """策略评估结果"""
    template: str
    score: float
    best_legs: List[Dict] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)


def run_option_eval(
    data_store: DataStore,
    sim_date: date,
    spot_price: float,
    overall_iv: float,
    iv_rank: float,
    config: SimulationConfig
) -> Optional[StrategyResult]:
    """
    运行期权评估
    
    Args:
        data_store: 数据存储
        sim_date: 模拟日期
        spot_price: 标的价格
        overall_iv: 整体 IV
        iv_rank: IV Rank
        config: 策略配置
    
    Returns:
        StrategyResult 或 None
    """
    results = []
    
    # 评估 Template C (主推)
    if config.is_template_enabled('C'):
        result_c = _eval_template_c(data_store, sim_date, spot_price, iv_rank, config)
        if result_c:
            results.append(result_c)
    
    # 评估 Template A
    if config.is_template_enabled('A'):
        result_a = _eval_template_a(data_store, sim_date, spot_price, iv_rank, config)
        if result_a:
            results.append(result_a)
    
    # 评估 Template D
    if config.is_template_enabled('D'):
        result_d = _eval_template_d(data_store, sim_date, spot_price, iv_rank, config)
        if result_d:
            results.append(result_d)
    
    if not results:
        return None
    
    # 选择得分最高的
    best = max(results, key=lambda x: x.score)
    return best


def pick_best_strategy(results: List[StrategyResult]) -> Optional[StrategyResult]:
    """从多个结果中选择最优"""
    if not results:
        return None
    return max(results, key=lambda x: x.score)


def _eval_template_c(
    data_store: DataStore,
    sim_date: date,
    spot_price: float,
    iv_rank: float,
    config: SimulationConfig
) -> Optional[StrategyResult]:
    """
    评估 Template C - 通用平衡看多策略
    
    5腿组合：
    - Leg1: +Call (ATM, rolling 对象)
    - Leg2: +Put (mid DTE, 买入保护)
    - Leg3: -Put (mid/premium DTE, 卖出收入)
    - Leg4: +Put (far DTE, 远期保护)
    - Leg5: -Put (far/premium DTE, 卖出收入)
    """
    legs = []
    
    cfg = config.tmpl_c_leg1_call
    if cfg.enabled:
        # 查找符合条件的 Call
        leg1 = _find_option_leg(
            data_store, sim_date, spot_price,
            option_type='C',
            delta_range=(cfg.delta_min, cfg.delta_max) if cfg.delta_min else (0.65, 0.75),
            dte_range=(cfg.dte_min, cfg.dte_max) if cfg.dte_min else (20, 27),
            pos=1
        )
        if leg1:
            legs.append(leg1)
    
    # Leg2, Leg3, Leg4, Leg5 类似...
    # 简化版：这里只实现 Leg1 作为示例
    
    if len(legs) < 3:  # 至少需要3条腿
        return None
    
    # 计算组合得分 (简化版)
    score = _calc_strategy_score(legs, spot_price)
    
    return StrategyResult(
        template='C',
        score=score,
        best_legs=legs,
        metrics={'legs_count': len(legs)}
    )


def _eval_template_a(
    data_store: DataStore,
    sim_date: date,
    spot_price: float,
    iv_rank: float,
    config: SimulationConfig
) -> Optional[StrategyResult]:
    """评估 Template A - Put-Skew Calendar"""
    # TODO: 实现 Template A 评估
    return None


def _eval_template_d(
    data_store: DataStore,
    sim_date: date,
    spot_price: float,
    iv_rank: float,
    config: SimulationConfig
) -> Optional[StrategyResult]:
    """评估 Template D - Call-Skew Calendar"""
    # TODO: 实现 Template D 评估
    return None


def _find_option_leg(
    data_store: DataStore,
    sim_date: date,
    spot_price: float,
    option_type: str,
    delta_range: Tuple[float, float],
    dte_range: Tuple[int, int],
    pos: int
) -> Optional[Dict]:
    """
    查找符合条件的期权腿
    
    简化版实现 - 实际应该更复杂
    """
    # 获取期权链
    options = data_store.get_options_chain(sim_date, option_type)
    
    if options.empty:
        return None
    
    # 筛选 DTE
    options['dte'] = (options['expiration'] - pd.to_datetime(sim_date)).dt.days
    mask = (options['dte'] >= dte_range[0]) & (options['dte'] <= dte_range[1])
    candidates = options[mask].copy()
    
    if candidates.empty:
        return None
    
    # 筛选 Delta (简化：使用 delta 列或近似计算)
    if 'delta' in candidates.columns:
        mask = (candidates['delta'] >= delta_range[0]) & (candidates['delta'] <= delta_range[1])
        candidates = candidates[mask]
    
    if candidates.empty:
        return None
    
    # 选择最接近 ATM 的
    candidates['dist_from_atm'] = abs(candidates['strike'] - spot_price)
    best = candidates.loc[candidates['dist_from_atm'].idxmin()]
    
    return {
        'type': option_type,
        'K': float(best['strike']),
        'T': int(best['dte']),
        'pos': pos,
        'mid': float(best.get('mid', (best.get('bid', 0) + best.get('ask', 0)) / 2)),
        'bid': float(best.get('bid', 0)),
        'ask': float(best.get('ask', 0)),
        'delta': float(best.get('delta', 0)),
        'iv': float(best.get('implied_volatility', best.get('iv', 0.3))),
        'expiry': best['expiration'].strftime('%Y-%m-%d') if pd.notna(best['expiration']) else '',
        'initial_price': float(best.get('mid', (best.get('bid', 0) + best.get('ask', 0)) / 2)),
    }


def _calc_strategy_score(legs: List[Dict], spot_price: float) -> float:
    """计算策略得分 (简化版)"""
    # 这里可以实现复杂的评分逻辑
    # 例如：PnL 矩阵、风险调整收益等
    
    # 简化：基于 delta 平衡的得分
    total_delta = sum(leg.get('delta', 0) * leg.get('pos', 0) for leg in legs)
    delta_score = 1.0 - abs(total_delta)  # delta 越接近0越好
    
    # 基于成本的得分
    total_cost = sum(leg.get('mid', 0) * leg.get('pos', 0) for leg in legs)
    cost_score = 1.0 / (1.0 + abs(total_cost))  # 成本越低越好
    
    return delta_score * 0.5 + cost_score * 0.5
