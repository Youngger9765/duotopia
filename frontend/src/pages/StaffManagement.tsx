import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Plus, Search, Edit2, Trash2, X, UserCog, Mail, Phone, Building2, Calendar } from 'lucide-react'
import { adminApi } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

interface Staff {
  id: string
  full_name: string
  email: string
  phone?: string
  role: 'teacher' | 'admin'
  school_id: number
  school?: {
    id: number
    name: string
  }
  is_active: boolean
  created_at: string
  updated_at?: string
}

function StaffManagement() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { toast } = useToast()
  const [showAddStaff, setShowAddStaff] = useState(false)
  const [editingStaff, setEditingStaff] = useState<Staff | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSchool, setSelectedSchool] = useState<string>('all')
  const [selectedRole, setSelectedRole] = useState<string>('all')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [staffList, setStaffList] = useState<Staff[]>([])
  const [schools, setSchools] = useState<any[]>([])
  
  // Handle URL query parameters
  useEffect(() => {
    const action = searchParams.get('action')
    
    if (action === 'add') {
      setShowAddStaff(true)
      // Clear the action parameter
      const newParams = new URLSearchParams(searchParams)
      newParams.delete('action')
      setSearchParams(newParams)
    }
  }, [searchParams.get('action')])

  // Fetch data on component mount
  useEffect(() => {
    fetchStaffList()
    fetchSchools()
  }, [])

  const fetchStaffList = async () => {
    try {
      setLoading(true)
      const response = await adminApi.getUsers()
      setStaffList(response.data)
    } catch (error) {
      console.error('Failed to fetch staff:', error)
      toast({
        title: "錯誤",
        description: "無法載入教職員資料",
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

  const roleLabels = {
    teacher: '教師',
    admin: '管理員'
  }

  // Filter staff based on search and filters
  const filteredStaff = staffList.filter(staff => {
    const matchesSearch = staff.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         staff.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (staff.phone && staff.phone.includes(searchTerm))
    const matchesSchool = selectedSchool === 'all' || staff.school_id === parseInt(selectedSchool)
    const matchesRole = selectedRole === 'all' || staff.role === selectedRole
    
    return matchesSearch && matchesSchool && matchesRole
  })

  const handleAddStaff = async (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    
    try {
      const userData = {
        email: formData.get('email') as string,
        password: formData.get('password') as string,
        full_name: formData.get('name') as string,
        role: formData.get('role') as string,
        phone: formData.get('phone') as string,
        school_id: parseInt(formData.get('schoolId') as string)
      }
      
      await adminApi.createUser(userData)
      toast({
        title: "成功",
        description: "教職員已新增",
      })
      setShowAddStaff(false)
      fetchStaffList()
    } catch (error: any) {
      toast({
        title: "錯誤",
        description: error.response?.data?.detail || "無法新增教職員",
        variant: "destructive",
      })
    }
  }

  const handleUpdateStaff = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingStaff) return
    
    const formData = new FormData(e.target as HTMLFormElement)
    
    try {
      const updateData = {
        full_name: formData.get('name') as string,
        email: formData.get('email') as string,
        phone: formData.get('phone') as string,
        role: formData.get('role') as string,
        school_id: parseInt(formData.get('schoolId') as string),
        is_active: formData.get('status') === 'active'
      }
      
      await adminApi.updateUser(editingStaff.id, updateData)
      toast({
        title: "成功",
        description: "教職員資料已更新",
      })
      setEditingStaff(null)
      fetchStaffList()
    } catch (error: any) {
      toast({
        title: "錯誤",
        description: error.response?.data?.detail || "無法更新教職員資料",
        variant: "destructive",
      })
    }
  }

  const handleDeleteStaff = async (id: string) => {
    try {
      await adminApi.deleteUser(id)
      toast({
        title: "成功",
        description: "教職員已刪除",
      })
      setShowDeleteConfirm(null)
      fetchStaffList()
    } catch (error: any) {
      toast({
        title: "錯誤",
        description: error.response?.data?.detail || "無法刪除教職員",
        variant: "destructive",
      })
      setShowDeleteConfirm(null)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">教職員管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理學校內的教職員資訊</p>
      </div>

      {/* Filters */}
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
          
          <select
            value={selectedSchool}
            onChange={(e) => setSelectedSchool(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">所有學校</option>
            {schools.map(inst => (
              <option key={inst.id} value={inst.id}>{inst.name}</option>
            ))}
          </select>
          
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">所有職位</option>
            {Object.entries(roleLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          
          <Button onClick={() => setShowAddStaff(true)}>
            <Plus className="w-4 h-4 mr-2" />
            新增教職員
          </Button>
        </div>
      </div>

      {/* Staff List */}
      <div className="flex-1 bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-500">載入中...</div>
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  教職員資訊
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  聯絡方式
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  職位與部門
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  學校
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  狀態
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">操作</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredStaff.map((staff) => (
                <tr key={staff.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <UserCog className="h-5 w-5 text-blue-600" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{staff.full_name}</div>
                        <div className="text-sm text-gray-500">ID: {staff.id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 flex items-center">
                      <Mail className="w-4 h-4 mr-1 text-gray-400" />
                      {staff.email}
                    </div>
                    {staff.phone && (
                      <div className="text-sm text-gray-500 flex items-center mt-1">
                        <Phone className="w-4 h-4 mr-1 text-gray-400" />
                        {staff.phone}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{roleLabels[staff.role]}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 flex items-center">
                      <Building2 className="w-4 h-4 mr-1 text-gray-400" />
                      {staff.school?.name || '未分配'}
                    </div>
                    <div className="text-sm text-gray-500 flex items-center mt-1">
                      <Calendar className="w-4 h-4 mr-1 text-gray-400" />
                      入職：{new Date(staff.created_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      staff.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {staff.is_active ? '在職' : '停用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => setEditingStaff(staff)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setShowDeleteConfirm(staff.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {filteredStaff.length === 0 && (
            <div className="text-center py-12">
              <UserCog className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">沒有找到教職員</h3>
              <p className="mt-1 text-sm text-gray-500">請調整搜尋條件或新增教職員</p>
            </div>
          )}
        </div>
        )}
      </div>

      {/* Add Staff Modal */}
      {showAddStaff && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">新增教職員</h3>
              <button
                onClick={() => setShowAddStaff(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleAddStaff}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    姓名 *
                  </label>
                  <input
                    name="name"
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email *
                  </label>
                  <input
                    name="email"
                    type="email"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    電話 *
                  </label>
                  <input
                    name="phone"
                    type="tel"
                    required
                    placeholder="09XX-XXX-XXX"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    密碼 *
                  </label>
                  <input
                    name="password"
                    type="password"
                    required
                    placeholder="請輸入初始密碼"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    職位 *
                  </label>
                  <select
                    name="role"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">請選擇職位</option>
                    {Object.entries(roleLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    所屬學校 *
                  </label>
                  <select
                    name="schoolId"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">請選擇學校</option>
                    {schools.map(inst => (
                      <option key={inst.id} value={inst.id}>{inst.name}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    部門
                  </label>
                  <input
                    name="department"
                    type="text"
                    placeholder="例如：英語教學部"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    入職日期 *
                  </label>
                  <input
                    name="joinDate"
                    type="date"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAddStaff(false)}
                >
                  取消
                </Button>
                <Button type="submit">
                  新增教職員
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Staff Modal */}
      {editingStaff && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">編輯教職員資訊</h3>
              <button
                onClick={() => setEditingStaff(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={handleUpdateStaff}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    姓名 *
                  </label>
                  <input
                    name="name"
                    type="text"
                    defaultValue={editingStaff.full_name}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email *
                  </label>
                  <input
                    name="email"
                    type="email"
                    defaultValue={editingStaff.email}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    電話 *
                  </label>
                  <input
                    name="phone"
                    type="tel"
                    defaultValue={editingStaff.phone}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    職位 *
                  </label>
                  <select
                    name="role"
                    defaultValue={editingStaff.role}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    {Object.entries(roleLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    所屬學校 *
                  </label>
                  <select
                    name="schoolId"
                    defaultValue={editingStaff.school_id}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    {schools.map(inst => (
                      <option key={inst.id} value={inst.id}>{inst.name}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    部門
                  </label>
                  <input
                    name="department"
                    type="text"
                    placeholder="例如：英語教學部"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    狀態 *
                  </label>
                  <select
                    name="status"
                    defaultValue={editingStaff.is_active ? 'active' : 'inactive'}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="active">在職</option>
                    <option value="inactive">停用</option>
                  </select>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditingStaff(null)}
                >
                  取消
                </Button>
                <Button type="submit">
                  儲存變更
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-sm w-full p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">確認刪除</h3>
            <p className="text-sm text-gray-500 mb-6">
              確定要刪除這位教職員嗎？此操作無法復原。
            </p>
            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => setShowDeleteConfirm(null)}
              >
                取消
              </Button>
              <Button
                variant="destructive"
                onClick={() => handleDeleteStaff(showDeleteConfirm)}
              >
                確認刪除
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StaffManagement