"""
报告 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.models.backtest import BacktestSummary, EquityCurvePoint, TradeResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/backtests/{backtest_id}/report/summary", response_model=BacktestSummary)
async def get_report_summary(
    backtest_id: UUID,
    db: Session = Depends(get_db)
):
    """获取回测摘要"""
    service = ReportService(db)
    summary = service.get_summary(backtest_id)
    if not summary:
        raise HTTPException(status_code=404, detail="回测不存在或未完成")
    return summary


@router.get("/backtests/{backtest_id}/report/equity-curve", response_model=List[EquityCurvePoint])
async def get_equity_curve(
    backtest_id: UUID,
    db: Session = Depends(get_db)
):
    """获取权益曲线数据"""
    service = ReportService(db)
    return service.get_equity_curve(backtest_id)


@router.get("/backtests/{backtest_id}/report/trades", response_model=List[TradeResponse])
async def get_trades(
    backtest_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取交易记录"""
    service = ReportService(db)
    return service.get_trades(backtest_id, skip, limit)


@router.get("/backtests/{backtest_id}/report/download")
async def download_report(
    backtest_id: UUID,
    format: str = "pdf",  # pdf, excel, csv
    db: Session = Depends(get_db)
):
    """下载回测报告"""
    # TODO: 实现报告导出
    return {"message": "报告导出功能开发中"}
