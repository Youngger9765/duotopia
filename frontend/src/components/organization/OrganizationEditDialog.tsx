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
import { Loader2 } from "lucide-react";

interface Organization {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  is_active: boolean;
  owner_name?: string;
  owner_email?: string;
}

interface OrganizationEditDialogProps {
  organization: Organization | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function OrganizationEditDialog({
  organization,
  open,
  onOpenChange,
  onSuccess,
}: OrganizationEditDialogProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    display_name: "",
    description: "",
    contact_email: "",
    contact_phone: "",
    address: "",
    is_active: true,
  });

  // Reset form when organization changes
  useEffect(() => {
    if (organization) {
      setFormData({
        name: organization.name || "",
        display_name: organization.display_name || "",
        description: organization.description || "",
        contact_email: organization.contact_email || "",
        contact_phone: organization.contact_phone || "",
        address: organization.address || "",
        is_active: organization.is_active,
      });
      setError(null);
    }
  }, [organization]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!organization) return;

    setLoading(true);
    setError(null);

    try {
      // If display_name is empty, set it to null to ensure sidebar shows 'name'
      const submitData = {
        ...formData,
        display_name: formData.display_name || null,
      };

      const response = await fetch(
        `${API_URL}/api/organizations/${organization.id}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(submitData),
        },
      );

      if (response.ok) {
        onSuccess();
        onOpenChange(false);
      } else {
        const data = await response.json();
        setError(data.detail || "更新失敗");
      }
    } catch (error) {
      console.error("Failed to update organization:", error);
      setError("網路連線錯誤");
    } finally {
      setLoading(false);
    }
  };

  if (!organization) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>編輯機構</DialogTitle>
          <DialogDescription>修改機構的基本資訊和聯絡方式</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Owner Email (只讀) */}
          {organization?.owner_email && (
            <div className="space-y-2 p-3 bg-blue-50 rounded-lg">
              <Label className="text-sm font-medium text-blue-900">
                機構 Owner
              </Label>
              <div className="text-sm">
                <div className="text-blue-800 font-medium">
                  {organization.owner_name || "未命名"}
                </div>
                <div className="text-blue-600 mt-1">
                  {organization.owner_email}
                </div>
              </div>
            </div>
          )}

          {/* 機構名稱 */}
          <div className="space-y-2">
            <Label htmlFor="name">
              機構名稱 <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              required
              placeholder="輸入機構名稱"
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
              placeholder="輸入機構描述（選填）"
              rows={3}
            />
          </div>

          {/* 聯絡信箱 */}
          <div className="space-y-2">
            <Label htmlFor="contact_email">聯絡信箱</Label>
            <Input
              id="contact_email"
              type="email"
              value={formData.contact_email}
              onChange={(e) =>
                setFormData({ ...formData, contact_email: e.target.value })
              }
              placeholder="example@email.com"
            />
          </div>

          {/* 聯絡電話 */}
          <div className="space-y-2">
            <Label htmlFor="contact_phone">聯絡電話</Label>
            <Input
              id="contact_phone"
              type="tel"
              value={formData.contact_phone}
              onChange={(e) =>
                setFormData({ ...formData, contact_phone: e.target.value })
              }
              placeholder="02-1234-5678"
            />
          </div>

          {/* 地址 */}
          <div className="space-y-2">
            <Label htmlFor="address">地址</Label>
            <Textarea
              id="address"
              value={formData.address}
              onChange={(e) =>
                setFormData({ ...formData, address: e.target.value })
              }
              placeholder="輸入機構地址（選填）"
              rows={2}
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

          {/* Error Message */}
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 rounded-lg">
              {error}
            </div>
          )}

          {/* Footer */}
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
