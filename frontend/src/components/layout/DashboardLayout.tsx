import { useState } from 'react'
import { RefreshCw } from 'lucide-react'
import AssetCards from '../cards/AssetCards'
import PositionTable from '../positions/PositionTable'
import Treemap from '../treemap/Treemap'
import PerformanceChart from '../performance/PerformanceChart'
import { useAssets, usePositions, useTreemap, usePerformance } from '../../hooks'

type TreemapMode = 'market' | 'watchlist'

export default function DashboardLayout() {
  const [mode, setMode] = useState<TreemapMode>('market')

  const assets      = useAssets()
  const positions   = usePositions()
  const treemap     = useTreemap(mode)
  const performance = usePerformance()

  const lastUpdate = assets.data
    ? new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : null

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col gap-3 p-4">

      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold tracking-wide text-white">台股 Treemap Dashboard</span>
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
      <AssetCards data={assets.data} loading={assets.loading} />

      {/* ── 主內容：持倉表 + Treemap ───────────────────────────── */}
      <div className="flex gap-3 flex-1" style={{ minHeight: 480 }}>

        {/* 左側持倉表 */}
        <aside className="w-72 flex-shrink-0 bg-gray-900 rounded-xl p-3 overflow-hidden">
          <PositionTable data={positions.data} loading={positions.loading} />
        </aside>

        {/* 右側 Treemap */}
        <main className="flex-1 bg-gray-900 rounded-xl p-3 flex flex-col gap-2 overflow-hidden">
          {/* 切換按鈕 */}
          <div className="flex items-center justify-between flex-shrink-0">
            <span className="text-sm font-semibold text-gray-200">
              {mode === 'market' ? '全台股 Treemap' : '自選清單 Treemap'}
            </span>
            <div className="flex gap-1.5">
              {(['market', 'watchlist'] as TreemapMode[]).map(m => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`px-3 py-1 text-xs rounded-md transition-colors ${
                    mode === m
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {m === 'market' ? '全台股' : '自選清單'}
                </button>
              ))}
            </div>
          </div>

          {/* Treemap 主體 */}
          <div className="flex-1 overflow-hidden">
            <Treemap data={treemap.data} loading={treemap.loading} />
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
