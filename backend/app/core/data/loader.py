"""
数据加载层 - 从 sim_data_loader.py 迁移

职责：
1. 加载 Parquet 数据文件
2. 提供标的股票、期权链查询
3. 计算 IV Rank / IV Percentile
4. 生成 DailyContext
"""
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, List

import pandas as pd
import numpy as np

from app.core.engine.decision import DailyContext

log = logging.getLogger(__name__)


class DataStore:
    """
    数据存储 - 替代 sim_data_loader
    
    加载和管理：
    - underlying.parquet (标的股票数据)
    - options.parquet (期权链数据)
    """
    
    def __init__(self, data_dir: Path, symbol: str = "TSLA"):
        self.data_dir = data_dir
        self.symbol = symbol
        
        # 数据缓存
        self._underlying: Optional[pd.DataFrame] = None
        self._options: Optional[pd.DataFrame] = None
        self._loaded = False
        
    def load(self) -> bool:
        """加载所有数据文件"""
        try:
            # 加载标的股票数据
            underlying_path = self.data_dir / f"underlying_{self.symbol}_with_iv.parquet"
            if underlying_path.exists():
                self._underlying = pd.read_parquet(underlying_path)
                # 确保 date 列是 datetime 类型
                if 'date' in self._underlying.columns:
                    self._underlying['date'] = pd.to_datetime(self._underlying['date'])
                log.info(f"Loaded underlying data: {len(self._underlying)} rows")
            else:
                log.error(f"Underlying file not found: {underlying_path}")
                return False
            
            # 加载期权链数据
            options_path = self.data_dir / f"options_{self.symbol}.parquet"
            if options_path.exists():
                self._options = pd.read_parquet(options_path)
                if 'date' in self._options.columns:
                    self._options['date'] = pd.to_datetime(self._options['date'])
                if 'expiration' in self._options.columns:
                    self._options['expiration'] = pd.to_datetime(self._options['expiration'])
                log.info(f"Loaded options data: {len(self._options)} rows")
            else:
                log.error(f"Options file not found: {options_path}")
                return False
            
            self._loaded = True
            return True
            
        except Exception as e:
            log.error(f"Failed to load data: {e}")
            return False
    
    def get_underlying(self, sim_date: date) -> Optional[pd.Series]:
        """获取指定日期的标的股票数据"""
        if not self._loaded or self._underlying is None:
            return None
        
        mask = self._underlying['date'].dt.date == sim_date
        rows = self._underlying[mask]
        
        if rows.empty:
            return None
        
        return rows.iloc[0]
    
    def get_options_chain(
        self,
        sim_date: date,
        option_type: Optional[str] = None
    ) -> pd.DataFrame:
        """获取指定日期的期权链"""
        if not self._loaded or self._options is None:
            return pd.DataFrame()
        
        mask = self._options['date'].dt.date == sim_date
        
        if option_type:
            mask = mask & (self._options['option_type'] == option_type)
        
        return self._options[mask].copy()
    
    def find_closest_expiry(self, sim_date: date, target_dte: int) -> Optional[date]:
        """找到最接近目标 DTE 的到期日"""
        if not self._loaded or self._options is None:
            return None
        
        # 获取该日期的所有到期日
        mask = self._options['date'].dt.date == sim_date
        expiries = self._options[mask]['expiration'].unique()
        
        if len(expiries) == 0:
            return None
        
        # 计算每个到期日的 DTE
        dtes = [(pd.to_datetime(exp).date(), (pd.to_datetime(exp).date() - sim_date).days) 
                for exp in expiries]
        
        # 找到最接近的
        closest = min(dtes, key=lambda x: abs(x[1] - target_dte))
        return closest[0]
    
    def get_daily_context(self, sim_date: date, lookback_days: int = 130) -> Optional[DailyContext]:
        """
        生成 DailyContext
        
        包含：
        - 成交量均值 (20d, 5d, 15d, 3d)
        - 上一交易日成交量
        - 昨收价
        - 过去3天 high/low
        - IV Rank / IV Percentile
        """
        if not self._loaded or self._underlying is None:
            return None
        
        # 获取历史数据 (sim_date 之前)
        history = self._underlying[self._underlying['date'].dt.date < sim_date].copy()
        
        if len(history) < lookback_days:
            return None
        
        ctx = DailyContext()
        
        # 成交量计算
        if 'volume' in history.columns:
            ctx.avg_volume_20d = history['volume'].tail(20).mean()
            ctx.avg_volume_5d = history['volume'].tail(5).mean()
            ctx.avg_volume_15d = history['volume'].tail(15).mean()
            ctx.avg_volume_3d = history['volume'].tail(3).mean()
            ctx.prev_volume = history['volume'].iloc[-1]
            ctx.last_3d_volumes = history['volume'].tail(3).tolist()
        
        # 价格计算
        if 'close' in history.columns:
            ctx.prev_close = history['close'].iloc[-1]
        
        if 'high' in history.columns:
            ctx.high_3d = history['high'].tail(3).max()
        
        if 'low' in history.columns:
            ctx.low_3d = history['low'].tail(3).min()
        
        # IV Rank / IV Percentile 计算
        if 'ImpliedVolatility' in history.columns:
            current_iv = self.get_underlying(sim_date)
            if current_iv is not None and 'ImpliedVolatility' in current_iv:
                current_iv_value = current_iv['ImpliedVolatility']
                
                # IV Percentile (252天)
                iv_history_252 = history['ImpliedVolatility'].tail(252).dropna()
                if len(iv_history_252) > 0:
                    ctx.iv_percentile = (iv_history_252 < current_iv_value).mean() * 100
                
                # IV Rank (130天)
                iv_history_130 = history['ImpliedVolatility'].tail(130).dropna()
                if len(iv_history_130) > 0:
                    iv_min = iv_history_130.min()
                    iv_max = iv_history_130.max()
                    if iv_max > iv_min:
                        ctx.iv_rank = ((current_iv_value - iv_min) / (iv_max - iv_min)) * 100
        
        return ctx
