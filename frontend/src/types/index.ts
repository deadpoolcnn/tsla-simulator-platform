// 类型定义

export interface Backtest {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  symbols: string[]
  start_date: string
  end_date: string
  strategy_config: StrategyConfig
  total_return?: number
  sharpe_ratio?: number
  max_drawdown?: number
  win_rate?: number
  total_trades?: number
  created_at: string
  completed_at?: string
}

export interface StrategyConfig {
  template: 'A' | 'C' | 'D'
  initial_capital: number
  signal_min_conditions: number
  rolling_profit_enabled: boolean
  rolling_profit_start_pct: number
  rolling_profit_step_pct: number
  rolling_profit_final_pct: number
  iv_rank_min: number
  iv_rank_max: number
  iv_percentile_min: number
  iv_percentile_max: number
}

export interface Trade {
  id: string
  entry_date: string
  exit_date?: string
  entry_price: number
  exit_price?: number
  pnl?: number
  pnl_pct?: number
  legs: Leg[]
  close_type?: 'trigger' | 'expire' | 'manual'
}

export interface Leg {
  type: 'call' | 'put'
  strike: number
  dte: number
  pos: number
  delta: number
  iv: number
  expiry: string
}

export interface BacktestSummary {
  total_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  total_trades: number
  avg_trade_return: number
  profit_factor?: number
  calmar_ratio?: number
}

export interface EquityPoint {
  date: string
  equity: number
  drawdown: number
  cash: number
  positions_value: number
}
