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

interface TeacherInfo {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface TeacherRoleEditDialogProps {
  teacher: TeacherInfo | null;
  organizationId: string;
  currentUserRole: string;
  currentUserId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function TeacherRoleEditDialog({
  teacher,
  organizationId,
  currentUserRole,
  currentUserId,
  open,
  onOpenChange,
  onSuccess,
}: TeacherRoleEditDialogProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const [loading, setLoading] = useState(false);
  const [selectedRole, setSelectedRole] = useState<string>("");

  // Reset form when teacher changes
  useEffect(() => {
    if (teacher) {
      setSelectedRole(teacher.role);
    }
  }, [teacher]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teacher || !selectedRole) return;

    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/organizations/${organizationId}/teachers/${teacher.id}/role`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ role: selectedRole }),
        },
      );

      if (response.ok) {
        toast.success("角色更新成功");
        onSuccess();
        onOpenChange(false);
      } else {
        const data = await response.json();
        toast.error(data.detail || "角色更新失敗");
      }
    } catch (error) {
      console.error("Failed to update teacher role:", error);
      toast.error("網路連線錯誤");
    } finally {
      setLoading(false);
    }
  };

  if (!teacher) return null;

  // Can't edit own role
  const isSelf = teacher.id === currentUserId;

  // org_admin can't select org_owner option
  const canSelectOwner = currentUserRole === "org_owner";

  // Available role options
  const roleOptions = [
    { value: "teacher", label: "教師" },
    { value: "org_admin", label: "組織管理員" },
    ...(canSelectOwner ? [{ value: "org_owner", label: "組織擁有者" }] : []),
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>編輯角色</DialogTitle>
          <DialogDescription>
            更改 {teacher.name} ({teacher.email}) 在組織中的角色
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isSelf ? (
            <div className="p-3 text-sm text-amber-600 bg-amber-50 rounded-lg">
              您無法編輯自己的角色
            </div>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="role">
                組織角色 <span className="text-red-500">*</span>
              </Label>
              <Select value={selectedRole} onValueChange={setSelectedRole}>
                <SelectTrigger id="role">
                  <SelectValue placeholder="選擇角色" />
                </SelectTrigger>
                <SelectContent>
                  {roleOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!canSelectOwner && (
                <p className="text-xs text-gray-500">
                  注意：組織管理員無法指派組織擁有者角色
                </p>
              )}
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              取消
            </Button>
            <Button type="submit" disabled={loading || isSelf}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  更新中...
                </>
              ) : (
                "儲存"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
