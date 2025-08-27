import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { GraduationCap, Users } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl font-bold text-gray-900 mb-4">
            Duotopia
          </h1>
          <p className="text-2xl text-gray-600 mb-12">
            AI 驅動的多元智能英語學習平台
          </p>
          
          <div className="grid md:grid-cols-2 gap-8 max-w-2xl mx-auto">
            {/* Teacher Card */}
            <div className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow">
              <GraduationCap className="w-16 h-16 mx-auto mb-4 text-blue-600" />
              <h2 className="text-2xl font-semibold mb-4">我是教師</h2>
              <p className="text-gray-600 mb-6">
                管理班級、建立課程、派發作業
              </p>
              <div className="space-y-3">
                <Link to="/teacher/login" className="block">
                  <Button className="w-full">
                    教師登入
                  </Button>
                </Link>
                <Link to="/teacher/register" className="block">
                  <Button variant="outline" className="w-full">
                    註冊新帳號
                  </Button>
                </Link>
              </div>
            </div>

            {/* Student Card */}
            <div className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow">
              <Users className="w-16 h-16 mx-auto mb-4 text-green-600" />
              <h2 className="text-2xl font-semibold mb-4">我是學生</h2>
              <p className="text-gray-600 mb-6">
                查看作業、練習口說、追蹤進度
              </p>
              <div className="space-y-3">
                <Link to="/student/login" className="block">
                  <Button className="w-full bg-green-600 hover:bg-green-700">
                    學生登入
                  </Button>
                </Link>
                <div className="text-sm text-gray-500">
                  請使用教師提供的帳號密碼
                </div>
              </div>
            </div>
          </div>

          <div className="mt-12 text-sm text-gray-500">
            <p>Demo 教師帳號：demo@duotopia.com / demo123</p>
            <p>Demo 學生密碼：20120101</p>
          </div>
        </div>
      </div>
    </div>
  )
}