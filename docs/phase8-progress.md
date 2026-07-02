# Phase 8 進度摘要（全域準備 → Task 8-2）

> 記錄已完成的變更與驗證方式。

---

## 全域準備

**做了什麼**
- 確認 Python 後端套件全數安裝（`fastapi`、`uvicorn`、`shioaji` 等）
- 安裝 Node.js 22（系統原為 v18，Vite 8 需 v20.19+）
- 執行 `npm install`，安裝前端相依（含新增的 `@dnd-kit/core/sortable/utilities`）

**驗證**
```bash
node --version   # v22.x.x
npm --version    # 10.x.x
cd frontend && npm run dev   # Vite 正常啟動 → http://localhost:5173
```

---

## Task 8-0：後端 API 契約補齊

**做了什麼**

| 檔案 | 變更 |
|---|---|
| `app/core/shioaji_client.py` | 新增 `usage_pct`（滾動 5 秒視窗）、`last_login`、`reconnect()`、`record_api_calls()` |
| `app/api/routes_debug.py` | 新增 `POST /api/debug/reconnect` |
| `app/api/routes_market.py` | 新增 `GET /api/market/universe`（回傳 2185 檔股票清單） |
| `app/api/routes_admin.py` | 新增 `GET /api/admin/export-db`（下載 SQLite） |
| `app/main.py` | 掛載 `admin_router` |
| `app/scheduler/jobs.py` | snapshot 每批呼叫前執行 `record_api_calls()` |

**驗證**
```bash
# 啟動後端
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

# 測試端點
curl http://localhost:8000/health
# → {"status":"ok"}

curl http://localhost:8000/api/debug/status
# → {"connected":true,"usage_pct":...,"last_login":"..."}

curl -X POST http://localhost:8000/api/debug/reconnect
# → {"connected":true,"message":"重新連線成功"}

curl http://localhost:8000/api/market/universe | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))"
# → 2185

# 瀏覽器開以下網址，應自動下載 app.db
http://localhost:8000/api/admin/export-db
```

---

## Task 8-1：Header 狀態列 + 下載

**做了什麼**

| 檔案 | 動作 |
|---|---|
| `src/api/types.ts` | 新增 `ApiStatusResponse`、`ReconnectResponse` |
| `src/api/client.ts` | 新增 `getStatus()`、`reconnect()`（POST）、`exportDb()`（回 Blob） |
| `src/hooks/index.ts` | 新增 `useApiStatus()`（15s 輪詢） |
| `src/components/status/ApiStatusBadge.tsx` | 顯示 `永豐金 API: xx%` + 🟢/🔴 燈號；≥90% 轉紅 |
| `src/components/layout/Header.tsx` | 整合 Badge、重新連線按鈕、重新整理、下載 |
| `src/components/layout/DashboardLayout.tsx` | 舊 header inline → 改用 `<Header />` 元件 |

**驗證（需後端已啟動）**
1. 開啟 `http://localhost:5173`
2. Header 應顯示 `永豐金 API: xx% 🟢 已連線`，每 15 秒自動更新
3. 點 **[重新連線]** → 按鈕變旋轉 → 完成後 toast「重新連線成功」
4. 點 **[下載]** → 瀏覽器下載 `app.db`
5. 停止後端 → Header 背景變紅，燈號變 🔴

---

## Task 8-2：KPI 卡片擴充為 5 張

**做了什麼**

| 檔案 | 動作 |
|---|---|
| `src/api/types.ts` | `AssetsResponse` 新增 6 個 optional 副欄位（`day_pnl` / `day_pnl_rate` / `margin_value` / `short_value` / `unrealized_pnl` / `realized_pnl_today`） |
| `src/lib/colors.ts` | 新增 `pnlClass(n)` — 正綠負紅零灰 CSS class |
| `src/components/cards/AssetCards.tsx` | 改寫為 5 張卡片 + Skeleton + 錯誤橫幅 |

**5 張卡片說明**

| # | 卡片 | 主數字 | 副資訊 |
|---|---|---|---|
| 1 | NAV（藍色） | `nav` | 當日損益 / 當日損益%（後端補充後顯示） |
| 2 | 現金 | `cash` | 融資損益 / 融券損益（非零才顯示） |
| 3 | 現股市值 | `stock_value` | 融資市值 / 融券市值（後端補充後顯示） |
| 4 | 未實現損益 | `unrealized_pnl` | 今日實現損益（後端補充後顯示，否則「—」） |
| 5 | 待交割款 | `pending_settlement` | T+1 / T+2 明細（純文字）|

**驗證**
1. 開啟 `http://localhost:5173`
2. 卡片列應顯示 5 張
3. 桌機（≥1024px）5 欄並排，平板 3 欄，手機 2 欄
4. 卡片 5 右側有藍/靛色環圖，顯示 T+1 / T+2 佔比
5. 第 4 張「未實現損益」目前後端未提供，應顯示「—」且不報錯
6. 拔掉後端 → 卡片顯示 Skeleton，恢復後端 → 自動刷新

---

## 快速啟動（本地開發）

```bash
# 終端機 1：後端
cd stock-treemap-docker/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 終端機 2：前端（需 Node 22）
cd stock-treemap-docker/frontend
npm run dev
# → 開啟 http://localhost:5173
```

---

## 下一步：Task 8-3 起

| Task | 內容 |
|---|---|
| 8-3 | ListPanel 分頁（庫存 / 自選清單 Tab） |
| 8-4 | 自選清單動態搜尋與新增 |
| 8-5 | 拖拽排序 + 持久化 |
| 8-6 | Treemap 工具列 / 圖例 / 全螢幕 |
| **8-7** | **手機 Treemap 修正（Bug，優先）** |
| 8-8 | 績效圖 + 結算時間改 18:00 |
