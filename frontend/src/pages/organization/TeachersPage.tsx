import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { API_URL } from "@/config/api";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import { StaffTable, StaffMember } from "@/components/organization/StaffTable";
import { InviteTeacherDialog } from "@/components/organization/InviteTeacherDialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Users, UserPlus } from "lucide-react";
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
  const [organization, setOrganization] = useState<{ name: string } | null>(
    null,
  );
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">人員管理</h1>
          <p className="text-gray-600 mt-2">管理組織內的教師成員</p>
        </div>
        <Button className="gap-2" onClick={() => setInviteDialogOpen(true)}>
          <UserPlus className="h-4 w-4" />
          邀請教師
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              總教師數
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{teachers.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              活躍教師
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {teachers.filter((t) => t.is_active).length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              管理員
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {
                teachers.filter((t) =>
                  ["org_owner", "org_admin", "school_admin"].includes(t.role),
                ).length
              }
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Teachers Table */}
      <Card>
        <CardHeader>
          <CardTitle>教師列表</CardTitle>
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
            <StaffTable
              staff={teachers}
              organizationId={effectiveOrgId}
              onRoleUpdated={fetchTeachers}
              showEmail={true}
            />
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
