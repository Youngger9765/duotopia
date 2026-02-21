import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { API_URL } from "@/config/api";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import {
  StaffTable,
  StaffMember,
  StaffSortField,
  SortDirection,
} from "@/components/organization/StaffTable";
import { InviteTeacherDialog } from "@/components/organization/InviteTeacherDialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Users,
  UserPlus,
  Search,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";

// Use StaffMember from StaffTable component

/**
 * TeachersPage - Manage teachers within the organization portal
 */
export default function TeachersPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const token = useTeacherAuthStore((state) => state.token);
  const { selectedNode } = useOrganization();

  const [teachers, setTeachers] = useState<StaffMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [organization, setOrganization] = useState<{
    name: string;
    teacher_license_count?: number;
  } | null>(null);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);

  // Search, sort, pagination state
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<StaffSortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const effectiveOrgId =
    orgId ||
    (selectedNode?.type === "organization" ? selectedNode.id : undefined);

  useEffect(() => {
    const fetchOrg = async () => {
      if (!effectiveOrgId || !token) return;
      try {
        const res = await fetch(
          `${API_URL}/api/organizations/${effectiveOrgId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );
        if (res.ok) {
          const data = await res.json();
          setOrganization(data);
        }
      } catch (error) {
        console.error("Failed to fetch organization:", error);
      }
    };
    if (effectiveOrgId && token) {
      fetchOrg();
    }
  }, [effectiveOrgId, token]);

  useEffect(() => {
    if (effectiveOrgId) {
      fetchTeachers();
    }
  }, [effectiveOrgId]);

  const fetchTeachers = async () => {
    if (!effectiveOrgId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_URL}/api/organizations/${effectiveOrgId}/teachers`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setTeachers(data);
      } else {
        setError(`載入教師列表失敗：${response.status}`);
        toast.error("載入教師列表失敗");
      }
    } catch (error) {
      console.error("Failed to fetch teachers:", error);
      setError("網路連線錯誤，請檢查您的網路連線");
      toast.error("網路錯誤");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (
    teacher: StaffMember,
    isActive: boolean,
  ) => {
    try {
      const response = await fetch(
        `${API_URL}/api/organizations/${effectiveOrgId}/teachers/${teacher.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ role: teacher.role, is_active: isActive }),
        },
      );

      if (response.ok) {
        toast.success(isActive ? "教師已啟用" : "教師已停用");
        fetchTeachers();
      } else {
        toast.error("更新狀態失敗");
      }
    } catch (error) {
      console.error("Failed to toggle teacher status:", error);
      toast.error("網路錯誤");
    }
  };

  const handleSort = (field: StaffSortField) => {
    if (sortField === field) {
      // Cycle through: asc -> desc -> null
      if (sortDirection === "asc") {
        setSortDirection("desc");
      } else if (sortDirection === "desc") {
        setSortField(null);
        setSortDirection(null);
      }
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
    setCurrentPage(1);
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
  };

  // Filter, sort, and paginate teachers
  const filteredTeachers = teachers.filter((teacher) => {
    const searchLower = searchQuery.toLowerCase();
    return (
      teacher.name.toLowerCase().includes(searchLower) ||
      teacher.email.toLowerCase().includes(searchLower)
    );
  });

  const sortedTeachers = [...filteredTeachers].sort((a, b) => {
    if (!sortField || !sortDirection) return 0;

    let aValue: string | number | undefined;
    let bValue: string | number | undefined;

    switch (sortField) {
      case "name":
        aValue = a.name;
        bValue = b.name;
        break;
      case "email":
        aValue = a.email;
        bValue = b.email;
        break;
      case "role":
        aValue = a.role;
        bValue = b.role;
        break;
      case "created_at":
        aValue = new Date(a.created_at).getTime();
        bValue = new Date(b.created_at).getTime();
        break;
    }

    if (typeof aValue === "string" && typeof bValue === "string") {
      return sortDirection === "asc"
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    } else {
      const numA = Number(aValue);
      const numB = Number(bValue);
      return sortDirection === "asc" ? numA - numB : numB - numA;
    }
  });

  const totalPages = Math.ceil(sortedTeachers.length / itemsPerPage);
  const paginatedTeachers = sortedTeachers.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage,
  );

  // Role management is now handled by StaffTable component

  if (!effectiveOrgId) {
    return (
      <div className="p-8 text-center">
        <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <p className="text-gray-500">請先選擇組織</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: "組織管理" },
          {
            label: organization?.name || "...",
            href: `/organization/${orgId}`,
          },
          { label: "人員管理" },
        ]}
      />

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">人員管理</h1>
        <p className="text-gray-600 mt-2">管理組織內的教師成員</p>
      </div>

      {/* Statistics */}
      <div
        className="grid gap-6"
        style={{ gridTemplateColumns: "repeat(auto-fill, 200px)" }}
      >
        <Card
          className="flex flex-col items-center justify-center"
          style={{ width: 200, height: 200 }}
        >
          <Users className="h-8 w-8 text-blue-600 mb-2" />
          <div className="text-3xl font-bold">{teachers.length}</div>
          <p className="text-sm text-gray-500 mt-2">總教師數</p>
        </Card>

        <Card
          className="flex flex-col items-center justify-center"
          style={{ width: 200, height: 200 }}
        >
          <Users className="h-8 w-8 text-green-600 mb-2" />
          <div className="text-3xl font-bold">
            {teachers.filter((t) => t.is_active).length}
          </div>
          <p className="text-sm text-gray-500 mt-2">活躍教師</p>
        </Card>

        <Card
          className="flex flex-col items-center justify-center"
          style={{ width: 200, height: 200 }}
        >
          <Users className="h-8 w-8 text-purple-600 mb-2" />
          <div className="text-3xl font-bold">
            {
              teachers.filter((t) =>
                ["org_owner", "org_admin", "school_admin"].includes(t.role),
              ).length
            }
          </div>
          <p className="text-sm text-gray-500 mt-2">管理員</p>
        </Card>

        {/* License Status Card */}
        {organization?.teacher_license_count !== undefined && (
          <Card
            className="flex flex-col items-center justify-center"
            style={{ width: 200, height: 200 }}
          >
            {(() => {
              const licenseCount = organization.teacher_license_count;
              const usedCount = teachers.length;
              const usageRate =
                licenseCount > 0 ? (usedCount / licenseCount) * 100 : 0;

              // Determine color based on usage rate
              let iconColor = "text-blue-600";
              let textColor = "text-gray-900";
              if (usageRate >= 95) {
                iconColor = "text-red-600";
                textColor = "text-red-600";
              } else if (usageRate >= 80) {
                iconColor = "text-orange-600";
                textColor = "text-orange-600";
              }

              return (
                <>
                  <Users className={`h-8 w-8 ${iconColor} mb-2`} />
                  <div className={`text-3xl font-bold ${textColor}`}>
                    {usedCount} / {licenseCount}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">授權狀況</p>
                  <p className={`text-xs ${textColor} mt-1`}>
                    {usageRate.toFixed(0)}% 使用
                  </p>
                </>
              );
            })()}
          </Card>
        )}
      </div>

      {/* Teachers Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle>教師列表</CardTitle>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜尋姓名或 Email..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-9 w-64"
              />
            </div>
            <Button className="gap-2" onClick={() => setInviteDialogOpen(true)}>
              <UserPlus className="h-4 w-4" />
              邀請教師
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <LoadingSpinner />
          ) : error ? (
            <ErrorMessage message={error} onRetry={fetchTeachers} />
          ) : teachers.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500 mb-2">此組織尚無教師</p>
              <Button
                variant="outline"
                onClick={() => setInviteDialogOpen(true)}
                className="mt-4 gap-2"
              >
                <UserPlus className="h-4 w-4" />
                邀請第一位教師
              </Button>
            </div>
          ) : (
            <>
              <StaffTable
                staff={paginatedTeachers}
                organizationId={effectiveOrgId}
                onRoleUpdated={fetchTeachers}
                onToggleStatus={handleToggleStatus}
                sortField={sortField}
                sortDirection={sortDirection}
                onSort={handleSort}
                showEmail={true}
              />

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-3 mt-6">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setCurrentPage((prev) => Math.max(1, prev - 1))
                    }
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="text-sm text-gray-600">
                    第 {currentPage} 頁 / 共 {totalPages} 頁（共{" "}
                    {filteredTeachers.length} 位教師）
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setCurrentPage((prev) => Math.min(totalPages, prev + 1))
                    }
                    disabled={currentPage === totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Invite Teacher Dialog */}
      {effectiveOrgId && (
        <InviteTeacherDialog
          organizationId={effectiveOrgId}
          open={inviteDialogOpen}
          onOpenChange={setInviteDialogOpen}
          onSuccess={fetchTeachers}
        />
      )}
    </div>
  );
}
