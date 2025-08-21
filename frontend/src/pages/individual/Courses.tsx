import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Plus, Search, Clock, Edit2, Trash2, Eye, Activity, X, FileText, ChevronLeft, ChevronRight, DollarSign } from 'lucide-react'
import { api } from '@/lib/api'

interface Course {
  id: string
  title: string
  description: string
  difficulty_level: string
  pricing_per_lesson: number
  lesson_count: number
  classroom_id?: string
  classroom_name?: string
  is_public: boolean
  teacher_name: string
  copied_from_title?: string
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

export default function IndividualCourses() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showAddCourse, setShowAddCourse] = useState(false)
  const [showAddLesson, setShowAddLesson] = useState(false)
  const [editingCourse, setEditingCourse] = useState<Course | null>(null)
  const [editingLesson, setEditingLesson] = useState<Lesson | null>(null)
  const [showLessonPreview, setShowLessonPreview] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null)
  const [searchCoursesTerm, setSearchCoursesTerm] = useState('')
  const [searchLessonsTerm, setSearchLessonsTerm] = useState('')
  const [courseFilter, setCourseFilter] = useState<string>('all') // all, public, classroom
  const [coursePanelCollapsed, setCoursePanelCollapsed] = useState(false)
  const [lessonPanelCollapsed, setLessonPanelCollapsed] = useState(false)
  const [courses, setCourses] = useState<Course[]>([])
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [lessonContents] = useState<LessonContent[]>([])
  const [, setLoading] = useState(false)
  const [showLessonEditor, setShowLessonEditor] = useState(false)

  // Fetch data on component mount
  useEffect(() => {
    fetchCourses()
  }, [])

  const fetchCourses = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/individual/courses')
      setCourses(response.data)
    } catch (error) {
      console.error('Failed to fetch courses:', error)
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

  const handleDeleteCourse = async (courseId: string) => {
    try {
      await api.delete(`/api/individual/courses/${courseId}`)
      setCourses(prev => prev.filter(c => c.id !== courseId))
      if (selectedCourse?.id === courseId) {
        setSelectedCourse(null)
        setLessons([])
      }
    } catch (error) {
      console.error('Failed to delete course:', error)
      alert('刪除課程失敗')
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

  // Handle URL query parameters
  useEffect(() => {
    const action = searchParams.get('action')
    if (action === 'add') {
      setShowAddCourse(true)
      setSearchParams({})
    }
  }, [searchParams, setSearchParams])

  const filteredCourses = courses.filter(course => {
    const matchesSearch = course.title.toLowerCase().includes(searchCoursesTerm.toLowerCase()) ||
                         course.description.toLowerCase().includes(searchCoursesTerm.toLowerCase())
    const matchesFilter = courseFilter === 'all' || 
                         (courseFilter === 'public' && course.is_public) ||
                         (courseFilter === 'classroom' && course.classroom_id)
    return matchesSearch && matchesFilter
  })

  // Auto-select first course if none selected
  useEffect(() => {
    if (!selectedCourse && filteredCourses.length > 0) {
      setSelectedCourse(filteredCourses[0])
    }
  }, [selectedCourse, filteredCourses.length])

  // Fetch units when course is selected
  useEffect(() => {
    if (selectedCourse) {
      fetchCourseLessons(selectedCourse.id)
    }
  }, [selectedCourse?.id])

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

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">課程管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理您的課程和單元內容</p>
      </div>

      {/* Course Filter */}
      <div className="mb-4 bg-white p-4 rounded-lg shadow">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">課程類型：</label>
          <select
            value={courseFilter}
            onChange={(e) => {
              setCourseFilter(e.target.value)
              setSelectedCourse(null)
              setSelectedLesson(null)
            }}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">所有課程</option>
            <option value="public">公版課程</option>
            <option value="classroom">教室課程</option>
          </select>
          <div className="ml-auto text-sm text-gray-600">
            共 {filteredCourses.length} 個課程
          </div>
        </div>
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
                onClick={() => setShowAddCourse(true)}
                className="p-2 hover:bg-gray-100 rounded-md mt-2"
                title="新增課程"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="p-4 border-b">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-base font-medium">課程列表</h3>
                <div className="flex items-center gap-2">
                  <Button size="sm" onClick={() => setShowAddCourse(true)}>
                    <Plus className="w-4 h-4 mr-1" />
                    新增課程
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
                        {course.is_public && (
                          <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                            公版
                          </span>
                        )}
                        {course.classroom_name && (
                          <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            教室
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-1 truncate">{course.description}</p>
                      <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                        {course.classroom_name && (
                          <span>{course.classroom_name}</span>
                        )}
                        <span className="flex items-center">
                          <Activity className="w-3 h-3 mr-1" />
                          {course.lesson_count} 個單元
                        </span>
                        <span className="flex items-center text-green-600">
                          <DollarSign className="w-3 h-3 mr-1" />
                          {course.pricing_per_lesson}/堂
                        </span>
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          {course.difficulty_level}
                        </span>
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
                        <Edit2 className="w-3 h-3 text-gray-600" />
                      </button>
                      <button
                        onClick={async (e) => {
                          e.stopPropagation()
                          if (window.confirm('確定要刪除此課程嗎？')) {
                            handleDeleteCourse(course.id)
                          }
                        }}
                        className="p-1 hover:bg-gray-200 rounded"
                      >
                        <Trash2 className="w-3 h-3 text-red-600" />
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
                        {selectedCourse.classroom_name || '公版課程'} • {selectedCourse.difficulty_level}
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
                                <Edit2 className="w-3 h-3 text-gray-600" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (window.confirm('確定要刪除此單元嗎？')) {
                                    handleDeleteLesson(lesson.id)
                                  }
                                }}
                                className="p-1 hover:bg-gray-200 rounded"
                              >
                                <Trash2 className="w-3 h-3 text-red-600" />
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
                        {currentLessonContent.materials.map((material: any, index: number) => (
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
                          {currentLessonContent.objectives.map((objective: any, index: number) => (
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

      {/* 新增課程對話框 */}
      {showAddCourse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowAddCourse(false)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">新增課程</h2>
              <button
                onClick={() => setShowAddCourse(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              try {
                await api.post('/api/individual/courses', {
                  title: formData.get('title'),
                  description: formData.get('description'),
                  difficulty_level: formData.get('difficulty_level'),
                  pricing_per_lesson: Number(formData.get('pricing_per_lesson')),
                  is_public: formData.get('is_public') === 'true'
                })
                setShowAddCourse(false)
                fetchCourses()
              } catch (error) {
                console.error('Failed to create course:', error)
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
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    難度等級
                  </label>
                  <select
                    name="difficulty_level"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="beginner">初級</option>
                    <option value="intermediate">中級</option>
                    <option value="advanced">高級</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    每堂課程價格
                  </label>
                  <input
                    name="pricing_per_lesson"
                    type="number"
                    required
                    defaultValue={0}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    name="is_public"
                    type="checkbox"
                    value="true"
                    id="is_public"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_public" className="ml-2 block text-sm text-gray-900">
                    設為公版課程
                  </label>
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button type="button" variant="outline" onClick={() => setShowAddCourse(false)}>
                  取消
                </Button>
                <Button type="submit">
                  建立課程
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
                  pricing_per_lesson: Number(formData.get('pricing_per_lesson')),
                  is_public: formData.get('is_public') === 'true'
                })
                setEditingCourse(null)
                fetchCourses()
              } catch (error) {
                console.error('Failed to update course:', error)
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
                    required
                    defaultValue={editingCourse.description}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    難度等級
                  </label>
                  <select
                    name="difficulty_level"
                    required
                    defaultValue={editingCourse.difficulty_level}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="beginner">初級</option>
                    <option value="intermediate">中級</option>
                    <option value="advanced">高級</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    每堂課程價格
                  </label>
                  <input
                    name="pricing_per_lesson"
                    type="number"
                    required
                    defaultValue={editingCourse.pricing_per_lesson}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    name="is_public"
                    type="checkbox"
                    value="true"
                    id="edit_is_public"
                    defaultChecked={editingCourse.is_public}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="edit_is_public" className="ml-2 block text-sm text-gray-900">
                    設為公版課程
                  </label>
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
                  is_active: true
                })
                setShowAddLesson(false)
                fetchCourseLessons(selectedCourse.id)
              } catch (error) {
                console.error('Failed to create lesson:', error)
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

      {/* 單元預覽對話框 */}
      {showLessonPreview && selectedLesson && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowLessonPreview(false)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">單元預覽</h2>
              <button
                onClick={() => setShowLessonPreview(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium">{selectedLesson.title}</h3>
                <div className="mt-2 flex items-center space-x-3 text-sm text-gray-500">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                    {activityTypeMap[selectedLesson.activity_type] || selectedLesson.activity_type}
                  </span>
                  <span>第 {selectedLesson.lesson_number} 課</span>
                  <span className="flex items-center">
                    <Clock className="w-4 h-4 mr-1" />
                    {selectedLesson.time_limit_minutes} 分鐘
                  </span>
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                    selectedLesson.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {selectedLesson.is_active ? '啟用' : '停用'}
                  </span>
                </div>
              </div>
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2">單元內容</h4>
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {selectedLesson.content ? JSON.stringify(selectedLesson.content, null, 2) : '尚無內容'}
                  </p>
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowLessonPreview(false)
                    setShowLessonEditor(true)
                  }}
                >
                  <Edit2 className="w-4 h-4 mr-1" />
                  編輯內容
                </Button>
                <Button onClick={() => setShowLessonPreview(false)}>
                  關閉
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 單元編輯對話框 */}
      {showLessonEditor && selectedLesson && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowLessonEditor(false)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">編輯單元內容</h2>
              <button
                onClick={() => setShowLessonEditor(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium">{selectedLesson.title}</h3>
                <div className="mt-2 flex items-center space-x-3 text-sm text-gray-500">
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
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2">編輯單元內容</h4>
                <div className="bg-gray-50 p-4 rounded-md">
                  <textarea
                    className="w-full h-40 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="請輸入單元內容..."
                    defaultValue={currentLessonContent?.content || ''}
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button variant="outline" onClick={() => setShowLessonEditor(false)}>
                  取消
                </Button>
                <Button onClick={() => setShowLessonEditor(false)}>
                  儲存變更
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      
    </div>
  )
}