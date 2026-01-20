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
  onSuccess: () => void;
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
    null
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && schoolId) {
      fetchClassrooms();
    }
  }, [open, schoolId]);

  useEffect(() => {
    if (student && student.classrooms && student.classrooms.length > 0) {
      // 預設選擇第一個班級（如果有的話）
      setSelectedClassroomId(student.classrooms[0].id);
    } else {
      setSelectedClassroomId(null);
    }
  }, [student]);

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
        }
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
        selectedClassroomId
      );

      toast.success("學生已成功指派到班級");
      onSuccess();
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

  // 檢查學生是否已在這個班級
  const isAlreadyInClassroom = student.classrooms?.some(
    (c) => c.id === selectedClassroomId
  );

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
                  {classrooms.map((classroom) => (
                    <SelectItem
                      key={classroom.id}
                      value={classroom.id.toString()}
                    >
                      {classroom.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {isAlreadyInClassroom && (
              <p className="text-sm text-yellow-600">
                此學生已經在此班級中
              </p>
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
            disabled={isSubmitting || !selectedClassroomId || loading}
          >
            {isSubmitting ? "處理中..." : "確認"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

