import { Card, Row, Col, Statistic } from 'antd'
import { RiseOutlined, FallOutlined, LineChartOutlined } from '@ant-design/icons'

function Home() {
  return (
    <div>
      <h2>欢迎使用 TSLA Simulator</h2>
      <p>期权回测平台 - 前后端分离架构</p>
      
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="今日回测"
              value={5}
              prefix={<LineChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="总收益"
              value={15.2}
              suffix="%"
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="最大回撤"
              value={8.5}
              suffix="%"
              prefix={<FallOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="快速开始" style={{ marginTop: 24 }}>
        <ol>
          <li>在"策略配置"页面配置你的交易策略</li>
          <li>在"回测运行"页面创建新的回测任务</li>
          <li>在"报告中心"查看回测结果和分析</li>
        </ol>
      </Card>
    </div>
  )
}

export default Home
