import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import type { PerformanceResponse } from '../../api/types'

interface ChartPoint {
  date: string
  nav: number
  p0050: number
  p2330: number
}

interface Props {
  data: PerformanceResponse | null
  loading: boolean
}

function CustomTooltip({ active, payload, label }: {
  active?: boolean
  payload?: { name: string; value: number; color: string }[]
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-2 text-xs shadow-lg">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}：{p.value >= 0 ? '+' : ''}{p.value.toFixed(2)}%
        </p>
      ))}
    </div>
  )
}

export default function PerformanceChart({ data, loading }: Props) {
  if (loading && !data) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500 text-sm">
        載入中…
      </div>
    )
  }

  if (!data || data.record_count === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500 text-sm">
        尚無歷史資料（每日 15:40 自動記錄）
      </div>
    )
  }

  const chartData: ChartPoint[] = data.nav.dates.map((date, i) => ({
    date: date.slice(5),   // "MM-DD"
    nav: data.nav.values[i],
    p0050: data.price_0050.values[i],
    p2330: data.price_2330.values[i],
  }))

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 10, fill: '#6b7280' }}
          tickLine={false}
          axisLine={{ stroke: '#374151' }}
        />
        <YAxis
          tickFormatter={v => `${v.toFixed(1)}%`}
          tick={{ fontSize: 10, fill: '#6b7280' }}
          tickLine={false}
          axisLine={false}
          width={48}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
          formatter={(value) => (
            <span style={{ color: '#9ca3af' }}>{value}</span>
          )}
        />
        <Line
          type="monotone" dataKey="nav" name="我的資產"
          stroke="#60a5fa" strokeWidth={2} dot={false} activeDot={{ r: 3 }}
        />
        <Line
          type="monotone" dataKey="p0050" name="0050"
          stroke="#34d399" strokeWidth={1.5} dot={false} activeDot={{ r: 3 }}
        />
        <Line
          type="monotone" dataKey="p2330" name="2330"
          stroke="#f59e0b" strokeWidth={1.5} dot={false} activeDot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
