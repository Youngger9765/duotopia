import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { API_URL } from "@/config/api";
import { useProgramAPI } from "@/hooks/useProgramAPI";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import { ProgramTreeView } from "@/components/shared/ProgramTreeView";
import { ProgramTreeProgram } from "@/hooks/useProgramTree";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OrganizationProgram } from "@/types/organizationPrograms";
import { BookOpen } from "lucide-react";
import { toast } from "sonner";

/**
 * MaterialsPage - Manage organization-level educational programs/materials
 */
export default function MaterialsPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const token = useTeacherAuthStore((state) => state.token);
  const user = useTeacherAuthStore((state) => state.user);
  const { selectedNode } = useOrganization();

  const [programs, setPrograms] = useState<OrganizationProgram[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [organization, setOrganization] = useState<{ name: string } | null>(
    null,
  );

  const effectiveOrgId =
    orgId ||
    (selectedNode?.type === "organization" ? selectedNode.id : undefined);

  // Use unified Programs API
  const api = useProgramAPI({
    scope: "organization",
    organizationId: effectiveOrgId,
  });

  // Memoized callback to prevent infinite loop
  const handleProgramsChange = useCallback((updatedPrograms: ProgramTreeProgram[]) => {
    setPrograms(updatedPrograms as OrganizationProgram[]);
  }, []);

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
      fetchPrograms();
    }
  }, [effectiveOrgId]);

  const fetchPrograms = async () => {
    if (!effectiveOrgId) return;

    try {
      setLoading(true);
      setError(null);

      const data = await api.getPrograms();
      setPrograms(data);
    } catch (error) {
      console.error("Failed to fetch programs:", error);
      setError("載入教材列表失敗");
      toast.error("載入教材列表失敗");
    } finally {
      setLoading(false);
    }
  };

  // Check if current user can manage materials
  const canManageMaterials =
    user?.role === "org_owner" || user?.role === "org_admin";

  if (!effectiveOrgId) {
    return (
      <div className="p-8 text-center">
        <BookOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
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
          { label: "組織教材" },
        ]}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">組織教材</h1>
          <p className="text-gray-600 mt-2">管理組織層級的教學教材與課程</p>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              總教材數
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{programs.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              啟用中
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {programs.filter((p) => p.is_active).length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              總時數
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {programs.reduce((sum, p) => sum + (p.total_hours || 0), 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Programs Table */}
      <Card>
        <CardHeader>
          <CardTitle>教材列表</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <LoadingSpinner />
          ) : error ? (
            <ErrorMessage
              message={error}
              onRetry={() => window.location.reload()}
            />
          ) : programs.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500 mb-2">此組織尚無教材</p>
              {canManageMaterials && (
                <p className="text-sm text-gray-400 mt-4">
                  點擊上方「新增教材」按鈕開始建立
                </p>
              )}
            </div>
          ) : (
            <div className="mt-4">
              <ProgramTreeView
                programs={programs}
                onProgramsChange={handleProgramsChange}
                onRefresh={fetchPrograms}
                showCreateButton={canManageMaterials}
                createButtonText="新增教材"
                scope="organization"
                organizationId={effectiveOrgId}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
