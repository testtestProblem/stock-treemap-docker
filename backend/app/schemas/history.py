from __future__ import annotations

from pydantic import BaseModel


class PerformanceSeries(BaseModel):
    """單一績效曲線：日期序列 + 對應的標準化 % 值（以第一筆為基準 = 0）。"""
    dates: list[str]    # ["2025-01-02", "2025-01-03", ...]
    values: list[float] # [0.0, 1.23, -0.45, ...]  (%)


class PerformanceResponse(BaseModel):
    """三條績效曲線：我的資產 / 0050 / 2330，均以首日為基準標準化。"""
    nav: PerformanceSeries
    price_0050: PerformanceSeries
    price_2330: PerformanceSeries
    record_count: int
