import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Plus, Edit2, Trash2, Search, Building2, MapPin, Phone, Mail, Users, Calendar } from 'lucide-react'
import { adminApi } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

interface Institution {
  id: number
  name: string
  address?: string
  phone?: string
  email?: string
  created_at: string
  updated_at?: string
  type?: 'school' | 'branch' | 'tutoring_center'
  status?: 'active' | 'inactive'
  principalName?: string
  establishedDate?: string
  // Additional stats from API
  teacherCount?: number
  studentCount?: number
  classCount?: number
  courseCount?: number
}

function InstitutionManagement() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { toast } = useToast()
  const [showAddInstitution, setShowAddInstitution] = useState(false)
  const [editingInstitution, setEditingInstitution] = useState<Institution | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [statsData, setStatsData] = useState<any>(null)

  // Handle URL query parameters
  useEffect(() => {
    const action = searchParams.get('action')
    
    if (action === 'add') {
      setShowAddInstitution(true)
      // Clear the action parameter after opening modal
      const newParams = new URLSearchParams(searchParams)
      newParams.delete('action')
      setSearchParams(newParams)
    }
  }, [searchParams.get('action')])

  // Load real data from API
  useEffect(() => {
    const loadInstitutions = async () => {
      setLoading(true)
      try {
        const response = await adminApi.getSchools()
        const schools = response.data.map((school: any) => ({
          id: school.id,
          name: school.name,
          address: school.address || '',
          phone: school.phone || '',
          email: `${school.code?.toLowerCase()}@duotopia.com` || '',
          created_at: school.created_at,
          updated_at: school.updated_at,
          type: 'school' as const,
          status: 'active' as const,
          principalName: '校長',
          establishedDate: school.created_at?.split('T')[0],
          teacherCount: 0,
          studentCount: 0,
          classCount: 0,
          courseCount: 0
        }))
        setInstitutions(schools)
      } catch (error) {
        console.error('Failed to load institutions:', error)
        toast({
          title: '載入失敗',
          description: '無法載入機構資料，請稍後再試',
          variant: 'destructive',
        })
      } finally {
        setLoading(false)
      }
    }

    loadInstitutions()
  }, [])

  const getTypeColor = (type?: string) => {
    switch (type) {
      case 'school': return 'bg-blue-100 text-blue-800'
      case 'branch': return 'bg-green-100 text-green-800'
      case 'tutoring_center': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeLabel = (type?: string) => {
    switch (type) {
      case 'school': return '學校'
      case 'branch': return '分校'
      case 'tutoring_center': return '補習班'
      default: return '未分類'
    }
  }

  const filteredInstitutions = institutions.filter(inst => {
    const matchesSearch = inst.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (inst.address && inst.address.toLowerCase().includes(searchTerm.toLowerCase())) ||
                         (inst.email && inst.email.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesType = filterType === 'all' || inst.type === filterType
    return matchesSearch && matchesType
  })

  // Get stats for each institution from statsData
  const getInstitutionStats = (institutionId: number) => {
    if (!statsData || !statsData.schools) return { users: 0, students: 0, classes: 0, courses: 0 }
    const schoolStats = statsData.schools.find((s: any) => s.id === institutionId)
    return schoolStats || { users: 0, students: 0, classes: 0, courses: 0 }
  }

  const handleAddInstitution = async (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    
    try {
      const institutionData = {
        name: formData.get('name') as string,
        address: formData.get('address') as string || undefined,
        phone: formData.get('phone') as string || undefined,
        email: formData.get('email') as string || undefined
      }
      
      await adminApi.createSchool(institutionData)
      toast({
        title: "成功",
        description: "機構已新增",
      })
      setShowAddInstitution(false)
      fetchInstitutions()
      fetchStats()
    } catch (error: any) {
      toast({
        title: "錯誤",
        description: error.response?.data?.detail || "無法新增機構",
        variant: "destructive",
      })
    }
  }

  const handleUpdateInstitution = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingInstitution) return
    
    const formData = new FormData(e.target as HTMLFormElement)
    
    try {
      const updateData = {
        name: formData.get('name') as string,
        address: formData.get('address') as string || undefined,
        phone: formData.get('phone') as string || undefined,
        email: formData.get('email') as string || undefined
      }
      
      await adminApi.updateSchool(editingInstitution.id, updateData)
      toast({
        title: "成功",
        description: "機構資料已更新",
      })
      setEditingInstitution(null)
      fetchInstitutions()
      fetchStats()
    } catch (error: any) {
      toast({
        title: "錯誤",
        description: error.response?.data?.detail || "無法更新機構資料",
        variant: "destructive",
      })
    }
  }

  const handleDeleteInstitution = async (id: number) => {
    try {
      await adminApi.deleteSchool(id)
      toast({
        title: "成功",
        description: "機構已刪除",
      })
      setShowDeleteConfirm(null)
      fetchInstitutions()
      fetchStats()
    } catch (error: any) {
      toast({
        title: "錯誤",
        description: error.response?.data?.detail || "無法刪除機構",
        variant: "destructive",
      })
      setShowDeleteConfirm(null)
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-500">載入中...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">學校管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理所有學校和分校</p>
      </div>

      {/* Filters and Actions */}
      <div className="flex flex-col sm:flex-row justify-between gap-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜尋學校名稱、地址或負責人..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 w-80"
            />
          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">所有類型</option>
            <option value="school">學校</option>
            <option value="branch">分校</option>
            <option value="tutoring_center">補習班</option>
          </select>
        </div>
        <Button onClick={() => setShowAddInstitution(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新增學校
        </Button>
      </div>

      {/* Institution Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredInstitutions.map((institution) => (
          <div key={institution.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center">
                  <div className="h-12 w-12 rounded-lg bg-gray-100 flex items-center justify-center">
                    <Building2 className="h-6 w-6 text-gray-600" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-gray-900">{institution.name}</h3>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTypeColor(institution.type)}`}>
                      {getTypeLabel(institution.type)}
                    </span>
                  </div>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  institution.status === 'active' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {institution.status === 'active' ? '營運中' : '已停用'}
                </span>
              </div>

              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <div className="flex items-center">
                  <MapPin className="w-4 h-4 mr-2 text-gray-400" />
                  <span className="truncate">{institution.address}</span>
                </div>
                <div className="flex items-center">
                  <Phone className="w-4 h-4 mr-2 text-gray-400" />
                  <span>{institution.phone}</span>
                </div>
                <div className="flex items-center">
                  <Mail className="w-4 h-4 mr-2 text-gray-400" />
                  <span>{institution.email}</span>
                </div>
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between text-sm">
                  <div>
                    <p className="text-gray-500">負責人</p>
                    <p className="font-medium text-gray-900">{institution.principalName}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-500">教師</p>
                    <p className="font-medium text-gray-900">{institution.teacherCount}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-gray-500">學生</p>
                    <p className="font-medium text-gray-900">{institution.studentCount}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <div className="flex items-center text-xs text-gray-500">
                  <Calendar className="w-3 h-3 mr-1" />
                  成立於 {institution.establishedDate}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setEditingInstitution(institution)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <Edit2 className="w-4 h-4 text-gray-600" />
                  </button>
                  <button
                    onClick={() => setShowDeleteConfirm(institution.id)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <Trash2 className="w-4 h-4 text-red-600" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Institution Modal */}
      {showAddInstitution && (
        <AddInstitutionModal
          onClose={() => setShowAddInstitution(false)}
          onSave={async (newInstitution) => {
            try {
              const response = await adminApi.createSchool({
                name: newInstitution.name,
                address: newInstitution.address,
                phone: newInstitution.phone,
                code: newInstitution.name.substring(0, 3).toUpperCase() + Date.now().toString().slice(-3)
              })
              // Reload institutions after creation
              const refreshResponse = await adminApi.getSchools()
              const schools = refreshResponse.data.map((school: any) => ({
                id: school.id,
                name: school.name,
                address: school.address || '',
                phone: school.phone || '',
                email: `${school.code?.toLowerCase()}@duotopia.com` || '',
                created_at: school.created_at,
                updated_at: school.updated_at,
                type: 'school' as const,
                status: 'active' as const,
                principalName: newInstitution.principalName || '校長',
                establishedDate: school.created_at?.split('T')[0],
                teacherCount: 0,
                studentCount: 0,
                classCount: 0,
                courseCount: 0
              }))
              setInstitutions(schools)
              toast({
                title: '成功',
                description: '學校已新增',
              })
            } catch (error) {
              console.error('Failed to create institution:', error)
              toast({
                title: '新增失敗',
                description: '無法新增學校，請稍後再試',
                variant: 'destructive',
              })
            }
            setShowAddInstitution(false)
          }}
        />
      )}

      {/* Edit Institution Modal */}
      {editingInstitution && (
        <EditInstitutionModal
          institution={editingInstitution}
          onClose={() => setEditingInstitution(null)}
          onSave={async (updatedInstitution) => {
            try {
              await adminApi.updateSchool(updatedInstitution.id, {
                name: updatedInstitution.name,
                address: updatedInstitution.address,
                phone: updatedInstitution.phone
              })
              // Reload institutions after update
              const response = await adminApi.getSchools()
              const schools = response.data.map((school: any) => ({
                id: school.id,
                name: school.name,
                address: school.address || '',
                phone: school.phone || '',
                email: `${school.code?.toLowerCase()}@duotopia.com` || '',
                created_at: school.created_at,
                updated_at: school.updated_at,
                type: 'school' as const,
                status: 'active' as const,
                principalName: '校長',
                establishedDate: school.created_at?.split('T')[0],
                teacherCount: 0,
                studentCount: 0,
                classCount: 0,
                courseCount: 0
              }))
              setInstitutions(schools)
              toast({
                title: '成功',
                description: '學校資料已更新',
              })
            } catch (error) {
              console.error('Failed to update institution:', error)
              toast({
                title: '更新失敗',
                description: '無法更新學校資料，請稍後再試',
                variant: 'destructive',
              })
            }
            setEditingInstitution(null)
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-sm w-full p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">確認刪除</h3>
            <p className="text-sm text-gray-500 mb-6">
              確定要刪除這個學校嗎？此操作無法復原，相關的教師和學生資料也會受到影響。
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
                onClick={async () => {
                  try {
                    await adminApi.deleteSchool(showDeleteConfirm)
                    // Reload institutions after deletion
                    const response = await adminApi.getSchools()
                    const schools = response.data.map((school: any) => ({
                      id: school.id,
                      name: school.name,
                      address: school.address || '',
                      phone: school.phone || '',
                      email: `${school.code?.toLowerCase()}@duotopia.com` || '',
                      created_at: school.created_at,
                      updated_at: school.updated_at,
                      type: 'school' as const,
                      status: 'active' as const,
                      principalName: '校長',
                      establishedDate: school.created_at?.split('T')[0],
                      teacherCount: 0,
                      studentCount: 0,
                      classCount: 0,
                      courseCount: 0
                    }))
                    setInstitutions(schools)
                    toast({
                      title: '成功',
                      description: '學校已刪除',
                    })
                  } catch (error) {
                    console.error('Failed to delete institution:', error)
                    toast({
                      title: '刪除失敗',
                      description: '無法刪除學校，請稍後再試',
                      variant: 'destructive',
                    })
                  }
                  setShowDeleteConfirm(null)
                }}
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

function AddInstitutionModal({ onClose, onSave }: any) {
  const [formData, setFormData] = useState({
    name: '',
    type: 'school' as Institution['type'],
    address: '',
    phone: '',
    email: '',
    principalName: ''
  })

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">新增學校</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">學校名稱 *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="例如：台北總校"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">機構類型 *</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as Institution['type'] })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="school">學校</option>
              <option value="branch">分校</option>
              <option value="tutoring_center">補習班</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">地址 *</label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="請輸入完整地址"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">聯絡電話 *</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="02-2700-1234"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="school@duotopia.com"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">負責人姓名 *</label>
            <input
              type="text"
              value={formData.principalName}
              onChange={(e) => setFormData({ ...formData, principalName: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="例如：陳校長"
            />
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave(formData)} 
            className="flex-1"
            disabled={!formData.name || !formData.address || !formData.phone || !formData.email || !formData.principalName}
          >
            新增
          </Button>
        </div>
      </div>
    </div>
  )
}

function EditInstitutionModal({ institution, onClose, onSave }: any) {
  const [formData, setFormData] = useState({
    name: institution.name,
    type: institution.type,
    address: institution.address,
    phone: institution.phone,
    email: institution.email,
    principalName: institution.principalName,
    status: institution.status
  })

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">編輯機構</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">學校名稱 *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">機構類型 *</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as Institution['type'] })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="school">學校</option>
              <option value="branch">分校</option>
              <option value="tutoring_center">補習班</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">地址 *</label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">聯絡電話 *</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">負責人姓名 *</label>
            <input
              type="text"
              value={formData.principalName}
              onChange={(e) => setFormData({ ...formData, principalName: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">狀態</label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value as 'active' | 'inactive' })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="active">營運中</option>
              <option value="inactive">已停用</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave({ ...institution, ...formData })} 
            className="flex-1"
          >
            儲存變更
          </Button>
        </div>
      </div>
    </div>
  )
}

export default InstitutionManagement