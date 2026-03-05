"""
回测 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import asyncio
import json

from app.database import get_db
from app.models.backtest import BacktestCreate, BacktestResponse, BacktestProgress, BacktestSummary
from app.services.backtest_service import BacktestService
from app.tasks.backtest_tasks import run_backtest_task

router = APIRouter()


@router.post("/backtests", response_model=BacktestResponse)
async def create_backtest(
    data: BacktestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建回测任务"""
    service = BacktestService(db)
    backtest = service.create_backtest(data)
    
    # 异步启动回测
    run_backtest_task.delay(str(backtest.id))
    
    return backtest


@router.get("/backtests", response_model=List[BacktestResponse])
async def list_backtests(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取回测列表"""
    service = BacktestService(db)
    return service.list_backtests(skip, limit)


@router.get("/backtests/{backtest_id}", response_model=BacktestResponse)
async def get_backtest(
    backtest_id: UUID,
    db: Session = Depends(get_db)
):
    """获取回测详情"""
    service = BacktestService(db)
    backtest = service.get_backtest(backtest_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="回测不存在")
    return backtest


@router.delete("/backtests/{backtest_id}")
async def delete_backtest(
    backtest_id: UUID,
    db: Session = Depends(get_db)
):
    """删除回测"""
    service = BacktestService(db)
    success = service.delete_backtest(backtest_id)
    if not success:
        raise HTTPException(status_code=404, detail="回测不存在")
    return {"message": "删除成功"}


@router.get("/backtests/{backtest_id}/progress")
async def get_progress_stream(backtest_id: UUID):
    """SSE 实时推送回测进度"""
    async def event_generator():
        from app.config import settings
        import redis
        
        r = redis.from_url(settings.REDIS_URL)
        channel = f"backtest:{backtest_id}:progress"
        pubsub = r.pubsub()
        pubsub.subscribe(channel)
        
        try:
            while True:
                message = pubsub.get_message(timeout=1)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    # 如果完成或失败，结束流
                    if data.get("status") in ["completed", "failed"]:
                        break
                        
                await asyncio.sleep(0.1)
        finally:
            pubsub.unsubscribe()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.post("/backtests/{backtest_id}/cancel")
async def cancel_backtest(
    backtest_id: UUID,
    db: Session = Depends(get_db)
):
    """取消运行中的回测"""
    # TODO: 实现取消逻辑
    return {"message": "已取消"}
