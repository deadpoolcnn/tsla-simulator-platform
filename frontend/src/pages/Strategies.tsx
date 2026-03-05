import { Card, Descriptions, Switch, InputNumber, Form, Button, message } from 'antd'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getStrategyTemplates, getDefaultConfig, updateStrategyConfig } from '../api/strategy'

function Strategies() {
  const { data: templates } = useQuery({
    queryKey: ['strategy-templates'],
    queryFn: getStrategyTemplates
  })

  const { data: defaultConfig } = useQuery({
    queryKey: ['default-config'],
    queryFn: getDefaultConfig
  })

  return (
    <div>
      <h2>策略配置</h2>
      
      <Card title="策略模板" style={{ marginTop: 24 }}>
        {templates?.map((template: any) => (
          <Card.Grid
            key={template.id}
            style={{
              width: '33.33%',
              backgroundColor: template.enabled ? '#f6ffed' : '#f5f5f5'
            }}
          >
            <h4>{template.name}</h4>
            <p>{template.description}</p>
            <p>状态: {template.enabled ? '✅ 启用' : '❌ 禁用'}</p>
          </Card.Grid>
        ))}
      </Card>

      {defaultConfig && (
        <Card title="Template C 配置" style={{ marginTop: 24 }}>
          <Descriptions bordered column={2}>
            <Descriptions.Item label="初始资金">${defaultConfig.initial_capital?.toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label="信号条件">{defaultConfig.signal_min_conditions}/7</Descriptions.Item>
            <Descriptions.Item label="滚动获利">{defaultConfig.rolling_profit_enabled ? '启用' : '禁用'}</Descriptions.Item>
            <Descriptions.Item label="起始涨幅">{(defaultConfig.rolling_profit_start_pct * 100).toFixed(0)}%</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </div>
  )
}

export default Strategies
