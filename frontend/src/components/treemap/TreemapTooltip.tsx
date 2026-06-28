import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'motion/react'
import { changeColor } from '../../lib/colors'

interface TileData {
  code: string
  name: string
  industry: string
  close: number
  change_price: number
  change_rate: number
  total_volume: number
  total_amount: number
}

interface Props {
  tile: TileData | null
  x: number   // viewport clientX
  y: number   // viewport clientY
}

const W = 200
const H = 172

/** 成交額：億 / 萬 自動換算 */
function fmtAmount(n: number) {
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)} 億`
  if (n >= 1e4) return `${(n / 1e4).toFixed(0)} 萬`
  return n.toLocaleString()
}

/** 成交量：K 張 */
function fmtVol(n: number) {
  return n >= 1000
    ? `${(n / 1000).toFixed(1)}K 張`
    : `${n} 張`
}

function Row({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex justify-between items-baseline gap-2">
      <span className="text-gray-400 text-[10px] whitespace-nowrap">{label}</span>
      <span className={`tabular-nums text-xs font-medium ${color ?? 'text-gray-100'}`}>
        {value}
      </span>
    </div>
  )
}

export default function TreemapTooltip({ tile, x, y }: Props) {
  // 靠近右側或底部時自動翻轉位置
  const left = x + W + 16 > window.innerWidth  ? x - W - 8  : x + 12
  const top  = y + H + 16 > window.innerHeight ? y - H - 8  : y + 12

  return createPortal(
    <AnimatePresence>
      {tile && (
        <motion.div
          key={tile.code}
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.94 }}
          transition={{ duration: 0.1 }}
          style={{ position: 'fixed', left, top, zIndex: 9999, pointerEvents: 'none', width: W }}
          className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl px-3 py-2.5 flex flex-col gap-1.5"
        >
          {/* 代號 + 名稱 */}
          <div className="flex items-baseline gap-1.5 border-b border-gray-700 pb-1.5">
            <span className="font-mono font-bold text-white text-sm">{tile.code}</span>
            <span className="text-gray-400 text-xs truncate">{tile.name}</span>
          </div>

          {/* 產業 */}
          <p className="text-[10px] text-gray-500 -mt-0.5">{tile.industry}</p>

          {/* 行情資料 */}
          <div className="flex flex-col gap-1 mt-0.5">
            <Row
              label="現價"
              value={tile.close > 0 ? tile.close.toFixed(tile.close >= 100 ? 1 : 2) : '--'}
            />
            <Row
              label="漲跌"
              value={`${tile.change_price >= 0 ? '+' : ''}${tile.change_price.toFixed(2)}`}
              color={changeColor(tile.change_rate)}
            />
            <Row
              label="漲跌幅"
              value={`${tile.change_rate >= 0 ? '+' : ''}${tile.change_rate.toFixed(2)}%`}
              color={changeColor(tile.change_rate)}
            />
            <div className="border-t border-gray-800 my-0.5" />
            <Row label="成交量" value={fmtVol(tile.total_volume)} />
            <Row label="成交額" value={fmtAmount(tile.total_amount)} />
          </div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  )
}
