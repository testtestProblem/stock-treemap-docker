# 前端互動規格與底層邏輯規劃

> 本文件依據 `frontend_layout_propotype.md`（ASCII 視覺佈局總覽 + 功能描述）撰寫，
> 並對齊現有實作（`frontend/src/**`）與後端 API 契約（`ARCHITECTURE.md`、`backend/app/api/*`）。
> 定位：下一階段（Phase 8）前端互動與狀態管理的設計藍圖，確認後再逐步實作。

---

## 0. 設計原則

- **前端只讀後端 JSON**：所有帳務/行情資料來自 REST API，前端不直接接觸 Shioaji。
- **狀態單向流動**：Server State（輪詢快取）與 UI State（分頁、排序、篩選）分離管理。
- **樂觀更新 + 後端同步**：使用者操作（排序、加入自選）先更新本地畫面，再非同步同步後端；失敗則回滾。
- **RWD 優先**：桌機左右雙欄、手機上下堆疊；Treemap 在行動裝置需可正常渲染（修正現有已知問題）。
- **色彩語意（美式漲跌色）**：漲 = 綠 `#22c55e`、跌 = 紅 `#ef4444`、平盤 = 灰，沿用 `src/lib/colors.ts`。

---

## 1. 全域佈局對照（ASCII → 元件樹）

```
DashboardLayout
├─ Header（全域導覽 + API 狀態列）              ← Row: Header
│   ├─ 標題（點擊重設 Treemap 視角）
│   ├─ ApiStatusBadge（使用量 % + 連線燈號）
│   ├─ 手動登入 / 重新連線 API 按鈕
│   ├─ 最後更新時間
│   ├─ 重新整理 ↻
│   └─ 下載（匯出資料庫）
├─ AssetCards（5 張 KPI 卡片）                  ← Row 1
├─ MainWorkspace（左右雙欄響應式）              ← Row 2
│   ├─ 左：ListPanel
│   │    ├─ WatchlistTabs（庫存 / 自選1 / 自選2 / +新增）
│   │    ├─ ListHeader（欄位標題）
│   │    ├─ 可拖拽的股票卡片列表（DnD）
│   │    └─ WatchlistInputBar（僅自選 Tab 顯示）
│   └─ 右：TreemapPanel
│        ├─ TreemapToolbar（Filter / Metric / 全螢幕）
│        ├─ Treemap（D3 畫布）
│        └─ TreemapLegend（色階圖例 + 級距切換）
└─ PerformanceChart（資產績效與基準對比）        ← Row 3
```

> 目前實作已有：`AssetCards`（4 張）、`PositionTable`、`Treemap`、`PerformanceChart`、`DashboardLayout`。
> 本規格新增 / 擴充：第 5 張卡片、WatchlistTabs、拖拽排序、輸入列、API 狀態列、下載、全螢幕、圖例級距。

---

## 2. Header：全域導覽與 API 狀態列

### 2.1 視覺與元素

| 元素 | 說明 | 資料來源 |
|---|---|---|
| 標題 `台股 Treemap Dashboard` | 點擊 → `treemapRef.reset()` 重設視角 | — |
| API 使用量 `[ 永豐金 API: 85% ]` | 顯示當日/當前用量百分比 | `GET /api/debug/status`（需擴充 `usage`） |
| 連線燈號 🟢/🔴 | `connected=true` 綠、`false` 紅 | `GET /api/debug/status`（`connected`） |
| `[手動登入API]` / `[重新連線]` | 觸發後端重新登入 | `POST /api/debug/reconnect`（**待新增**） |
| `[最後更新 14:30:22]` | 最近一次成功輪詢時間 | 前端輪詢時間戳 |
| `[重新整理 ↻]` | 手動觸發所有 hook `refresh()` | — |
| `[下載]` | 匯出資料庫至本地 | `GET /api/admin/export-db`（**待新增**） |

### 2.2 互動邏輯

- **連線狀態輪詢**：新增 `useApiStatus()`（間隔 15s），回傳 `{ connected, usage_pct, last_login }`。
- **燈號規則**：
  - `connected === true` → 🟢「已連線」。
  - `connected === false` → 🔴「未登入」，且整條狀態列背景轉紅（`bg-red-900/40`）以強提醒。
- **使用量顯示**：`usage_pct ≥ 90%` 時數字轉黃/紅並顯示警告 Tooltip（避免觸發 Shioaji 限流：5 秒 50 次）。
- **手動登入 / 重新連線**：
  1. 點擊 → 按鈕進入 loading（禁用、旋轉 icon）。
  2. 呼叫 `POST /api/debug/reconnect`。
  3. 成功 → 重新拉一次 `useApiStatus()` 並 toast「重新連線成功」。
  4. 失敗 → toast 錯誤；按鈕恢復可點。
- **自動重連（後端負責，前端呈現）**：後端偵測斷線時每 30 分鐘嘗試一次 `login()`（避免維護期無窮迴圈）。前端僅透過燈號反映最新狀態，不主動觸發重連迴圈。

### 2.3 底層契約（需後端新增）

```
GET  /api/debug/status
  → { connected: bool, usage_pct: number, simulation: bool,
      stock_account: string | null, last_login: string | null }

POST /api/debug/reconnect        # 觸發 shioaji_client 重新 login
  → { connected: bool, message: string }

GET  /api/admin/export-db        # 回傳 SQLite 檔（Content-Disposition: attachment）
  → application/octet-stream (app.db)
```

---

## 3. Row 1：帳戶資訊卡片區（KPI Dashboard）

佈局規劃 5 張卡片（現有 4 張 → 擴充第 5 張「待交割款」）。全部綁定 `GET /api/account/assets`（`useAssets`，30s）。

| # | 卡片 | 主數字 | 副資訊 | 對應欄位 |
|---|---|---|---|---|
| 1 | NAV 淨資產 | `nav` | 當日損益 / 當日損益 % | `nav`（副：需後端補當日損益，見下）|
| 2 | Cash 現金餘額 | `cash` | 融資損益 / 融券損益 | `cash` / `margin_pnl` / `short_pnl` |
| 3 | 現股市值 | `stock_value` | 融資市值 / 融券市值 | `stock_value`（副：需後端補分項）|
| 4 | 未實現損益 | 未實現總損益 | 今日實現總損益 | 需後端補 `unrealized_pnl` / `realized_pnl` |
| 5 | 待交割款 | `pending_settlement` | T+1 / T+2 待交割款 | `pending_settlement` / `pending_t1` / `pending_t2` |

### 3.1 互動邏輯

- **著色**：損益類數字依正負套 `pnlColor()`（綠/紅），零為灰。
- **待交割款（卡片 5）**：純文字顯示 `pending_settlement` 為主數字，`pending_t1`（T+1）與 `pending_t2`（T+2）各為副行，依正負著色。
- **載入 / 錯誤狀態**：`loading` 顯示 skeleton；`error` 顯示「—」並保留最後一次成功值（stale-while-revalidate）。

### 3.2 契約缺口（建議後端補充）

現有 `AssetsResponse` 已含 `nav/cash/stock_value/margin_pnl/short_pnl/pending_t1/pending_t2/pending_settlement`。
規格新增需求（若要完整呈現卡片副資訊）：
```
+ day_pnl: number          # 當日損益
+ day_pnl_rate: number     # 當日損益 %
+ margin_value: number     # 融資市值
+ short_value: number      # 融券市值
+ unrealized_pnl: number   # 未實現總損益
+ realized_pnl_today: number  # 今日實現總損益
```
> 若後端短期無法補齊，前端以「—」佔位並隱藏該副行，不阻塞主數字顯示。

---

## 4. Row 2 左側：持倉 / 自選列表（ListPanel）

### 4.1 分頁（WatchlistTabs）

- Tabs：`[ 庫存 ]`、`[ 自選清單 1 ]`、`[ 自選清單 2 ]`、`[ + 新增 ]`。
- **UI State**：`activeTab: 'holdings' | 'watchlist:{id}'`，存於 URL query 或 `localStorage`，重整後復原。
- **資料來源**：
  - `庫存` → `usePositions()`（`GET /api/account/positions`）。
  - `自選清單 N` → `useWatchlist(id)`（`GET /api/market/watchlist`，需擴充支援多份清單）。
- **`+ 新增`**：新增一份自選清單（多清單需後端 key 擴充，見 4.5）。

### 4.2 列表卡片欄位（對照 ASCII）

每檔股票卡片顯示三行資訊：
```
[☰] stock_code | type   | 損益%
    stock_name / vendor  | 損益額
    股數 | 均價 | 現價 | 市值
```
| 欄位 | 來源（庫存）| 來源（自選）|
|---|---|---|
| `stock_code` | `PositionItem.code` | watchlist code |
| `type` badge | `position_type`（現股/融資/融券）| 「自選」|
| 損益% / 損益額 | `pnl`（+ 需 `pnl_rate`）| 由快照 `change_rate` 推算 |
| 股數 / 均價 / 現價 / 市值 | `quantity`/`avg_price`/`last_price`/`market_value` | 自選僅有現價（快照）|
| 拖拽手柄 `☰` | 僅自選 Tab 顯示 | ✔ |

### 4.3 動態搜尋與新增（WatchlistInputBar）

**條件渲染**：僅當 `activeTab` 為自選清單時，於列表最下方渲染輸入列；`庫存` Tab 隱藏。

**輸入行為**：
- 支援 **股號**（如 `5443`）或 **股名/廠商名**（如 `均豪`）模糊搜尋（Fuzzy Search）。
- 資料源：前端載入一次 universe（`GET /api/market/universe`，`{code,name,industry}[]`，**建議新增**），本地做 fuzzy match，即時顯示下拉建議（debounce 200ms）。
- 觸發加入：點右側 `[+]` 或按 `Enter`：
  1. 驗證代號存在於 universe。
  2. 若已在清單 → toast「已存在」不重複加入。
  3. 通過 → 樂觀更新（push 至清單陣列末端）→ 呼叫 `setWatchlist(codes)` 同步後端。
  4. 後端失敗 → 回滾並 toast 錯誤。

### 4.4 拖拽排序（Drag-and-Drop Reordering）

- **範圍**：僅自選清單啟用（庫存排序由後端損益/市值排序，不可拖拽）。
- **實作**：採用 `@dnd-kit/core` + `@dnd-kit/sortable`（輕量、支援觸控），手柄為 `☰`（`GripVertical` icon）。
- **流程**：
  1. `onDragStart` → 提升卡片 z-index、半透明。
  2. 拖曳中即時重排（`arrayMove`）。
  3. `onDragEnd` → 捕捉新順序索引 → 進入持久化流程（第 4.5 節）。
- **無障礙**：手柄提供 `aria-label`，支援鍵盤（`@dnd-kit` 內建 keyboard sensor）。

### 4.5 順序持久化（State Persistence）

- **本地緩存（快速響應）**：`onDragEnd` 立即寫入 `localStorage`（key `watchlist_order:{id}`），畫面即時反映，重整不閃回舊序。
- **後端同步（永久記憶）**：debounce 500ms 後呼叫 `PUT /api/market/watchlist`，更新資料庫 `kv_store`，確保跨裝置 / 重整復原。
- **衝突處理**：後端回傳的最新 `codes` 作為權威來源；本地與後端不一致時以後端為準並更新 cache。

**多清單契約擴充建議**（現有僅單一 `watchlist` key）：
```
GET  /api/market/watchlists            → { lists: [{id, name, codes}] }
PUT  /api/market/watchlists/{id}       → { id, name, codes }
POST /api/market/watchlists            → 新增一份清單
```
> 若暫不做多清單，可先以單一 `watchlist` 落地（Tab 只有「庫存 / 自選清單」兩個），multi-list 列為後續。

---

## 5. Row 2 右側：Treemap 面板（TreemapPanel）

延用現有 `Treemap.tsx`（D3 hierarchy + zoom/pan + 動態字體），擴充工具列與圖例。

### 5.1 工具列（TreemapToolbar）

| 控制項 | 選項 | 綁定 |
|---|---|---|
| Filter：資料範圍 | `左側列表`（自選/庫存）/ `全台股` | `mode` state |
| Filter：市場別 | `上市櫃 / 上市 / 上櫃` | 前端過濾 `industry`/market 或後端參數 |
| Filter：類別 | `ETF / 一般股` | 前端過濾 |
| Metric（大小依據）| `成交量 total_volume` / `成交價/成交額 total_amount` | `sizeBy` state（已實作）|
| Window | `全螢幕 ⛶` | Fullscreen API |

- **全螢幕**：呼叫 `element.requestFullscreen()`，退出用 `Esc`；全螢幕時 `ResizeObserver` 觸發 D3 重算幾何。
- **市場/類別篩選**：以 `TreemapStock.industry` 與代號規則（ETF 多為 `00` 開頭）在前端過濾 children；若需精確，後端 `treemap` 增加 `market`、`category` query 參數。

### 5.2 色階圖例（TreemapLegend）

- 對照 ASCII：`淺紅 有點深紅 深紅 灰 深綠 有點深綠 淺綠`，級距 `[-6% -4% -2% 0 +2% +4% +6%]`。
- **級距切換 `[大|中|小]`**：調整色階映射的飽和級距（例如 大 = ±10%、中 = ±6%、小 = ±3%），與 `treemapColor(rate, span)` 共用同一公式。
- 圖例點擊某級距 → 可選：高亮該區間格子（後續增強，非必要）。

### 5.3 行動裝置 Treemap 修正（已知問題）

現況：手機 Treemap 無法顯示。根因通常為容器高度塌陷（flex 子項 `min-height: 0` + SVG 高度 0）。修正規劃：
- 行動版給 `TreemapPanel` 明確最小高度（`min-h-[60vh]`），避免高度為 0。
- `ResizeObserver` 初次量測若寬/高為 0，延遲一幀（`requestAnimationFrame`）重量。
- 觸控手勢：`d3.zoom` 啟用 touch，區分「單指捲動頁面」與「雙指縮放 Treemap」，避免手勢衝突。

---

## 6. Row 3：資產績效與基準對比（PerformanceChart）

延用現有 Recharts `LineChart`，綁 `GET /api/history/performance`（`usePerformance`，5min）。

- 三條曲線：`我的資產 (nav)`、`0050 (price_0050)`、`2330 (price_2330)`，皆標準化為累積報酬率 %。
- **雙 Y 軸（對照 ASCII）**：左軸 = 趨勢報酬率 %，右軸 = 我的資產絕對數字（可選，預設只顯示 % 單軸；雙軸為增強）。
- 圖例：`[■ 我的資產] [▲ 0050 臺灣精選] [● 2330 台積電]`。
- Tooltip：hover 顯示該日期三者百分比；無資料時顯示提示文字（不報錯）。
- **記錄時間調整**：後端每日結算時間由 15:40 改為 **18:00**（`new 需求.txt`），前端無需改動，僅資料點時間隨之變化。

---

## 7. 資料流與狀態管理

### 7.1 Server State（輪詢）

沿用 `usePoll` 通用 hook（立即執行 → `setInterval` → 卸載取消 → `refresh()`）。

| Hook | 端點 | 間隔 |
|---|---|---|
| `useApiStatus`（新增）| `/api/debug/status` | 15s |
| `useAssets` | `/api/account/assets` | 30s |
| `usePositions` | `/api/account/positions` | 30s |
| `useTreemap(mode)` | `/api/market/treemap` | 60s |
| `useWatchlist`（新增/擴充）| `/api/market/watchlist(s)` | 手動 + 變更後 refetch |
| `usePerformance` | `/api/history/performance` | 5min |

### 7.2 UI State（本地）

| State | 儲存位置 | 說明 |
|---|---|---|
| `activeTab` | localStorage | 分頁復原 |
| `sizeBy` / `mode` | React state | Treemap 工具列 |
| `legendSpan`（大/中/小）| localStorage | 圖例級距 |
| `watchlist_order:{id}` | localStorage + 後端 | 拖拽順序（樂觀）|
| `filters`（市場/類別）| React state | Treemap 篩選 |

### 7.3 樂觀更新流程（加入自選 / 拖拽）

```
使用者操作
  → 更新本地陣列（畫面立即變）
  → 寫 localStorage（快速響應）
  → debounce → PUT 後端（永久記憶）
        ├─ 成功 → 以後端回傳 codes 為準
        └─ 失敗 → 回滾本地 + toast 錯誤
```

---

## 8. 下載功能（匯出資料庫）

- Header `[下載]` 按鈕 → `GET /api/admin/export-db`。
- 前端以 `fetch` 取得 blob → `URL.createObjectURL` → 觸發 `<a download="app.db">` 下載。
- 後端回傳 `backend/data/app.db`（`FileResponse`，設 `Content-Disposition: attachment`）。
- 大檔或權限考量：正式環境建議加簡易 Auth；下載中顯示 loading。

---

## 9. 元件與檔案規劃（新增 / 修改）

| 檔案 | 動作 | 說明 |
|---|---|---|
| `components/layout/Header.tsx` | 新增 | 抽離 Header，含 API 狀態列 / 登入 / 下載 |
| `components/status/ApiStatusBadge.tsx` | 新增 | 使用量 % + 燈號 |
| `components/cards/AssetCards.tsx` | 修改 | 擴充為 5 張純文字卡片 |
| `components/list/ListPanel.tsx` | 新增 | 整合 Tabs + 列表 + 輸入列 |
| `components/list/WatchlistTabs.tsx` | 新增 | 分頁切換 |
| `components/list/SortableStockRow.tsx` | 新增 | 可拖拽卡片（dnd-kit）|
| `components/list/WatchlistInputBar.tsx` | 新增 | 模糊搜尋 + 加入 |
| `components/positions/PositionTable.tsx` | 沿用 | 庫存 Tab 內容 |
| `components/treemap/TreemapToolbar.tsx` | 新增 | Filter/Metric/全螢幕 |
| `components/treemap/TreemapLegend.tsx` | 新增 | 色階 + 級距切換 |
| `components/treemap/Treemap.tsx` | 修改 | 行動裝置高度/觸控修正 |
| `hooks/index.ts` | 修改 | 新增 `useApiStatus`、`useWatchlist`、`useUniverse` |
| `api/client.ts` / `api/types.ts` | 修改 | 新增 status/reconnect/universe/export、watchlist 擴充 |
| `lib/fuzzy.ts` | 新增 | 股號/股名模糊搜尋 |
| `lib/colors.ts` | 修改 | `treemapColor(rate, span)` 支援級距 |

新增相依：`@dnd-kit/core`、`@dnd-kit/sortable`、`@dnd-kit/utilities`（拖拽）。

---

## 10. 後端契約缺口彙整（需協同新增/擴充）

| 端點 | 狀態 | 用途 |
|---|---|---|
| `GET /api/debug/status` | 擴充 `usage_pct` | API 使用量 + 連線狀態 |
| `POST /api/debug/reconnect` | **新增** | 手動重新登入 |
| `GET /api/market/universe` | **新增** | 前端模糊搜尋資料源 |
| `GET/PUT /api/market/watchlists(/{id})` | **新增（多清單）** | 自選清單 1/2 |
| `GET /api/admin/export-db` | **新增** | 下載資料庫 |
| `AssetsResponse` 副欄位 | 擴充 | 卡片當日/未實現/融資市值等 |
| 每日結算時間 15:40 → 18:00 | 修改 | 對齊 `new 需求.txt` |
| Shioaji 斷線自動重連（30 分鐘一次）| 修改 | `shioaji_client.py` |

---

## 11. 實作階段建議（Phase 8）

- **8-1 Header 狀態列**：`useApiStatus`、燈號、手動重連、下載。
- **8-2 卡片擴充**：第 5 張待交割款（純文字）+ 副欄位（後端補齊後啟用）。
- **8-3 列表分頁**：WatchlistTabs + 庫存/自選資料綁定。
- **8-4 搜尋與新增**：universe + fuzzy + InputBar + 樂觀更新。
- **8-5 拖拽排序 + 持久化**：dnd-kit + localStorage + PUT 同步。
- **8-6 Treemap 工具列 / 圖例 / 全螢幕**。
- **8-7 行動裝置 Treemap 修正**。
- **8-8 績效圖雙軸 + 結算時間調整驗證**。

> 每階段完成後暫停確認，方式沿用瀏覽器手動驗收 + 比對後端數值（見 `ARCHITECTURE.md` 第 7 節）。
