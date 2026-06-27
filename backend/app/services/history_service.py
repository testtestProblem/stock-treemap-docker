"""歷史績效商業邏輯：讀取 daily_performance 並標準化為 %。

標準化公式：
  pct_change[i] = (value[i] / value[0] - 1) × 100

若資料少於 2 筆，回傳現有資料（不拋錯）。
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DailyPerformance
from app.schemas.history import PerformanceResponse, PerformanceSeries

logger = logging.getLogger(__name__)


def get_performance(db: Session) -> PerformanceResponse:
    """從 daily_performance 讀取所有紀錄，回傳三條標準化 % 曲線。"""
    rows = (
        db.execute(select(DailyPerformance).order_by(DailyPerformance.date.asc()))
        .scalars()
        .all()
    )

    if not rows:
        empty = PerformanceSeries(dates=[], values=[])
        return PerformanceResponse(
            nav=empty, price_0050=empty, price_2330=empty, record_count=0
        )

    dates      = [r.date       for r in rows]
    nav_vals   = [r.nav        for r in rows]
    p0050_vals = [r.price_0050 for r in rows]
    p2330_vals = [r.price_2330 for r in rows]

    return PerformanceResponse(
        nav=PerformanceSeries(dates=dates, values=_normalize(nav_vals)),
        price_0050=PerformanceSeries(dates=dates, values=_normalize(p0050_vals)),
        price_2330=PerformanceSeries(dates=dates, values=_normalize(p2330_vals)),
        record_count=len(rows),
    )


def _normalize(values: list[float]) -> list[float]:
    """以第一筆為基準，計算每日累積報酬率（%）。"""
    if not values or values[0] == 0:
        return [0.0] * len(values)
    base = values[0]
    return [round((v / base - 1) * 100, 4) for v in values]
