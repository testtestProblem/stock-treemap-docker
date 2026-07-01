from __future__ import annotations

from pydantic import BaseModel


class AssetsResponse(BaseModel):
    """NAV = cash + stock_value + margin_pnl + short_pnl + pending_settlement

    cash            : acc_balance（永豐回傳值，已內含融資保證金）
    stock_value     : 現股持倉市值（last_price × quantity）
    margin_pnl      : 融資未實現損益（StockOrderCond.MarginTrading 的 pnl 合計）
    short_pnl       : 融券未實現損益（StockOrderCond.ShortSelling 的 pnl 合計）
    pending_t1      : T+1 交割款
    pending_t2      : T+2 交割款
    pending_settlement : T+1 + T+2 合計（通常為負，代表應付）
    nav             : 真實總資產

    以下欄位為擴充副資訊，無法取得時回傳 None（前端以「—」呈現）：
    unrealized_pnl      : 所有持倉未實現損益合計（現股+融資+融券 pnl）
    margin_value        : 融資持倉毛市值
    short_value         : 融券持倉毛市值
    day_pnl             : 當日損益（依快照 change_price × 持股數 估算）
    day_pnl_rate        : 當日損益率（%）
    realized_pnl_today  : 今日已實現損益（來自 list_profit_loss，5 分鐘快取）
    """
    nav: float
    cash: float
    stock_value: float
    margin_pnl: float
    short_pnl: float
    pending_t1: float
    pending_t2: float
    pending_settlement: float
    # 副資訊欄位（Optional）
    unrealized_pnl: float | None = None
    margin_value: float | None = None
    short_value: float | None = None
    day_pnl: float | None = None
    day_pnl_rate: float | None = None
    realized_pnl_today: float | None = None


class PositionItem(BaseModel):
    code: str
    name: str
    position_type: str          # "現股" | "融資" | "融券"
    quantity: int               # 總持股數（股）
    avg_price: float            # 加權平均成本
    last_price: float           # 目前股價
    market_value: float         # last_price × quantity（毛市值，供顯示）
    pnl: float                  # 未實現損益（直接來自 API）
    industry: str               # 產業別
