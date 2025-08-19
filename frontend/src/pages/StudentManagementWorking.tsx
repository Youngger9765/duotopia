import { useState, useEffect } from 'react'
import { adminApi } from '@/lib/api'

interface Student {
  id: string
  full_name: string
  email: string
  school_name: string
  class_name?: string
}

function StudentManagementWorking() {
  const [students, setStudents] = useState<Student[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStudents()
  }, [])

  const fetchStudents = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await adminApi.getStudents()
      console.log('學生資料:', response.data)
      setStudents(response.data || [])
    } catch (error) {
      console.error('獲取學生資料失敗:', error)
      setError('無法載入學生資料')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">學生管理</h2>
        <div className="text-gray-500">載入中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">學生管理</h2>
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <p className="text-red-800">{error}</p>
          <button 
            onClick={fetchStudents}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            重試
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">學生管理</h2>
      
      <div className="mb-4">
        <p className="text-gray-600">共找到 {students.length} 位學生</p>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium">學生名單</h3>
        </div>
        
        <div className="divide-y divide-gray-200">
          {students.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              暫無學生資料
            </div>
          ) : (
            students.map((student) => (
              <div key={student.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">{student.full_name}</h4>
                    <p className="text-sm text-gray-500">{student.email}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">{student.school_name}</p>
                    <p className="text-sm text-gray-500">
                      {student.class_name || '未分班'}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default StudentManagementWorking