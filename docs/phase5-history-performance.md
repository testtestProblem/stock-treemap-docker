# 階段 5：歷史績效 + 每日排程

> 目標：每日 15:40 自動計算 NAV 並記錄 0050/2330 收盤價寫入 SQLite；`/api/history/performance` 回傳三條標準化 % 曲線供前端繪圖。

---

## 完成狀態

- [x] `schemas/history.py` 定義 `PerformanceSeries`、`PerformanceResponse`
- [x] `services/history_service.py` 實作 `get_performance()` 與 `_normalize()`
- [x] `scheduler/jobs.py` 實作 `daily_settlement_job`（含 2330 開盤檢查、upsert）
- [x] `scheduler/scheduler.py` 掛載 15:40 mon-fri cron job
- [x] `api/routes_history.py` 實作 `GET /performance` 與 `POST /trigger-daily`
- [x] pytest 9 項全過
- [x] 實機驗收：手動觸發寫入 `nav=2,459,507  0050=103.1  2330=2340.0`

---

## 端點契約

| Method | 路徑 | 說明 |
|--------|------|------|
| `GET` | `/api/history/performance` | 三條標準化 % 曲線（我的資產 / 0050 / 2330） |
| `POST` | `/api/history/trigger-daily` | 手動觸發每日結算（除錯 / 補跑，正式可加 Auth） |

---

## 回應結構

```json
{
  "record_count": 30,
  "nav": {
    "dates":  ["2026-05-01", "2026-05-02", "..."],
    "values": [0.0, 1.23, -0.45, "..."]
  },
  "price_0050": {
    "dates":  ["2026-05-01", "..."],
    "values": [0.0, 0.67, "..."]
  },
  "price_2330": {
    "dates":  ["2026-05-01", "..."],
    "values": [0.0, 2.10, "..."]
  }
}
```

**標準化公式**：以最早一筆為基準（= 0%），後續每日累積報酬率：

```
values[i] = (raw[i] / raw[0] - 1) × 100
```

三條曲線共用同一 `dates` 序列，前端可直接對應畫在同一圖表上做績效比較。

---

## daily_settlement_job 執行流程

```
15:40 觸發（mon-fri, Asia/Taipei）
  │
  ├─ 1. 讀 snapshot_store["2330"]["close"]
  │      close == 0 → 今日未開盤，靜默跳過
  │
  ├─ 2. 讀 snapshot_store["0050"]["close"]
  │      close == 0 → 記錄警告，仍繼續（以 0 寫入）
  │
  ├─ 3. 呼叫 get_assets(api) 取得當日 NAV
  │      失敗 → log error，中止本次執行
  │
  └─ 4. Upsert DailyPerformance(date=today, nav, price_0050, price_2330)
         當日已有紀錄 → 覆寫（支援補跑）
         成功 → log 確認訊息
```

---

## 資料庫設計（daily_performance）

```sql
CREATE TABLE daily_performance (
    date       TEXT PRIMARY KEY,   -- "2026-06-27"
    nav        REAL NOT NULL,
    price_0050 REAL NOT NULL,
    price_2330 REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 異動檔案

### `backend/app/schemas/history.py`（新增）

```python
class PerformanceSeries(BaseModel):
    dates: list[str]
    values: list[float]   # 標準化後的 %

class PerformanceResponse(BaseModel):
    nav: PerformanceSeries
    price_0050: PerformanceSeries
    price_2330: PerformanceSeries
    record_count: int
```

### `backend/app/services/history_service.py`（實作）

```
get_performance(db)
  ├─ SELECT * FROM daily_performance ORDER BY date ASC
  ├─ 若空 → 回傳空曲線（record_count=0）
  └─ _normalize(values) 分別處理三個序列

_normalize(values)
  ├─ 若 base == 0 → 回傳全 0 列表
  └─ return [(v/base - 1) * 100 for v in values]
```

### `backend/app/scheduler/jobs.py`（更新）

- 新增 `daily_settlement_job()`：
  1. 檢查 2330 開盤
  2. 取 NAV（`get_assets`）
  3. Upsert `DailyPerformance`

### `backend/app/scheduler/scheduler.py`（更新）

```python
scheduler.add_job(
    daily_settlement_job,
    trigger="cron",
    hour=15, minute=40,
    day_of_week="mon-fri",
    id="daily_settlement_job",
    max_instances=1,
)
```

### `backend/app/api/routes_history.py`（實作）

- `GET /performance` → `history_service.get_performance(db)`
- `POST /trigger-daily` → 直接 `await daily_settlement_job()`

---

## 目錄結構（階段 5 新增 / 異動）

```
backend/
├── app/
│   ├── api/
│   │   └── routes_history.py     ← 完整實作（替換 TODO）
│   ├── schemas/
│   │   └── history.py            ← 新增
│   ├── services/
│   │   └── history_service.py    ← 完整實作（替換 TODO）
│   └── scheduler/
│       ├── jobs.py               ← 新增 daily_settlement_job
│       └── scheduler.py          ← 掛載 cron job
└── tests/
    └── test_history_service.py   ← 新增（9 個測試案例）
```

---

## 實機驗收結果（2026-06-27）

```
POST /api/history/trigger-daily
  → {"status": "ok"}

SQLite daily_performance:
  date=2026-06-27  nav=2,459,507  0050=103.1  2330=2340.0

GET /api/history/performance
  → record_count=1
    nav.values     = [0.0]   ← 首筆基準本身為 0%
    price_0050.values = [0.0]
    price_2330.values = [0.0]
```

---

## 驗收清單

### 自動測試

```bash
conda run -n stock_treemap pytest backend/tests/test_history_service.py -v
# 預期：9 passed
```

| 測試名稱 | 驗證項目 |
|----------|----------|
| `test_normalize_base_is_zero` | 第一筆輸出為 0.0 |
| `test_normalize_correct_pct` | (210/200-1)×100 = 5.0 等數值正確性 |
| `test_normalize_empty` | 空輸入回傳空列表 |
| `test_normalize_single` | 單筆回傳 [0.0] |
| `test_normalize_zero_base` | 基準為 0 時不拋例外，全回傳 0.0 |
| `test_performance_empty_db` | 空資料庫回傳 record_count=0 |
| `test_performance_single_row` | 單筆資料 values=[0.0] |
| `test_performance_multiple_rows` | 三條曲線長度一致，數值驗算正確 |
| `test_performance_dates_order` | 日期保持 asc 排序 |

### 手動 API 驗收

```bash
# 1. 確認 DB 初始為空（首次啟動）
curl http://localhost:8000/api/history/performance
# 預期：record_count=0

# 2. 手動觸發每日結算
curl -X POST http://localhost:8000/api/history/trigger-daily
# 預期：{"status": "ok", "message": "..."}

# 3. 確認寫入後有一筆資料
curl http://localhost:8000/api/history/performance
# 預期：record_count=1，三條 values=[0.0]

# 4. 再次觸發（測試 upsert 不重複建立）
curl -X POST http://localhost:8000/api/history/trigger-daily
curl http://localhost:8000/api/history/performance
# 預期：record_count 仍為 1（upsert 覆寫同日）
```

### 人工驗收

| 項目 | 驗證方式 |
|------|----------|
| NAV 值 | 與 `/api/account/assets` 的 `nav` 欄位吻合 |
| 0050 收盤價 | 與永豐 App / TW Stock 行情比對 |
| 2330 收盤價 | 與永豐 App / TW Stock 行情比對 |
| 2330 未開盤跳過 | 非交易日呼叫 trigger-daily → DB 不新增紀錄 |

---

## 已知限制

1. **`trigger-daily` 無身份驗證**：任何人可呼叫。正式環境建議加 API Key Header 或僅允許本機 IP。
2. **快照延遲**：`daily_settlement_job` 使用 `snapshot_store` 的快取價，若排程在 15:40 正好是快照更新前，收盤價可能是 15:38 的資料。誤差極小，可接受。
3. **補跑機制**：目前只支援「觸發當下的今日資料」。若需補跑歷史特定日期，需手動插入 SQL 或擴充 API（本期未實作）。
4. **首筆 values = 0.0 是正常的**：績效圖基準點即為開始追蹤的第一天，繪圖時前端顯示為「0%」。累積兩筆以上才能看到漲跌曲線。
