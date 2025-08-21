import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: email,
          password: password,
        }),
      })
      
      if (!response.ok) {
        alert('登入失敗：電子郵件或密碼錯誤')
        return
      }
      
      const data = await response.json()
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('userRole', data.user_type || 'teacher')
      localStorage.setItem('userId', data.user_id)
      
      // Check if it's a dual system user
      if (data.is_individual_teacher && data.is_institutional_admin) {
        // User has both roles, redirect to role selection or default
        navigate('/teacher')
      } else if (data.is_individual_teacher) {
        // Individual teacher only
        navigate('/individual')
      } else if (data.is_institutional_admin || data.user_type === 'admin') {
        // Institutional admin
        navigate('/institutional')
      } else {
        // Regular teacher (old system)
        navigate('/teacher')
      }
    } catch (error) {
      alert('登入失敗：請檢查網路連線')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            教師登入
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            或{' '}
            <Link to="/student-login" className="font-medium text-blue-600 hover:text-blue-500">
              學生登入
            </Link>
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                密碼
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="密碼"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div>
            <Button type="submit" className="w-full">
              登入
            </Button>
          </div>
          
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 text-gray-500">或使用測試帳號</span>
            </div>
          </div>
          
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => {
                setEmail('teacher@individual.com')
                setPassword('test123')
              }}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              個體戶教師
            </button>
            
            <button
              type="button"
              onClick={() => {
                setEmail('admin@institution.com')
                setPassword('test123')
              }}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              機構管理員
            </button>
            
            <button
              type="button"
              onClick={() => {
                setEmail('hybrid@test.com')
                setPassword('test123')
              }}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              混合型使用者
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default LoginPage