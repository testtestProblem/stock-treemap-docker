"""APScheduler 實例與啟動/停止函式。

階段 2 實作排程任務掛載。
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone="Asia/Taipei")


def start() -> None:
    # TODO 階段 2 掛載 snapshot_job
    # TODO 階段 5 掛載 daily_settlement_job
    scheduler.start()


def stop() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
