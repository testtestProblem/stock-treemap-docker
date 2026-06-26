"""Shioaji 單例包裝。

階段 1 實作：lifespan 呼叫 connect() / disconnect()。
其他模組透過 get_api() 取得全域實例，不自行 login。
"""
from __future__ import annotations

import shioaji as sj

_api: sj.Shioaji | None = None


def connect(api_key: str, secret_key: str, production: bool = True) -> sj.Shioaji:
    global _api
    if _api is not None:
        return _api
    _api = sj.Shioaji(simulation=not production)
    _api.login(api_key=api_key, secret_key=secret_key, fetch_contract=True)
    return _api


def disconnect() -> None:
    global _api
    if _api is not None:
        _api.logout()
        _api = None


def get_api() -> sj.Shioaji:
    if _api is None:
        raise RuntimeError("Shioaji 尚未初始化，請確認 lifespan 已正確執行")
    return _api
