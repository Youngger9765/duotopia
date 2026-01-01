import { Route } from "react-router-dom";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import OrganizationLayout from "@/layouts/OrganizationLayout";
import OrganizationDashboard from "@/pages/organization/OrganizationDashboard";
import SchoolsPage from "@/pages/organization/SchoolsPage";
import TeachersPage from "@/pages/organization/TeachersPage";
import OrganizationEditPage from "@/pages/organization/OrganizationEditPage";
import SchoolEditPage from "@/pages/organization/SchoolEditPage";
import OrganizationsListPage from "@/pages/organization/OrganizationsListPage";

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

    {/* All organizations list page - Admin only */}
    <Route
      path="all"
      element={
        <ProtectedRoute requireAdmin={true}>
          <OrganizationsListPage />
        </ProtectedRoute>
      }
    />

    {/* Organization detail page */}
    <Route path=":orgId" element={<OrganizationEditPage />} />

    {/* Schools management under specific organization */}
    <Route path=":orgId/schools" element={<SchoolsPage />} />

    {/* Teachers management under specific organization */}
    <Route path=":orgId/teachers" element={<TeachersPage />} />

    {/* School edit page */}
    <Route path="schools/:schoolId/edit" element={<SchoolEditPage />} />

    {/* Default schools/teachers pages (use selected org from context) */}
    <Route path="schools" element={<SchoolsPage />} />
    <Route path="teachers" element={<TeachersPage />} />

    {/* Default redirect to dashboard */}
    <Route index element={<OrganizationDashboard />} />
  </Route>
);
