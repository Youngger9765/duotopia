import { Routes, Route, Navigate } from 'react-router-dom'
import Home from './pages/Home'
import TeacherLogin from './pages/TeacherLogin'
import TeacherRegister from './pages/TeacherRegister'
import TeacherDashboardWithSidebar from './pages/TeacherDashboardWithSidebar'
import TeacherDashboard from './pages/teacher/TeacherDashboard'
import TeacherClassrooms from './pages/teacher/TeacherClassrooms'
import TeacherStudents from './pages/teacher/TeacherStudents'
import TeacherTemplatePrograms from './pages/teacher/TeacherTemplatePrograms'
import ClassroomDetail from './pages/teacher/ClassroomDetail'
import TeacherAssignmentDetailPage from './pages/teacher/TeacherAssignmentDetailPage'
import GradingPage from './pages/teacher/GradingPage'
import StudentLogin from './pages/StudentLogin'
import StudentDashboard from './pages/StudentDashboard'
import StudentAssignmentList from './pages/student/StudentAssignmentList'
import StudentAssignmentDetail from './pages/student/StudentAssignmentDetail'
import AssignmentDetail from './pages/student/AssignmentDetail'
import StudentActivityPage from './pages/student/StudentActivityPage'
import StudentLayout from './components/StudentLayout'
import EmailVerification from './pages/EmailVerification'
import StudentProfile from './pages/student/StudentProfile'
import DatabaseAdminPage from './pages/admin/DatabaseAdminPage'
import DebugPage from './pages/DebugPage'
import TermsOfService from './pages/TermsOfService'
import PricingPage from './pages/PricingPage'
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
      <Route path="/terms" element={<TermsOfService />} />
      <Route path="/pricing" element={<PricingPage />} />

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

      <Route path="/teacher/students" element={<TeacherStudents />} />
      <Route path="/teacher/programs" element={<TeacherTemplatePrograms />} />
      <Route path="/teacher/template-programs/:id" element={<ClassroomDetail isTemplateMode={true} />} />

      {/* Student Routes */}
      <Route path="/student/login" element={<StudentLogin />} />

      {/* Email Verification */}
      <Route path="/verify-email" element={<EmailVerification />} />

      {/* Admin Routes */}
      <Route path="/admin/database" element={<DatabaseAdminPage />} />

      {/* Student Routes with Layout */}
      <Route path="/student" element={<StudentLayout />}>
        <Route path="dashboard" element={<StudentDashboard />} />
        <Route path="assignments" element={<StudentAssignmentList />} />
        <Route path="assignment/:id/detail" element={<StudentAssignmentDetail />} />
        <Route path="assignment/:id" element={<AssignmentDetail />} />
        <Route path="assignment/:assignmentId/activity" element={<StudentActivityPage />} />
        <Route path="assignment/:id/activity/:progressId" element={<AssignmentDetail />} />
        <Route path="progress" element={<div className="p-8 text-center">學習進度頁面開發中...</div>} />
        <Route path="achievements" element={<div className="p-8 text-center">成就頁面開發中...</div>} />
        <Route path="calendar" element={<div className="p-8 text-center">行事曆頁面開發中...</div>} />
        <Route path="messages" element={<div className="p-8 text-center">訊息頁面開發中...</div>} />
        <Route path="profile" element={<StudentProfile />} />
        <Route path="settings" element={<div className="p-8 text-center">設定頁面開發中...</div>} />
      </Route>

      {/* Debug 頁面 */}
      <Route path="/debug" element={<DebugPage />} />

      {/* Default redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </>
  )
}

export default App
