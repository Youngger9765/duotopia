import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { API_URL } from "@/config/api";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import { MaterialCreateDialog } from "@/components/organization/MaterialCreateDialog";
import { MaterialEditDialog } from "@/components/organization/MaterialEditDialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { BookOpen, Plus, Edit2, Trash2, Loader2 } from "lucide-react";
import { toast } from "sonner";

interface ProgramData {
  id: number;
  organization_id: string;
  name: string;
  description?: string;
  level?: string;
  total_hours?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * MaterialsPage - Manage organization-level educational programs/materials
 */
export default function MaterialsPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const token = useTeacherAuthStore((state) => state.token);
  const user = useTeacherAuthStore((state) => state.user);
  const { selectedNode } = useOrganization();

  const [programs, setPrograms] = useState<ProgramData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingProgram, setEditingProgram] = useState<ProgramData | null>(
    null,
  );
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  const effectiveOrgId =
    orgId ||
    (selectedNode?.type === "organization" ? selectedNode.id : undefined);

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

      const response = await fetch(
        `${API_URL}/api/organizations/${effectiveOrgId}/programs`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setPrograms(data);
      } else {
        setError(`載入教材列表失敗：${response.status}`);
        toast.error("載入教材列表失敗");
      }
    } catch (error) {
      console.error("Failed to fetch programs:", error);
      setError("網路連線錯誤，請檢查您的網路連線");
      toast.error("網路錯誤");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setShowCreateDialog(true);
  };

  const handleEdit = (program: ProgramData) => {
    setEditingProgram(program);
    setShowEditDialog(true);
  };

  const handleDelete = async (programId: number) => {
    if (!deleteConfirmId) {
      setDeleteConfirmId(programId);
      return;
    }

    setDeleting(true);
    try {
      const response = await fetch(
        `${API_URL}/api/organizations/${effectiveOrgId}/programs/${programId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        toast.success("教材刪除成功");
        setDeleteConfirmId(null);
        fetchPrograms();
      } else {
        const error = await response.json();
        toast.error(error.detail || "刪除失敗");
      }
    } catch (error) {
      console.error("Failed to delete program:", error);
      toast.error("網路錯誤");
    } finally {
      setDeleting(false);
    }
  };

  const getLevelLabel = (level?: string) => {
    if (!level) return "-";
    return level.toUpperCase();
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
      <Breadcrumb items={[{ label: "組織管理" }, { label: "組織教材" }]} />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">組織教材</h1>
          <p className="text-gray-600 mt-2">管理組織層級的教學教材與課程</p>
        </div>
        {canManageMaterials && (
          <Button onClick={handleCreate} className="gap-2">
            <Plus className="h-4 w-4" />
            新增教材
          </Button>
        )}
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
            <ErrorMessage message={error} onRetry={fetchPrograms} />
          ) : programs.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500 mb-2">此組織尚無教材</p>
              {canManageMaterials && (
                <Button
                  variant="outline"
                  onClick={handleCreate}
                  className="mt-4 gap-2"
                >
                  <Plus className="h-4 w-4" />
                  新增第一個教材
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>教材名稱</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead>等級</TableHead>
                  <TableHead>時數</TableHead>
                  <TableHead>建立時間</TableHead>
                  <TableHead>狀態</TableHead>
                  {canManageMaterials && (
                    <TableHead className="text-right">操作</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {programs.map((program) => (
                  <TableRow key={program.id}>
                    <TableCell className="font-medium">
                      {program.name}
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      {program.description || "-"}
                    </TableCell>
                    <TableCell>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {getLevelLabel(program.level)}
                      </span>
                    </TableCell>
                    <TableCell>{program.total_hours || "-"}</TableCell>
                    <TableCell>
                      {new Date(program.created_at).toLocaleDateString("zh-TW")}
                    </TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          program.is_active
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {program.is_active ? "啟用" : "停用"}
                      </span>
                    </TableCell>
                    {canManageMaterials && (
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(program)}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(program.id)}
                            disabled={deleting}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            {deleting && deleteConfirmId === program.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      {effectiveOrgId && (
        <MaterialCreateDialog
          organizationId={effectiveOrgId}
          open={showCreateDialog}
          onOpenChange={setShowCreateDialog}
          onSuccess={fetchPrograms}
        />
      )}

      {/* Edit Dialog */}
      {effectiveOrgId && (
        <MaterialEditDialog
          program={editingProgram}
          organizationId={effectiveOrgId}
          open={showEditDialog}
          onOpenChange={(open) => {
            setShowEditDialog(open);
            if (!open) {
              setEditingProgram(null);
            }
          }}
          onSuccess={fetchPrograms}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmId !== null}
        onOpenChange={() => setDeleteConfirmId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>確認刪除</DialogTitle>
            <DialogDescription>
              確定要刪除此教材嗎？此操作無法復原。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteConfirmId(null)}
              disabled={deleting}
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}
              disabled={deleting}
            >
              {deleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  刪除中...
                </>
              ) : (
                "確認刪除"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
