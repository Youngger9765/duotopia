import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button'

function TeacherDashboard() {
  const location = useLocation()
  
  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold">Duotopia 教師平台</h1>
              </div>
              <div className="ml-6 flex space-x-8">
                <Link
                  to="/teacher"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    location.pathname === '/teacher' 
                      ? 'border-blue-500 text-gray-900' 
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  總覽
                </Link>
                <Link
                  to="/teacher/classes"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    location.pathname === '/teacher/classes' 
                      ? 'border-blue-500 text-gray-900' 
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  班級管理
                </Link>
                <Link
                  to="/teacher/assignments"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    location.pathname === '/teacher/assignments' 
                      ? 'border-blue-500 text-gray-900' 
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  作業管理
                </Link>
              </div>
            </div>
            <div className="flex items-center">
              <Button variant="outline" size="sm">
                登出
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<TeacherOverview />} />
          <Route path="/classes" element={<div>班級管理頁面</div>} />
          <Route path="/assignments" element={<div>作業管理頁面</div>} />
        </Routes>
      </main>
    </div>
  )
}

function TeacherOverview() {
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-700">歡迎回來！</h2>
          <p className="mt-2 text-gray-500">這是您的教師儀表板</p>
        </div>
      </div>
    </div>
  )
}

export default TeacherDashboard