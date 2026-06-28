import { useState, useRef } from 'react'
import { RefreshCw } from 'lucide-react'
import AssetCards from '../cards/AssetCards'
import PositionTable from '../positions/PositionTable'
import Treemap, { type SizeBy, type TreemapHandle } from '../treemap/Treemap'
import PerformanceChart from '../performance/PerformanceChart'
import { useAssets, usePositions, useTreemap, usePerformance } from '../../hooks'

type TreemapMode = 'market' | 'watchlist'

const SIZE_OPTIONS: { value: SizeBy; label: string }[] = [
  { value: 'total_amount', label: '成交額' },
  { value: 'total_volume', label: '成交量' },
]

const MODE_OPTIONS: { value: TreemapMode; label: string }[] = [
  { value: 'market',    label: '全台股' },
  { value: 'watchlist', label: '自選清單' },
]

function ToggleGroup<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[]
  value: T
  onChange: (v: T) => void
}) {
  return (
    <div className="flex rounded-md overflow-hidden border border-gray-700">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`px-3 py-1 text-xs transition-colors ${
            value === opt.value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

export default function DashboardLayout() {
  const [mode,   setMode]   = useState<TreemapMode>('market')
  const [sizeBy, setSizeBy] = useState<SizeBy>('total_amount')
  const treemapRef = useRef<TreemapHandle>(null)

  const assets      = useAssets()
  const positions   = usePositions()
  const treemap     = useTreemap(mode)
  const performance = usePerformance()

  const lastUpdate = assets.data
    ? new Date().toLocaleTimeString('zh-TW', {
        hour: '2-digit', minute: '2-digit', second: '2-digit',
      })
    : null

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col gap-3 p-4">

      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="text-lg font-bold tracking-wide text-white cursor-pointer hover:text-blue-300 transition-colors"
            title="點擊重設 Treemap 視角"
            onClick={() => treemapRef.current?.reset()}
          >
            台股 Treemap Dashboard
          </span>
          <span className="text-xs text-gray-600 border border-gray-700 rounded px-1.5 py-0.5">
            永豐金 Shioaji
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          {lastUpdate && <span>更新：{lastUpdate}</span>}
          <button
            onClick={() => { assets.refresh(); positions.refresh(); treemap.refresh() }}
            className="flex items-center gap-1 text-gray-400 hover:text-gray-200 transition-colors"
          >
            <RefreshCw size={12} />
            重新整理
          </button>
        </div>
      </header>

      {/* ── 資產卡片 ────────────────────────────────────────────── */}
      <AssetCards data={assets.data} loading={assets.loading} error={assets.error} />

      {/* ── 主內容：持倉表 + Treemap ───────────────────────────── */}
      {/* flex-col on mobile, flex-row on lg+ */}
      <div className="flex flex-col lg:flex-row gap-3 flex-1" style={{ minHeight: 480 }}>

        {/* 左側持倉表（mobile 固定高 300px，lg 側欄） */}
        <aside className="w-full lg:w-72 flex-shrink-0 bg-gray-900 rounded-xl p-3 overflow-hidden"
          style={{ height: 'auto', minHeight: 0 }}
        >
          <div className="h-72 lg:h-full">
            <PositionTable data={positions.data} loading={positions.loading} error={positions.error} />
          </div>
        </aside>

        {/* 右側 Treemap（mobile 最小高 420px） */}
        <main className="flex-1 bg-gray-900 rounded-xl p-3 flex flex-col gap-2 min-w-0 min-h-[420px]">

          {/* 工具列：模式切換 + 大小依據 */}
          <div className="flex items-center justify-between flex-shrink-0 flex-wrap gap-2">
            <span className="text-sm font-semibold text-gray-200">
              {mode === 'market' ? '全台股' : '自選清單'} Treemap
            </span>

            <div className="flex items-center gap-2">
              {/* 大小依據 */}
              <span className="text-xs text-gray-500">大小</span>
              <ToggleGroup
                options={SIZE_OPTIONS}
                value={sizeBy}
                onChange={(v) => setSizeBy(v)}
              />

              {/* 模式 */}
              <span className="text-xs text-gray-500 ml-2">範圍</span>
              <ToggleGroup
                options={MODE_OPTIONS}
                value={mode}
                onChange={(v) => setMode(v)}
              />
            </div>
          </div>

          {/* Treemap 主體 */}
          <div className="flex-1 overflow-hidden min-h-0">
            <Treemap
              ref={treemapRef}
              data={treemap.data}
              loading={treemap.loading}
              sizeBy={sizeBy}
            />
          </div>
        </main>
      </div>

      {/* ── 底部績效圖 ───────────────────────────────────────────── */}
      <section className="bg-gray-900 rounded-xl p-3">
        <p className="text-sm font-semibold text-gray-200 mb-2">
          資產績效比較（累積報酬率 %）
        </p>
        <div className="h-48">
          <PerformanceChart data={performance.data} loading={performance.loading} />
        </div>
      </section>
    </div>
  )
}
