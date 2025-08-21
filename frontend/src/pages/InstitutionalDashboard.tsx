import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { Home, Users, Building2, GraduationCap, BookOpen, LogOut, Menu, X, ChevronLeft } from 'lucide-react'
import { useState, useEffect } from 'react'
import { RoleSwitcher } from '@/components/RoleSwitcher'
import { api } from '@/lib/api'

// 機構管理頁面組件
import InstitutionalSchools from './institutional/Schools'
import InstitutionalClassrooms from './institutional/Classrooms'
import InstitutionalStudents from './institutional/Students'
import InstitutionalCourses from './institutional/Courses'

function InstitutionalDashboard() {
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  
  useEffect(() => {
    fetchUserInfo()
  }, [])
  
  const fetchUserInfo = async () => {
    try {
      const response = await api.get('/api/role/current')
      setUserInfo(response.data)
      
      // 確認是機構管理員
      if (response.data.current_role_context !== 'institutional' && 
          response.data.effective_role !== 'admin') {
        navigate('/teacher')
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error)
    }
  }
  
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    navigate('/')
  }

  const navItems = [
    { path: '/institutional', label: '總覽', icon: Home },
    { path: '/institutional/schools', label: '學校管理', icon: Building2 },
    { path: '/institutional/classrooms', label: '教室管理', icon: Users },
    { path: '/institutional/students', label: '學生管理', icon: GraduationCap },
    { path: '/institutional/courses', label: '課程管理', icon: BookOpen },
  ]
  
  return (
    <div className="h-screen flex overflow-hidden bg-gray-100">
      {/* Sidebar - Desktop */}
      <aside className={`hidden lg:flex lg:flex-shrink-0 transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-64'}`}>
        <div className="flex flex-col w-full">
          <div className="flex-1 flex flex-col bg-white shadow-sm h-full">
            {/* Logo section */}
            <div className="flex items-center justify-between h-16 flex-shrink-0 px-4 bg-white border-b border-gray-200">
              {!sidebarCollapsed && <h1 className="text-xl font-bold">機構管理系統</h1>}
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className={`p-1.5 hover:bg-gray-100 rounded-md transition-transform ${
                  sidebarCollapsed ? 'rotate-180' : ''
                }`}
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
            </div>
            
            {/* Navigation */}
            <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
              <nav className="flex-1 px-2 space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                        isActive
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      <Icon
                        className={`${sidebarCollapsed ? '' : 'mr-3'} h-5 w-5 ${
                          isActive
                            ? 'text-blue-700'
                            : 'text-gray-400 group-hover:text-gray-500'
                        }`}
                      />
                      {!sidebarCollapsed && item.label}
                    </Link>
                  )
                })}
              </nav>
            </div>
            
            {/* User info section */}
            <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
              <div className="flex-shrink-0 w-full">
                {!sidebarCollapsed ? (
                  <>
                    <div className="flex items-center">
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">
                          {userInfo?.primary_role === 'admin' ? '管理員' : '教師'}
                        </div>
                        <div className="text-xs text-gray-500">
                          機構管理模式
                        </div>
                      </div>
                    </div>
                    {/* Role Switcher */}
                    {userInfo?.has_multiple_roles && (
                      <div className="mt-3 mb-3">
                        <RoleSwitcher />
                      </div>
                    )}
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      <LogOut className="mr-2 h-4 w-4" />
                      登出
                    </button>
                  </>
                ) : (
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center justify-center p-2 text-gray-700 hover:bg-gray-50 rounded-md"
                  >
                    <LogOut className="h-5 w-5" />
                  </button>
                )}
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
              <h1 className="text-xl font-bold">機構管理系統</h1>
            </div>
            
            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <nav className="px-2 space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={`group flex items-center px-2 py-2 text-base font-medium rounded-md ${
                        isActive
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      <Icon
                        className={`mr-4 h-6 w-6 ${
                          isActive
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
                className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              >
                <Menu className="h-6 w-6" />
              </button>
              <h1 className="text-xl font-bold">機構管理系統</h1>
              <div className="w-10" />
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto bg-gray-100">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <Routes>
                <Route path="/" element={<InstitutionalOverview />} />
                <Route path="/schools" element={<InstitutionalSchools />} />
                <Route path="/classrooms" element={<InstitutionalClassrooms />} />
                <Route path="/students" element={<InstitutionalStudents />} />
                <Route path="/courses" element={<InstitutionalCourses />} />
              </Routes>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

function InstitutionalOverview() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">機構管理總覽</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">管理學校</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">3</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">總教室數</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">24</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">總學生數</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">486</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">活躍課程</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">18</dd>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InstitutionalDashboard