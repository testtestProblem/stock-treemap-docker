import { useState } from 'react'
import { RefreshCw, Download, Wifi } from 'lucide-react'
import ApiStatusBadge from '../status/ApiStatusBadge'
import { api } from '../../api/client'
import type { ApiStatusResponse } from '../../api/types'

interface Props {
  onResetTreemap: () => void
  lastUpdate: string | null
  onRefreshAll: () => void
  apiStatus: {
    data: ApiStatusResponse | null
    loading: boolean
    refresh: () => void
  }
}

export default function Header({
  onResetTreemap,
  lastUpdate,
  onRefreshAll,
  apiStatus,
}: Props) {
  const [reconnecting, setReconnecting] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null)

  const showToast = (msg: string, ok: boolean) => {
    setToast({ msg, ok })
    setTimeout(() => setToast(null), 3000)
  }

  const handleReconnect = async () => {
    setReconnecting(true)
    try {
      const res = await api.reconnect()
      apiStatus.refresh()
      showToast(res.message, res.connected)
    } catch (e) {
      showToast(e instanceof Error ? e.message : '重新連線失敗', false)
    } finally {
      setReconnecting(false)
    }
  }

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const blob = await api.exportDb()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'app.db'
      a.click()
      URL.revokeObjectURL(url)
      showToast('資料庫下載完成', true)
    } catch (e) {
      showToast(e instanceof Error ? e.message : '下載失敗', false)
    } finally {
      setDownloading(false)
    }
  }

  const disconnected = apiStatus.data?.connected === false

  return (
    <>
      <header
        className={`flex items-center justify-between flex-wrap gap-2 rounded-lg px-3 py-2 transition-colors ${
          disconnected ? 'bg-red-900/40' : ''
        }`}
      >
        {/* 左側：標題 + API 狀態 */}
        <div className="flex items-center gap-3 flex-wrap">
          <span
            className="text-lg font-bold tracking-wide text-white cursor-pointer hover:text-blue-300 transition-colors"
            title="點擊重設 Treemap 視角"
            onClick={onResetTreemap}
          >
            台股 Treemap Dashboard
          </span>
          <ApiStatusBadge status={apiStatus.data} loading={apiStatus.loading} />
        </div>

        {/* 右側：操作按鈕 */}
        <div className="flex items-center gap-3 text-xs text-gray-500 flex-wrap">
          {lastUpdate && <span>最後更新 {lastUpdate}</span>}

          <button
            onClick={handleReconnect}
            disabled={reconnecting}
            className="flex items-center gap-1 text-gray-400 hover:text-gray-200 transition-colors disabled:opacity-50"
            title="手動重新登入 Shioaji API"
          >
            <Wifi size={12} className={reconnecting ? 'animate-spin' : ''} />
            {reconnecting ? '連線中…' : '重新連線'}
          </button>

          <button
            onClick={onRefreshAll}
            className="flex items-center gap-1 text-gray-400 hover:text-gray-200 transition-colors"
          >
            <RefreshCw size={12} />
            重新整理
          </button>

          <button
            onClick={handleDownload}
            disabled={downloading}
            className="flex items-center gap-1 text-gray-400 hover:text-gray-200 transition-colors disabled:opacity-50"
            title="下載 SQLite 資料庫至本地"
          >
            <Download size={12} />
            {downloading ? '下載中…' : '下載'}
          </button>
        </div>
      </header>

      {/* Toast 提示 */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-2 rounded-lg text-sm shadow-lg ${
            toast.ok
              ? 'bg-green-800 text-green-100 border border-green-600'
              : 'bg-red-800 text-red-100 border border-red-600'
          }`}
        >
          {toast.msg}
        </div>
      )}
    </>
  )
}
