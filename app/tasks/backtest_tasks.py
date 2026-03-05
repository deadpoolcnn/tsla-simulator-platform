"""
回测异步任务 - 集成新引擎
"""
import json
import logging
import math
from datetime import datetime, timezone, date
from pathlib import Path

from app.celery_app import celery_app
from app.database import SessionLocal
from app.config import settings
from app.models import Backtest
from app.models.backtest import BacktestStatus

import redis

log = logging.getLogger(__name__)


def _to_serializable(obj):
    """
    递归将对象转换为 JSON/PostgreSQL 可序列化的 Python 原生类型：
    - date / datetime → ISO 字符串
    - numpy 数值类型 → int / float
    - nan / inf → None
    - list / dict 递归处理
    """
    import numpy as np
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return _to_serializable(obj.tolist())
    return obj


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
        
        # 5. 序列化结果（date / numpy 类型 → Python 原生类型）
        safe_equity_curve = _to_serializable(results['equity_curve'])
        safe_total_return  = _to_serializable(results['total_return'])
        safe_sharpe        = _to_serializable(results['sharpe_ratio'])
        safe_drawdown      = _to_serializable(results['max_drawdown'])
        safe_win_rate      = _to_serializable(results['win_rate'])

        # 5. 保存结果到数据库
        backtest.status = BacktestStatus.COMPLETED
        backtest.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        backtest.total_return = safe_total_return
        backtest.sharpe_ratio = safe_sharpe
        backtest.max_drawdown = safe_drawdown
        backtest.win_rate = safe_win_rate
        backtest.total_trades = int(results['total_trades'])
        backtest.equity_curve = safe_equity_curve
        
        # 保存交易记录
        from app.models import Trade
        for trade_data in results['trades']:
            d = _to_serializable(trade_data)
            # entry_date / exit_date 需要 date 对象写入 Date 列
            entry_d = trade_data['entry_date']
            exit_d  = trade_data['exit_date']
            if isinstance(entry_d, str):
                entry_d = date.fromisoformat(entry_d[:10])
            if isinstance(exit_d, str):
                exit_d = date.fromisoformat(exit_d[:10])
            trade = Trade(
                backtest_id=backtest_id,
                entry_date=entry_d,
                exit_date=exit_d,
                entry_price=d['entry_price'],
                exit_price=d['exit_price'],
                pnl=d['pnl'],
                pnl_pct=d['pnl_pct'],
                legs=d['legs'],
                close_type=d['close_type']
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
                "message": f"回测完成: 总收益 {safe_total_return:.2%}",
                "total_return": safe_total_return,
                "sharpe_ratio": safe_sharpe,
            })
        )
        
        log.info(f"回测任务完成: {backtest_id}, 总收益: {safe_total_return:.2%}")
        
        return {
            "status": "completed",
            "backtest_id": backtest_id,
            "total_return": safe_total_return,
            "sharpe_ratio": safe_sharpe,
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
