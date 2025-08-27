import { Routes, Route, Navigate } from 'react-router-dom'
import Home from './pages/Home'
import TeacherLogin from './pages/TeacherLogin'
import TeacherRegister from './pages/TeacherRegister'
import TeacherDashboardWithSidebar from './pages/TeacherDashboardWithSidebar'
import TeacherDashboard from './pages/teacher/TeacherDashboard'
import TeacherClassrooms from './pages/teacher/TeacherClassrooms'
import TeacherStudents from './pages/teacher/TeacherStudents'
import TeacherPrograms from './pages/teacher/TeacherPrograms'
import StudentLogin from './pages/StudentLogin'
import StudentDashboard from './pages/StudentDashboard'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      
      {/* Teacher Routes */}
      <Route path="/teacher/login" element={<TeacherLogin />} />
      <Route path="/teacher/register" element={<TeacherRegister />} />
      <Route path="/teacher/dashboard-old" element={<TeacherDashboardWithSidebar />} />
      
      {/* New Teacher Routes with separate pages */}
      <Route path="/teacher/dashboard" element={<TeacherDashboard />} />
      <Route path="/teacher/classrooms" element={<TeacherClassrooms />} />
      <Route path="/teacher/students" element={<TeacherStudents />} />
      <Route path="/teacher/programs" element={<TeacherPrograms />} />
      
      {/* Student Routes */}
      <Route path="/student/login" element={<StudentLogin />} />
      <Route path="/student/dashboard" element={<StudentDashboard />} />
      
      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App