"""APScheduler 排程任務定義。

snapshot_job        ：每 2 分鐘抓全市場快照，更新 snapshot_store（階段 2）
daily_settlement_job：每日 15:40 計算 NAV 並寫入 daily_performance（階段 5）
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date
from itertools import islice

from app.core.shioaji_client import get_api
from app.db.database import SessionLocal
from app.db.models import DailyPerformance
from app.services import snapshot_store, stock_universe
from app.services.account_service import get_assets

logger = logging.getLogger(__name__)

_BATCH_SIZE = 500
_BATCH_DELAY_SEC = 1.5


def _batched(iterable, size: int):
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk


async def snapshot_job() -> None:
    """抓取全市場 Snapshot 並更新記憶體快取。"""
    try:
        api = get_api()
    except RuntimeError:
        logger.warning("snapshot_job: Shioaji 尚未初始化，跳過本次執行")
        return

    universe = stock_universe.get_universe()
    if not universe:
        logger.warning("snapshot_job: stock_universe 尚未載入，跳過本次執行")
        return

    contracts = []
    for code in universe:
        try:
            contract = api.Contracts.Stocks[code]
            if contract is not None:
                contracts.append(contract)
        except (KeyError, AttributeError):
            pass

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

        await asyncio.sleep(_BATCH_DELAY_SEC)

    logger.info("snapshot_job 完成，本次更新 %d 檔，快取總計 %d 檔",
                updated, len(snapshot_store.get_all()))


async def daily_settlement_job() -> None:
    """每日 15:40 計算 NAV 並存入 daily_performance。

    執行前提：
    1. Shioaji 已登入
    2. snapshot_store 中 2330 的 close > 0（確認今日有開盤）

    若 2330 未開盤（假日/停牌），靜默跳過，不寫入資料庫。
    """
    today = date.today().strftime("%Y-%m-%d")
    logger.info("daily_settlement_job 開始，日期 %s", today)

    # 1. 檢查 2330 是否開盤
    snap = snapshot_store.get_all()
    close_2330 = snap.get("2330", {}).get("close", 0)
    if not close_2330:
        logger.info("daily_settlement_job: 2330 收盤價為 0，今日可能未開盤，跳過")
        return

    close_0050 = snap.get("0050", {}).get("close", 0)
    if not close_0050:
        logger.warning("daily_settlement_job: 0050 收盤價為 0，仍繼續寫入（以 0 記錄）")

    # 2. 計算 NAV
    try:
        api = get_api()
        assets = get_assets(api)
        nav = assets.nav
    except Exception as e:
        logger.error("daily_settlement_job: 取得 NAV 失敗：%s", e)
        return

    # 3. 寫入 daily_performance（當日已存在則 upsert）
    db = SessionLocal()
    try:
        row = db.get(DailyPerformance, today)
        if row is None:
            row = DailyPerformance(
                date=today,
                nav=nav,
                price_0050=close_0050,
                price_2330=close_2330,
            )
            db.add(row)
        else:
            row.nav = nav
            row.price_0050 = close_0050
            row.price_2330 = close_2330

        db.commit()
        logger.info(
            "daily_settlement_job 完成：date=%s nav=%.0f 0050=%.2f 2330=%.0f",
            today, nav, close_0050, close_2330,
        )
    except Exception as e:
        db.rollback()
        logger.error("daily_settlement_job: 寫入 DB 失敗：%s", e)
    finally:
        db.close()
