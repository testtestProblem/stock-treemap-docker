"""載入 stock_index/*.txt，建立全市場代號查詢字典。

階段 2 實作完整邏輯，此處提供佔位結構。
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

STOCK_INDEX_DIR = Path(__file__).parents[4] / "stock_index"


class StockInfo(TypedDict):
    name: str
    industry: str
    market: str


# 格式：{code: StockInfo}
_universe: dict[str, StockInfo] = {}


def load_universe() -> None:
    """啟動時呼叫一次，解析三份 txt 建立 _universe。"""
    # TODO 階段 2 實作
    pass


def get_universe() -> dict[str, StockInfo]:
    return _universe
