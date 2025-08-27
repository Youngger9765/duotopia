import { Routes, Route, Navigate } from 'react-router-dom'
import Home from './pages/Home'
import TeacherLogin from './pages/TeacherLogin'
import TeacherRegister from './pages/TeacherRegister'
import TeacherDashboardWithSidebar from './pages/TeacherDashboardWithSidebar'
import StudentLogin from './pages/StudentLogin'
import StudentDashboard from './pages/StudentDashboard'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      
      {/* Teacher Routes */}
      <Route path="/teacher/login" element={<TeacherLogin />} />
      <Route path="/teacher/register" element={<TeacherRegister />} />
      <Route path="/teacher/dashboard" element={<TeacherDashboardWithSidebar />} />
      
      {/* Student Routes */}
      <Route path="/student/login" element={<StudentLogin />} />
      <Route path="/student/dashboard" element={<StudentDashboard />} />
      
      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App