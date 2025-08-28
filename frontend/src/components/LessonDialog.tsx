import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { AlertTriangle } from 'lucide-react';

interface Lesson {
  id?: number;
  name: string;
  description?: string;
  order_index?: number;
  estimated_minutes?: number;
  program_id?: number;
}

interface LessonDialogProps {
  lesson: Lesson | null;
  dialogType: 'create' | 'edit' | 'delete' | null;
  programId?: number;
  onClose: () => void;
  onSave: (lesson: Lesson) => void;
  onDelete?: (lessonId: number) => void;
}

export function LessonDialog({
  lesson,
  dialogType,
  programId,
  onClose,
  onSave,
  onDelete
}: LessonDialogProps) {
  const [formData, setFormData] = useState<Lesson>({
    name: '',
    description: '',
    order_index: 1,
    estimated_minutes: 30,
    program_id: programId
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (lesson && (dialogType === 'edit' || dialogType === 'delete')) {
      setFormData({
        name: lesson.name,
        description: lesson.description || '',
        order_index: lesson.order_index || 1,
        estimated_minutes: lesson.estimated_minutes || 30,
        program_id: lesson.program_id || programId
      });
    } else if (dialogType === 'create') {
      setFormData({
        name: '',
        description: '',
        order_index: 1,
        estimated_minutes: 30,
        program_id: programId
      });
    }
  }, [lesson, dialogType, programId]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.name?.trim()) {
      newErrors.name = '單元名稱為必填';
    }
    
    if (!formData.estimated_minutes || formData.estimated_minutes < 1) {
      newErrors.estimated_minutes = '預估時間必須大於 0';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      if (dialogType === 'create') {
        // TODO: 實作 API 呼叫
        console.log('Creating lesson:', formData);
        onSave({ ...formData, id: Date.now() }); // Mock ID
      } else if (dialogType === 'edit' && lesson) {
        // TODO: 實作 API 呼叫
        console.log('Updating lesson:', lesson.id, formData);
        onSave({ ...lesson, ...formData });
      }
      onClose();
    } catch (error) {
      console.error('Failed to save lesson:', error);
      setErrors({ submit: '儲存失敗，請稍後再試' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!lesson?.id || !onDelete) return;
    
    setLoading(true);
    try {
      // TODO: 實作 API 呼叫
      console.log('Deleting lesson:', lesson.id);
      onDelete(lesson.id);
      onClose();
    } catch (error) {
      console.error('Failed to delete lesson:', error);
      alert('刪除失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  if (!dialogType) return null;

  // Create/Edit Dialog
  if (dialogType === 'create' || dialogType === 'edit') {
    return (
      <Dialog open={true} onOpenChange={() => onClose()}>
        <DialogContent className="bg-white" style={{ backgroundColor: 'white' }}>
          <DialogHeader>
            <DialogTitle>
              {dialogType === 'create' ? '新增單元' : '編輯單元'}
            </DialogTitle>
            <DialogDescription>
              {dialogType === 'create' 
                ? '為課程新增學習單元' 
                : '修改單元資訊'}
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div>
              <label htmlFor="name" className="text-sm font-medium">
                單元名稱 <span className="text-red-500">*</span>
              </label>
              <input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className={`w-full mt-1 px-3 py-2 border rounded-md ${errors.name ? 'border-red-500' : ''}`}
                placeholder="例：Unit 1: Greetings 打招呼"
              />
              {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name}</p>}
            </div>
            
            <div>
              <label htmlFor="description" className="text-sm font-medium">
                單元描述
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="學習目標與內容簡述..."
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="order" className="text-sm font-medium">
                  順序
                </label>
                <input
                  id="order"
                  type="number"
                  value={formData.order_index}
                  onChange={(e) => setFormData({ ...formData, order_index: parseInt(e.target.value) || 1 })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                  placeholder="1"
                  min="1"
                />
              </div>
              
              <div>
                <label htmlFor="minutes" className="text-sm font-medium">
                  預估時間（分鐘）<span className="text-red-500">*</span>
                </label>
                <input
                  id="minutes"
                  type="number"
                  value={formData.estimated_minutes}
                  onChange={(e) => setFormData({ ...formData, estimated_minutes: parseInt(e.target.value) || 0 })}
                  className={`w-full mt-1 px-3 py-2 border rounded-md ${errors.estimated_minutes ? 'border-red-500' : ''}`}
                  placeholder="30"
                  min="1"
                />
                {errors.estimated_minutes && <p className="text-xs text-red-500 mt-1">{errors.estimated_minutes}</p>}
              </div>
            </div>

            {errors.submit && (
              <p className="text-sm text-red-500 bg-red-50 p-2 rounded">{errors.submit}</p>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={onClose} disabled={loading}>
              取消
            </Button>
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? '處理中...' : dialogType === 'create' ? '新增' : '儲存'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  // Delete Confirmation Dialog
  if (dialogType === 'delete' && lesson) {
    return (
      <Dialog open={true} onOpenChange={() => onClose()}>
        <DialogContent className="bg-white" style={{ backgroundColor: 'white' }}>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <span>確認刪除單元</span>
            </DialogTitle>
            <DialogDescription>
              確定要刪除單元「{lesson.name}」嗎？此操作無法復原。
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">單元資料：</p>
              <p className="font-medium mt-1">{lesson.name}</p>
              {lesson.description && (
                <p className="text-sm text-gray-500 mt-1">{lesson.description}</p>
              )}
              {lesson.estimated_minutes && (
                <p className="text-sm text-gray-500 mt-1">預估時間：{lesson.estimated_minutes} 分鐘</p>
              )}
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={onClose} disabled={loading}>
              取消
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDelete} 
              disabled={loading}
            >
              {loading ? '刪除中...' : '確認刪除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return null;
}