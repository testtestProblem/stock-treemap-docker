"""開發除錯用端點，正式環境可移除或加 Auth 保護。"""
from fastapi import APIRouter

from app.core import shioaji_client

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/status")
def get_status():
    """回傳 Shioaji 連線狀態與帳戶資訊。"""
    return shioaji_client.get_status()
