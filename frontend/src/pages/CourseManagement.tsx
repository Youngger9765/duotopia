import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Plus, Search, BookOpen, Clock, Users, MoreVertical, Edit2, Trash2, Eye, Activity } from 'lucide-react'

interface Course {
  id: string
  title: string
  description: string
  grade: string
  totalActivities: number
  createdAt: string
  status: 'active' | 'draft'
}

function CourseManagement() {
  const [showAddCourse, setShowAddCourse] = useState(false)
  const [editingCourse, setEditingCourse] = useState<Course | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  
  const [courses, setCourses] = useState<Course[]>([
    {
      id: '1',
      title: '第一課 - 活動管理',
      description: '學習基本的活動管理技巧',
      grade: '初級',
      totalActivities: 4,
      createdAt: '2024-01-10',
      status: 'active'
    },
    {
      id: '2',
      title: '聽力克漏字',
      description: '提升聽力理解能力',
      grade: '中級',
      totalActivities: 3,
      createdAt: '2024-01-08',
      status: 'active'
    },
    {
      id: '3',
      title: '造句活動',
      description: '練習句型結構與文法',
      grade: '中級',
      totalActivities: 5,
      createdAt: '2024-01-05',
      status: 'active'
    },
    {
      id: '4',
      title: '錄音集',
      description: '口語表達練習',
      grade: '高級',
      totalActivities: 0,
      createdAt: '2024-01-03',
      status: 'draft'
    }
  ])

  const filteredCourses = courses.filter(course =>
    course.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    course.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">課程管理</h2>
        <p className="text-sm text-gray-500 mt-1">建立和管理您的課程內容</p>
      </div>

      {/* Action Bar */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜尋課程..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 w-64"
            />
          </div>
        </div>
        <Button onClick={() => setShowAddCourse(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新增課程
        </Button>
      </div>

      {/* Course List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {filteredCourses.map((course) => (
            <li key={course.id} className="hover:bg-gray-50">
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center min-w-0 flex-1">
                    <div className="flex-shrink-0">
                      <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
                        <BookOpen className="h-5 w-5 text-blue-600" />
                      </div>
                    </div>
                    <div className="ml-4 flex-1">
                      <div className="flex items-center">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {course.title}
                        </h3>
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          course.status === 'active' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {course.status === 'active' ? '已發布' : '草稿'}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-gray-500 truncate">
                        {course.description}
                      </p>
                      <div className="mt-2 flex items-center text-xs text-gray-500 space-x-4">
                        <span className="flex items-center">
                          <Activity className="w-3 h-3 mr-1" />
                          {course.totalActivities} 個活動
                        </span>
                        <span className="flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {course.createdAt}
                        </span>
                        <span className="flex items-center">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            {course.grade}
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="ml-4 flex items-center space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        // Navigate to course detail
                      }}
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      查看
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingCourse(course)}
                    >
                      <Edit2 className="w-4 h-4 mr-1" />
                      編輯
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Add Course Modal */}
      {showAddCourse && (
        <AddCourseModal
          onClose={() => setShowAddCourse(false)}
          onSave={(newCourse) => {
            setCourses([...courses, {
              ...newCourse,
              id: Date.now().toString(),
              totalActivities: 0,
              createdAt: new Date().toISOString().split('T')[0],
              status: 'draft'
            }])
            setShowAddCourse(false)
          }}
        />
      )}

      {/* Edit Course Modal */}
      {editingCourse && (
        <EditCourseModal
          course={editingCourse}
          onClose={() => setEditingCourse(null)}
          onSave={(updatedCourse) => {
            setCourses(courses.map(c =>
              c.id === updatedCourse.id ? updatedCourse : c
            ))
            setEditingCourse(null)
          }}
        />
      )}
    </div>
  )
}

function AddCourseModal({ 
  onClose, 
  onSave 
}: { 
  onClose: () => void
  onSave: (course: Partial<Course>) => void 
}) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    grade: '初級'
  })

  const handleSave = () => {
    if (formData.title && formData.description) {
      onSave(formData)
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">新增課程</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">課程標題 *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="請輸入課程標題"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">課程描述 *</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="請描述這個課程的內容和目標"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">難度等級</label>
            <select
              value={formData.grade}
              onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
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
            disabled={!formData.title || !formData.description}
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
        <h3 className="text-lg font-medium text-gray-900 mb-4">編輯課程</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">課程標題 *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">課程描述 *</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">難度等級</label>
            <select
              value={formData.grade}
              onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
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
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
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

export default CourseManagement