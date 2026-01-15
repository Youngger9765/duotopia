import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { API_URL } from "@/config/api";
import { useProgramAPI } from "@/hooks/useProgramAPI";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import { MaterialCreateDialog } from "@/components/organization/MaterialCreateDialog";
import { MaterialEditDialog } from "@/components/organization/MaterialEditDialog";
import { LessonDialog } from "@/components/LessonDialog";
import { ProgramTreeView } from "@/components/shared/ProgramTreeView";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  OrganizationLesson,
  OrganizationProgram,
} from "@/types/organizationPrograms";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  BookOpen,
  Loader2,
} from "lucide-react";
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
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingProgram, setEditingProgram] =
    useState<OrganizationProgram | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [organization, setOrganization] = useState<{ name: string } | null>(null);

  // Lesson dialog state
  const [lessonDialogType, setLessonDialogType] = useState<
    "create" | "edit" | "delete" | null
  >(null);
  const [selectedLesson, setSelectedLesson] =
    useState<OrganizationLesson | null>(null);
  const [lessonProgramId, setLessonProgramId] = useState<number | undefined>();

  type ItemWithId = { id?: number };

  const effectiveOrgId =
    orgId ||
    (selectedNode?.type === "organization" ? selectedNode.id : undefined);

  // Use unified Programs API
  const api = useProgramAPI({
    scope: 'organization',
    organizationId: effectiveOrgId,
  });

  useEffect(() => {
    const fetchOrg = async () => {
      if (!effectiveOrgId || !token) return;
      try {
        const res = await fetch(`${API_URL}/api/organizations/${effectiveOrgId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setOrganization(data);
        }
      } catch (error) {
        console.error('Failed to fetch organization:', error);
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

  const handleCreate = () => {
    setShowCreateDialog(true);
  };

  const handleEdit = (program: OrganizationProgram) => {
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
        // Update state without re-fetching
        setPrograms(prevPrograms =>
          prevPrograms.filter(program => program.id !== deleteConfirmId)
        );
        toast.success("教材刪除成功");
        setDeleteConfirmId(null);
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

  // Lesson handlers
  const handleCreateLesson = (programId: number) => {
    setSelectedLesson(null);
    setLessonProgramId(programId);
    setLessonDialogType("create");
  };

  const handleEditLesson = (programId: number, lessonId: number) => {
    const program = programs.find((p) => p.id === programId);
    const lesson = program?.lessons?.find((l) => l.id === lessonId);
    if (lesson && program) {
      setSelectedLesson(lesson);
      setLessonProgramId(program.id);
      setLessonDialogType("edit");
    }
  };

  const handleSaveLesson = (lessonData: OrganizationLesson) => {
    if (lessonDialogType === "create" && lessonProgramId) {
      // lessonData is already the created lesson from LessonDialog
      setPrograms(prevPrograms =>
        prevPrograms.map(program => {
          if (program.id === lessonProgramId) {
            return {
              ...program,
              lessons: [...(program.lessons || []), lessonData],
            };
          }
          return program;
        })
      );
      toast.success("課程單元新增成功");
    } else if (lessonDialogType === "edit") {
      // lessonData is already the updated lesson
      setPrograms(prevPrograms =>
        prevPrograms.map(program => ({
          ...program,
          lessons: program.lessons?.map(lesson =>
            lesson.id === lessonData.id ? lessonData : lesson
          ),
        }))
      );
      toast.success("課程單元更新成功");
    }

    setLessonDialogType(null);
    setSelectedLesson(null);
    setLessonProgramId(undefined);
  };

  const handleDeleteLesson = async (lessonId: number) => {
    try {
      await api.deleteLesson(lessonId);

      // Update state without re-fetching
      setPrograms(prevPrograms =>
        prevPrograms.map(program => ({
          ...program,
          lessons: program.lessons?.filter(lesson => lesson.id !== lessonId),
        }))
      );

      toast.success("課程單元刪除成功");
      setLessonDialogType(null);
      setSelectedLesson(null);
    } catch (error) {
      console.error("Failed to delete lesson:", error);
      toast.error("刪除失敗");
    }
  };

  const handleDeleteContent = async (contentId: number) => {
    try {
      await api.deleteContent(contentId);

      // Update state without re-fetching
      setPrograms(prevPrograms =>
        prevPrograms.map(program => ({
          ...program,
          lessons: program.lessons?.map(lesson => ({
            ...lesson,
            contents: lesson.contents?.filter(content => content.id !== contentId),
          })),
        }))
      );

      toast.success("內容刪除成功");
    } catch (error) {
      console.error("Failed to delete content:", error);
      toast.error("刪除失敗");
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
      <Breadcrumb items={[
        { label: "組織管理" },
        { label: organization?.name || "...", href: `/organization/${orgId}` },
        { label: "組織教材" }
      ]} />

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
            <ErrorMessage message={error} onRetry={() => window.location.reload()} />
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
                showCreateButton={canManageMaterials}
                createButtonText="新增教材"
                onCreateClick={handleCreate}
                onCreate={(level, parentId) => {
                  if (level === 1) {
                    handleCreateLesson(parentId as number);
                  }
                }}
                onEdit={(item, level) => {
                  if (level === 0) {
                    const program = programs.find((p) => p.id === item.id);
                    if (program) handleEdit(program);
                  } else if (level === 1) {
                    const lessonItem = item as OrganizationLesson;
                    if (!lessonItem.id) {
                      return;
                    }
                    const program = programs.find(p =>
                      p.lessons?.some((l) => l.id === lessonItem.id)
                    );
                    if (program) {
                      handleEditLesson(program.id, lessonItem.id);
                    }
                  }
                }}
                onDelete={(item, level) => {
                  if (level === 0 && canManageMaterials) {
                    const itemId = (item as ItemWithId).id;
                    if (!itemId) {
                      return;
                    }
                    handleDelete(itemId);
                  } else if (level === 1 && canManageMaterials) {
                    // Show delete confirmation dialog
                    const lessonItem = item as OrganizationLesson;
                    if (!lessonItem.id) {
                      return;
                    }
                    const program = programs.find(p =>
                      p.lessons?.some((l) => l.id === lessonItem.id)
                    );
                    const lesson = program?.lessons?.find(
                      (l) => l.id === lessonItem.id
                    );
                    if (lesson && program) {
                      setSelectedLesson(lesson);
                      setLessonProgramId(program.id);
                      setLessonDialogType("delete");
                    }
                  } else if (level === 2 && canManageMaterials) {
                    const itemId = (item as ItemWithId).id;
                    if (!itemId) {
                      return;
                    }
                    handleDeleteContent(itemId);
                  }
                }}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      {effectiveOrgId && (
        <MaterialCreateDialog
          organizationId={effectiveOrgId}
          open={showCreateDialog}
          onOpenChange={setShowCreateDialog}
          onSuccess={(newProgram) => {
            setPrograms(prevPrograms => [...prevPrograms, newProgram]);
          }}
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
          onSuccess={(updatedProgram) => {
            setPrograms(prevPrograms =>
              prevPrograms.map(p =>
                p.id === updatedProgram.id
                  ? { ...updatedProgram, lessons: p.lessons || [] }
                  : p
              )
            );
          }}
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

      {/* Lesson Dialog */}
      <LessonDialog
        lesson={selectedLesson}
        dialogType={lessonDialogType}
        programId={lessonProgramId}
        onClose={() => {
          setLessonDialogType(null);
          setSelectedLesson(null);
          setLessonProgramId(undefined);
        }}
        onSave={handleSaveLesson}
        onDelete={handleDeleteLesson}
      />

    </div>
  );
}
