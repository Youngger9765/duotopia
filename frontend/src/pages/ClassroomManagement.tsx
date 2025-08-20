import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Plus, Edit2, Trash2, Search, UserPlus, MoreVertical, X, FileText, BookOpen, BookPlus, Check, Users } from 'lucide-react'
import { teacherApi, adminApi } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

interface Classroom {
  id: string
  name: string
  grade: string
  teacher: string
  studentCount: number
  schoolId: string
  schoolName: string
}

interface Student {
  id: string
  name: string
  email: string
  status: 'active' | 'inactive'
  joinDate: string
}

interface Course {
  id: string
  name: string
  description: string
  schoolId: string
}

function ClassroomManagement() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { toast } = useToast()
  const [selectedClassroom, setSelectedClassroom] = useState<Classroom | null>(null)
  const [showAddClassroom, setShowAddClassroom] = useState(false)
  const [editingClassroom, setEditingClassroom] = useState<Classroom | null>(null)
  const [showAddStudent, setShowAddStudent] = useState(false)
  const [showManageCourses, setShowManageCourses] = useState(false)
  const [searchClassroomTerm, setSearchClassroomTerm] = useState('')
  const [searchStudentTerm, setSearchStudentTerm] = useState('')
  const [selectedSchool, setSelectedInstitution] = useState<string>('all')
  const [activeTab, setActiveTab] = useState<'courses' | 'students' | 'assignments'>('courses')
  const [loading, setLoading] = useState(true)
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [schools, setSchools] = useState<any[]>([])
  const [classroomStudents, setClassroomStudents] = useState<Record<string, Student[]>>({})

  // Handle URL query parameters
  useEffect(() => {
    const action = searchParams.get('action')
    
    if (action === 'add') {
      setShowAddClassroom(true)
      // Clear the action parameter
      const newParams = new URLSearchParams(searchParams)
      newParams.delete('action')
      setSearchParams(newParams)
    }
  }, [searchParams.get('action')])

  // Fetch data on component mount
  useEffect(() => {
    fetchClassrooms()
    fetchSchools()
  }, [])

  const fetchClassrooms = async () => {
    try {
      setLoading(true)
      const response = await teacherApi.getClassrooms()
      const formattedClassrooms = response.data.map((cls: any) => ({
        id: cls.id,
        name: cls.name,
        grade: cls.grade_level || cls.grade,
        teacher: cls.teacher_name || '未指定',
        studentCount: cls.student_count || 0,
        schoolId: cls.school_id,
        schoolName: cls.school_name || ''
      }))
      setClassrooms(formattedClassrooms)
    } catch (error) {
      console.error('Failed to fetch classrooms:', error)
      toast({
        title: "錯誤",
        description: "無法載入教室資料",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchSchools = async () => {
    try {
      const response = await adminApi.getSchools()
      setSchools(response.data)
    } catch (error) {
      console.error('Failed to fetch schools:', error)
    }
  }

  const fetchClassroomStudents = async (classroomId: string) => {
    try {
      const response = await teacherApi.getClassroomStudents(classroomId)
      const students = response.data.map((student: any) => ({
        id: student.id,
        name: student.name,
        email: student.email,
        status: 'active' as const,
        joinDate: student.created_at?.split('T')[0] || new Date().toISOString().split('T')[0]
      }))
      setClassroomStudents(prev => ({ ...prev, [classroomId]: students }))
    } catch (error) {
      console.error('Failed to fetch classroom students:', error)
    }
  }

  // Mock courses data
  const [availableCourses] = useState<Course[]>([
    { id: '1', name: 'English Conversation 101', description: '基礎英語會話課程', schoolId: '1' },
    { id: '2', name: 'Advanced Grammar', description: '進階文法課程', schoolId: '1' },
    { id: '3', name: 'Business English', description: '商業英語課程', schoolId: '1' },
    { id: '4', name: 'Pronunciation Practice', description: '發音練習課程', schoolId: '2' },
    { id: '5', name: 'Writing Skills', description: '寫作技巧課程', schoolId: '2' },
    { id: '6', name: 'Test Preparation', description: '考試準備課程', schoolId: '3' },
  ])

  // Class-course relationships
  const [classroomCourses, setClassroomCourses] = useState<Record<string, string[]>>({
    '1': ['1', '2'], // 六年一班 has English Conversation 101 and Advanced Grammar
    '2': ['1', '3'], // 六年二班 has English Conversation 101 and Business English
    '3': ['4', '5'], // 五年三班 has Pronunciation Practice and Writing Skills
    '4': ['6'],      // 國一甲班 has Test Preparation
  })

  const filteredClassrooms = classrooms.filter(cls => {
    const matchesSearch = cls.name.toLowerCase().includes(searchClassroomTerm.toLowerCase())
    const matchesSchool = selectedSchool === 'all' || cls.schoolId === selectedSchool
    return matchesSearch && matchesSchool
  })

  const currentClassroomStudents = selectedClassroom ? (classroomStudents[selectedClassroom.id] || []) : []
  const filteredStudents = currentClassroomStudents.filter(student =>
    student && student.name && student.email && (
      student.name.toLowerCase().includes(searchStudentTerm.toLowerCase()) ||
      student.email.toLowerCase().includes(searchStudentTerm.toLowerCase())
    )
  )

  return (
    <div className="h-full">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">教室管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理教室和學生分配</p>
      </div>

      {/* School Filter */}
      <div className="mb-4 bg-white p-4 rounded-lg shadow">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">選擇學校：</label>
          <select
            value={selectedSchool}
            onChange={(e) => {
              setSelectedSchool(e.target.value)
              setSelectedClassroom(null) // Clear selected classroom when changing school
            }}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">所有學校</option>
            {schools.map(inst => (
              <option key={inst.id} value={inst.id}>{inst.name}</option>
            ))}
          </select>
          <div className="ml-auto text-sm text-gray-600">
            共 {filteredClassrooms.length} 個教室
          </div>
        </div>
      </div>

      <div className="flex gap-6 h-[calc(100vh-320px)]">
        {/* Left Panel - Class List */}
        <div className="w-1/3 bg-white rounded-lg shadow overflow-hidden flex flex-col">
          <div className="p-4 border-b">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-medium">教室列表</h3>
              <Button size="sm" onClick={() => setShowAddClassroom(true)}>
                <Plus className="w-4 h-4 mr-1" />
                新增教室
              </Button>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="搜尋教室..."
                value={searchClassroomTerm}
                onChange={(e) => setSearchClassroomTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
              />
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {filteredClassrooms.map((cls) => (
              <div
                key={cls.id}
                onClick={() => {
                  setSelectedClassroom(cls)
                  if (!classroomStudents[cls.id]) {
                    fetchClassroomStudents(cls.id)
                  }
                }}
                className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                  selectedClassroom?.id === cls.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{cls.name}</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      {cls.teacher} · 年級 {cls.grade}
                    </p>
                    <p className="text-sm text-gray-500">
                      {cls.schoolName} · {cls.studentCount} 位學生
                    </p>
                    <div className="mt-2 flex items-center space-x-3 text-xs text-gray-500">
                      <span className="flex items-center">
                        <BookOpen className="w-3 h-3 mr-1" />
                        {classroomCourses[cls.id]?.length || 0} 個課程
                      </span>
                      <span className="flex items-center">
                        <FileText className="w-3 h-3 mr-1" />
                        3 個作業
                      </span>
                      <span className="text-orange-600">
                        2 個待批改
                      </span>
                    </div>
                  </div>
                  <div className="flex space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setEditingClassroom(cls)
                      }}
                      className="p-1 hover:bg-gray-200 rounded"
                    >
                      <Edit2 className="w-4 h-4 text-gray-600" />
                    </button>
                    <button
                      onClick={async (e) => {
                        e.stopPropagation()
                        if (window.confirm(`確定要刪除「${cls.name}」嗎？`)) {
                          try {
                            await teacherApi.deleteClassroom(cls.id)
                            toast({
                              title: "成功",
                              description: "班級已刪除",
                            })
                            fetchClassrooms()
                            if (selectedClassroom?.id === cls.id) {
                              setSelectedClassroom(null)
                            }
                          } catch (error: any) {
                            toast({
                              title: "錯誤",
                              description: error.response?.data?.detail || "無法刪除教室",
                              variant: "destructive",
                            })
                          }
                        }
                      }}
                      className="p-1 hover:bg-gray-200 rounded"
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Panel - Tabbed Content */}
        <div className="flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col">
          {selectedClassroom ? (
            <>
              <div className="p-4 border-b">
                <div className="mb-3">
                  <h3 className="text-lg font-medium">{selectedClassroom.name}</h3>
                  <p className="text-sm text-gray-500">{selectedClassroom.schoolName} · {currentClassroomStudents.length} 位學生</p>
                </div>
                
                {/* Tab Navigation */}
                <div className="flex border-b">
                  <button
                    onClick={() => setActiveTab('courses')}
                    className={`px-4 py-2 -mb-px text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'courses'
                        ? 'text-blue-600 border-blue-600'
                        : 'text-gray-500 border-transparent hover:text-gray-700'
                    }`}
                  >
                    <BookOpen className="inline-block w-4 h-4 mr-1" />
                    管理課程
                  </button>
                  <button
                    onClick={() => setActiveTab('students')}
                    className={`px-4 py-2 -mb-px text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'students'
                        ? 'text-blue-600 border-blue-600'
                        : 'text-gray-500 border-transparent hover:text-gray-700'
                    }`}
                  >
                    <Users className="inline-block w-4 h-4 mr-1" />
                    管理學生
                  </button>
                  <button
                    onClick={() => setActiveTab('assignments')}
                    className={`px-4 py-2 -mb-px text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'assignments'
                        ? 'text-blue-600 border-blue-600'
                        : 'text-gray-500 border-transparent hover:text-gray-700'
                    }`}
                  >
                    <FileText className="inline-block w-4 h-4 mr-1" />
                    管理作業
                  </button>
                </div>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-hidden">
                {activeTab === 'courses' && selectedClassroom && (
                  <CourseTabContent 
                    selectedClassroom={selectedClassroom}
                    classroomCourses={classroomCourses[selectedClassroom.id] || []}
                    availableCourses={availableCourses.filter(course => course.schoolId === selectedClassroom.schoolId)}
                    onManageCourses={() => setShowManageCourses(true)}
                  />
                )}
                
                {activeTab === 'students' && selectedClassroom && (
                  <StudentTabContent
                    students={filteredStudents}
                    searchTerm={searchStudentTerm}
                    onSearchChange={setSearchStudentTerm}
                    onAddStudent={() => setShowAddStudent(true)}
                  />
                )}
                
                {activeTab === 'assignments' && selectedClassroom && (
                  <AssignmentTabContent
                    classroomId={selectedClassroom.id}
                    classroomName={selectedClassroom.name}
                  />
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <p>請選擇一個教室查看詳情</p>
            </div>
          )}
        </div>
      </div>

      {/* Add Class Modal */}
      {showAddClassroom && (
        <AddClassroomModal
          onClose={() => setShowAddClassroom(false)}
          onSave={async (newClass) => {
            try {
              const classData = {
                name: newClass.name,
                grade_level: newClass.grade,
                school_id: newClass.schoolId
              }
              
              await teacherApi.createClassroom(classData)
              toast({
                title: "成功",
                description: "教室已新增",
              })
              fetchClassrooms()
              setShowAddClassroom(false)
            } catch (error: any) {
              toast({
                title: "錯誤",
                description: error.response?.data?.detail || "無法新增教室",
                variant: "destructive",
              })
            }
          }}
          schools={schools}
        />
      )}

      {/* Edit Class Modal */}
      {editingClassroom && (
        <EditClassroomModal
          classroomData={editingClassroom}
          onClose={() => setEditingClassroom(null)}
          onSave={async (updatedClassroom) => {
            try {
              const updateData = {
                name: updatedClass.name,
                grade_level: updatedClassroom.grade
              }
              
              await teacherApi.updateClassroom(updatedClassroom.id, updateData)
              toast({
                title: "成功",
                description: "教室資料已更新",
              })
              fetchClassrooms()
              setEditingClassroom(null)
            } catch (error: any) {
              toast({
                title: "錯誤",
                description: error.response?.data?.detail || "無法更新教室資料",
                variant: "destructive",
              })
            }
          }}
        />
      )}

      {/* Add Student to Class Modal */}
      {showAddStudent && selectedClassroom && (
        <AddStudentToClassroomModal
          classroomName={selectedClassroom.name}
          classroomId={selectedClassroom.id}
          onClose={() => setShowAddStudent(false)}
          onSave={async (studentIds) => {
            try {
              await teacherApi.addStudentsToClassroom(selectedClassroom.id, studentIds)
              toast({
                title: "成功",
                description: "學生已加入教室",
              })
              fetchClassroomStudents(selectedClassroom.id)
              setShowAddStudent(false)
            } catch (error: any) {
              toast({
                title: "錯誤",
                description: error.response?.data?.detail || "無法加入學生",
                variant: "destructive",
              })
            }
          }}
        />
      )}

      {/* Manage Courses Modal */}
      {showManageCourses && selectedClassroom && (
        <ManageCoursesModal
          classroomId={selectedClassroom.id}
          classroomName={selectedClassroom.name}
          schoolId={selectedClassroom.schoolId}
          currentCourses={classroomCourses[selectedClassroom.id] || []}
          availableCourses={availableCourses.filter(course => course.schoolId === selectedClassroom.schoolId)}
          onClose={() => setShowManageCourses(false)}
          onSave={(courseIds) => {
            setClassroomCourses({
              ...classroomCourses,
              [selectedClassroom.id]: courseIds
            })
            setShowManageCourses(false)
          }}
        />
      )}
    </div>
  )
}

function AddClassroomModal({ onClose, onSave, schools }: any) {
  const [formData, setFormData] = useState({
    name: '',
    grade: '',
    teacher: '王老師',
    schoolId: '',
    schoolName: ''
  })

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">新增教室</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">所屬學校 *</label>
            <select
              value={formData.schoolId}
              onChange={(e) => {
                const inst = schools.find(i => i.id === e.target.value)
                setFormData({ 
                  ...formData, 
                  schoolId: e.target.value,
                  schoolName: inst?.name || ''
                })
              }}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="">請選擇學校</option>
              {schools.map(inst => (
                <option key={inst.id} value={inst.id}>{inst.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">教室名稱 *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="例如：六年一班"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">年級 *</label>
            <select
              value={formData.grade}
              onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
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
            <select
              value={formData.teacher}
              onChange={(e) => setFormData({ ...formData, teacher: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="王老師">王老師</option>
              <option value="李老師">李老師</option>
              <option value="張老師">張老師</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave(formData)} 
            className="flex-1"
            disabled={!formData.name || !formData.grade || !formData.schoolId}
          >
            新增
          </Button>
        </div>
      </div>
    </div>
  )
}

function EditClassroomModal({ classroomData, onClose, onSave }: any) {
  const [formData, setFormData] = useState({
    name: classroomData.name,
    grade: classroomData.grade,
    teacher: classroomData.teacher,
    schoolId: classroomData.schoolId,
    schoolName: classroomData.schoolName
  })

  // Schools data would come from props in real app

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">編輯教室</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">所屬學校</label>
            <input
              type="text"
              value={formData.schoolName}
              disabled
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm bg-gray-100 text-gray-600 cursor-not-allowed sm:text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">教室建立後無法更改所屬學校</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">教室名稱</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">年級</label>
            <select
              value={formData.grade}
              onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
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
            <select
              value={formData.teacher}
              onChange={(e) => setFormData({ ...formData, teacher: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="王老師">王老師</option>
              <option value="李老師">李老師</option>
              <option value="張老師">張老師</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave({ ...classroomData, ...formData })} 
            className="flex-1"
          >
            儲存
          </Button>
        </div>
      </div>
    </div>
  )
}

function AddStudentToClassroomModal({ classroomName, classroomId, onClose, onSave }: any) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedStudents, setSelectedStudents] = useState<string[]>([])

  // Mock available students (not in this class)
  const availableStudents = [
    { id: '10', name: '趙小新', email: 'student10@duotopia.com' },
    { id: '11', name: '錢小芬', email: 'student11@duotopia.com' },
    { id: '12', name: '孫小偉', email: 'student12@duotopia.com' },
  ]

  const filteredStudents = availableStudents.filter(student =>
    student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    student.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">新增學生到 {classroomName}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜尋學生..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>
        </div>

        <div className="max-h-64 overflow-y-auto mb-4">
          {filteredStudents.map((student) => (
            <label
              key={student.id}
              className="flex items-center p-3 border-b hover:bg-gray-50 cursor-pointer"
            >
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
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <div className="ml-3">
                <div className="text-sm font-medium text-gray-900">{student.name}</div>
                <div className="text-sm text-gray-500">{student.email}</div>
              </div>
            </label>
          ))}
        </div>

        <div className="flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave(selectedStudents)} 
            className="flex-1"
            disabled={selectedStudents.length === 0}
          >
            新增 ({selectedStudents.length})
          </Button>
        </div>
      </div>
    </div>
  )
}

function ManageCoursesModal({ 
  classroomId, 
  classroomName, 
  schoolId,
  currentCourses, 
  availableCourses, 
  onClose, 
  onSave 
}: { 
  classroomId: string
  classroomName: string
  schoolId: string
  currentCourses: string[]
  availableCourses: Course[]
  onClose: () => void
  onSave: (courseIds: string[]) => void 
}) {
  const [selectedCourses, setSelectedCourses] = useState<string[]>(currentCourses)

  const handleToggleCourse = (courseId: string) => {
    if (selectedCourses.includes(courseId)) {
      setSelectedCourses(selectedCourses.filter(id => id !== courseId))
    } else {
      setSelectedCourses([...selectedCourses, courseId])
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-[80vh] overflow-hidden">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">管理課程 - {classroomName}</h3>
            <p className="text-sm text-gray-500 mt-1">選擇要引入到此班級的課程</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-700">
            <strong>提示：</strong>只能選擇同學校內的課程。已選擇 {selectedCourses.length} 個課程。
          </p>
        </div>

        <div className="overflow-y-auto max-h-[50vh]">
          {availableCourses.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <BookOpen className="mx-auto h-12 w-12 text-gray-400 mb-2" />
              <p>此學校尚無可用課程</p>
              <p className="text-sm mt-1">請先到課程管理建立課程</p>
            </div>
          ) : (
            <div className="space-y-2">
              {availableCourses.map((course) => (
                <label
                  key={course.id}
                  className="flex items-start p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedCourses.includes(course.id)}
                    onChange={() => handleToggleCourse(course.id)}
                    className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <div className="ml-3 flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-900">{course.name}</h4>
                      {selectedCourses.includes(course.id) && (
                        <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                          已引入
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{course.description}</p>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave(selectedCourses)} 
            className="flex-1"
          >
            <Check className="w-4 h-4 mr-2" />
            確認儲存 ({selectedCourses.length})
          </Button>
        </div>
      </div>
    </div>
  )
}

// Course Tab Content Component
function CourseTabContent({ 
  selectedClassroom, 
  classroomCourses, 
  availableCourses, 
  onManageCourses 
}: {
  selectedClassroom: Classroom
  classroomCourses: string[]
  availableCourses: Course[]
  onManageCourses: () => void
}) {
  const enrolledCourses = availableCourses.filter(course => classroomCourses.includes(course.id))
  
  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-sm font-medium text-gray-700">已引入課程 ({enrolledCourses.length})</h4>
        <Button size="sm" onClick={onManageCourses}>
          <BookPlus className="w-4 h-4 mr-1" />
          管理課程
        </Button>
      </div>
      
      {enrolledCourses.length > 0 ? (
        <div className="space-y-3">
          {enrolledCourses.map(course => (
            <div key={course.id} className="p-4 border rounded-lg hover:bg-gray-50">
              <h5 className="font-medium text-gray-900">{course.name}</h5>
              <p className="text-sm text-gray-500 mt-1">{course.description}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <BookOpen className="mx-auto h-12 w-12 text-gray-400 mb-2" />
          <p>尚未引入任何課程</p>
          <Button size="sm" variant="outline" className="mt-2" onClick={onManageCourses}>
            開始引入課程
          </Button>
        </div>
      )}
    </div>
  )
}

// Student Tab Content Component
function StudentTabContent({ 
  students, 
  searchTerm, 
  onSearchChange, 
  onAddStudent 
}: {
  students: Student[]
  searchTerm: string
  onSearchChange: (term: string) => void
  onAddStudent: () => void
}) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b">
        <div className="flex justify-between items-center mb-3">
          <div className="relative flex-1 mr-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜尋學生..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>
          <Button size="sm" onClick={onAddStudent}>
            <UserPlus className="w-4 h-4 mr-1" />
            新增學生
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {students.length > 0 ? (
          <table className="min-w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  學生姓名
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  狀態
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  加入日期
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {students.map((student) => (
                <tr key={student.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                        <span className="text-xs font-medium text-gray-600">
                          {student.name.charAt(1)}
                        </span>
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900">{student.name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{student.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      student.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {student.status === 'active' ? '在學' : '停課'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {student.joinDate}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-gray-600 hover:text-gray-900">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Users className="h-12 w-12 text-gray-400 mb-2" />
            <p className="text-lg mb-2">尚無學生資料</p>
            <p className="text-sm">點擊「新增學生」開始添加學生</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Assignment Tab Content Component
function AssignmentTabContent({ 
  classroomId, 
  className 
}: {
  classroomId: string
  className: string
}) {
  // Mock assignment data
  const assignments = [
    {
      id: '1',
      title: 'Unit 3 - Speaking Practice',
      description: '錄音練習：課文朗讀與對話',
      dueDate: '2024-01-20',
      status: 'active',
      submittedCount: 18,
      totalStudents: 24,
      gradedCount: 12
    },
    {
      id: '2',
      title: 'Reading Comprehension Test',
      description: '閱讀理解測驗：第三單元',
      dueDate: '2024-01-18',
      status: 'active',
      submittedCount: 22,
      totalStudents: 24,
      gradedCount: 5
    }
  ]

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-sm font-medium text-gray-700">教室作業</h4>
        <Button 
          size="sm"
          onClick={() => window.location.href = `/teacher/assignments?classroomId=${classroomId}&action=add`}
        >
          <Plus className="w-4 h-4 mr-1" />
          新增作業
        </Button>
      </div>
      
      <div className="space-y-3">
        {assignments.map(assignment => (
          <div key={assignment.id} className="p-4 border rounded-lg hover:bg-gray-50">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h5 className="font-medium text-gray-900">{assignment.title}</h5>
                <p className="text-sm text-gray-500 mt-1">{assignment.description}</p>
                <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                  <span className="flex items-center">
                    <Users className="w-3 h-3 mr-1" />
                    {assignment.submittedCount}/{assignment.totalStudents} 已提交
                  </span>
                  <span className="flex items-center">
                    <FileText className="w-3 h-3 mr-1" />
                    {assignment.gradedCount} 已批改
                  </span>
                  <span className="flex items-center">
                    截止：{assignment.dueDate}
                  </span>
                </div>
              </div>
              <div className="ml-4 flex flex-col space-y-1">
                <Button size="sm" variant="outline">
                  查看詳情
                </Button>
                {assignment.submittedCount > assignment.gradedCount && (
                  <Button size="sm">
                    批改作業
                  </Button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {assignments.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-2" />
          <p>尚無作業</p>
          <Button size="sm" variant="outline" className="mt-2">
            新增第一個作業
          </Button>
        </div>
      )}
    </div>
  )
}

export default ClassroomManagement