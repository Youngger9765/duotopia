import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-800 mb-4">
            歡迎來到 Duotopia
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            AI 驅動的多元智能英語學習平台
          </p>
          
          <div className="flex gap-4 justify-center">
            <Link to="/student-login">
              <Button size="lg" className="px-8 py-6 text-lg">
                學生登入
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="px-8 py-6 text-lg">
                教師登入
              </Button>
            </Link>
          </div>
        </div>
        
        <div className="mt-16 grid md:grid-cols-3 gap-8">
          <div className="text-center p-6">
            <h3 className="text-xl font-semibold mb-2">個人化學習</h3>
            <p className="text-gray-600">
              AI 根據每位學生的學習進度和能力，提供客製化的學習內容
            </p>
          </div>
          <div className="text-center p-6">
            <h3 className="text-xl font-semibold mb-2">互動式練習</h3>
            <p className="text-gray-600">
              多樣化的練習活動，包含聽說讀寫全方位訓練
            </p>
          </div>
          <div className="text-center p-6">
            <h3 className="text-xl font-semibold mb-2">即時回饋</h3>
            <p className="text-gray-600">
              AI 即時評估學生表現，提供建設性的回饋和改進建議
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage