# 台股 Treemap Dashboard

全端台股熱力圖儀表板，透過永豐金 **Shioaji API** 即時取得市場行情與個人帳務，
以現代化 Dashboard 呈現全台股 / 自選股 Treemap、精確 T+2 真實資產（NAV），以及與 0050、2330 的每日績效比較。

---

## 技術棧

| 層 | 技術 | 說明 |
|---|---|---|
| 後端語言 | Python 3.10+ | 主要後端語言 |
| Web 框架 | FastAPI + Uvicorn | REST API 伺服器、lifespan 事件管理 |
| 券商 API | Shioaji (永豐金) | 行情快照、K 線、持倉、帳戶、交割款 |
| 排程 | APScheduler | 全市場快照（每 2 分鐘）、每日結算（15:40） |
| 資料庫 | SQLAlchemy + SQLite | 每日績效儲存、自選清單 KV Store |
| 快取 | cachetools TTLCache | K 線資料快取，避免 Shioaji 速率限制 |
| 設定管理 | pydantic-settings | `.env` 讀取 API 金鑰 |
| 前端框架 | React 19 + Vite | SPA、HMR 開發體驗 |
| 樣式 | Tailwind CSS v4 | CSS-driven 設定，`@import "tailwindcss"` |
| 圖表佈局 | D3.js | Treemap 幾何運算（hierarchy、treemap、zoom） |
| 圖表渲染 | Recharts | 績效比較折線圖 |
| 動畫 | Motion (motion/react) | 卡片進場、持倉 stagger、Tooltip 淡入/淡出 |
| 圖示 | Lucide React | 統一 SVG 圖示 |

---

## 專案目錄結構

```
stock_treemap_final1/
│
├── backend/                        # FastAPI 後端
│   ├── .env                        # API 金鑰（不進版控）
│   ├── requirements.txt            # Python 相依套件
│   └── app/
│       ├── main.py                 # FastAPI 進入點、lifespan、CORS、路由掛載
│       ├── config.py               # pydantic-settings 設定（SJ_API_KEY 等）
│       │
│       ├── core/
│       │   ├── shioaji_client.py   # Shioaji 單例管理（登入 / 登出 / get_api()）
│       │   └── cache.py            # TTLCache 定義（kbars_cache）
│       │
│       ├── db/
│       │   ├── database.py         # SQLAlchemy engine + SessionLocal
│       │   ├── init_db.py          # create_all() 建立資料表
│       │   └── models.py           # DailyPerformance、KvStore 資料表定義
│       │
│       ├── schemas/
│       │   ├── account.py          # AssetsResponse、PositionItem Pydantic 模型
│       │   ├── market.py           # TreemapResponse、KbarsResponse、WatchlistResponse
│       │   └── history.py          # PerformanceSeries、PerformanceResponse
│       │
│       ├── services/
│       │   ├── stock_universe.py   # 解析 stock_index/*.txt → 全台股代碼/名稱/產業字典
│       │   ├── snapshot_store.py   # 全市場最新快照記憶體儲存（thread-safe dict）
│       │   ├── account_service.py  # NAV 計算、整股零股合併（現股/融資/融券）
│       │   ├── market_service.py   # Treemap 產業分層、K 線抓取（TTL 快取）
│       │   ├── watchlist_service.py# 自選清單 CRUD（KvStore JSON）
│       │   └── history_service.py  # 歷史績效查詢、標準化為累積報酬率 %
│       │
│       ├── api/
│       │   ├── routes_account.py   # GET /api/account/assets、/positions
│       │   ├── routes_market.py    # GET /api/market/treemap、/kbars、/watchlist（GET/PUT）
│       │   ├── routes_history.py   # GET /api/history/performance、POST /trigger-daily
│       │   └── routes_debug.py     # Debug 端點（持倉明細、快照狀態）
│       │
│       ├── scheduler/
│       │   ├── scheduler.py        # APScheduler 實例、job 註冊
│       │   └── jobs.py             # snapshot_job（每 2 min）、daily_settlement_job（15:40）
│       │
│       └── tests/
│           ├── test_stock_universe.py
│           ├── test_account_service.py
│           ├── test_market_service.py
│           └── test_history_service.py
│
├── frontend/                       # React + Vite 前端
│   ├── index.html
│   ├── vite.config.ts              # Vite 設定、/api 與 /health Proxy → localhost:8000
│   ├── package.json
│   └── src/
│       ├── main.tsx                # React DOM 掛載點
│       ├── App.tsx                 # 根元件（渲染 DashboardLayout）
│       ├── index.css               # Tailwind v4 @import
│       │
│       ├── api/
│       │   ├── client.ts           # fetch 封裝（get / put）、所有 API 呼叫函式
│       │   └── types.ts            # TypeScript 介面（對應後端 Pydantic schema）
│       │
│       ├── hooks/
│       │   ├── usePoll.ts          # 通用輪詢 hook（立即執行 + setInterval + cleanup）
│       │   └── index.ts            # useAssets / usePositions / useTreemap / usePerformance
│       │
│       ├── lib/
│       │   ├── colors.ts           # 美式漲跌色（漲綠跌紅）、treemapColor() 深淺計算
│       │   └── format.ts           # fmtMoney / fmtPrice / fmtPct 數字格式化
│       │
│       └── components/
│           ├── layout/
│           │   └── DashboardLayout.tsx     # 主版面：Header + 卡片 + 持倉 + Treemap + 績效圖
│           ├── cards/
│           │   └── AssetCards.tsx          # 4 張資產卡片（Motion 進場 + Skeleton + Error）
│           ├── positions/
│           │   └── PositionTable.tsx       # 持倉列表（stagger 動畫 + Skeleton + Error）
│           ├── treemap/
│           │   ├── Treemap.tsx             # D3 layout + zoom/pan + 動態字體 + Tooltip hover
│           │   └── TreemapTooltip.tsx      # Hover Tooltip（Portal 至 body）
│           └── performance/
│               └── PerformanceChart.tsx    # Recharts 折線圖（NAV / 0050 / 2330 累積報酬率%）
│
├── stock_index/                    # 原始股票清單資料（上市 / 上櫃 / ETF .txt）
├── docs/                           # 各階段開發文件
│   ├── phase0-scaffold.md
│   ├── phase1-shioaji-connection.md
│   ├── phase2-universe-snapshot.md
│   ├── phase3-account-assets.md
│   ├── phase4-market-endpoints.md
│   ├── phase5-history-performance.md
│   ├── phase6-frontend-dashboard.md
│   ├── phase7-ui-polish.md
│   └── sino-api-position-nav.md
├── ARCHITECTURE.md                 # 整體架構設計說明
├── CLAUDE.md                       # 專案規格書（需求來源）
└── README.md                       # 本文件
```

---

## 核心設計決策

### NAV（真實總資產）計算公式

```
NAV = 現金 (acc_balance)
    + 現股市值 (stock_value)
    + 融資未實現損益 (margin_pnl)
    + 融券未實現損益 (short_pnl)
    + T+1 待交割款 (pending_t1)
    + T+2 待交割款 (pending_t2)
```

> `acc_balance` 已包含融資保證金，故融資部位只貢獻損益而非全額市值，避免重複計算。

### Shioaji 持倉合併規則

Shioaji `list_positions()` 對整張部位同時回傳 `Unit.Common`（張）與 `Unit.Share`（股），兩者互相重疊。
實作上**只使用 `Unit.Share`**，並以 `(code, cond)` 為鍵合併，避免重複計算。

### 市場資料架構（Event-driven）

全台股行情**禁止** Request-driven：
- APScheduler 每 2 分鐘在背景批次抓取全市場 Snapshot，寫入記憶體 `snapshot_store`
- 前端呼叫 `/api/market/treemap` 時，永遠只讀取已快取的快照

### Treemap 互動設計

| 功能 | 實作方式 |
|---|---|
| 滾輪縮放 / 拖曳 | `d3.zoom`，Scale 1x–8x，translateExtent 邊界鎖定 |
| 動態字體 | `tileLayout(w, h, scale)`：以視覺像素空間計算後除以 k 換回 SVG 座標 |
| 縮放後補出文字 | 放大時小格子依序補出：漲跌幅 → 現價 → 代號 → 名稱 |
| Hover Tooltip | `createPortal` 渲染至 body，`position: fixed` 避免裁切 |
| 重設視角 | `useImperativeHandle` 暴露 `reset()`，點擊 Header 標題觸發 |

---

## API 端點速覽

| Method | Path | 說明 |
|---|---|---|
| `GET` | `/health` | 服務健康確認 |
| `GET` | `/api/account/assets` | 真實 NAV 與各分項 |
| `GET` | `/api/account/positions` | 合併後持倉列表 |
| `GET` | `/api/market/treemap?mode=market\|watchlist` | 產業分層 Treemap 資料 |
| `GET` | `/api/market/kbars?code=&start=&end=` | 歷史 K 線（TTL 快取） |
| `GET` | `/api/market/watchlist` | 取得自選清單 |
| `PUT` | `/api/market/watchlist` | 更新自選清單 |
| `GET` | `/api/history/performance` | 每日累積報酬率序列 |
| `POST` | `/api/history/trigger-daily` | 手動觸發每日結算 |

---

## 快速啟動

### 環境需求

- Python 3.10+（建議使用 conda）
- Node.js 18+

### 1. 設定 API 金鑰

在 `backend/` 建立 `.env`：

```env
SJ_API_KEY=your_api_key
SJ_SEC_KEY=your_secret_key
```

### 2. 啟動後端

```bash
# 建立並啟動 conda 環境
conda create -n stock_treemap python=3.10 -y
conda activate stock_treemap
pip install -r backend/requirements.txt

# 啟動
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 啟動前端

```bash
cd frontend
npm install
npm run dev
```

開啟 `http://localhost:5173`

### 4. 執行後端測試

```bash
conda run -n stock_treemap pytest backend/tests/ -v
```

---

## Dashboard 功能一覽

### 頂部資產卡片（30 秒自動更新）

| 卡片 | 資料來源欄位 |
|---|---|
| 真實總資產 NAV | `nav` |
| 現金餘額 | `cash` |
| 現股市值 | `stock_value`（附融資損益副文字） |
| 待交割款 | `pending_settlement`（附 T+1 / T+2 明細） |

### Treemap（60 秒自動更新）

- **方塊大小**：可切換「成交額」或「成交量」
- **範圍**：全台股 / 自選清單
- **顏色**：美式漲跌色，-10% 深紅 → 0% 灰 → +10% 亮綠
- **Hover Tooltip**：代號、名稱、產業、現價、漲跌額、漲跌幅、成交量、成交額
- **左下圖例**：漸層色條 -10% → 0% → +10%
- **縮放**：滾輪 1x–8x，邊界鎖定，放大後自動補出文字
- **重設**：點擊左上標題還原視角

### 左側持倉列表（30 秒自動更新）

每筆顯示代號、持倉類型（現股 / 融資 / 融券）、名稱、股數、均價、現價、市值、損益率（著色）

### 底部績效圖（5 分鐘自動更新）

Recharts 折線圖，對比「我的資產」、「0050」、「2330」累積報酬率 %

---

## 資料庫結構

| 資料表 | 欄位 | 用途 |
|---|---|---|
| `daily_performance` | `date, nav, close_0050, close_2330` | 每日 15:40 結算記錄 |
| `kv_store` | `key, json_value` | 自選清單（key=`watchlist`）等 KV 儲存 |

---

## TODO

- [ ] 自選清單管理 UI（新增 / 刪除股票，目前需透過 `PUT /api/market/watchlist` 直接更新）
- [ ] K 線圖 Modal（點擊 Treemap 格子彈出個股 K 線）
- [ ] Treemap 點擊下鑽（產業群組 → 個股）
- [ ] WebSocket 即時推播（取代輪詢，降低延遲）
- [ ] 深色 / 淺色主題切換
- [ ] Docker Compose 一鍵部署
- [ ] iOS / Android 觸控縮放測試與優化
