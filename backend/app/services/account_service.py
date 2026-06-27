"""帳務商業邏輯：NAV 計算、持倉分類合併。

正確 NAV 公式（已由實際帳戶驗證）：
  NAV = cash + stock_value + margin_pnl + short_pnl + pending_settlement

  cash              : api.account_balance().acc_balance
                      永豐系統內含融資保證金，因此融資部位只計損益，不計全額市值。
  stock_value       : Σ(last_price × quantity) for cond == Cash
  margin_pnl        : Σ(pnl) for cond == MarginTrading
  short_pnl         : Σ(pnl) for cond == ShortSelling
  pending_settlement: Σ(amount, T∈{1,2})

持倉分類依 StockPosition.cond（欄位名稱已由 /api/debug/positions/all-fields 確認）：
  StockOrderCond.Cash         → 現股
  StockOrderCond.MarginTrading→ 融資
  StockOrderCond.ShortSelling → 融券

Unit.Share 回傳所有持倉，quantity 單位為「股」，不使用 Unit.Common 避免重複計算。
"""
from __future__ import annotations

import logging
from collections import defaultdict

import shioaji as sj
StockOrderCond = sj.StockOrderCond

from app.schemas.account import AssetsResponse, PositionItem
from app.services.stock_universe import get_universe

logger = logging.getLogger(__name__)

_COND_LABEL = {
    StockOrderCond.Cash:         "現股",
    StockOrderCond.MarginTrading:"融資",
    StockOrderCond.ShortSelling: "融券",
}


def get_assets(api: sj.Shioaji) -> AssetsResponse:
    """計算真實淨資產（NAV）。"""
    acc_balance = api.account_balance(account=api.stock_account).acc_balance

    positions = _merge_positions(api)
    stock_value  = sum(p.market_value for p in positions if p.position_type == "現股")
    margin_pnl   = sum(p.pnl         for p in positions if p.position_type == "融資")
    short_pnl    = sum(p.pnl         for p in positions if p.position_type == "融券")

    settlements  = api.settlements(account=api.stock_account)
    pending_t1   = sum(s.amount for s in settlements if s.T == 1)
    pending_t2   = sum(s.amount for s in settlements if s.T == 2)
    pending      = pending_t1 + pending_t2

    nav = acc_balance + stock_value + margin_pnl + short_pnl + pending

    logger.info(
        "NAV=%.0f cash=%.0f stock=%.0f margin_pnl=%.0f short_pnl=%.0f t1=%.0f t2=%.0f",
        nav, acc_balance, stock_value, margin_pnl, short_pnl, pending_t1, pending_t2,
    )
    return AssetsResponse(
        nav=nav,
        cash=acc_balance,
        stock_value=stock_value,
        margin_pnl=margin_pnl,
        short_pnl=short_pnl,
        pending_t1=pending_t1,
        pending_t2=pending_t2,
        pending_settlement=pending,
    )


def get_positions(api: sj.Shioaji) -> list[PositionItem]:
    return _merge_positions(api)


def _merge_positions(api: sj.Shioaji) -> list[PositionItem]:
    """合併同一 (code, cond) 的多筆部位為單筆 PositionItem。

    以 (code, cond) 為 key，確保現股與融資各自獨立合併，不互相混淆。
    """
    universe = get_universe()
    all_positions = api.list_positions(account=api.stock_account, unit=sj.Unit.Share)

    # key = (code, cond_str)
    merged: dict[tuple, dict] = defaultdict(lambda: {
        "shares": 0,
        "cost_sum": 0.0,
        "pnl": 0.0,
        "last_price": 0.0,
        "cond": None,
    })

    for pos in all_positions:
        key = (pos.code, pos.cond)
        merged[key]["shares"]   += pos.quantity
        merged[key]["cost_sum"] += pos.price * pos.quantity
        merged[key]["pnl"]      += pos.pnl
        merged[key]["cond"]      = pos.cond
        if pos.quantity > 0 or merged[key]["last_price"] == 0.0:
            merged[key]["last_price"] = pos.last_price

    result: list[PositionItem] = []
    for (code, _), data in merged.items():
        shares = data["shares"]
        if shares <= 0:
            continue
        avg_price  = data["cost_sum"] / shares
        last_price = data["last_price"]
        cond       = data["cond"]
        label      = _COND_LABEL.get(cond, str(cond))
        info       = universe.get(code, {})
        result.append(PositionItem(
            code=code,
            name=info.get("name", code),
            position_type=label,
            quantity=shares,
            avg_price=round(avg_price, 2),
            last_price=last_price,
            market_value=round(last_price * shares, 0),
            pnl=round(data["pnl"], 0),
            industry=info.get("industry", "其他"),
        ))

    return sorted(result, key=lambda p: p.market_value, reverse=True)
