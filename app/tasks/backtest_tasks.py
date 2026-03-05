"""
回测异步任务 - 集成新引擎
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.celery_app import celery_app
from app.database import SessionLocal
from app.config import settings
from app.models import Backtest
from app.models.backtest import BacktestStatus

import redis

log = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def run_backtest_task(self, backtest_id: str):
    """
    执行回测任务
    
    这是核心任务，使用新的 BacktestEngine
    """
    db = SessionLocal()
    redis_client = redis.from_url(settings.REDIS_URL)
    
    try:
        # 获取回测配置
        backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if not backtest:
            raise ValueError(f"回测 {backtest_id} 不存在")
        
        # 更新状态为运行中
        backtest.status = BacktestStatus.RUNNING
        backtest.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        
        log.info(f"开始回测任务: {backtest_id}")
        
        # 发布进度更新的函数
        def publish_progress(progress: int, message: str, **kwargs):
            data = {
                "backtest_id": backtest_id,
                "status": "running",
                "progress": progress,
                "message": message,
                **kwargs
            }
            redis_client.publish(f"backtest:{backtest_id}:progress", json.dumps(data))
            log.info(f"Progress {progress}%: {message}")
        
        # ========== 导入新引擎 ==========
        from app.core.engine.config import SimulationConfig
        from app.core.engine.simulator import BacktestEngine
        from app.core.data.loader import DataStore
        
        # 1. 解析配置
        config = SimulationConfig(**backtest.strategy_config)
        
        # 2. 加载数据
        data_dir = Path(settings.DATA_DIR) / backtest.symbols[0].lower()
        data_store = DataStore(data_dir, symbol=backtest.symbols[0])
        
        if not data_store.load():
            raise ValueError(f"数据加载失败: {data_dir}")
        
        publish_progress(5, "数据加载完成")
        
        # 3. 创建回测引擎
        engine = BacktestEngine(config, data_store)
        
        # 4. 运行回测
        from datetime import date as dt_date
        start = dt_date.fromisoformat(backtest.start_date.isoformat()[:10])
        end = dt_date.fromisoformat(backtest.end_date.isoformat()[:10])
        
        results = engine.run(
            start_date=start,
            end_date=end,
            progress_callback=publish_progress
        )
        
        # 5. 保存结果到数据库
        backtest.status = BacktestStatus.COMPLETED
        backtest.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        backtest.total_return = results['total_return']
        backtest.sharpe_ratio = results['sharpe_ratio']
        backtest.max_drawdown = results['max_drawdown']
        backtest.win_rate = results['win_rate']
        backtest.total_trades = results['total_trades']
        backtest.equity_curve = results['equity_curve']
        
        # 保存交易记录
        from app.models import Trade
        for trade_data in results['trades']:
            trade = Trade(
                backtest_id=backtest_id,
                entry_date=datetime.fromisoformat(trade_data['entry_date'].isoformat()) if hasattr(trade_data['entry_date'], 'isoformat') else trade_data['entry_date'],
                exit_date=datetime.fromisoformat(trade_data['exit_date'].isoformat()) if hasattr(trade_data['exit_date'], 'isoformat') else trade_data['exit_date'],
                entry_price=trade_data['entry_price'],
                exit_price=trade_data['exit_price'],
                pnl=trade_data['pnl'],
                pnl_pct=trade_data['pnl_pct'],
                legs=trade_data['legs'],
                close_type=trade_data['close_type']
            )
            db.add(trade)
        
        db.commit()
        
        # 发布完成消息
        redis_client.publish(
            f"backtest:{backtest_id}:progress",
            json.dumps({
                "backtest_id": backtest_id,
                "status": "completed",
                "progress": 100,
                "message": f"回测完成: 总收益 {results['total_return']:.2%}",
                "total_return": results['total_return'],
                "sharpe_ratio": results['sharpe_ratio']
            })
        )
        
        log.info(f"回测任务完成: {backtest_id}, 总收益: {results['total_return']:.2%}")
        
        return {
            "status": "completed",
            "backtest_id": backtest_id,
            "total_return": results['total_return'],
            "sharpe_ratio": results['sharpe_ratio']
        }
        
    except Exception as exc:
        log.error(f"回测任务失败: {backtest_id}, 错误: {exc}")

        # 更新失败状态
        if backtest:
            backtest.status = BacktestStatus.FAILED
            backtest.error_message = str(exc)
            backtest.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
        
        # 发布失败消息
        redis_client.publish(
            f"backtest:{backtest_id}:progress",
            json.dumps({
                "backtest_id": backtest_id,
                "status": "failed",
                "progress": 0,
                "message": f"回测失败: {str(exc)}"
            })
        )
        
        # 重试逻辑
        raise self.retry(exc=exc, countdown=60)
        
    finally:
        db.close()
        redis_client.close()
