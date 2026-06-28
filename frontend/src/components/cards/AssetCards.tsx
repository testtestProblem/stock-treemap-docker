import { motion, AnimatePresence } from 'motion/react'
import type { AssetsResponse } from '../../api/types'
import { fmtMoney } from '../../lib/format'

function SkeletonBlock({ className = '' }: { className?: string }) {
  return <div className={`bg-gray-700 rounded animate-pulse ${className}`} />
}

function SkeletonCard({ accent = false }: { accent?: boolean }) {
  return (
    <div className={`rounded-xl p-4 flex flex-col gap-2 ${accent ? 'bg-blue-900/40 border border-blue-700/50' : 'bg-gray-800'}`}>
      <SkeletonBlock className="h-3 w-20" />
      <SkeletonBlock className="h-7 w-32" />
      <SkeletonBlock className="h-2.5 w-24 opacity-50" />
    </div>
  )
}

interface CardData {
  label: string
  value: string
  sub?: string
  accent?: boolean
}

function Card({ label, value, sub, accent, index }: CardData & { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.07, ease: 'easeOut' }}
      className={`rounded-xl p-4 flex flex-col gap-1 ${accent ? 'bg-blue-900/40 border border-blue-700/50' : 'bg-gray-800'}`}
    >
      <p className="text-xs text-gray-400 tracking-wide">{label}</p>
      <p className={`text-2xl font-semibold tabular-nums ${accent ? 'text-blue-300' : 'text-gray-100'}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-gray-500">{sub}</p>}
    </motion.div>
  )
}

interface Props {
  data: AssetsResponse | null
  loading: boolean
  error?: string | null
}

export default function AssetCards({ data, loading, error }: Props) {
  const v    = (n: number) => fmtMoney(n)
  const sign = (n: number) => n >= 0 ? '+' : ''

  const cards: CardData[] = data
    ? [
        { label: '真實總資產 NAV', value: `$${v(data.nav)}`, accent: true },
        { label: '現金餘額',       value: `$${v(data.cash)}` },
        {
          label: '現股市值',
          value: `$${v(data.stock_value)}`,
          sub: (data.margin_pnl !== 0 || data.short_pnl !== 0)
            ? `融資損益 ${sign(data.margin_pnl)}${v(data.margin_pnl)}`
            : undefined,
        },
        {
          label: '待交割款',
          value: `$${v(data.pending_settlement)}`,
          sub: `T+1: ${v(data.pending_t1)}  T+2: ${v(data.pending_t2)}`,
        },
      ]
    : []

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <AnimatePresence mode="wait" initial={false}>
        {!data ? (
          /* Skeleton */
          <>
            <SkeletonCard key="sk-0" accent />
            <SkeletonCard key="sk-1" />
            <SkeletonCard key="sk-2" />
            <SkeletonCard key="sk-3" />
          </>
        ) : (
          /* 真實資料，帶 stagger 進場 */
          <>
            {cards.map((c, i) => (
              <Card key={c.label} {...c} index={i} />
            ))}
          </>
        )}
      </AnimatePresence>

      {/* 錯誤橫幅 */}
      {error && !loading && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="col-span-2 md:col-span-4 text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-1.5"
        >
          帳務 API 錯誤：{error}
        </motion.p>
      )}
    </div>
  )
}
