// 帳務
export interface AssetsResponse {
  nav: number
  acc_balance: number
  position_value: number
  pending_settlement: number
}

export interface Position {
  code: string
  name: string
  quantity: number      // 總股數
  avg_price: number
  last_price: number
  market_value: number
  pnl: number
}

// 市場
export interface TreemapNode {
  name: string
  code?: string
  industry?: string
  change_rate?: number
  total_amount?: number
  children?: TreemapNode[]
}

export interface KbarItem {
  ts: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// 歷史績效
export interface PerformancePoint {
  date: string
  nav_pct: number
  pct_0050: number
  pct_2330: number
}
