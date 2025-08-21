import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, Users, BookOpen, Copy, Edit, Trash2, ChevronLeft, Search, Activity, Clock, FileText, Eye, ChevronRight, DollarSign, X, Edit2 } from 'lucide-react'
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
  lesson_count: number
  difficulty_level?: string
  pricing_per_lesson?: number
}

interface Lesson {
  id: string
  lesson_number: number
  title: string
  activity_type: string
  time_limit_minutes: number
  is_active: boolean
  content?: any
  course_id: string
}

interface LessonContent {
  id: string
  lessonId: string
  content: string
  instructions: string
  materials?: string[]
  objectives?: string[]
}

const activityTypeMap: Record<string, string> = {
  reading_assessment: '錄音集',
  speaking_practice: '口說練習',
  speaking_scenario: '情境對話',
  listening_cloze: '聽力填空',
  sentence_making: '造句練習',
  speaking_quiz: '口說測驗'
}

export default function ClassroomDetail() {
  const { classroomId } = useParams()
  const navigate = useNavigate()
  const [classroom, setClassroom] = useState<any>(null)
  const [students, setStudents] = useState<Student[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [publicCourses, setPublicCourses] = useState<Course[]>([])
  const [lessonContents, setLessonContents] = useState<LessonContent[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'students' | 'courses'>('students')
  
  // Student management states
  const [showAddStudent, setShowAddStudent] = useState(false)
  
  // Course management states (three-panel design)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null)
  const [searchCoursesTerm, setSearchCoursesTerm] = useState('')
  const [searchLessonsTerm, setSearchLessonsTerm] = useState('')
  const [coursePanelCollapsed, setCoursePanelCollapsed] = useState(false)
  const [lessonPanelCollapsed, setLessonPanelCollapsed] = useState(false)
  const [showCopyModal, setShowCopyModal] = useState(false)
  const [showAddCourse, setShowAddCourse] = useState(false)
  const [showAddLesson, setShowAddLesson] = useState(false)
  const [showLessonPreview, setShowLessonPreview] = useState(false)
  const [showLessonEditor, setShowLessonEditor] = useState(false)
  const [editingLesson, setEditingLesson] = useState<Lesson | null>(null)
  const [editingCourse, setEditingCourse] = useState<Course | null>(null)
  const [selectedStudents, setSelectedStudents] = useState<string[]>([])
  const [showAssignStudents, setShowAssignStudents] = useState(false)
  const [allClassrooms, setAllClassrooms] = useState<any[]>([])

  useEffect(() => {
    fetchClassroomDetails()
    fetchAllClassrooms()
  }, [classroomId])

  const fetchAllClassrooms = async () => {
    try {
      const response = await api.get('/api/individual/classrooms')
      setAllClassrooms(response.data)
    } catch (error) {
      console.error('Failed to fetch all classrooms:', error)
    }
  }

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

  const fetchCourseLessons = async (courseId: string) => {
    try {
      const response = await api.get(`/api/individual/courses/${courseId}/lessons`)
      setLessons(response.data)
    } catch (error) {
      console.error('Failed to fetch course lessons:', error)
    }
  }

  const handleDeleteLesson = async (lessonId: string) => {
    try {
      if (!selectedCourse) return
      await api.delete(`/api/individual/courses/${selectedCourse.id}/lessons/${lessonId}`)
      setLessons(prev => prev.filter(l => l.id !== lessonId))
      if (selectedLesson?.id === lessonId) {
        setSelectedLesson(null)
      }
    } catch (error) {
      console.error('Failed to delete lesson:', error)
      alert('刪除單元失敗')
    }
  }

  // Auto-select first course if none selected
  useEffect(() => {
    if (!selectedCourse && courses.length > 0) {
      setSelectedCourse(courses[0])
    }
  }, [selectedCourse, courses.length])

  // Fetch lessons when course is selected
  useEffect(() => {
    if (selectedCourse) {
      fetchCourseLessons(selectedCourse.id)
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

  const currentCourseLessons = selectedCourse 
    ? lessons.filter(lesson => 
        lesson.course_id === selectedCourse.id &&
        (lesson.title.toLowerCase().includes(searchLessonsTerm.toLowerCase()) ||
         lesson.activity_type.toLowerCase().includes(searchLessonsTerm.toLowerCase()))
      )
    : []

  const currentLessonContent = selectedLesson
    ? lessonContents.find(content => content.lessonId === selectedLesson.id) || {
        id: selectedLesson.id,
        lessonId: selectedLesson.id,
        content: selectedLesson.content?.instructions || '單元內容尚未設定',
        instructions: '請完成以下單元',
        materials: selectedLesson.content?.materials || [],
        objectives: selectedLesson.content?.objectives || []
      }
    : null

  if (loading) {
    return <div>載入中...</div>
  }

  const renderStudentsTab = () => (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-lg font-medium">班級學生</h2>
          {selectedStudents.length > 0 && (
            <p className="text-sm text-gray-500">已選擇 {selectedStudents.length} 位學生</p>
          )}
        </div>
        <div className="flex gap-2">
          {selectedStudents.length > 0 && (
            <Button 
              variant="outline" 
              onClick={() => setShowAssignStudents(true)}
            >
              <Users className="mr-2 h-4 w-4" />
              分配班級 ({selectedStudents.length})
            </Button>
          )}
          <Button onClick={() => setShowAddStudent(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新增學生
          </Button>
        </div>
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
                  註冊日期
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
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {student.enrolled_at ? (() => {
                      const date = new Date(student.enrolled_at)
                      const year = date.getFullYear()
                      const month = String(date.getMonth() + 1).padStart(2, '0')
                      const day = String(date.getDate()).padStart(2, '0')
                      const hours = String(date.getHours()).padStart(2, '0')
                      const minutes = String(date.getMinutes()).padStart(2, '0')
                      return `${year}/${month}/${day} ${hours}:${minutes}`
                    })() : '-'}
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
                      setSelectedLesson(null)
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
                            {course.lesson_count} 個單元
                          </span>
                          {course.pricing_per_lesson && (
                            <span className="flex items-center text-green-600">
                              <DollarSign className="w-3 h-3 mr-1" />
                              {course.pricing_per_lesson}/堂
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
                            setEditingCourse(course)
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
          <div className={`${lessonPanelCollapsed ? 'w-12' : 'w-96'} bg-white rounded-lg shadow overflow-hidden flex flex-col transition-all duration-300`}>
            {selectedCourse ? (
              <>
                {lessonPanelCollapsed ? (
                  <div className="p-2 border-b flex flex-col items-center">
                    <button
                      onClick={() => setLessonPanelCollapsed(false)}
                      className="p-2 hover:bg-gray-100 rounded-md"
                      title="展開單元列表"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setShowAddLesson(true)}
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
                        <Button size="sm" onClick={() => setShowAddLesson(true)}>
                          <Plus className="w-4 h-4 mr-1" />
                          新增單元
                        </Button>
                        <button
                          onClick={() => setLessonPanelCollapsed(true)}
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
                        value={searchLessonsTerm}
                        onChange={(e) => setSearchLessonsTerm(e.target.value)}
                        className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                      />
                    </div>
                  </div>
                )}

                {!lessonPanelCollapsed && (
                  <div className="flex-1 overflow-y-auto">
                    {currentCourseLessons.length > 0 ? (
                      <div className="divide-y divide-gray-200">
                        {currentCourseLessons.map((lesson) => (
                          <div 
                            key={lesson.id} 
                            onClick={() => setSelectedLesson(lesson)}
                            className={`p-3 hover:bg-gray-50 cursor-pointer ${
                              selectedLesson?.id === lesson.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                            }`}
                          >
                            <div className="flex justify-between items-start">
                              <div className="flex items-start space-x-2">
                                <div className="flex-shrink-0">
                                  <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-sm font-medium text-blue-800">
                                    {lesson.lesson_number}
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <h4 className="text-sm font-medium text-gray-900 truncate">{lesson.title}</h4>
                                  <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                      {activityTypeMap[lesson.activity_type] || lesson.activity_type}
                                    </span>
                                    <span className="flex items-center">
                                      <Clock className="w-3 h-3 mr-1" />
                                      {lesson.time_limit_minutes} 分鐘
                                    </span>
                                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                                      lesson.is_active 
                                        ? 'bg-green-100 text-green-800' 
                                        : 'bg-gray-100 text-gray-800'
                                    }`}>
                                      {lesson.is_active ? '啟用' : '停用'}
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center space-x-1 ml-2">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setEditingLesson(lesson)
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
            {selectedLesson && currentLessonContent ? (
              <>
                <div className="p-4 border-b">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-medium">{selectedLesson.title}</h3>
                      <div className="mt-1 flex items-center space-x-3 text-sm text-gray-500">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          {activityTypeMap[selectedLesson.activity_type] || selectedLesson.activity_type}
                        </span>
                        <span>第 {selectedLesson.lesson_number} 課</span>
                        <span className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          {selectedLesson.time_limit_minutes} 分鐘
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setShowLessonPreview(true)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        預覽
                      </Button>
                      <Button 
                        size="sm"
                        onClick={() => setShowLessonEditor(true)}
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
                        <p className="text-sm text-blue-800">{currentLessonContent.instructions}</p>
                      </div>
                    </div>

                    {/* Content Section */}
                    <div className="mb-6">
                      <h4 className="text-base font-medium text-gray-900 mb-2">單元內容</h4>
                      <div className="bg-gray-50 p-6 rounded-lg">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{currentLessonContent.content}</p>
                      </div>
                    </div>

                    {/* Materials Section */}
                    {currentLessonContent.materials && currentLessonContent.materials.length > 0 && (
                      <div className="mb-6">
                        <h4 className="text-base font-medium text-gray-900 mb-2">教材資源</h4>
                        <div className="grid grid-cols-1 gap-3">
                          {currentLessonContent.materials.map((material, index) => (
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
                    {currentLessonContent.objectives && currentLessonContent.objectives.length > 0 && (
                      <div className="mb-6">
                        <h4 className="text-base font-medium text-gray-900 mb-2">學習目標</h4>
                        <div className="bg-white border border-gray-200 rounded-lg p-4">
                          <ul className="list-disc list-inside space-y-1">
                            {currentLessonContent.objectives.map((objective, index) => (
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
                        <p className="text-sm text-gray-500 mt-2">單元數: {course.lesson_count}</p>
                        {course.pricing_per_lesson && (
                          <p className="text-sm text-green-600 mt-1">${course.pricing_per_lesson}/堂</p>
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

      {/* 新增單元對話框 */}
      {showAddLesson && selectedCourse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowAddLesson(false)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">新增單元</h2>
              <button
                onClick={() => setShowAddLesson(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              try {
                await api.post(`/api/individual/courses/${selectedCourse.id}/lessons`, {
                  lesson_number: lessons.length + 1,
                  title: formData.get('title'),
                  activity_type: formData.get('activity_type'),
                  time_limit_minutes: Number(formData.get('time_limit_minutes')),
                  content: {}  // 初始化為空內容
                })
                setShowAddLesson(false)
                fetchCourseLessons(selectedCourse.id)
              } catch (error: any) {
                console.error('Failed to create lesson:', error)
                alert(error.response?.data?.detail || '建立單元失敗')
              }
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    單元名稱
                  </label>
                  <input
                    name="title"
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="例如：Unit 1 - My Family"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    活動類型
                  </label>
                  <select
                    name="activity_type"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="reading_assessment">錄音集</option>
                    <option value="speaking_practice" disabled>口說練習</option>
                    <option value="speaking_scenario" disabled>情境對話</option>
                    <option value="listening_cloze" disabled>聽力填空</option>
                    <option value="sentence_making" disabled>造句練習</option>
                    <option value="speaking_quiz" disabled>口說測驗</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    時間限制（分鐘）
                  </label>
                  <input
                    name="time_limit_minutes"
                    type="number"
                    required
                    defaultValue={60}
                    min={1}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="bg-gray-50 p-3 rounded-md">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">課程：</span>{selectedCourse.title}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">單元編號：</span>第 {lessons.length + 1} 課
                  </p>
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button type="button" variant="outline" onClick={() => setShowAddLesson(false)}>
                  取消
                </Button>
                <Button type="submit">
                  建立單元
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 編輯單元對話框 */}
      {editingLesson && selectedCourse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setEditingLesson(null)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">編輯單元</h2>
              <button
                onClick={() => setEditingLesson(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              try {
                await api.put(`/api/individual/courses/${selectedCourse.id}/lessons/${editingLesson.id}`, {
                  title: formData.get('title'),
                  activity_type: formData.get('activity_type'),
                  time_limit_minutes: Number(formData.get('time_limit_minutes')),
                  is_active: formData.get('is_active') === 'true'
                })
                setEditingLesson(null)
                fetchCourseLessons(selectedCourse.id)
              } catch (error) {
                console.error('Failed to update lesson:', error)
              }
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    單元名稱
                  </label>
                  <input
                    name="title"
                    type="text"
                    required
                    defaultValue={editingLesson.title}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    活動類型
                  </label>
                  <select
                    name="activity_type"
                    required
                    defaultValue={editingLesson.activity_type}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="reading_assessment">錄音集</option>
                    <option value="speaking_practice" disabled>口說練習</option>
                    <option value="speaking_scenario" disabled>情境對話</option>
                    <option value="listening_cloze" disabled>聽力填空</option>
                    <option value="sentence_making" disabled>造句練習</option>
                    <option value="speaking_quiz" disabled>口說測驗</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    時間限制（分鐘）
                  </label>
                  <input
                    name="time_limit_minutes"
                    type="number"
                    required
                    defaultValue={editingLesson.time_limit_minutes}
                    min={1}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    name="is_active"
                    type="checkbox"
                    value="true"
                    id="edit_is_active"
                    defaultChecked={editingLesson.is_active}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="edit_is_active" className="ml-2 block text-sm text-gray-900">
                    啟用單元
                  </label>
                </div>
                <div className="bg-gray-50 p-3 rounded-md">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">課程：</span>{selectedCourse.title}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">單元編號：</span>第 {editingLesson.lesson_number} 課
                  </p>
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button type="button" variant="outline" onClick={() => setEditingLesson(null)}>
                  取消
                </Button>
                <Button type="submit">
                  更新單元
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 編輯課程對話框 */}
      {editingCourse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setEditingCourse(null)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">編輯課程</h2>
              <button
                onClick={() => setEditingCourse(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              try {
                await api.put(`/api/individual/courses/${editingCourse.id}`, {
                  title: formData.get('title'),
                  description: formData.get('description'),
                  difficulty_level: formData.get('difficulty_level'),
                  pricing_per_lesson: Number(formData.get('pricing_per_lesson')) || null
                })
                setEditingCourse(null)
                fetchClassroomDetails()
              } catch (error: any) {
                console.error('Failed to update course:', error)
                alert(error.response?.data?.detail || '更新課程失敗')
              }
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    課程名稱
                  </label>
                  <input
                    name="title"
                    type="text"
                    required
                    defaultValue={editingCourse.title}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    課程描述
                  </label>
                  <textarea
                    name="description"
                    rows={3}
                    defaultValue={editingCourse.description}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="請描述課程內容..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    難度等級
                  </label>
                  <select
                    name="difficulty_level"
                    defaultValue={editingCourse.difficulty_level}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">請選擇難度等級</option>
                    <option value="preA">preA</option>
                    <option value="A1">A1</option>
                    <option value="A2">A2</option>
                    <option value="B1">B1</option>
                    <option value="B2">B2</option>
                    <option value="C1">C1</option>
                    <option value="C2">C2</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    每堂課價格
                  </label>
                  <input
                    name="pricing_per_lesson"
                    type="number"
                    defaultValue={editingCourse.pricing_per_lesson}
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="例如：500"
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button type="button" variant="outline" onClick={() => setEditingCourse(null)}>
                  取消
                </Button>
                <Button type="submit">
                  更新課程
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}