"""市場相關端點。

GET /api/market/treemap           — 階段 4 實作
GET /api/market/kbars             — 階段 4 實作
GET /api/market/snapshot-status   — 階段 2 實作（開發除錯用）
"""
from fastapi import APIRouter

from app.services.snapshot_store import get_status

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/snapshot-status")
def snapshot_status():
    return get_status()


@router.get("/treemap")
def get_treemap(mode: str = "market"):
    # TODO 階段 4 實作
    return {"message": "階段 4 尚未實作", "mode": mode}


@router.get("/kbars")
def get_kbars(code: str, start: str = "", end: str = ""):
    # TODO 階段 4 實作
    return {"message": "階段 4 尚未實作", "code": code}
