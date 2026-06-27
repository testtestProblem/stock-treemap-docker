"""市場相關端點。

GET  /api/market/treemap             — 產業分層 Treemap（讀快取）
GET  /api/market/kbars               — 個股 K 線（TTL 快取）
GET  /api/market/snapshot-status     — 快照狀態（除錯用）
GET  /api/market/watchlist           — 讀取自選清單
PUT  /api/market/watchlist           — 更新自選清單
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import shioaji_client
from app.db.database import get_db
from app.schemas.market import KbarsResponse, TreemapResponse, WatchlistResponse, WatchlistUpdate
from app.services import market_service, snapshot_store, stock_universe, watchlist_service

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/snapshot-status")
def snapshot_status():
    """快照快取狀態（除錯用）。"""
    status = snapshot_store.get_status()
    status["universe_total"] = len(stock_universe.get_universe())
    return status


@router.get("/treemap", response_model=TreemapResponse)
def get_treemap(mode: str = "market", db: Session = Depends(get_db)):
    """回傳 D3 treemap 二層階層資料。

    mode=market    → 全市場（快照快取）
    mode=watchlist → 僅自選清單中的代號
    """
    if mode not in ("market", "watchlist"):
        raise HTTPException(status_code=400, detail="mode 必須為 market 或 watchlist")

    wl = watchlist_service.get_watchlist(db) if mode == "watchlist" else []
    return market_service.build_treemap(mode=mode, watchlist=wl)


@router.get("/kbars", response_model=KbarsResponse)
def get_kbars(code: str, start: str = "", end: str = ""):
    """回傳個股日 K 線（OHLCV），帶 TTL 快取避免重複呼叫 Shioaji。"""
    api = shioaji_client.get_api()
    return market_service.get_kbars(api=api, code=code, start=start, end=end)


@router.get("/watchlist", response_model=WatchlistResponse)
def get_watchlist(db: Session = Depends(get_db)):
    """讀取自選清單。"""
    return WatchlistResponse(codes=watchlist_service.get_watchlist(db))


@router.put("/watchlist", response_model=WatchlistResponse)
def update_watchlist(body: WatchlistUpdate, db: Session = Depends(get_db)):
    """覆寫自選清單（去重保序）。"""
    saved = watchlist_service.set_watchlist(db, body.codes)
    return WatchlistResponse(codes=saved)
