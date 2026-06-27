# Shioaji API — 持倉單位行為與 NAV 公式備忘錄

> 本文記錄永豐金 Shioaji `list_positions()` 的實際回傳行為，
> 以及經三輪實機除錯後確認的正確 NAV 計算公式。
> **後續開發請以本文為準，勿重蹈覆轍。**

---

## 一、`list_positions()` 單位行為（最重要）

### 函式簽名

```python
api.list_positions(account=api.stock_account, unit=Unit.Common)
api.list_positions(account=api.stock_account, unit=Unit.Share)
```

### 關鍵發現：兩個 unit **並非互斥**

```
┌──────────────────────┬──────────────────┬──────────────────────────────┐
│ 持倉類型              │ Unit.Common      │ Unit.Share                   │
├──────────────────────┼──────────────────┼──────────────────────────────┤
│ 整張部位（≥1000股）  │ ✅ 回傳          │ ✅ 回傳（同一筆！）           │
│                      │ quantity 單位：張 │ quantity 單位：股             │
├──────────────────────┼──────────────────┼──────────────────────────────┤
│ 零股部位（< 1000股） │ ✅ 回傳          │ ✅ 回傳                       │
│                      │ quantity = 0     │ quantity = 實際股數           │
├──────────────────────┼──────────────────┼──────────────────────────────┤
│ 融資部位             │ ✅ 回傳          │ ✅ 回傳（同一筆！）           │
│                      │ quantity 單位：張 │ quantity 單位：股             │
└──────────────────────┴──────────────────┴──────────────────────────────┘
```

### 實機資料佐證（2026-06-27）

以 **0050** 為例（持有 3 張整股）：

```
Unit.Common 回傳：
  { code: "0050", quantity: 3,    price: 91.87, last_price: 103.1, pnl: 32939 }
                  ↑ 張

Unit.Share 回傳：
  { code: "0050", quantity: 3000, price: 91.87, last_price: 103.1, pnl: 32939 }
                  ↑ 股（= 3 張 × 1000）
```

> `price`、`last_price`、`pnl` **完全相同** — 這是同一筆資料的兩種表達方式。

以 **2330** 為例（持有 270 零股，無整張）：

```
Unit.Common 回傳：
  { code: "2330", quantity: 0,   price: 1931.15, pnl: 107601 }
                  ↑ 0 張（不足一張故為 0，但 pnl 仍帶值）

Unit.Share 回傳：
  { code: "2330", quantity: 270, price: 1931.15, pnl: 107601 }
                  ↑ 270 股
```

### 正確使用方式

```python
# ✅ 正確：只呼叫一次 Unit.Share，已涵蓋所有持倉
all_positions = api.list_positions(account=api.stock_account, unit=sj.Unit.Share)

# ❌ 錯誤：同時呼叫兩者再加總 → 整張部位雙重計算
common = api.list_positions(..., unit=sj.Unit.Common)
odd    = api.list_positions(..., unit=sj.Unit.Share)
# common × 1000 + odd = 整張部位被算兩次！
```

---

## 二、`StockPosition` 欄位清單（實機確認）

```python
# 由 /api/debug/positions/all-fields 取得
{
  "id":                    "0",
  "code":                  "0050",
  "direction":             "Action.Buy",
  "quantity":              "3000",          # Unit.Share 時為股數
  "price":                 "91.87",         # 加權平均成本
  "last_price":            "103.1",         # 目前市價
  "pnl":                   "32939.0",       # 未實現損益（含手續費調整）
  "yd_quantity":           "3000",          # 昨日庫存
  "cond":                  "StockOrderCond.Cash",  # ← 欄位名是 cond，非 order_condition
  "margin_purchase_amount":"0",             # 融資餘額（融資部位 > 0）
  "collateral":            "0",             # 擔保品（融券相關）
  "short_sale_margin":     "0",             # 融券保證金
  "interest":              "0"              # 利息
}
```

> ⚠️ **陷阱**：欄位名稱為 `cond`，不是常見文件寫的 `order_condition`。

### `cond` 可能值

```python
import shioaji as sj
StockOrderCond = sj.StockOrderCond  # 使用 sj.StockOrderCond，避免棄用警告

StockOrderCond.Cash          # 現股
StockOrderCond.MarginTrading # 融資
StockOrderCond.ShortSelling  # 融券
StockOrderCond.Netting       # 餘額交割
```

---

## 三、`acc_balance` 的含義（決定 NAV 公式）

### 關鍵事實

> **永豐的 `acc_balance` 已內含融資保證金。**
>
> 當你下融資單時，保證金（約 40%）從可用餘額扣除，
> 但仍反映在 `acc_balance` 中，**不會從帳戶數字消失**。

### 驗算佐證

以 **00673R 融資 6000 股**為例（cost 14.71，last 15.72，融資餘額 52,000）：

```
理論保證金  = 6000 × 14.71 × 40% ≈ 35,304
融資餘額    = 52,000（由 margin_purchase_amount 取得）
融資毛市值  = 6000 × 15.72 = 94,320
融資淨值    = 94,320 - 52,000 = 42,320
融資損益    = pnl = 5,773

若 acc_balance 不含保證金：
  NAV = cash + 現股 + 融資淨值 + settlement
      = 699,438 + 1,805,944 + 42,320 + (-51,648)
      = 2,496,054   ← 高估約 36,547（≈ 保證金 35,304）

若 acc_balance 含保證金（正確）：
  NAV = cash + 現股 + 融資損益 + settlement
      = 699,438 + 1,805,944 + 5,773 + (-51,648)
      = 2,459,507   ← 與券商 App 吻合 ✅
```

---

## 四、最終 NAV 公式

```
NAV = cash + stock_value + margin_pnl + short_pnl + pending_settlement

  cash              = api.account_balance().acc_balance
                      （含融資保證金，含融券擔保品）

  stock_value       = Σ (last_price × quantity)
                        for pos where pos.cond == StockOrderCond.Cash

  margin_pnl        = Σ pos.pnl
                        for pos where pos.cond == StockOrderCond.MarginTrading

  short_pnl         = Σ pos.pnl
                        for pos where pos.cond == StockOrderCond.ShortSelling

  pending_settlement= Σ settlement.amount
                        for settlement where settlement.T in (1, 2)
                      （T=0 為當日已結算，不計入；T=1/2 為應付款，通常為負值）
```

### 公式摘要

| 持倉類型 | NAV 貢獻 | 理由 |
|----------|----------|------|
| 現股 | `last_price × quantity` | 市值即淨值 |
| 融資 | `pnl`（損益） | 保證金已在 `cash` 中；市值 = 保證金 + 借款 + 損益，借款已由券商持有不計入 |
| 融券 | `pnl`（損益） | 擔保品已在 `cash` 中；放空收入 = 擔保品來源，損益為淨差 |

---

## 五、合併邏輯

### 分組 key

以 `(code, cond)` 為合併 key（而非單純 `code`），避免同一代號的現股與融資被混在一起。

```python
key = (pos.code, pos.cond)
```

**範例：00673R**

```
(code="00673R", cond=Cash)          → 現股 3000 股，market_value = 47,160
(code="00673R", cond=MarginTrading) → 融資 6000 股，market_value = 94,320（毛，僅顯示用）
                                                     pnl = 5,773（計入 NAV）
```

### 同代號、同 cond 的多筆（分批買進）

Unit.Share 可能對同一 `(code, cond)` 回傳多筆（不同批次買入），需累加：

```python
merged[key]["shares"]   += pos.quantity
merged[key]["cost_sum"] += pos.price * pos.quantity  # 加權成本
merged[key]["pnl"]      += pos.pnl
```

**範例：00673R 同為融資但分兩批**

```
batch1: quantity=3000, price=11.79, pnl=11,687
batch2: quantity=6000, price=14.71, pnl= 5,773
合計：  quantity=9000, avg_price=13.40, pnl=17,460
```

---

## 六、程式碼位置

| 模組 | 路徑 | 職責 |
|------|------|------|
| 持倉合併 | `backend/app/services/account_service.py` | `_merge_positions()` |
| NAV 計算 | `backend/app/services/account_service.py` | `get_assets()` |
| API 路由 | `backend/app/api/routes_account.py` | GET /api/account/assets |
| Schema | `backend/app/schemas/account.py` | `AssetsResponse`, `PositionItem` |
| 除錯端點 | `backend/app/api/routes_debug.py` | all-fields / raw / breakdown |
| 測試 | `backend/tests/test_account_service.py` | 7 個測試案例 |
