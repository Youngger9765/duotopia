import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Plus, Search, BookOpen, Clock, Users, MoreVertical, Edit2, Trash2, Eye, Activity, X, FileText, Calendar, ChevronLeft, ChevronRight } from 'lucide-react'
import { teacherApi, adminApi } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

interface Course {
  id: string
  title: string
  description: string
  grade: string
  totalActivities: number
  createdAt: string
  status: 'active' | 'draft'
  schoolId: string
  schoolName: string
}

interface CourseActivity {
  id: string
  title: string
  type: '活動管理' | '聽力克漏字' | '造句活動' | '錄音集' | '填空活動'
  courseId: string
  dueDate?: string
  totalStudents: number
  completedStudents: number
  createdAt: string
  status: 'active' | 'draft' | 'completed'
}

interface ActivityContent {
  id: string
  activityId: string
  content: string
  instructions: string
  resources?: string[]
}

function CourseManagement() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { toast } = useToast()
  const [showAddCourse, setShowAddCourse] = useState(false)
  const [showAddActivity, setShowAddActivity] = useState(false)
  const [editingCourse, setEditingCourse] = useState<Course | null>(null)
  const [editingActivity, setEditingActivity] = useState<CourseActivity | null>(null)
  const [showActivityPreview, setShowActivityPreview] = useState(false)
  const [showActivityEditor, setShowActivityEditor] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [selectedActivity, setSelectedActivity] = useState<CourseActivity | null>(null)
  const [searchCoursesTerm, setSearchCoursesTerm] = useState('')
  const [searchActivitiesTerm, setSearchActivitiesTerm] = useState('')
  const [selectedSchool, setSelectedSchool] = useState<string>('all')
  const [coursePanelCollapsed, setCoursePanelCollapsed] = useState(false)
  const [activityPanelCollapsed, setActivityPanelCollapsed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [courses, setCourses] = useState<Course[]>([])
  const [schools, setSchools] = useState<any[]>([])
  const [activities, setActivities] = useState<CourseActivity[]>([])

  const [activityContents, setActivityContents] = useState<ActivityContent[]>([])

  // Fetch data on component mount
  useEffect(() => {
    fetchCourses()
    fetchSchools()
  }, [])

  const fetchCourses = async () => {
    try {
      setLoading(true)
      const response = await teacherApi.getCourses()
      const formattedCourses = response.data.map((course: any) => ({
        id: course.id,
        title: course.title,
        description: course.description || '',
        grade: course.grade_level || course.grade || '初級',
        totalActivities: course.activity_count || 0,
        createdAt: course.created_at,
        status: course.status || 'active',
        schoolId: course.school_id,
        schoolName: course.school_name || ''
      }))
      setCourses(formattedCourses)
    } catch (error) {
      console.error('Failed to fetch courses:', error)
      toast({
        title: "錯誤",
        description: "無法載入課程資料",
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

  const fetchCourseActivities = async (courseId: string) => {
    try {
      const response = await teacherApi.getLessons(courseId)
      
      // Map backend activity types to Chinese names
      const typeMapping: Record<string, string> = {
        'reading_assessment': '活動管理',
        'listening_cloze': '聽力克漏字',
        'sentence_making': '造句活動',
        'speaking_practice': '錄音集',
        'speaking_quiz': '口語測驗',
        'speaking_scenario': '情境對話'
      }
      
      const formattedActivities = response.data.map((lesson: any) => ({
        id: lesson.id,
        title: lesson.title,
        type: typeMapping[lesson.activity_type] || lesson.type || '活動管理',
        courseId: lesson.course_id,
        dueDate: lesson.due_date,
        totalStudents: lesson.student_count || 0,
        completedStudents: lesson.completed_count || 0,
        createdAt: lesson.created_at,
        status: lesson.status || 'active'
      }))
      setActivities(formattedActivities)
    } catch (error) {
      console.error('Failed to fetch course activities:', error)
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
    const matchesSchool = selectedSchool === 'all' || course.schoolId === selectedSchool
    return matchesSearch && matchesSchool
  })

  // Auto-select first course if none selected
  useEffect(() => {
    if (!selectedCourse && filteredCourses.length > 0) {
      setSelectedCourse(filteredCourses[0])
    }
  }, [selectedCourse, filteredCourses.length])

  // Fetch activities when course is selected
  useEffect(() => {
    if (selectedCourse) {
      fetchCourseActivities(selectedCourse.id)
    }
  }, [selectedCourse?.id])

  const currentCourseActivities = selectedCourse 
    ? activities.filter(activity => 
        activity.courseId === selectedCourse.id &&
        (activity.title.toLowerCase().includes(searchActivitiesTerm.toLowerCase()) ||
         activity.type.toLowerCase().includes(searchActivitiesTerm.toLowerCase()))
      )
    : []

  const currentActivityContent = selectedActivity
    ? activityContents.find(content => content.activityId === selectedActivity.id) || {
        id: selectedActivity.id,
        activityId: selectedActivity.id,
        content: '活動內容尚未設定',
        instructions: '請完成以下活動',
        resources: []
      }
    : null

  // Update course activity count when activities change
  const updateCourseActivityCount = (courseId: string) => {
    const count = activities.filter(a => a.courseId === courseId).length
    setCourses(prev => prev.map(c => 
      c.id === courseId ? { ...c, totalActivities: count } : c
    ))
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">課程管理</h2>
        <p className="text-sm text-gray-500 mt-1">建立和管理您的課程內容</p>
      </div>

      {/* School Filter */}
      <div className="mb-4 bg-white p-4 rounded-lg shadow">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">選擇學校：</label>
          <select
            value={selectedSchool}
            onChange={(e) => {
              setSelectedSchool(e.target.value)
              setSelectedCourse(null)
              setSelectedActivity(null)
            }}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">所有學校</option>
            {schools.map(inst => (
              <option key={inst.id} value={inst.id}>{inst.name}</option>
            ))}
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
                    setSelectedActivity(null)
                  }}
                  className={`p-3 border-b cursor-pointer hover:bg-gray-50 ${
                    selectedCourse?.id === course.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                  }`}
                >
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                      <h4 className="font-medium text-sm text-gray-900 truncate">{course.title}</h4>
                      <span className={`ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                        course.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {course.status === 'active' ? '已發布' : '草稿'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1 truncate">{course.description}</p>
                    <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                      <span>{course.schoolName}</span>
                      <span className="flex items-center">
                        <Activity className="w-3 h-3 mr-1" />
                        {course.totalActivities} 個活動
                      </span>
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                        {course.grade}
                      </span>
                    </div>
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
                          try {
                            await teacherApi.deleteCourse(course.id)
                            toast({
                              title: "成功",
                              description: "課程已刪除",
                            })
                            fetchCourses()
                            if (selectedCourse?.id === course.id) {
                              setSelectedCourse(null)
                              setSelectedActivity(null)
                            }
                          } catch (error: any) {
                            toast({
                              title: "錯誤",
                              description: error.response?.data?.detail || "無法刪除課程",
                              variant: "destructive",
                            })
                          }
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

        {/* Second Panel - Activities */}
        <div className={`${activityPanelCollapsed ? 'w-12' : 'w-96'} bg-white rounded-lg shadow overflow-hidden flex flex-col transition-all duration-300`}>
          {selectedCourse ? (
            <>
              {activityPanelCollapsed ? (
                <div className="p-2 border-b flex flex-col items-center">
                  <button
                    onClick={() => setActivityPanelCollapsed(false)}
                    className="p-2 hover:bg-gray-100 rounded-md"
                    title="展開活動列表"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setShowAddActivity(true)}
                    className="p-2 hover:bg-gray-100 rounded-md mt-2"
                    title="新增活動"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="p-4 border-b">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-base font-medium">{selectedCourse.title} - 活動</h3>
                      <p className="text-xs text-gray-500">{selectedCourse.schoolName}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" onClick={() => setShowAddActivity(true)}>
                        <Plus className="w-4 h-4 mr-1" />
                        新增活動
                      </Button>
                      <button
                        onClick={() => setActivityPanelCollapsed(true)}
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
                      placeholder="搜尋活動..."
                      value={searchActivitiesTerm}
                      onChange={(e) => setSearchActivitiesTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                  </div>
                </div>
              )}

              {!activityPanelCollapsed && (
                <div className="flex-1 overflow-y-auto">
                  {currentCourseActivities.length > 0 ? (
                  <div className="divide-y divide-gray-200">
                    {currentCourseActivities.map((activity) => (
                      <div 
                        key={activity.id} 
                        onClick={() => setSelectedActivity(activity)}
                        className={`p-3 hover:bg-gray-50 cursor-pointer ${
                          selectedActivity?.id === activity.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex items-start space-x-2">
                            <div className="flex-shrink-0">
                              <div className="h-8 w-8 rounded-lg bg-blue-100 flex items-center justify-center">
                                <FileText className="h-4 w-4 text-blue-600" />
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="text-sm font-medium text-gray-900 truncate">{activity.title}</h4>
                              <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                  {activity.type}
                                </span>
                                <span className="flex items-center">
                                  <Users className="w-3 h-3 mr-1" />
                                  {activity.completedStudents}/{activity.totalStudents} 完成
                                </span>
                                {activity.dueDate && (
                                  <span className="flex items-center">
                                    <Calendar className="w-3 h-3 mr-1" />
                                    {activity.dueDate}
                                  </span>
                                )}
                                <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                                  activity.status === 'active' 
                                    ? 'bg-green-100 text-green-800' 
                                    : activity.status === 'completed'
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {activity.status === 'active' ? '已發布' : activity.status === 'completed' ? '已完成' : '草稿'}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-1 ml-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                setEditingActivity(activity)
                              }}
                              className="p-1 hover:bg-gray-200 rounded"
                            >
                              <Edit2 className="w-3 h-3 text-gray-600" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                setActivities(prev => prev.filter(a => a.id !== activity.id))
                                updateCourseActivityCount(selectedCourse.id)
                                if (selectedActivity?.id === activity.id) {
                                  setSelectedActivity(null)
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
                      <p className="text-sm mb-2">尚無活動</p>
                      <p className="text-xs">點擊「新增活動」開始添加活動</p>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <p className="text-sm">請選擇一個課程查看活動</p>
            </div>
          )}
        </div>

        {/* Third Panel - Activity Content */}
        <div className="flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col">
          {selectedActivity && currentActivityContent ? (
            <>
              <div className="p-4 border-b">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-medium">{selectedActivity.title}</h3>
                    <div className="mt-1 flex items-center space-x-3 text-sm text-gray-500">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                        {selectedActivity.type}
                      </span>
                      <span>{selectedCourse?.title}</span>
                      {selectedActivity.dueDate && (
                        <span className="flex items-center">
                          <Calendar className="w-4 h-4 mr-1" />
                          截止日期：{selectedActivity.dueDate}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => setShowActivityPreview(true)}
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      預覽
                    </Button>
                    <Button 
                      size="sm"
                      onClick={() => setShowActivityEditor(true)}
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
                    <h4 className="text-base font-medium text-gray-900 mb-2">活動說明</h4>
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <p className="text-sm text-blue-800">{currentActivityContent.instructions}</p>
                    </div>
                  </div>

                  {/* Content Section */}
                  <div className="mb-6">
                    <h4 className="text-base font-medium text-gray-900 mb-2">活動內容</h4>
                    <div className="bg-gray-50 p-6 rounded-lg">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{currentActivityContent.content}</p>
                    </div>
                  </div>

                  {/* Resources Section */}
                  {currentActivityContent.resources && currentActivityContent.resources.length > 0 && (
                    <div className="mb-6">
                      <h4 className="text-base font-medium text-gray-900 mb-2">相關資源</h4>
                      <div className="grid grid-cols-1 gap-3">
                        {currentActivityContent.resources.map((resource, index) => (
                          <div key={index} className="flex items-center p-3 bg-white border border-gray-200 rounded-lg hover:shadow-sm">
                            <FileText className="w-5 h-5 text-gray-400 mr-3" />
                            <span className="text-sm text-gray-700">{resource}</span>
                            <Button size="sm" variant="ghost" className="ml-auto">
                              下載
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Statistics Section */}
                  <div className="mb-6">
                    <h4 className="text-base font-medium text-gray-900 mb-2">完成統計</h4>
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600">完成進度</p>
                          <p className="text-2xl font-semibold text-gray-900">
                            {selectedActivity.completedStudents}/{selectedActivity.totalStudents}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-600">完成率</p>
                          <p className="text-2xl font-semibold text-green-600">
                            {selectedActivity.totalStudents > 0 
                              ? Math.round((selectedActivity.completedStudents / selectedActivity.totalStudents) * 100) 
                              : 0}%
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                <p className="text-sm">請選擇一個活動查看內容</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add Course Modal */}
      {showAddCourse && (
        <AddCourseModal
          schools={schools}
          onClose={() => setShowAddCourse(false)}
          onSave={async (newCourse) => {
            try {
              const courseData = {
                title: newCourse.title,
                description: newCourse.description,
                grade_level: newCourse.grade,
                school_id: newCourse.schoolId,
                status: 'active'
              }
              
              await teacherApi.createCourse(courseData)
              toast({
                title: "成功",
                description: "課程已建立",
              })
              fetchCourses()
              setShowAddCourse(false)
            } catch (error: any) {
              toast({
                title: "錯誤",
                description: error.response?.data?.detail || "無法建立課程",
                variant: "destructive",
              })
            }
          }}
        />
      )}

      {/* Edit Course Modal */}
      {editingCourse && (
        <EditCourseModal
          course={editingCourse}
          onClose={() => setEditingCourse(null)}
          onSave={async (updatedCourse) => {
            try {
              const updateData = {
                title: updatedCourse.title,
                description: updatedCourse.description,
                grade_level: updatedCourse.grade,
                status: updatedCourse.status
              }
              
              await teacherApi.updateCourse(updatedCourse.id, updateData)
              toast({
                title: "成功",
                description: "課程已更新",
              })
              fetchCourses()
              setEditingCourse(null)
            } catch (error: any) {
              toast({
                title: "錯誤",
                description: error.response?.data?.detail || "無法更新課程",
                variant: "destructive",
              })
            }
          }}
        />
      )}

      {/* Add Activity Modal */}
      {showAddActivity && selectedCourse && (
        <AddActivityModal
          courseId={selectedCourse.id}
          courseName={selectedCourse.title}
          onClose={() => setShowAddActivity(false)}
          onSave={async (newActivity) => {
            try {
              // Map Chinese activity types to backend enums
              const typeMapping: Record<string, string> = {
                '活動管理': 'reading_assessment',
                '聽力克漏字': 'listening_cloze',
                '造句活動': 'sentence_making',
                '錄音集': 'speaking_practice',
                '填空活動': 'reading_assessment'
              }
              
              // Get existing lessons count to determine lesson number
              const existingLessons = activities.length
              
              const activityData = {
                title: newActivity.title,
                lesson_number: existingLessons + 1,
                activity_type: typeMapping[newActivity.type] || 'reading_assessment',
                content: {
                  type: 'activity',
                  instructions: '請完成以下活動',
                  sections: []
                },
                time_limit_minutes: 30
              }
              
              await teacherApi.createLesson(selectedCourse.id, activityData)
              toast({
                title: "成功",
                description: "活動已建立",
              })
              fetchCourseActivities(selectedCourse.id)
              setShowAddActivity(false)
            } catch (error: any) {
              toast({
                title: "錯誤",
                description: error.response?.data?.detail || "無法建立活動",
                variant: "destructive",
              })
            }
          }}
        />
      )}

      {/* Edit Activity Modal */}
      {editingActivity && (
        <EditActivityModal
          activity={editingActivity}
          onClose={() => setEditingActivity(null)}
          onSave={(updatedActivity) => {
            setActivities(activities.map(a =>
              a.id === updatedActivity.id ? updatedActivity : a
            ))
            setEditingActivity(null)
          }}
        />
      )}

      {/* Activity Preview Modal */}
      {showActivityPreview && selectedActivity && (
        <ActivityPreviewModal
          activity={selectedActivity}
          content={currentActivityContent}
          onClose={() => setShowActivityPreview(false)}
        />
      )}

      {/* Activity Editor Modal */}
      {showActivityEditor && selectedActivity && (
        <ActivityEditorModal
          activity={selectedActivity}
          content={currentActivityContent}
          onClose={() => setShowActivityEditor(false)}
          onSave={(updatedContent) => {
            // Update activity content
            setActivityContents(prev => 
              prev.map(content => 
                content.activityId === selectedActivity.id 
                  ? updatedContent 
                  : content
              )
            )
            setShowActivityEditor(false)
          }}
        />
      )}
    </div>
  )
}

function AddCourseModal({ 
  schools,
  onClose, 
  onSave 
}: { 
  schools: any[]
  onClose: () => void
  onSave: (course: Partial<Course>) => void 
}) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    grade: '初級',
    schoolId: '',
    schoolName: ''
  })

  const handleSave = () => {
    if (formData.title && formData.description && formData.schoolId) {
      onSave(formData)
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">新增課程</h3>
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
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="">請選擇學校</option>
              {schools.map(inst => (
                <option key={inst.id} value={inst.id}>{inst.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">課程標題 *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="請輸入課程標題"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">課程描述 *</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="請描述這個課程的內容和目標"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">難度等級</label>
            <select
              value={formData.grade}
              onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="初級">初級</option>
              <option value="中級">中級</option>
              <option value="高級">高級</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={handleSave} 
            className="flex-1"
            disabled={!formData.title || !formData.description || !formData.schoolId}
          >
            建立課程
          </Button>
        </div>
      </div>
    </div>
  )
}

function EditCourseModal({ 
  course,
  onClose, 
  onSave 
}: { 
  course: Course
  onClose: () => void
  onSave: (course: Course) => void 
}) {
  const [formData, setFormData] = useState({
    title: course.title,
    description: course.description,
    grade: course.grade,
    status: course.status
  })

  const handleSave = () => {
    onSave({
      ...course,
      ...formData
    })
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">編輯課程</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">課程標題 *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">課程描述 *</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">難度等級</label>
            <select
              value={formData.grade}
              onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="初級">初級</option>
              <option value="中級">中級</option>
              <option value="高級">高級</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">狀態</label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value as 'active' | 'draft' })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="draft">草稿</option>
              <option value="active">已發布</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button onClick={handleSave} className="flex-1">
            儲存變更
          </Button>
        </div>
      </div>
    </div>
  )
}

function AddActivityModal({ 
  courseId,
  courseName,
  onClose, 
  onSave 
}: { 
  courseId: string
  courseName: string
  onClose: () => void
  onSave: (activity: Partial<CourseActivity>) => void 
}) {
  const [formData, setFormData] = useState({
    title: '',
    type: '活動管理' as CourseActivity['type'],
    dueDate: ''
  })

  const activityTypes: CourseActivity['type'][] = ['活動管理', '聽力克漏字', '造句活動', '錄音集', '填空活動']

  const handleSave = () => {
    if (formData.title && formData.type) {
      onSave(formData)
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">新增活動</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mb-4 bg-blue-50 p-3 rounded-md">
          <p className="text-sm text-blue-700">
            課程：<span className="font-medium">{courseName}</span>
          </p>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">活動標題 *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="請輸入活動標題"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">活動類型 *</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as CourseActivity['type'] })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              {activityTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">截止日期（選填）</label>
            <input
              type="date"
              value={formData.dueDate}
              onChange={(e) => setFormData({ ...formData, dueDate: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={handleSave} 
            className="flex-1"
            disabled={!formData.title || !formData.type}
          >
            建立活動
          </Button>
        </div>
      </div>
    </div>
  )
}

function EditActivityModal({ 
  activity,
  onClose, 
  onSave 
}: { 
  activity: CourseActivity
  onClose: () => void
  onSave: (activity: CourseActivity) => void 
}) {
  const [formData, setFormData] = useState({
    title: activity.title,
    type: activity.type,
    dueDate: activity.dueDate || '',
    status: activity.status
  })

  const activityTypes: CourseActivity['type'][] = ['活動管理', '聽力克漏字', '造句活動', '錄音集', '填空活動']

  const handleSave = () => {
    onSave({
      ...activity,
      ...formData
    })
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">編輯活動</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">活動標題 *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">活動類型 *</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as CourseActivity['type'] })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              {activityTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">截止日期</label>
            <input
              type="date"
              value={formData.dueDate}
              onChange={(e) => setFormData({ ...formData, dueDate: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">狀態</label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value as CourseActivity['status'] })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="draft">草稿</option>
              <option value="active">已發布</option>
              <option value="completed">已完成</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button onClick={handleSave} className="flex-1">
            儲存變更
          </Button>
        </div>
      </div>
    </div>
  )
}

function ActivityPreviewModal({
  activity,
  content,
  onClose
}: {
  activity: CourseActivity
  content: ActivityContent | null
  onClose: () => void
}) {
  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h3 className="text-lg font-medium text-gray-900">活動預覽</h3>
            <p className="text-sm text-gray-500">{activity.title}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <div className="mb-6">
            <h4 className="text-base font-medium text-gray-900 mb-2">活動說明</h4>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-800">
                {content?.instructions || '請完成以下活動'}
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h4 className="text-base font-medium text-gray-900 mb-2">活動內容</h4>
            <div className="bg-gray-50 p-6 rounded-lg">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {content?.content || '活動內容尚未設定'}
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h4 className="text-base font-medium text-gray-900 mb-2">活動資訊</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white p-4 border border-gray-200 rounded-lg">
                <p className="text-sm text-gray-600">活動類型</p>
                <p className="font-medium">{activity.type}</p>
              </div>
              <div className="bg-white p-4 border border-gray-200 rounded-lg">
                <p className="text-sm text-gray-600">完成進度</p>
                <p className="font-medium">{activity.completedStudents}/{activity.totalStudents}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ActivityEditorModal({
  activity,
  content,
  onClose,
  onSave
}: {
  activity: CourseActivity
  content: ActivityContent | null
  onClose: () => void
  onSave: (content: ActivityContent) => void
}) {
  const [formData, setFormData] = useState({
    instructions: content?.instructions || '請完成以下活動',
    content: content?.content || '活動內容尚未設定',
    resources: content?.resources || []
  })

  const handleSave = () => {
    const updatedContent: ActivityContent = {
      id: content?.id || activity.id,
      activityId: activity.id,
      instructions: formData.instructions,
      content: formData.content,
      resources: formData.resources
    }
    onSave(updatedContent)
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h3 className="text-lg font-medium text-gray-900">編輯活動內容</h3>
            <p className="text-sm text-gray-500">{activity.title}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">活動說明</label>
              <textarea
                value={formData.instructions}
                onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="請輸入活動說明..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">活動內容</label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                rows={8}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="請輸入活動內容..."
              />
            </div>
          </div>
        </div>

        <div className="px-6 py-4 border-t flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button onClick={handleSave} className="flex-1">
            儲存變更
          </Button>
        </div>
      </div>
    </div>
  )
}

export default CourseManagement