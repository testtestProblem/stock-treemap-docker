"""市場商業邏輯：Treemap 產業分層組裝、kbars 歷史 K 線（TTL 快取）。

Treemap：
  - 來源：snapshot_store（背景排程每 2 分鐘更新）
  - 結構：root → [IndustryNode → [TreemapStock]]
  - 大小權重：total_amount（成交值），排除 total_amount == 0 的非交易標的
  - 顏色依據：change_rate（漲跌幅 %）

kbars：
  - 快取 key："{code}:{start}:{end}"，TTL = 60 秒
  - 日期預設：start = 60 天前，end = 今日
  - Shioaji 回傳 ts 為 nanoseconds，需除以 1e9 轉為 Unix 秒
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, timedelta

import shioaji as sj

from app.core.cache import kbars_cache
from app.schemas.market import (
    IndustryNode,
    KbarItem,
    KbarsResponse,
    TreemapResponse,
    TreemapStock,
)
from app.services import snapshot_store

logger = logging.getLogger(__name__)


def build_treemap(mode: str, watchlist: list[str]) -> TreemapResponse:
    """從 snapshot_store 組裝 D3 treemap 階層。

    mode='market'    → 全市場快照
    mode='watchlist' → 僅自選清單中的代號
    """
    snap = snapshot_store.get_all()
    status = snapshot_store.get_status()

    if mode == "watchlist" and watchlist:
        snap = {code: snap[code] for code in watchlist if code in snap}

    # 按產業分組，過濾未有成交量的標的
    by_industry: dict[str, list[TreemapStock]] = defaultdict(list)
    for code, s in snap.items():
        if not s.get("total_amount", 0):
            continue
        by_industry[s.get("industry", "其他")].append(
            TreemapStock(
                code=code,
                name=s.get("name", code),
                industry=s.get("industry", "其他"),
                close=s.get("close", 0.0),
                change_price=s.get("change_price", 0.0),
                change_rate=s.get("change_rate", 0.0),
                total_volume=s.get("total_volume", 0),
                total_amount=s.get("total_amount", 0.0),
            )
        )

    # 產業節點按總成交值降冪排序；節點內個股也按成交值排序
    industry_nodes = [
        IndustryNode(
            name=industry,
            children=sorted(stocks, key=lambda x: x.total_amount, reverse=True),
        )
        for industry, stocks in sorted(
            by_industry.items(),
            key=lambda kv: sum(s.total_amount for s in kv[1]),
            reverse=True,
        )
    ]

    return TreemapResponse(
        mode=mode,
        name="全市場" if mode == "market" else "自選清單",
        children=industry_nodes,
        last_updated=status.get("last_updated"),
    )


def get_kbars(api: sj.Shioaji, code: str, start: str, end: str) -> KbarsResponse:
    """取得個股日 K 線，以 TTL 快取減少 Shioaji 呼叫。

    快取命中直接回傳；未命中時呼叫 api.kbars() 並存入快取。
    """
    # Shioaji 限制：單次查詢不得超過 30 日曆天（保守用 28 天）
    _MAX_DAYS = 28

    if not end:
        end = date.today().strftime("%Y-%m-%d")
    if not start:
        start = (date.fromisoformat(end) - timedelta(days=_MAX_DAYS)).strftime("%Y-%m-%d")

    # 確保範圍不超過 30 天（前端傳超過時自動截斷起始日）
    start_d = date.fromisoformat(start)
    end_d   = date.fromisoformat(end)
    if (end_d - start_d).days > _MAX_DAYS:
        start_d = end_d - timedelta(days=_MAX_DAYS)
        start = start_d.strftime("%Y-%m-%d")

    cache_key = f"{code}:{start}:{end}"
    if cache_key in kbars_cache:
        logger.debug("kbars cache HIT: %s", cache_key)
        cached: KbarsResponse = kbars_cache[cache_key]
        cached.from_cache = True
        return cached

    logger.info("kbars cache MISS: %s，呼叫 Shioaji", cache_key)
    try:
        contract = api.Contracts.Stocks[code]
    except (KeyError, AttributeError):
        logger.warning("kbars：找不到合約 %s", code)
        return KbarsResponse(code=code, start=start, end=end, bars=[])

    raw = api.kbars(contract=contract, start=start, end=end)

    bars: list[KbarItem] = []
    if raw and hasattr(raw, "ts"):
        for i, ts_ns in enumerate(raw.ts):
            bars.append(KbarItem(
                ts=int(ts_ns // 1_000_000_000),   # nanoseconds → seconds
                open=raw.Open[i],
                high=raw.High[i],
                low=raw.Low[i],
                close=raw.Close[i],
                volume=int(raw.Volume[i]),
                amount=float(raw.Amount[i]) if hasattr(raw, "Amount") else 0.0,
            ))

    resp = KbarsResponse(code=code, start=start, end=end, bars=bars, from_cache=False)
    kbars_cache[cache_key] = resp
    return resp
