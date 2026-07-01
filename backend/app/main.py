import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core import shioaji_client
from app.db.init_db import init_db
from app.scheduler import scheduler as sched
from app.services.stock_universe import load_universe
from app.api.routes_account import router as account_router
from app.api.routes_admin import router as admin_router
from app.api.routes_debug import router as debug_router
from app.api.routes_history import router as history_router
from app.api.routes_market import router as market_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 建立 SQLite 資料表
    init_db()

    # 2. 載入股票清單（一次性，存入記憶體）
    load_universe()

    # 3. 初始化 Shioaji 單例
    logger.info("正在登入 Shioaji...")
    shioaji_client.connect(
        api_key=settings.SJ_API_KEY,
        secret_key=settings.SJ_SEC_KEY,
        production=settings.SJ_PRODUCTION,
    )

    # 4. 啟動排程器（含立即執行第一次 snapshot_job）
    sched.start()

    yield

    # 關閉
    sched.stop()
    shioaji_client.disconnect()


app = FastAPI(title="股票 Treemap Dashboard API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(debug_router)
app.include_router(account_router)
app.include_router(market_router)
app.include_router(history_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    return {"status": "ok"}
