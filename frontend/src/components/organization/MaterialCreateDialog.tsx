import { useState } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

interface MaterialCreateDialogProps {
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

export function MaterialCreateDialog({
  organizationId,
  open,
  onOpenChange,
  onSuccess,
}: MaterialCreateDialogProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    level: "",
    total_hours: "",
  });

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      level: "",
      total_hours: "",
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error("請填寫教材名稱");
      return;
    }

    setLoading(true);
    try {
      const requestData: {
        name: string;
        description?: string;
        level?: string;
        total_hours?: number;
      } = {
        name: formData.name.trim(),
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
        `${API_URL}/api/organizations/${organizationId}/programs`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(requestData),
        },
      );

      if (response.ok) {
        toast.success("教材建立成功");
        resetForm();
        onSuccess();
        onOpenChange(false);
      } else {
        const data = await response.json();
        toast.error(data.detail || "建立失敗");
      }
    } catch (error) {
      console.error("Failed to create program:", error);
      toast.error("網路連線錯誤");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        onOpenChange(isOpen);
        if (!isOpen) {
          resetForm();
        }
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>新增教材</DialogTitle>
          <DialogDescription>建立新的組織教材與課程</DialogDescription>
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
              placeholder="例如：初級英語會話"
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

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                onOpenChange(false);
                resetForm();
              }}
              disabled={loading}
            >
              取消
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  建立中...
                </>
              ) : (
                "建立"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
