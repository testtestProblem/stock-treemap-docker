"""帳務相關端點。

GET /api/account/assets   — 階段 3 實作
GET /api/account/positions — 階段 3 實作
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/assets")
def get_assets():
    # TODO 階段 3 實作
    return {"message": "階段 3 尚未實作"}


@router.get("/positions")
def get_positions():
    # TODO 階段 3 實作
    return {"message": "階段 3 尚未實作"}
