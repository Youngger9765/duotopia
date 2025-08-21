import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function StudentLoginPage() {
  const [step, setStep] = useState(1)
  const [teacherEmail, setTeacherEmail] = useState('')
  const [teacherId, setTeacherId] = useState('')
  const [selectedClass, setSelectedClass] = useState('')
  const [selectedStudent, setSelectedStudent] = useState('')
  const [password, setPassword] = useState('')
  const [classes, setClasses] = useState<any[]>([])
  const [students, setStudents] = useState<any[]>([])
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleTeacherEmail = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/student-login/teachers/search?email=${teacherEmail}`
      )
      setTeacherId(response.data.id)
      
      // Get teacher's classrooms
      const classroomsResponse = await axios.get(
        `${API_BASE_URL}/api/student-login/teachers/${response.data.id}/classrooms`
      )
      setClasses(classroomsResponse.data)
      setStep(2)
    } catch (err) {
      setError('找不到此老師的Email')
    }
  }

  const handleClassSelection = async (classId: string) => {
    setSelectedClass(classId)
    setError('')
    
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/student-login/classrooms/${classId}/students`
      )
      setStudents(response.data)
      setStep(3)
    } catch (err) {
      setError('無法取得班級學生名單')
    }
  }

  const handleStudentSelection = (studentId: string) => {
    setSelectedStudent(studentId)
    setStep(4)
  }

  const handlePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/student-login/verify-password`, {
        student_id: selectedStudent,
        password: password
      })
      
      // Save token and student info
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('userRole', 'student')
      localStorage.setItem('studentInfo', JSON.stringify(response.data.student))
      
      navigate('/student')
    } catch (err) {
      setError('密碼錯誤')
    }
  }

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              <div className="mb-8">
                <span className="text-6xl">👨‍🏫</span>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                請輸入您的老師 Email
              </h2>
              <p className="text-gray-600">我們需要找到您所屬的班級</p>
            </div>
            <form onSubmit={handleTeacherEmail} className="mt-8 space-y-6">
              <input
                type="email"
                required
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="teacher@example.com"
                value={teacherEmail}
                onChange={(e) => setTeacherEmail(e.target.value)}
              />
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <Button type="submit" className="w-full">
                下一步
              </Button>
              <div className="text-center text-gray-600">
                或選擇最近使用過的老師：
              </div>
              <div className="flex justify-center">
                <button
                  type="button"
                  onClick={() => setTeacherEmail('teacher@individual.com')}
                  className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
                >
                  teacher@individual.com
                </button>
              </div>
            </form>
          </div>
        )

      case 2:
        return (
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              <div className="mb-8">
                <span className="text-6xl">🏫</span>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                請選擇您的班級
              </h2>
              <p className="text-gray-600">找到 {classes.length} 個班級</p>
            </div>
            <div className="space-y-4">
              {classes.map((cls) => (
                <button
                  key={cls.id}
                  onClick={() => handleClassSelection(cls.id)}
                  className="w-full p-4 text-left border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors flex items-center justify-between"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">👥</span>
                    <span className="font-medium">{cls.name}</span>
                  </div>
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(1)}
              className="text-blue-600 hover:text-blue-500"
            >
              ← 返回上一步
            </button>
          </div>
        )

      case 3:
        return (
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              <div className="mb-8">
                <span className="text-6xl">🎓</span>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                請找到您的姓名
              </h2>
              <p className="text-gray-600">
                {classes.find(c => c.id === selectedClass)?.name} - {students.length} 位學生
              </p>
            </div>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {students.map((student) => (
                <button
                  key={student.id}
                  onClick={() => handleStudentSelection(student.id)}
                  className="w-full p-4 text-left border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">👤</span>
                    <div>
                      <div className="font-medium">{student.full_name}</div>
                      <div className="text-sm text-gray-500">{student.email}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
            <button
              onClick={() => setStep(2)}
              className="text-blue-600 hover:text-blue-500"
            >
              ← 返回上一步
            </button>
          </div>
        )

      case 4:
        return (
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              <div className="mb-8">
                <span className="text-6xl">🎉</span>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                你好，{students.find(s => s.id === selectedStudent)?.full_name}！
              </h2>
              <p className="text-gray-600">請輸入您的密碼</p>
            </div>
            <form onSubmit={handlePassword} className="mt-8 space-y-6">
              <input
                type="password"
                required
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="請輸入您的密碼"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <p className="text-sm text-gray-500">
                預設密碼為您的生日（YYYYMMDD格式）
              </p>
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <Button type="submit" className="w-full">
                登入
              </Button>
            </form>
            <button
              onClick={() => setStep(3)}
              className="text-blue-600 hover:text-blue-500"
            >
              ← 返回上一步
            </button>
          </div>
        )
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="flex flex-col items-center">
        <div className="mb-8">
          <Link to="/" className="flex items-center space-x-2 text-gray-600 hover:text-gray-900">
            <span>←</span>
            <span>學生登入</span>
          </Link>
          <div className="text-sm text-gray-500 mt-2">
            步驟 {step}/4
          </div>
        </div>
        {renderStep()}
        
        {/* 測試帳號小抄 */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg max-w-md">
            <h3 className="text-sm font-semibold text-yellow-800 mb-2">🎓 測試帳號小抄</h3>
            <div className="text-xs text-yellow-700 space-y-2">
              <div>
                <strong>老師 Email:</strong> teacher@individual.com
              </div>
              <div>
                <strong>教室:</strong> 測試教室A
              </div>
              <div className="pt-2 border-t border-yellow-200">
                <strong>學生帳號：</strong>
                <ul className="mt-1 space-y-1">
                  <li>• 張小明 - 密碼: 20100101</li>
                  <li>• 李小華 - 密碼: 20110215</li>
                  <li>• 王小美 - 密碼: 20100820</li>
                </ul>
              </div>
              <div className="text-xs pt-2 opacity-75">
                💡 密碼格式：YYYYMMDD（生日）
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default StudentLoginPage