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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Loader2, User, Mail, Shield, Info } from "lucide-react";
import { toast } from "sonner";

interface InviteTeacherDialogProps {
  organizationId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function InviteTeacherDialog({
  organizationId,
  open,
  onOpenChange,
  onSuccess,
}: InviteTeacherDialogProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    name: "",
    role: "teacher",
  });

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case "org_owner":
        return "bg-purple-100 text-purple-800";
      case "org_admin":
        return "bg-blue-100 text-blue-800";
      case "school_admin":
        return "bg-green-100 text-green-800";
      case "teacher":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case "org_owner":
        return "組織擁有者";
      case "org_admin":
        return "組織管理員";
      case "school_admin":
        return "學校管理員";
      case "teacher":
        return "教師";
      default:
        return role;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.email || !formData.name) {
      toast.error("請填寫所有必填欄位");
      return;
    }

    setLoading(true);

    try {
      // Invite teacher to organization
      const response = await fetch(
        `${API_URL}/api/organizations/${organizationId}/teachers/invite`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(formData),
        },
      );

      if (response.ok) {
        toast.success("工作人員邀請成功");
        onSuccess();
        onOpenChange(false);
        setFormData({ email: "", name: "", role: "teacher" });
      } else {
        const data = await response.json();
        toast.error(data.detail || "邀請失敗");
      }
    } catch (error) {
      console.error("Failed to invite teacher:", error);
      toast.error("網路連線錯誤");
    } finally {
      setLoading(false);
    }
  };

  return (
    <TooltipProvider>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>邀請教師加入組織</DialogTitle>
            <DialogDescription>
              非Duotopia會員教師須收發【Email認證】並【設定密碼】
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 基本資料區塊 */}
            <div className="space-y-4">
              <div className="text-sm font-medium text-gray-700 flex items-center gap-2 pb-2 border-b">
                <User className="h-4 w-4" />
                基本資料
              </div>

              <div className="grid grid-cols-[100px_1fr] gap-x-4 gap-y-4 items-center">
                <Label htmlFor="name" className="text-right">
                  姓名 <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  required
                  placeholder="請輸入教師姓名"
                />

                <Label htmlFor="email" className="text-right">
                  Email <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  required
                  placeholder="example@email.com"
                />
              </div>
            </div>

            {/* 權限設定區塊 */}
            <div className="space-y-4">
              <div className="text-sm font-medium text-gray-700 flex items-center gap-2 pb-2 border-b">
                <Shield className="h-4 w-4" />
                權限設定
              </div>

              <div className="grid grid-cols-[100px_1fr] gap-x-4 gap-y-4 items-center">
                <Label
                  htmlFor="role"
                  className="text-right flex items-center justify-end gap-2"
                >
                  角色
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                      >
                        <Info className="h-4 w-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent
                      side="right"
                      className="max-w-xs bg-gray-900 text-white border-gray-900"
                    >
                      <div className="space-y-2 text-left">
                        <p className="font-medium text-sm">角色權限說明：</p>
                        <p className="text-xs">
                          <strong>組織管理員：</strong>
                          可編輯組織教材、管理班級與學生、派發/批改作業
                        </p>
                        <p className="text-xs">
                          <strong>學校管理員：</strong>
                          可管理班級與學生、派發/批改作業
                        </p>
                        <p className="text-xs">
                          <strong>教師：</strong>僅可派發/批改作業
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </Label>
                <Select
                  value={formData.role}
                  onValueChange={(value) =>
                    setFormData({ ...formData, role: value })
                  }
                >
                  <SelectTrigger id="role">
                    <SelectValue>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(
                          formData.role,
                        )}`}
                      >
                        {getRoleLabel(formData.role)}
                      </span>
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="teacher">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        教師
                      </span>
                    </SelectItem>
                    <SelectItem value="school_admin">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        學校管理員
                      </span>
                    </SelectItem>
                    <SelectItem value="org_admin">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        組織管理員
                      </span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter className="gap-2">
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
                    邀請中...
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                    發送邀請
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
}
