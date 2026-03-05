import api from './index'

export interface BacktestCreate {
  name: string
  symbols: string[]
  start_date: string
  end_date: string
  strategy_config: {
    template: string
    initial_capital: number
    [key: string]: any
  }
}

export const getBacktests = () => api.get('/backtests').then(res => res.data)

export const getBacktest = (id: string) => api.get(`/backtests/${id}`).then(res => res.data)

export const createBacktest = (data: BacktestCreate) => 
  api.post('/backtests', data).then(res => res.data)

export const deleteBacktest = (id: string) => 
  api.delete(`/backtests/${id}`).then(res => res.data)

export const getBacktestProgress = (id: string) => {
  // SSE 连接
  return new EventSource(`/api/v1/backtests/${id}/progress`)
}

export const getBacktestSummary = (id: string) => 
  api.get(`/backtests/${id}/report/summary`).then(res => res.data)

export const getEquityCurve = (id: string) => 
  api.get(`/backtests/${id}/report/equity-curve`).then(res => res.data)

export const getTrades = (id: string) => 
  api.get(`/backtests/${id}/report/trades`).then(res => res.data)
