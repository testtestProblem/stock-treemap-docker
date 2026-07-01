// 帳務
export interface AssetsResponse {
  nav: number
  cash: number
  stock_value: number
  margin_pnl: number
  short_pnl: number
  pending_t1: number
  pending_t2: number
  pending_settlement: number
}

export interface PositionItem {
  code: string
  name: string
  position_type: string   // "現股" | "融資" | "融券"
  quantity: number
  avg_price: number
  last_price: number
  market_value: number
  pnl: number
  industry: string
}

// 市場
export interface TreemapStock {
  code: string
  name: string
  industry: string
  close: number
  change_price: number
  change_rate: number
  total_volume: number
  total_amount: number
}

export interface IndustryNode {
  name: string
  children: TreemapStock[]
}

export interface TreemapResponse {
  mode: string
  name: string
  children: IndustryNode[]
  last_updated: string | null
}

export interface KbarItem {
  ts: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
}

export interface KbarsResponse {
  code: string
  start: string
  end: string
  bars: KbarItem[]
  from_cache: boolean
}

// 歷史績效
export interface PerformanceSeries {
  dates: string[]
  values: number[]
}

export interface PerformanceResponse {
  nav: PerformanceSeries
  price_0050: PerformanceSeries
  price_2330: PerformanceSeries
  record_count: number
}

// 自選清單
export interface WatchlistResponse {
  codes: string[]
}

// API 狀態（Task 8-1）
export interface ApiStatusResponse {
  connected: boolean
  usage_pct: number
  simulation?: boolean
  stock_account?: string | null
  last_login?: string | null
  accounts?: string[]
}

export interface ReconnectResponse {
  connected: boolean
  message: string
}
