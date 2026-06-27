# 階段 4：行情端點 — Treemap 產業分層 + kbars K 線

> 目標：實作 `/api/market/treemap`（讀背景快照快取、產業分層）、`/api/market/kbars`（TTL 快取保護）、以及自選清單 CRUD（SQLite kv_store）。

---

## 完成狀態

- [x] `schemas/market.py` 定義 Treemap / kbars / Watchlist 回應模型
- [x] `services/watchlist_service.py` 自選清單 SQLite CRUD（kv_store key=`watchlist`）
- [x] `services/market_service.py` 實作 `build_treemap()` 與 `get_kbars()`
- [x] `api/routes_market.py` 完整路由（treemap / kbars / watchlist GET+PUT）
- [x] pytest 8 項全過
- [x] 實機驗收：treemap 36 產業、kbars 5049 筆分鐘 K、cache hit 確認

---

## 端點契約

| Method | 路徑 | 說明 |
|--------|------|------|
| `GET` | `/api/market/treemap?mode=market` | 全市場 Treemap（讀快照快取） |
| `GET` | `/api/market/treemap?mode=watchlist` | 自選股 Treemap |
| `GET` | `/api/market/kbars?code=2330&start=&end=` | 個股日/分鐘 K 線 |
| `GET` | `/api/market/watchlist` | 讀取自選清單 |
| `PUT` | `/api/market/watchlist` | 覆寫自選清單（body: `{"codes": ["2330","0050"]}`） |
| `GET` | `/api/market/snapshot-status` | 快照快取狀態（除錯用） |

---

## Treemap 資料結構

```json
{
  "mode": "market",
  "name": "全市場",
  "last_updated": "2026-06-27T11:59:14.054762",
  "children": [
    {
      "name": "半導體業",
      "children": [
        {
          "code": "2330",
          "name": "台積電",
          "industry": "半導體業",
          "close": 2340.0,
          "change_price": -50.0,
          "change_rate": -2.09,
          "total_volume": 18523000,
          "total_amount": 4.3e10
        }
      ]
    }
  ]
}
```

D3 使用 `total_amount`（成交值）作為方塊大小，`change_rate` 作為顏色依據。

---

## kbars 重要限制（Shioaji API）

> ⚠️ **單次查詢上限：28 天**（保守值，Shioaji 官方限制 30 日曆天）

- `start` / `end` 未傳時，預設為「今日往前 28 天 → 今日」
- 若傳入範圍超過 28 天，**自動截斷**起始日（不拋錯）
- kbars 回傳為**分鐘 K**（非日 K），5049 筆 / 28 天屬正常數量
- Shioaji 回傳 `ts` 為 nanoseconds，服務層除以 `1e9` 轉為 Unix 秒

```
cache_key = "{code}:{start}:{end}"
TTL = 60 秒（core/cache.py 的 kbars_cache）
```

---

## 異動檔案

### `backend/app/schemas/market.py`（新增）

```python
class TreemapStock(BaseModel):
    code, name, industry, close, change_price, change_rate,
    total_volume, total_amount

class IndustryNode(BaseModel):
    name: str
    children: list[TreemapStock]

class TreemapResponse(BaseModel):
    mode, name, children: list[IndustryNode], last_updated

class KbarItem(BaseModel):
    ts, open, high, low, close, volume, amount

class KbarsResponse(BaseModel):
    code, start, end, bars: list[KbarItem], from_cache

class WatchlistResponse(BaseModel):
    codes: list[str]

class WatchlistUpdate(BaseModel):
    codes: list[str]
```

### `backend/app/services/watchlist_service.py`（新增）

- `get_watchlist(db)` → `list[str]`
- `set_watchlist(db, codes)` → 去重保序，覆寫 kv_store，回傳儲存後清單

### `backend/app/services/market_service.py`（實作）

```
build_treemap(mode, watchlist)
  ├─ snapshot_store.get_all()
  ├─ mode=watchlist 時依 watchlist 過濾
  ├─ 過濾 total_amount == 0 的非交易標的
  ├─ 依 industry 分組，按總成交值降冪排序產業
  └─ 回傳 TreemapResponse

get_kbars(api, code, start, end)
  ├─ 限制 end - start ≤ 28 天
  ├─ 查 kbars_cache["{code}:{start}:{end}"]
  ├─ cache HIT → from_cache=True 直接回傳
  ├─ cache MISS → api.kbars() → 組裝 KbarItem
  │    ts_ns // 1_000_000_000 轉為 Unix 秒
  └─ 存入 kbars_cache，回傳 KbarsResponse
```

### `backend/app/api/routes_market.py`（更新）

- `GET /treemap` → `build_treemap(mode, watchlist)`
- `GET /kbars` → `get_kbars(api, code, start, end)`
- `GET /watchlist` → `get_watchlist(db)`
- `PUT /watchlist` → `set_watchlist(db, codes)`

---

## 目錄結構（階段 4 新增 / 異動）

```
backend/
├── app/
│   ├── api/
│   │   └── routes_market.py     ← 完整實作（替換 TODO）
│   ├── schemas/
│   │   └── market.py            ← 新增
│   └── services/
│       ├── market_service.py    ← 完整實作（替換 TODO）
│       └── watchlist_service.py ← 新增
└── tests/
    └── test_market_service.py   ← 新增（8 個測試案例）
```

---

## 實機驗收結果（2026-06-27）

```
GET /api/market/treemap?mode=market
  → mode=market  industries=36  last_updated=2026-06-27T11:59:14

Top 5 產業（依成交值）：
  半導體業         202 stocks  total_amount=778,188,790,750
  電子零組件業      211 stocks  total_amount=410,746,670,400
  ETF              224 stocks  total_amount=136,355,297,104
  光電業           117 stocks  total_amount=110,590,880,200
  電腦及週邊設備業  110 stocks  total_amount= 81,605,216,910

GET /api/market/treemap?mode=watchlist  (watchlist=["2330","0050","00673R"])
  → 2 個產業  3 檔股票

GET /api/market/kbars?code=2330
  → bars=5049  start=2026-05-30  end=2026-06-27  from_cache=False
  第二次呼叫  from_cache=True
```

---

## 驗收清單

### 自動測試

```bash
conda run -n stock_treemap pytest backend/tests/test_market_service.py -v
# 預期：8 passed
```

| 測試名稱 | 驗證項目 |
|----------|----------|
| `test_treemap_market_all` | 成交值 0 的標的被過濾 |
| `test_treemap_industry_grouping` | 同產業歸入同一節點 |
| `test_treemap_industry_sorted_by_amount` | 產業按總成交值降冪排列 |
| `test_treemap_watchlist_filter` | watchlist 模式只回傳指定代號 |
| `test_treemap_watchlist_missing_code` | 不在快照中的代號靜默略過 |
| `test_kbars_returns_correct_bars` | ts 從 ns → 秒、OHLCV 正確 |
| `test_kbars_cache_hit` | 第二次相同查詢命中快取，Shioaji 只呼叫一次 |
| `test_kbars_unknown_code` | 找不到合約回傳空 bars，不拋例外 |

### 手動 API 驗收

```bash
# 1. 全市場 treemap（確認 industries > 30，last_updated 有值）
curl http://localhost:8000/api/market/treemap?mode=market

# 2. 自選清單寫入
curl -X PUT http://localhost:8000/api/market/watchlist \
     -H "Content-Type: application/json" \
     -d '{"codes": ["2330","0050","00673R"]}'

# 3. 自選股 treemap（確認只回傳 3 檔）
curl http://localhost:8000/api/market/treemap?mode=watchlist

# 4. kbars（確認 bars > 0，from_cache=false）
curl "http://localhost:8000/api/market/kbars?code=2330"

# 5. 再次呼叫（確認 from_cache=true）
curl "http://localhost:8000/api/market/kbars?code=2330"
```

---

## 已知限制

1. **kbars 為分鐘 K**：Shioaji 預設回傳分鐘 K，若需日 K 需傳入 `freq` 參數（本期未實作，前端依需求擴充）。
2. **treemap 資料時效**：依賴 APScheduler 每 2 分鐘更新的快照，非即時串流；`last_updated` 欄位供前端顯示資料新鮮度。
3. **非交易日 kbars**：`start`/`end` 若跨非交易日（假日），Shioaji 自動跳過，bars 數量會少於預期，屬正常現象。
4. **快照量為 0 時 treemap 空回應**：若伺服器剛啟動且排程尚未跑完，`snapshot_store` 為空，`treemap` 回傳空 children。前端需顯示載入狀態（階段 7 處理）。
