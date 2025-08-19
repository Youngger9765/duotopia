import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Users, UserPlus, School, Plus, Search, Filter, Edit2, X, Check } from 'lucide-react'

interface Student {
  id: string
  name: string
  email: string
  class: string
  classId?: string
  status: '已分班' | '待分班'
  birthDate?: string
  parentEmail?: string
  parentPhone?: string
}

interface Class {
  id: string
  name: string
  teacher: string
  students: number
  grade: string
}

function StudentManagement() {
  const [activeTab, setActiveTab] = useState<'students' | 'classes'>('students')
  const [showAddStudent, setShowAddStudent] = useState(false)
  const [showAddClass, setShowAddClass] = useState(false)
  const [editingStudent, setEditingStudent] = useState<Student | null>(null)
  const [showAssignClass, setShowAssignClass] = useState(false)
  const [selectedStudentsForAssign, setSelectedStudentsForAssign] = useState<string[]>([])

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

      {/* Content based on active tab */}
      {activeTab === 'students' ? (
        <StudentListView 
          showAddStudent={showAddStudent} 
          setShowAddStudent={setShowAddStudent}
          editingStudent={editingStudent}
          setEditingStudent={setEditingStudent}
          showAssignClass={showAssignClass}
          setShowAssignClass={setShowAssignClass}
          selectedStudentsForAssign={selectedStudentsForAssign}
          setSelectedStudentsForAssign={setSelectedStudentsForAssign}
        />
      ) : (
        <ClassListView 
          showAddClass={showAddClass} 
          setShowAddClass={setShowAddClass}
        />
      )}
    </div>
  )
}

function StudentListView({ 
  showAddStudent, 
  setShowAddStudent,
  editingStudent,
  setEditingStudent,
  showAssignClass,
  setShowAssignClass,
  selectedStudentsForAssign,
  setSelectedStudentsForAssign
}: any) {
  const [selectedStudents, setSelectedStudents] = useState<string[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  
  const [students, setStudents] = useState<Student[]>([
    { id: '1', name: '陳小明', email: 'student1@duotopia.com', class: '六年一班', classId: '1', status: '已分班', birthDate: '20090828' },
    { id: '2', name: '林小華', email: 'student2@duotopia.com', class: '未分班', status: '待分班', birthDate: '20090828' },
    { id: '3', name: '王小美', email: 'student3@duotopia.com', class: '六年二班', classId: '2', status: '已分班', birthDate: '20090828' },
    { id: '4', name: '張小強', email: 'student4@duotopia.com', class: '未分班', status: '待分班', birthDate: '20090828' },
  ])

  const filteredStudents = students.filter(student => 
    student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    student.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleAssignToClass = () => {
    setSelectedStudentsForAssign(selectedStudents)
    setShowAssignClass(true)
  }

  return (
    <div>
      {/* Action Bar */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜尋學生姓名或Email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 w-64"
            />
          </div>
          <Button variant="outline" size="sm">
            <Filter className="w-4 h-4 mr-2" />
            篩選
          </Button>
        </div>
        <div className="flex space-x-2">
          {selectedStudents.length > 0 && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleAssignToClass}
            >
              分配到班級 ({selectedStudents.length})
            </Button>
          )}
          <Button onClick={() => setShowAddStudent(true)}>
            <UserPlus className="w-4 h-4 mr-2" />
            新增學生
          </Button>
        </div>
      </div>

      {/* Student List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {filteredStudents.map((student) => (
            <li key={student.id} className="hover:bg-gray-50">
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedStudents.includes(student.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedStudents([...selectedStudents, student.id])
                        } else {
                          setSelectedStudents(selectedStudents.filter(id => id !== student.id))
                        }
                      }}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-4"
                    />
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600">
                          {student.name.charAt(1)}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{student.name}</div>
                        <div className="text-sm text-gray-500">{student.email}</div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-sm">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        student.status === '已分班' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {student.class}
                      </span>
                    </div>
                    <div className="flex space-x-2">
                      {student.status === '待分班' && (
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => {
                            setSelectedStudentsForAssign([student.id])
                            setShowAssignClass(true)
                          }}
                        >
                          分配班級
                        </Button>
                      )}
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setEditingStudent(student)}
                      >
                        <Edit2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Add Student Modal */}
      {showAddStudent && (
        <AddStudentModal 
          onClose={() => setShowAddStudent(false)}
          onSave={(newStudent: any) => {
            // Add new student logic
            setShowAddStudent(false)
          }}
        />
      )}

      {/* Edit Student Modal */}
      {editingStudent && (
        <EditStudentModal 
          student={editingStudent}
          onClose={() => setEditingStudent(null)}
          onSave={(updatedStudent: Student) => {
            setStudents(students.map(s => 
              s.id === updatedStudent.id ? updatedStudent : s
            ))
            setEditingStudent(null)
          }}
        />
      )}

      {/* Assign Class Modal */}
      {showAssignClass && (
        <AssignClassModal
          studentIds={selectedStudentsForAssign}
          students={students}
          onClose={() => {
            setShowAssignClass(false)
            setSelectedStudentsForAssign([])
            setSelectedStudents([])
          }}
          onAssign={(classId: string, className: string) => {
            // Update students with new class
            setStudents(students.map(student => {
              if (selectedStudentsForAssign.includes(student.id)) {
                return {
                  ...student,
                  class: className,
                  classId: classId,
                  status: '已分班' as const
                }
              }
              return student
            }))
            setShowAssignClass(false)
            setSelectedStudentsForAssign([])
            setSelectedStudents([])
          }}
        />
      )}
    </div>
  )
}

function ClassListView({ showAddClass, setShowAddClass }: any) {
  const classes: Class[] = [
    { id: '1', name: '六年一班', teacher: '王老師', students: 24, grade: '6' },
    { id: '2', name: '六年二班', teacher: '王老師', students: 22, grade: '6' },
    { id: '3', name: '五年三班', teacher: '李老師', students: 20, grade: '5' },
  ]

  return (
    <div>
      {/* Action Bar */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜尋班級名稱..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 w-64"
            />
          </div>
        </div>
        <Button onClick={() => setShowAddClass(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新增班級
        </Button>
      </div>

      {/* Class Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {classes.map((cls) => (
          <div key={cls.id} className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">{cls.name}</h3>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  年級 {cls.grade}
                </span>
              </div>
              <div className="text-sm text-gray-500 space-y-1">
                <p>教師：{cls.teacher}</p>
                <p>學生人數：{cls.students} 人</p>
              </div>
              <div className="mt-4 flex space-x-2">
                <Button size="sm" variant="outline" className="flex-1">
                  查看學生
                </Button>
                <Button size="sm" variant="outline" className="flex-1">
                  管理
                </Button>
              </div>
            </div>
          </div>
        ))}
        
        {/* Add New Class Card */}
        <div 
          onClick={() => setShowAddClass(true)}
          className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow border-2 border-dashed border-gray-300 cursor-pointer group"
        >
          <div className="px-4 py-5 sm:p-6 h-full flex items-center justify-center">
            <div className="text-center">
              <Plus className="mx-auto h-12 w-12 text-gray-400 group-hover:text-gray-500" />
              <p className="mt-2 text-sm text-gray-500 group-hover:text-gray-700">新增班級</p>
            </div>
          </div>
        </div>
      </div>

      {/* Add Class Modal */}
      {showAddClass && (
        <AddClassModal onClose={() => setShowAddClass(false)} />
      )}
    </div>
  )
}

function EditStudentModal({ 
  student, 
  onClose, 
  onSave 
}: { 
  student: Student
  onClose: () => void
  onSave: (student: Student) => void 
}) {
  const [formData, setFormData] = useState({
    name: student.name,
    email: student.email,
    birthDate: student.birthDate || '',
    parentEmail: student.parentEmail || '',
    parentPhone: student.parentPhone || '',
  })

  const handleSave = () => {
    onSave({
      ...student,
      ...formData
    })
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">編輯學生資料</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">學生姓名</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">生日</label>
            <input
              type="text"
              value={formData.birthDate}
              onChange={(e) => setFormData({ ...formData, birthDate: e.target.value })}
              placeholder="YYYYMMDD"
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">家長 Email</label>
            <input
              type="email"
              value={formData.parentEmail}
              onChange={(e) => setFormData({ ...formData, parentEmail: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="parent@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">家長電話</label>
            <input
              type="tel"
              value={formData.parentPhone}
              onChange={(e) => setFormData({ ...formData, parentPhone: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="0912345678"
            />
          </div>

          {student.status === '已分班' && (
            <div className="bg-gray-50 p-3 rounded-md">
              <p className="text-sm text-gray-600">
                目前班級：<span className="font-medium">{student.class}</span>
              </p>
            </div>
          )}
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button onClick={handleSave} className="flex-1">
            <Check className="w-4 h-4 mr-2" />
            儲存
          </Button>
        </div>
      </div>
    </div>
  )
}

function AssignClassModal({ 
  studentIds, 
  students,
  onClose, 
  onAssign 
}: { 
  studentIds: string[]
  students: Student[]
  onClose: () => void
  onAssign: (classId: string, className: string) => void 
}) {
  const [selectedClass, setSelectedClass] = useState('')
  
  const selectedStudents = students.filter(s => studentIds.includes(s.id))
  
  const classes = [
    { id: '1', name: '六年一班', teacher: '王老師', grade: '6' },
    { id: '2', name: '六年二班', teacher: '王老師', grade: '6' },
    { id: '3', name: '五年三班', teacher: '李老師', grade: '5' },
  ]

  const handleAssign = () => {
    const cls = classes.find(c => c.id === selectedClass)
    if (cls) {
      onAssign(selectedClass, cls.name)
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">分配班級</h3>
        
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">
            將以下 {selectedStudents.length} 位學生分配到班級：
          </p>
          <div className="bg-gray-50 rounded-md p-3 max-h-32 overflow-y-auto">
            {selectedStudents.map(student => (
              <div key={student.id} className="text-sm text-gray-700">
                • {student.name} ({student.email})
              </div>
            ))}
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            選擇班級
          </label>
          <div className="space-y-2">
            {classes.map(cls => (
              <label
                key={cls.id}
                className={`flex items-center p-3 border rounded-md cursor-pointer transition-colors ${
                  selectedClass === cls.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input
                  type="radio"
                  name="class"
                  value={cls.id}
                  checked={selectedClass === cls.id}
                  onChange={(e) => setSelectedClass(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-gray-900">{cls.name}</div>
                  <div className="text-xs text-gray-500">
                    {cls.teacher} · 年級 {cls.grade}
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={handleAssign} 
            className="flex-1"
            disabled={!selectedClass}
          >
            確認分配
          </Button>
        </div>
      </div>
    </div>
  )
}

function AddStudentModal({ onClose, onSave }: any) {
  const [assignToClass, setAssignToClass] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    birthDate: '',
    classId: '',
    parentEmail: '',
    parentPhone: '',
  })

  const handleSave = () => {
    // Validate and save
    onSave({
      ...formData,
      id: Date.now().toString(),
      class: assignToClass && formData.classId ? '已分配' : '未分班',
      status: assignToClass && formData.classId ? '已分班' : '待分班'
    })
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">新增學生</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">學生姓名 *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="請輸入學生姓名"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Email *</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="student@example.com"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">生日 (密碼)</label>
            <input
              type="text"
              value={formData.birthDate}
              onChange={(e) => setFormData({ ...formData, birthDate: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="YYYYMMDD"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">家長 Email</label>
            <input
              type="email"
              value={formData.parentEmail}
              onChange={(e) => setFormData({ ...formData, parentEmail: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="parent@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">家長電話</label>
            <input
              type="tel"
              value={formData.parentPhone}
              onChange={(e) => setFormData({ ...formData, parentPhone: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="0912345678"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              checked={assignToClass}
              onChange={(e) => setAssignToClass(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label className="ml-2 block text-sm text-gray-900">
              立即分配到班級
            </label>
          </div>

          {assignToClass && (
            <div>
              <label className="block text-sm font-medium text-gray-700">選擇班級</label>
              <select 
                value={formData.classId}
                onChange={(e) => setFormData({ ...formData, classId: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">請選擇班級</option>
                <option value="1">六年一班</option>
                <option value="2">六年二班</option>
                <option value="3">五年三班</option>
              </select>
            </div>
          )}
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={handleSave} 
            className="flex-1"
            disabled={!formData.name || !formData.email}
          >
            新增
          </Button>
        </div>
      </div>
    </div>
  )
}

function AddClassModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">新增班級</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">班級名稱</label>
            <input
              type="text"
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="例如：六年一班"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">年級</label>
            <select className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm">
              <option value="">請選擇年級</option>
              <option value="1">一年級</option>
              <option value="2">二年級</option>
              <option value="3">三年級</option>
              <option value="4">四年級</option>
              <option value="5">五年級</option>
              <option value="6">六年級</option>
              <option value="7">國一</option>
              <option value="8">國二</option>
              <option value="9">國三</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">教師</label>
            <select className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm">
              <option value="">請選擇教師</option>
              <option value="1">王老師</option>
              <option value="2">李老師</option>
              <option value="3">張老師</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button className="flex-1">
            新增
          </Button>
        </div>
      </div>
    </div>
  )
}

export default StudentManagement