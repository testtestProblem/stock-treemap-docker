import type { ApiStatusResponse } from '../../api/types'

interface Props {
  status: ApiStatusResponse | null
  loading?: boolean
}

export default function ApiStatusBadge({ status, loading }: Props) {
  if (loading && !status) {
    return (
      <span className="text-xs text-gray-500 animate-pulse">
        永豐金 API: —
      </span>
    )
  }

  const connected = status?.connected ?? false
  const usagePct = status?.usage_pct ?? 0

  const usageColor =
    usagePct >= 90 ? 'text-red-400' :
    usagePct >= 70 ? 'text-yellow-400' :
    'text-gray-300'

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className={usageColor} title="最近 5 秒 API 用量（限流 50 次/5s）">
        永豐金 API: {usagePct.toFixed(0)}%
      </span>
      <span
        className="flex items-center gap-1"
        title={connected ? '已連線' : '未登入'}
      >
        <span
          className={`inline-block w-2 h-2 rounded-full ${
            connected ? 'bg-green-500' : 'bg-red-500'
          }`}
        />
        <span className={connected ? 'text-green-400' : 'text-red-400'}>
          {connected ? '已連線' : '未登入'}
        </span>
      </span>
    </div>
  )
}
