import { Navigate } from 'react-router-dom';
import { useTeacherAuthStore } from '@/stores/teacherAuthStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const isAuthenticated = useTeacherAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/teacher/login" replace />;
  }

  return <>{children}</>;
}
