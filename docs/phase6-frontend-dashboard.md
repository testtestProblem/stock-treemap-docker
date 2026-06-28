# 階段 6：前端 Dashboard 串接

## 完成狀態

全部功能已實作並通過驗收。

---

## 新增 / 修改檔案清單

### API 層

| 檔案 | 說明 |
|---|---|
| `frontend/src/api/types.ts` | 對齊後端實際 schema：`AssetsResponse`（nav/cash/stock_value/margin_pnl/short_pnl/pending_*）、`PositionItem`（含 position_type）、`TreemapResponse`（IndustryNode → TreemapStock 階層）、`PerformanceResponse`（PerformanceSeries）、`WatchlistResponse` |
| `frontend/src/api/client.ts` | 補全 `put()` 方法；新增 `getWatchlist`、`setWatchlist`；修正 `getKbars` 簽名 |

### Hooks 層

| 檔案 | 說明 |
|---|---|
| `frontend/src/hooks/usePoll.ts` | 通用輪詢 hook：立即執行一次 → setInterval → 元件卸載時取消（`cancelled flag`）；提供 `refresh()` 強制重新整理 |
| `frontend/src/hooks/index.ts` | 業務 hook 匯出：`useAssets`（30s）、`usePositions`（30s）、`useTreemap`（60s）、`usePerformance`（5min） |

### 工具層

| 檔案 | 說明 |
|---|---|
| `frontend/src/lib/format.ts` | `fmtMoney`（整數逗號）、`fmtPrice`（兩位小數）、`fmtPct`（+/- 符號 + 小數） |

### 元件層

| 檔案 | 說明 |
|---|---|
| `frontend/src/components/cards/AssetCards.tsx` | 4 張卡片：NAV（藍色強調）、現金、現股市值（附融資損益副文字）、待交割（附 T+1/T+2 明細） |
| `frontend/src/components/positions/PositionTable.tsx` | 持倉列表：現股／融資／融券 badge + 損益著色；每筆顯示代號、名稱、股數、均價、現價、市值 |
| `frontend/src/components/treemap/Treemap.tsx` | 主要 D3 Treemap（詳見下方） |
| `frontend/src/components/performance/PerformanceChart.tsx` | Recharts LineChart：3 條折線（我的資產/0050/2330）；自訂 Tooltip、累積報酬率 %；無資料時顯示提示文字 |
| `frontend/src/components/layout/DashboardLayout.tsx` | 主版面：Header + 資產卡片 + 持倉表 + Treemap + 績效圖；含手動重新整理按鈕 |

---

## Treemap 元件詳細架構

### 功能一覽

| 功能 | 說明 |
|---|---|
| D3 hierarchy + treemap layout | 以 `d3.hierarchy` 讀取後端巢狀結構，`d3.treemap` 計算格子幾何，只操作純數學，不觸碰 DOM |
| ResizeObserver | 容器尺寸改變時自動重新計算 D3 layout，SVG 同步更新 |
| 格子內容 | 代號（monospace 粗體）、名稱（截斷至 6 字）、現價、漲跌幅 % |
| 動態字體 | `tileLayout(w, h, scale)` 在**視覺像素空間**計算字體大小與顯示門檻，再 ÷ scale 換回 SVG 座標 |
| 滾輪縮放 / 拖曳 | `d3.zoom`：Scale Extent 1x–8x，透過 React state (`transform`) 套用至 `<g transform>` |
| 邊界阻尼 | `.extent` + `.translateExtent` 嚴格限制拖曳範圍在畫布邊界內 |
| 游標樣式 | 預設 `grab`，拖曳中 `grabbing` |
| 重設視角 | 透過 `forwardRef + useImperativeHandle` 暴露 `reset()` 方法；點擊 Header 標題觸發，D3 transition 350ms 平滑還原 |
| 方塊大小切換 | SizeBy prop：`total_amount`（成交額）或 `total_volume`（成交量） |
| 顏色圖例 | 左下角漸層色條：-10% 深紅 → 0% 灰 → +10% 亮綠，與 `treemapColor()` 同一套公式 |
| 縮放後文字補出 | 原本因太小被隱藏的文字，放大後依序補出（漲跌幅 → 現價 → 代號 → 名稱） |

### `tileLayout(w, h, scale)` 計算原理

```
視覺寬高 = w × k,  h × k      (k = transform.k)
      ↓ 在視覺空間計算字體大小（8–14px）、行高、各行 y、顯示門檻
      ↓ 所有數值 ÷ k 換算回 SVG 座標
      → zoom <g transform> 再 × k 還原成視覺大小
```

效果：縮放不影響文字視覺大小；放大時小格子依序顯示更多資訊。

---

## 版面佈局

```
┌─ Header ─────────────────────────────────────────────────────────┐
│  台股 Treemap Dashboard（點擊重設視角）     [更新時間] [重新整理] │
├─ 資產卡片 ────────────────────────────────────────────────────────┤
│  NAV（藍色）  │  現金  │  現股市值  │  待交割                    │
├─ 主內容 ──────────────────────────────────────────────────────────┤
│                    │                                              │
│  持倉列表          │  大小 [成交額][成交量]  範圍 [全台股][自選]  │
│  （每 30s 更新）   │                                              │
│                    │  D3 Treemap（縮放/拖曳/圖例）                │
│                    │                                              │
├─ 績效圖 ──────────────────────────────────────────────────────────┤
│  Recharts LineChart：我的資產 / 0050 / 2330 累積報酬率 %         │
└───────────────────────────────────────────────────────────────────┘
```

---

## 輪詢策略

| 資料 | 間隔 | 說明 |
|---|---|---|
| 帳戶資產（assets） | 30 秒 | 即時性較高 |
| 持倉列表（positions） | 30 秒 | 即時性較高 |
| Treemap 市場資料 | 60 秒 | 後端已快取（APScheduler 每 2 分鐘更新） |
| 歷史績效（performance） | 5 分鐘 | 每日更新，不需高頻輪詢 |

---

## 驗收方式

### 1. 前端啟動

```bash
# 前端
cd frontend && npm run dev
# 後端（另一個終端）
cd backend && uvicorn app.main:app --port 8000
```

開啟 `http://localhost:5173`。

### 2. 資產卡片

- [ ] NAV 顯示藍色且數字正確（與 `/api/account/assets` 回傳值一致）
- [ ] 現金、現股市值、待交割各自對應後端欄位
- [ ] 30 秒後自動更新（Header 更新時間改變）

### 3. 持倉列表

- [ ] 列出所有持倉，現股/融資/融券 badge 顏色不同
- [ ] 損益正數顯示綠色，負數顯示紅色
- [ ] `GET http://localhost:5173/api/account/positions` 回傳陣列，型別包含 `position_type`

### 4. Treemap

```bash
# 驗證資料
Invoke-RestMethod http://localhost:5173/api/market/treemap?mode=market | ConvertTo-Json -Depth 4
```

- [ ] 全台股模式顯示所有上市上櫃股票格子
- [ ] 漲停（+10%）為亮綠，跌停（-10%）為深紅，平盤為灰色
- [ ] 每個格子顯示：代號、名稱、現價、漲跌幅 %（依大小自動隱藏）
- [ ] 切換「成交額 / 成交量」按鈕，格子大小重新排列
- [ ] 切換「自選清單」模式，只顯示 watchlist 中的股票
- [ ] 滑鼠滾輪縮放：1x–8x，`cursor: grab / grabbing`
- [ ] 拖曳不超出畫布邊界
- [ ] 放大後小格子補出更多文字（代號、現價等）
- [ ] 點擊 Header 標題，Treemap 平滑還原至 1x 初始位置
- [ ] 左下角顯示顏色圖例（-10% → 0% → +10%）

### 5. 績效圖

```bash
# 如無歷史資料，先手動觸發一筆
Invoke-RestMethod -Method Post http://localhost:5173/api/history/trigger-daily
```

- [ ] 有資料時顯示 3 條折線（藍/綠/橙）
- [ ] Y 軸顯示 % 單位，Tooltip 顯示各項百分比
- [ ] 無資料時顯示提示文字（不報錯）

### 6. Vite Proxy 驗證

```bash
Invoke-RestMethod http://localhost:5173/api/account/assets | ConvertTo-Json
# 應回傳 nav, cash, stock_value, margin_pnl, short_pnl, pending_* 所有欄位
```

---

## 已知限制

- 自選清單目前只能透過 `PUT /api/market/watchlist` 直接更新 JSON，尚無前端 UI 管理介面（Phase 7 TODO）
- K 線圖 Modal 尚未實作
- 績效圖歷史資料需要等到第一次 15:40 排程執行後才有資料，可用 `trigger-daily` 手動補入
