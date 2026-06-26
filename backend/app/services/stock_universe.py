"""載入 stock_index/*.txt，建立全市場代號查詢字典。

三份檔案：Listed_Company_list.txt（上市）、OTC_Company_list.txt（上櫃）、ETF_list.txt（ETF）
欄位（TAB 分隔）：代號 名稱 ISIN 上市日 市場別 產業別 CFICode 備註
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)

STOCK_INDEX_DIR = Path(__file__).parents[3] / "stock_index"

_FILES = {
    "Listed_Company_list.txt": "TSE",   # 上市
    "OTC_Company_list.txt": "OTC",      # 上櫃
    "ETF_list.txt": "TSE",              # ETF（多數掛牌於上市）
}


class StockInfo(TypedDict):
    name: str
    industry: str
    market: str       # TSE | OTC
    is_etf: bool


# {code: StockInfo}
_universe: dict[str, StockInfo] = {}


def load_universe() -> None:
    """啟動時呼叫一次，解析三份 txt 建立 _universe。"""
    global _universe
    loaded: dict[str, StockInfo] = {}

    for filename, market in _FILES.items():
        filepath = STOCK_INDEX_DIR / filename
        if not filepath.exists():
            logger.warning("找不到股票清單：%s", filepath)
            continue

        is_etf = filename.startswith("ETF")
        count = 0

        with filepath.open(encoding="utf-8-sig") as f:
            for line in f:
                cols = line.rstrip("\n").split("\t")
                # 跳過標題列（第一欄不是純數字或字母開頭的代號）
                if len(cols) < 2 or cols[0].startswith("有價") or cols[0].startswith("代號"):
                    continue
                code = cols[0].strip()
                name = cols[1].strip() if len(cols) > 1 else ""
                industry = cols[5].strip() if len(cols) > 5 else ""

                if not code or not name:
                    continue

                # ETF 產業別常為空，補預設值
                if not industry:
                    industry = "ETF" if is_etf else "其他"

                loaded[code] = StockInfo(
                    name=name,
                    industry=industry,
                    market=market,
                    is_etf=is_etf,
                )
                count += 1

        logger.info("載入 %s：%d 檔", filename, count)

    _universe = loaded
    logger.info("全市場共載入 %d 檔", len(_universe))


def get_universe() -> dict[str, StockInfo]:
    return _universe


def get_codes_by_market(market: str) -> list[str]:
    """取得特定市場（TSE / OTC）的所有代號。"""
    return [code for code, info in _universe.items() if info["market"] == market]
