import { useState } from 'react'
import { Card, Form, Input, DatePicker, Button, Select, InputNumber, Switch, message } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { createBacktest } from '../api/backtest'

const { RangePicker } = DatePicker
const { Option } = Select

function Backtest() {
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      const [startDate, endDate] = values.dateRange
      
      const payload = {
        name: values.name,
        symbols: [values.symbol],
        start_date: startDate.format('YYYY-MM-DD'),
        end_date: endDate.format('YYYY-MM-DD'),
        strategy_config: {
          template: values.template,
          initial_capital: values.initial_capital,
          signal_min_conditions: values.signal_min_conditions,
          rolling_profit_enabled: values.rolling_profit_enabled,
          rolling_profit_start_pct: values.rolling_profit_start_pct,
          rolling_profit_step_pct: values.rolling_profit_step_pct,
          rolling_profit_final_pct: values.rolling_profit_final_pct,
        }
      }
      
      await createBacktest(payload)
      message.success('回测任务已创建')
      form.resetFields()
    } catch (error) {
      message.error('创建失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>创建回测</h2>
      
      <Card title="回测配置" style={{ marginTop: 24 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            symbol: 'TSLA',
            template: 'C',
            initial_capital: 100000,
            signal_min_conditions: 4,
            rolling_profit_enabled: true,
            rolling_profit_start_pct: 0.07,
            rolling_profit_step_pct: 0.03,
            rolling_profit_final_pct: 0.80,
          }}
        >
          <Form.Item
            name="name"
            label="回测名称"
            rules={[{ required: true, message: '请输入回测名称' }]}
          >
            <Input placeholder="例如：TSLA 2024 Template C" />
          </Form.Item>

          <Form.Item
            name="symbol"
            label="标的股票"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="TSLA">TSLA - Tesla</Option>
              <Option value="PLTR">PLTR - Palantir</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="dateRange"
            label="回测区间"
            rules={[{ required: true, message: '请选择回测区间' }]}
          >
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="template"
            label="策略模板"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="A">Template A - Put-Skew Calendar</Option>
              <Option value="C">Template C - 通用平衡看多 (推荐)</Option>
              <Option value="D">Template D - Call-Skew Calendar</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="initial_capital"
            label="初始资金"
          >
            <InputNumber
              style={{ width: '100%' }}
              formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value!.replace(/\$\s?|(,*)/g, '')}
              min={10000}
              step={10000}
            />
          </Form.Item>

          <Form.Item
            name="signal_min_conditions"
            label="信号条件 (7选4)"
            tooltip="至少需要满足的条件数量"
          >
            <InputNumber min={1} max={7} />
          </Form.Item>

          <Form.Item
            name="rolling_profit_enabled"
            label="启用滚动获利"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item shouldUpdate={(prev, curr) => prev.rolling_profit_enabled !== curr.rolling_profit_enabled}>
            {({ getFieldValue }) =>
              getFieldValue('rolling_profit_enabled') ? (
                <>
                  <Form.Item name="rolling_profit_start_pct" label="起始涨幅">
                    <InputNumber min={0} max={1} step={0.01} formatter={v => `${(v! * 100).toFixed(0)}%`} />
                  </Form.Item>
                  <Form.Item name="rolling_profit_step_pct" label="步进涨幅">
                    <InputNumber min={0} max={1} step={0.01} formatter={v => `${(v! * 100).toFixed(0)}%`} />
                  </Form.Item>
                  <Form.Item name="rolling_profit_final_pct" label="完全平仓涨幅">
                    <InputNumber min={0} max={2} step={0.01} formatter={v => `${(v! * 100).toFixed(0)}%`} />
                  </Form.Item>
                </>
              ) : null
            }
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<PlayCircleOutlined />}
              loading={loading}
              size="large"
            >
              开始回测
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Backtest
