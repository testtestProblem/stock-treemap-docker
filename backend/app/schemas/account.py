from pydantic import BaseModel


class AssetsResponse(BaseModel):
    nav: float                  # 真實總資產 = acc_balance + position_value + pending_settlement
    acc_balance: float          # 帳戶餘額（現金）
    position_value: float       # 持倉總市值
    pending_settlement: float   # T+1/T+2 交割款（通常為負值，代表應付）


class PositionItem(BaseModel):
    code: str
    name: str
    quantity: int               # 總持股數（股）= 整股張數×1000 + 零股數量
    avg_price: float            # 加權平均成本
    last_price: float           # 目前股價
    market_value: float         # 市值 = last_price × quantity
    pnl: float                  # 未實現損益（整合整股+零股）
    industry: str               # 產業別（由 stock_universe 補入）
