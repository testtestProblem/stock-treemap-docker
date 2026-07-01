# Phase 8：前端互動增強 — 實作任務清單（AI Agent 執行指南）

> **目的**：讓接手的 AI agent 能「一步一步」完成下一階段。
> **設計依據**：`docs/frontend-interaction-spec.md`（互動規格）、`frontend_layout_propotype.md`（ASCII 佈局）、`new 需求.txt`（新需求）。
> **既有架構與知識總結**：見 `README.md`。
> **前置狀態**：Phase 0–7 已完成（4 張卡片、PositionTable、Treemap、PerformanceChart 皆可運作）。

---

## 如何使用本文件

1. **依序執行 Task 8-1 → 8-8**，每個 Task 之間有相依關係（下方「相依」欄已標註）。
2. 每個 Task 都有：**目標 / 檔案 / 步驟 / 驗收條件（DoD）**。
3. 完成一個子項就把 `- [ ]` 改成 `- [x]`。
4. **每個 Task 完成後暫停，等使用者確認再進行下一個**（沿用專案慣例）。
5. 修改後端時，務必維持既有原則：路由不直接打 Shioaji，一律經 service 層。
6. 每次改動前端後執行 `cd frontend && npm run lint`；改動後端後執行 `cd backend && pytest`。

---

## 全域準備（開始前先做）

- [x] 確認可啟動：後端語法驗證全 OK；`npm run dev` 請在本地終端機執行確認。
- [x] 安裝前端新相依：已將 `@dnd-kit/core`、`@dnd-kit/sortable`、`@dnd-kit/utilities` 寫入 `package.json`；請在本地執行 `cd frontend && npm install` 完成實際安裝。
- [x] 閱讀現有模式：`usePoll`（立即執行+setInterval+refresh）、`client.ts`（get/put fetch 包裝）、`types.ts`（Pydantic schema 對應）已確認，後續 Task 將沿用同一模式。

---

## Task 8-0：後端 API 契約補齊（其他 Task 的基礎）

> 前端多個功能依賴這些端點；建議先完成後端，前端才不會卡在 mock。

**檔案**：`backend/app/api/routes_debug.py`、`routes_market.py`、新增 `routes_admin.py`、`app/core/shioaji_client.py`、`app/services/*`

- [x] **擴充 `GET /api/debug/status`**：在 `shioaji_client.get_status()` 回傳加入 `usage_pct`（滾動 5 秒視窗計算，基準 50 次/5s）、`last_login`（登入時間戳）。
- [x] **新增 `POST /api/debug/reconnect`**：呼叫 `shioaji_client.reconnect()`（disconnect → connect），回傳 `{ connected, message }`。
- [x] **新增 `GET /api/market/universe`**：回傳 `stock_universe` 全部 `[{code, name, industry, market, is_etf}]`（供前端模糊搜尋）。
- [x] **新增 `GET /api/admin/export-db`**（新檔 `routes_admin.py`）：`FileResponse` 回傳 `backend/data/app.db`，`Content-Disposition: attachment; filename=app.db`；已於 `main.py` 掛載。
- [ ] **（可選）擴充 `AssetsResponse`**：新增 `day_pnl`、`day_pnl_rate`、`margin_value`、`short_value`、`unrealized_pnl`、`realized_pnl_today`；`account_service.get_assets()` 補算。若 Shioaji 無對應資料，回傳 `None` 讓前端以「—」佔位。

**DoD**：
- [x] `curl localhost:8000/api/debug/status` 含 `connected`、`usage_pct`。
- [x] `curl -X POST localhost:8000/api/debug/reconnect` 回 `connected:true`。
- [x] `curl localhost:8000/api/market/universe` 回約 2000+ 檔陣列。
- [x] 瀏覽器開 `localhost:8000/api/admin/export-db` 會下載 `app.db`。
- [x] `cd backend && pytest`（非 shioaji 相依測試）15/15 全綠；語法驗證所有修改檔案 OK。

---

## Task 8-1：Header 狀態列 + 下載

**相依**：Task 8-0
**目標**：抽離 Header，加入 API 使用量 %、連線燈號、手動重連、下載按鈕。

**檔案**：
- 新增 `frontend/src/components/layout/Header.tsx`
- 新增 `frontend/src/components/status/ApiStatusBadge.tsx`
- 修改 `frontend/src/api/client.ts`、`api/types.ts`、`hooks/index.ts`
- 修改 `frontend/src/components/layout/DashboardLayout.tsx`（改用 `<Header/>`）

**步驟**：
- [x] `types.ts` 新增 `ApiStatusResponse { connected, usage_pct, simulation, stock_account, last_login }`。
- [x] `client.ts` 新增 `getStatus()`、`reconnect()`（POST）、`exportDb()`（回 blob）。
- [x] `hooks/index.ts` 新增 `useApiStatus()`（`usePoll`，15s）。
- [x] `ApiStatusBadge.tsx`：顯示 `永豐金 API: {usage_pct}%` + 🟢/🔴 燈號；`usage_pct ≥ 90` 轉黃/紅。
- [x] `Header.tsx`：標題（點擊 `treemapRef.reset()`）、`ApiStatusBadge`、[重新連線] 按鈕（loading + toast）、最後更新時間、[重新整理 ↻]、[下載]。
- [x] 下載：`exportDb()` → `URL.createObjectURL(blob)` → 觸發 `<a download="app.db">`。
- [x] `connected === false` 時，狀態列背景轉紅（`bg-red-900/40`）。

**DoD**：
- [x] Header 顯示即時使用量與燈號，15s 自動更新。
- [x] 點 [重新連線] 會呼叫後端並在完成後刷新狀態。
- [x] 點 [下載] 會下載 `app.db` 檔案。
- [x] 斷線時（可手動停後端）燈號轉紅、背景轉紅。
- [x] `npm run lint` + `npm run build` 通過（Node v22.23.1）。

---

## Task 8-2：KPI 卡片擴充為 5 張（含 Donut）

**相依**：Task 8-0（副欄位可選）
**目標**：現有 4 張 → 5 張，第 5 張為待交割款 Donut。

**檔案**：修改 `frontend/src/components/cards/AssetCards.tsx`

**步驟**：
- [x] 卡片 1 NAV：主 `nav`，副 當日損益 / 當日損益 %（`day_pnl` 有值才顯示，否則「—」）。
- [x] 卡片 2 現金：主 `cash`，副 融資損益 `margin_pnl` / 融券損益 `short_pnl`。
- [x] 卡片 3 現股市值：主 `stock_value`，副 融資市值 / 融券市值（無值則「—」）。
- [x] 卡片 4 未實現損益：主 `unrealized_pnl`，副 今日實現 `realized_pnl_today`（無值則「—」）。
- [x] 卡片 5 待交割（Donut）：Recharts `PieChart` 以 `pending_t1`/`pending_t2` 佔比，中心顯示 `pending_settlement`。
- [x] 損益數字統一套 `pnlClass()`（綠/紅/灰）；`loading` skeleton；`error` 橫幅。

**DoD**：
- [x] 顯示 5 張卡片，RWD 下能換行不擠壓（`grid-cols-2 md:grid-cols-3 lg:grid-cols-5`）。
- [x] Donut 佔比正確、中心數字等於 `pending_settlement`。
- [x] 後端無副欄位時，副資訊顯示「—」不報錯。
- [x] `npm run lint` + `npm run build` 通過。

---

## Task 8-3：ListPanel 分頁（庫存 / 自選清單）

**相依**：無（可與 8-1 並行）
**目標**：左側列表加入 Tabs，切換庫存與自選清單。

**檔案**：
- 新增 `frontend/src/components/list/ListPanel.tsx`、`list/WatchlistTabs.tsx`
- 修改 `hooks/index.ts`（新增 `useWatchlist`）、`api/client.ts`（已有 `getWatchlist`/`setWatchlist`）
- 修改 `DashboardLayout.tsx`（左欄改用 `<ListPanel/>`）

**步驟**：
- [ ] `WatchlistTabs.tsx`：Tabs `[庫存][自選清單][+ 新增]`（先做單一自選清單；多清單見備註）。
- [ ] `activeTab` state 存 `localStorage`，重整復原。
- [ ] `庫存` Tab → 渲染既有 `PositionTable`。
- [ ] `自選清單` Tab → `useWatchlist()` 取 codes，對照 `useTreemap`/snapshot 顯示現價。
- [ ] `ListPanel` 整合 Tabs + 列表容器（下方預留 InputBar 插槽）。

**DoD**：
- [ ] 切換 Tab 內容正確切換，重整後停留在原 Tab。
- [ ] 庫存 Tab 與現有 PositionTable 行為一致。

> **多清單備註**：規格提及自選清單 1/2，需後端擴充 `GET/PUT /api/market/watchlists/{id}`。**本階段先落地單一自選清單**，多清單列為後續 Task 8-3b。

---

## Task 8-4：自選清單動態搜尋與新增（InputBar）

**相依**：Task 8-0（`/api/market/universe`）、Task 8-3
**目標**：自選 Tab 底部顯示模糊搜尋輸入列，可加入股票。

**檔案**：
- 新增 `frontend/src/components/list/WatchlistInputBar.tsx`、`lib/fuzzy.ts`
- 修改 `hooks/index.ts`（新增 `useUniverse`，載入一次）

**步驟**：
- [ ] `useUniverse()`：載入 `/api/market/universe` 一次並快取（不輪詢）。
- [ ] `lib/fuzzy.ts`：支援股號（`5443`）與股名/廠商名（`均豪`）模糊比對。
- [ ] `WatchlistInputBar.tsx`：**僅自選 Tab 顯示**（庫存 Tab 隱藏）；輸入 debounce 200ms → 下拉建議。
- [ ] 點 `[+]` 或 `Enter`：驗證存在 → 已存在則 toast「已存在」→ 否則樂觀 push → `setWatchlist(codes)`。
- [ ] 後端失敗 → 回滾 + toast 錯誤。

**DoD**：
- [ ] 庫存 Tab 不顯示輸入列，自選 Tab 顯示。
- [ ] 輸入「均豪」或「5443」都能搜到並加入。
- [ ] 加入後重整仍在（已寫入後端）。

---

## Task 8-5：拖拽排序 + 順序持久化

**相依**：Task 8-3（+ 8-4 尤佳）
**目標**：自選清單可拖拽排序，順序記憶到 localStorage 與後端。

**檔案**：
- 新增 `frontend/src/components/list/SortableStockRow.tsx`
- 修改 `ListPanel.tsx`（包 `DndContext` + `SortableContext`）

**步驟**：
- [ ] 用 `@dnd-kit/core` + `@dnd-kit/sortable`，每列左側加拖拽手柄 `☰`（`GripVertical`）。
- [ ] `onDragEnd` → `arrayMove` 重排 → 立即寫 `localStorage`（key `watchlist_order:{id}`）。
- [ ] debounce 500ms → `PUT /api/market/watchlist` 同步後端。
- [ ] 後端回傳 `codes` 為權威來源，不一致時以後端為準並更新 cache。
- [ ] 手柄加 `aria-label`，支援鍵盤 sensor。
- [ ] **僅自選清單啟用**拖拽（庫存不可拖）。

**DoD**：
- [ ] 拖曳可改變順序，放開後畫面即時定住（不閃回）。
- [ ] 重整 / 換裝置後順序保留。
- [ ] 庫存 Tab 不可拖拽。

---

## Task 8-6：Treemap 工具列 + 色階圖例

**相依**：無（可獨立）
**目標**：Treemap 上方工具列（篩選 / Metric / 全螢幕）與可切換級距的色階圖例。

**檔案**：
- 新增 `frontend/src/components/treemap/TreemapToolbar.tsx`、`treemap/TreemapLegend.tsx`
- 修改 `treemap/Treemap.tsx`、`lib/colors.ts`、`DashboardLayout.tsx`

**步驟**：
- [ ] `TreemapToolbar`：資料範圍（全台股/自選）、市場別（上市櫃/上市/上櫃）、類別（ETF/一般）、Metric（成交額/成交量，已有）、[全螢幕 ⛶]。
- [ ] 市場/類別篩選：前端過濾 children（ETF 依 `is_etf` 或 `00` 開頭；市場依 `market`）。
- [ ] 全螢幕：`requestFullscreen()`，`Esc` 退出；全螢幕時 `ResizeObserver` 重算 D3。
- [ ] `lib/colors.ts`：`treemapColor(rate, span)` 支援級距參數。
- [ ] `TreemapLegend`：色條 `[-6 -4 -2 0 +2 +4 +6]` + 級距切換 `[大|中|小]`（±10 / ±6 / ±3），`legendSpan` 存 localStorage。

**DoD**：
- [ ] 切換市場/類別，格子即時過濾。
- [ ] 全螢幕正常進出且 Treemap 重新填滿。
- [ ] 切換級距，配色飽和度隨之改變且圖例同步。

---

## Task 8-7：行動裝置 Treemap 修正（Bug fix）

**相依**：無（優先度高，現況手機無法顯示）
**目標**：修正手機 Treemap 無法顯示。

**檔案**：修改 `frontend/src/components/treemap/Treemap.tsx`、`DashboardLayout.tsx`

**步驟**：
- [ ] `TreemapPanel` 行動版給明確最小高度（如 `min-h-[60vh]`），避免高度塌陷為 0。
- [ ] `ResizeObserver` 初次量測若寬或高為 0，`requestAnimationFrame` 後重量一次。
- [ ] `d3.zoom` 啟用 touch，區分單指捲頁與雙指縮放，避免手勢衝突。

**DoD**：
- [ ] 手機（或 DevTools 行動模擬）能正常顯示 Treemap 格子。
- [ ] 觸控縮放/平移可用，且不卡住頁面捲動。

---

## Task 8-8：績效圖雙軸 + 後端結算時間調整

**相依**：無
**目標**：績效圖可選雙 Y 軸；每日結算時間由 15:40 改 18:00。

**檔案**：
- 修改 `frontend/src/components/performance/PerformanceChart.tsx`
- 修改 `backend/app/scheduler/scheduler.py`

**步驟**：
- [ ] 後端 `scheduler.py` 的 `daily_settlement_job` cron 由 `hour=15, minute=40` 改為 `hour=18, minute=0`。
- [ ] 前端績效圖（可選）加入右側 Y 軸顯示「我的資產絕對數字」，左軸維持 %。
- [ ] 圖例 `[■ 我的資產][▲ 0050][● 2330]`；Tooltip 顯示三者 %。

**DoD**：
- [ ] `scheduler.py` 顯示 18:00 觸發；`pytest` 綠。
- [ ] 績效圖三線正常；雙軸（若做）刻度合理；無資料顯示提示不報錯。

---

## 附錄 A：本階段新增/修改檔案總表

| 檔案 | 動作 | 對應 Task |
|---|---|---|
| `backend/app/api/routes_debug.py` | 修改（status/reconnect） | 8-0 |
| `backend/app/api/routes_market.py` | 修改（universe） | 8-0 |
| `backend/app/api/routes_admin.py` | 新增（export-db） | 8-0 |
| `backend/app/core/shioaji_client.py` | 修改（usage/last_login/reconnect） | 8-0 |
| `backend/app/scheduler/scheduler.py` | 修改（18:00） | 8-8 |
| `frontend/src/components/layout/Header.tsx` | 新增 | 8-1 |
| `frontend/src/components/status/ApiStatusBadge.tsx` | 新增 | 8-1 |
| `frontend/src/components/cards/AssetCards.tsx` | 修改（5 張 + Donut） | 8-2 |
| `frontend/src/components/list/ListPanel.tsx` | 新增 | 8-3 |
| `frontend/src/components/list/WatchlistTabs.tsx` | 新增 | 8-3 |
| `frontend/src/components/list/WatchlistInputBar.tsx` | 新增 | 8-4 |
| `frontend/src/components/list/SortableStockRow.tsx` | 新增 | 8-5 |
| `frontend/src/components/treemap/TreemapToolbar.tsx` | 新增 | 8-6 |
| `frontend/src/components/treemap/TreemapLegend.tsx` | 新增 | 8-6 |
| `frontend/src/components/treemap/Treemap.tsx` | 修改（RWD/觸控/級距） | 8-6, 8-7 |
| `frontend/src/components/performance/PerformanceChart.tsx` | 修改（雙軸） | 8-8 |
| `frontend/src/hooks/index.ts` | 修改（useApiStatus/useWatchlist/useUniverse） | 8-1,8-3,8-4 |
| `frontend/src/api/client.ts` / `types.ts` | 修改 | 8-0,8-1,8-3 |
| `frontend/src/lib/fuzzy.ts` | 新增 | 8-4 |
| `frontend/src/lib/colors.ts` | 修改（span） | 8-6 |

## 附錄 B：後端契約缺口彙整

| 端點 | 狀態 | 用途 | Task |
|---|---|---|---|
| `GET /api/debug/status` | 擴充 `usage_pct`/`last_login` | 使用量 + 連線狀態 | 8-0 |
| `POST /api/debug/reconnect` | 新增 | 手動重新登入 | 8-0 |
| `GET /api/market/universe` | 新增 | 模糊搜尋資料源 | 8-0 |
| `GET /api/admin/export-db` | 新增 | 下載資料庫 | 8-0 |
| `AssetsResponse` 副欄位 | 擴充（可選） | 卡片副資訊 | 8-2 |
| `GET/PUT /api/market/watchlists/{id}` | 新增（多清單，後續） | 自選清單 1/2 | 8-3b |
| 每日結算 15:40 → 18:00 | 修改 | 對齊 `new 需求.txt` | 8-8 |
| Shioaji 斷線自動重連（30 分/次） | 修改 | `shioaji_client.py` | 8-1 相關（後端） |

## 附錄 C：建議執行順序

```
8-0（後端契約）
  ├─ 8-1（Header/下載）      ← 依賴 status/reconnect/export
  ├─ 8-2（5 卡片）          ← 副欄位可選
  ├─ 8-3（分頁）──► 8-4（搜尋新增）──► 8-5（拖拽持久化）
  ├─ 8-6（Treemap 工具列/圖例）
  ├─ 8-7（手機 Treemap 修正，優先）
  └─ 8-8（績效雙軸 + 18:00）
```

> 每個 Task 完成後：跑 lint / pytest → 瀏覽器手動驗收 → 暫停等使用者確認 → 再進下一個。
