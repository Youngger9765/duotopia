import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Plus, Edit2, Trash2, Search, UserCheck, Mail, Phone, Calendar, Building2, Download, Upload } from 'lucide-react'

interface Teacher {
  id: string
  name: string
  email: string
  phone: string
  institutionId: string
  institutionName: string
  subjects: string[]
  hireDate: string
  status: 'active' | 'inactive' | 'on_leave'
  classCount: number
  studentCount: number
}

function TeacherManagement() {
  const [showAddTeacher, setShowAddTeacher] = useState(false)
  const [editingTeacher, setEditingTeacher] = useState<Teacher | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterInstitution, setFilterInstitution] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')

  const [teachers, setTeachers] = useState<Teacher[]>([
    {
      id: '1',
      name: '王老師',
      email: 'teacher1@duotopia.com',
      phone: '0912-345-678',
      institutionId: '1',
      institutionName: '台北總校',
      subjects: ['英語', '數學'],
      hireDate: '2020-03-15',
      status: 'active',
      classCount: 3,
      studentCount: 48
    },
    {
      id: '2',
      name: '李老師',
      email: 'teacher2@duotopia.com',
      phone: '0923-456-789',
      institutionId: '1',
      institutionName: '台北總校',
      subjects: ['國文', '歷史'],
      hireDate: '2020-08-01',
      status: 'active',
      classCount: 2,
      studentCount: 35
    },
    {
      id: '3',
      name: '張老師',
      email: 'teacher3@duotopia.com',
      phone: '0934-567-890',
      institutionId: '2',
      institutionName: '新竹分校',
      subjects: ['數學', '物理'],
      hireDate: '2021-01-10',
      status: 'active',
      classCount: 4,
      studentCount: 62
    },
    {
      id: '4',
      name: '陳老師',
      email: 'teacher4@duotopia.com',
      phone: '0945-678-901',
      institutionId: '3',
      institutionName: '台中補習班',
      subjects: ['英語'],
      hireDate: '2022-02-20',
      status: 'on_leave',
      classCount: 0,
      studentCount: 0
    }
  ])

  const institutions = [
    { id: '1', name: '台北總校' },
    { id: '2', name: '新竹分校' },
    { id: '3', name: '台中補習班' }
  ]

  const filteredTeachers = teachers.filter(teacher => {
    const matchesSearch = teacher.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         teacher.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         teacher.subjects.some(s => s.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesInstitution = filterInstitution === 'all' || teacher.institutionId === filterInstitution
    const matchesStatus = filterStatus === 'all' || teacher.status === filterStatus
    return matchesSearch && matchesInstitution && matchesStatus
  })

  const getStatusLabel = (status: Teacher['status']) => {
    switch (status) {
      case 'active': return '在職'
      case 'inactive': return '離職'
      case 'on_leave': return '請假中'
    }
  }

  const getStatusColor = (status: Teacher['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      case 'on_leave': return 'bg-yellow-100 text-yellow-800'
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">教師名冊</h2>
        <p className="text-sm text-gray-500 mt-1">管理所有機構的教師資料</p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">教師總數</dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">{teachers.length}</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">在職教師</dt>
            <dd className="mt-1 text-3xl font-semibold text-green-600">
              {teachers.filter(t => t.status === 'active').length}
            </dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">總班級數</dt>
            <dd className="mt-1 text-3xl font-semibold text-blue-600">
              {teachers.reduce((sum, t) => sum + t.classCount, 0)}
            </dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">總學生數</dt>
            <dd className="mt-1 text-3xl font-semibold text-purple-600">
              {teachers.reduce((sum, t) => sum + t.studentCount, 0)}
            </dd>
          </div>
        </div>
      </div>

      {/* Filters and Actions */}
      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <div className="flex flex-col lg:flex-row justify-between gap-4">
          <div className="flex flex-col sm:flex-row gap-4 flex-1">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="搜尋教師姓名、Email或科目..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <select
              value={filterInstitution}
              onChange={(e) => setFilterInstitution(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">所有機構</option>
              {institutions.map(inst => (
                <option key={inst.id} value={inst.id}>{inst.name}</option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">所有狀態</option>
              <option value="active">在職</option>
              <option value="inactive">離職</option>
              <option value="on_leave">請假中</option>
            </select>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              匯入
            </Button>
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              匯出
            </Button>
            <Button onClick={() => setShowAddTeacher(true)}>
              <Plus className="w-4 h-4 mr-2" />
              新增教師
            </Button>
          </div>
        </div>
      </div>

      {/* Teacher Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                教師資料
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                所屬機構
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                教授科目
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                班級 / 學生
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                狀態
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredTeachers.map((teacher) => (
              <tr key={teacher.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                      <UserCheck className="h-5 w-5 text-gray-600" />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{teacher.name}</div>
                      <div className="text-sm text-gray-500 flex items-center">
                        <Mail className="w-3 h-3 mr-1" />
                        {teacher.email}
                      </div>
                      <div className="text-sm text-gray-500 flex items-center">
                        <Phone className="w-3 h-3 mr-1" />
                        {teacher.phone}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center text-sm">
                    <Building2 className="w-4 h-4 mr-1 text-gray-400" />
                    <span className="text-gray-900">{teacher.institutionName}</span>
                  </div>
                  <div className="flex items-center text-xs text-gray-500 mt-1">
                    <Calendar className="w-3 h-3 mr-1" />
                    入職：{teacher.hireDate}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex flex-wrap gap-1">
                    {teacher.subjects.map((subject, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {subject}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div>{teacher.classCount} 個班級</div>
                  <div>{teacher.studentCount} 位學生</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(teacher.status)}`}>
                    {getStatusLabel(teacher.status)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setEditingTeacher(teacher)}
                      className="text-indigo-600 hover:text-indigo-900"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        // Delete logic
                      }}
                      className="text-red-600 hover:text-red-900"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Teacher Modal */}
      {showAddTeacher && (
        <AddTeacherModal
          institutions={institutions}
          onClose={() => setShowAddTeacher(false)}
          onSave={(newTeacher: any) => {
            setTeachers([...teachers, {
              ...newTeacher,
              id: Date.now().toString(),
              hireDate: new Date().toISOString().split('T')[0],
              status: 'active',
              classCount: 0,
              studentCount: 0
            }])
            setShowAddTeacher(false)
          }}
        />
      )}

      {/* Edit Teacher Modal */}
      {editingTeacher && (
        <EditTeacherModal
          teacher={editingTeacher}
          institutions={institutions}
          onClose={() => setEditingTeacher(null)}
          onSave={(updatedTeacher: any) => {
            setTeachers(teachers.map(t =>
              t.id === updatedTeacher.id ? updatedTeacher : t
            ))
            setEditingTeacher(null)
          }}
        />
      )}
    </div>
  )
}

function AddTeacherModal({ institutions, onClose, onSave }: any) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    institutionId: '',
    institutionName: '',
    subjects: [] as string[],
    subjectInput: ''
  })

  const addSubject = () => {
    if (formData.subjectInput && !formData.subjects.includes(formData.subjectInput)) {
      setFormData({
        ...formData,
        subjects: [...formData.subjects, formData.subjectInput],
        subjectInput: ''
      })
    }
  }

  const removeSubject = (subject: string) => {
    setFormData({
      ...formData,
      subjects: formData.subjects.filter((s: any) => s !== subject)
    })
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">新增教師</h3>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">教師姓名 *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="請輸入姓名"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">所屬機構 *</label>
              <select
                value={formData.institutionId}
                onChange={(e) => {
                  const inst = institutions.find((i: any) => i.id === e.target.value)
                  setFormData({ 
                    ...formData, 
                    institutionId: e.target.value,
                    institutionName: inst?.name || ''
                  })
                }}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">請選擇機構</option>
                {institutions.map((inst: any) => (
                  <option key={inst.id} value={inst.id}>{inst.name}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="teacher@duotopia.com"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">聯絡電話 *</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="0912-345-678"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">教授科目</label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={formData.subjectInput}
                onChange={(e) => setFormData({ ...formData, subjectInput: e.target.value })}
                onKeyPress={(e) => e.key === 'Enter' && addSubject()}
                className="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="輸入科目名稱"
              />
              <Button type="button" onClick={addSubject} size="sm">
                新增
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.subjects.map((subject: any, index: number) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                >
                  {subject}
                  <button
                    type="button"
                    onClick={() => removeSubject(subject)}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave(formData)} 
            className="flex-1"
            disabled={!formData.name || !formData.email || !formData.phone || !formData.institutionId}
          >
            新增
          </Button>
        </div>
      </div>
    </div>
  )
}

function EditTeacherModal({ teacher, institutions, onClose, onSave }: any) {
  const [formData, setFormData] = useState({
    name: teacher.name,
    email: teacher.email,
    phone: teacher.phone,
    institutionId: teacher.institutionId,
    institutionName: teacher.institutionName,
    subjects: teacher.subjects,
    status: teacher.status,
    subjectInput: ''
  })

  const addSubject = () => {
    if (formData.subjectInput && !formData.subjects.includes(formData.subjectInput)) {
      setFormData({
        ...formData,
        subjects: [...formData.subjects, formData.subjectInput],
        subjectInput: ''
      })
    }
  }

  const removeSubject = (subject: string) => {
    setFormData({
      ...formData,
      subjects: formData.subjects.filter((s: any) => s !== subject)
    })
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">編輯教師資料</h3>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">教師姓名 *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">所屬機構 *</label>
              <select
                value={formData.institutionId}
                onChange={(e) => {
                  const inst = institutions.find((i: any) => i.id === e.target.value)
                  setFormData({ 
                    ...formData, 
                    institutionId: e.target.value,
                    institutionName: inst?.name || ''
                  })
                }}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                {institutions.map((inst: any) => (
                  <option key={inst.id} value={inst.id}>{inst.name}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">聯絡電話 *</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">教授科目</label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={formData.subjectInput}
                onChange={(e) => setFormData({ ...formData, subjectInput: e.target.value })}
                onKeyPress={(e) => e.key === 'Enter' && addSubject()}
                className="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="輸入科目名稱"
              />
              <Button type="button" onClick={addSubject} size="sm">
                新增
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.subjects.map((subject: any, index: number) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                >
                  {subject}
                  <button
                    type="button"
                    onClick={() => removeSubject(subject)}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">狀態</label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value as Teacher['status'] })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="active">在職</option>
              <option value="inactive">離職</option>
              <option value="on_leave">請假中</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave({ ...teacher, ...formData })} 
            className="flex-1"
          >
            儲存變更
          </Button>
        </div>
      </div>
    </div>
  )
}

export default TeacherManagement