import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { logError } from "@/utils/errorLogger";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

interface Classroom {
  id: string;
  name: string;
  teacher_name: string | null;
  teacher_id?: number | null;
}

interface Teacher {
  id: number;
  name: string;
  email: string;
}

interface AssignTeacherDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  classroom: Classroom | null;
  teachers: Teacher[];
  onSuccess: () => void;
}

export function AssignTeacherDialog({
  open,
  onOpenChange,
  classroom,
  teachers,
  onSuccess,
}: AssignTeacherDialogProps) {
  const [selectedTeacherId, setSelectedTeacherId] = useState<number | null>(
    null
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (classroom) {
      setSelectedTeacherId(classroom.teacher_id || null);
    }
  }, [classroom]);

  const handleClose = () => {
    setSelectedTeacherId(null);
    onOpenChange(false);
  };

  const handleSubmit = async () => {
    if (!classroom) return;

    setIsSubmitting(true);
    try {
      await apiClient.assignTeacherToClassroom(
        parseInt(classroom.id),
        selectedTeacherId
      );

      toast.success(
        selectedTeacherId
          ? "導師指派成功"
          : "已取消導師指派"
      );
      onSuccess();
      handleClose();
    } catch (error) {
      logError("Failed to assign teacher", error, {
        classroomId: classroom.id,
        teacherId: selectedTeacherId,
      });
      toast.error("指派導師失敗，請稍後再試");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!classroom) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {classroom.teacher_name ? "更換導師" : "指派導師"}
          </DialogTitle>
          <DialogDescription>
            {classroom.teacher_name
              ? `為 ${classroom.name} 指派新的導師`
              : `為 ${classroom.name} 指派導師`}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="teacher-select">選擇導師</Label>
            <Select
              value={selectedTeacherId?.toString() || "none"}
              onValueChange={(value) =>
                setSelectedTeacherId(value === "none" ? null : parseInt(value))
              }
              disabled={isSubmitting}
            >
              <SelectTrigger id="teacher-select">
                <SelectValue placeholder="選擇導師（可選）" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">未指派</SelectItem>
                {teachers.map((teacher) => (
                  <SelectItem key={teacher.id} value={teacher.id.toString()}>
                    {teacher.name} ({teacher.email})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? "處理中..." : "確認"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

