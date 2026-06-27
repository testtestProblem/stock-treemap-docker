"""驗證 NAV 公式與持倉合併邏輯。

正確公式：NAV = cash + stock_value + margin_pnl + short_pnl + pending_settlement
  - cash       : acc_balance（含融資保證金，因此融資只計損益）
  - stock_value: 現股市值（last_price × quantity）
  - margin_pnl : 融資未實現損益（pnl）
  - short_pnl  : 融券未實現損益（pnl）
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import shioaji as sj
StockOrderCond = sj.StockOrderCond

from app.services.account_service import _merge_positions, get_assets


# ---------- helpers ----------

def _balance(amount: float):
    return SimpleNamespace(acc_balance=amount)


def _pos(code: str, quantity: int, price: float, last_price: float,
         pnl: float, cond=StockOrderCond.Cash):
    return SimpleNamespace(
        code=code, quantity=quantity, price=price,
        last_price=last_price, pnl=pnl, cond=cond,
    )


def _settlement(amount: float, T: int):
    return SimpleNamespace(amount=amount, T=T)


def _make_api(balance, positions, settlements):
    api = MagicMock()
    api.stock_account = MagicMock()
    api.account_balance.return_value = _balance(balance)
    api.list_positions.return_value = positions
    api.settlements.return_value = settlements
    return api


# ---------- NAV tests ----------

def test_nav_cash_only():
    """純現股：NAV = cash + stock_value + settlement。"""
    api = _make_api(
        balance=100_000,
        positions=[_pos("2330", 1000, 1000.0, 1100.0, 100_000, StockOrderCond.Cash)],
        settlements=[_settlement(-30_000, T=1), _settlement(-20_000, T=2)],
    )
    with patch("app.services.account_service.get_universe",
               return_value={"2330": {"name": "台積電", "industry": "半導體業"}}):
        r = get_assets(api)

    assert r.cash == 100_000
    assert r.stock_value == 1_100_000   # 1100 × 1000
    assert r.margin_pnl == 0
    assert r.short_pnl == 0
    assert r.pending_t1 == -30_000
    assert r.pending_t2 == -20_000
    assert r.pending_settlement == -50_000
    assert r.nav == 1_150_000


def test_nav_with_margin():
    """融資：只加 pnl，不加全額市值（保證金已在 cash 中）。"""
    api = _make_api(
        balance=699_438,
        positions=[
            _pos("00673R", 3000, 11.79, 15.72, 11_687, StockOrderCond.Cash),
            _pos("00673R", 6000, 14.71, 15.72,  5_773, StockOrderCond.MarginTrading),
        ],
        settlements=[_settlement(-51_648, T=1)],
    )
    with patch("app.services.account_service.get_universe",
               return_value={"00673R": {"name": "元大滬深300正2", "industry": "ETF"}}):
        r = get_assets(api)

    assert r.stock_value == 3000 * 15.72       # 現股：47,160
    assert r.margin_pnl  == 5_773              # 融資：只算 pnl
    assert r.nav == 699_438 + 47_160 + 5_773 + (-51_648)


def test_nav_no_positions():
    """無持倉時 NAV = cash + settlement。"""
    api = _make_api(balance=500_000, positions=[], settlements=[_settlement(-10_000, T=2)])
    with patch("app.services.account_service.get_universe", return_value={}):
        r = get_assets(api)
    assert r.nav == 490_000


# ---------- 持倉合併 tests ----------

def test_merge_cash_position():
    """現股：market_value = last_price × quantity，position_type = 現股。"""
    api = _make_api(
        balance=0,
        positions=[_pos("2330", 2000, 1000.0, 1100.0, 200_000, StockOrderCond.Cash)],
        settlements=[],
    )
    with patch("app.services.account_service.get_universe",
               return_value={"2330": {"name": "台積電", "industry": "半導體業"}}):
        ps = _merge_positions(api)

    assert len(ps) == 1
    p = ps[0]
    assert p.position_type == "現股"
    assert p.quantity == 2000
    assert p.market_value == 2_200_000


def test_merge_margin_position():
    """融資：market_value 仍為 gross（供顯示），position_type = 融資。"""
    api = _make_api(
        balance=0,
        positions=[_pos("00673R", 6000, 14.71, 15.72, 5_773, StockOrderCond.MarginTrading)],
        settlements=[],
    )
    with patch("app.services.account_service.get_universe",
               return_value={"00673R": {"name": "元大滬深300正2", "industry": "ETF"}}):
        ps = _merge_positions(api)

    assert len(ps) == 1
    p = ps[0]
    assert p.position_type == "融資"
    assert p.quantity == 6000
    assert p.market_value == 94_320   # gross，僅供顯示
    assert p.pnl == 5_773


def test_merge_cash_and_margin_same_code():
    """同代號的現股 + 融資分開合併為兩筆 PositionItem。"""
    api = _make_api(
        balance=0,
        positions=[
            _pos("00673R", 3000, 11.79, 15.72, 11_687, StockOrderCond.Cash),
            _pos("00673R", 6000, 14.71, 15.72,  5_773, StockOrderCond.MarginTrading),
        ],
        settlements=[],
    )
    with patch("app.services.account_service.get_universe",
               return_value={"00673R": {"name": "元大滬深300正2", "industry": "ETF"}}):
        ps = _merge_positions(api)

    assert len(ps) == 2
    types = {p.position_type for p in ps}
    assert types == {"現股", "融資"}

    cash_p = next(p for p in ps if p.position_type == "現股")
    assert cash_p.quantity == 3000

    margin_p = next(p for p in ps if p.position_type == "融資")
    assert margin_p.quantity == 6000


def test_merge_batched_buys():
    """同代號同性質的分批買進，合併為一筆，加權平均成本正確。"""
    api = _make_api(
        balance=0,
        positions=[
            _pos("0050", 1000, 200.0, 210.0, 10_000, StockOrderCond.Cash),
            _pos("0050",  300, 205.0, 210.0,  1_500, StockOrderCond.Cash),
        ],
        settlements=[],
    )
    with patch("app.services.account_service.get_universe",
               return_value={"0050": {"name": "元大台灣50", "industry": "ETF"}}):
        ps = _merge_positions(api)

    assert len(ps) == 1
    p = ps[0]
    assert p.quantity == 1300
    assert abs(p.avg_price - 201.15) < 0.01
    assert p.market_value == 1300 * 210
