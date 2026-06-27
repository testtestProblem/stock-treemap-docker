from __future__ import annotations

from pydantic import BaseModel


# ── Treemap ──────────────────────────────────────────────────────────────────

class TreemapStock(BaseModel):
    """葉節點：單一個股快照資料。"""
    code: str
    name: str
    industry: str
    close: float
    change_price: float
    change_rate: float        # 漲跌幅 %
    total_volume: int
    total_amount: float       # 成交值（作為 D3 treemap sizing weight）


class IndustryNode(BaseModel):
    """中間節點：產業群。"""
    name: str
    children: list[TreemapStock]


class TreemapResponse(BaseModel):
    """D3 treemap 所需的二層階層結構。"""
    mode: str                 # "market" | "watchlist"
    name: str                 # 根節點標籤
    children: list[IndustryNode]
    last_updated: str | None  # snapshot_store 最後更新時間


# ── Kbars ────────────────────────────────────────────────────────────────────

class KbarItem(BaseModel):
    ts: int       # Unix timestamp（秒）
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float


class KbarsResponse(BaseModel):
    code: str
    start: str
    end: str
    bars: list[KbarItem]
    from_cache: bool = False


# ── Watchlist ────────────────────────────────────────────────────────────────

class WatchlistResponse(BaseModel):
    codes: list[str]


class WatchlistUpdate(BaseModel):
    codes: list[str]
