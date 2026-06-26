"""帳務商業邏輯：NAV 計算、整股/零股持倉合併。

NAV = acc_balance + position_value + pending_settlement
    其中 pending_settlement = Σ(settlement.amount, T∈{1,2})
    settlement.amount 為帶正負號的金額（應付為負），直接相加即可。

整股 quantity 單位：張（1 張 = 1000 股）→ 轉換時 × 1000
零股 quantity 單位：股（直接使用）
"""
from __future__ import annotations

import logging
from collections import defaultdict

import shioaji as sj
Unit = sj.Unit

from app.schemas.account import AssetsResponse, PositionItem
from app.services.stock_universe import get_universe

logger = logging.getLogger(__name__)


def get_assets(api: sj.Shioaji) -> AssetsResponse:
    """計算真實淨資產價值（NAV）。"""
    # 1. 帳戶現金餘額
    balance = api.account_balance(account=api.stock_account)
    acc_balance = balance.acc_balance

    # 2. 持倉總市值（整股 + 零股合併後計算）
    positions = _merge_positions(api)
    position_value = sum(p.market_value for p in positions)

    # 3. T+1 / T+2 交割款（帶號值，應付為負）
    settlements = api.settlements(account=api.stock_account)
    pending_settlement = sum(
        s.amount for s in settlements if s.T in (1, 2)
    )

    nav = acc_balance + position_value + pending_settlement

    logger.info(
        "NAV=%.0f acc_balance=%.0f position_value=%.0f pending=%.0f",
        nav, acc_balance, position_value, pending_settlement,
    )
    return AssetsResponse(
        nav=nav,
        acc_balance=acc_balance,
        position_value=position_value,
        pending_settlement=pending_settlement,
    )


def get_positions(api: sj.Shioaji) -> list[PositionItem]:
    """回傳整股+零股合併後的持倉列表。"""
    return _merge_positions(api)


def _merge_positions(api: sj.Shioaji) -> list[PositionItem]:
    """將同一代號的整股與零股部位合併為單筆 PositionItem。

    整股 quantity 單位為「張」，1 張 = 1000 股，合併時需換算。
    加權平均成本：(整股成本 + 零股成本) / 總股數
    """
    universe = get_universe()

    # 取得整股部位
    common = api.list_positions(account=api.stock_account, unit=Unit.Common)
    # 取得零股部位
    odd = api.list_positions(account=api.stock_account, unit=Unit.Share)

    # 以 code 為 key 累積：{code: {shares, cost_sum, pnl, last_price}}
    merged: dict[str, dict] = defaultdict(lambda: {
        "shares": 0,
        "cost_sum": 0.0,
        "pnl": 0.0,
        "last_price": 0.0,
    })

    for pos in common:
        shares = pos.quantity * 1000   # 張 → 股
        merged[pos.code]["shares"] += shares
        merged[pos.code]["cost_sum"] += pos.price * shares
        merged[pos.code]["pnl"] += pos.pnl
        merged[pos.code]["last_price"] = pos.last_price

    for pos in odd:
        shares = pos.quantity          # 已是「股」單位
        merged[pos.code]["shares"] += shares
        merged[pos.code]["cost_sum"] += pos.price * shares
        merged[pos.code]["pnl"] += pos.pnl
        if merged[pos.code]["last_price"] == 0.0:
            merged[pos.code]["last_price"] = pos.last_price

    result: list[PositionItem] = []
    for code, data in merged.items():
        shares = data["shares"]
        if shares <= 0:
            continue
        avg_price = data["cost_sum"] / shares if shares else 0.0
        last_price = data["last_price"]
        info = universe.get(code, {})
        result.append(PositionItem(
            code=code,
            name=info.get("name", code),
            quantity=shares,
            avg_price=round(avg_price, 2),
            last_price=last_price,
            market_value=round(last_price * shares, 0),
            pnl=round(data["pnl"], 0),
            industry=info.get("industry", "其他"),
        ))

    return sorted(result, key=lambda p: p.market_value, reverse=True)
