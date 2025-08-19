import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Plus, Search, Users, School } from 'lucide-react'

function StudentManagementSimple() {
  const [activeTab, setActiveTab] = useState<'students' | 'classes'>('students')
  const [searchTerm, setSearchTerm] = useState('')
  const [showAddStudent, setShowAddStudent] = useState(false)

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">學生管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理學生資料、分配班級</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('students')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'students'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Users className="inline-block w-4 h-4 mr-2" />
            學生名單
          </button>
          <button
            onClick={() => setActiveTab('classes')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'classes'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <School className="inline-block w-4 h-4 mr-2" />
            班級管理
          </button>
        </nav>
      </div>

      {/* Filters */}
      <div className="mb-4 bg-white p-4 rounded-lg shadow">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="搜尋姓名、Email或電話..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          
          <select className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500">
            <option value="all">所有學校</option>
            <option value="1">台北總校</option>
            <option value="2">新竹分校</option>
            <option value="3">台中補習班</option>
          </select>
          
          <select className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500">
            <option value="all">所有狀態</option>
            <option value="assigned">已分班</option>
            <option value="unassigned">待分班</option>
          </select>
          
          {activeTab === 'students' && (
            <Button onClick={() => setShowAddStudent(true)}>
              <Plus className="w-4 h-4 mr-2" />
              新增學生
            </Button>
          )}
          
          {activeTab === 'classes' && (
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              新增班級
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          {activeTab === 'students' ? (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">學生名單</h3>
              <div className="text-gray-500">
                這裡會顯示學生列表。目前為簡化版本。
              </div>
            </div>
          ) : (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">班級管理</h3>
              <div className="text-gray-500">
                這裡會顯示班級列表。目前為簡化版本。
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add Student Modal */}
      {showAddStudent && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">新增學生</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">學生姓名</label>
                <input
                  type="text"
                  placeholder="請輸入學生姓名"
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input
                  type="email"
                  placeholder="student@example.com"
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            <div className="mt-6 flex space-x-3">
              <Button 
                onClick={() => setShowAddStudent(false)} 
                variant="outline" 
                className="flex-1"
              >
                取消
              </Button>
              <Button className="flex-1">
                新增
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StudentManagementSimple