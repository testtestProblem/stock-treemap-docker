"""驗證歷史績效服務：標準化計算邏輯與空資料處理。"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.history_service import _normalize, get_performance
from app.schemas.history import PerformanceResponse


# ── _normalize 單元測試 ────────────────────────────────────────────────────

def test_normalize_base_is_zero():
    """第一筆應為 0.0。"""
    result = _normalize([100.0, 110.0, 90.0])
    assert result[0] == 0.0


def test_normalize_correct_pct():
    """標準化值應為 (v/base - 1) × 100。"""
    result = _normalize([200.0, 210.0, 180.0])
    assert abs(result[1] - 5.0) < 0.001    # (210/200 - 1) * 100 = 5.0
    assert abs(result[2] - (-10.0)) < 0.001  # (180/200 - 1) * 100 = -10.0


def test_normalize_empty():
    assert _normalize([]) == []


def test_normalize_single():
    assert _normalize([100.0]) == [0.0]


def test_normalize_zero_base():
    """基準為 0 時不應拋例外，回傳全 0。"""
    result = _normalize([0.0, 100.0])
    assert result == [0.0, 0.0]


# ── get_performance 整合測試 ──────────────────────────────────────────────

def _make_row(date, nav, p0050, p2330):
    from types import SimpleNamespace
    return SimpleNamespace(date=date, nav=nav, price_0050=p0050, price_2330=p2330)


def _make_db(rows):
    """模擬 SQLAlchemy Session，讓 db.execute().scalars().all() 回傳 rows。"""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    execute_mock = MagicMock()
    execute_mock.scalars.return_value = scalars_mock
    db = MagicMock()
    db.execute.return_value = execute_mock
    return db


def test_performance_empty_db():
    """資料庫無紀錄時，三條曲線均為空。"""
    db = _make_db([])
    result = get_performance(db)
    assert result.record_count == 0
    assert result.nav.dates == []
    assert result.nav.values == []


def test_performance_single_row():
    """只有一筆時，值應為 [0.0]（基準本身）。"""
    db = _make_db([_make_row("2025-01-02", 1_000_000, 150.0, 1000.0)])
    result = get_performance(db)
    assert result.record_count == 1
    assert result.nav.values == [0.0]
    assert result.price_0050.values == [0.0]


def test_performance_multiple_rows():
    """多筆資料時，三條曲線長度一致且起點為 0。"""
    rows = [
        _make_row("2025-01-02", 1_000_000, 150.0, 1000.0),
        _make_row("2025-01-03", 1_050_000, 153.0, 1030.0),
        _make_row("2025-01-06", 980_000,  148.5,  990.0),
    ]
    db = _make_db(rows)
    result = get_performance(db)

    assert result.record_count == 3
    assert len(result.nav.dates) == 3
    assert len(result.nav.values) == 3
    assert len(result.price_0050.values) == 3
    assert len(result.price_2330.values) == 3

    # 起點均為 0
    assert result.nav.values[0] == 0.0
    assert result.price_0050.values[0] == 0.0
    assert result.price_2330.values[0] == 0.0

    # 第二筆驗算
    assert abs(result.nav.values[1] - 5.0) < 0.01       # (1050000/1000000-1)*100
    assert abs(result.price_0050.values[1] - 2.0) < 0.01 # (153/150-1)*100
    assert abs(result.price_2330.values[1] - 3.0) < 0.01 # (1030/1000-1)*100


def test_performance_dates_order():
    """日期序列應保持資料庫排序的順序（asc）。"""
    rows = [
        _make_row("2025-01-02", 1_000_000, 150.0, 1000.0),
        _make_row("2025-01-03", 1_050_000, 153.0, 1030.0),
    ]
    db = _make_db(rows)
    result = get_performance(db)
    assert result.nav.dates == ["2025-01-02", "2025-01-03"]
