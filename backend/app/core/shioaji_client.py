"""Shioaji 單例包裝。

全程只在 FastAPI lifespan 呼叫 connect() / disconnect() 一次。
其他模組透過 get_api() 取得實例，絕不自行呼叫 login()。
"""
from __future__ import annotations

import logging
from typing import Any

import shioaji as sj

logger = logging.getLogger(__name__)

_api: sj.Shioaji | None = None
_login_info: dict[str, Any] = {}


def connect(api_key: str, secret_key: str, production: bool = True) -> sj.Shioaji:
    """建立 Shioaji 連線（冪等：已登入則直接回傳）。"""
    global _api, _login_info
    if _api is not None:
        return _api

    _api = sj.Shioaji(simulation=not production)
    accounts = _api.login(api_key=api_key, secret_key=secret_key, fetch_contract=True)

    # 記錄登入後的帳戶清單供 debug 端點使用
    _login_info = {
        "simulation": not production,
        "accounts": [str(a) for a in accounts] if accounts else [],
        "stock_account": str(_api.stock_account) if _api.stock_account else None,
    }
    logger.info("Shioaji 登入成功，帳戶數：%d", len(_login_info["accounts"]))
    return _api


def disconnect() -> None:
    """登出並清除單例。"""
    global _api, _login_info
    if _api is not None:
        try:
            _api.logout()
        except Exception:
            pass
        _api = None
        _login_info = {}
        logger.info("Shioaji 已登出")


def get_api() -> sj.Shioaji:
    """取得已登入的 Shioaji 實例；尚未初始化則拋例外。"""
    if _api is None:
        raise RuntimeError("Shioaji 尚未初始化，請確認 lifespan 已正確執行")
    return _api


def get_status() -> dict[str, Any]:
    """回傳目前連線狀態，供 /api/debug/status 使用。"""
    if _api is None:
        return {"connected": False}
    return {
        "connected": True,
        **_login_info,
    }
