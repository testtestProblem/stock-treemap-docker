"""開發除錯用端點，正式環境可移除或加 Auth 保護。"""
from fastapi import APIRouter

from app.core import shioaji_client

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/status")
def get_status():
    """回傳 Shioaji 連線狀態與帳戶資訊。"""
    return shioaji_client.get_status()


@router.get("/positions/raw")
def get_positions_raw():
    """回傳 Shioaji 原始整股/零股持倉，供除錯用。"""
    api = shioaji_client.get_api()
    import shioaji as sj

    common = api.list_positions(account=api.stock_account, unit=sj.Unit.Common)
    share = api.list_positions(account=api.stock_account, unit=sj.Unit.Share)

    def fmt(pos):
        return {
            "code": pos.code,
            "quantity": pos.quantity,
            "price": pos.price,
            "last_price": pos.last_price,
            "pnl": pos.pnl,
        }

    return {
        "common": [fmt(p) for p in common],
        "share": [fmt(p) for p in share],
        "common_count": len(common),
        "share_count": len(share),
    }


@router.get("/positions/all-fields")
def get_positions_all_fields():
    """印出第一筆 position 的所有屬性，確認欄位名稱。"""
    api = shioaji_client.get_api()
    import shioaji as sj

    rows = api.list_positions(account=api.stock_account, unit=sj.Unit.Share)
    if not rows:
        return {"error": "no positions"}
    first = rows[0]
    return {k: str(v) for k, v in vars(first).items()}


@router.get("/positions/breakdown")
def get_positions_breakdown():
    """逐筆列出 Unit.Share 每筆市值（含 cond / margin 欄位）。"""
    api = shioaji_client.get_api()
    import shioaji as sj

    rows = api.list_positions(account=api.stock_account, unit=sj.Unit.Share)

    items = []
    total_gross = 0.0
    total_margin_loan = 0.0
    for pos in rows:
        mv_gross = round(pos.last_price * pos.quantity, 0)
        loan = getattr(pos, "margin_purchase_amount", 0) or 0
        cond = str(getattr(pos, "cond", "unknown"))
        total_gross += mv_gross
        total_margin_loan += loan
        items.append({
            "code": pos.code,
            "cond": cond,
            "quantity_shares": pos.quantity,
            "price_cost": pos.price,
            "last_price": pos.last_price,
            "market_value_gross": mv_gross,
            "margin_purchase_amount": loan,
            "market_value_net": mv_gross - loan,
            "pnl_from_api": pos.pnl,
        })

    return {
        "rows": items,
        "row_count": len(items),
        "total_gross": total_gross,
        "total_margin_loan": total_margin_loan,
        "total_net": total_gross - total_margin_loan,
    }
