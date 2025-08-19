import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Plus, Edit2, Trash2, Search, Building2, MapPin, Phone, Mail, Users, Calendar } from 'lucide-react'

interface Institution {
  id: string
  name: string
  type: 'school' | 'tutoring_center' | 'branch'
  address: string
  phone: string
  email: string
  principalName: string
  teacherCount: number
  studentCount: number
  establishedDate: string
  status: 'active' | 'inactive'
}

function InstitutionManagement() {
  const [showAddInstitution, setShowAddInstitution] = useState(false)
  const [editingInstitution, setEditingInstitution] = useState<Institution | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<string>('all')

  const [institutions, setInstitutions] = useState<Institution[]>([
    {
      id: '1',
      name: '台北總校',
      type: 'school',
      address: '台北市大安區信義路四段123號',
      phone: '02-2700-1234',
      email: 'taipei@duotopia.com',
      principalName: '陳校長',
      teacherCount: 12,
      studentCount: 245,
      establishedDate: '2020-01-15',
      status: 'active'
    },
    {
      id: '2',
      name: '新竹分校',
      type: 'branch',
      address: '新竹市東區光復路二段456號',
      phone: '03-5678-9012',
      email: 'hsinchu@duotopia.com',
      principalName: '林主任',
      teacherCount: 8,
      studentCount: 156,
      establishedDate: '2021-03-20',
      status: 'active'
    },
    {
      id: '3',
      name: '台中補習班',
      type: 'tutoring_center',
      address: '台中市西區台灣大道二段789號',
      phone: '04-2345-6789',
      email: 'taichung@duotopia.com',
      principalName: '黃主任',
      teacherCount: 5,
      studentCount: 85,
      establishedDate: '2022-06-10',
      status: 'active'
    }
  ])

  const filteredInstitutions = institutions.filter(inst => {
    const matchesSearch = inst.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         inst.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         inst.principalName.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = filterType === 'all' || inst.type === filterType
    return matchesSearch && matchesType
  })

  const getTypeLabel = (type: Institution['type']) => {
    switch (type) {
      case 'school': return '學校'
      case 'branch': return '分校'
      case 'tutoring_center': return '補習班'
    }
  }

  const getTypeColor = (type: Institution['type']) => {
    switch (type) {
      case 'school': return 'bg-blue-100 text-blue-800'
      case 'branch': return 'bg-green-100 text-green-800'
      case 'tutoring_center': return 'bg-purple-100 text-purple-800'
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">機構管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理所有教育機構和分校</p>
      </div>

      {/* Filters and Actions */}
      <div className="flex flex-col sm:flex-row justify-between gap-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜尋機構名稱、地址或負責人..."
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
          新增機構
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
                    onClick={() => {
                      // Delete logic
                    }}
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
          onSave={(newInstitution) => {
            setInstitutions([...institutions, {
              ...newInstitution,
              id: Date.now().toString(),
              teacherCount: 0,
              studentCount: 0,
              establishedDate: new Date().toISOString().split('T')[0],
              status: 'active'
            }])
            setShowAddInstitution(false)
          }}
        />
      )}

      {/* Edit Institution Modal */}
      {editingInstitution && (
        <EditInstitutionModal
          institution={editingInstitution}
          onClose={() => setEditingInstitution(null)}
          onSave={(updatedInstitution) => {
            setInstitutions(institutions.map(inst =>
              inst.id === updatedInstitution.id ? updatedInstitution : inst
            ))
            setEditingInstitution(null)
          }}
        />
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
        <h3 className="text-lg font-medium text-gray-900 mb-4">新增機構</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">機構名稱 *</label>
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
            <label className="block text-sm font-medium text-gray-700">機構名稱 *</label>
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