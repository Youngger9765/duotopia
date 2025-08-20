import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, Users, BookOpen, Copy, Edit, Trash2, ChevronLeft, Search, Activity, Clock, FileText, Eye, ChevronRight, DollarSign } from 'lucide-react'
import { api } from '@/lib/api'

interface Student {
  id: string
  full_name: string
  email: string
  enrollment_id: string
  payment_status: string
}

interface Course {
  id: string
  title: string
  description: string
  is_public: boolean
  classroom_id: string | null
  copied_from_id: string | null
  copied_from_title?: string
  unit_count: number
  difficulty_level?: string
  pricing_per_unit?: number
}

interface Unit {
  id: string
  unit_number: number
  title: string
  activity_type: string
  time_limit_minutes: number
  is_active: boolean
  content?: any
  course_id: string
}

interface UnitContent {
  id: string
  unitId: string
  content: string
  instructions: string
  materials?: string[]
  objectives?: string[]
}

export default function ClassroomDetail() {
  const { classroomId } = useParams()
  const navigate = useNavigate()
  const [classroom, setClassroom] = useState<any>(null)
  const [students, setStudents] = useState<Student[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [units, setUnits] = useState<Unit[]>([])
  const [publicCourses, setPublicCourses] = useState<Course[]>([])
  const [unitContents, setUnitContents] = useState<UnitContent[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'students' | 'courses'>('students')
  
  // Student management states
  const [showAddStudent, setShowAddStudent] = useState(false)
  
  // Course management states (three-panel design)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null)
  const [searchCoursesTerm, setSearchCoursesTerm] = useState('')
  const [searchUnitsTerm, setSearchUnitsTerm] = useState('')
  const [coursePanelCollapsed, setCoursePanelCollapsed] = useState(false)
  const [unitPanelCollapsed, setUnitPanelCollapsed] = useState(false)
  const [showCopyModal, setShowCopyModal] = useState(false)
  const [showAddCourse, setShowAddCourse] = useState(false)
  const [showAddUnit, setShowAddUnit] = useState(false)
  const [showUnitPreview, setShowUnitPreview] = useState(false)
  const [showUnitEditor, setShowUnitEditor] = useState(false)

  useEffect(() => {
    fetchClassroomDetails()
  }, [classroomId])

  const fetchClassroomDetails = async () => {
    try {
      const [classroomRes, studentsRes, coursesRes, publicRes] = await Promise.all([
        api.get(`/api/individual/classrooms/${classroomId}`),
        api.get(`/api/individual/classrooms/${classroomId}/students`),
        api.get(`/api/individual/classrooms/${classroomId}/courses`),
        api.get('/api/individual/courses/public')
      ])
      
      setClassroom(classroomRes.data)
      setStudents(studentsRes.data)
      setCourses(coursesRes.data)
      setPublicCourses(publicRes.data)
    } catch (error) {
      console.error('Failed to fetch classroom details:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchCourseUnits = async (courseId: string) => {
    try {
      const response = await api.get(`/api/individual/courses/${courseId}/lessons`)
      setUnits(response.data)
    } catch (error) {
      console.error('Failed to fetch course units:', error)
    }
  }

  // Auto-select first course if none selected
  useEffect(() => {
    if (!selectedCourse && courses.length > 0) {
      setSelectedCourse(courses[0])
    }
  }, [selectedCourse, courses.length])

  // Fetch units when course is selected
  useEffect(() => {
    if (selectedCourse) {
      fetchCourseUnits(selectedCourse.id)
    }
  }, [selectedCourse?.id])

  const handleAddStudent = async (studentId: string) => {
    try {
      await api.post(`/api/individual/classrooms/${classroomId}/students`, {
        student_id: studentId
      })
      await fetchClassroomDetails()
      setShowAddStudent(false)
    } catch (error) {
      console.error('Failed to add student:', error)
    }
  }

  const handleRemoveStudent = async (enrollmentId: string) => {
    if (!confirm('確定要移除這個學生嗎？')) return
    
    try {
      await api.delete(`/api/individual/enrollments/${enrollmentId}`)
      await fetchClassroomDetails()
    } catch (error) {
      console.error('Failed to remove student:', error)
    }
  }

  const handleCopyCourse = async (courseId: string) => {
    try {
      await api.post(`/api/individual/classrooms/${classroomId}/courses/copy`, {
        source_course_id: courseId
      })
      await fetchClassroomDetails()
      setShowCopyModal(false)
    } catch (error) {
      console.error('Failed to copy course:', error)
    }
  }

  const filteredCourses = courses.filter(course =>
    course.title.toLowerCase().includes(searchCoursesTerm.toLowerCase()) ||
    course.description.toLowerCase().includes(searchCoursesTerm.toLowerCase())
  )

  const currentCourseUnits = selectedCourse 
    ? units.filter(unit => 
        unit.course_id === selectedCourse.id &&
        (unit.title.toLowerCase().includes(searchUnitsTerm.toLowerCase()) ||
         unit.activity_type.toLowerCase().includes(searchUnitsTerm.toLowerCase()))
      )
    : []

  const currentUnitContent = selectedUnit
    ? unitContents.find(content => content.unitId === selectedUnit.id) || {
        id: selectedUnit.id,
        unitId: selectedUnit.id,
        content: selectedUnit.content?.instructions || '單元內容尚未設定',
        instructions: '請完成以下單元',
        materials: selectedUnit.content?.materials || [],
        objectives: selectedUnit.content?.objectives || []
      }
    : null

  if (loading) {
    return <div>載入中...</div>
  }

  const renderStudentsTab = () => (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-medium">班級學生</h2>
        <Button onClick={() => setShowAddStudent(true)}>
          <Plus className="mr-2 h-4 w-4" />
          新增學生
        </Button>
      </div>

      {students.length === 0 ? (
        <Card>
          <CardContent className="text-center py-8">
            <Users className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500">尚未加入任何學生</p>
            <Button 
              variant="outline" 
              className="mt-4"
              onClick={() => setShowAddStudent(true)}
            >
              新增第一個學生
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  姓名
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  付款狀態
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {students.map((student) => (
                <tr key={student.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {student.full_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {student.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      student.payment_status === 'paid'
                        ? 'bg-green-100 text-green-800'
                        : student.payment_status === 'overdue'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {student.payment_status === 'paid' ? '已付款' : 
                       student.payment_status === 'overdue' ? '逾期' : '待付款'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Button 
                      size="sm" 
                      variant="ghost"
                      onClick={() => handleRemoveStudent(student.enrollment_id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )

  const renderCoursesTab = () => {
    if (courses.length === 0) {
      return (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-medium">教室課程</h2>
          </div>
          <Card>
            <CardContent className="text-center py-12">
              <BookOpen className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">尚未建立任何課程</h3>
              <p className="text-gray-500 mb-6">開始建立您的第一個課程，或從公版課程複製</p>
              <div className="space-x-3">
                <Button 
                  variant="outline"
                  onClick={() => setShowCopyModal(true)}
                >
                  <Copy className="mr-2 h-4 w-4" />
                  從公版複製
                </Button>
                <Button onClick={() => setShowAddCourse(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  建立新課程
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    return (
      <div className="h-full flex flex-col">
        <div className="mb-4">
          <h2 className="text-xl font-bold text-gray-900">教室課程管理</h2>
          <p className="text-sm text-gray-500 mt-1">管理 {classroom?.name} 的課程和單元內容</p>
        </div>

        <div className="flex-1 flex gap-4 min-h-0">
          {/* First Panel - Course List */}
          <div className={`${coursePanelCollapsed ? 'w-12' : 'w-80'} bg-white rounded-lg shadow overflow-hidden flex flex-col transition-all duration-300`}>
            {coursePanelCollapsed ? (
              <div className="p-2 border-b flex flex-col items-center">
                <button
                  onClick={() => setCoursePanelCollapsed(false)}
                  className="p-2 hover:bg-gray-100 rounded-md"
                  title="展開課程列表"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setShowCopyModal(true)}
                  className="p-2 hover:bg-gray-100 rounded-md mt-2"
                  title="複製課程"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="p-4 border-b">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-base font-medium">教室課程</h3>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => setShowCopyModal(true)}>
                      <Copy className="w-4 h-4 mr-1" />
                      複製
                    </Button>
                    <button
                      onClick={() => setCoursePanelCollapsed(true)}
                      className="p-1 hover:bg-gray-100 rounded"
                      title="收合面板"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="搜尋課程..."
                    value={searchCoursesTerm}
                    onChange={(e) => setSearchCoursesTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                  />
                </div>
              </div>
            )}
            
            {!coursePanelCollapsed && (
              <div className="flex-1 overflow-y-auto">
                {filteredCourses.map((course) => (
                  <div
                    key={course.id}
                    onClick={() => {
                      setSelectedCourse(course)
                      setSelectedUnit(null)
                    }}
                    className={`p-3 border-b cursor-pointer hover:bg-gray-50 ${
                      selectedCourse?.id === course.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center">
                          <h4 className="font-medium text-sm text-gray-900 truncate">{course.title}</h4>
                          {course.copied_from_title && (
                            <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                              複製
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-1 truncate">{course.description}</p>
                        <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                          <span className="flex items-center">
                            <Activity className="w-3 h-3 mr-1" />
                            {course.unit_count} 個單元
                          </span>
                          {course.pricing_per_unit && (
                            <span className="flex items-center text-green-600">
                              <DollarSign className="w-3 h-3 mr-1" />
                              {course.pricing_per_unit}/堂
                            </span>
                          )}
                          {course.difficulty_level && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                              {course.difficulty_level}
                            </span>
                          )}
                        </div>
                        {course.copied_from_title && (
                          <p className="text-xs text-gray-400 mt-1">複製自: {course.copied_from_title}</p>
                        )}
                      </div>
                      <div className="flex space-x-1 ml-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            // Edit course logic here
                          }}
                          className="p-1 hover:bg-gray-200 rounded"
                        >
                          <Edit className="w-3 h-3 text-gray-600" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Second Panel - Lessons */}
          <div className={`${unitPanelCollapsed ? 'w-12' : 'w-96'} bg-white rounded-lg shadow overflow-hidden flex flex-col transition-all duration-300`}>
            {selectedCourse ? (
              <>
                {unitPanelCollapsed ? (
                  <div className="p-2 border-b flex flex-col items-center">
                    <button
                      onClick={() => setUnitPanelCollapsed(false)}
                      className="p-2 hover:bg-gray-100 rounded-md"
                      title="展開單元列表"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setShowAddUnit(true)}
                      className="p-2 hover:bg-gray-100 rounded-md mt-2"
                      title="新增單元"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="p-4 border-b">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="text-base font-medium">{selectedCourse.title} - 單元</h3>
                        <p className="text-xs text-gray-500">
                          {selectedCourse.difficulty_level || '課程'}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" onClick={() => setShowAddUnit(true)}>
                          <Plus className="w-4 h-4 mr-1" />
                          新增單元
                        </Button>
                        <button
                          onClick={() => setUnitPanelCollapsed(true)}
                          className="p-1 hover:bg-gray-100 rounded"
                          title="收合面板"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                      <input
                        type="text"
                        placeholder="搜尋單元..."
                        value={searchUnitsTerm}
                        onChange={(e) => setSearchUnitsTerm(e.target.value)}
                        className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                      />
                    </div>
                  </div>
                )}

                {!unitPanelCollapsed && (
                  <div className="flex-1 overflow-y-auto">
                    {currentCourseUnits.length > 0 ? (
                      <div className="divide-y divide-gray-200">
                        {currentCourseUnits.map((unit) => (
                          <div 
                            key={unit.id} 
                            onClick={() => setSelectedUnit(unit)}
                            className={`p-3 hover:bg-gray-50 cursor-pointer ${
                              selectedUnit?.id === unit.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                            }`}
                          >
                            <div className="flex justify-between items-start">
                              <div className="flex items-start space-x-2">
                                <div className="flex-shrink-0">
                                  <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-sm font-medium text-blue-800">
                                    {unit.unit_number}
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <h4 className="text-sm font-medium text-gray-900 truncate">{unit.title}</h4>
                                  <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                      {unit.activity_type}
                                    </span>
                                    <span className="flex items-center">
                                      <Clock className="w-3 h-3 mr-1" />
                                      {unit.time_limit_minutes} 分鐘
                                    </span>
                                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                                      unit.is_active 
                                        ? 'bg-green-100 text-green-800' 
                                        : 'bg-gray-100 text-gray-800'
                                    }`}>
                                      {unit.is_active ? '啟用' : '停用'}
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center space-x-1 ml-2">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    // Edit unit logic here
                                  }}
                                  className="p-1 hover:bg-gray-200 rounded"
                                >
                                  <Edit className="w-3 h-3 text-gray-600" />
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <Activity className="h-12 w-12 text-gray-400 mb-2" />
                        <p className="text-sm mb-2">尚無單元</p>
                        <p className="text-xs">點擊「新增單元」開始添加單元</p>
                      </div>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <p className="text-sm">請選擇一個課程查看單元</p>
              </div>
            )}
          </div>

          {/* Third Panel - Lesson Content */}
          <div className="flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col">
            {selectedUnit && currentUnitContent ? (
              <>
                <div className="p-4 border-b">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-medium">{selectedUnit.title}</h3>
                      <div className="mt-1 flex items-center space-x-3 text-sm text-gray-500">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          {selectedUnit.activity_type}
                        </span>
                        <span>第 {selectedUnit.unit_number} 課</span>
                        <span className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          {selectedUnit.time_limit_minutes} 分鐘
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setShowUnitPreview(true)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        預覽
                      </Button>
                      <Button 
                        size="sm"
                        onClick={() => setShowUnitEditor(true)}
                      >
                        編輯內容
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6">
                  <div className="max-w-4xl mx-auto">
                    {/* Instructions Section */}
                    <div className="mb-6">
                      <h4 className="text-base font-medium text-gray-900 mb-2">單元說明</h4>
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <p className="text-sm text-blue-800">{currentUnitContent.instructions}</p>
                      </div>
                    </div>

                    {/* Content Section */}
                    <div className="mb-6">
                      <h4 className="text-base font-medium text-gray-900 mb-2">單元內容</h4>
                      <div className="bg-gray-50 p-6 rounded-lg">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{currentUnitContent.content}</p>
                      </div>
                    </div>

                    {/* Materials Section */}
                    {currentUnitContent.materials && currentUnitContent.materials.length > 0 && (
                      <div className="mb-6">
                        <h4 className="text-base font-medium text-gray-900 mb-2">教材資源</h4>
                        <div className="grid grid-cols-1 gap-3">
                          {currentUnitContent.materials.map((material, index) => (
                            <div key={index} className="flex items-center p-3 bg-white border border-gray-200 rounded-lg hover:shadow-sm">
                              <FileText className="w-5 h-5 text-gray-400 mr-3" />
                              <span className="text-sm text-gray-700">{material}</span>
                              <Button size="sm" variant="ghost" className="ml-auto">
                                下載
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Objectives Section */}
                    {currentUnitContent.objectives && currentUnitContent.objectives.length > 0 && (
                      <div className="mb-6">
                        <h4 className="text-base font-medium text-gray-900 mb-2">學習目標</h4>
                        <div className="bg-white border border-gray-200 rounded-lg p-4">
                          <ul className="list-disc list-inside space-y-1">
                            {currentUnitContent.objectives.map((objective, index) => (
                              <li key={index} className="text-sm text-gray-700">{objective}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm">請選擇一個單元查看內容</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/individual/classrooms')}
          className="mr-4"
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          返回
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{classroom?.name}</h1>
          <p className="text-sm text-gray-500">
            {classroom?.grade_level} • {classroom?.location} • ${classroom?.pricing}/堂
          </p>
        </div>
      </div>

      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('students')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'students'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Users className="inline h-4 w-4 mr-2" />
              學生管理 ({students.length}/{classroom?.max_students || 10})
            </button>
            <button
              onClick={() => setActiveTab('courses')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'courses'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <BookOpen className="inline h-4 w-4 mr-2" />
              課程管理 ({courses.length})
            </button>
          </nav>
        </div>
      </div>

      <div className="flex-1">
        {activeTab === 'students' && renderStudentsTab()}
        {activeTab === 'courses' && renderCoursesTab()}
      </div>

      {/* 新增學生對話框 */}
      {showAddStudent && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium mb-4">新增學生到班級</h3>
            {/* 這裡應該有學生選擇器 */}
            <div className="mt-4 flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowAddStudent(false)}>
                取消
              </Button>
              <Button onClick={() => handleAddStudent('student-id')}>
                確認新增
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 複製課程對話框 */}
      {showCopyModal && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-medium mb-4">從公版課程複製</h3>
            <div className="grid grid-cols-1 gap-4">
              {publicCourses.map((course) => (
                <Card key={course.id} className="cursor-pointer hover:shadow-md">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-medium">{course.title}</h4>
                        <p className="text-sm text-gray-600 mt-1">{course.description}</p>
                        <p className="text-sm text-gray-500 mt-2">單元數: {course.unit_count}</p>
                        {course.pricing_per_unit && (
                          <p className="text-sm text-green-600 mt-1">${course.pricing_per_unit}/堂</p>
                        )}
                      </div>
                      <Button 
                        size="sm"
                        onClick={() => handleCopyCourse(course.id)}
                      >
                        複製
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            <div className="mt-4 flex justify-end">
              <Button variant="outline" onClick={() => setShowCopyModal(false)}>
                關閉
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}