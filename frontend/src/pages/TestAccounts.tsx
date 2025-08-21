import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export default function TestAccounts() {
  const navigate = useNavigate()

  const copyBoth = (email: string, password: string) => {
    // 複製帳號密碼到剪貼簿
    const text = `帳號: ${email}\n密碼: ${password}`
    navigator.clipboard.writeText(text)
    
    // 跳轉到登入頁面
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">測試帳號</h1>
          <p className="text-gray-600">點擊按鈕複製帳號密碼，然後貼到登入頁面</p>
        </div>

        <div className="space-y-4">
          <div className="bg-white rounded-lg p-6 shadow">
            <h2 className="text-xl font-bold mb-2">1. 個體戶教師</h2>
            <p className="text-gray-600 mb-4">只能管理個人教室、課程、學生</p>
            <div className="bg-gray-50 p-3 rounded mb-4 font-mono text-sm">
              <div>帳號: individual@test.com</div>
              <div>密碼: test123</div>
            </div>
            <Button 
              className="w-full"
              onClick={() => copyBoth('individual@test.com', 'test123')}
            >
              複製帳號密碼並前往登入
            </Button>
          </div>

          <div className="bg-white rounded-lg p-6 shadow">
            <h2 className="text-xl font-bold mb-2">2. 機構管理員</h2>
            <p className="text-gray-600 mb-4">可管理學校、教職員、所有教學資源</p>
            <div className="bg-gray-50 p-3 rounded mb-4 font-mono text-sm">
              <div>帳號: institutional@test.com</div>
              <div>密碼: test123</div>
            </div>
            <Button 
              className="w-full"
              onClick={() => copyBoth('institutional@test.com', 'test123')}
            >
              複製帳號密碼並前往登入
            </Button>
          </div>

          <div className="bg-white rounded-lg p-6 shadow">
            <h2 className="text-xl font-bold mb-2">3. 混合型使用者</h2>
            <p className="text-gray-600 mb-4">可在個體戶和機構管理員角色間切換</p>
            <div className="bg-gray-50 p-3 rounded mb-4 font-mono text-sm">
              <div>帳號: hybrid@test.com</div>
              <div>密碼: test123</div>
            </div>
            <Button 
              className="w-full"
              onClick={() => copyBoth('hybrid@test.com', 'test123')}
            >
              複製帳號密碼並前往登入
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}