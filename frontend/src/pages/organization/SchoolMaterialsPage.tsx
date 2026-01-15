import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import { ProgramTreeView } from "@/components/shared/ProgramTreeView";
import { SchoolProgramCreateDialog } from "@/components/shared/SchoolProgramCreateDialog";
import { LessonDialog } from "@/components/LessonDialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Content } from "@/types";
import { BookOpen, Loader2 } from "lucide-react";
import { toast } from "sonner";

interface School {
  id: string;
  name: string;
  organization_id: string;
}

interface Organization {
  id: string;
  name: string;
}

interface Program {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  total_hours?: number;
  lessons?: Lesson[];
}

interface Lesson {
  id?: number;
  name: string;
  description?: string;
  order_index?: number;
  estimated_minutes?: number;
  program_id?: number;
  contents?: Content[];
}

/**
 * SchoolMaterialsPage - Manage school-level materials
 */
export default function SchoolMaterialsPage() {
  const { schoolId } = useParams<{ schoolId: string }>();
  const token = useTeacherAuthStore((state) => state.token);
  const user = useTeacherAuthStore((state) => state.user);

  const [school, setSchool] = useState<School | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create/Edit dialog state
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingProgram, setEditingProgram] = useState<Program | null>(null);
  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [saving, setSaving] = useState(false);

  // Delete confirmation
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Lesson dialog state
  const [lessonDialogType, setLessonDialogType] = useState<
    "create" | "edit" | "delete" | null
  >(null);
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null);
  const [lessonProgramId, setLessonProgramId] = useState<number | undefined>();

  useEffect(() => {
    if (schoolId) {
      fetchData();
    }
  }, [schoolId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch school info
      const schoolRes = await fetch(`${API_URL}/api/schools/${schoolId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!schoolRes.ok) {
        setError("載入學校資訊失敗");
        return;
      }

      const schoolData = await schoolRes.json();
      setSchool(schoolData);

      // Fetch organization info
      const orgRes = await fetch(
        `${API_URL}/api/organizations/${schoolData.organization_id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (orgRes.ok) {
        const orgData = await orgRes.json();
        setOrganization(orgData);
      }

      // Fetch school programs
      const programsRes = await fetch(
        `${API_URL}/api/schools/${schoolId}/programs`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (programsRes.ok) {
        const programsData = await programsRes.json();
        setPrograms(programsData);
      } else {
        setPrograms([]);
      }
    } catch (err) {
      console.error("Failed to fetch data:", err);
      setError("網路連線錯誤");
      toast.error("載入失敗");
    } finally {
      setLoading(false);
    }
  };

  // Check if current user can manage materials
  const canManageMaterials =
    user?.role === "org_owner" ||
    user?.role === "org_admin" ||
    user?.role === "school_admin" ||
    user?.role === "school_director";

  // Create program
  const handleCreate = () => {
    setShowCreateDialog(true);
  };

  // Edit program
  const handleEdit = (program: Program) => {
    setEditingProgram(program);
    setFormName(program.name);
    setFormDescription(program.description || "");
    setShowEditDialog(true);
  };

  const handleEditSubmit = async () => {
    if (!editingProgram || !formName.trim()) {
      toast.error("請填寫教材名稱");
      return;
    }

    setSaving(true);
    try {
      const response = await fetch(
        `${API_URL}/api/schools/${schoolId}/programs/${editingProgram.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name: formName.trim(),
            description: formDescription.trim() || undefined,
          }),
        }
      );

      if (response.ok) {
        const updatedProgram = await response.json();
        setPrograms((prev) =>
          prev.map((p) =>
            p.id === editingProgram.id
              ? { ...updatedProgram, lessons: p.lessons }
              : p
          )
        );
        setShowEditDialog(false);
        setEditingProgram(null);
        toast.success("教材更新成功");
      } else {
        const err = await response.json();
        toast.error(err.detail || "更新失敗");
      }
    } catch (err) {
      console.error("Failed to update program:", err);
      toast.error("網路錯誤");
    } finally {
      setSaving(false);
    }
  };

  // Delete program
  const handleDelete = async (programId: number) => {
    if (!deleteConfirmId) {
      setDeleteConfirmId(programId);
      return;
    }

    setDeleting(true);
    try {
      const response = await fetch(
        `${API_URL}/api/schools/${schoolId}/programs/${programId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        setPrograms((prev) => prev.filter((p) => p.id !== programId));
        setDeleteConfirmId(null);
        toast.success("教材刪除成功");
      } else {
        const err = await response.json();
        toast.error(err.detail || "刪除失敗");
      }
    } catch (err) {
      console.error("Failed to delete program:", err);
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

  const handleSaveLesson = (lessonData: Lesson) => {
    if (lessonDialogType === "create" && lessonProgramId) {
      setPrograms((prev) =>
        prev.map((program) => {
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
      setPrograms((prev) =>
        prev.map((program) => ({
          ...program,
          lessons: program.lessons?.map((lesson) =>
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
      const response = await fetch(
        `${API_URL}/api/schools/${schoolId}/programs/lessons/${lessonId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        setPrograms((prev) =>
          prev.map((program) => ({
            ...program,
            lessons: program.lessons?.filter((lesson) => lesson.id !== lessonId),
          }))
        );
        toast.success("課程單元刪除成功");
      } else {
        toast.error("刪除失敗");
      }
    } catch (err) {
      console.error("Failed to delete lesson:", err);
      toast.error("網路錯誤");
    }

    setLessonDialogType(null);
    setSelectedLesson(null);
  };

  const handleDeleteContent = async (contentId: number) => {
    try {
      const response = await fetch(
        `${API_URL}/api/schools/${schoolId}/programs/contents/${contentId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        setPrograms((prev) =>
          prev.map((program) => ({
            ...program,
            lessons: program.lessons?.map((lesson) => ({
              ...lesson,
              contents: lesson.contents?.filter((c) => c.id !== contentId),
            })),
          }))
        );
        toast.success("內容刪除成功");
      } else {
        toast.error("刪除失敗");
      }
    } catch (err) {
      console.error("Failed to delete content:", err);
      toast.error("網路錯誤");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !school) {
    return (
      <div className="space-y-6">
        <ErrorMessage message={error || "找不到學校"} onRetry={fetchData} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: "組織管理" },
          ...(organization
            ? [
                {
                  label: organization.name,
                  href: `/organization/${organization.id}`,
                },
              ]
            : []),
          {
            label: school.name,
            href: `/organization/schools/${school.id}`,
          },
          { label: "學校教材" },
        ]}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">學校教材</h1>
          <p className="text-gray-600 mt-2">
            {school.name} 的教學教材與課程
          </p>
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

      {/* Programs List */}
      <Card>
        <CardHeader>
          <CardTitle>教材列表</CardTitle>
        </CardHeader>
        <CardContent>
          {programs.length === 0 && !canManageMaterials ? (
            <div className="text-center py-12">
              <BookOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500 mb-2">此學校尚無教材</p>
            </div>
          ) : (
            <div className="mt-4">
              <ProgramTreeView
                programs={programs}
                onProgramsChange={setPrograms}
                onRefresh={fetchData}
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
                    const lessonItem = item as Lesson;
                    if (!lessonItem.id) return;
                    const program = programs.find((p) =>
                      p.lessons?.some((l) => l.id === lessonItem.id)
                    );
                    if (program) {
                      handleEditLesson(program.id, lessonItem.id);
                    }
                  }
                }}
                onDelete={(item, level) => {
                  if (level === 0 && canManageMaterials) {
                    const itemId = (item as { id?: number }).id;
                    if (itemId) handleDelete(itemId);
                  } else if (level === 1 && canManageMaterials) {
                    const lessonItem = item as Lesson;
                    if (!lessonItem.id) return;
                    const program = programs.find((p) =>
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
                    const contentItem = item as { id?: number };
                    if (contentItem.id) {
                      handleDeleteContent(contentItem.id);
                    }
                  }
                }}
              />
            </div>
          )}
        </CardContent>
      </Card>

      <SchoolProgramCreateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        schoolId={schoolId || ""}
        schoolName={school?.name || ""}
        organizationId={organization?.id}
        onSuccess={fetchData}
      />

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>編輯教材</DialogTitle>
            <DialogDescription>修改教材資訊</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">
                教材名稱 <span className="text-red-500">*</span>
              </Label>
              <Input
                id="edit-name"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="輸入教材名稱"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">描述</Label>
              <Textarea
                id="edit-description"
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                placeholder="輸入教材描述（選填）"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowEditDialog(false);
                setEditingProgram(null);
              }}
              disabled={saving}
            >
              取消
            </Button>
            <Button onClick={handleEditSubmit} disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  儲存中...
                </>
              ) : (
                "儲存"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
        apiBasePath={`${API_URL}/api/schools/${schoolId}`}
        authToken={token || undefined}
      />
    </div>
  );
}
