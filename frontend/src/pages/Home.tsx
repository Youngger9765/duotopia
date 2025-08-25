import { useState, useEffect } from 'react'

function Home() {
  const [apiStatus, setApiStatus] = useState<string>('checking...')

  useEffect(() => {
    // 測試 API 連線
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setApiStatus(data.status))
      .catch(() => setApiStatus('offline'))
  }, [])

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Duotopia
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          英語學習平台
        </p>
        
        <div className="bg-white rounded-lg shadow-md p-6 max-w-md mx-auto">
          <h2 className="text-lg font-semibold mb-4">系統狀態</h2>
          <div className="flex justify-between items-center">
            <span>後端 API:</span>
            <span className={`px-2 py-1 rounded text-sm ${
              apiStatus === 'healthy' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {apiStatus}
            </span>
          </div>
        </div>

        <div className="mt-8 space-x-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg">
            教師登入
          </button>
          <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg">
            學生登入
          </button>
        </div>
      </div>
    </div>
  )
}

export default Home