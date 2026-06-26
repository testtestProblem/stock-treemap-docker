import type { AssetsResponse, Position, TreemapNode, KbarItem, PerformancePoint } from './types'

const BASE = ''  // Vite proxy 轉發至 localhost:8000

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API ${path} 回傳 ${res.status}`)
  return res.json() as Promise<T>
}

export const api = {
  health: () => get<{ status: string }>('/health'),
  getAssets: () => get<AssetsResponse>('/api/account/assets'),
  getPositions: () => get<Position[]>('/api/account/positions'),
  getTreemap: (mode: 'market' | 'watchlist' = 'market') =>
    get<TreemapNode>(`/api/market/treemap?mode=${mode}`),
  getKbars: (code: string, start: string, end: string) =>
    get<KbarItem[]>(`/api/market/kbars?code=${code}&start=${start}&end=${end}`),
  getPerformance: () => get<PerformancePoint[]>('/api/history/performance'),
}
