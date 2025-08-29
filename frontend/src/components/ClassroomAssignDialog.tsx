import React from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { School } from 'lucide-react';

interface ClassroomAssignDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (classroomId: number) => void;
  classrooms: Array<{ id: number; name: string }>;
  studentCount: number;
}

export function ClassroomAssignDialog({
  open,
  onClose,
  onConfirm,
  classrooms,
  studentCount
}: ClassroomAssignDialogProps) {
  const [selectedClassroomId, setSelectedClassroomId] = React.useState<number | null>(null);

  const handleConfirm = () => {
    if (selectedClassroomId) {
      onConfirm(selectedClassroomId);
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-white max-w-md" style={{ backgroundColor: 'white' }}>
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <School className="h-5 w-5" />
            <span>分配班級</span>
          </DialogTitle>
          <DialogDescription>
            為選中的 {studentCount} 位學生分配班級
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <label htmlFor="classroom-select" className="text-sm font-medium mb-2 block">
            選擇班級
          </label>
          <select
            id="classroom-select"
            value={selectedClassroomId || ''}
            onChange={(e) => setSelectedClassroomId(e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border rounded-md"
          >
            <option value="">請選擇班級</option>
            {classrooms.map((classroom) => (
              <option key={classroom.id} value={classroom.id}>
                {classroom.name}
              </option>
            ))}
          </select>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button 
            onClick={handleConfirm}
            disabled={!selectedClassroomId}
          >
            確定分配
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}