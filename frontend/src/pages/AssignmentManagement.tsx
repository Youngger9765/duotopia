import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Plus, Search, FileText, Users, AlertCircle, Calendar, Download } from 'lucide-react'

interface Assignment {
  id: string
  title: string
  description: string
  classId: string
  className: string
  institutionId: string
  institutionName: string
  dueDate: string
  createdAt: string
  status: 'active' | 'closed'
  totalStudents: number
  submittedCount: number
  gradedCount: number
}

function AssignmentManagement() {
  const [searchParams, setSearchParams] = useSearchParams()
  const classId = searchParams.get('classId')
  
  const [showAddAssignment, setShowAddAssignment] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedInstitution, setSelectedInstitution] = useState<string>('all')
  const [selectedClass, setSelectedClass] = useState<string>(classId || 'all')
  const [filterStatus, setFilterStatus] = useState<string>('all')

  // Handle URL query parameters
  useEffect(() => {
    const action = searchParams.get('action')
    const filter = searchParams.get('filter')
    
    if (action === 'add') {
      setShowAddAssignment(true)
      // Remove the action from URL but keep other params
      const newParams = new URLSearchParams(searchParams)
      newParams.delete('action')
      setSearchParams(newParams)
    }
    
    if (filter === 'pending') {
      setFilterStatus('active')
      // You might want to add additional filtering logic here
    }
  }, [searchParams.get('action'), searchParams.get('filter')])

  // Mock institutions data
  const institutions = [
    { id: '1', name: '台北總校' },
    { id: '2', name: '新竹分校' },
    { id: '3', name: '台中補習班' }
  ]

  // Mock classes data
  const classes = [
    { id: '1', name: '六年一班', institutionId: '1' },
    { id: '2', name: '六年二班', institutionId: '1' },
    { id: '3', name: '五年三班', institutionId: '2' },
    { id: '4', name: '國一甲班', institutionId: '3' }
  ]

  const [assignments] = useState<Assignment[]>([
    {
      id: '1',
      title: 'Lesson 3 - Speaking Practice',
      description: '錄音練習：課文朗讀與對話',
      classId: '1',
      className: '六年一班',
      institutionId: '1',
      institutionName: '台北總校',
      dueDate: '2024-01-20',
      createdAt: '2024-01-13',
      status: 'active',
      totalStudents: 24,
      submittedCount: 18,
      gradedCount: 12
    },
    {
      id: '2',
      title: 'Reading Comprehension Test',
      description: '閱讀理解測驗：第三單元',
      classId: '2',
      className: '六年二班',
      institutionId: '1',
      institutionName: '台北總校',
      dueDate: '2024-01-18',
      createdAt: '2024-01-11',
      status: 'active',
      totalStudents: 22,
      submittedCount: 22,
      gradedCount: 5
    },
    {
      id: '3',
      title: '造句練習 - 過去式',
      description: '使用過去式動詞造句，每個動詞造兩個句子',
      classId: '3',
      className: '五年三班',
      institutionId: '2',
      institutionName: '新竹分校',
      dueDate: '2024-01-15',
      createdAt: '2024-01-08',
      status: 'closed',
      totalStudents: 20,
      submittedCount: 20,
      gradedCount: 20
    }
  ])

  const filteredAssignments = assignments.filter(assignment => {
    const matchesSearch = assignment.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         assignment.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesInstitution = selectedInstitution === 'all' || assignment.institutionId === selectedInstitution
    const matchesClass = selectedClass === 'all' || assignment.classId === selectedClass
    const matchesStatus = filterStatus === 'all' || assignment.status === filterStatus
    return matchesSearch && matchesInstitution && matchesClass && matchesStatus
  })

  const pendingCount = filteredAssignments.reduce((sum, a) => sum + (a.submittedCount - a.gradedCount), 0)

  return (
    <div>
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">作業管理</h2>
        <p className="text-sm text-gray-500 mt-1">查看所有班級的作業和批改進度</p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">總作業數</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{filteredAssignments.length}</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">進行中</dt>
            <dd className="mt-1 text-3xl font-semibold text-blue-600">
              {filteredAssignments.filter(a => a.status === 'active').length}
            </dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">待批改</dt>
            <dd className="mt-1 text-3xl font-semibold text-orange-600">{pendingCount}</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">完成率</dt>
            <dd className="mt-1 text-3xl font-semibold text-green-600">
              {filteredAssignments.length > 0 
                ? Math.round(filteredAssignments.reduce((sum, a) => sum + (a.submittedCount / a.totalStudents), 0) / filteredAssignments.length * 100)
                : 0}%
            </dd>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-4 bg-white p-4 rounded-lg shadow">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mr-2">學校：</label>
            <select
              value={selectedInstitution}
              onChange={(e) => {
                setSelectedInstitution(e.target.value)
                setSelectedClass('all')
              }}
              className="px-3 py-1 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">所有學校</option>
              {institutions.map(inst => (
                <option key={inst.id} value={inst.id}>{inst.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mr-2">班級：</label>
            <select
              value={selectedClass}
              onChange={(e) => {
                setSelectedClass(e.target.value)
                // When a class is selected, automatically select its institution
                if (e.target.value !== 'all') {
                  const selectedClassData = classes.find(cls => cls.id === e.target.value)
                  if (selectedClassData) {
                    setSelectedInstitution(selectedClassData.institutionId)
                  }
                }
              }}
              className="px-3 py-1 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">所有班級</option>
              {classes
                .filter(cls => selectedInstitution === 'all' || cls.institutionId === selectedInstitution)
                .map(cls => (
                  <option key={cls.id} value={cls.id}>{cls.name}</option>
                ))
              }
            </select>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mr-2">狀態：</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">全部</option>
              <option value="active">進行中</option>
              <option value="closed">已結束</option>
            </select>
          </div>
        </div>
      </div>

      {/* Action Bar */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜尋作業標題或描述..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 w-64"
            />
          </div>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            匯出報表
          </Button>
          <Button onClick={() => setShowAddAssignment(true)}>
            <Plus className="w-4 h-4 mr-2" />
            新增作業
          </Button>
        </div>
      </div>

      {/* Assignment List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {filteredAssignments.map((assignment) => (
            <li key={assignment.id} className="hover:bg-gray-50">
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center min-w-0 flex-1">
                    <div className="flex-shrink-0">
                      <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
                        <FileText className="h-5 w-5 text-blue-600" />
                      </div>
                    </div>
                    <div className="ml-4 flex-1">
                      <div className="flex items-center">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {assignment.title}
                        </h3>
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          assignment.status === 'active' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {assignment.status === 'active' ? '進行中' : '已結束'}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-gray-500 truncate">
                        {assignment.description}
                      </p>
                      <div className="mt-2 flex items-center text-xs text-gray-500 space-x-4">
                        <span className="font-medium text-gray-700">
                          {assignment.institutionName} · {assignment.className}
                        </span>
                        <span className="flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          截止：{assignment.dueDate}
                        </span>
                        <span className="flex items-center">
                          <Users className="w-3 h-3 mr-1" />
                          {assignment.submittedCount}/{assignment.totalStudents} 已提交
                        </span>
                        {assignment.submittedCount > assignment.gradedCount && (
                          <span className="flex items-center text-orange-600">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            {assignment.submittedCount - assignment.gradedCount} 待批改
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="ml-4 flex items-center space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        // Navigate to assignment detail
                      }}
                    >
                      查看詳情
                    </Button>
                    <Button
                      size="sm"
                      variant={assignment.submittedCount > assignment.gradedCount ? "default" : "outline"}
                      onClick={() => {
                        // Navigate to grading
                      }}
                    >
                      批改作業
                    </Button>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Add Assignment Modal */}
      {showAddAssignment && (
        <AddAssignmentModal
          defaultClassId={classId}
          onClose={() => setShowAddAssignment(false)}
          onSave={(_newAssignment: any) => {
            // Add new assignment logic
            setShowAddAssignment(false)
          }}
        />
      )}
    </div>
  )
}

function AddAssignmentModal({ defaultClassId, onClose, onSave }: any) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    classId: defaultClassId || '',
    dueDate: ''
  })

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">新增作業</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">作業標題 *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="請輸入作業標題"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">作業描述</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="請描述作業內容和要求"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">選擇班級 *</label>
            <select
              value={formData.classId}
              onChange={(e) => setFormData({ ...formData, classId: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              disabled={!!defaultClassId}
            >
              <option value="">請選擇班級</option>
              <option value="1">六年一班</option>
              <option value="2">六年二班</option>
              <option value="3">五年三班</option>
              <option value="4">國一甲班</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">截止日期 *</label>
            <input
              type="date"
              value={formData.dueDate}
              onChange={(e) => setFormData({ ...formData, dueDate: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave(formData)} 
            className="flex-1"
            disabled={!formData.title || !formData.classId || !formData.dueDate}
          >
            建立作業
          </Button>
        </div>
      </div>
    </div>
  )
}

export default AssignmentManagement