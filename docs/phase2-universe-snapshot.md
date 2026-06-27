# 階段 2：股票清單載入 + 全市場快照排程

> 目標：啟動時一次性載入全市場代號字典，並以 APScheduler 每 2 分鐘在背景抓取全市場 Snapshot 存入記憶體，前端請求只讀快取，不直接觸發 Shioaji。

## 完成狀態

- [x] `stock_universe.py` 解析三份 txt，載入 2185 檔
- [x] `snapshot_store.py` 提供記憶體快取的 `update()` / `get_all()` / `get_status()`
- [x] `jobs.py` 實作 `snapshot_job`（分批 ≤500 檔、批間延遲 1.5 秒）
- [x] `scheduler.py` 掛載 snapshot_job（每 2 分鐘、啟動立即執行）
- [x] `main.py` lifespan 加入 `load_universe()` 與 `sched.start()` / `sched.stop()`
- [x] `routes_market.py` `/api/market/snapshot-status` 加入 `universe_total` 欄位
- [x] pytest 6 項全過
- [x] Push 至 GitHub（commit `9cbd5ed`）

---

## 異動檔案

### `backend/app/services/stock_universe.py`

解析規則：

| 來源檔案 | market | is_etf | 產業別為空時預設 |
|----------|--------|--------|----------------|
| `Listed_Company_list.txt` | TSE | false | 其他 |
| `OTC_Company_list.txt` | OTC | false | 其他 |
| `ETF_list.txt` | TSE | true | ETF |

欄位說明（TAB 分隔）：

```
col 0 = 代號
col 1 = 名稱
col 4 = 市場別
col 5 = 產業別
```

對外介面：

```python
load_universe()              # 啟動時呼叫一次
get_universe()               # 回傳 {code: StockInfo}
get_codes_by_market("TSE")   # 取得特定市場代號清單
```

### `backend/app/scheduler/jobs.py`

```
snapshot_job() 流程：
  1. get_api()             → 取得 Shioaji 實例（未連線則 skip）
  2. get_universe()        → 取得所有代號
  3. api.Contracts.Stocks[code]  → 查合約（查不到則 skip）
  4. 每批 ≤500 個合約呼叫 api.snapshots()
  5. 批次間 asyncio.sleep(1.5s)   → 保護 5 秒 50 次限流
  6. snapshot_store.update(batch_data)
```

每筆快取資料格式：

```python
{
  "code": "2330",
  "name": "台積電",
  "industry": "半導體業",
  "market": "TSE",
  "is_etf": False,
  "close": 980.0,
  "change_price": 5.0,
  "change_rate": 0.51,      # % 漲跌幅，Treemap 著色用
  "total_volume": 25820,
  "total_amount": 25313960000,  # 成交值，Treemap 大小權重
  "open": 975.0,
  "high": 982.0,
  "low": 974.0,
}
```

### `backend/app/scheduler/scheduler.py`

```python
scheduler.add_job(
    snapshot_job,
    trigger="interval",
    minutes=2,
    id="snapshot_job",
    max_instances=1,              # 上一批未完成時不重複啟動
    next_run_time=datetime.now(), # 啟動立即執行
)
```

### `backend/app/main.py` — lifespan 啟動順序

```
1. init_db()         建立 SQLite 資料表
2. load_universe()   載入股票清單（一次性）
3. shioaji_client.connect()  登入 Shioaji
4. sched.start()     啟動排程器（同時觸發第一次 snapshot_job）
```

---

## 載入統計

| 來源 | 檔數 |
|------|------|
| 上市（Listed） | 1085 |
| 上櫃（OTC） | 884 |
| ETF | 224 |
| **universe 合計** | **2185** |
| snapshot_store 快取 | 2180（5 檔在 Shioaji 商品檔中無對應合約） |

---

## 啟動方式

```powershell
$env:PYTHONPATH = "c:\Users\TT\Documents\cursor\stock_treemap_final1\backend"
C:\Users\TT\anaconda3\envs\stock_treemap\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

啟動後 log 應出現：

```
INFO stock_universe: 載入 Listed_Company_list.txt：1085 檔
INFO stock_universe: 載入 OTC_Company_list.txt：884 檔
INFO stock_universe: 載入 ETF_list.txt：224 檔
INFO stock_universe: 全市場共載入 2185 檔
INFO app.main: 正在登入 Shioaji...
INFO shioaji_client: Shioaji 登入成功，帳戶數：1
INFO apscheduler.scheduler: Scheduler started
INFO app.scheduler.scheduler: APScheduler 已啟動，snapshot_job 每 2 分鐘執行
INFO apscheduler.executors.default: Running job "snapshot_job ..."
INFO jobs: snapshot_job 開始，共 2180 個合約，分批大小 500
INFO jobs: snapshot_job 完成，本次更新 2180 檔，快取總計 2180 檔
```

---

## 驗收方式

### 1. pytest 單元測試

```powershell
$env:PYTHONPATH = "c:\Users\TT\Documents\cursor\stock_treemap_final1\backend"
C:\Users\TT\anaconda3\envs\stock_treemap\Scripts\pytest.exe backend/tests/test_stock_universe.py -v
```

預期：6 passed

```
test_total_count          PASSED  (universe > 2000)
test_tsmc_exists          PASSED  (2330 = 台積電, TSE)
test_0050_exists          PASSED  (0050 = 元大台灣50, ETF)
test_otc_stock_exists     PASSED  (OTC > 500 檔)
test_no_empty_name        PASSED
test_industry_not_empty   PASSED
```

### 2. 快照快取端點

```powershell
Invoke-RestMethod http://localhost:8000/api/market/snapshot-status | ConvertTo-Json
```

預期回傳：

```json
{
  "total": 2180,
  "last_updated": "2026-06-26T23:09:46.871793",
  "universe_total": 2185
}
```

驗收重點：
- `total` > 2000（快照已更新）
- `last_updated` 不為 `null`
- `universe_total` = 2185
- 等待 2 分鐘後再呼叫，`last_updated` 應自動更新

### 3. 瀏覽器 Console

```javascript
fetch('/api/market/snapshot-status').then(r => r.json()).then(console.log)
// 預期：{ total: 2180, last_updated: "...", universe_total: 2185 }
```

### 4. 限流保護驗收

觀察 log，5 批次（2180/500 ≈ 5）應在約 10 秒內完成：

```
snapshot_job 開始
# 批次 1（約 1.5s）
# 批次 2（約 1.5s）
# ...
snapshot_job 完成，本次更新 2180 檔
```

---

## 注意事項

- `STOCK_INDEX_DIR` 路徑：`Path(__file__).parents[3] / "stock_index"`（相對 `backend/app/services/stock_universe.py` 往上 3 層到專案根目錄）
- `max_instances=1`：若某次 snapshot_job 超過 2 分鐘尚未完成，下一次觸發會被跳過，避免重複打 API
- 非交易時間（盤後/盤前）仍會執行排程，此時 Shioaji 回傳的資料為最後一次交易資料，為正常現象

---

## 下一步：階段 3

- `GET /api/account/assets`：NAV = acc_balance + 持倉市值 + settlements(T+1/T+2)
- `GET /api/account/positions`：整股（×1000 股）與零股合併，以 code 為 key 合計
- pytest mock 整股/零股 list 驗 NAV 公式與合併邏輯
