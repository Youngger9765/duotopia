import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";

/**
 * RoleBasedRedirect - Automatically redirects users based on their roles
 *
 * Logic:
 * - If user has organization roles (org_owner, org_admin, school_admin) → /organization/dashboard
 * - Otherwise → /teacher/dashboard
 */
export function RoleBasedRedirect() {
  const { isAuthenticated, token } = useTeacherAuthStore();
  const [redirectPath, setRedirectPath] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkRolesAndRedirect = async () => {
      if (!isAuthenticated || !token) {
        setRedirectPath("/teacher/login");
        setIsLoading(false);
        return;
      }

      try {
        // Priority: Use user.role if available (from login response)
        const currentUser = useTeacherAuthStore.getState().user;
        if (currentUser?.role) {
          // Already have role info, directly determine redirect
          const hasOrgRole = [
            "org_owner",
            "org_admin",
            "school_admin",
          ].includes(currentUser.role);
          setRedirectPath(
            hasOrgRole ? "/organization/dashboard" : "/teacher/dashboard",
          );
          setIsLoading(false);
          return;
        }

        // Fallback: Fetch roles if not in user object (legacy login)
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/api/teachers/me/roles`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );

        if (response.ok) {
          const data = await response.json();
          const userRoles = data.all_roles || [];

          // Check if user has any organization role
          const hasOrgRole = userRoles.some((role: string) =>
            ["org_owner", "org_admin", "school_admin"].includes(role),
          );

          if (hasOrgRole) {
            setRedirectPath("/organization/dashboard");
          } else {
            setRedirectPath("/teacher/dashboard");
          }
        } else {
          // Default to teacher dashboard if API fails
          setRedirectPath("/teacher/dashboard");
        }
      } catch (error) {
        console.error("Failed to check roles for redirect:", error);
        setRedirectPath("/teacher/dashboard");
      } finally {
        setIsLoading(false);
      }
    };

    checkRolesAndRedirect();
  }, [isAuthenticated, token]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-gray-500">正在導向...</div>
      </div>
    );
  }

  if (redirectPath) {
    return <Navigate to={redirectPath} replace />;
  }

  // Fallback
  return <Navigate to="/teacher/dashboard" replace />;
}
