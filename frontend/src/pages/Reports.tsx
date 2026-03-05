import { useState } from 'react'
import { Card, Table, Tag, Button, Progress, Space } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { getBacktests, deleteBacktest } from '../api/backtest'

function Reports() {
  const { data: backtests, isLoading, refetch } = useQuery({
    queryKey: ['backtests'],
    queryFn: getBacktests
  })

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: Record<string, string> = {
          pending: 'default',
          running: 'processing',
          completed: 'success',
          failed: 'error'
        }
        const labels: Record<string, string> = {
          pending: '等待中',
          running: '运行中',
          completed: '已完成',
          failed: '失败'
        }
        return <Tag color={colors[status]}>{labels[status] || status}</Tag>
      }
    },
    {
      title: '标的',
      dataIndex: 'symbols',
      key: 'symbols',
      render: (symbols: string[]) => symbols?.join(', ')
    },
    {
      title: '区间',
      key: 'dateRange',
      render: (_: any, record: any) => (
        `${record.start_date?.slice(0, 10)} ~ ${record.end_date?.slice(0, 10)}`
      )
    },
    {
      title: '总收益',
      dataIndex: 'total_return',
      key: 'total_return',
      render: (value: number) => value ? `${(value * 100).toFixed(2)}%` : '-'
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpe_ratio',
      key: 'sharpe_ratio',
      render: (value: number) => value?.toFixed(2) || '-'
    },
    {
      title: '最大回撤',
      dataIndex: 'max_drawdown',
      key: 'max_drawdown',
      render: (value: number) => value ? `${(value * 100).toFixed(2)}%` : '-'
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (value: string) => new Date(value).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" onClick={() => handleView(record.id)}>查看</Button>
          <Button type="link" danger onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      )
    }
  ]

  const handleView = (id: string) => {
    // TODO: 跳转到详情页
    console.log('View:', id)
  }

  const handleDelete = async (id: string) => {
    await deleteBacktest(id)
    refetch()
  }

  return (
    <div>
      <h2>回测报告</h2>
      
      <Card style={{ marginTop: 24 }}>
        <Table
          dataSource={backtests}
          columns={columns}
          rowKey="id"
          loading={isLoading}
        />
      </Card>
    </div>
  )
}

export default Reports
