import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useOrganization } from "@/contexts/OrganizationContext";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { OrganizationTree } from "@/components/organization/OrganizationTree";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, School, Users, GraduationCap } from "lucide-react";
import { API_URL } from "@/config/api";
import { OrganizationPointsBalance } from "@/components/OrganizationPointsBalance";
import { OrganizationPointsHistory } from "@/components/OrganizationPointsHistory";

interface OrganizationStats {
  total_organizations: number;
  total_schools: number;
  total_teachers: number;
  total_students: number;
}

interface Organization {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

interface SchoolData {
  id: string;
  organization_id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

/**
 * OrganizationDashboard - Main dashboard for organization management
 * Shows organization hierarchy tree and statistics
 */
export default function OrganizationDashboard() {
  const navigate = useNavigate();
  const token = useTeacherAuthStore((state) => state.token);
  const userRoles = useTeacherAuthStore((state) => state.userRoles);
  const { organizations, setOrganizations, selectedNode, setIsFetchingOrgs } =
    useOrganization();
  const [stats, setStats] = useState<OrganizationStats>({
    total_organizations: 0,
    total_schools: 0,
    total_teachers: 0,
    total_students: 0,
  });
  const [loadingStats, setLoadingStats] = useState(true);
  const hasFetchedRef = useRef(false);
  const hasRedirectedRef = useRef(false);

  // Fetch organizations on mount
  useEffect(() => {
    const fetchOrganizations = async () => {
      if (!token || hasFetchedRef.current || organizations.length > 0) {
        return;
      }

      hasFetchedRef.current = true;
      setIsFetchingOrgs(true);

      try {
        const response = await fetch(`${API_URL}/api/organizations`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
          const data = await response.json();
          setOrganizations(data);
        } else {
          console.error("Failed to fetch organizations:", response.status);
        }
      } catch (error) {
        console.error("Error fetching organizations:", error);
      } finally {
        setIsFetchingOrgs(false);
      }
    };

    fetchOrganizations();
  }, [token, organizations.length, setOrganizations, setIsFetchingOrgs]);

  // Auto-redirect based on user role
  useEffect(() => {
    const checkAndRedirect = async () => {
      // If user is already on dashboard, respect their choice and don't redirect
      const currentPath = window.location.pathname;
      if (currentPath === "/organization/dashboard") {
        console.log("👤 User is on dashboard, respecting their choice");
        return;
      }

      if (
        !token ||
        !userRoles ||
        userRoles.length === 0 ||
        hasRedirectedRef.current
      ) {
        return;
      }

      // Wait for organizations to be fetched first
      if (hasFetchedRef.current === false) {
        return;
      }

      const hasOrgOwner = userRoles.includes("org_owner");
      const hasOrgAdmin = userRoles.includes("org_admin");
      const hasSchoolAdmin = userRoles.includes("school_admin");
      const hasSchoolDirector = userRoles.includes("school_director");

      // org_owner can stay on dashboard (see all organizations)
      if (hasOrgOwner) {
        console.log("🏢 org_owner: staying on dashboard");
        return;
      }

      // org_admin should go to their first accessible organization
      if (hasOrgAdmin) {
        if (organizations.length > 0) {
          console.log("🏢 org_admin: redirecting to first organization");
          hasRedirectedRef.current = true;
          navigate(`/organization/${organizations[0].id}`);
        } else {
          console.warn("⚠️ org_admin but no organizations found");
        }
        return;
      }

      // school-level users should go to their first school
      if (hasSchoolAdmin || hasSchoolDirector) {
        try {
          console.log("🏫 school-level user: fetching schools for redirect");
          const response = await fetch(`${API_URL}/api/schools`, {
            headers: { Authorization: `Bearer ${token}` },
          });

          if (response.ok) {
            const schools = await response.json();
            if (schools.length > 0) {
              console.log("🏫 Redirecting to first school", schools[0].id);
              hasRedirectedRef.current = true;
              navigate(`/organization/schools/${schools[0].id}`);
            } else {
              console.warn("⚠️ school-level user but no schools found");
            }
          } else {
            console.error("❌ Failed to fetch schools:", response.status);
          }
        } catch (error) {
          console.error("❌ Error fetching schools for redirect:", error);
        }
      }
    };

    checkAndRedirect();
  }, [token, userRoles, organizations, navigate]);

  // Fetch statistics from backend API
  useEffect(() => {
    const fetchStats = async () => {
      if (!token) return;

      try {
        setLoadingStats(true);

        // Try to fetch stats from backend API
        const response = await fetch(`${API_URL}/api/organizations/stats`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
          const data = await response.json();
          setStats({
            total_organizations:
              data.total_organizations || organizations.length,
            total_schools: data.total_schools || 0,
            total_teachers: data.total_teachers || 0,
            total_students: data.total_students || 0,
          });
        } else {
          // Fallback: count from local organizations data
          console.warn("Stats API not available, using fallback");
          setStats({
            total_organizations: organizations.length,
            total_schools: 0,
            total_teachers: 0,
            total_students: 0,
          });
        }
      } catch (error) {
        console.error("Error fetching stats:", error);
        // Fallback on error
        setStats({
          total_organizations: organizations.length,
          total_schools: 0,
          total_teachers: 0,
          total_students: 0,
        });
      } finally {
        setLoadingStats(false);
      }
    };

    fetchStats();
  }, [token, organizations.length]);

  const handleNodeSelect = (
    type: "organization" | "school",
    data: Organization | SchoolData,
  ) => {
    console.log("Selected node:", type, data);
    // TODO: Show detailed information in a side panel
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">組織架構總覽</h1>
        <p className="text-gray-600 mt-2">管理您的組織、學校和成員</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">組織總數</CardTitle>
            <Building2 className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? "..." : stats.total_organizations}
            </div>
            <p className="text-xs text-gray-500 mt-1">您管理的組織</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">學校總數</CardTitle>
            <School className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? "..." : stats.total_schools}
            </div>
            <p className="text-xs text-gray-500 mt-1">所有組織下的學校</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">教師總數</CardTitle>
            <Users className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? "..." : stats.total_teachers}
            </div>
            <p className="text-xs text-gray-500 mt-1">活躍教師帳號</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">學生總數</CardTitle>
            <GraduationCap className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loadingStats ? "..." : stats.total_students}
            </div>
            <p className="text-xs text-gray-500 mt-1">所有班級的學生</p>
          </CardContent>
        </Card>
      </div>

      {/* Points Section - Only show for specific organization */}
      {selectedNode && selectedNode.type === "organization" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <OrganizationPointsBalance organizationId={selectedNode.data.id} />
          </div>
          <div className="lg:col-span-2">
            <OrganizationPointsHistory organizationId={selectedNode.data.id} />
          </div>
        </div>
      )}

      {/* Organization Tree */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            組織架構圖
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selectedNode && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-sm font-medium text-blue-900">
                目前選取：
                {selectedNode.type === "organization" ? "組織" : "學校"}
              </div>
              <div className="text-lg font-semibold text-blue-900 mt-1">
                {selectedNode.data.display_name || selectedNode.data.name}
              </div>
              {selectedNode.data.description && (
                <div className="text-sm text-blue-700 mt-1">
                  {selectedNode.data.description}
                </div>
              )}
            </div>
          )}

          <OrganizationTree onNodeSelect={handleNodeSelect} />
        </CardContent>
      </Card>
    </div>
  );
}
