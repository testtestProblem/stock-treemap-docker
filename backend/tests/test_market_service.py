"""驗證市場服務：Treemap 組裝邏輯、kbars 快取行為。

使用 unittest.mock，不需要 Shioaji 連線。
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.market import TreemapResponse, KbarsResponse
from app.services import market_service
from app.core.cache import kbars_cache


# ── helpers ────────────────────────────────────────────────────────────────

def _snap(code: str, industry: str, change_rate: float, total_amount: float) -> dict:
    return {
        "code": code,
        "name": f"公司{code}",
        "industry": industry,
        "close": 100.0,
        "change_price": change_rate,
        "change_rate": change_rate,
        "total_volume": int(total_amount / 100),
        "total_amount": total_amount,
    }


MOCK_STORE = {
    "2330": _snap("2330", "半導體業", 2.5,  5_000_000_000),
    "2454": _snap("2454", "半導體業", 1.0,  1_000_000_000),
    "2317": _snap("2317", "電子零組件業", -1.0, 800_000_000),
    "0050": _snap("0050", "ETF",       0.5,  300_000_000),
    "XXXX": {**_snap("XXXX", "其他",   0.0,  0)},  # 成交值 0，應被過濾
}


# ── Treemap tests ──────────────────────────────────────────────────────────

def test_treemap_market_all():
    """全市場 treemap：成交值 0 的標的需被過濾。"""
    with patch("app.services.market_service.snapshot_store.get_all", return_value=MOCK_STORE), \
         patch("app.services.market_service.snapshot_store.get_status", return_value={"last_updated": "2026-01-01T15:40:00"}):
        result = market_service.build_treemap(mode="market", watchlist=[])

    assert result.mode == "market"
    all_codes = {s.code for ind in result.children for s in ind.children}
    assert "XXXX" not in all_codes   # 成交值 0 被過濾
    assert "2330" in all_codes
    assert "2317" in all_codes


def test_treemap_industry_grouping():
    """同產業應歸入同一 IndustryNode。"""
    with patch("app.services.market_service.snapshot_store.get_all", return_value=MOCK_STORE), \
         patch("app.services.market_service.snapshot_store.get_status", return_value={}):
        result = market_service.build_treemap(mode="market", watchlist=[])

    industry_names = {node.name for node in result.children}
    assert "半導體業" in industry_names
    assert "電子零組件業" in industry_names

    semi = next(n for n in result.children if n.name == "半導體業")
    semi_codes = {s.code for s in semi.children}
    assert semi_codes == {"2330", "2454"}


def test_treemap_industry_sorted_by_amount():
    """產業節點應按總成交值由大到小排序。"""
    with patch("app.services.market_service.snapshot_store.get_all", return_value=MOCK_STORE), \
         patch("app.services.market_service.snapshot_store.get_status", return_value={}):
        result = market_service.build_treemap(mode="market", watchlist=[])

    amounts = [
        sum(s.total_amount for s in node.children)
        for node in result.children
    ]
    assert amounts == sorted(amounts, reverse=True)


def test_treemap_watchlist_filter():
    """watchlist 模式只回傳指定代號。"""
    with patch("app.services.market_service.snapshot_store.get_all", return_value=MOCK_STORE), \
         patch("app.services.market_service.snapshot_store.get_status", return_value={}):
        result = market_service.build_treemap(mode="watchlist", watchlist=["2330", "0050"])

    all_codes = {s.code for ind in result.children for s in ind.children}
    assert all_codes == {"2330", "0050"}
    assert result.mode == "watchlist"


def test_treemap_watchlist_missing_code():
    """watchlist 含不在快照中的代號時，靜默略過不報錯。"""
    with patch("app.services.market_service.snapshot_store.get_all", return_value=MOCK_STORE), \
         patch("app.services.market_service.snapshot_store.get_status", return_value={}):
        result = market_service.build_treemap(mode="watchlist", watchlist=["2330", "9999"])

    all_codes = {s.code for ind in result.children for s in ind.children}
    assert "9999" not in all_codes
    assert "2330" in all_codes


# ── kbars tests ────────────────────────────────────────────────────────────

def _make_kbars_api(ts_list, opens, highs, lows, closes, volumes):
    raw = SimpleNamespace(
        ts=ts_list, Open=opens, High=highs, Low=lows,
        Close=closes, Volume=volumes, Amount=[0.0] * len(ts_list),
    )
    api = MagicMock()
    api.Contracts.Stocks.__getitem__ = MagicMock(return_value=MagicMock())
    api.kbars.return_value = raw
    return api


def test_kbars_returns_correct_bars():
    """kbars 正確轉換 nanosecond timestamp 並回傳 OHLCV。"""
    kbars_cache.clear()

    ts_ns = [1_700_000_000 * 1_000_000_000]  # 1 bar
    api = _make_kbars_api(ts_ns, [100.0], [110.0], [95.0], [105.0], [1000])

    result = market_service.get_kbars(api, "2330", "2024-01-01", "2024-01-31")

    assert len(result.bars) == 1
    bar = result.bars[0]
    assert bar.ts == 1_700_000_000
    assert bar.open == 100.0
    assert bar.close == 105.0
    assert bar.volume == 1000
    assert result.from_cache is False


def test_kbars_cache_hit():
    """第二次相同查詢應命中快取，不再呼叫 Shioaji。"""
    kbars_cache.clear()

    ts_ns = [1_700_000_000 * 1_000_000_000]
    api = _make_kbars_api(ts_ns, [100.0], [110.0], [95.0], [105.0], [1000])

    market_service.get_kbars(api, "2330", "2024-01-01", "2024-01-31")
    result2 = market_service.get_kbars(api, "2330", "2024-01-01", "2024-01-31")

    assert result2.from_cache is True
    assert api.kbars.call_count == 1   # 只呼叫一次


def test_kbars_unknown_code():
    """找不到合約時回傳空的 bars 列表，不拋出例外。"""
    kbars_cache.clear()

    api = MagicMock()
    api.Contracts.Stocks.__getitem__ = MagicMock(side_effect=KeyError("9999"))

    result = market_service.get_kbars(api, "9999", "2024-01-01", "2024-01-31")
    assert result.bars == []
    assert result.code == "9999"
