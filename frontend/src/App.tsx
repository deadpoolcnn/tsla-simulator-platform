import { Routes, Route } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import { Link, useLocation } from 'react-router-dom'
import { DashboardOutlined, PlayCircleOutlined, BarChartOutlined, DatabaseOutlined } from '@ant-design/icons'
import Home from './pages/Home'
import Backtest from './pages/Backtest'
import Strategies from './pages/Strategies'
import Reports from './pages/Reports'

const { Header, Content, Sider } = Layout

function App() {
  const location = useLocation()
  
  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: <Link to="/">首页</Link> },
    { key: '/strategies', icon: <BarChartOutlined />, label: <Link to="/strategies">策略配置</Link> },
    { key: '/backtest', icon: <PlayCircleOutlined />, label: <Link to="/backtest">回测运行</Link> },
    { key: '/reports', icon: <DatabaseOutlined />, label: <Link to="/reports">报告中心</Link> },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '20px' }}>TSLA Simulator</h1>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content style={{ background: '#fff', padding: 24, margin: 0, minHeight: 280 }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/strategies" element={<Strategies />} />
              <Route path="/backtest" element={<Backtest />} />
              <Route path="/reports" element={<Reports />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default App
