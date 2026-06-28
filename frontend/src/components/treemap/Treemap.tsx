import {
  forwardRef, useImperativeHandle,
  useRef, useEffect, useState, useMemo,
} from 'react'
import * as d3 from 'd3'
import type { TreemapResponse } from '../../api/types'
import { treemapColor } from '../../lib/colors'
import TreemapTooltip from './TreemapTooltip'

export type SizeBy = 'total_amount' | 'total_volume'

export interface TreemapHandle {
  /** D3 zoom 平滑還原至 identity transform */
  reset: () => void
}

interface Tile {
  x0: number; y0: number; x1: number; y1: number
  code: string; name: string; industry: string
  change_rate: number; change_price: number; close: number
  total_volume: number; total_amount: number
}

interface Props {
  data: TreemapResponse | null
  loading: boolean
  sizeBy: SizeBy
}

/**
 * 依「視覺尺寸」計算排版，再換算回 SVG 座標。
 * scale = D3 zoom 的 k 值（transform.k）。
 * 放大時小格子也能依視覺大小決定是否顯示更多文字。
 */
function tileLayout(w: number, h: number, scale: number) {
  // ── 全部在視覺像素空間計算 ──────────────────────────────────
  const vw = w * scale
  const vh = h * scale
  const sq = Math.sqrt(vw * vh)

  const codeFsV = Math.max(8,  Math.min(sq / 6.5, 14))
  const metaFsV = Math.max(7,  Math.min(sq / 8.5, 11))
  const lineHV  = codeFsV * 1.45
  const xPadV   = 3

  let cur = codeFsV + 2
  const yCodeV  = cur;  cur += lineHV
  const yNameV  = cur;  cur += lineHV
  const yCloseV = cur;  cur += lineHV
  const yRateV  = cur

  // ── 顯示門檻：全以視覺像素判斷 ─────────────────────────────
  const showCode  = vw > 22 && vh > 16
  const showName  = vw > 62 && vh > yNameV  + metaFsV
  const showClose = vw > 42 && vh > yCloseV + metaFsV
  const showRate  = vw > 22 && vh > yRateV  - lineHV + metaFsV

  // ── 換算回 SVG 座標（÷ scale），zoom <g> 再放大回視覺尺寸 ──
  return {
    codeFs: codeFsV / scale,
    metaFs: metaFsV / scale,
    xPad:   xPadV   / scale,
    showCode, showName, showClose, showRate,
    yCode:  yCodeV  / scale,
    yName:  yNameV  / scale,
    yClose: yCloseV / scale,
    yRate:  yRateV  / scale,
  }
}

const Treemap = forwardRef<TreemapHandle, Props>(
  function Treemap({ data, loading, sizeBy }, ref) {
    const containerRef = useRef<HTMLDivElement>(null)
    const svgRef       = useRef<SVGSVGElement>(null)
    const zoomRef      = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null)

    const [dims,       setDims]       = useState({ width: 0, height: 0 })
    const [transform,  setTransform]  = useState<d3.ZoomTransform>(d3.zoomIdentity)
    const [isDragging, setIsDragging] = useState(false)
    const [hoveredTile, setHoveredTile] = useState<Tile | null>(null)
    const [cursorPos,   setCursorPos]   = useState({ x: 0, y: 0 })

    // 向外暴露 reset()
    useImperativeHandle(ref, () => ({
      reset() {
        const svg  = svgRef.current
        const zoom = zoomRef.current
        if (!svg || !zoom) return
        d3.select(svg)
          .transition()
          .duration(350)
          .call(zoom.transform, d3.zoomIdentity)
      },
    }))

    // ResizeObserver
    useEffect(() => {
      const el = containerRef.current
      if (!el) return
      const ro = new ResizeObserver(([entry]) => {
        setDims({
          width:  Math.floor(entry.contentRect.width),
          height: Math.floor(entry.contentRect.height),
        })
      })
      ro.observe(el)
      return () => ro.disconnect()
    }, [])

    // D3 Zoom 初始化（dims 改變時重建，重設至 identity）
    useEffect(() => {
      const svg = svgRef.current
      if (!svg || !dims.width || !dims.height) return

      const zoom = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([1, 8])
        .extent([[0, 0], [dims.width, dims.height]])
        // translateExtent 嚴格限制拖曳範圍在畫布邊界內
        .translateExtent([[0, 0], [dims.width, dims.height]])
        .on('start', () => setIsDragging(true))
        .on('zoom',  (event) => setTransform(event.transform))
        .on('end',   () => setIsDragging(false))

      zoomRef.current = zoom
      const sel = d3.select(svg)
      sel.call(zoom)
      // 視窗大小改變時還原至 identity
      setTransform(d3.zoomIdentity)

      return () => { sel.on('.zoom', null) }
    }, [dims])

    // D3 treemap 幾何計算
    const tiles = useMemo<Tile[]>(() => {
      if (!data || !dims.width || !dims.height) return []

      const root = d3.hierarchy(data as never)
        .sum((d: never) => {
          const s = d as { total_amount?: number; total_volume?: number }
          return sizeBy === 'total_volume'
            ? (s.total_volume ?? 0)
            : (s.total_amount ?? 0)
        })
        .sort((a, b) => (b.value ?? 0) - (a.value ?? 0))

      const rectRoot = d3.treemap<never>()
        .size([dims.width, dims.height])
        .paddingOuter(2)
        .paddingInner(1)
        (root) as d3.HierarchyRectangularNode<never>

      return rectRoot.leaves().map((leaf) => {
        const d = leaf.data as {
          code: string; name: string; industry: string
          change_rate: number; change_price: number; close: number
          total_volume: number; total_amount: number
        }
        return {
          x0: leaf.x0, y0: leaf.y0, x1: leaf.x1, y1: leaf.y1,
          code: d.code, name: d.name, industry: d.industry ?? '',
          change_rate:  d.change_rate  ?? 0,
          change_price: d.change_price ?? 0,
          close:        d.close        ?? 0,
          total_volume: d.total_volume ?? 0,
          total_amount: d.total_amount ?? 0,
        }
      })
    }, [data, dims, sizeBy])

    return (
      <div ref={containerRef} className="w-full h-full relative overflow-hidden">
        {loading && !data && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500 text-sm">
            載入中…
          </div>
        )}

        {data && dims.width > 0 && (
          <svg
            ref={svgRef}
            width={dims.width}
            height={dims.height}
            style={{
              display: 'block',
              cursor: isDragging ? 'grabbing' : 'grab',
              userSelect: 'none',
            }}
            onMouseMove={(e) => setCursorPos({ x: e.clientX, y: e.clientY })}
            onMouseLeave={() => setHoveredTile(null)}
          >
            {/* ClipPath 定義：在 tile 的本地座標系下裁切文字 */}
            <defs>
              {tiles.map((t, i) => (
                <clipPath key={i} id={`tm-clip-${i}`}>
                  <rect
                    width={Math.max(0, t.x1 - t.x0 - 3)}
                    height={Math.max(0, t.y1 - t.y0 - 3)}
                  />
                </clipPath>
              ))}
            </defs>

            {/* 整個 Treemap 套用 D3 zoom transform */}
            <g transform={transform.toString()}>
              {tiles.map((t, i) => {
                const w   = t.x1 - t.x0
                const h   = t.y1 - t.y0
                // 傳入 transform.k，讓文字顯示門檻隨縮放動態調整
                const lyt      = tileLayout(w, h, transform.k)
                const color    = treemapColor(t.change_rate)
                const rateTxt  = `${t.change_rate >= 0 ? '+' : ''}${t.change_rate.toFixed(2)}%`
                const closeTxt = t.close > 0
                  ? t.close.toFixed(t.close >= 100 ? 1 : 2)
                  : ''

                return (
                  <g key={`${t.code}-${i}`} transform={`translate(${t.x0},${t.y0})`}>
                    <rect
                      width={w} height={h}
                      fill={color}
                      stroke="#0f172a" strokeWidth={0.5}
                      rx={2}
                      onMouseEnter={() => setHoveredTile(t)}
                    />
                    <g clipPath={`url(#tm-clip-${i})`}>
                      {lyt.showCode && (
                        <text
                          x={lyt.xPad} y={lyt.yCode}
                          fill="white"
                          fontSize={lyt.codeFs}
                          fontWeight="700"
                          fontFamily="monospace"
                        >
                          {t.code}
                        </text>
                      )}
                      {lyt.showName && (
                        <text
                          x={lyt.xPad} y={lyt.yName}
                          fill="rgba(255,255,255,0.7)"
                          fontSize={lyt.metaFs}
                        >
                          {t.name.length > 6 ? t.name.slice(0, 6) + '…' : t.name}
                        </text>
                      )}
                      {lyt.showClose && closeTxt && (
                        <text
                          x={lyt.xPad} y={lyt.yClose}
                          fill="rgba(255,255,255,0.85)"
                          fontSize={lyt.metaFs}
                        >
                          {closeTxt}
                        </text>
                      )}
                      {lyt.showRate && (
                        <text
                          x={lyt.xPad}
                          y={
                            lyt.showClose && closeTxt ? lyt.yRate
                            : lyt.showName             ? lyt.yClose
                            : lyt.showCode             ? lyt.yName
                            : lyt.yCode
                          }
                          fill="rgba(255,255,255,0.95)"
                          fontSize={lyt.metaFs}
                        >
                          {rateTxt}
                        </text>
                      )}
                    </g>
                  </g>
                )
              })}
            </g>
          </svg>
        )}

        {/* Tooltip（portal 至 body，不受 overflow-hidden 裁切） */}
        <TreemapTooltip tile={hoveredTile} x={cursorPos.x} y={cursorPos.y} />

        {/* 顏色圖例 */}
        <div className="absolute bottom-5 left-3 flex flex-col items-start gap-0.5 pointer-events-none select-none">
          {/* 漸層色條：與 treemapColor() 同一套公式 */}
          <div
            className="w-52 h-2.5 rounded-full shadow-md"
            style={{
              background: [
                'linear-gradient(to right',
                'rgb(207,0,0)    0%',      // -10%
                'rgb(144,0,0)   25%',      // -5%
                'rgb(80,0,0)  49.5%',      // ≈ 0- (極暗紅)
                'rgb(107,114,128) 50%',    // 0%  (灰)
                'rgb(0,80,0)   50.5%',     // ≈ 0+ (極暗綠)
                'rgb(0,144,0)   75%',      // +5%
                'rgb(0,207,0)  100%)',     // +10%
              ].join(','),
            }}
          />
          {/* 刻度標籤 */}
          <div className="flex justify-between w-52 px-0.5">
            {['-10%', '-5%', '0%', '+5%', '+10%'].map((label) => (
              <span key={label} className="text-[9px] text-gray-400 leading-none">
                {label}
              </span>
            ))}
          </div>
        </div>

        {/* 最後更新時間 */}
        {data?.last_updated && (
          <div className="absolute bottom-1 right-2 text-[9px] text-gray-600 pointer-events-none">
            {new Date(data.last_updated).toLocaleTimeString('zh-TW', {
              hour: '2-digit', minute: '2-digit',
            })}
          </div>
        )}
      </div>
    )
  }
)

export default Treemap
