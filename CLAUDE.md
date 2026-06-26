# 任務概述
我需要開發一個全端 (Full-stack) 的網站，網站的主要功能是透過永豐金 Shioaji API (Sino API) 取得台股市場資料與個人帳務資訊，並在前端 Dashboard 顯示。
主要亮點包含：全台股/自選股 Treemap 熱力圖、精確的 T+2 真實資產計算，以及每日資產變動與 0050、2330 的績效比較。

# 角色
你是資深全端 (Full-stack) 工程師，寫程式架構分明，解耦，讓其他工程師快速瞭解

# 技術棧 (Tech Stack)
- 後端：Python 3.10+, FastAPI, `shioaji`, `uvicorn`, `python-dotenv`, `SQLAlchemy` (SQLite), `APScheduler`
- 前端:
1. React 19	元件狀態渲染、生命週期追蹤。
2. Vite	極速本地開發伺服器與 Rollup 生產打包（Hot Module Replacement 已由平台接管）。
3. Tailwind CSS v4	使用 @tailwindcss/vite 與 @import "tailwindcss"; 系統，全 CSS-driven 設定，提供系統化間距。
4. D3.js (d3)	接管樹型圖分層幾何圖形運算（d3.hierarchy, d3.treemap）、縮放阻尼控制。
5. Recharts	高效能 SVG 折線與網格圖表，支援 Tooltip 遮罩與動態過濾。
6. Motion (motion/react)	支援物理彈簧插值動畫（Spring UI）、AnimatePresence 退出動畫，打造頂級轉場。
7. Lucide React	統一規格的 SVG 圖示庫。

# 參考
- 前端: https://github.com/testtestProblem/treemap_for_demo/tree/main
1. 參考Dashboard 用熱力圖呈現
2. 參考記錄每天資產變化，對比0050與2330的績效

- 後端: https://github.com/testtestProblem/tw_stock_treemap
1. 參考製作全台股treemap
- 後端: https://github.com/testtestProblem/sino_test_agent_cursor
1. 參考sino api 如何使用

# 後端架構與 Sino API 規範 (非常重要)
請參考專案內的 `sino_API_full.md` 與 `SINO_API_GUIDE.md`，並嚴格遵守以下 API 規範：
1. **連線管理 (Singleton)**：Shioaji 不支援多程式同時 Login。請在 FastAPI 中建立一個全域的單例模式 (Singleton) 或是利用 FastAPI 的 lifespan event 進行初始化。
2. **登入機制**：讀取 `.env` 檔中的 `SJ_API_KEY` 與 `SJ_SEC_KEY`。登入時必須帶入參數 `api.login(api_key=..., secret_key=..., fetch_contract=True)`，確保商品檔載入。
3. **速率限制與快取 (Rate Limiting & Caching)**：Sino API 有嚴格的限流 (例如行情查詢 5秒內 50次上限)。後端必須針對頻繁呼叫的端點（如 Snapshot 或 Kbars）實作記憶體快取 (如 `cachetools` 或簡單的 dict TTL 快取)，避免直接把前端的請求無腦轉發給 Shioaji 導致被鎖 IP。
4. **持倉計算 (Positions)**：呼叫 `api.list_positions()` 時，請特別注意永豐 API 將整股 (`Unit.Common`) 與零股 (`Unit.Share`) 拆分。請參考 `SINO_POSITION_ALGORITHMS.md` 的邏輯，在後端將同一檔股票的整股與零股合併後再回傳給前端。
5. 對於「全台股」的資料，不要做 Request-driven，請改用 Event-driven (排程)。利用後端的 APScheduler 每 1 到 3 分鐘在背景抓取一次全市場的 Snapshot（並分批送出），在記憶體或 SQLite 中更新一份最新的 JSON/Dict。前端呼叫 API 時，永遠只拿背景快取好的那份現成資料。

# 需實作的後端 API 端點
- `GET /api/account/assets`: 精確計算真實資產。取得 `api.account_balance()`，加上 `api.list_positions()` 的總市值，**並扣除 `api.settlements()` 中的 T+1 與 T+2 應扣交割款**，回傳真實總資產 (Net Asset Value)。
- `GET /api/account/positions`: 呼叫並合併 `api.list_positions()`，回傳持倉列表。
- `GET /api/market/treemap`: 產生 Treemap 階層資料。接受參數區分「全市場」或「自選清單」，權重以市值或成交值計算。
- `GET /api/market/kbars?code={code}`: 呼叫 `api.kbars()` 取得歷史 K 線。
- `GET /api/history/performance`: 從 SQLite 撈取歷史資產紀錄與 0050、2330 的價格變化，供前端繪製比較圖。
- **每日排程任務 (APScheduler)**: 每天下午 15:40 自動執行(且2330有開盤)，計算當日「真實總資產」，並抓取 0050 與 2330 的當日收盤價，一併存入 SQLite 資料表 `daily_performance` 中。
- SQLite 儲存的自選清單及資產結算，用json儲存

# 前端需求
1. 建立一個現代化的 Dashboard 版面 (參考 `treemap_for_demo`)。
2. **頂部資訊卡片**：顯示「真實總資產」、「帳戶餘額」、「目前持倉市值」、「待交割款」。
3. **資產績效比較圖**：使用 Line Chart 畫出「我的資產走勢」、「0050 走勢」、「2330 走勢」的對比曲線 (需將走勢標準化為百分比 % 以便於同圖表比較)。
4. **左側持倉區塊**：顯示「目前持倉列表」，以表格呈現。
5. **右側/主區塊 Treemap**：
   - 用熱力圖呈現台股資訊。
   - 提供按鈕切換「全台股」與「自選清單」。
   - 板塊需顯示代號、名稱與漲跌幅，用美式漲跌顏色

# 開發步驟
請按照以下順序一步步開發，每完成一步請暫停讓我確認：
1. 先建立 FastAPI 後端與 Shioaji 連線設定。
2. 實作並測試上述 4 個後端 API 端點。
3. 建立前端專案架構並串接後端 API。
4. 完善前端 UI 與圖表呈現。