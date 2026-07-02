import { motion, AnimatePresence } from 'motion/react'
import type { AssetsResponse } from '../../api/types'
import { fmtMoney, fmtPct } from '../../lib/format'
import { pnlClass } from '../../lib/colors'

// ── Skeleton ──────────────────────────────────────────────────────────────────

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

// ── 通用卡片 ──────────────────────────────────────────────────────────────────

interface SubLine {
  label: string
  value: string
  valueClass?: string
}

interface CardProps {
  label: string
  main: string
  mainClass?: string
  subs?: SubLine[]
  accent?: boolean
  index: number
}

function Card({ label, main, mainClass, subs, accent, index }: CardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.07, ease: 'easeOut' }}
      className={`rounded-xl p-4 flex flex-col gap-1 ${
        accent ? 'bg-blue-900/40 border border-blue-700/50' : 'bg-gray-800'
      }`}
    >
      <p className="text-xs text-gray-400 tracking-wide">{label}</p>
      <p className={`text-2xl font-semibold tabular-nums ${mainClass ?? (accent ? 'text-blue-300' : 'text-gray-100')}`}>
        {main}
      </p>
      {subs?.map(s => (
        <p key={s.label} className="text-xs text-gray-500">
          {s.label}
          <span className={`ml-1 ${s.valueClass ?? ''}`}>{s.value}</span>
        </p>
      ))}
    </motion.div>
  )
}

// ── 主元件 ────────────────────────────────────────────────────────────────────

interface Props {
  data: AssetsResponse | null
  loading: boolean
  error?: string | null
}

function optSub(label: string, n: number | null | undefined, fmt: (v: number) => string): SubLine | undefined {
  if (n == null) return undefined
  return { label, value: fmt(n), valueClass: pnlClass(n) }
}

export default function AssetCards({ data, loading, error }: Props) {
  const $ = (n: number) => `$${fmtMoney(n)}`
  const sign = (n: number) => (n >= 0 ? '+' : '')

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      <AnimatePresence mode="wait" initial={false}>
        {!data ? (
          <>
            <SkeletonCard key="sk-0" accent />
            <SkeletonCard key="sk-1" />
            <SkeletonCard key="sk-2" />
            <SkeletonCard key="sk-3" />
            <SkeletonCard key="sk-4" />
          </>
        ) : (
          <>
            {/* 卡片 1：NAV */}
            <Card
              index={0}
              accent
              label="真實總資產 NAV"
              main={$(data.nav)}
              subs={[
                optSub('當日損益', data.day_pnl, v => `${sign(v)}${fmtMoney(v)}`),
                optSub('當日損益%', data.day_pnl_rate, v => fmtPct(v)),
              ].filter(Boolean) as SubLine[]}
            />

            {/* 卡片 2：現金 */}
            <Card
              index={1}
              label="現金餘額"
              main={$(data.cash)}
              subs={[
                { label: '融資損益', value: `${sign(data.margin_pnl)}${fmtMoney(data.margin_pnl)}`, valueClass: pnlClass(data.margin_pnl) },
                { label: '融券損益', value: `${sign(data.short_pnl)}${fmtMoney(data.short_pnl)}`,   valueClass: pnlClass(data.short_pnl) },
              ].filter(s => s.value !== '+0' && s.value !== '0')}
            />

            {/* 卡片 3：現股市值 */}
            <Card
              index={2}
              label="現股市值"
              main={$(data.stock_value)}
              subs={[
                optSub('融資市值', data.margin_value, fmtMoney),
                optSub('融券市值', data.short_value, fmtMoney),
              ].filter(Boolean) as SubLine[]}
            />

            {/* 卡片 4：未實現損益 */}
            <Card
              index={3}
              label="未實現損益"
              main={
                data.unrealized_pnl != null
                  ? `${sign(data.unrealized_pnl)}${fmtMoney(data.unrealized_pnl)}`
                  : '—'
              }
              mainClass={
                data.unrealized_pnl != null
                  ? pnlClass(data.unrealized_pnl)
                  : 'text-gray-500'
              }
              subs={[
                optSub('今日實現', data.realized_pnl_today, v => `${sign(v)}${fmtMoney(v)}`),
              ].filter(Boolean) as SubLine[]}
            />

            {/* 卡片 5：待交割款 */}
            <Card
              index={4}
              label="待交割款"
              main={$(data.pending_settlement)}
              subs={[
                { label: 'T+1', value: fmtMoney(data.pending_t1), valueClass: pnlClass(data.pending_t1) },
                { label: 'T+2', value: fmtMoney(data.pending_t2), valueClass: pnlClass(data.pending_t2) },
              ]}
            />
          </>
        )}
      </AnimatePresence>

      {/* 錯誤橫幅 */}
      {error && !loading && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="col-span-2 md:col-span-3 lg:col-span-5 text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-1.5"
        >
          帳務 API 錯誤：{error}
        </motion.p>
      )}
    </div>
  )
}
