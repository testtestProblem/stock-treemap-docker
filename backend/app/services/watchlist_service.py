"""自選清單：以 SQLite kv_store 持久化，key = 'watchlist'。

格式：JSON 陣列，如 ["2330", "0050", "2317"]
"""
from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.db.models import KvStore

logger = logging.getLogger(__name__)

_KEY = "watchlist"
_DEFAULT: list[str] = []


def get_watchlist(db: Session) -> list[str]:
    row = db.get(KvStore, _KEY)
    if row is None:
        return list(_DEFAULT)
    try:
        return json.loads(row.json_value)
    except (json.JSONDecodeError, TypeError):
        logger.warning("watchlist JSON 解析失敗，回傳空清單")
        return list(_DEFAULT)


def set_watchlist(db: Session, codes: list[str]) -> list[str]:
    """覆寫自選清單，去重並保序，回傳儲存後的清單。"""
    # 去重保序
    seen: set[str] = set()
    deduped = [c for c in codes if not (c in seen or seen.add(c))]  # type: ignore[func-returns-value]

    row = db.get(KvStore, _KEY)
    if row is None:
        row = KvStore(key=_KEY, json_value=json.dumps(deduped, ensure_ascii=False))
        db.add(row)
    else:
        row.json_value = json.dumps(deduped, ensure_ascii=False)

    db.commit()
    logger.info("自選清單更新：%d 檔 → %s", len(deduped), deduped)
    return deduped
