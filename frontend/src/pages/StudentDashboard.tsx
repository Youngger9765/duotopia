import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { BookOpen, FileText, TrendingUp, LogOut, Menu, X, Settings, Users } from 'lucide-react'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { Toaster } from '@/components/ui/toaster'

function StudentDashboard() {
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [teacherInfo, setTeacherInfo] = useState<any>(null)
  const { toast } = useToast()
  
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    localStorage.removeItem('studentInfo')
    navigate('/')
  }

  // 獲取當前老師資訊
  useEffect(() => {
    const fetchTeacherInfo = async () => {
      const studentInfo = JSON.parse(localStorage.getItem('studentInfo') || '{}')
      if (studentInfo.teacher_id) {
        try {
          const response = await api.get(`/api/student-login/teachers/${studentInfo.teacher_id}/info`)
          setTeacherInfo(response.data)
        } catch (error) {
          console.error('無法獲取老師資訊:', error)
        }
      }
    }
    fetchTeacherInfo()
  }, [])

  const navItems = [
    { path: '/student', label: '我的課程', icon: BookOpen },
    { path: '/student/assignments', label: '作業', icon: FileText },
    { path: '/student/progress', label: '學習進度', icon: TrendingUp },
    { path: '/student/settings', label: '設定', icon: Settings },
  ]
  
  return (
    <div className="h-screen flex overflow-hidden bg-gray-100">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex lg:flex-shrink-0">
        <div className="flex flex-col w-64">
          <div className="flex-1 flex flex-col bg-white shadow-sm h-full">
            {/* Logo section */}
            <div className="flex items-center h-16 flex-shrink-0 px-4 bg-white border-b border-gray-200">
              <h1 className="text-xl font-bold">Duotopia 學習平台</h1>
            </div>
            
            {/* Navigation */}
            <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
              <nav className="flex-1 px-2 space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                        location.pathname === item.path
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      <Icon
                        className={`mr-3 h-5 w-5 ${
                          location.pathname === item.path
                            ? 'text-blue-700'
                            : 'text-gray-400 group-hover:text-gray-500'
                        }`}
                      />
                      {item.label}
                    </Link>
                  )
                })}
              </nav>
            </div>
            
            {/* User info section */}
            <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
              <div className="flex-shrink-0 w-full">
                <div className="flex items-center">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {JSON.parse(localStorage.getItem('studentInfo') || '{}').name || '學生'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {JSON.parse(localStorage.getItem('studentInfo') || '{}').email || ''}
                    </div>
                    <div className="text-xs text-gray-400 mt-1 flex items-center">
                      <Users className="h-3 w-3 mr-1" />
                      老師：{teacherInfo?.full_name || '載入中...'}
                    </div>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="mt-3 w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  登出
                </button>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 flex z-40 lg:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white h-full">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button
                onClick={() => setSidebarOpen(false)}
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              >
                <X className="h-6 w-6 text-white" />
              </button>
            </div>
            
            {/* Mobile Logo */}
            <div className="flex items-center h-16 flex-shrink-0 px-4 bg-white border-b border-gray-200">
              <h1 className="text-xl font-bold">Duotopia 學習平台</h1>
            </div>
            
            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <nav className="px-2 space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={`group flex items-center px-2 py-2 text-base font-medium rounded-md ${
                        location.pathname === item.path
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      <Icon
                        className={`mr-4 h-6 w-6 ${
                          location.pathname === item.path
                            ? 'text-blue-700'
                            : 'text-gray-400 group-hover:text-gray-500'
                        }`}
                      />
                      {item.label}
                    </Link>
                  )
                })}
              </nav>
            </div>
            
            {/* User info section - Mobile */}
            <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
              <div className="flex-shrink-0 w-full">
                <div className="flex items-center">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {JSON.parse(localStorage.getItem('studentInfo') || '{}').name || '學生'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {JSON.parse(localStorage.getItem('studentInfo') || '{}').email || ''}
                    </div>
                    <div className="text-xs text-gray-400 mt-1 flex items-center">
                      <Users className="h-3 w-3 mr-1" />
                      老師：{teacherInfo?.full_name || '載入中...'}
                    </div>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="mt-3 w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  登出
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile header */}
        <header className="lg:hidden bg-white shadow-sm">
          <div className="px-4 sm:px-6">
            <div className="flex items-center justify-between h-16">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              >
                <Menu className="h-6 w-6" />
              </button>
              <h1 className="text-xl font-bold">Duotopia 學習平台</h1>
              <div className="w-10" /> {/* Spacer for centering */}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto bg-gray-100">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <Routes>
                <Route path="/" element={<StudentOverview />} />
                <Route path="/assignments" element={<StudentAssignments />} />
                <Route path="/progress" element={<StudentProgress />} />
                <Route path="/settings" element={<StudentSettings toast={toast} />} />
              </Routes>
            </div>
          </div>
        </main>
      </div>
      <Toaster />
    </div>
  )
}

function StudentOverview() {
  const studentInfo = JSON.parse(localStorage.getItem('studentInfo') || '{}')
  
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">歡迎回來，{studentInfo.name}！</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">本週作業</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">3</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">已完成</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">12</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">學習時數</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">24.5</dd>
          </div>
        </div>
      </div>
      
      <div className="mt-8">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">最近的課程</h3>
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            <li className="px-4 py-4 sm:px-6 hover:bg-gray-50 cursor-pointer">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                      <BookOpen className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-900">基礎英語會話</div>
                    <div className="text-sm text-gray-500">下次上課：今天下午 2:00</div>
                  </div>
                </div>
                <div>
                  <Button size="sm">進入課程</Button>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

function StudentAssignments() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">我的作業</h2>
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          <li className="px-4 py-4 sm:px-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">Lesson 3 - Speaking Practice</p>
                <p className="text-sm text-gray-500">截止日期：2024/01/15</p>
              </div>
              <Button size="sm">開始作業</Button>
            </div>
          </li>
          <li className="px-4 py-4 sm:px-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">Reading Comprehension Test</p>
                <p className="text-sm text-gray-500">截止日期：2024/01/18</p>
              </div>
              <Button size="sm">開始作業</Button>
            </div>
          </li>
        </ul>
      </div>
    </div>
  )
}

function StudentProgress() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">學習進度</h2>
      <div className="bg-white shadow rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">口說練習</span>
              <span className="text-gray-900 font-medium">75%</span>
            </div>
            <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: '75%' }}></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">閱讀理解</span>
              <span className="text-gray-900 font-medium">60%</span>
            </div>
            <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: '60%' }}></div>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">聽力練習</span>
              <span className="text-gray-900 font-medium">85%</span>
            </div>
            <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: '85%' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StudentSettings({ toast }: { toast: any }) {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  const navigate = useNavigate()
  
  const studentInfo = JSON.parse(localStorage.getItem('studentInfo') || '{}')

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (newPassword !== confirmPassword) {
      toast({
        title: "錯誤",
        description: "新密碼與確認密碼不相符"
      })
      return
    }
    
    if (newPassword.length < 4) {
      toast({
        title: "錯誤", 
        description: "新密碼至少需要4個字符"
      })
      return
    }
    
    setIsChangingPassword(true)
    
    try {
      await api.post('/api/student-login/change-password', {
        student_id: studentInfo.id,
        current_password: currentPassword,
        new_password: newPassword
      })
      
      toast({
        title: "成功",
        description: "密碼修改成功！"
      })
      
      // 更新本地存儲的學生資訊
      const updatedStudentInfo = { ...studentInfo, is_default_password: false }
      localStorage.setItem('studentInfo', JSON.stringify(updatedStudentInfo))
      
      // 清空表單
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      
    } catch (error: any) {
      toast({
        title: "錯誤",
        description: error.response?.data?.detail || "密碼修改失敗"
      })
    } finally {
      setIsChangingPassword(false)
    }
  }

  const handleSwitchTeacher = () => {
    // 清除登入資訊並導向學生登入頁面
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    localStorage.removeItem('studentInfo')
    navigate('/student-login')
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">設定</h2>
      
      {/* 學生資訊 */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">學生資訊</h3>
        <div className="grid grid-cols-1 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">姓名</label>
            <div className="mt-1 text-sm text-gray-900">{studentInfo.name}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <div className="mt-1 text-sm text-gray-900">{studentInfo.email || '未設定'}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">密碼狀態</label>
            <div className="mt-1">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                studentInfo.is_default_password
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-green-100 text-green-800'
              }`}>
                {studentInfo.is_default_password ? '使用預設密碼' : '已設定自訂密碼'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 密碼修改 */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">修改密碼</h3>
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              當前密碼
            </label>
            <input
              type="password"
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder={studentInfo.is_default_password ? "請輸入您的生日 (YYYYMMDD)" : "請輸入當前密碼"}
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              新密碼
            </label>
            <input
              type="password"
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="至少4個字符"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              確認新密碼
            </label>
            <input
              type="password"
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="再次輸入新密碼"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>
          <Button
            type="submit"
            disabled={isChangingPassword}
            className="w-full"
          >
            {isChangingPassword ? '修改中...' : '修改密碼'}
          </Button>
        </form>
      </div>

      {/* 切換老師 */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">切換老師</h3>
        <p className="text-sm text-gray-600 mb-4">
          如果您需要進入其他老師的教室，請使用此功能。這將會登出當前會話並要求您重新進行學生登入流程。
        </p>
        <Button
          onClick={handleSwitchTeacher}
          variant="outline"
          className="w-full"
        >
          切換到其他老師
        </Button>
      </div>
    </div>
  )
}

export default StudentDashboard