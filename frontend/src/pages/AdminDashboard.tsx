import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Home, GraduationCap, BookOpen, Building2, LogOut, Menu, X, UserCheck, Settings } from 'lucide-react'
import { useState } from 'react'
import InstitutionManagement from './InstitutionManagement'
import TeacherManagement from './TeacherManagement'
import StudentManagement from './StudentManagement'
import CourseManagement from './CourseManagement'

function AdminDashboard() {
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    navigate('/')
  }

  const navItems = [
    { path: '/admin', label: '總覽', icon: Home },
    { path: '/admin/institution', label: '機構管理', icon: Building2 },
    { path: '/admin/teachers', label: '教師名冊', icon: UserCheck },
    { path: '/admin/students', label: '學生名單', icon: GraduationCap },
    { path: '/admin/courses', label: '機構內課程', icon: BookOpen },
    { path: '/admin/settings', label: '系統設定', icon: Settings },
  ]
  
  return (
    <div className="h-screen flex overflow-hidden bg-gray-100">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex lg:flex-shrink-0">
        <div className="flex flex-col w-64">
          <div className="flex-1 flex flex-col bg-white shadow-sm h-full">
            {/* Logo section */}
            <div className="flex items-center h-16 flex-shrink-0 px-4 bg-white border-b border-gray-200">
              <h1 className="text-xl font-bold">機構管理系統</h1>
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
                      系統管理員
                    </div>
                    <div className="text-xs text-gray-500">
                      admin@duotopia.com
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      機構管理員
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
              <h1 className="text-xl font-bold">機構管理系統</h1>
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
                      系統管理員
                    </div>
                    <div className="text-xs text-gray-500">
                      admin@duotopia.com
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      機構管理員
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
              <h1 className="text-xl font-bold">機構管理系統</h1>
              <div className="w-10" /> {/* Spacer for centering */}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto bg-gray-100">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <Routes>
                <Route path="/" element={<AdminOverview />} />
                <Route path="/institution" element={<InstitutionManagement />} />
                <Route path="/teachers" element={<TeacherManagement />} />
                <Route path="/students" element={<StudentManagement />} />
                <Route path="/courses" element={<CourseManagement />} />
                <Route path="/settings" element={<SystemSettings />} />
              </Routes>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

function AdminOverview() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">機構總覽</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">機構數量</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">3</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">教師總數</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">24</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">學生總數</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">486</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">活躍課程</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">45</dd>
          </div>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">機構活動統計</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">台北分校</span>
                  <span className="text-gray-900 font-medium">245 位學生</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '50%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">新竹分校</span>
                  <span className="text-gray-900 font-medium">156 位學生</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: '32%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">台中分校</span>
                  <span className="text-gray-900 font-medium">85 位學生</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-yellow-600 h-2 rounded-full" style={{ width: '18%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">最新加入教師</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-sm">
                  <p className="font-medium text-gray-900">陳老師</p>
                  <p className="text-gray-500">台北分校 · 2 天前</p>
                </div>
                <Button size="sm" variant="outline">查看</Button>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm">
                  <p className="font-medium text-gray-900">林老師</p>
                  <p className="text-gray-500">新竹分校 · 5 天前</p>
                </div>
                <Button size="sm" variant="outline">查看</Button>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm">
                  <p className="font-medium text-gray-900">黃老師</p>
                  <p className="text-gray-500">台中分校 · 1 週前</p>
                </div>
                <Button size="sm" variant="outline">查看</Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function SystemSettings() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">系統設定</h2>
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center text-gray-500">
          <Settings className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2">系統設定功能開發中</p>
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard