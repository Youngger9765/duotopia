import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Home, Users, LogOut, Menu, X, GraduationCap, BookOpen, Building2, ChevronDown, ChevronRight, Plus, UserPlus, School, UserCog, ChevronLeft } from 'lucide-react'
import { useState, useEffect } from 'react'
import { LucideIcon } from 'lucide-react'
import StudentManagementOriginal from './StudentManagement'


interface LegacyNavigationItem {
  path?: string;
  label: string;
  icon?: LucideIcon;
  type?: string;
  subItems?: { label: string; icon: LucideIcon; action: () => void }[];
}
import { RoleSwitcher } from '@/components/RoleSwitcher'
import { useAuth } from '@/contexts/AuthContext'

// 使用完整版本的 StudentManagement 組件
function StudentManagement() {
  return <StudentManagementOriginal />
}
import CourseManagement from './CourseManagement'
import ClassroomManagement from './ClassroomManagement'
import InstitutionManagement from './InstitutionManagement'
import AssignmentManagement from './AssignmentManagement'
import StaffManagement from './StaffManagement'

function TeacherDashboard() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [expandedItems, setExpandedItems] = useState<string[]>([])
  const [roleInfo] = useState<any>({
    current_role_context: 'individual',
    effective_role: 'teacher',
    has_multiple_roles: false
  })
  
  useEffect(() => {
    // fetchRoleInfo() // Disabled for now as API doesn't exist
  }, [])
  
  // const fetchRoleInfo = async () => {
  //   try {
  //     const response = await api.get('/api/role/current')
  //     setRoleInfo(response.data)
  //   } catch (error) {
  //     console.error('Failed to fetch role info:', error)
  //   }
  // }
  
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    navigate('/')
  }

  const toggleExpand = (path: string) => {
    setExpandedItems(prev => 
      prev.includes(path) 
        ? [] // Collapse if already expanded
        : [path] // Only expand this one, collapse others
    )
  }

  // Build navigation items based on role
  const getNavItems = (): LegacyNavigationItem[] => {
    const items: LegacyNavigationItem[] = [
      { path: '/teacher', label: '總覽', icon: Home },
    ]
    
    // Institutional admin items
    if (roleInfo?.current_role_context === 'institutional' || 
        (roleInfo?.effective_role === 'admin' && roleInfo?.current_role_context !== 'individual')) {
      items.push(
        { label: '機構管理', type: 'section' },
        { 
          path: '/teacher/institutions', 
          label: '學校管理', 
          icon: Building2,
          subItems: [
            { label: '新增學校', icon: Plus, action: () => navigate('/teacher/institutions?action=add') },
            { label: '學校列表', icon: Building2, action: () => navigate('/teacher/institutions') }
          ]
        },
        { 
          path: '/teacher/staff', 
          label: '教職員管理', 
          icon: UserCog,
          subItems: [
            { label: '新增教職員', icon: UserPlus, action: () => navigate('/teacher/staff?action=add') },
            { label: '教職員列表', icon: Users, action: () => navigate('/teacher/staff') }
          ]
        }
      )
    }
    
    // Both institutional and individual teacher items
    items.push(
      { label: '教學管理', type: 'section' },
      { 
        path: '/teacher/classrooms', 
        label: '教室管理', 
        icon: Users,
        subItems: [
          { label: '新增教室', icon: Plus, action: () => navigate('/teacher/classrooms?action=add') },
          { label: '教室列表', icon: School, action: () => navigate('/teacher/classrooms') }
        ]
      },
      { 
        path: '/teacher/students', 
        label: '學生管理', 
        icon: GraduationCap,
        subItems: [
          { label: '新增學生', icon: UserPlus, action: () => navigate('/teacher/students?action=add') },
          { label: '學生名單', icon: Users, action: () => navigate('/teacher/students?tab=students') }
        ]
      },
      { 
        path: '/teacher/courses', 
        label: '課程管理', 
        icon: BookOpen,
        subItems: [
          { label: '新增課程', icon: Plus, action: () => navigate('/teacher/courses?action=add') },
          { label: '課程列表', icon: BookOpen, action: () => navigate('/teacher/courses') }
        ]
      }
    )
    
    return items
  }
  
  const navItems = roleInfo ? getNavItems() : []
  
  return (
    <div className="h-screen flex overflow-hidden bg-gray-100">
      {/* Sidebar - Desktop */}
      <aside className={`hidden lg:flex lg:flex-shrink-0 transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-64'}`}>
        <div className="flex flex-col w-full">
          <div className="flex-1 flex flex-col bg-white shadow-sm h-full relative">
            {/* Logo section */}
            <div className="flex items-center justify-between h-16 flex-shrink-0 px-4 bg-white border-b border-gray-200">
              {!sidebarCollapsed && <h1 className="text-xl font-bold">Duotopia 教師平台</h1>}
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
                {navItems.map((item: LegacyNavigationItem, idx: number) => {
                  // Handle section headers
                  if (item.type === 'section') {
                    return (
                      <div key={idx} className="pt-4 pb-2">
                        {!sidebarCollapsed && (
                          <p className="px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                            {item.label}
                          </p>
                        )}
                      </div>
                    )
                  }
                  
                  if (!item.path) return null
                  
                  const Icon = item.icon || Home
                  const isExpanded = expandedItems.includes(item.path)
                  const isActive = location.pathname === item.path || 
                                 location.pathname.startsWith(item.path + '/')
                  
                  return (
                    <div key={item.path}>
                      <div className="relative">
                        {item.subItems ? (
                          <button
                            onClick={() => {
                              if (item.path) {
                                toggleExpand(item.path)
                                navigate(item.path)
                              }
                            }}
                            className={`group w-full flex items-center px-2 py-2 text-sm font-medium rounded-md ${
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
                            {!sidebarCollapsed && (
                              <>
                                <span className="flex-1 text-left">{item.label}</span>
                                {isExpanded ? (
                                  <ChevronDown className="h-4 w-4 ml-auto" />
                                ) : (
                                  <ChevronRight className="h-4 w-4 ml-auto" />
                                )}
                              </>
                            )}
                          </button>
                        ) : (
                          <Link
                            to={item.path || '/teacher'}
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
                        )}
                      </div>
                      
                      {/* Sub-items */}
                      {item.subItems && isExpanded && !sidebarCollapsed && (
                        <div className="ml-8 space-y-1 mt-1">
                          {item.subItems.map((subItem: any, index: number) => {
                            const SubIcon = subItem.icon
                            return (
                              <button
                                key={index}
                                onClick={subItem.action}
                                className="group w-full flex items-center px-2 py-1.5 text-xs font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
                              >
                                <SubIcon className="mr-2 h-4 w-4 text-gray-400 group-hover:text-gray-500" />
                                {subItem.label}
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </div>
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
                          {user?.full_name || '教師'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {user?.email || ''}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {roleInfo?.effective_role === 'admin' ? '管理員' : '教師'}
                        </div>
                      </div>
                    </div>
                    {/* Role Switcher */}
                    {roleInfo?.has_multiple_roles && (
                      <div className="mt-3 mb-3">
                        <RoleSwitcher />
                      </div>
                    )}
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
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
              <h1 className="text-xl font-bold">Duotopia 教師平台</h1>
            </div>
            
            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <nav className="px-2 space-y-1">
                {navItems.map((item: LegacyNavigationItem, idx: number) => {
                  // Handle section headers
                  if (item.type === 'section') {
                    return (
                      <div key={idx} className="pt-4 pb-2">
                        {!sidebarCollapsed && (
                          <p className="px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                            {item.label}
                          </p>
                        )}
                      </div>
                    )
                  }
                  
                  if (!item.path) return null
                  
                  const Icon = item.icon || Home
                  const isExpanded = expandedItems.includes(item.path)
                  const isActive = location.pathname === item.path || 
                                 location.pathname.startsWith(item.path + '/')
                  
                  return (
                    <div key={item.path}>
                      <div className="relative">
                        {item.subItems ? (
                          <button
                            onClick={() => {
                              if (item.path) {
                                toggleExpand(item.path)
                                navigate(item.path)
                              }
                            }}
                            className={`group w-full flex items-center px-2 py-2 text-base font-medium rounded-md ${
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
                            <span className="flex-1 text-left">{item.label}</span>
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4 ml-auto" />
                            ) : (
                              <ChevronRight className="h-4 w-4 ml-auto" />
                            )}
                          </button>
                        ) : (
                          <Link
                            to={item.path || '/teacher'}
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
                        )}
                      </div>
                      
                      {/* Sub-items */}
                      {item.subItems && isExpanded && (
                        <div className="ml-10 space-y-1 mt-1">
                          {item.subItems.map((subItem: any, index: number) => {
                            const SubIcon = subItem.icon
                            return (
                              <button
                                key={index}
                                onClick={() => {
                                  subItem.action()
                                  setSidebarOpen(false)
                                }}
                                className="group w-full flex items-center px-2 py-1.5 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
                              >
                                <SubIcon className="mr-2 h-4 w-4 text-gray-400 group-hover:text-gray-500" />
                                {subItem.label}
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </div>
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
                      {user?.full_name || '教師'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {user?.email || ''}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {roleInfo?.effective_role === 'admin' ? '管理員' : '教師'}
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
              <h1 className="text-xl font-bold">Duotopia 教師平台</h1>
              <div className="w-10" /> {/* Spacer for centering */}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto bg-gray-100">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <Routes>
                <Route path="/" element={<TeacherOverview />} />
                <Route path="/students" element={<StudentManagement />} />
                <Route path="/classrooms" element={<ClassroomManagement />} />
                <Route path="/courses" element={<CourseManagement />} />
                <Route path="/institutions" element={<InstitutionManagement />} />
                <Route path="/assignments" element={<AssignmentManagement />} />
                <Route path="/staff" element={<StaffManagement />} />
              </Routes>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

function TeacherOverview() {
  const { user } = useAuth()
  
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">歡迎回來，{user?.full_name || '老師'}！</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">總學生數</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">48</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">管理班級</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">2</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">待批改作業</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">12</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">本週完成率</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">87%</dd>
          </div>
        </div>
      </div>
      
      <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">最新提交的作業</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-sm">
                  <p className="font-medium text-gray-900">陳小明 - Lesson 3 Speaking</p>
                  <p className="text-gray-500">六年一班 · 5分鐘前</p>
                </div>
                <Button size="sm" variant="outline">批改</Button>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm">
                  <p className="font-medium text-gray-900">林小華 - Reading Test</p>
                  <p className="text-gray-500">六年二班 · 15分鐘前</p>
                </div>
                <Button size="sm" variant="outline">批改</Button>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">班級表現</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">六年一班</span>
                  <span className="text-gray-900 font-medium">92%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: '92%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">六年二班</span>
                  <span className="text-gray-900 font-medium">78%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '78%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TeacherDashboard