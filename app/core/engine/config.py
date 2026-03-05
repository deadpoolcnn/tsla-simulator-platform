"""
策略配置 - 从 sim_config.py 迁移

将原有的 Python 常量改为 Pydantic 模型，支持从 API 请求动态配置
"""
from pydantic import BaseModel, Field, model_validator
from typing import List, Tuple, Optional, Dict


class LegConfig(BaseModel):
    """单腿配置"""
    enabled: bool = True
    delta_min: Optional[float] = None
    delta_max: Optional[float] = None
    dte_min: Optional[int] = None
    dte_max: Optional[int] = None
    quantity: int = 1


class SimulationConfig(BaseModel):
    """
    回测配置 - 替代原有的 sim_config.py 常量
    
    从 API 请求体中解析，支持动态配置不同回测参数
    """
    
    # ========== 基础配置 ==========
    template: str = Field(default="C", description="策略模板: A, C, D")
    symbols: List[str] = Field(default=["TSLA"])
    initial_capital: float = Field(default=100000, gt=0)
    
    # ========== 信号条件配置 ==========
    signal_min_conditions: int = Field(default=4, ge=1, le=7, description="7选4条件最小满足数")
    price_move_threshold: float = Field(default=0.018, description="股价偏离阈值")
    
    vol_3d_15d_ratio: float = Field(default=1.10)
    vol_prev_5d_ratio: float = Field(default=1.15)
    price_hl_deviation: float = Field(default=0.05)
    
    daily_vol_20d_ratio: float = Field(default=1.3)
    daily_vol_5d_ratio: float = Field(default=1.3)
    
    # ========== IV 筛选配置 ==========
    iv_rank_min: float = Field(default=20)
    iv_rank_max: float = Field(default=80)
    iv_percentile_min: float = Field(default=30)
    iv_percentile_max: float = Field(default=70)
    
    iv_scan_dte_min: int = Field(default=5)
    iv_scan_dte_max: int = Field(default=90)
    iv_scan_offsets: List[int] = Field(default=[5, 20, 45])
    
    # ========== Template A 配置 (Put-Skew) ==========
    tmpl_a_enabled: bool = False
    tmpl_a_short_put_delta: Tuple[float, float] = (-0.15, -0.10)
    tmpl_a_short_put_dte_1: List[int] = Field(default_factory=lambda: list(range(5, 11)))
    tmpl_a_short_put_dte_2: List[int] = Field(default_factory=lambda: list(range(7, 13)))
    tmpl_a_long_put_delta: Tuple[float, float] = (-0.35, -0.25)
    tmpl_a_long_put_dte: List[int] = Field(default_factory=lambda: list(range(20, 31)))
    tmpl_a_atm_call_delta: Tuple[float, float] = (0.45, 0.55)
    tmpl_a_atm_call_dte: List[int] = Field(default_factory=lambda: list(range(30, 41)))
    tmpl_a_total_delta: Tuple[float, float] = (-0.05, 0.05)
    
    # ========== Template C 配置 (主推) ==========
    tmpl_c_enabled: bool = True
    
    # 5条腿配置
    tmpl_c_leg1_call: LegConfig = LegConfig(
        enabled=True, delta_min=0.65, delta_max=0.75, dte_min=20, dte_max=27
    )
    tmpl_c_leg2_mid_buy: LegConfig = LegConfig(
        enabled=True, delta_min=-0.45, delta_max=-0.40, dte_min=20, dte_max=30
    )
    tmpl_c_leg3_mid_sell: LegConfig = LegConfig(
        enabled=True, delta_min=-0.20, delta_max=-0.15, dte_min=150, dte_max=210
    )
    tmpl_c_leg4_far_buy: LegConfig = LegConfig(
        enabled=True, delta_min=-0.35, delta_max=-0.25, dte_min=30, dte_max=45
    )
    tmpl_c_leg5_far_sell: LegConfig = LegConfig(
        enabled=True, delta_min=-0.15, delta_max=-0.10, dte_min=150, dte_max=210
    )
    tmpl_c_total_delta: Tuple[float, float] = (0.15, 0.20)
    
    # ========== Template D 配置 (Call-Skew) ==========
    tmpl_d_enabled: bool = False
    tmpl_d_short_call_delta: Tuple[float, float] = (0.20, 0.25)
    tmpl_d_short_call_dte_1: List[int] = Field(default_factory=lambda: list(range(14, 21)))
    tmpl_d_short_call_dte_2: List[int] = Field(default_factory=lambda: list(range(14, 21)))
    tmpl_d_long_call_delta: Tuple[float, float] = (0.45, 0.50)
    tmpl_d_long_call_dte: List[int] = Field(default_factory=lambda: list(range(14, 21)))
    tmpl_d_atm_put_delta: Tuple[float, float] = (-0.50, -0.40)
    tmpl_d_atm_put_dte: List[int] = Field(default_factory=lambda: list(range(30, 41)))
    tmpl_d_total_delta: Tuple[float, float] = (0.0, 0.10)
    
    # ========== 止盈止损配置 ==========
    tmpl_a_tp_pct: float = 0.06
    tmpl_a_sl_pct: float = 0.06
    tmpl_c_tp_pct: float = 0.08
    tmpl_c_sl_pct: float = 0.08
    tmpl_d_tp_pct: float = 0.07
    tmpl_d_sl_pct: float = 0.06
    
    # ========== 滚动获利配置 ==========
    rolling_profit_enabled: bool = True
    rolling_profit_start_pct: float = Field(default=0.07, description="起始涨幅")
    rolling_profit_step_pct: float = Field(default=0.03, description="步进涨幅")
    rolling_profit_final_pct: float = Field(default=0.80, description="完全平仓涨幅")
    
    # ========== 财报黑名单 ==========
    earnings_blackout_enabled: bool = True
    earnings_blackout_pre_days: int = 1
    earnings_blackout_post_days: int = 1
    
    # ========== 执行配置 ==========
    slippage: float = 0.01  # 每腿滑点
    option_multiplier: int = 100
    max_positions: int = 100
    
    # ========== 向量化评分配置 ==========
    vector_score_enabled: bool = True
    vector_score_min_train: int = 100
    vector_score_threshold_quantile: float = 0.0
    
    @model_validator(mode='before')
    @classmethod
    def remap_api_leg_keys(cls, values: Dict) -> Dict:
        """
        将 API 层的短键名映射到引擎的完整键名。
        例如: leg1_call -> tmpl_c_leg1_call
        这样前端/API 传参无需加 tmpl_c_ 前缀。
        """
        if not isinstance(values, dict):
            return values
        leg_map = {
            'leg1_call':    'tmpl_c_leg1_call',
            'leg2_mid_buy': 'tmpl_c_leg2_mid_buy',
            'leg3_mid_sell': 'tmpl_c_leg3_mid_sell',
            'leg4_far_buy': 'tmpl_c_leg4_far_buy',
            'leg5_far_sell': 'tmpl_c_leg5_far_sell',
        }
        for api_key, sim_key in leg_map.items():
            if api_key in values:
                values[sim_key] = values.pop(api_key)
        return values

    def get_tp_sl(self, template: str) -> Tuple[float, float]:
        """获取指定模板的止盈止损比例"""
        mapping = {
            'A': (self.tmpl_a_tp_pct, self.tmpl_a_sl_pct),
            'C': (self.tmpl_c_tp_pct, self.tmpl_c_sl_pct),
            'D': (self.tmpl_d_tp_pct, self.tmpl_d_sl_pct),
        }
        return mapping.get(template, (0.08, 0.08))
    
    def is_template_enabled(self, template: str) -> bool:
        """检查模板是否启用"""
        mapping = {
            'A': self.tmpl_a_enabled,
            'C': self.tmpl_c_enabled,
            'D': self.tmpl_d_enabled,
        }
        return mapping.get(template, False)
