/** 美式漲跌色：漲綠跌紅 */
export const COLORS = {
  up: '#22c55e',    // green-500
  down: '#ef4444',  // red-500
  flat: '#6b7280',  // gray-500
} as const

export function changeColor(rate: number): string {
  if (rate > 0) return COLORS.up
  if (rate < 0) return COLORS.down
  return COLORS.flat
}

/** 依漲跌幅深淺計算 Treemap 格子顏色（±10% 為上下限） */
export function treemapColor(rate: number): string {
  const clamped = Math.max(-10, Math.min(10, rate))
  const ratio = Math.abs(clamped) / 10
  if (clamped > 0) {
    const g = Math.round(80 + ratio * 127)
    return `rgb(0, ${g}, 0)`
  }
  if (clamped < 0) {
    const r = Math.round(80 + ratio * 127)
    return `rgb(${r}, 0, 0)`
  }
  return COLORS.flat
}
