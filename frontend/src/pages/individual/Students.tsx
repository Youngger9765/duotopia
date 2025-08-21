import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Plus, Search, Edit2, Trash2, Users, Upload, Download, X, Eye, Mail, Calendar, Key, RotateCcw, Copy, MoreVertical } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface Student {
  id: string
  full_name: string
  email: string
  birth_date: string
  referred_by: string
  learning_goals: string
  classroom_names?: string[]
  classroom_ids?: string[]
  is_default_password?: boolean
  default_password?: string
}

interface Classroom {
  id: string
  name: string
}

export default function IndividualStudents() {
  const { toast } = useToast()
  const [students, setStudents] = useState<Student[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddStudent, setShowAddStudent] = useState(false)
  const [editingStudent, setEditingStudent] = useState<Student | null>(null)
  const [showBulkImport, setShowBulkImport] = useState(false)
  const [selectedStudents, setSelectedStudents] = useState<string[]>([])
  const [showAssignClassroom, setShowAssignClassroom] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [classrooms, setClassrooms] = useState<Classroom[]>([])
  const [viewingStudent, setViewingStudent] = useState<Student | null>(null)
  const [assigningStudent, setAssigningStudent] = useState<Student | null>(null)
  const [studentClassrooms, setStudentClassrooms] = useState<{[key: string]: string[]}>({})

  useEffect(() => {
    fetchStudents()
    fetchClassrooms()
  }, [])

  const fetchStudents = async () => {
    try {
      const response = await api.get('/api/individual/students')
      setStudents(response.data)
    } catch (error) {
      console.error('Failed to fetch students:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchClassrooms = async () => {
    try {
      const response = await api.get('/api/individual/classrooms')
      setClassrooms(response.data)
    } catch (error) {
      console.error('Failed to fetch classrooms:', error)
    }
  }

  const fetchStudentClassrooms = async (studentId: string) => {
    try {
      const response = await api.get(`/api/individual/students/${studentId}/classrooms`)
      setStudentClassrooms(prev => ({
        ...prev,
        [studentId]: response.data.classroom_ids || []
      }))
      return response.data.classroom_ids || []
    } catch (error) {
      console.error('Failed to fetch student classrooms:', error)
      return []
    }
  }

  const handleDeleteStudent = async (studentId: string) => {
    try {
      await api.delete(`/api/individual/students/${studentId}`)
      setStudents(prev => prev.filter(s => s.id !== studentId))
    } catch (error) {
      console.error('Failed to delete student:', error)
      toast({
        variant: "destructive",
        title: "刪除失敗",
        description: "刪除學生失敗，請稍後再試"
      })
    }
  }

  const handleAssignClassrooms = async (studentIds: string[], classroomIds: string[]) => {
    try {
      const response = await api.post('/api/individual/students/assign-classrooms', {
        student_ids: studentIds,
        classroom_ids: classroomIds
      })
      
      fetchStudents()
      setSelectedStudents([])
      setShowAssignClassroom(false)
      
      // 顯示成功訊息
      if (response.data.errors && response.data.errors.length > 0) {
        toast({
          variant: "default",
          title: "部分成功",
          description: `${response.data.message}\n\n錯誤：\n${response.data.errors.join('\n')}`
        })
      } else {
        toast({
          title: "分配成功",
          description: response.data.message
        })
      }
    } catch (error: any) {
      console.error('Failed to assign classrooms:', error)
      toast({
        variant: "destructive",
        title: "分配失敗",
        description: error.response?.data?.detail || '分配班級失敗'
      })
    }
  }

  const handleResetPassword = async (student: Student) => {
    if (!window.confirm(`確定要重置 ${student.full_name} 的密碼為預設密碼（生日）嗎？`)) {
      return
    }

    try {
      const response = await api.post(`/api/individual/students/${student.id}/reset-password`)
      
      // 更新本地狀態
      setStudents(prev => prev.map(s => 
        s.id === student.id 
          ? { 
              ...s, 
              is_default_password: true, 
              default_password: response.data.default_password 
            }
          : s
      ))
      
      // 顯示成功訊息
      toast({
        title: "密碼重置成功",
        description: `${response.data.message}\n\n新密碼：${response.data.default_password}`
      })
    } catch (error: any) {
      console.error('Failed to reset password:', error)
      toast({
        variant: "destructive",
        title: "重置失敗",
        description: error.response?.data?.detail || '重置密碼失敗'
      })
    }
  }

  const filteredStudents = students.filter(student => 
    student.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    student.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return <div>載入中...</div>
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">學生管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理您的學生資料和班級分配</p>
      </div>

      {/* 操作列 */}
      <div className="mb-4 bg-white p-4 rounded-lg shadow">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="搜尋學生姓名或 Email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setShowBulkImport(true)}
            >
              <Upload className="w-4 h-4 mr-1" />
              批量匯入
            </Button>
            {selectedStudents.length > 0 && (
              <Button
                variant="outline"
                onClick={() => setShowAssignClassroom(true)}
              >
                <Users className="w-4 h-4 mr-1" />
                分配班級 ({selectedStudents.length})
              </Button>
            )}
            <Button onClick={() => setShowAddStudent(true)}>
              <Plus className="w-4 h-4 mr-1" />
              新增學生
            </Button>
          </div>
        </div>
      </div>

      {/* 學生列表 */}
      <div className="flex-1 bg-white shadow overflow-hidden rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  checked={selectedStudents.length === filteredStudents.length && filteredStudents.length > 0}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedStudents(filteredStudents.map(s => s.id))
                    } else {
                      setSelectedStudents([])
                    }
                  }}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                學生資料
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                所屬班級
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                加入方式
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                學習目標
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                密碼狀態
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredStudents.map((student) => (
              <tr key={student.id} className="hover:bg-gray-50">
                <td className="px-4 py-4">
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
                </td>
                <td className="px-6 py-4">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{student.full_name}</div>
                    <div className="text-sm text-gray-500 flex items-center mt-1">
                      <Mail className="w-3 h-3 mr-1 text-gray-400" />
                      {student.email || '未設定'}
                    </div>
                    <div className="text-sm text-gray-500 flex items-center mt-1">
                      <Calendar className="w-3 h-3 mr-1 text-gray-400" />
                      {student.birth_date}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="space-y-1">
                    <div>
                      {student.classroom_ids && student.classroom_ids.length > 0 ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          已分配
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          未分配
                        </span>
                      )}
                    </div>
                    <button
                      onClick={async () => {
                        setAssigningStudent(student)
                        await fetchStudentClassrooms(student.id)
                      }}
                      className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <Users className="w-3 h-3 mr-1" />
                      分配
                    </button>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {student.referred_by || '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  <div className="max-w-xs truncate">
                    {student.learning_goals || '-'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {student.is_default_password ? (
                    <div className="space-y-1">
                      <div className="flex items-center text-green-600 text-sm">
                        <Key className="w-4 h-4 mr-1" />
                        <span>預設密碼</span>
                      </div>
                      {student.default_password && (
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                            {student.default_password}
                          </span>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(student.default_password || '')
                              toast({
                                title: "已複製",
                                description: "密碼已複製到剪貼簿"
                              })
                            }}
                            className="text-gray-400 hover:text-gray-600 p-1"
                            title="複製密碼"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center text-blue-600 text-sm">
                      <Key className="w-4 h-4 mr-1" />
                      <span>自訂密碼</span>
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <div className="flex items-center justify-center space-x-2">
                    <button
                      onClick={() => setViewingStudent(student)}
                      className="text-blue-600 hover:text-blue-900 p-1"
                      title="查看"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setEditingStudent(student)}
                      className="text-blue-600 hover:text-blue-900 p-1"
                      title="編輯"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button className="text-gray-600 hover:text-gray-900 p-1">
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => handleResetPassword(student)}
                          className="text-orange-600"
                        >
                          <RotateCcw className="w-4 h-4 mr-2" />
                          重置密碼
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => {
                            if (window.confirm('確定要刪除此學生嗎？')) {
                              handleDeleteStudent(student.id)
                            }
                          }}
                          className="text-red-600"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          刪除
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredStudents.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            沒有找到符合條件的學生
          </div>
        )}
      </div>

      {/* 新增學生對話框 */}
      {showAddStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowAddStudent(false)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">新增學生</h2>
              <button
                onClick={() => setShowAddStudent(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              try {
                const response = await api.post('/api/individual/students', {
                  full_name: formData.get('full_name'),
                  email: formData.get('email'),
                  birth_date: formData.get('birth_date'),
                  referred_by: formData.get('referred_by'),
                  learning_goals: formData.get('learning_goals')
                })
                setShowAddStudent(false)
                fetchStudents()
                
                // 顯示預設密碼資訊
                const student = response.data
                toast({
                  title: "學生建立成功！",
                  description: `登入資訊：\n姓名：${student.full_name}\n帳號：${student.email}\n預設密碼：${student.default_password}\n\n註：學生可以後續自行更改密碼`
                })
              } catch (error: any) {
                console.error('Failed to create student:', error)
                toast({
                  variant: "destructive",
                  title: "新增失敗",
                  description: error.response?.data?.detail || '新增學生失敗'
                })
              }
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    學生姓名 <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="full_name"
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email（選填）
                  </label>
                  <input
                    name="email"
                    type="email"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    生日 <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="birth_date"
                    type="date"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    推薦人
                  </label>
                  <input
                    name="referred_by"
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="例如：朋友推薦、網路搜尋等"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    學習目標
                  </label>
                  <textarea
                    name="learning_goals"
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="請描述學生的學習目標..."
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button type="button" variant="outline" onClick={() => setShowAddStudent(false)}>
                  取消
                </Button>
                <Button type="submit">
                  新增學生
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 編輯學生對話框 */}
      {editingStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setEditingStudent(null)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">編輯學生</h2>
              <button
                onClick={() => setEditingStudent(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              try {
                await api.put(`/api/individual/students/${editingStudent.id}`, {
                  full_name: formData.get('full_name'),
                  email: formData.get('email'),
                  birth_date: formData.get('birth_date'),
                  referred_by: formData.get('referred_by'),
                  learning_goals: formData.get('learning_goals')
                })
                setEditingStudent(null)
                fetchStudents()
              } catch (error) {
                console.error('Failed to update student:', error)
                alert('更新學生失敗')
              }
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    學生姓名 <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="full_name"
                    type="text"
                    required
                    defaultValue={editingStudent.full_name}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email（選填）
                  </label>
                  <input
                    name="email"
                    type="email"
                    defaultValue={editingStudent.email}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    生日 <span className="text-red-500">*</span>
                  </label>
                  <input
                    name="birth_date"
                    type="date"
                    required
                    defaultValue={editingStudent.birth_date}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    推薦人
                  </label>
                  <input
                    name="referred_by"
                    type="text"
                    defaultValue={editingStudent.referred_by}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    學習目標
                  </label>
                  <textarea
                    name="learning_goals"
                    rows={3}
                    defaultValue={editingStudent.learning_goals}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button type="button" variant="outline" onClick={() => setEditingStudent(null)}>
                  取消
                </Button>
                <Button type="submit">
                  更新學生
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 批量匯入對話框 */}
      {showBulkImport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowBulkImport(false)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">批量匯入學生</h2>
              <button
                onClick={() => setShowBulkImport(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div className="bg-blue-50 p-4 rounded-md">
                <h3 className="text-sm font-medium text-blue-800 mb-2">匯入格式說明：</h3>
                <p className="text-sm text-blue-700">
                  請準備 CSV 檔案，包含以下欄位：
                </p>
                <ul className="mt-2 text-sm text-blue-700 list-disc list-inside">
                  <li>姓名（必填）</li>
                  <li>Email（必填）</li>
                  <li>生日（必填，格式：YYYY-MM-DD）</li>
                  <li>推薦人（選填）</li>
                  <li>學習目標（選填）</li>
                </ul>
              </div>
              
              <div>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    // 下載範本
                    const csvContent = "姓名,Email,生日,推薦人,學習目標\n張三,zhangsan@example.com,2010-01-01,朋友推薦,提升英語口說能力";
                    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                    const link = document.createElement("a");
                    const url = URL.createObjectURL(blob);
                    link.setAttribute("href", url);
                    link.setAttribute("download", "學生資料範本.csv");
                    link.style.visibility = 'hidden';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                  }}
                >
                  <Download className="w-4 h-4 mr-2" />
                  下載範本
                </Button>
              </div>

              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
                <div className="text-center">
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-600">
                    拖放 CSV 檔案到這裡，或點擊選擇檔案
                  </p>
                  <input
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={async (e) => {
                      const file = e.target.files?.[0]
                      if (!file) return
                      
                      const formData = new FormData()
                      formData.append('file', file)
                      
                      try {
                        await api.post('/api/individual/students/bulk-import', formData, {
                          headers: {
                            'Content-Type': 'multipart/form-data',
                          },
                        })
                        setShowBulkImport(false)
                        fetchStudents()
                        alert('批量匯入成功')
                      } catch (error) {
                        console.error('Failed to bulk import:', error)
                        alert('批量匯入失敗')
                      }
                    }}
                  />
                  <Button
                    variant="outline"
                    className="mt-2"
                    onClick={() => {
                      const input = document.querySelector('input[type="file"]') as HTMLInputElement
                      input?.click()
                    }}
                  >
                    選擇檔案
                  </Button>
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end">
              <Button variant="outline" onClick={() => setShowBulkImport(false)}>
                關閉
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 分配班級對話框 */}
      {showAssignClassroom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowAssignClassroom(false)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">分配班級</h2>
              <button
                onClick={() => setShowAssignClassroom(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              const selectedClassroomIds = Array.from(formData.getAll('classroom_ids')) as string[]
              
              if (selectedClassroomIds.length === 0) {
                alert('請至少選擇一個班級')
                return
              }
              
              await handleAssignClassrooms(selectedStudents, selectedClassroomIds)
            }}>
              <div className="space-y-4">
                <div className="bg-gray-50 p-3 rounded-md">
                  <p className="text-sm text-gray-600">
                    已選擇 <span className="font-medium">{selectedStudents.length}</span> 位學生
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    選擇班級
                  </label>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {classrooms.map((classroom) => (
                      <label key={classroom.id} className="flex items-center p-2 hover:bg-gray-50 rounded">
                        <input
                          name="classroom_ids"
                          type="checkbox"
                          value={classroom.id}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">{classroom.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button type="button" variant="outline" onClick={() => setShowAssignClassroom(false)}>
                  取消
                </Button>
                <Button type="submit">
                  分配班級
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 查看學生詳情對話框 */}
      {viewingStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setViewingStudent(null)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">學生詳情</h2>
              <button
                onClick={() => setViewingStudent(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-500">姓名</label>
                  <p className="mt-1 text-sm text-gray-900">{viewingStudent.full_name}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">Email</label>
                  <p className="mt-1 text-sm text-gray-900">{viewingStudent.email}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">生日</label>
                  <p className="mt-1 text-sm text-gray-900">{viewingStudent.birth_date}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">推薦人</label>
                  <p className="mt-1 text-sm text-gray-900">{viewingStudent.referred_by || '-'}</p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">學習目標</label>
                <p className="mt-1 text-sm text-gray-900">{viewingStudent.learning_goals || '-'}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">所屬班級</label>
                <p className="mt-1 text-sm text-gray-900">
                  {viewingStudent.classroom_names?.join(', ') || '未分配班級'}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-500">密碼狀態</label>
                <div className="mt-1 bg-gray-50 p-3 rounded-md">
                  <p className="text-sm text-gray-700">
                    <span className="font-medium">帳號：</span>{viewingStudent.email}
                  </p>
                  <div className="text-sm text-gray-700">
                    <span className="font-medium">密碼狀態：</span>
                    {viewingStudent.is_default_password ? (
                      <span className="text-green-600 ml-1">使用預設密碼（生日）</span>
                    ) : (
                      <span className="text-blue-600 ml-1">已設定自訂密碼</span>
                    )}
                  </div>
                  {viewingStudent.is_default_password && viewingStudent.default_password && (
                    <p className="text-sm text-gray-500 mt-1">
                      <span className="font-medium">預設密碼：</span>
                      <span className="font-mono bg-gray-200 px-2 py-1 rounded text-xs ml-1">
                        {viewingStudent.default_password}
                      </span>
                    </p>
                  )}
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => {
                  setViewingStudent(null)
                  setEditingStudent(viewingStudent)
                }}
              >
                <Edit2 className="w-4 h-4 mr-1" />
                編輯
              </Button>
              <Button onClick={() => setViewingStudent(null)}>
                關閉
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 單個學生分配班級對話框 */}
      {assigningStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setAssigningStudent(null)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">分配班級</h2>
              <button
                onClick={() => setAssigningStudent(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={async (e) => {
              e.preventDefault()
              const formData = new FormData(e.currentTarget)
              const selectedClassroomIds = Array.from(formData.getAll('classroom_ids')) as string[]
              
              if (selectedClassroomIds.length === 0) {
                alert('請至少選擇一個班級')
                return
              }
              
              try {
                await handleAssignClassrooms([assigningStudent.id], selectedClassroomIds)
                // 清除該學生的班級快取，強制下次重新載入
                setStudentClassrooms(prev => {
                  const newState = { ...prev }
                  delete newState[assigningStudent.id]
                  return newState
                })
                setAssigningStudent(null)
              } catch (error) {
                console.error('Failed to assign student to classrooms:', error)
              }
            }}>
              <div className="space-y-4">
                <div className="bg-gray-50 p-3 rounded-md">
                  <p className="text-sm text-gray-600">
                    學生：<span className="font-medium">{assigningStudent.full_name}</span>
                  </p>
                  <p className="text-xs text-gray-500">{assigningStudent.email}</p>
                  {assigningStudent.classroom_names && assigningStudent.classroom_names.length > 0 && (
                    <p className="text-xs text-gray-500 mt-1">
                      目前班級：{assigningStudent.classroom_names.join(', ')}
                    </p>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    選擇要加入的班級
                  </label>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {classrooms.map((classroom) => {
                      const isAlreadyInClassroom = studentClassrooms[assigningStudent.id]?.includes(classroom.id)
                      return (
                        <label key={classroom.id} className="flex items-center p-2 hover:bg-gray-50 rounded">
                          <input
                            name="classroom_ids"
                            type="checkbox"
                            value={classroom.id}
                            defaultChecked={isAlreadyInClassroom}
                            key={`${assigningStudent.id}-${classroom.id}-${isAlreadyInClassroom}`}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className={`ml-2 text-sm ${isAlreadyInClassroom ? 'text-green-700 font-medium' : 'text-gray-700'}`}>
                            {classroom.name}
                            {isAlreadyInClassroom && <span className="text-xs text-green-600 ml-1">(已加入)</span>}
                          </span>
                        </label>
                      )
                    })}
                  </div>
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <Button type="button" variant="outline" onClick={() => setAssigningStudent(null)}>
                  取消
                </Button>
                <Button type="submit">
                  更新班級分配
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}