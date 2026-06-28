import { motion, AnimatePresence } from 'motion/react'
import { AlertCircle } from 'lucide-react'
import type { PositionItem } from '../../api/types'
import { fmtMoney, fmtPrice, fmtPct } from '../../lib/format'

const TYPE_STYLE: Record<string, string> = {
  '現股': 'bg-gray-700 text-gray-300',
  '融資': 'bg-amber-900/60 text-amber-300',
  '融券': 'bg-purple-900/60 text-purple-300',
}

function SkeletonBlock({ className = '' }: { className?: string }) {
  return <div className={`bg-gray-700/70 rounded animate-pulse ${className}`} />
}

function SkeletonRow() {
  return (
    <div className="bg-gray-700/40 rounded-lg px-3 py-2 flex flex-col gap-1.5">
      <div className="flex justify-between">
        <SkeletonBlock className="h-3 w-14" />
        <SkeletonBlock className="h-3 w-10" />
      </div>
      <SkeletonBlock className="h-2.5 w-20" />
      <div className="grid grid-cols-4 gap-1">
        {[0,1,2,3].map(i => <SkeletonBlock key={i} className="h-3" />)}
      </div>
    </div>
  )
}

interface Props {
  data: PositionItem[] | null
  loading: boolean
  error?: string | null
}

export default function PositionTable({ data, loading, error }: Props) {
  const pnlRate = (pos: PositionItem) => {
    const cost = pos.avg_price * pos.quantity
    return cost > 0 ? pos.pnl / cost * 100 : 0
  }

  return (
    <div className="flex flex-col h-full">
      {/* 標題列 */}
      <div className="flex items-center justify-between mb-2 flex-shrink-0">
        <span className="text-sm font-semibold text-gray-200">持倉列表</span>
        {data && <span className="text-xs text-gray-500">{data.length} 檔</span>}
      </div>

      {/* 錯誤 */}
      {error && !loading && (
        <div className="flex items-center gap-1.5 text-xs text-red-400 mb-2 flex-shrink-0">
          <AlertCircle size={11} />
          <span>{error}</span>
        </div>
      )}

      <div className="overflow-y-auto flex-1 space-y-1 pr-0.5">
        {/* Skeleton */}
        {loading && !data && (
          <div className="space-y-1">
            {[0,1,2,3].map(i => <SkeletonRow key={i} />)}
          </div>
        )}

        {/* 持倉列表（AnimatePresence 讓新增/移除有動畫） */}
        <AnimatePresence initial={false}>
          {data?.map((pos, i) => (
            <motion.div
              key={`${pos.code}-${pos.position_type}`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2, delay: i * 0.025 }}
              className="bg-gray-700/50 rounded-lg px-3 py-2 text-xs"
            >
              {/* 代號 + 類型 + 損益率 */}
              <div className="flex items-center justify-between mb-0.5">
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-gray-100">{pos.code}</span>
                  <span className={`text-[10px] rounded px-1 py-0.5 ${TYPE_STYLE[pos.position_type] ?? TYPE_STYLE['現股']}`}>
                    {pos.position_type}
                  </span>
                </div>
                <span className={pnlRate(pos) >= 0 ? 'text-green-400' : 'text-red-400'}>
                  {fmtPct(pnlRate(pos))}
                </span>
              </div>

              {/* 名稱 */}
              <p className="text-gray-400 truncate mb-1">{pos.name}</p>

              {/* 數量 / 均價 / 現價 / 市值 */}
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
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
