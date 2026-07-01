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

副資訊欄位計算說明：
  unrealized_pnl    : Σ(pnl) for 所有持倉（現股+融資+融券），直接加總
  margin_value      : Σ(last_price × quantity) for 融資持倉（毛市值）
  short_value       : Σ(last_price × quantity) for 融券持倉（毛市值）
  day_pnl           : Σ(snapshot.change_price × quantity)，依快照估算；快照未就緒回 None
  day_pnl_rate      : day_pnl / (nav - day_pnl) × 100，回傳 %；day_pnl 為 None 時回 None
  realized_pnl_today: api.list_profit_loss(today, today) 合計，5 分鐘 TTL 快取
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import date

import shioaji as sj
StockOrderCond = sj.StockOrderCond

from app.schemas.account import AssetsResponse, PositionItem
from app.services.stock_universe import get_universe
from app.services import snapshot_store

logger = logging.getLogger(__name__)

_COND_LABEL = {
    StockOrderCond.Cash:         "現股",
    StockOrderCond.MarginTrading:"融資",
    StockOrderCond.ShortSelling: "融券",
}

# ── realized_pnl_today TTL 快取（5 分鐘）────────────────────────────────────
_REALIZED_TTL = 300.0

_realized_cache: dict = {"value": None, "ts": 0.0}


def _get_realized_pnl_today(api: sj.Shioaji) -> float | None:
    """查詢今日已實現損益（帶 5 分鐘快取避免頻繁呼叫）。"""
    now = time.monotonic()
    if now - _realized_cache["ts"] < _REALIZED_TTL:
        return _realized_cache["value"]

    try:
        today = date.today().strftime("%Y-%m-%d")
        result = api.list_profit_loss(
            account=api.stock_account,
            begin_date=today,
            end_date=today,
        )
        total = sum(getattr(r, "pnl", 0) or 0 for r in result) if result else 0.0
        _realized_cache["value"] = round(total, 0)
        logger.info("realized_pnl_today=%.0f", _realized_cache["value"])
    except Exception as e:
        logger.warning("list_profit_loss 查詢失敗（回傳 None）：%s", e)
        _realized_cache["value"] = None

    _realized_cache["ts"] = now
    return _realized_cache["value"]


def _calc_day_pnl(positions: list[PositionItem]) -> float | None:
    """依快照 change_price × quantity 估算當日損益。

    快照尚未就緒（市場剛開盤或排程未執行）時回傳 None。
    """
    snap = snapshot_store.get_all()
    if not snap:
        return None

    total = 0.0
    matched = 0
    for p in positions:
        s = snap.get(p.code)
        if s:
            total += s.get("change_price", 0.0) * p.quantity
            matched += 1

    if matched == 0:
        return None

    return round(total, 0)


# ── 主要函式 ──────────────────────────────────────────────────────────────────

def get_assets(api: sj.Shioaji) -> AssetsResponse:
    """計算真實淨資產（NAV）並附加副資訊欄位。"""
    acc_balance = api.account_balance(account=api.stock_account).acc_balance

    positions = _merge_positions(api)

    # 核心 NAV 欄位
    stock_value  = sum(p.market_value for p in positions if p.position_type == "現股")
    margin_pnl   = sum(p.pnl         for p in positions if p.position_type == "融資")
    short_pnl    = sum(p.pnl         for p in positions if p.position_type == "融券")

    settlements  = api.settlements(account=api.stock_account)
    pending_t1   = sum(s.amount for s in settlements if s.T == 1)
    pending_t2   = sum(s.amount for s in settlements if s.T == 2)
    pending      = pending_t1 + pending_t2

    nav = acc_balance + stock_value + margin_pnl + short_pnl + pending

    # 副資訊欄位
    unrealized_pnl = round(sum(p.pnl for p in positions), 0)
    margin_value   = round(sum(p.market_value for p in positions if p.position_type == "融資"), 0)
    short_value    = round(sum(p.market_value for p in positions if p.position_type == "融券"), 0)

    day_pnl      = _calc_day_pnl(positions)
    day_pnl_rate = None
    if day_pnl is not None:
        prev_nav = nav - day_pnl
        day_pnl_rate = round(day_pnl / prev_nav * 100, 2) if prev_nav != 0 else None

    realized_pnl_today = _get_realized_pnl_today(api)

    logger.info(
        "NAV=%.0f cash=%.0f stock=%.0f margin_pnl=%.0f short_pnl=%.0f "
        "t1=%.0f t2=%.0f unrealized=%.0f day_pnl=%s realized=%s",
        nav, acc_balance, stock_value, margin_pnl, short_pnl,
        pending_t1, pending_t2, unrealized_pnl,
        f"{day_pnl:.0f}" if day_pnl is not None else "None",
        f"{realized_pnl_today:.0f}" if realized_pnl_today is not None else "None",
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
        unrealized_pnl=unrealized_pnl,
        margin_value=margin_value,
        short_value=short_value,
        day_pnl=day_pnl,
        day_pnl_rate=day_pnl_rate,
        realized_pnl_today=realized_pnl_today,
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
