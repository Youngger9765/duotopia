import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, Users, DollarSign, Edit2, Trash2, Search, BarChart, Calendar, MapPin, X, UserPlus, Settings } from 'lucide-react'
import { api } from '@/lib/api'

interface Classroom {
  id: string
  name: string
  grade_level: string
  location: string
  pricing: number
  max_students: number
  student_count?: number
  weekly_schedule?: any
  description?: string
}

interface Student {
  id: string
  full_name: string
  email: string
}

interface ClassroomStats {
  total_students: number
  active_assignments: number
  completion_rate: number
  average_score: number
}

export default function IndividualClassrooms() {
  const navigate = useNavigate()
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddClassroom, setShowAddClassroom] = useState(false)
  const [editingClassroom, setEditingClassroom] = useState<Classroom | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [showManageStudents, setShowManageStudents] = useState<Classroom | null>(null)
  const [showStats, setShowStats] = useState<Classroom | null>(null)
  const [classroomStudents, setClassroomStudents] = useState<Student[]>([])
  const [classroomStats, setClassroomStats] = useState<ClassroomStats | null>(null)

  useEffect(() => {
    fetchClassrooms()
  }, [])

  const fetchClassrooms = async () => {
    try {
      const response = await api.get('/api/individual/classrooms')
      setClassrooms(response.data)
    } catch (error) {
      console.error('Failed to fetch classrooms:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteClassroom = async (classroomId: string) => {
    try {
      await api.delete(`/api/individual/classrooms/${classroomId}`)
      setClassrooms(prev => prev.filter(c => c.id !== classroomId))
    } catch (error) {
      console.error('Failed to delete classroom:', error)
      alert('刪除教室失敗')
    }
  }

  const fetchClassroomStudents = async (classroomId: string) => {
    try {
      const response = await api.get(`/api/individual/classrooms/${classroomId}/students`)
      setClassroomStudents(response.data)
    } catch (error) {
      console.error('Failed to fetch classroom students:', error)
    }
  }

  const fetchClassroomStats = async (classroomId: string) => {
    try {
      const response = await api.get(`/api/individual/classrooms/${classroomId}/stats`)
      setClassroomStats(response.data)
    } catch (error) {
      console.error('Failed to fetch classroom stats:', error)
    }
  }

  const filteredClassrooms = classrooms.filter(classroom =>
    classroom.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    classroom.location.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return <div>載入中...</div>
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">教室管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理您的教室和學生</p>
      </div>

      {/* 操作列 */}
      <div className="mb-4 bg-white p-4 rounded-lg shadow">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="搜尋教室名稱或地點..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <Button onClick={() => setShowAddClassroom(true)}>
            <Plus className="w-4 h-4 mr-1" />
            建立新教室
          </Button>
        </div>
      </div>

      {/* 教室卡片列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredClassrooms.map((classroom) => (
          <Card 
            key={classroom.id} 
            className="hover:shadow-lg transition-shadow"
          >
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="cursor-pointer" onClick={() => navigate(`/individual/classrooms/${classroom.id}`)}>
                  {classroom.name}
                </span>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => setEditingClassroom(classroom)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <Edit2 className="h-4 w-4 text-gray-600" />
                  </button>
                  <button
                    onClick={() => {
                      if (window.confirm('確定要刪除此教室嗎？')) {
                        handleDeleteClassroom(classroom.id)
                      }
                    }}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <Trash2 className="h-4 w-4 text-red-600" />
                  </button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center text-sm text-gray-600">
                  <Users className="h-4 w-4 mr-2" />
                  學生人數: {classroom.student_count || 0}/{classroom.max_students || 30}
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Calendar className="h-4 w-4 mr-2" />
                  年級: {classroom.grade_level}
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <MapPin className="h-4 w-4 mr-2" />
                  地點: {classroom.location}
                </div>
                <div className="flex items-center text-sm font-medium text-green-600">
                  <DollarSign className="h-4 w-4 mr-2" />
                  {classroom.pricing}/堂
                </div>
              </div>
              
              <div className="mt-4 flex flex-wrap gap-2">
                <Button 
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setShowManageStudents(classroom)
                    fetchClassroomStudents(classroom.id)
                  }}
                >
                  <UserPlus className="h-3 w-3 mr-1" />
                  管理學生
                </Button>
                <Button 
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setShowStats(classroom)
                    fetchClassroomStats(classroom.id)
                  }}
                >
                  <BarChart className="h-3 w-3 mr-1" />
                  統計
                </Button>
                <Button 
                  size="sm"
                  onClick={() => navigate(`/individual/classrooms/${classroom.id}`)}
                >
                  進入教室
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {filteredClassrooms.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          {searchTerm ? '沒有找到符合條件的教室' : '尚未建立任何教室'}
        </div>
      )}

      {/* 新增教室對話框 */}
      {showAddClassroom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowAddClassroom(false)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">建立新教室</h2>
              <button
                onClick={() => setShowAddClassroom(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              try {
                await api.post('/api/individual/classrooms', {
                  name: formData.get('name'),
                  grade_level: formData.get('grade_level'),
                  location: formData.get('location'),
                  pricing: Number(formData.get('pricing')),
                  max_students: Number(formData.get('max_students')),
                  description: formData.get('description')
                })
                setShowAddClassroom(false)
                fetchClassrooms()
              } catch (error) {
                console.error('Failed to create classroom:', error)
                alert('建立教室失敗')
              }
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    教室名稱 <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="name"
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="例如：六年級英語班"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    年級 <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="grade_level"
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="例如：六年級"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    地點 <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="location"
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="例如：台北市大安區"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      每堂課程價格 <span className="text-red-500">*</span>
                    </label>
                    <input
                      name="pricing"
                      type="number"
                      required
                      defaultValue={500}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      最大學生數 <span className="text-red-500">*</span>
                    </label>
                    <input
                      name="max_students"
                      type="number"
                      required
                      defaultValue={30}
                      min={1}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    教室描述
                  </label>
                  <textarea
                    name="description"
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="請描述教室特色..."
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button type="button" variant="outline" onClick={() => setShowAddClassroom(false)}>
                  取消
                </Button>
                <Button type="submit">
                  建立教室
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 編輯教室對話框 */}
      {editingClassroom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setEditingClassroom(null)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">編輯教室</h2>
              <button
                onClick={() => setEditingClassroom(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              try {
                await api.put(`/api/individual/classrooms/${editingClassroom.id}`, {
                  name: formData.get('name'),
                  grade_level: formData.get('grade_level'),
                  location: formData.get('location'),
                  pricing: Number(formData.get('pricing')),
                  max_students: Number(formData.get('max_students')),
                  description: formData.get('description')
                })
                setEditingClassroom(null)
                fetchClassrooms()
              } catch (error) {
                console.error('Failed to update classroom:', error)
                alert('更新教室失敗')
              }
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    教室名稱 <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="name"
                    type="text"
                    required
                    defaultValue={editingClassroom.name}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    年級 <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="grade_level"
                    type="text"
                    required
                    defaultValue={editingClassroom.grade_level}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    地點 <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="location"
                    type="text"
                    required
                    defaultValue={editingClassroom.location}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      每堂課程價格 <span className="text-red-500">*</span>
                    </label>
                    <input
                      name="pricing"
                      type="number"
                      required
                      defaultValue={editingClassroom.pricing}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      最大學生數 <span className="text-red-500">*</span>
                    </label>
                    <input
                      name="max_students"
                      type="number"
                      required
                      defaultValue={editingClassroom.max_students}
                      min={1}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    教室描述
                  </label>
                  <textarea
                    name="description"
                    rows={3}
                    defaultValue={editingClassroom.description}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button type="button" variant="outline" onClick={() => setEditingClassroom(null)}>
                  取消
                </Button>
                <Button type="submit">
                  更新教室
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 管理學生對話框 */}
      {showManageStudents && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowManageStudents(null)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">管理學生 - {showManageStudents.name}</h2>
              <button
                onClick={() => setShowManageStudents(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-600">
                  目前學生人數: <span className="font-medium">{classroomStudents.length}</span> / {showManageStudents.max_students}
                </p>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">學生列表</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {classroomStudents.map((student) => (
                    <div key={student.id} className="flex items-center justify-between p-2 bg-white border rounded">
                      <div>
                        <p className="text-sm font-medium">{student.full_name}</p>
                        <p className="text-xs text-gray-500">{student.email}</p>
                      </div>
                      <button
                        onClick={async () => {
                          try {
                            await api.delete(`/api/individual/classrooms/${showManageStudents.id}/students/${student.id}`)
                            setClassroomStudents(prev => prev.filter(s => s.id !== student.id))
                          } catch (error) {
                            console.error('Failed to remove student:', error)
                            alert('移除學生失敗')
                          }
                        }}
                        className="text-red-600 hover:text-red-900"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                  {classroomStudents.length === 0 && (
                    <p className="text-sm text-gray-500 text-center py-4">尚無學生</p>
                  )}
                </div>
              </div>
              
              <div className="mt-4">
                <Button
                  variant="outline"
                  onClick={() => navigate('/individual/students?action=assign&classroom=' + showManageStudents.id)}
                  className="w-full"
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  新增學生到此教室
                </Button>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end">
              <Button onClick={() => setShowManageStudents(null)}>
                關閉
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 查看統計對話框 */}
      {showStats && classroomStats && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowStats(null)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">教室統計 - {showStats.name}</h2>
              <button
                onClick={() => setShowStats(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-blue-600 mb-1">學生總數</p>
                  <p className="text-2xl font-bold text-blue-900">{classroomStats.total_students}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-green-600 mb-1">進行中作業</p>
                  <p className="text-2xl font-bold text-green-900">{classroomStats.active_assignments}</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <p className="text-sm text-purple-600 mb-1">作業完成率</p>
                  <p className="text-2xl font-bold text-purple-900">{classroomStats.completion_rate}%</p>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <p className="text-sm text-yellow-600 mb-1">平均分數</p>
                  <p className="text-2xl font-bold text-yellow-900">{classroomStats.average_score}</p>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <Button
                  variant="outline"
                  onClick={() => navigate(`/individual/classrooms/${showStats.id}`)}
                >
                  查看詳細
                </Button>
                <Button onClick={() => setShowStats(null)}>
                  關閉
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}