import type { AssetsResponse } from '../../api/types'
import { fmtMoney } from '../../lib/format'

interface CardProps {
  label: string
  value: string
  sub?: string
  accent?: boolean
}

function Card({ label, value, sub, accent }: CardProps) {
  return (
    <div className={`rounded-xl p-4 flex flex-col gap-1 ${accent ? 'bg-blue-900/40 border border-blue-700/50' : 'bg-gray-800'}`}>
      <p className="text-xs text-gray-400 tracking-wide">{label}</p>
      <p className={`text-2xl font-semibold tabular-nums ${accent ? 'text-blue-300' : 'text-gray-100'}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-gray-500">{sub}</p>}
    </div>
  )
}

interface Props {
  data: AssetsResponse | null
  loading: boolean
}

export default function AssetCards({ data, loading }: Props) {
  const blank = '--'
  const v = (n: number | undefined) => n === undefined ? blank : fmtMoney(n)
  const sign = (n: number) => n >= 0 ? '+' : ''

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <Card
        label="真實總資產 NAV"
        value={loading ? '載入中…' : (data ? `$${v(data.nav)}` : blank)}
        accent
      />
      <Card
        label="現金餘額"
        value={data ? `$${v(data.cash)}` : blank}
      />
      <Card
        label="現股市值"
        value={data ? `$${v(data.stock_value)}` : blank}
        sub={
          data && (data.margin_pnl !== 0 || data.short_pnl !== 0)
            ? `融資損益 ${sign(data.margin_pnl)}${fmtMoney(data.margin_pnl)}`
            : undefined
        }
      />
      <Card
        label="待交割款"
        value={data ? `$${v(data.pending_settlement)}` : blank}
        sub={
          data
            ? `T+1: ${fmtMoney(data.pending_t1)}  T+2: ${fmtMoney(data.pending_t2)}`
            : undefined
        }
      />
    </div>
  )
}
