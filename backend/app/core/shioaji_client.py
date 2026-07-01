"""Shioaji 單例包裝。

全程只在 FastAPI lifespan 呼叫 connect() / disconnect() 一次。
其他模組透過 get_api() 取得實例，絕不自行呼叫 login()。

API 用量追蹤：
  record_api_calls(n) 每次呼叫 Shioaji 前記錄筆數，
  usage_pct() 以滾動 5 秒視窗（限流 50 次）計算使用率 %。
"""
from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime
from typing import Any

import shioaji as sj

logger = logging.getLogger(__name__)

# ── 單例 ──────────────────────────────────────────────────────────────────────
_api: sj.Shioaji | None = None
_login_info: dict[str, Any] = {}
_login_time: datetime | None = None

# 保存登入憑證供 reconnect() 重用
_stored_api_key: str = ""
_stored_secret_key: str = ""
_stored_production: bool = True

# ── API 用量追蹤（滾動 5 秒視窗，Shioaji 限流：50 次 / 5 秒）─────────────────
_RATE_LIMIT = 50
_RATE_WINDOW = 5.0      # 秒
_call_timestamps: deque[float] = deque()


def record_api_calls(n: int = 1) -> None:
    """記錄 n 次 Shioaji API 呼叫時間戳，供 usage_pct 計算。"""
    now = time.monotonic()
    for _ in range(n):
        _call_timestamps.append(now)
    # 清除視窗外的舊記錄
    cutoff = now - _RATE_WINDOW
    while _call_timestamps and _call_timestamps[0] < cutoff:
        _call_timestamps.popleft()


def _calc_usage_pct() -> float:
    """回傳最近 5 秒內 API 呼叫次數佔限流上限的百分比（0–100）。"""
    if not _call_timestamps:
        return 0.0
    cutoff = time.monotonic() - _RATE_WINDOW
    recent = sum(1 for t in _call_timestamps if t >= cutoff)
    return min(round(recent / _RATE_LIMIT * 100, 1), 100.0)


# ── 連線操作 ──────────────────────────────────────────────────────────────────

def connect(api_key: str, secret_key: str, production: bool = True) -> sj.Shioaji:
    """建立 Shioaji 連線（冪等：已登入則直接回傳）。"""
    global _api, _login_info, _login_time
    global _stored_api_key, _stored_secret_key, _stored_production

    # 儲存憑證供 reconnect() 重用
    _stored_api_key = api_key
    _stored_secret_key = secret_key
    _stored_production = production

    if _api is not None:
        return _api

    _api = sj.Shioaji(simulation=not production)
    accounts = _api.login(api_key=api_key, secret_key=secret_key, fetch_contract=True)
    _login_time = datetime.now()

    _login_info = {
        "simulation": not production,
        "accounts": [str(a) for a in accounts] if accounts else [],
        "stock_account": str(_api.stock_account) if _api.stock_account else None,
    }
    logger.info("Shioaji 登入成功，帳戶數：%d", len(_login_info["accounts"]))
    return _api


def disconnect() -> None:
    """登出並清除單例。"""
    global _api, _login_info, _login_time
    if _api is not None:
        try:
            _api.logout()
        except Exception:
            pass
        _api = None
        _login_info = {}
        _login_time = None
        logger.info("Shioaji 已登出")


def reconnect() -> dict[str, Any]:
    """手動重新登入（disconnect → connect），回傳新連線狀態。"""
    if not _stored_api_key:
        return {"connected": False, "message": "尚未初始化，缺少登入憑證"}
    try:
        disconnect()
        connect(_stored_api_key, _stored_secret_key, _stored_production)
        logger.info("Shioaji 重新連線成功")
        return {"connected": True, "message": "重新連線成功"}
    except Exception as e:
        logger.error("Shioaji 重新連線失敗：%s", e)
        return {"connected": False, "message": str(e)}


def get_api() -> sj.Shioaji:
    """取得已登入的 Shioaji 實例；尚未初始化則拋例外。"""
    if _api is None:
        raise RuntimeError("Shioaji 尚未初始化，請確認 lifespan 已正確執行")
    return _api


def get_status() -> dict[str, Any]:
    """回傳目前連線狀態，供 /api/debug/status 使用。"""
    if _api is None:
        return {
            "connected": False,
            "usage_pct": 0.0,
            "last_login": None,
        }
    return {
        "connected": True,
        "usage_pct": _calc_usage_pct(),
        "last_login": _login_time.isoformat() if _login_time else None,
        **_login_info,
    }
