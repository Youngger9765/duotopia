import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Plus, Edit2, Trash2, Search, UserPlus, MoreVertical, X } from 'lucide-react'

interface Class {
  id: string
  name: string
  grade: string
  teacher: string
  studentCount: number
}

interface Student {
  id: string
  name: string
  email: string
  status: 'active' | 'inactive'
  joinDate: string
}

function ClassManagement() {
  const [selectedClass, setSelectedClass] = useState<Class | null>(null)
  const [showAddClass, setShowAddClass] = useState(false)
  const [editingClass, setEditingClass] = useState<Class | null>(null)
  const [showAddStudent, setShowAddStudent] = useState(false)
  const [searchClassTerm, setSearchClassTerm] = useState('')
  const [searchStudentTerm, setSearchStudentTerm] = useState('')

  const [classes, setClasses] = useState<Class[]>([
    { id: '1', name: '六年一班', grade: '6', teacher: '王老師', studentCount: 24 },
    { id: '2', name: '六年二班', grade: '6', teacher: '王老師', studentCount: 22 },
    { id: '3', name: '五年三班', grade: '5', teacher: '李老師', studentCount: 20 },
    { id: '4', name: '國一甲班', grade: '7', teacher: '張老師', studentCount: 28 },
  ])

  const [classStudents, setClassStudents] = useState<Record<string, Student[]>>({
    '1': [
      { id: '1', name: '陳小明', email: 'student1@duotopia.com', status: 'active', joinDate: '2024-01-01' },
      { id: '2', name: '林小華', email: 'student2@duotopia.com', status: 'active', joinDate: '2024-01-01' },
      { id: '3', name: '王小美', email: 'student3@duotopia.com', status: 'active', joinDate: '2024-01-02' },
    ],
    '2': [
      { id: '4', name: '張小強', email: 'student4@duotopia.com', status: 'active', joinDate: '2024-01-03' },
      { id: '5', name: '李小芳', email: 'student5@duotopia.com', status: 'active', joinDate: '2024-01-03' },
    ],
    '3': [
      { id: '6', name: '黃小志', email: 'student6@duotopia.com', status: 'active', joinDate: '2024-01-05' },
    ],
    '4': []
  })

  const filteredClasses = classes.filter(cls =>
    cls.name.toLowerCase().includes(searchClassTerm.toLowerCase())
  )

  const currentClassStudents = selectedClass ? (classStudents[selectedClass.id] || []) : []
  const filteredStudents = currentClassStudents.filter(student =>
    student.name.toLowerCase().includes(searchStudentTerm.toLowerCase()) ||
    student.email.toLowerCase().includes(searchStudentTerm.toLowerCase())
  )

  return (
    <div className="h-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">班級管理</h2>
        <p className="text-sm text-gray-500 mt-1">管理班級和學生分配</p>
      </div>

      <div className="flex gap-6 h-[calc(100vh-280px)]">
        {/* Left Panel - Class List */}
        <div className="w-1/3 bg-white rounded-lg shadow overflow-hidden flex flex-col">
          <div className="p-4 border-b">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-medium">班級列表</h3>
              <Button size="sm" onClick={() => setShowAddClass(true)}>
                <Plus className="w-4 h-4 mr-1" />
                新增班級
              </Button>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="搜尋班級..."
                value={searchClassTerm}
                onChange={(e) => setSearchClassTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
              />
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {filteredClasses.map((cls) => (
              <div
                key={cls.id}
                onClick={() => setSelectedClass(cls)}
                className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                  selectedClass?.id === cls.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{cls.name}</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      {cls.teacher} · 年級 {cls.grade}
                    </p>
                    <p className="text-sm text-gray-500">
                      {cls.studentCount} 位學生
                    </p>
                  </div>
                  <div className="flex space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setEditingClass(cls)
                      }}
                      className="p-1 hover:bg-gray-200 rounded"
                    >
                      <Edit2 className="w-4 h-4 text-gray-600" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        // Delete class logic
                      }}
                      className="p-1 hover:bg-gray-200 rounded"
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Panel - Student List */}
        <div className="flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col">
          {selectedClass ? (
            <>
              <div className="p-4 border-b">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <h3 className="text-lg font-medium">{selectedClass.name} - 學生名單</h3>
                    <p className="text-sm text-gray-500">{currentClassStudents.length} 位學生</p>
                  </div>
                  <Button size="sm" onClick={() => setShowAddStudent(true)}>
                    <UserPlus className="w-4 h-4 mr-1" />
                    新增學生
                  </Button>
                </div>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="搜尋學生..."
                    value={searchStudentTerm}
                    onChange={(e) => setSearchStudentTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                  />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto">
                {filteredStudents.length > 0 ? (
                  <table className="min-w-full">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          學生姓名
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Email
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          狀態
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          加入日期
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          操作
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredStudents.map((student) => (
                        <tr key={student.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                                <span className="text-xs font-medium text-gray-600">
                                  {student.name.charAt(1)}
                                </span>
                              </div>
                              <div className="ml-3">
                                <div className="text-sm font-medium text-gray-900">{student.name}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-500">{student.email}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              student.status === 'active' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {student.status === 'active' ? '在學' : '停課'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {student.joinDate}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button className="text-gray-600 hover:text-gray-900">
                              <MoreVertical className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-gray-500">
                    <p className="text-lg mb-2">尚無學生資料</p>
                    <p className="text-sm">點擊「新增學生」開始添加學生</p>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <p>請選擇一個班級查看學生名單</p>
            </div>
          )}
        </div>
      </div>

      {/* Add Class Modal */}
      {showAddClass && (
        <AddClassModal
          onClose={() => setShowAddClass(false)}
          onSave={(newClass) => {
            const classWithId = {
              ...newClass,
              id: Date.now().toString(),
              studentCount: 0
            }
            setClasses([...classes, classWithId])
            setClassStudents({ ...classStudents, [classWithId.id]: [] })
            setShowAddClass(false)
          }}
        />
      )}

      {/* Edit Class Modal */}
      {editingClass && (
        <EditClassModal
          classData={editingClass}
          onClose={() => setEditingClass(null)}
          onSave={(updatedClass) => {
            setClasses(classes.map(c =>
              c.id === updatedClass.id ? updatedClass : c
            ))
            setEditingClass(null)
          }}
        />
      )}

      {/* Add Student to Class Modal */}
      {showAddStudent && selectedClass && (
        <AddStudentToClassModal
          className={selectedClass.name}
          onClose={() => setShowAddStudent(false)}
          onSave={(students) => {
            // Add students to class logic
            setShowAddStudent(false)
          }}
        />
      )}
    </div>
  )
}

function AddClassModal({ onClose, onSave }: any) {
  const [formData, setFormData] = useState({
    name: '',
    grade: '',
    teacher: '王老師'
  })

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">新增班級</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">班級名稱</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="例如：六年一班"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">年級</label>
            <select
              value={formData.grade}
              onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="">請選擇年級</option>
              <option value="1">一年級</option>
              <option value="2">二年級</option>
              <option value="3">三年級</option>
              <option value="4">四年級</option>
              <option value="5">五年級</option>
              <option value="6">六年級</option>
              <option value="7">國一</option>
              <option value="8">國二</option>
              <option value="9">國三</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">教師</label>
            <select
              value={formData.teacher}
              onChange={(e) => setFormData({ ...formData, teacher: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="王老師">王老師</option>
              <option value="李老師">李老師</option>
              <option value="張老師">張老師</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave(formData)} 
            className="flex-1"
            disabled={!formData.name || !formData.grade}
          >
            新增
          </Button>
        </div>
      </div>
    </div>
  )
}

function EditClassModal({ classData, onClose, onSave }: any) {
  const [formData, setFormData] = useState({
    name: classData.name,
    grade: classData.grade,
    teacher: classData.teacher
  })

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">編輯班級</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">班級名稱</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">年級</label>
            <select
              value={formData.grade}
              onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="1">一年級</option>
              <option value="2">二年級</option>
              <option value="3">三年級</option>
              <option value="4">四年級</option>
              <option value="5">五年級</option>
              <option value="6">六年級</option>
              <option value="7">國一</option>
              <option value="8">國二</option>
              <option value="9">國三</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">教師</label>
            <select
              value={formData.teacher}
              onChange={(e) => setFormData({ ...formData, teacher: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="王老師">王老師</option>
              <option value="李老師">李老師</option>
              <option value="張老師">張老師</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave({ ...classData, ...formData })} 
            className="flex-1"
          >
            儲存
          </Button>
        </div>
      </div>
    </div>
  )
}

function AddStudentToClassModal({ className, onClose, onSave }: any) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedStudents, setSelectedStudents] = useState<string[]>([])

  // Mock available students (not in this class)
  const availableStudents = [
    { id: '10', name: '趙小新', email: 'student10@duotopia.com' },
    { id: '11', name: '錢小芬', email: 'student11@duotopia.com' },
    { id: '12', name: '孫小偉', email: 'student12@duotopia.com' },
  ]

  const filteredStudents = availableStudents.filter(student =>
    student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    student.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">新增學生到 {className}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="搜尋學生..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>
        </div>

        <div className="max-h-64 overflow-y-auto mb-4">
          {filteredStudents.map((student) => (
            <label
              key={student.id}
              className="flex items-center p-3 border-b hover:bg-gray-50 cursor-pointer"
            >
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
              <div className="ml-3">
                <div className="text-sm font-medium text-gray-900">{student.name}</div>
                <div className="text-sm text-gray-500">{student.email}</div>
              </div>
            </label>
          ))}
        </div>

        <div className="flex space-x-3">
          <Button onClick={onClose} variant="outline" className="flex-1">
            取消
          </Button>
          <Button 
            onClick={() => onSave(selectedStudents)} 
            className="flex-1"
            disabled={selectedStudents.length === 0}
          >
            新增 ({selectedStudents.length})
          </Button>
        </div>
      </div>
    </div>
  )
}

export default ClassManagement