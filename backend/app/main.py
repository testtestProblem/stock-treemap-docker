from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.init_db import init_db
from app.api.routes_account import router as account_router
from app.api.routes_market import router as market_router
from app.api.routes_history import router as history_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 建立資料表（若不存在）
    init_db()
    # 階段 1：初始化 Shioaji 單例
    # 階段 2：啟動排程器
    yield
    # 階段 1：logout Shioaji
    # 階段 2：停止排程器


app = FastAPI(title="股票 Treemap Dashboard API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(account_router)
app.include_router(market_router)
app.include_router(history_router)


@app.get("/health")
def health():
    return {"status": "ok"}
