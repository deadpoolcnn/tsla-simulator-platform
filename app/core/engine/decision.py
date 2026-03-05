"""
买入信号判断 - 从 sim_decision.py 迁移

适配 FastAPI 架构，从全局配置改为参数注入
"""
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import List, Tuple, Optional

import pandas as pd
import numpy as np

from app.core.engine.config import SimulationConfig

log = logging.getLogger(__name__)


@dataclass
class Signal:
    """买入信号结果"""
    triggered: bool = False
    price: float = 0.0
    overall_iv: float = 0.0
    conditions_met: List[str] = field(default_factory=list)
    all_check_msgs: List[Tuple[str, bool, str]] = field(default_factory=list)
    mandatory_details: List[Tuple[str, bool, str]] = field(default_factory=list)
    mandatory_failed: List[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class DailyContext:
    """每日上下文数据"""
    avg_volume_20d: float = 0
    avg_volume_5d: float = 0
    avg_volume_15d: float = 0
    avg_volume_3d: float = 0
    prev_volume: float = 0
    prev_close: float = 0
    last_3d_volumes: List[float] = field(default_factory=list)
    high_3d: float = 0
    low_3d: float = 0
    iv_rank: float = 50
    iv_percentile: float = 50


def check_buy_signal(
    today_row: pd.Series,
    ctx: Optional[DailyContext],
    tracker,
    account_balance: float,
    config: SimulationConfig
) -> Signal:
    """
    检查买入信号
    
    Args:
        today_row: 当日 underlying 数据 (close, volume, ImpliedVolatility, ...)
        ctx: DailyContext (基于 sim_date 之前的历史)
        tracker: 持仓跟踪器
        account_balance: 当前可用资金
        config: 策略配置
    
    Returns:
        Signal 对象
    """
    sig = Signal()
    
    price = float(today_row.get('close', 0))
    overall_iv = float(today_row.get('ImpliedVolatility', 0))
    today_volume = float(today_row.get('volume', 0))
    
    if price <= 0 or overall_iv <= 0:
        sig.reason = "invalid price or IV"
        return sig
    
    sig.price = price
    sig.overall_iv = overall_iv
    
    # ========== Phase 1: 7选4 条件检查 ==========
    checks = [
        ("C1", _check_c1(today_volume, ctx, config)),
        ("C2", _check_c2(today_volume, ctx, config)),
        ("C3", _check_c3(price, ctx, config)),
        ("C4", _check_c4(ctx, config)),
        ("C5", _check_c5(ctx, config)),
        ("C6", _check_c6(ctx, config)),
        ("C7", _check_c7(price, ctx, config)),
    ]
    
    met = []
    all_msgs = []
    for label, (ok, msg) in checks:
        all_msgs.append((label, ok, msg))
        if ok:
            met.append(label)
    
    sig.all_check_msgs = all_msgs
    sig.conditions_met = met
    n_met = len(met)
    
    if n_met < config.signal_min_conditions:
        sig.reason = f"conditions {n_met}/7 < {config.signal_min_conditions}: {','.join(met)}"
        return sig
    
    # ========== Phase 2: 5个必要条件 ==========
    failed = []
    
    # M1: IV Rank 和 IV Percentile 范围检查
    iv_rank = ctx.iv_rank if ctx else 50
    iv_pct = ctx.iv_percentile if ctx else 50
    m1_pass = (
        config.iv_rank_min <= iv_rank < config.iv_rank_max and
        config.iv_percentile_min <= iv_pct < config.iv_percentile_max
    )
    if not m1_pass:
        failed.append("M1")
    
    # M4: 资金检查
    m4_pass = account_balance >= config.initial_capital * 0.1  # MIN_LIQUIDITY
    if not m4_pass:
        failed.append("M4")
    
    # M5: Vector Score (简化版，实际实现需要更复杂逻辑)
    # TODO: 实现 vector score 检查
    m5_pass = True
    
    sig.mandatory_details = [
        ("M1", m1_pass, f"IVR={iv_rank:.1f} IVP={iv_pct:.1f}"),
        ("M4", m4_pass, f"cash=${account_balance:,.0f}"),
        ("M5", m5_pass, "vs=enabled"),
    ]
    sig.mandatory_failed = failed
    
    if failed:
        sig.reason = f"mandatory failed: {','.join(failed)}"
        return sig
    
    # ========== All passed ==========
    sig.triggered = True
    sig.reason = f"SIGNAL: {n_met}/7 ({','.join(met)}), all mandatory OK"
    return sig


# ========== 7选4 条件检查函数 ==========

def _check_c1(today_volume: float, ctx: Optional[DailyContext], config: SimulationConfig) -> Tuple[bool, str]:
    """C1: 当日成交量 / 20日均量 >= 1.3"""
    if not ctx or ctx.avg_volume_20d <= 0:
        return False, "C1: 20d_avg=0"
    ratio = today_volume / ctx.avg_volume_20d
    threshold = config.daily_vol_20d_ratio
    if ratio >= threshold:
        return True, f"C1: vol/20d={ratio:.2f}"
    return False, f"C1: vol/20d={ratio:.2f}(<{threshold})"


def _check_c2(today_volume: float, ctx: Optional[DailyContext], config: SimulationConfig) -> Tuple[bool, str]:
    """C2: 当日成交量 / 5日均量 >= 1.3"""
    if not ctx or ctx.avg_volume_5d <= 0:
        return False, "C2: 5d_avg=0"
    ratio = today_volume / ctx.avg_volume_5d
    threshold = config.daily_vol_5d_ratio
    if ratio >= threshold:
        return True, f"C2: vol/5d={ratio:.2f}"
    return False, f"C2: vol/5d={ratio:.2f}(<{threshold})"


def _check_c3(price: float, ctx: Optional[DailyContext], config: SimulationConfig) -> Tuple[bool, str]:
    """C3: 当前股价偏离昨收 >= +-1.8%"""
    prev_close = ctx.prev_close if ctx else 0
    if prev_close <= 0:
        return False, "C3: prev_close=0"
    pct = (price - prev_close) / prev_close
    threshold = config.price_move_threshold
    if abs(pct) >= threshold:
        return True, f"C3: move={pct:+.2%}"
    return False, f"C3: move={pct:+.2%}(<+-{threshold:.1%})"


def _check_c4(ctx: Optional[DailyContext], config: SimulationConfig) -> Tuple[bool, str]:
    """C4: 3日均量 / 15日均量 >= 1.10"""
    if not ctx or ctx.avg_volume_15d <= 0:
        return False, "C4: 15d_avg=0"
    ratio = ctx.avg_volume_3d / ctx.avg_volume_15d
    threshold = config.vol_3d_15d_ratio
    if ratio >= threshold:
        return True, f"C4: 3d/15d={ratio:.2f}"
    return False, f"C4: ratio={ratio:.2f}(<{threshold})"


def _check_c5(ctx: Optional[DailyContext], config: SimulationConfig) -> Tuple[bool, str]:
    """C5: 上一交易日成交量 / 5日均量 >= 1.15"""
    if not ctx or ctx.avg_volume_5d <= 0:
        return False, "C5: 5d_avg=0"
    ratio = ctx.prev_volume / ctx.avg_volume_5d
    threshold = config.vol_prev_5d_ratio
    if ratio >= threshold:
        return True, f"C5: prev/5d={ratio:.2f}"
    return False, f"C5: ratio={ratio:.2f}(<{threshold})"


def _check_c6(ctx: Optional[DailyContext], config: SimulationConfig) -> Tuple[bool, str]:
    """C6: 过去连续3个交易日成交量递减"""
    if not ctx:
        return False, "C6: no context"
    vols = ctx.last_3d_volumes
    if len(vols) < 3:
        return False, "C6: need 3 days"
    if vols[0] > vols[1] > vols[2]:
        return True, f"C6: shrinking {vols[0]:.0f}>{vols[1]:.0f}>{vols[2]:.0f}"
    return False, "C6: not shrinking"


def _check_c7(price: float, ctx: Optional[DailyContext], config: SimulationConfig) -> Tuple[bool, str]:
    """C7: 过去3天 high 或 low 与现价偏差 <= 5%"""
    if not ctx or ctx.high_3d <= 0 or ctx.low_3d <= 0 or price <= 0:
        return False, "C7: no HL data"
    dev_high = abs(price - ctx.high_3d) / price
    dev_low = abs(price - ctx.low_3d) / price
    threshold = config.price_hl_deviation
    if dev_high <= threshold or dev_low <= threshold:
        return True, f"C7: dev_high={dev_high:.2%}, dev_low={dev_low:.2%}"
    return False, f"C7: dev_high={dev_high:.2%}, dev_low={dev_low:.2%}(>{threshold:.0%})"
