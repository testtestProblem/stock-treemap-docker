# 階段 0：鷹架（Scaffold）

> 目標：建立前後端基礎骨架，確認可正常啟動，不含任何商業邏輯。

## 完成狀態

- [x] 後端資料夾結構與佔位模組
- [x] conda 虛擬環境 `stock_treemap` + 相依安裝
- [x] FastAPI 應用程式可啟動，`/health` 正常回應
- [x] 前端 Vite + React 19 + TypeScript 專案建立
- [x] Tailwind CSS v4 設定完成
- [x] 前端相依安裝（D3、Recharts、Motion、Lucide）
- [x] Vite proxy 設定（`/api` 與 `/health` 轉發至 `:8000`）
- [x] 前端空白 Dashboard 版面鷹架
- [x] `.gitignore`（排除 `.env`、`*.db`、`node_modules` 等）

---

## 目錄結構

```
stock_treemap_final1/
├── .env                          ← Shioaji 金鑰（不進 git）
├── .gitignore
├── ARCHITECTURE.md               ← 全專案架構設計文件
├── CLAUDE.md                     ← 專案規格書
├── docs/
│   └── phase0-scaffold.md        ← 本文件
├── stock_index/
│   ├── Listed_Company_list.txt   ← 上市股（~1072 檔）
│   ├── OTC_Company_list.txt      ← 上櫃股（~876 檔）
│   └── ETF_list.txt              ← ETF（~224 檔）
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py               ← FastAPI app + lifespan + CORS + /health
│   │   ├── config.py             ← pydantic-settings 讀 .env
│   │   ├── core/
│   │   │   ├── shioaji_client.py ← Shioaji 單例佔位（階段 1 填入）
│   │   │   └── cache.py          ← TTLCache 工具
│   │   ├── db/
│   │   │   ├── database.py       ← SQLite engine / SessionLocal
│   │   │   ├── models.py         ← 3 張資料表定義
│   │   │   └── init_db.py        ← create_all()
│   │   ├── services/
│   │   │   ├── stock_universe.py ← 股票清單載入佔位（階段 2）
│   │   │   ├── snapshot_store.py ← 記憶體快照儲存佔位（階段 2）
│   │   │   ├── account_service.py← NAV / 持倉合併佔位（階段 3）
│   │   │   ├── market_service.py ← Treemap / kbars 佔位（階段 4）
│   │   │   └── history_service.py← 績效標準化佔位（階段 5）
│   │   ├── scheduler/
│   │   │   ├── jobs.py           ← 排程任務佔位（階段 2、5）
│   │   │   └── scheduler.py      ← APScheduler 實例佔位
│   │   └── api/
│   │       ├── routes_account.py ← /api/account/* 佔位（階段 3）
│   │       ├── routes_market.py  ← /api/market/* 佔位（階段 4）
│   │       └── routes_history.py ← /api/history/* 佔位（階段 5）
│   ├── data/
│   │   └── app.db                ← SQLite（自動建立，不進 git）
│   └── tests/
│
└── frontend/
    ├── vite.config.ts            ← Tailwind v4 plugin + proxy 設定
    ├── package.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css             ← @import "tailwindcss";
        ├── api/
        │   ├── client.ts         ← fetch 包裝（5 個 API 呼叫）
        │   └── types.ts          ← 所有回應型別定義
        ├── lib/
        │   └── colors.ts         ← 美式漲跌色 + treemapColor()
        └── components/
            └── layout/
                └── DashboardLayout.tsx ← 空白版面鷹架
```

---

## 資料庫資料表（已建立，尚未寫入資料）

| 資料表 | 用途 | 主要欄位 |
|--------|------|----------|
| `daily_performance` | 每日 15:40 排程寫入 | date(PK), nav, price_0050, price_2330 |
| `kv_store` | 自選清單等 JSON 鍵值 | key(PK), json_value(TEXT) |
| `asset_snapshot` | 當日資產/持倉原始備查 | date(PK), payload(TEXT JSON) |

---

## 啟動方式

### 後端（終端機 1）

```powershell
$env:PYTHONPATH = "c:\Users\TT\Documents\cursor\stock_treemap_final1\backend"
C:\Users\TT\anaconda3\envs\stock_treemap\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端（終端機 2）

```powershell
cd c:\Users\TT\Documents\cursor\stock_treemap_final1\frontend
npm run dev
```

前端網址：`http://localhost:5173`
後端網址：`http://localhost:8000`

---

## 驗收方式

### 1. 後端 `/health`

```powershell
Invoke-RestMethod http://localhost:8000/health
```

預期回傳：
```json
{ "status": "ok" }
```

### 2. 瀏覽器 Console 測試 Proxy

開啟 `http://localhost:5173`，在 Console 輸入：

```javascript
// 測試 proxy 是否通（預期：{ "status": "ok" }）
fetch('/health').then(r => r.json()).then(console.log)

// 測試 /api 路由是否可達（預期：{ "total": 0, "last_updated": null }）
fetch('/api/market/snapshot-status').then(r => r.json()).then(console.log)
```

若回傳包含 `detail: 'Not Found'` 表示 proxy 正常、只是路由不存在（這是正確行為，因為大多路由是階段 3-5 才實作）。

### 3. 前端建置無錯誤

```powershell
cd c:\Users\TT\Documents\cursor\stock_treemap_final1\frontend
npm run build
```

預期：`built in Xms`，無 TypeScript 或 Vite 錯誤。

---

## 各路由目前狀態

| 路由 | 狀態 | 實作階段 |
|------|------|----------|
| `GET /health` | ✅ 可用 | 已完成 |
| `GET /api/market/snapshot-status` | ✅ 可用（回傳空值） | 已完成 |
| `GET /api/account/assets` | 🔲 佔位 | 階段 3 |
| `GET /api/account/positions` | 🔲 佔位 | 階段 3 |
| `GET /api/market/treemap` | 🔲 佔位 | 階段 4 |
| `GET /api/market/kbars` | 🔲 佔位 | 階段 4 |
| `GET /api/history/performance` | 🔲 佔位 | 階段 5 |

---

## 下一步：階段 1

Shioaji 單例連線：

- `lifespan` 呼叫 `shioaji_client.connect()`（需先 `pip install shioaji`）
- 新增 `GET /api/debug/status` 顯示登入狀態與帳戶資訊
- 驗收：呼叫端點看到登入成功與 `stock_account` 資訊
