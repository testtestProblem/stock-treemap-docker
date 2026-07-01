import { api } from '../api/client'
import { usePoll } from './usePoll'

export const useAssets    = () => usePoll(() => api.getAssets(),      30_000)
export const usePositions = () => usePoll(() => api.getPositions(),   30_000)
export const usePerformance = () => usePoll(() => api.getPerformance(), 300_000)
export const useApiStatus = () => usePoll(() => api.getStatus(),       15_000)

export function useTreemap(mode: 'market' | 'watchlist') {
  return usePoll(() => api.getTreemap(mode), 60_000)
}
