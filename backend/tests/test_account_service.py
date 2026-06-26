"""驗證帳務商業邏輯：NAV 公式與整股/零股合併。

使用 unittest.mock 取代真實 Shioaji 呼叫，不需要網路連線。
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.account_service import _merge_positions, get_assets


# ---------- helpers ----------

def _balance(amount: float):
    return SimpleNamespace(acc_balance=amount)


def _position(code: str, quantity: int, price: float, last_price: float, pnl: float):
    return SimpleNamespace(
        code=code, quantity=quantity, price=price,
        last_price=last_price, pnl=pnl,
    )


def _settlement(amount: float, T: int):
    return SimpleNamespace(amount=amount, T=T)


def _make_api(balance, common_positions, odd_positions, settlements):
    api = MagicMock()
    api.stock_account = MagicMock()
    api.account_balance.return_value = _balance(balance)
    api.settlements.return_value = settlements

    def list_positions(account, unit):
        import shioaji as sj
        return common_positions if unit == sj.Unit.Common else odd_positions

    api.list_positions.side_effect = list_positions
    return api


# ---------- NAV tests ----------

def test_nav_basic():
    """NAV = 餘額 + 持倉市值 + 交割款（負值代表應付）。"""
    api = _make_api(
        balance=100_000,
        common_positions=[_position("2330", quantity=1, price=1000.0, last_price=1100.0, pnl=100_000)],
        odd_positions=[],
        settlements=[
            _settlement(-30_000, T=1),
            _settlement(-20_000, T=2),
        ],
    )
    with patch("app.services.account_service.get_universe", return_value={"2330": {"name": "台積電", "industry": "半導體業"}}):
        result = get_assets(api)

    # position_value = 1100 * 1000 = 1_100_000
    # pending_settlement = -50_000
    # NAV = 100_000 + 1_100_000 + (-50_000) = 1_150_000
    assert result.acc_balance == 100_000
    assert result.position_value == 1_100_000
    assert result.pending_settlement == -50_000
    assert result.nav == 1_150_000


def test_nav_no_positions():
    """無持倉時，NAV = 餘額（忽略 T=0 的交割款）。"""
    api = _make_api(
        balance=500_000,
        common_positions=[],
        odd_positions=[],
        settlements=[
            _settlement(500_000, T=0),   # T=0 不計入 pending
            _settlement(-10_000, T=1),
        ],
    )
    with patch("app.services.account_service.get_universe", return_value={}):
        result = get_assets(api)

    assert result.nav == 500_000 + 0 + (-10_000)


# ---------- 持倉合併 tests ----------

def test_merge_common_only():
    """只有整股：quantity 需 × 1000。"""
    api = _make_api(
        balance=0,
        common_positions=[_position("2330", quantity=2, price=1000.0, last_price=1100.0, pnl=200_000)],
        odd_positions=[],
        settlements=[],
    )
    with patch("app.services.account_service.get_universe", return_value={"2330": {"name": "台積電", "industry": "半導體業"}}):
        positions = _merge_positions(api)

    assert len(positions) == 1
    p = positions[0]
    assert p.code == "2330"
    assert p.quantity == 2000          # 2 張 × 1000
    assert p.avg_price == 1000.0
    assert p.market_value == 2_200_000


def test_merge_odd_only():
    """只有零股：quantity 直接使用（單位為股）。"""
    api = _make_api(
        balance=0,
        common_positions=[],
        odd_positions=[_position("2330", quantity=500, price=1050.0, last_price=1100.0, pnl=25_000)],
        settlements=[],
    )
    with patch("app.services.account_service.get_universe", return_value={"2330": {"name": "台積電", "industry": "半導體業"}}):
        positions = _merge_positions(api)

    assert len(positions) == 1
    assert positions[0].quantity == 500
    assert positions[0].market_value == 550_000


def test_merge_common_and_odd():
    """整股 + 零股合併：加權平均成本正確。"""
    api = _make_api(
        balance=0,
        common_positions=[_position("0050", quantity=1, price=200.0, last_price=210.0, pnl=10_000)],
        odd_positions=[_position("0050", quantity=300, price=205.0, last_price=210.0, pnl=1_500)],
        settlements=[],
    )
    with patch("app.services.account_service.get_universe", return_value={"0050": {"name": "元大台灣50", "industry": "ETF"}}):
        positions = _merge_positions(api)

    assert len(positions) == 1
    p = positions[0]
    # 整股：1000 股 @ 200；零股：300 股 @ 205
    # 加權成本 = (200*1000 + 205*300) / 1300 = 261500/1300 ≈ 201.15
    assert p.quantity == 1300
    assert abs(p.avg_price - 201.15) < 0.01
    assert p.market_value == 1300 * 210


def test_merge_multiple_codes():
    """多檔股票各自合併，不相互混淆。"""
    api = _make_api(
        balance=0,
        common_positions=[
            _position("2330", quantity=1, price=1000.0, last_price=1100.0, pnl=100_000),
            _position("2317", quantity=2, price=250.0, last_price=260.0, pnl=20_000),
        ],
        odd_positions=[
            _position("2330", quantity=200, price=1050.0, last_price=1100.0, pnl=10_000),
        ],
        settlements=[],
    )
    with patch("app.services.account_service.get_universe", return_value={
        "2330": {"name": "台積電", "industry": "半導體業"},
        "2317": {"name": "鴻海", "industry": "電子零組件業"},
    }):
        positions = _merge_positions(api)

    codes = {p.code for p in positions}
    assert codes == {"2330", "2317"}

    tsmc = next(p for p in positions if p.code == "2330")
    assert tsmc.quantity == 1200   # 1000 + 200
    foxconn = next(p for p in positions if p.code == "2317")
    assert foxconn.quantity == 2000
