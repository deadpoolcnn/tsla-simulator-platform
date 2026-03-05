"""
回测引擎入口 - 从 run_simulation.py 迁移

核心职责：
1. 加载配置和数据
2. 遍历日期执行回测
3. 调用决策、评估、执行模块
4. 生成结果并推送进度
"""
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
import pandas as pd
import numpy as np

from app.core.engine.config import SimulationConfig
from app.core.engine.decision import check_buy_signal
from app.core.engine.option_eval import run_option_eval, pick_best_strategy
from app.core.engine.executor import execute_buy, execute_sell, price_position_mtm
from app.core.engine.position_tracker import PositionTracker
from app.core.data.loader import DataStore

log = logging.getLogger("simulator")


class BacktestEngine:
    """
    回测引擎 - 替代原有的 run_simulation.py
    
    用法:
        engine = BacktestEngine(config, data_store)
        results = engine.run(start_date, end_date, progress_callback)
    """
    
    def __init__(
        self,
        config: SimulationConfig,
        data_store: DataStore,
    ):
        self.config = config
        self.data_store = data_store
        self.tracker = PositionTracker(config.initial_capital)
        
        # 每日状态记录
        self.daily_records: List[Dict] = []
        self.trades: List[Dict] = []
        
    def run(
        self,
        start_date: date,
        end_date: date,
        progress_callback: Optional[Callable[[int, str, Dict], None]] = None
    ) -> Dict[str, Any]:
        """
        执行回测
        
        Args:
            start_date: 回测开始日期
            end_date: 回测结束日期
            progress_callback: 进度回调函数 (progress_pct, message, extra_data)
        
        Returns:
            {
                'total_return': float,
                'sharpe_ratio': float,
                'max_drawdown': float,
                'win_rate': float,
                'total_trades': int,
                'equity_curve': List[Dict],
                'trades': List[Dict],
                'daily_records': List[Dict]
            }
        """
        total_days = (end_date - start_date).days + 1
        current_day = 0
        
        log.info(f"开始回测: {start_date} ~ {end_date}, 初始资金: ${self.config.initial_capital:,.0f}")
        
        # 遍历每个交易日
        sim_date = start_date
        while sim_date <= end_date:
            current_day += 1
            progress = int((current_day / total_days) * 100)
            
            # 推送进度
            if progress_callback:
                progress_callback(
                    progress,
                    f"Processing {sim_date}",
                    {
                        'current_date': sim_date.isoformat(),
                        'current_capital': self.tracker.get_total_equity(),
                        'open_positions': len(self.tracker.open_positions)
                    }
                )
            
            # 执行单日回测
            self._run_single_day(sim_date)
            
            sim_date += timedelta(days=1)
        
        # 回测结束，强制平仓所有持仓
        self._close_all_positions(end_date)
        
        # 生成报告
        results = self._generate_results()
        
        log.info(f"回测完成: 总收益 {results['total_return']:.2%}, 交易次数 {results['total_trades']}")
        
        return results
    
    def _run_single_day(self, sim_date: date):
        """执行单日回测逻辑"""
        # 1. 获取当日标的股票数据
        underlying = self.data_store.get_underlying(sim_date)
        if underlying is None:
            return
        
        # 2. 获取当日期权链数据
        options_df = self.data_store.get_options_chain(sim_date)
        if options_df.empty:
            return
        
        # 3. 检查财报黑名单
        if self._is_earnings_blackout(sim_date, underlying):
            return
        
        # 4. 获取当日上下文 (用于信号判断)
        context = self.data_store.get_daily_context(sim_date, lookback_days=130)
        
        # 5. 检查买入信号
        signal = check_buy_signal(
            today_row=underlying,
            ctx=context,
            tracker=self.tracker,
            account_balance=self.tracker.cash,
            config=self.config
        )
        
        if signal.triggered:
            # 6. 期权评估 - 寻找最优组合
            strategy_result = run_option_eval(
                data_store=self.data_store,
                sim_date=sim_date,
                spot_price=signal.price,
                overall_iv=signal.overall_iv,
                iv_rank=context.iv_rank if context else 50,
                config=self.config
            )
            
            if strategy_result and strategy_result.best_legs:
                # 7. 执行买入
                buy_result = execute_buy(
                    data_store=self.data_store,
                    sim_date=sim_date,
                    strategy_result=strategy_result,
                    config=self.config
                )
                
                if buy_result['success']:
                    self.tracker.open_position(
                        entry_date=sim_date,
                        entry_price=signal.price,
                        legs=buy_result['legs_detail'],
                        combo_fill=buy_result['combo_fill']
                    )
        
        # 8. 检查持仓止盈止损
        self._check_positions_exit(sim_date, underlying)
        
        # 9. 日终估值
        self._daily_mtm(sim_date, underlying)
    
    def _check_positions_exit(self, sim_date: date, underlying: pd.Series):
        """检查持仓是否需要平仓"""
        close_price = underlying['close']
        high = underlying['high']
        low = underlying['low']
        
        for position in self.tracker.open_positions[:]:
            # 计算触发价
            entry = position['entry_stock_price']
            template = position.get('template', 'C')
            tp_pct, sl_pct = self.config.get_tp_sl(template)
            
            trigger_high = entry * (1 + tp_pct)
            trigger_low = entry * (1 - sl_pct)
            
            close_type = None
            
            # 检查止盈
            if high >= trigger_high:
                close_type = 'trigger_tp'
            # 检查止损
            elif low <= trigger_low:
                close_type = 'trigger_sl'
            # 检查到期
            elif self._is_position_expired(position, sim_date):
                close_type = 'expire'
            
            if close_type:
                # 执行平仓
                sell_result = execute_sell(
                    data_store=self.data_store,
                    sim_date=sim_date,
                    position=position,
                    spot=close_price,
                    close_type=close_type,
                    config=self.config
                )
                
                if sell_result['success']:
                    self.tracker.close_position(
                        position=position,
                        exit_date=sim_date,
                        exit_price=close_price,
                        close_value=sell_result['close_value'],
                        pnl=sell_result['pnl'],
                        close_type=close_type
                    )
                    self.trades.append({
                        'entry_date': position['entry_date'],
                        'exit_date': sim_date,
                        'entry_price': entry,
                        'exit_price': close_price,
                        'pnl': sell_result['pnl'],
                        'pnl_pct': sell_result['pnl'] / position['entry_cost'],
                        'legs': position['legs'],
                        'close_type': close_type
                    })
    
    def _daily_mtm(self, sim_date: date, underlying: pd.Series):
        """每日盯市估值"""
        spot = underlying['close']
        total_mtm = 0
        
        for position in self.tracker.open_positions:
            mtm = price_position_mtm(
                data_store=self.data_store,
                sim_date=sim_date,
                position=position,
                spot=spot,
                config=self.config
            )
            total_mtm += mtm
        
        # 记录每日状态
        self.daily_records.append({
            'date': sim_date,
            'equity': self.tracker.cash + total_mtm,
            'cash': self.tracker.cash,
            'positions_value': total_mtm,
            'open_positions': len(self.tracker.open_positions)
        })
    
    def _close_all_positions(self, final_date: date):
        """回测结束，强制平仓所有持仓"""
        underlying = self.data_store.get_underlying(final_date)
        if underlying is None:
            return
        
        close_price = underlying['close']
        
        for position in self.tracker.open_positions[:]:
            sell_result = execute_sell(
                data_store=self.data_store,
                sim_date=final_date,
                position=position,
                spot=close_price,
                close_type='expire',
                config=self.config
            )
            
            if sell_result['success']:
                self.tracker.close_position(
                    position=position,
                    exit_date=final_date,
                    exit_price=close_price,
                    close_value=sell_result['close_value'],
                    pnl=sell_result['pnl'],
                    close_type='expire'
                )
    
    def _is_earnings_blackout(self, sim_date: date, underlying: pd.Series) -> bool:
        """检查是否在财报黑名单窗口"""
        if not self.config.earnings_blackout_enabled:
            return False
        
        # 检查 underlying 是否有财报标记
        if 'earnings_after_close' in underlying:
            return bool(underlying['earnings_after_close'])
        return False
    
    def _is_position_expired(self, position: Dict, sim_date: date) -> bool:
        """检查持仓是否到期"""
        for leg in position['legs']:
            expiry = pd.to_datetime(leg['expiry']).date()
            if expiry <= sim_date:
                return True
        return False
    
    def _generate_results(self) -> Dict[str, Any]:
        """生成回测结果报告"""
        if not self.daily_records:
            return {
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'total_trades': 0,
                'equity_curve': [],
                'trades': []
            }
        
        equity_curve = pd.DataFrame(self.daily_records)
        initial = self.config.initial_capital
        final = equity_curve['equity'].iloc[-1]
        
        # 计算收益
        total_return = (final - initial) / initial
        
        # 计算最大回撤
        equity_curve['cummax'] = equity_curve['equity'].cummax()
        equity_curve['drawdown'] = (equity_curve['equity'] - equity_curve['cummax']) / equity_curve['cummax']
        max_drawdown = equity_curve['drawdown'].min()
        
        # 计算夏普比率 (简化版，假设无风险利率为0)
        daily_returns = equity_curve['equity'].pct_change().dropna()
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0
        
        # 计算胜率
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'equity_curve': self.daily_records,
            'trades': self.trades
        }
