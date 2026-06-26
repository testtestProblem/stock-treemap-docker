from datetime import datetime

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DailyPerformance(Base):
    """每日 15:40 排程寫入：NAV 與基準收盤價。"""

    __tablename__ = "daily_performance"

    date: Mapped[str] = mapped_column(String(10), primary_key=True)
    nav: Mapped[float] = mapped_column(Float, nullable=False)
    price_0050: Mapped[float] = mapped_column(Float, nullable=False)
    price_2330: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class KvStore(Base):
    """通用 JSON 鍵值儲存（自選清單、設定等）。"""

    __tablename__ = "kv_store"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    json_value: Mapped[str] = mapped_column(Text, nullable=False)


class AssetSnapshot(Base):
    """每日資產/持倉/交割原始結算 JSON 備查。"""

    __tablename__ = "asset_snapshot"

    date: Mapped[str] = mapped_column(String(10), primary_key=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
