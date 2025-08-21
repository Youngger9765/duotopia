import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Users, School, Plus, Search, Edit2, X, Check } from 'lucide-react'
import { adminApi, teacherApi, api } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

interface Student {
  id: string
  name: string
  email: string
  classroomName: string
  classroomId?: string
  status: '已分班' | '待分班'
  birthDate?: string
  parentEmail?: string
  parentPhone?: string
  schoolId: string
  schoolName: string
}


function StudentManagement() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { toast } = useToast()
  const [activeTab, setActiveTab] = useState<'students' | 'classrooms'>('students')
  const [showAddStudent, setShowAddStudent] = useState(false)
  const [showAddClassroom, setShowAddClassroom] = useState(false)
  const [editingStudent, setEditingStudent] = useState<Student | null>(null)
  const [showAssignClassroom, setShowAssignClassroom] = useState(false)
  const [selectedStudentsForAssign, setSelectedStudentsForAssign] = useState<string[]>([])
  const [selectedSchool, setSelectedSchool] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRole, setSelectedRole] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const [students, setStudents] = useState<Student[]>([])
  const [schools, setSchools] = useState<any[]>([])
  const [classrooms, setClassrooms] = useState<any[]>([])
  const [isIndividual, setIsIndividual] = useState(false)

  // Fetch data on component mount
  useEffect(() => {
    fetchUserRole()
  }, [])

  const fetchUserRole = async () => {
    try {
      const response = await api.get('/api/role/current')
      const roleInfo = response.data
      
      // 判斷是否為個體戶
      const isIndividualTeacher = roleInfo.current_role_context === 'individual' || 
                                 (roleInfo.primary_role === 'teacher' && !roleInfo.is_institutional_admin)
      setIsIndividual(isIndividualTeacher)
      
      // 根據角色決定要載入哪些資料
      fetchStudents()
      fetchClassrooms()
      
      // 只有機構管理員才載入學校資料
      if (!isIndividualTeacher) {
        fetchSchools()
      }
    } catch (error) {
      console.error('Failed to fetch role info:', error)
      // 預設載入基本資料
      fetchStudents()
      fetchClassrooms()
    }
  }

  const fetchStudents = async () => {
    try {
      setLoading(true)
      const response = await adminApi.getStudents()
      const formattedStudents = response.data.map((student: any) => ({
        id: student.id,
        name: student.full_name || student.name || '',
        email: student.email,
        classroomName: student.classroom_name || '未分班',
        classroomId: student.classroom_id,
        status: student.classroom_id ? '已分班' : '待分班',
        birthDate: student.birth_date,
        schoolId: student.school_id || '1',
        schoolName: student.school_name || '未指定學校'
      }))
      setStudents(formattedStudents)
    } catch (error) {
      console.error('Failed to fetch students:', error)
      toast({
        title: "錯誤",
        description: "無法載入學生資料",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchSchools = async () => {
    try {
      const response = await adminApi.getSchools()
      setSchools(response.data || [])
    } catch (error) {
      console.error('Failed to fetch schools:', error)
      setSchools([]) // 確保 schools 不是 undefined
      toast({
        title: "警告",
        description: "無法載入學校資料",
        variant: "destructive",
      })
    }
  }

  const fetchClassrooms = async () => {
    try {
      const response = await teacherApi.getClassrooms()
      setClassrooms(response.data || [])
    } catch (error) {
      console.error('Failed to fetch classrooms:', error)
      setClassrooms([])
    }
  }

  // Handle URL query parameters
  useEffect(() => {
    const action = searchParams.get('action')
    const tab = searchParams.get('tab')
    
    if (tab === 'students') {
      setActiveTab('students')
    } else if (tab === 'classrooms') {
      setActiveTab('classrooms')
    }
    
    if (action === 'add') {
      setShowAddStudent(true)
      // Clear the action parameter
      const newParams = new URLSearchParams(searchParams)
      newParams.delete('action')
      setSearchParams(newParams)
    } else if (action === 'assign') {
      setShowAssignClassroom(true)
      // Clear the action parameter
      const newParams = new URLSearchParams(searchParams)
      newParams.delete('action')
      setSearchParams(newParams)
    }
  }, [searchParams.get('action'), searchParams.get('tab')])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">載入中...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">學生管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理學生資料、分配教室</p>
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
            onClick={() => setActiveTab('classrooms')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'classrooms'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <School className="inline-block w-4 h-4 mr-2" />
            教室管理
          </button>
        </nav>
      </div>

      {/* Compact Filters */}
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
          
          {!isIndividual && (
            <select
              value={selectedSchool}
              onChange={(e) => setSelectedSchool(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">所有學校</option>
              {schools.map((school) => (
                <option key={school.id} value={school.id}>
                  {school.name}
                </option>
              ))}
            </select>
          )}
          
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
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
          
          {activeTab === 'classrooms' && (
            <Button onClick={() => setShowAddClassroom(true)}>
              <Plus className="w-4 h-4 mr-2" />
              新增教室
            </Button>
          )}
        </div>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'students' ? (
        <StudentListView 
          students={students}
          loading={loading}
          showAddStudent={showAddStudent} 
          setShowAddStudent={setShowAddStudent}
          editingStudent={editingStudent}
          setEditingStudent={setEditingStudent}
          showAssignClassroom={showAssignClassroom}
          setShowAssignClassroom={setShowAssignClassroom}
          selectedStudentsForAssign={selectedStudentsForAssign}
          setSelectedStudentsForAssign={setSelectedStudentsForAssign}
          selectedSchool={selectedSchool}
          searchTerm={searchTerm}
          selectedRole={selectedRole}
          fetchStudents={fetchStudents}
          schools={schools}
          classrooms={classrooms}
        />
      ) : (
        <ClassListView 
          showAddClassroom={showAddClassroom} 
          setShowAddClassroom={setShowAddClassroom}
          selectedSchool={selectedSchool}
          searchTerm={searchTerm}
        />
      )}
    </div>
  )
}

function StudentListView({ 
  students,
  showAddStudent, 
  setShowAddStudent,
  editingStudent,
  setEditingStudent,
  showAssignClassroom,
  setShowAssignClassroom,
  selectedStudentsForAssign,
  setSelectedStudentsForAssign,
  selectedSchool,
  searchTerm,
  selectedRole,
  fetchStudents,
  schools,
  classrooms
}: any) {
  const { toast } = useToast()
  const [selectedStudents, setSelectedStudents] = useState<string[]>([])
  
  const filteredStudents = (students || []).filter((student: any) => {
    const matchesSearch = student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         student.email.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSchool = selectedSchool === 'all' || student.schoolId === selectedSchool
    const matchesRole = selectedRole === 'all' || 
                       (selectedRole === 'assigned' && student.status === '已分班') ||
                       (selectedRole === 'unassigned' && student.status === '待分班')
    return matchesSearch && matchesSchool && matchesRole
  })

  const handleAssignToClassroom = () => {
    setSelectedStudentsForAssign(selectedStudents)
    setShowAssignClassroom(true)
  }

  return (
    <div>
      {/* Action buttons for selected students */}
      {selectedStudents.length > 0 && (
        <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700">
              已選擇 {selectedStudents.length} 位學生
            </span>
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleAssignToClassroom}
            >
              分配到教室
            </Button>
          </div>
        </div>
      )}

      {/* Student List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {filteredStudents.map((student: any) => (
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
                    <div>
                      <div className="text-sm text-gray-600">{student.schoolName}</div>
                      <div className="text-sm">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          student.status === '已分班' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {student.classroomName}
                        </span>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      {student.status === '待分班' && (
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => {
                            setSelectedStudentsForAssign([student.id])
                            setShowAssignClassroom(true)
                          }}
                        >
                          分配教室
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
          onSave={async (newStudent: any) => {
            try {
              const defaultSchoolId = schools && schools.length > 0 ? schools[0]?.id : '1';
              const studentData = {
                name: newStudent.name,
                email: newStudent.email,
                birth_date: newStudent.birthDate,
                school_id: newStudent.schoolId || defaultSchoolId,
                parent_email: newStudent.parentEmail,
                parent_phone: newStudent.parentPhone,
                grade: newStudent.grade || '6'
              }
              
              await adminApi.createStudent(studentData)
              toast({
                title: "成功",
                description: "學生已新增",
              })
              fetchStudents()
              setShowAddStudent(false)
            } catch (error: any) {
              toast({
                title: "錯誤",
                description: error.response?.data?.detail || "無法新增學生",
                variant: "destructive",
              })
            }
          }}
          schools={schools}
        />
      )}

      {/* Edit Student Modal */}
      {editingStudent && (
        <EditStudentModal 
          student={editingStudent}
          onClose={() => setEditingStudent(null)}
          onSave={async (updatedStudent: any) => {
            try {
              const updateData = {
                name: updatedStudent.name,
                email: updatedStudent.email,
                // phone: updatedStudent.phone,
                birth_date: updatedStudent.birthDate,
                parent_email: updatedStudent.parentEmail,
                parent_phone: updatedStudent.parentPhone,
                // grade: updatedStudent.grade
              }
              
              await adminApi.updateStudent(updatedStudent.id, updateData)
              toast({
                title: "成功",
                description: "學生資料已更新",
              })
              fetchStudents()
              setEditingStudent(null)
            } catch (error: any) {
              toast({
                title: "錯誤",
                description: error.response?.data?.detail || "無法更新學生資料",
                variant: "destructive",
              })
            }
          }}
        />
      )}

      {/* Assign Class Modal */}
      {showAssignClassroom && (
        <AssignClassModal
          studentIds={selectedStudentsForAssign}
          students={students}
          classes={classrooms}
          onClose={() => {
            setShowAssignClassroom(false)
            setSelectedStudentsForAssign([])
            setSelectedStudents([])
          }}
          onAssign={async () => {
            // Update students with new class
            fetchStudents()
            setShowAssignClassroom(false)
            setSelectedStudentsForAssign([])
            setSelectedStudents([])
          }}
        />
      )}
    </div>
  )
}

function ClassListView({ showAddClass, setShowAddClass, selectedSchool, searchTerm }: any) {
  interface Class {
    id: string
    name: string
    teacher: string
    students: number
    grade: string
    schoolId: string
    schoolName: string
  }
  const classes: Class[] = [
    { id: '1', name: '六年一班', teacher: '王老師', students: 24, grade: '6', schoolId: '1', schoolName: '台北總校' },
    { id: '2', name: '六年二班', teacher: '王老師', students: 22, grade: '6', schoolId: '1', schoolName: '台北總校' },
    { id: '3', name: '五年三班', teacher: '李老師', students: 20, grade: '5', schoolId: '2', schoolName: '新竹分校' },
    { id: '4', name: '國一甲班', teacher: '張老師', students: 28, grade: '7', schoolId: '3', schoolName: '台中補習班' },
  ]
  
  const filteredClasses = classes.filter(cls => {
    const matchesSearch = cls.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSchool = selectedSchool === 'all' || cls.schoolId === selectedSchool
    return matchesSearch && matchesSchool
  })

  return (
    <div>

      {/* Results count */}
      <div className="mb-2 text-sm text-gray-600">
        共 {filteredClasses.length} 個班級
      </div>

      {/* Class Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredClasses.map((cls) => (
          <div key={cls.id} className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">{cls.name}</h3>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  年級 {cls.grade}
                </span>
              </div>
              <div className="text-sm text-gray-500 space-y-1">
                <p>學校：{cls.schoolName}</p>
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
                目前教室：<span className="font-medium">{student.classroomName}</span>
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
  classes,
  onClose, 
  onAssign 
}: { 
  studentIds: string[]
  students: Student[]
  classes: any[]
  onClose: () => void
  onAssign: (classroomId: string, classroomName: string) => void 
}) {
  const [selectedClass, setSelectedClass] = useState('')
  
  const selectedStudents = students.filter(s => studentIds.includes(s.id))

  const handleAssign = () => {
    const cls = classes.find(c => c.id === selectedClass)
    if (cls) {
      onAssign(selectedClass, cls.name)
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">分配教室</h3>
        
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">
            將以下 {selectedStudents.length} 位學生分配到教室：
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
            選擇教室
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
    classroomId: '',
    parentEmail: '',
    parentPhone: '',
  })

  const handleSave = () => {
    // Validate and save
    onSave({
      ...formData,
      id: Date.now().toString(),
      classroomName: assignToClass && formData.classroomId ? '已分配' : '未分班',
      status: assignToClass && formData.classroomId ? '已分班' : '待分班'
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
              立即分配到教室
            </label>
          </div>

          {assignToClass && (
            <div>
              <label className="block text-sm font-medium text-gray-700">選擇教室</label>
              <select 
                value={formData.classroomId}
                onChange={(e) => setFormData({ ...formData, classroomId: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">請選擇教室</option>
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