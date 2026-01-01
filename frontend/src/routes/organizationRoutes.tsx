import { Route } from "react-router-dom";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import OrganizationLayout from "@/layouts/OrganizationLayout";
import OrganizationDashboard from "@/pages/organization/OrganizationDashboard";
import SchoolsPage from "@/pages/organization/SchoolsPage";
import TeachersPage from "@/pages/organization/TeachersPage";

/**
 * Organization Routes - Accessible only to users with organization roles
 * Required roles: org_owner, org_admin, school_admin
 */
export const organizationRoutes = (
  <Route
    path="/organization"
    element={
      <ProtectedRoute
        requiredRoles={["org_owner", "org_admin", "school_admin"]}
      >
        <OrganizationLayout />
      </ProtectedRoute>
    }
  >
    {/* Dashboard - Organization structure overview */}
    <Route path="dashboard" element={<OrganizationDashboard />} />

    {/* Schools management under specific organization */}
    <Route path=":orgId/schools" element={<SchoolsPage />} />

    {/* Teachers management under specific organization */}
    <Route path=":orgId/teachers" element={<TeachersPage />} />

    {/* Default schools/teachers pages (use selected org from context) */}
    <Route path="schools" element={<SchoolsPage />} />
    <Route path="teachers" element={<TeachersPage />} />

    {/* Default redirect to dashboard */}
    <Route index element={<OrganizationDashboard />} />
  </Route>
);
