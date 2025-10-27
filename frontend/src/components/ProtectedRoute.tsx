import { Navigate } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

export function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
  const isAuthenticated = useTeacherAuthStore((state) => state.isAuthenticated);
  const user = useTeacherAuthStore((state) => state.user);

  if (!isAuthenticated) {
    return <Navigate to="/teacher/login" replace />;
  }

  // 如果需要 admin 權限但用戶不是 admin
  if (requireAdmin && user?.role !== "admin") {
    return <Navigate to="/teacher/dashboard" replace />;
  }

  return <>{children}</>;
}
