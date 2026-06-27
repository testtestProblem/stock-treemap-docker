# 階段 3：帳務 API — NAV 計算 + 持倉列表

> 目標：實作 `/api/account/assets` 與 `/api/account/positions`，精確計算真實總資產（NAV），並正確合併整股 / 零股 / 融資 / 融券部位。

---

## 完成狀態

- [x] `schemas/account.py` 定義 `AssetsResponse`（含 T+1/T+2 分開欄位）與 `PositionItem`（含 `position_type`）
- [x] `services/account_service.py` 實作 `get_assets()` 與 `_merge_positions()`
- [x] `api/routes_account.py` 掛載 `/api/account/assets` 與 `/api/account/positions`
- [x] `api/routes_debug.py` 新增 `/api/debug/positions/raw`、`/api/debug/positions/breakdown`、`/api/debug/positions/all-fields` 除錯端點
- [x] pytest 7 項全過（含融資、分批買進等情境）
- [x] 三輪實機除錯，NAV 公式完全驗證正確

---

## 三輪 Bug 修正紀錄（重要）

### Bug 1 — Unit.Common + Unit.Share 雙重計算

| | 說明 |
|---|---|
| 現象 | 整張持倉市值被加算兩次，持倉市值虛增 ~48 萬 |
| 根因 | `Unit.Common`（單位：張）與 `Unit.Share`（單位：股）對**整張部位**各回傳一次，並非互斥 |
| 修正 | 移除 `Unit.Common` 呼叫，統一只使用 `Unit.Share`（已涵蓋全部持倉） |

### Bug 2 — 融資餘額未扣除

| | 說明 |
|---|---|
| 現象 | 持倉市值仍虛增 ~5.2 萬 |
| 根因 | 誤以為 `acc_balance` 不含融資保證金，未扣除 `margin_purchase_amount` |
| 修正 | 從 `gross_market_value` 扣除 `margin_loan` |

### Bug 3 — 融資部位計算方式錯誤（最終修正）

| | 說明 |
|---|---|
| 現象 | NAV 仍高估 ~3.6 萬 |
| 根因 | `acc_balance` **已內含融資保證金**，融資部位只需加損益（pnl），不可再加全額市值 |
| 修正 | 依 `StockPosition.cond`（`StockOrderCond`）區分現股 / 融資 / 融券，各自套用不同計算 |

---

## NAV 公式（最終版）

```
NAV = cash + stock_value + margin_pnl + short_pnl + pending_settlement

  cash            = api.account_balance().acc_balance
                    （永豐系統：含融資保證金）
  stock_value     = Σ(last_price × quantity)   for cond == Cash
  margin_pnl      = Σ(pnl)                     for cond == MarginTrading
  short_pnl       = Σ(pnl)                     for cond == ShortSelling
  pending_settlement = Σ(amount, T∈{1,2})
```

---

## 持倉分類規則

| `StockPosition.cond` | 欄位名稱 | position_type | NAV 貢獻 |
|----------------------|----------|---------------|----------|
| `StockOrderCond.Cash` | Cash | 現股 | `last_price × quantity` |
| `StockOrderCond.MarginTrading` | MarginTrading | 融資 | `pnl` only |
| `StockOrderCond.ShortSelling` | ShortSelling | 融券 | `pnl` only |

> ⚠️ 欄位名稱為 `pos.cond`（非 `pos.order_condition`），由 `/api/debug/positions/all-fields` 實機確認。

---

## 異動檔案

### `backend/app/schemas/account.py`

```python
class AssetsResponse(BaseModel):
    nav: float
    cash: float              # acc_balance（含融資保證金）
    stock_value: float       # 現股市值
    margin_pnl: float        # 融資未實現損益
    short_pnl: float         # 融券未實現損益
    pending_t1: float        # T+1 交割款
    pending_t2: float        # T+2 交割款
    pending_settlement: float

class PositionItem(BaseModel):
    code: str
    name: str
    position_type: str       # "現股" | "融資" | "融券"
    quantity: int
    avg_price: float
    last_price: float
    market_value: float      # last_price × quantity（毛市值，供顯示）
    pnl: float
    industry: str
```

### `backend/app/services/account_service.py`

- `get_assets(api)` → 回傳 `AssetsResponse`，依 `cond` 分流加總
- `get_positions(api)` → 呼叫 `_merge_positions(api)`
- `_merge_positions(api)` → 以 `(code, cond)` 為合併 key，同代號的現股與融資分開列出

### `backend/app/api/routes_account.py`

| 路徑 | 說明 |
|------|------|
| `GET /api/account/assets` | 回傳 `AssetsResponse` |
| `GET /api/account/positions` | 回傳 `list[PositionItem]` |

### `backend/app/api/routes_debug.py`（除錯用，正式可移除）

| 路徑 | 說明 |
|------|------|
| `GET /api/debug/positions/raw` | 原始整股 / 零股清單（含所有欄位） |
| `GET /api/debug/positions/breakdown` | 逐筆市值明細（含 margin_purchase_amount） |
| `GET /api/debug/positions/all-fields` | 第一筆 position 的所有屬性名稱 |

---

## 目錄結構（階段 3 新增 / 異動）

```
backend/
├── app/
│   ├── api/
│   │   ├── routes_account.py    ← 新增
│   │   └── routes_debug.py      ← 擴充（新增 3 個除錯端點）
│   ├── schemas/
│   │   └── account.py           ← 新增
│   └── services/
│       └── account_service.py   ← 新增
└── tests/
    └── test_account_service.py  ← 新增（7 個測試案例）
```

---

## 實機驗收結果（2026-06-27）

```json
{
  "nav": 2459507.0,
  "cash": 699438.0,
  "stock_value": 1805944.0,
  "margin_pnl": 5773.0,
  "short_pnl": 0.0,
  "pending_t1": 0.0,
  "pending_t2": -51648.0,
  "pending_settlement": -51648.0
}
```

**驗算：** 699,438 + 1,805,944 + 5,773 + 0 + (−51,648) = **2,459,507** ✓

---

## 驗收清單

### 自動測試

```bash
cd backend
conda run -n stock_treemap pytest tests/test_account_service.py -v
# 預期：7 passed, 0 warnings
```

測試覆蓋情境：

| 測試名稱 | 驗證項目 |
|----------|----------|
| `test_nav_cash_only` | 純現股 NAV = cash + stock_value + settlement |
| `test_nav_with_margin` | 融資只加 pnl，不加全額市值 |
| `test_nav_no_positions` | 無持倉時 NAV = cash + settlement |
| `test_merge_cash_position` | 現股 market_value 正確，position_type = 現股 |
| `test_merge_margin_position` | 融資 market_value = gross，position_type = 融資 |
| `test_merge_cash_and_margin_same_code` | 同代號現股 + 融資各自獨立 |
| `test_merge_batched_buys` | 分批買進加權平均成本正確 |

### 手動 API 驗收

啟動伺服器後依序呼叫：

```bash
# 1. NAV 結構正確性（含 pending_t1 / pending_t2 分開）
curl http://localhost:8000/api/account/assets

# 2. 持倉列表：確認 position_type 欄位，以及同代號現股/融資是否分開
curl http://localhost:8000/api/account/positions

# 3. 除錯：確認原始 cond 欄位值
curl http://localhost:8000/api/debug/positions/all-fields
```

### 人工對帳（使用永豐 App）

| 項目 | 驗證方式 |
|------|----------|
| NAV | 與永豐 App「總資產」比對，誤差應 < 100 元（收盤價差異） |
| 現股市值 | 對照 App「現股持倉市值」 |
| 融資盈虧 | 對照 App「融資未實現損益」 |
| T+2 交割款 | 對照 App「應付交割款」 |
| 持倉數量 | 各股 quantity 與 App 持股數一致 |

---

## 已知限制

1. **`last_price` 來源**：使用 `StockPosition.last_price`（非即時串流），市場開盤中可能有 1–2 分鐘延遲。待階段 2 的 `snapshot_store` 整合後可改用快照價格提升精確度。
2. **`pnl` 計算基準**：`pnl` 由永豐後端計算，可能含手續費調整，與純粹 `(last_price - avg_price) × quantity` 的理論值略有出入（約 0.1–0.5%），屬正常現象。
3. **融券支援**：架構已預留 `short_pnl` 欄位，目前帳戶無融券持倉，未實機驗證。
