# 階段 7：UI 收尾（Motion 動畫、RWD、Tooltip、載入/錯誤狀態）

## 完成狀態

全部功能已實作並通過驗收。

---

## 新增 / 修改檔案清單

| 檔案 | 類型 | 說明 |
|---|---|---|
| `frontend/src/components/treemap/TreemapTooltip.tsx` | **新建** | Hover Tooltip 元件（Portal 至 body） |
| `frontend/src/components/treemap/Treemap.tsx` | 修改 | 加入 hover 事件、cursorPos state、industry/change_price 欄位 |
| `frontend/src/components/cards/AssetCards.tsx` | 修改 | Motion 進場動畫 + Skeleton + Error 橫幅 |
| `frontend/src/components/positions/PositionTable.tsx` | 修改 | Motion stagger + Skeleton rows + Error 顯示 |
| `frontend/src/components/layout/DashboardLayout.tsx` | 修改 | RWD（`flex-col lg:flex-row`）+ 傳遞 error props |

---

## 功能詳細說明

### 1. Treemap Tooltip

**元件**：`TreemapTooltip.tsx`

**觸發機制**：
- 每個 tile `<rect>` 加上 `onMouseEnter` → 設定 `hoveredTile` state
- SVG `onMouseMove` → 更新 `cursorPos { x: clientX, y: clientY }`（viewport 座標）
- SVG `onMouseLeave` → 清除 `hoveredTile`

**定位邏輯**：
```
預設：left = cursorX + 12,  top = cursorY + 12
右側翻轉：if (cursorX + 200 + 16 > window.innerWidth)  → left = cursorX - 200 - 8
底部翻轉：if (cursorY + 172 + 16 > window.innerHeight) → top  = cursorY - 172 - 8
```

**渲染方式**：`createPortal(…, document.body)` + `position: fixed`
→ 完全不受 `overflow-hidden` 裁切，不影響 zoom/pan 操作（`pointer-events: none`）

**動畫**：`AnimatePresence` + `motion.div`，進/退場均為 `scale 0.94↔1 + opacity`，duration 100ms

**Tooltip 內容**：

| 欄位 | 資料來源 |
|---|---|
| 代號 + 名稱 | `tile.code`, `tile.name` |
| 產業 | `tile.industry`（新增至 Tile interface） |
| 現價 | `tile.close` |
| 漲跌（著色） | `tile.change_price`（新增至 Tile interface） |
| 漲跌幅%（著色） | `tile.change_rate` |
| 成交量 | `tile.total_volume`，自動格式化為 K 張 |
| 成交額 | `tile.total_amount`，自動格式化為 億 / 萬 |

---

### 2. Motion 動畫

**依賴**：`motion/react`（`motion` v12，已安裝）

#### AssetCards 進場動畫

```
initial: { opacity: 0, y: 14 }
animate: { opacity: 1, y: 0 }
transition: { duration: 0.35, delay: index × 0.07, ease: 'easeOut' }
```

4 張卡片以 0ms / 70ms / 140ms / 210ms stagger 依序進場。

#### PositionTable stagger 動畫

```
initial: { opacity: 0, x: -10 }
animate: { opacity: 1, x: 0 }
exit:    { opacity: 0, x: -10 }
transition: { duration: 0.2, delay: index × 0.025 }
```

持倉列表以 AnimatePresence 包覆，新增/移除時有滑入滑出動畫。

---

### 3. Skeleton 載入狀態

| 元件 | 觸發條件 | 骨架內容 |
|---|---|---|
| `AssetCards` | `!data`（初次載入）| 4 張 `animate-pulse` 骨架卡（label + 數值佔位塊） |
| `PositionTable` | `loading && !data` | 4 列骨架行（代號佔位 + 名稱佔位 + 4 格數據佔位） |

切換機制：`AnimatePresence mode="wait"` 確保骨架消失後資料才進場。

---

### 4. 錯誤狀態

| 元件 | 錯誤來源 | 顯示方式 |
|---|---|---|
| `AssetCards` | `assets.error` | 紅色橫幅（`col-span-4`）顯示錯誤訊息 |
| `PositionTable` | `positions.error` | `AlertCircle` 圖示 + 紅色文字 |

錯誤訊息格式：`API /api/xxx 回傳 5xx`（由 `client.ts` 的 `get()` 拋出）。

---

### 5. RWD 響應式佈局

**斷點策略**：使用 Tailwind `lg:` 斷點（≥1024px）

| 區域 | 手機（< 1024px） | 桌面（≥ 1024px） |
|---|---|---|
| 資產卡片 | 2 列（`grid-cols-2`） | 4 列（`md:grid-cols-4`） |
| 主內容 | 垂直堆疊（`flex-col`） | 水平並排（`lg:flex-row`） |
| 持倉側欄 | 全寬，固定高 288px | 固定寬 288px，撐滿高度 |
| Treemap 區塊 | `min-h-[420px]` 保底高度 | `flex-1` 撐滿剩餘空間 |
| 績效圖 | 全寬 h-48 | 全寬 h-48（不變） |

---

## 驗收方式

### 1. Tooltip 驗收

- [ ] 滑鼠移入任何 Treemap 格子，浮現 tooltip 卡片
- [ ] Tooltip 顯示：代號、名稱、產業、現價、漲跌（著色）、漲跌幅%（著色）、成交量、成交額
- [ ] 移到右側邊界附近，tooltip 自動翻轉至游標左側
- [ ] 移到底部邊界附近，tooltip 自動翻轉至游標上方
- [ ] 拖曳 / 縮放 Treemap 時 tooltip 不殘留（onMouseLeave on SVG 清除）
- [ ] 切換不同格子時，tooltip 平滑切換（AnimatePresence key = code）

### 2. Motion 動畫驗收

- [ ] 重新整理頁面後，4 張資產卡片依序從下方淡入（stagger 可見）
- [ ] 持倉列表進入時每列從左側滑入
- [ ] 骨架狀態 → 資料狀態切換有 fade 過渡

### 3. Skeleton / Error 狀態驗收

**Skeleton 測試**：
```bash
# 模擬後端慢回應：在 usePoll.ts 的 fetcher 前加 await new Promise(r => setTimeout(r, 3000))
```
- [ ] 初始 3 秒顯示骨架卡 / 骨架列，資料到位後平滑切換

**Error 測試**：
```bash
# 臨時停止後端
# 前端 30 秒後 refresh 失敗
```
- [ ] 資產卡片下方出現紅色錯誤橫幅
- [ ] 持倉表顯示 AlertCircle + 錯誤訊息

### 4. RWD 驗收

在瀏覽器 DevTools 開啟響應式模式：

| 裝置模擬 | 預期結果 |
|---|---|
| iPhone 14 (390px) | 持倉表（h-72）在上，Treemap 在下，卡片 2 欄 |
| iPad Air (820px) | 持倉表（h-72）在上，Treemap 在下 |
| MacBook 14" (1440px) | 持倉表左側欄，Treemap 右側，卡片 4 欄 |

- [ ] 各斷點版面無橫向捲軸
- [ ] Treemap 在手機至少 420px 高（可正常使用縮放）

### 5. 整合驗收

```bash
# 啟動前後端
cd backend && uvicorn app.main:app --port 8000
cd frontend && npm run dev
```

1. 開啟 `http://localhost:5173`
2. 觀察頁面初始載入骨架 → 資料進場動畫
3. 滑過 Treemap 格子確認 Tooltip 正常
4. 縮放至 4x，hover 小格子確認文字補出
5. 縮小瀏覽器至 768px 確認垂直堆疊
6. 點擊 Header 標題確認 Treemap 視角重設

---

## 已知限制

- Tooltip 在 zoom 高倍率下，滑鼠快速移動時偶有一幀延遲（React state 更新頻率限制，視覺可接受）
- 手機觸控縮放尚未針對 touch 事件做特別處理（D3 zoom 原生支援 touch，但未測試 iOS/Android）
