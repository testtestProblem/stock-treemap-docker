from app.db.database import Base, engine
from app.db import models  # noqa: F401 — 確保 mapper 已載入


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
