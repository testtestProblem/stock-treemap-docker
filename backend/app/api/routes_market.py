"""市場相關端點。

GET /api/market/treemap           — 階段 4 實作
GET /api/market/kbars             — 階段 4 實作
GET /api/market/snapshot-status   — 階段 2 實作（開發除錯用）
"""
from fastapi import APIRouter

from app.services import snapshot_store, stock_universe

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/snapshot-status")
def snapshot_status():
    status = snapshot_store.get_status()
    status["universe_total"] = len(stock_universe.get_universe())
    return status


@router.get("/treemap")
def get_treemap(mode: str = "market"):
    # TODO 階段 4 實作
    return {"message": "階段 4 尚未實作", "mode": mode}


@router.get("/kbars")
def get_kbars(code: str, start: str = "", end: str = ""):
    # TODO 階段 4 實作
    return {"message": "階段 4 尚未實作", "code": code}
