import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { format } from 'date-fns';
import { zhTW } from 'date-fns/locale';
import { CalendarIcon, Users, User } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

interface Student {
  id: number;
  name: string;
  email: string;
}

interface Content {
  id: number;
  title: string;
  type: string;
  lesson_id: number;
}

interface AssignmentDialogProps {
  open: boolean;
  onClose: () => void;
  classroomId: number;
  students: Student[];
  onSuccess?: () => void;
}

export function AssignmentDialog({
  open,
  onClose,
  classroomId,
  students,
  onSuccess
}: AssignmentDialogProps) {
  const [loading, setLoading] = useState(false);
  const [contents, setContents] = useState<Content[]>([]);
  const [formData, setFormData] = useState({
    title: '',
    instructions: '',
    content_id: '',
    student_ids: [] as number[],
    assign_to_all: false,
    due_date: undefined as Date | undefined,
  });

  useEffect(() => {
    if (open) {
      loadContents();
    }
  }, [open, classroomId]);

  const loadContents = async () => {
    try {
      const response = await apiClient.get(`/api/contents?classroom_id=${classroomId}`);
      setContents(response.data);
    } catch (error) {
      console.error('Failed to load contents:', error);
      toast.error('無法載入課程內容');
    }
  };

  const handleSubmit = async () => {
    // Validation
    if (!formData.content_id) {
      toast.error('請選擇課程內容');
      return;
    }
    if (!formData.title.trim()) {
      toast.error('請輸入作業標題');
      return;
    }
    if (!formData.assign_to_all && formData.student_ids.length === 0) {
      toast.error('請選擇學生或勾選「指派給全班」');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        content_id: parseInt(formData.content_id),
        classroom_id: classroomId,
        title: formData.title,
        instructions: formData.instructions || undefined,
        student_ids: formData.assign_to_all ? [] : formData.student_ids,
        due_date: formData.due_date ? formData.due_date.toISOString() : undefined,
      };

      const response = await apiClient.post('/api/assignments/create', payload);
      
      if (response.data.success) {
        toast.success(`成功創建 ${response.data.count} 份作業`);
        onSuccess?.();
        handleClose();
      }
    } catch (error: any) {
      console.error('Failed to create assignment:', error);
      toast.error(error.response?.data?.detail || '創建作業失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      title: '',
      instructions: '',
      content_id: '',
      student_ids: [],
      assign_to_all: false,
      due_date: undefined,
    });
    onClose();
  };

  const toggleStudent = (studentId: number) => {
    setFormData(prev => ({
      ...prev,
      student_ids: prev.student_ids.includes(studentId)
        ? prev.student_ids.filter(id => id !== studentId)
        : [...prev.student_ids, studentId]
    }));
  };

  const toggleAssignToAll = (checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      assign_to_all: checked,
      student_ids: checked ? [] : prev.student_ids
    }));
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>指派新作業</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Content Selection */}
          <div className="space-y-2">
            <Label htmlFor="content">選擇課程內容 *</Label>
            <Select
              value={formData.content_id}
              onValueChange={(value) => setFormData(prev => ({ ...prev, content_id: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="請選擇課程內容" />
              </SelectTrigger>
              <SelectContent>
                {contents.map(content => (
                  <SelectItem key={content.id} value={content.id.toString()}>
                    {content.title}
                    <span className="ml-2 text-xs text-gray-500">
                      ({content.type === 'reading_assessment' ? '朗讀評測' : content.type})
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">作業標題 *</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              placeholder="例：Unit 1 朗讀練習"
            />
          </div>

          {/* Instructions */}
          <div className="space-y-2">
            <Label htmlFor="instructions">作業說明（選填）</Label>
            <Textarea
              id="instructions"
              value={formData.instructions}
              onChange={(e) => setFormData(prev => ({ ...prev, instructions: e.target.value }))}
              placeholder="請詳細說明作業要求..."
              rows={3}
            />
          </div>

          {/* Due Date */}
          <div className="space-y-2">
            <Label>截止日期（選填）</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !formData.due_date && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {formData.due_date ? (
                    format(formData.due_date, "PPP", { locale: zhTW })
                  ) : (
                    <span>選擇截止日期</span>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={formData.due_date}
                  onSelect={(date) => setFormData(prev => ({ ...prev, due_date: date }))}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>

          {/* Student Selection */}
          <div className="space-y-2">
            <Label>指派對象 *</Label>
            
            {/* Assign to All Checkbox */}
            <div className="flex items-center space-x-2 p-3 bg-blue-50 rounded-lg">
              <Checkbox
                id="assign-to-all"
                checked={formData.assign_to_all}
                onCheckedChange={toggleAssignToAll}
              />
              <label
                htmlFor="assign-to-all"
                className="flex items-center cursor-pointer flex-1"
              >
                <Users className="h-4 w-4 mr-2" />
                <span className="font-medium">指派給全班所有學生</span>
                <span className="ml-2 text-sm text-gray-600">
                  ({students.length} 位學生)
                </span>
              </label>
            </div>

            {/* Individual Student Selection */}
            {!formData.assign_to_all && (
              <div className="border rounded-lg max-h-48 overflow-y-auto">
                {students.map(student => (
                  <div
                    key={student.id}
                    className="flex items-center space-x-2 p-3 hover:bg-gray-50 border-b last:border-b-0"
                  >
                    <Checkbox
                      id={`student-${student.id}`}
                      checked={formData.student_ids.includes(student.id)}
                      onCheckedChange={() => toggleStudent(student.id)}
                    />
                    <label
                      htmlFor={`student-${student.id}`}
                      className="flex items-center cursor-pointer flex-1"
                    >
                      <User className="h-4 w-4 mr-2" />
                      <span>{student.name}</span>
                      <span className="ml-2 text-sm text-gray-500">{student.email}</span>
                    </label>
                  </div>
                ))}
              </div>
            )}

            {!formData.assign_to_all && formData.student_ids.length > 0 && (
              <p className="text-sm text-gray-600">
                已選擇 {formData.student_ids.length} 位學生
              </p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? '創建中...' : '創建作業'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}