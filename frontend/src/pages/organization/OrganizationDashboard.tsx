import { useEffect, useState, useRef } from "react";
import { useOrganization } from "@/contexts/OrganizationContext";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { OrganizationTree } from "@/components/organization/OrganizationTree";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, School, Users, GraduationCap } from "lucide-react";
import { API_URL } from "@/config/api";

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
  const token = useTeacherAuthStore((state) => state.token);
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

  // Fetch statistics
  useEffect(() => {
    const fetchStats = async () => {
      if (!token) return;

      try {
        setLoadingStats(true);

        // For now, calculate stats from organizations data
        // TODO: Create backend endpoint for aggregated stats
        const orgCount = organizations.length;

        setStats({
          total_organizations: orgCount,
          total_schools: 0, // Will be updated when we fetch schools
          total_teachers: 0,
          total_students: 0,
        });
      } catch (error) {
        console.error("Error fetching stats:", error);
      } finally {
        setLoadingStats(false);
      }
    };

    if (organizations.length > 0) {
      fetchStats();
    }
  }, [token, organizations]);

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
