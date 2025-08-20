import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Plus, Search, BookOpen, Clock, Users, Edit2, Trash2, Eye, Activity, X, FileText, Calendar, ChevronLeft, ChevronRight, DollarSign } from 'lucide-react'
import { api } from '@/lib/api'

interface Course {
  id: string
  title: string
  description: string
  difficulty_level: string
  pricing_per_unit: number
  unit_count: number
  classroom_id?: string
  classroom_name?: string
  is_public: boolean
  teacher_name: string
  copied_from_title?: string
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

export default function IndividualCourses() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showAddCourse, setShowAddCourse] = useState(false)
  const [showAddUnit, setShowAddUnit] = useState(false)
  const [editingCourse, setEditingCourse] = useState<Course | null>(null)
  const [editingUnit, setEditingUnit] = useState<Unit | null>(null)
  const [showUnitPreview, setShowUnitPreview] = useState(false)
  const [showUnitEditor, setShowUnitEditor] = useState(false)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null)
  const [searchCoursesTerm, setSearchCoursesTerm] = useState('')
  const [searchUnitsTerm, setSearchUnitsTerm] = useState('')
  const [courseFilter, setCourseFilter] = useState<string>('all') // all, public, classroom
  const [coursePanelCollapsed, setCoursePanelCollapsed] = useState(false)
  const [unitPanelCollapsed, setUnitPanelCollapsed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [courses, setCourses] = useState<Course[]>([])
  const [units, setUnits] = useState<Unit[]>([])
  const [unitContents, setUnitContents] = useState<UnitContent[]>([])

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

  const fetchCourseUnits = async (courseId: string) => {
    try {
      const response = await api.get(`/api/individual/courses/${courseId}/lessons`)
      setUnits(response.data)
    } catch (error) {
      console.error('Failed to fetch course units:', error)
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
      fetchCourseUnits(selectedCourse.id)
    }
  }, [selectedCourse?.id])

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
              setSelectedUnit(null)
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
                          {course.unit_count} 個單元
                        </span>
                        <span className="flex items-center text-green-600">
                          <DollarSign className="w-3 h-3 mr-1" />
                          {course.pricing_per_unit}/堂
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
                            // Delete course logic here
                            console.log('Delete course:', course.id)
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
                        {selectedCourse.classroom_name || '公版課程'} • {selectedCourse.difficulty_level}
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
                                  setEditingUnit(unit)
                                }}
                                className="p-1 hover:bg-gray-200 rounded"
                              >
                                <Edit2 className="w-3 h-3 text-gray-600" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (window.confirm('確定要刪除此單元嗎？')) {
                                    setUnits(prev => prev.filter(l => l.id !== unit.id))
                                    if (selectedUnit?.id === unit.id) {
                                      setSelectedUnit(null)
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

      {/* Modals would go here - Add Course, Edit Course, Add Lesson, Edit Lesson, etc. */}
      {/* For brevity, I'm not including all modal implementations */}
      
    </div>
  )
}