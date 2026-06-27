# 階段 1：Shioaji 單例連線

> 目標：在 FastAPI lifespan 建立 Shioaji 全域單例，確保登入只發生一次，並提供除錯端點驗證連線狀態。

## 完成狀態

- [x] 安裝 `shioaji==1.5.4` 至 conda 環境 `stock_treemap`
- [x] `shioaji_client.py` 實作 `connect()` / `disconnect()` / `get_api()` / `get_status()`
- [x] `main.py` lifespan 於啟動時呼叫 `connect()`、關閉時呼叫 `disconnect()`
- [x] 新增 `routes_debug.py`，提供 `GET /api/debug/status`
- [x] `.gitignore` 排除 `shioaji.log`
- [x] Push 至 GitHub（commit `4b2f808`）

---

## 異動檔案

### `backend/app/core/shioaji_client.py`

單例核心邏輯：

```
connect()      ← lifespan 啟動時呼叫，登入並記錄帳戶資訊
disconnect()   ← lifespan 關閉時呼叫，安全登出
get_api()      ← 其他 service 呼叫，取得已登入實例；未初始化則 raise RuntimeError
get_status()   ← /api/debug/status 呼叫，回傳連線狀態 dict
```

重要規則：
- **任何模組禁止自行呼叫 `login()`**，一律透過 `get_api()` 取得實例
- `connect()` 具冪等性（已登入則直接回傳，不重複 login）

### `backend/app/main.py`

```python
@asynccontextmanager
async def lifespan(app):
    init_db()                                      # 建資料表
    shioaji_client.connect(                        # ← 階段 1 新增
        api_key=settings.SJ_API_KEY,
        secret_key=settings.SJ_SEC_KEY,
        production=settings.SJ_PRODUCTION,
    )
    # 階段 2：啟動排程器
    yield
    shioaji_client.disconnect()                    # ← 階段 1 新增
    # 階段 2：停止排程器
```

### `backend/app/api/routes_debug.py`（新增）

```
GET /api/debug/status   ← 回傳 Shioaji 連線狀態與帳戶資訊（開發用）
```

---

## 目前完整路由清單

| 路由 | 狀態 | 說明 |
|------|------|------|
| `GET /health` | ✅ | 伺服器存活確認 |
| `GET /api/debug/status` | ✅ | Shioaji 連線與帳戶資訊（本階段新增） |
| `GET /api/market/snapshot-status` | ✅ | 全市場快照快取狀態（目前回空值） |
| `GET /api/account/assets` | 🔲 佔位 | 階段 3 |
| `GET /api/account/positions` | 🔲 佔位 | 階段 3 |
| `GET /api/market/treemap` | 🔲 佔位 | 階段 4 |
| `GET /api/market/kbars` | 🔲 佔位 | 階段 4 |
| `GET /api/history/performance` | 🔲 佔位 | 階段 5 |

---

## 啟動方式

```powershell
# 終端機 1 — 後端
$env:PYTHONPATH = "c:\Users\TT\Documents\cursor\stock_treemap_final1\backend"
C:\Users\TT\anaconda3\envs\stock_treemap\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

```powershell
# 終端機 2 — 前端
cd c:\Users\TT\Documents\cursor\stock_treemap_final1\frontend
npm run dev
```

啟動後 log 應出現（亂碼為終端機編碼問題，不影響功能）：

```
INFO app.main: 正在登入 Shioaji...
INFO app.core.shioaji_client: Shioaji 登入成功，帳戶數：1
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## 驗收方式

### 1. 確認伺服器存活

```powershell
Invoke-RestMethod http://localhost:8000/health
# 預期：{ "status": "ok" }
```

### 2. 確認 Shioaji 連線成功

```powershell
Invoke-RestMethod http://localhost:8000/api/debug/status | ConvertTo-Json
```

預期回傳（正式環境）：

```json
{
  "connected": true,
  "simulation": false,
  "accounts": ["StockAccount(person_id='...', broker_id='...', account_id='...', signed=true, ...)"],
  "stock_account": "StockAccount(...)"
}
```

驗收重點：
- `connected` 必須為 `true`
- `simulation` 必須為 `false`（正式環境）
- `stock_account` 不為 `null`（確認有股票帳戶）

### 3. 瀏覽器 Console 驗收

開啟 `http://localhost:5173`，在 Console 執行：

```javascript
fetch('/api/debug/status').then(r => r.json()).then(console.log)
// 預期：{ connected: true, simulation: false, ... }
```

### 4. 關閉伺服器確認登出

停止 uvicorn（Ctrl+C）後，log 應出現：

```
INFO app.core.shioaji_client: Shioaji 已登出
```

---

## 注意事項

- Shioaji 每天 `login()` 上限 **1000 次**，禁止在路由或任何請求中重複呼叫
- 若收到 `RuntimeError: Shioaji 尚未初始化`，代表 lifespan 未正確執行，請確認 uvicorn 以 `app.main:app` 啟動
- `shioaji.log` 由 Shioaji 自動產生於執行目錄，已加入 `.gitignore`

---

## 下一步：階段 2

- 解析 `stock_index/*.txt` 建立全市場代號字典（`stock_universe`）
- 建立記憶體快照儲存（`snapshot_store`）
- APScheduler 每 2 分鐘背景抓取全市場 Snapshot（分批 ≤500 檔）
- 驗收：`GET /api/market/snapshot-status` 顯示約 2000+ 檔且時間戳會更新
