import api from './index'

export const getStrategyTemplates = () => 
  api.get('/strategies/templates').then(res => res.data)

export const getConfigSchema = () => 
  api.get('/strategies/config-schema').then(res => res.data)

export const getDefaultConfig = () => 
  api.get('/strategies/default-config').then(res => res.data)

export const updateStrategyConfig = (id: string, config: any) => 
  api.put(`/strategies/${id}/config`, config).then(res => res.data)
