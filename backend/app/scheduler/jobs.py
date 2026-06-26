"""APScheduler 排程任務定義。

snapshot_job        ：每 2 分鐘抓全市場快照，更新 snapshot_store（階段 2）
daily_settlement_job：每日 15:40 計算 NAV 並寫入 daily_performance（階段 5）
"""
from __future__ import annotations

import asyncio
import logging
from itertools import islice

from app.core.shioaji_client import get_api
from app.services import snapshot_store, stock_universe

logger = logging.getLogger(__name__)

_BATCH_SIZE = 500        # snapshots() 單次上限
_BATCH_DELAY_SEC = 1.5   # 批次間隔（秒），避開 5 秒 50 次限流


def _batched(iterable, size: int):
    """將可迭代物件切分成固定大小的批次。"""
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk


async def snapshot_job() -> None:
    """抓取全市場 Snapshot 並更新記憶體快取。

    僅取得在 Shioaji 商品檔中存在的合約，靜默跳過查無的代號。
    """
    try:
        api = get_api()
    except RuntimeError:
        logger.warning("snapshot_job: Shioaji 尚未初始化，跳過本次執行")
        return

    universe = stock_universe.get_universe()
    if not universe:
        logger.warning("snapshot_job: stock_universe 尚未載入，跳過本次執行")
        return

    # 取得所有可用的合約物件（過濾掉商品檔中不存在的代號）
    contracts = []
    for code in universe:
        try:
            contract = api.Contracts.Stocks[code]
            if contract is not None:
                contracts.append(contract)
        except (KeyError, AttributeError):
            pass  # 部分代號（如特定 ETF）可能不在股票商品檔中

    if not contracts:
        logger.warning("snapshot_job: 無可用合約，跳過本次執行")
        return

    logger.info("snapshot_job 開始，共 %d 個合約，分批大小 %d", len(contracts), _BATCH_SIZE)
    updated = 0

    for batch in _batched(contracts, _BATCH_SIZE):
        try:
            snapshots = api.snapshots(batch)
            batch_data: dict[str, dict] = {}
            for snap in snapshots:
                code = snap.code
                info = universe.get(code, {})
                batch_data[code] = {
                    "code": code,
                    "name": info.get("name", ""),
                    "industry": info.get("industry", "其他"),
                    "market": info.get("market", "TSE"),
                    "is_etf": info.get("is_etf", False),
                    "close": snap.close,
                    "change_price": snap.change_price,
                    "change_rate": snap.change_rate,
                    "total_volume": snap.total_volume,
                    "total_amount": snap.total_amount,
                    "open": snap.open,
                    "high": snap.high,
                    "low": snap.low,
                }
                updated += 1
            snapshot_store.update(batch_data)
        except Exception as e:
            logger.error("snapshot_job 批次抓取失敗：%s", e)

        # 避開限流：批次間等待
        await asyncio.sleep(_BATCH_DELAY_SEC)

    logger.info("snapshot_job 完成，本次更新 %d 檔，快取總計 %d 檔",
                updated, len(snapshot_store.get_all()))


# 階段 5 實作
async def daily_settlement_job() -> None:
    """每日 15:40 計算 NAV 並存入 daily_performance。"""
    # TODO 階段 5 實作
    pass
