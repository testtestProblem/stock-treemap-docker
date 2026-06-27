import type { PositionItem } from '../../api/types'
import { fmtMoney, fmtPrice, fmtPct } from '../../lib/format'

const TYPE_STYLE: Record<string, string> = {
  '現股': 'bg-gray-700 text-gray-300',
  '融資': 'bg-amber-900/60 text-amber-300',
  '融券': 'bg-purple-900/60 text-purple-300',
}

interface Props {
  data: PositionItem[] | null
  loading: boolean
}

export default function PositionTable({ data, loading }: Props) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-gray-200">持倉列表</span>
        {data && (
          <span className="text-xs text-gray-500">{data.length} 檔</span>
        )}
      </div>

      {loading && !data && (
        <p className="text-xs text-gray-500 text-center py-8">載入中…</p>
      )}

      <div className="overflow-y-auto flex-1 space-y-1 pr-1">
        {data?.map((pos) => (
          <div
            key={`${pos.code}-${pos.position_type}`}
            className="bg-gray-700/50 rounded-lg px-3 py-2 text-xs"
          >
            {/* 第一行：代號 + 持倉類型 + 損益 */}
            <div className="flex items-center justify-between mb-0.5">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-gray-100">{pos.code}</span>
                <span className={`text-[10px] rounded px-1 py-0.5 ${TYPE_STYLE[pos.position_type] ?? TYPE_STYLE['現股']}`}>
                  {pos.position_type}
                </span>
              </div>
              <span className={pos.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                {fmtPct(pos.pnl / (pos.avg_price * pos.quantity) * 100)}
              </span>
            </div>

            {/* 第二行：名稱 */}
            <p className="text-gray-400 truncate mb-1">{pos.name}</p>

            {/* 第三行：數量 / 均價 / 現價 / 市值 */}
            <div className="grid grid-cols-4 gap-1 text-gray-300 tabular-nums">
              <div>
                <p className="text-gray-500 text-[9px]">股數</p>
                <p>{pos.quantity.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-gray-500 text-[9px]">均價</p>
                <p>{fmtPrice(pos.avg_price)}</p>
              </div>
              <div>
                <p className="text-gray-500 text-[9px]">現價</p>
                <p>{fmtPrice(pos.last_price)}</p>
              </div>
              <div>
                <p className="text-gray-500 text-[9px]">市值</p>
                <p>{fmtMoney(pos.market_value)}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
