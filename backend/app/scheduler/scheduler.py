"""APScheduler 實例與啟動/停止函式。"""
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler.jobs import snapshot_job

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Taipei")


def start() -> None:
    """掛載所有排程任務並啟動排程器。"""
    # 全市場快照：每 2 分鐘，啟動後立即執行第一次
    scheduler.add_job(
        snapshot_job,
        trigger="interval",
        minutes=2,
        id="snapshot_job",
        replace_existing=True,
        max_instances=1,        # 避免上一批還沒跑完就啟動下一批
        next_run_time=datetime.now(),
    )
    # 階段 5：daily_settlement_job 於 15:40 觸發
    scheduler.start()
    logger.info("APScheduler 已啟動，snapshot_job 每 2 分鐘執行")


def stop() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler 已停止")
