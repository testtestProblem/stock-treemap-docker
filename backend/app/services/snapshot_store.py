"""全市場最新快照的記憶體儲存。

格式：{code: {close, change_rate, total_amount, name, industry, ...}}
排程每 2 分鐘更新，前端透過 /api/market/treemap 讀取。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

_store: dict[str, Any] = {}
_last_updated: datetime | None = None


def update(snapshots: dict[str, Any]) -> None:
    global _last_updated
    _store.update(snapshots)
    _last_updated = datetime.now()


def get_all() -> dict[str, Any]:
    return _store


def get_status() -> dict[str, Any]:
    return {
        "total": len(_store),
        "last_updated": _last_updated.isoformat() if _last_updated else None,
    }
