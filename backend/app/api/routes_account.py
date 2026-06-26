"""帳務相關端點。

GET /api/account/assets    — 真實總資產（NAV）
GET /api/account/positions — 整股+零股合併後持倉列表
"""
from fastapi import APIRouter, HTTPException

from app.core.shioaji_client import get_api
from app.schemas.account import AssetsResponse, PositionItem
from app.services import account_service

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/assets", response_model=AssetsResponse)
def get_assets():
    try:
        api = get_api()
        return account_service.get_assets(api)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"帳務查詢失敗：{e}")


@router.get("/positions", response_model=list[PositionItem])
def get_positions():
    try:
        api = get_api()
        return account_service.get_positions(api)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"持倉查詢失敗：{e}")
