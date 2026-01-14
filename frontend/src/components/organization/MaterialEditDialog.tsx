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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
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

interface MaterialEditDialogProps {
  program: ProgramData | null;
  organizationId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

const CEFR_LEVELS = [
  { value: "PreA", label: "Pre-A" },
  { value: "A1", label: "A1" },
  { value: "A2", label: "A2" },
  { value: "B1", label: "B1" },
  { value: "B2", label: "B2" },
  { value: "C1", label: "C1" },
  { value: "C2", label: "C2" },
];

export function MaterialEditDialog({
  program,
  organizationId,
  open,
  onOpenChange,
  onSuccess,
}: MaterialEditDialogProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    level: "",
    total_hours: "",
    is_active: true,
  });

  // Reset form when program changes
  useEffect(() => {
    if (program) {
      setFormData({
        name: program.name || "",
        description: program.description || "",
        level: program.level || "",
        total_hours: program.total_hours?.toString() || "",
        is_active: program.is_active,
      });
    }
  }, [program]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!program) return;

    if (!formData.name.trim()) {
      toast.error("請填寫教材名稱");
      return;
    }

    setLoading(true);
    try {
      const requestData: {
        name: string;
        is_active: boolean;
        description?: string;
        level?: string;
        total_hours?: number;
      } = {
        name: formData.name.trim(),
        is_active: formData.is_active,
      };

      if (formData.description.trim()) {
        requestData.description = formData.description.trim();
      }

      if (formData.level) {
        requestData.level = formData.level;
      }

      if (formData.total_hours) {
        const hours = parseInt(formData.total_hours);
        if (hours > 0) {
          requestData.total_hours = hours;
        }
      }

      const response = await fetch(
        `${API_URL}/api/organizations/${organizationId}/programs/${program.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(requestData),
        },
      );

      if (response.ok) {
        toast.success("教材更新成功");
        onSuccess();
        onOpenChange(false);
      } else {
        const data = await response.json();
        toast.error(data.detail || "更新失敗");
      }
    } catch (error) {
      console.error("Failed to update program:", error);
      toast.error("網路連線錯誤");
    } finally {
      setLoading(false);
    }
  };

  if (!program) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>編輯教材</DialogTitle>
          <DialogDescription>修改教材的基本資訊</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 教材名稱 */}
          <div className="space-y-2">
            <Label htmlFor="name">
              教材名稱 <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              required
              placeholder="輸入教材名稱"
            />
          </div>

          {/* 描述 */}
          <div className="space-y-2">
            <Label htmlFor="description">描述</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="輸入教材描述（選填）"
              rows={3}
            />
          </div>

          {/* CEFR 等級 */}
          <div className="space-y-2">
            <Label htmlFor="level">CEFR 等級</Label>
            <Select
              value={formData.level}
              onValueChange={(value) =>
                setFormData({ ...formData, level: value })
              }
            >
              <SelectTrigger id="level">
                <SelectValue placeholder="選擇等級（選填）" />
              </SelectTrigger>
              <SelectContent>
                {CEFR_LEVELS.map((level) => (
                  <SelectItem key={level.value} value={level.value}>
                    {level.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 總時數 */}
          <div className="space-y-2">
            <Label htmlFor="total_hours">總時數</Label>
            <Input
              id="total_hours"
              type="number"
              min="0"
              value={formData.total_hours}
              onChange={(e) =>
                setFormData({ ...formData, total_hours: e.target.value })
              }
              placeholder="例如：60（選填）"
            />
          </div>

          {/* 啟用狀態 */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="is_active"
              checked={formData.is_active}
              onCheckedChange={(checked: boolean) =>
                setFormData({ ...formData, is_active: checked })
              }
            />
            <Label htmlFor="is_active" className="cursor-pointer">
              {formData.is_active ? "啟用" : "停用"}
            </Label>
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
            <Button type="submit" disabled={loading}>
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
