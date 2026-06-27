import { useRef, useEffect, useState, useMemo } from 'react'
import * as d3 from 'd3'
import type { TreemapResponse } from '../../api/types'
import { treemapColor } from '../../lib/colors'

interface Tile {
  x0: number; y0: number; x1: number; y1: number
  code: string; name: string; change_rate: number; industry: string
}

interface Props {
  data: TreemapResponse | null
  loading: boolean
}

export default function Treemap({ data, loading }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dims, setDims] = useState({ width: 0, height: 0 })

  // ResizeObserver：偵測容器尺寸變化
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => {
      setDims({
        width: Math.floor(entry.contentRect.width),
        height: Math.floor(entry.contentRect.height),
      })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // D3 treemap 幾何計算（只依賴 data 與 dims，不操作 DOM）
  const tiles = useMemo<Tile[]>(() => {
    if (!data || !dims.width || !dims.height) return []

    const root = d3.hierarchy(data as never)
      .sum((d: never) => (d as { total_amount?: number }).total_amount ?? 0)
      .sort((a, b) => (b.value ?? 0) - (a.value ?? 0))

    d3.treemap<never>()
      .size([dims.width, dims.height])
      .paddingOuter(2)
      .paddingInner(1)
      (root)

    return root.leaves().map((leaf) => {
      const d = leaf.data as {
        code: string; name: string; change_rate: number; industry: string
      }
      return {
        x0: leaf.x0, y0: leaf.y0, x1: leaf.x1, y1: leaf.y1,
        code: d.code, name: d.name, change_rate: d.change_rate ?? 0,
        industry: d.industry,
      }
    })
  }, [data, dims])

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden">
      {loading && !data && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-500 text-sm">
          載入中…
        </div>
      )}

      {data && dims.width > 0 && (
        <svg
          width={dims.width}
          height={dims.height}
          style={{ display: 'block' }}
        >
          <defs>
            {tiles.map((t, i) => (
              <clipPath key={i} id={`clip-${i}`}>
                <rect width={Math.max(0, t.x1 - t.x0 - 2)} height={Math.max(0, t.y1 - t.y0 - 2)} />
              </clipPath>
            ))}
          </defs>

          {tiles.map((t, i) => {
            const w = t.x1 - t.x0
            const h = t.y1 - t.y0
            const color = treemapColor(t.change_rate)
            const showCode = w > 36 && h > 24
            const showRate = w > 36 && h > 38
            const showName = w > 50 && h > 52

            return (
              <g key={`${t.code}-${i}`} transform={`translate(${t.x0},${t.y0})`}>
                <rect
                  width={w}
                  height={h}
                  fill={color}
                  stroke="#0f172a"
                  strokeWidth={0.5}
                  rx={2}
                />
                <g clipPath={`url(#clip-${i})`}>
                  {showCode && (
                    <text
                      x={3} y={13}
                      fill="white"
                      fontSize={Math.min(12, w / 4)}
                      fontWeight="700"
                    >
                      {t.code}
                    </text>
                  )}
                  {showName && (
                    <text x={3} y={26} fill="rgba(255,255,255,0.75)" fontSize={9}>
                      {t.name.length > 6 ? t.name.slice(0, 6) + '…' : t.name}
                    </text>
                  )}
                  {showRate && (
                    <text
                      x={3}
                      y={showName ? 39 : 26}
                      fill="rgba(255,255,255,0.9)"
                      fontSize={10}
                    >
                      {t.change_rate >= 0 ? '+' : ''}{t.change_rate.toFixed(2)}%
                    </text>
                  )}
                </g>
              </g>
            )
          })}
        </svg>
      )}

      {data && data.last_updated && (
        <div className="absolute bottom-1 right-2 text-[9px] text-gray-600 pointer-events-none">
          {new Date(data.last_updated).toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })}
        </div>
      )}
    </div>
  )
}
