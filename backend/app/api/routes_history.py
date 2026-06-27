"""歷史績效端點。

GET  /api/history/performance      — 回傳三條標準化 % 曲線
POST /api/history/trigger-daily    — 手動觸發每日結算（除錯/補跑用）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.history import PerformanceResponse
from app.services import history_service

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/performance", response_model=PerformanceResponse)
def get_performance(db: Session = Depends(get_db)):
    """回傳我的資產 / 0050 / 2330 三條已標準化（%）的績效曲線。

    以 daily_performance 表的最早一筆為基準（= 0%），後續每日計算累積報酬率。
    """
    return history_service.get_performance(db)


@router.post("/trigger-daily")
async def trigger_daily():
    """手動觸發每日結算排程（除錯 / 補跑用，正式環境可加 Auth 保護）。

    執行 daily_settlement_job：檢查 2330 開盤 → 計算 NAV → 寫入 daily_performance。
    """
    from app.scheduler.jobs import daily_settlement_job
    await daily_settlement_job()
    return {"status": "ok", "message": "daily_settlement_job 已執行，請查看 /api/history/performance"}
