export type TabId = 'holdings' | 'watchlist'

interface Tab {
  id: TabId
  label: string
}

const TABS: Tab[] = [
  { id: 'holdings',  label: '庫存' },
  { id: 'watchlist', label: '自選清單' },
]

interface Props {
  active: TabId
  onChange: (id: TabId) => void
  holdingsCount?: number
  watchlistCount?: number
}

export default function WatchlistTabs({
  active,
  onChange,
  holdingsCount,
  watchlistCount,
}: Props) {
  const counts: Record<TabId, number | undefined> = {
    holdings:  holdingsCount,
    watchlist: watchlistCount,
  }

  return (
    <div className="flex items-center gap-1 flex-shrink-0 border-b border-gray-700 pb-2 mb-2">
      {TABS.map(tab => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
            active === tab.id
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'
          }`}
        >
          {tab.label}
          {counts[tab.id] != null && (
            <span className="ml-1 opacity-70">({counts[tab.id]})</span>
          )}
        </button>
      ))}
    </div>
  )
}
