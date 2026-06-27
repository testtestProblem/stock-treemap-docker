"""APScheduler 實例與啟動/停止函式。"""
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler.jobs import daily_settlement_job, snapshot_job

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
        max_instances=1,
        next_run_time=datetime.now(),
    )

    # 每日結算：台灣時間 15:40，weekday=0-4（週一到週五）
    scheduler.add_job(
        daily_settlement_job,
        trigger="cron",
        hour=15,
        minute=40,
        day_of_week="mon-fri",
        id="daily_settlement_job",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info("APScheduler 已啟動：snapshot_job 每 2 分鐘、daily_settlement_job 每日 15:40")


def stop() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler 已停止")
