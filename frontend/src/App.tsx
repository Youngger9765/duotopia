import { Routes, Route, Navigate } from 'react-router-dom'
import Home from './pages/Home'
import TeacherLogin from './pages/TeacherLogin'
import TeacherRegister from './pages/TeacherRegister'
import TeacherDashboardWithSidebar from './pages/TeacherDashboardWithSidebar'
import TeacherDashboard from './pages/teacher/TeacherDashboard'
import TeacherClassrooms from './pages/teacher/TeacherClassrooms'
import TeacherStudents from './pages/teacher/TeacherStudents'
import TeacherPrograms from './pages/teacher/TeacherPrograms'
import ClassroomDetail from './pages/teacher/ClassroomDetail'
import TeacherAssignmentDetailPage from './pages/teacher/TeacherAssignmentDetailPage'
import StudentGradingPage from './pages/teacher/StudentGradingPage'
import GradingPage from './pages/teacher/GradingPage'
import StudentLogin from './pages/StudentLogin'
import StudentDashboard from './pages/StudentDashboard'
import { Toaster } from 'sonner'

function App() {
  return (
    <>
      <Toaster
        position="top-center"
        richColors
        closeButton
        duration={3000}
      />
      <Routes>
      <Route path="/" element={<Home />} />

      {/* Teacher Routes */}
      <Route path="/teacher/login" element={<TeacherLogin />} />
      <Route path="/teacher/register" element={<TeacherRegister />} />
      <Route path="/teacher/dashboard-old" element={<TeacherDashboardWithSidebar />} />

      {/* New Teacher Routes with separate pages */}
      <Route path="/teacher/dashboard" element={<TeacherDashboard />} />
      <Route path="/teacher/classrooms" element={<TeacherClassrooms />} />
      <Route path="/teacher/classroom/:id" element={<ClassroomDetail />} />
      <Route path="/teacher/classroom/:classroomId/assignment/:assignmentId" element={<TeacherAssignmentDetailPage />} />
      <Route path="/teacher/classroom/:classroomId/assignment/:assignmentId/grading" element={<GradingPage />} />
      <Route path="/teacher/classroom/:classroomId/assignment/:assignmentId/grade/:studentId" element={<StudentGradingPage />} />

      <Route path="/teacher/students" element={<TeacherStudents />} />
      <Route path="/teacher/programs" element={<TeacherPrograms />} />

      {/* Student Routes */}
      <Route path="/student/login" element={<StudentLogin />} />
      <Route path="/student/dashboard" element={<StudentDashboard />} />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </>
  )
}

export default App
