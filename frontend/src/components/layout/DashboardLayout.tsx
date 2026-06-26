// 主 Dashboard 版面結構
// 階段 6 將填入實際資料元件
export default function DashboardLayout() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      {/* 頂部標題 */}
      <header className="px-6 py-4 border-b border-gray-800 flex items-center gap-3">
        <span className="text-xl font-bold tracking-wide">台股 Treemap Dashboard</span>
        <span className="text-xs text-gray-500">v0.1 鷹架</span>
      </header>

      {/* 頂部資訊卡片區（階段 6 替換） */}
      <section className="px-6 py-4 grid grid-cols-4 gap-4">
        {['真實總資產', '帳戶餘額', '持倉市值', '待交割款'].map((label) => (
          <div key={label} className="bg-gray-800 rounded-xl p-4">
            <p className="text-xs text-gray-400">{label}</p>
            <p className="text-2xl font-semibold mt-1 text-gray-300">--</p>
          </div>
        ))}
      </section>

      {/* 主內容區 */}
      <div className="flex flex-1 gap-4 px-6 pb-6">
        {/* 左側持倉表（階段 6 替換） */}
        <aside className="w-72 bg-gray-800 rounded-xl p-4 flex-shrink-0">
          <p className="text-sm font-semibold mb-3">持倉列表</p>
          <p className="text-xs text-gray-500">階段 6 實作</p>
        </aside>

        {/* 右側 Treemap（階段 6 替換） */}
        <main className="flex-1 bg-gray-800 rounded-xl p-4 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold">Treemap</p>
            <div className="flex gap-2">
              {['全台股', '自選清單'].map((label) => (
                <button
                  key={label}
                  className="px-3 py-1 text-xs rounded-md bg-gray-700 hover:bg-gray-600 transition-colors"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
            階段 6 實作
          </div>
        </main>
      </div>

      {/* 底部績效圖（階段 6 替換） */}
      <section className="px-6 pb-6">
        <div className="bg-gray-800 rounded-xl p-4">
          <p className="text-sm font-semibold mb-2">資產績效比較</p>
          <div className="h-40 flex items-center justify-center text-gray-500 text-sm">
            階段 6 實作
          </div>
        </div>
      </section>
    </div>
  )
}
