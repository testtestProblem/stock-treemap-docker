import type {
  AssetsResponse,
  PositionItem,
  TreemapResponse,
  KbarsResponse,
  PerformanceResponse,
  WatchlistResponse,
  ApiStatusResponse,
  ReconnectResponse,
} from './types'

const BASE = ''  // Vite proxy 轉發至 localhost:8000

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API ${path} 回傳 ${res.status}`)
  return res.json() as Promise<T>
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API PUT ${path} 回傳 ${res.status}`)
  return res.json() as Promise<T>
}

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST' })
  if (!res.ok) throw new Error(`API POST ${path} 回傳 ${res.status}`)
  return res.json() as Promise<T>
}

export const api = {
  health: () => get<{ status: string }>('/health'),

  // 除錯 / 狀態
  getStatus: () => get<ApiStatusResponse>('/api/debug/status'),
  reconnect: () => post<ReconnectResponse>('/api/debug/reconnect'),
  exportDb: async (): Promise<Blob> => {
    const res = await fetch(`${BASE}/api/admin/export-db`)
    if (!res.ok) throw new Error(`API /api/admin/export-db 回傳 ${res.status}`)
    return res.blob()
  },

  // 帳務
  getAssets: () => get<AssetsResponse>('/api/account/assets'),
  getPositions: () => get<PositionItem[]>('/api/account/positions'),

  // 市場
  getTreemap: (mode: 'market' | 'watchlist' = 'market') =>
    get<TreemapResponse>(`/api/market/treemap?mode=${mode}`),
  getKbars: (code: string, start = '', end = '') =>
    get<KbarsResponse>(`/api/market/kbars?code=${code}&start=${start}&end=${end}`),
  getWatchlist: () => get<WatchlistResponse>('/api/market/watchlist'),
  setWatchlist: (codes: string[]) =>
    put<WatchlistResponse>('/api/market/watchlist', { codes }),

  // 歷史績效
  getPerformance: () => get<PerformanceResponse>('/api/history/performance'),
}
