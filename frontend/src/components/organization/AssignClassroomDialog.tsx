import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
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
import { API_URL } from "@/config/api";

interface Student {
  id: number;
  name: string;
  classrooms?: Array<{ id: number; name: string }>;
}

interface Classroom {
  id: number;
  name: string;
}

interface AssignClassroomDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  student: Student | null;
  schoolId: string;
  onSuccess: () => void | Promise<void>;
}

export function AssignClassroomDialog({
  open,
  onOpenChange,
  student,
  schoolId,
  onSuccess,
}: AssignClassroomDialogProps) {
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [selectedClassroomId, setSelectedClassroomId] = useState<number | null>(
    null,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && schoolId) {
      fetchClassrooms();
      // 重置選擇
      setSelectedClassroomId(null);
    }
  }, [open, schoolId, student?.id]);

  const token = useTeacherAuthStore((state) => state.token);

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${API_URL}/api/schools/${schoolId}/classrooms`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setClassrooms(data);
      } else {
        logError("Failed to fetch classrooms", new Error(response.statusText), {
          schoolId,
        });
        toast.error("載入班級列表失敗");
      }
    } catch (error) {
      logError("Failed to fetch classrooms", error, { schoolId });
      toast.error("載入班級列表失敗");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSelectedClassroomId(null);
    onOpenChange(false);
  };

  const handleSubmit = async () => {
    if (!student || !selectedClassroomId) return;

    setIsSubmitting(true);
    try {
      await apiClient.addStudentToClassroom(
        schoolId,
        student.id,
        selectedClassroomId,
      );

      toast.success("學生已成功指派到班級");
      // 等待 onSuccess 完成（包含資料重新整理）後再關閉對話框
      await onSuccess();
      handleClose();
    } catch (error) {
      logError("Failed to assign student to classroom", error, {
        schoolId,
        studentId: student.id,
        classroomId: selectedClassroomId,
      });
      toast.error("指派班級失敗，請稍後再試");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!student) return null;

  // 過濾掉學生已經加入的班級（只顯示尚未被指派過的班級）
  // 確保 ID 類型一致（都轉換為數字進行比較）
  const studentClassroomIds = new Set(
    student.classrooms?.map((c) => Number(c.id)) || [],
  );
  const availableClassrooms = classrooms.filter(
    (classroom) => !studentClassroomIds.has(Number(classroom.id)),
  );

  // Debug: Log filtering results (only in development)
  if (process.env.NODE_ENV === "development") {
    console.log("[AssignClassroomDialog] Filtering:", {
      studentId: student.id,
      studentClassrooms: student.classrooms,
      studentClassroomIds: Array.from(studentClassroomIds),
      allClassrooms: classrooms.map((c) => ({ id: c.id, name: c.name })),
      availableClassrooms: availableClassrooms.map((c) => ({
        id: c.id,
        name: c.name,
      })),
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>指派班級</DialogTitle>
          <DialogDescription>
            為 {student.name} 指派班級（學生可以屬於多個班級）
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="classroom-select">選擇班級</Label>
            {loading ? (
              <div className="text-sm text-gray-500">載入中...</div>
            ) : (
              <Select
                value={selectedClassroomId?.toString() || ""}
                onValueChange={(value) =>
                  setSelectedClassroomId(value ? parseInt(value) : null)
                }
                disabled={isSubmitting}
              >
                <SelectTrigger id="classroom-select">
                  <SelectValue placeholder="選擇班級" />
                </SelectTrigger>
                <SelectContent>
                  {availableClassrooms.length === 0 ? (
                    <div className="px-2 py-1.5 text-sm text-gray-500 text-center">
                      沒有可用的班級
                    </div>
                  ) : (
                    availableClassrooms.map((classroom) => (
                      <SelectItem
                        key={classroom.id}
                        value={classroom.id.toString()}
                      >
                        {classroom.name}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            )}
            {availableClassrooms.length === 0 && !loading && (
              <p className="text-sm text-gray-500">此學生已加入所有班級</p>
            )}
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
          <Button
            onClick={handleSubmit}
            disabled={
              isSubmitting ||
              !selectedClassroomId ||
              loading ||
              availableClassrooms.length === 0
            }
          >
            {isSubmitting ? "處理中..." : "確認"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
