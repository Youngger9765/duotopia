import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/toaster'
import HomePage from '@/pages/HomePage'
import LoginPage from '@/pages/LoginPage'
import StudentLoginPage from '@/pages/StudentLoginPage'
import TeacherDashboard from '@/pages/TeacherDashboard'
import StudentDashboard from '@/pages/StudentDashboard'
import TestAccounts from '@/pages/TestAccounts'
import InstitutionalDashboard from '@/pages/InstitutionalDashboard'
import IndividualDashboard from '@/pages/IndividualDashboard'
import ReadingPracticeEditorPage from '@/pages/ReadingPracticeEditorPage'
import { AuthProvider } from '@/contexts/AuthContext'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/student-login" element={<StudentLoginPage />} />
            <Route path="/test-accounts" element={<TestAccounts />} />
            <Route path="/teacher/*" element={<TeacherDashboard />} />
            <Route path="/student/*" element={<StudentDashboard />} />
            <Route path="/institutional/*" element={<InstitutionalDashboard />} />
            <Route path="/individual/*" element={<IndividualDashboard />} />
            <Route path="/reading-practice-editor" element={<ReadingPracticeEditorPage />} />
          </Routes>
        </Router>
        <Toaster />
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App