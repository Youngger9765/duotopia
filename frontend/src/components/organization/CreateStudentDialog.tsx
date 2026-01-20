import { useState } from "react";
import { apiClient } from "@/lib/api";
import { logError } from "@/utils/errorLogger";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";

interface CreateStudentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  schoolId: string;
  onSuccess: () => void;
}

export function CreateStudentDialog({
  open,
  onOpenChange,
  schoolId,
  onSuccess,
}: CreateStudentDialogProps) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    student_number: "",
    birthdate: "",
    phone: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleClose = () => {
    setFormData({
      name: "",
      email: "",
      student_number: "",
      birthdate: "",
      phone: "",
    });
    onOpenChange(false);
  };

  const handleSubmit = async () => {
    const trimmedName = formData.name.trim();
    if (!trimmedName) {
      toast.error("請輸入學生姓名");
      return;
    }

    if (trimmedName.length > 100) {
      toast.error("學生姓名不能超過 100 個字元");
      return;
    }

    if (!formData.birthdate) {
      toast.error("請選擇出生日期");
      return;
    }

    if (!schoolId) {
      toast.error("找不到學校 ID");
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await apiClient.createSchoolStudent(schoolId, {
        name: trimmedName,
        email: formData.email || undefined,
        student_number: formData.student_number || undefined,
        birthdate: formData.birthdate,
        phone: formData.phone || undefined,
      });

      toast.success("學生建立成功", {
        description: result.default_password
          ? `預設密碼：${result.default_password}`
          : undefined,
      });
      onSuccess();
      handleClose();
    } catch (error) {
      logError("Failed to create student", error, { schoolId, formData });
      toast.error("建立學生失敗，請稍後再試");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>建立學生</DialogTitle>
          <DialogDescription>在學校中建立新學生</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">
              姓名 <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              placeholder="請輸入學生姓名"
              disabled={isSubmitting}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="student_number">學號</Label>
            <Input
              id="student_number"
              value={formData.student_number}
              onChange={(e) =>
                setFormData({ ...formData, student_number: e.target.value })
              }
              placeholder="選填"
              disabled={isSubmitting}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
              placeholder="選填"
              disabled={isSubmitting}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="birthdate">
              出生日期 <span className="text-red-500">*</span>
            </Label>
            <Input
              id="birthdate"
              type="date"
              value={formData.birthdate}
              onChange={(e) =>
                setFormData({ ...formData, birthdate: e.target.value })
              }
              disabled={isSubmitting}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="phone">電話</Label>
            <Input
              id="phone"
              value={formData.phone}
              onChange={(e) =>
                setFormData({ ...formData, phone: e.target.value })
              }
              placeholder="選填"
              disabled={isSubmitting}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isSubmitting}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? "建立中..." : "建立"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

