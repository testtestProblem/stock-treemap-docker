import { useState, useEffect } from 'react'
import { AlertCircle } from 'lucide-react'
import WatchlistTabs, { type TabId } from './WatchlistTabs'
import PositionTable from '../positions/PositionTable'
import type { PositionItem, TreemapResponse } from '../../api/types'
import { useWatchlist, useTreemap } from '../../hooks'
import { fmtPrice, fmtPct } from '../../lib/format'
import { pnlClass } from '../../lib/colors'

const LS_KEY = 'listpanel_active_tab'

function readTab(): TabId {
  try {
    const v = localStorage.getItem(LS_KEY)
    if (v === 'holdings' || v === 'watchlist') return v
  } catch {}
  return 'holdings'
}

// ── 自選清單股票列表 ───────────────────────────────────────────────────────────

function buildLookup(treemap: TreemapResponse | null): Map<string, { name: string; close: number; change_rate: number; change_price: number }> {
  const map = new Map<string, { name: string; close: number; change_rate: number; change_price: number }>()
  if (!treemap) return map
  for (const industry of treemap.children) {
    for (const stock of industry.children) {
      map.set(stock.code, {
        name: stock.name,
        close: stock.close,
        change_rate: stock.change_rate,
        change_price: stock.change_price,
      })
    }
  }
  return map
}

function WatchlistStockRow({ code, snap }: {
  code: string
  snap: { name: string; close: number; change_rate: number; change_price: number } | undefined
}) {
  return (
    <div className="bg-gray-700/50 rounded-lg px-3 py-2 text-xs">
      <div className="flex items-center justify-between mb-0.5">
        <div className="flex items-center gap-1.5">
          <span className="font-bold text-gray-100">{code}</span>
          <span className="text-[10px] text-gray-500 truncate max-w-[80px]">
            {snap?.name ?? '—'}
          </span>
        </div>
        {snap ? (
          <span className={pnlClass(snap.change_rate)}>
            {fmtPct(snap.change_rate)}
          </span>
        ) : (
          <span className="text-gray-600">—</span>
        )}
      </div>
      <div className="flex items-center gap-3 text-gray-400 tabular-nums">
        <span>
          <span className="text-gray-600 text-[9px] mr-0.5">現價</span>
          {snap ? fmtPrice(snap.close) : '—'}
        </span>
        {snap && (
          <span className={pnlClass(snap.change_price)}>
            {snap.change_price >= 0 ? '+' : ''}{fmtPrice(snap.change_price)}
          </span>
        )}
      </div>
    </div>
  )
}

function WatchlistList() {
  const watchlist = useWatchlist()
  const snapshotQuery = useTreemap('watchlist')

  const lookup = buildLookup(snapshotQuery.data)
  const codes = watchlist.data?.codes ?? []

  if (watchlist.loading && !watchlist.data) {
    return <div className="text-xs text-gray-500 animate-pulse px-1">載入中…</div>
  }

  if (watchlist.error) {
    return (
      <div className="flex items-center gap-1 text-xs text-red-400">
        <AlertCircle size={11} />
        <span>{watchlist.error}</span>
      </div>
    )
  }

  if (codes.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-xs text-gray-600">自選清單為空<br />可於下方搜尋新增</p>
      </div>
    )
  }

  return (
    <div className="overflow-y-auto flex-1 space-y-1 pr-0.5">
      {codes.map(code => (
        <WatchlistStockRow key={code} code={code} snap={lookup.get(code)} />
      ))}
    </div>
  )
}

// ── 主元件 ────────────────────────────────────────────────────────────────────

interface Props {
  positions: {
    data: PositionItem[] | null
    loading: boolean
    error: string | null
  }
}

export default function ListPanel({ positions }: Props) {
  const [activeTab, setActiveTab] = useState<TabId>(readTab)
  const watchlistQuery = useWatchlist()

  useEffect(() => {
    try { localStorage.setItem(LS_KEY, activeTab) } catch {}
  }, [activeTab])

  const watchlistCount = watchlistQuery.data?.codes.length

  return (
    <div className="flex flex-col h-full">
      <WatchlistTabs
        active={activeTab}
        onChange={setActiveTab}
        holdingsCount={positions.data?.length}
        watchlistCount={watchlistCount}
      />

      <div className="flex-1 min-h-0 flex flex-col">
        {activeTab === 'holdings' ? (
          <PositionTable
            data={positions.data}
            loading={positions.loading}
            error={positions.error}
          />
        ) : (
          <WatchlistList />
        )}
      </div>
    </div>
  )
}
