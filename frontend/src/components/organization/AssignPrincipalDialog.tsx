import { useState, useEffect } from "react";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

interface Teacher {
  id: number;
  email: string;
  name: string;
  is_active: boolean;
}

interface AssignPrincipalDialogProps {
  schoolId: string;
  organizationId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function AssignPrincipalDialog({
  schoolId,
  organizationId,
  open,
  onOpenChange,
  onSuccess,
}: AssignPrincipalDialogProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const [loading, setLoading] = useState(false);
  const [loadingTeachers, setLoadingTeachers] = useState(false);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [selectedTeacherId, setSelectedTeacherId] = useState<string>("");

  useEffect(() => {
    if (open) {
      fetchTeachers();
    }
  }, [open]);

  const fetchTeachers = async () => {
    try {
      setLoadingTeachers(true);

      // Fetch organization teachers
      const response = await fetch(
        `${API_URL}/api/organizations/${organizationId}/teachers`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setTeachers(data.filter((t: Teacher) => t.is_active));
      } else {
        toast.error("載入教師列表失敗");
      }
    } catch (error) {
      console.error("Failed to fetch teachers:", error);
      toast.error("網路連線錯誤");
    } finally {
      setLoadingTeachers(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeacherId) {
      toast.error("請選擇教師");
      return;
    }

    setLoading(true);

    try {
      // Step 1: Get current school teachers to find existing principal
      const teachersResponse = await fetch(
        `${API_URL}/api/schools/${schoolId}/teachers`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      let existingPrincipal = null;
      let selectedTeacherInSchool = null;

      if (teachersResponse.ok) {
        const schoolTeachers = await teachersResponse.json();
        existingPrincipal = schoolTeachers.find(
          (t: { id: number; roles?: string[] }) =>
            t.roles?.includes("school_admin"),
        );
        selectedTeacherInSchool = schoolTeachers.find(
          (t: { id: number }) => t.id === parseInt(selectedTeacherId),
        );
      }

      // Step 2: Remove school_admin from existing principal (if different from selected)
      if (
        existingPrincipal &&
        existingPrincipal.id !== parseInt(selectedTeacherId)
      ) {
        // Remove school_admin role from old principal
        const oldRoles = existingPrincipal.roles || [];
        const newRoles = oldRoles.filter((r: string) => r !== "school_admin");

        if (newRoles.length > 0) {
          // Keep teacher role if they have it
          await fetch(
            `${API_URL}/api/schools/${schoolId}/teachers/${existingPrincipal.id}`,
            {
              method: "PATCH",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({ roles: newRoles }),
            },
          );
        } else {
          // No other roles, remove from school entirely
          await fetch(
            `${API_URL}/api/schools/${schoolId}/teachers/${existingPrincipal.id}`,
            {
              method: "DELETE",
              headers: { Authorization: `Bearer ${token}` },
            },
          );
        }
      }

      // Step 3: Add or update selected teacher with school_admin role
      let response;

      if (selectedTeacherInSchool) {
        // Teacher already in school - update roles
        const currentRoles = selectedTeacherInSchool.roles || [];
        const newRoles = Array.from(new Set([...currentRoles, "school_admin"]));

        response = await fetch(
          `${API_URL}/api/schools/${schoolId}/teachers/${selectedTeacherId}`,
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ roles: newRoles }),
          },
        );
      } else {
        // Teacher not in school - add them
        response = await fetch(`${API_URL}/api/schools/${schoolId}/teachers`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            teacher_id: parseInt(selectedTeacherId),
            roles: ["school_admin"],
          }),
        });
      }

      if (response.ok) {
        toast.success("校長指派成功");
        onSuccess();
        onOpenChange(false);
        setSelectedTeacherId("");
      } else {
        const data = await response.json();
        toast.error(data.detail || "指派失敗");
      }
    } catch (error) {
      console.error("Failed to assign principal:", error);
      toast.error("網路連線錯誤");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>指派校長</DialogTitle>
          <DialogDescription>
            從組織的教師中選擇一位擔任校長（school_admin）
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="teacher">選擇校長</Label>
            {loadingTeachers ? (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                載入教師列表...
              </div>
            ) : (
              <Select
                value={selectedTeacherId}
                onValueChange={setSelectedTeacherId}
              >
                <SelectTrigger id="teacher">
                  <SelectValue placeholder="請選擇校長" />
                </SelectTrigger>
                <SelectContent>
                  {teachers.map((teacher) => (
                    <SelectItem key={teacher.id} value={teacher.id.toString()}>
                      {teacher.name} ({teacher.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {!loadingTeachers && teachers.length === 0 && (
              <p className="text-sm text-gray-500">
                此組織尚無教師，請先邀請教師加入組織
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              取消
            </Button>
            <Button type="submit" disabled={loading || !selectedTeacherId}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  指派中...
                </>
              ) : (
                "指派校長"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
