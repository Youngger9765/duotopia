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
import { BookOpen, Clock, Layers, Search, Copy, CheckCircle } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';

export interface TeacherProgram {
  id: number;
  name: string;
  description?: string;
  level: string;
  estimated_hours?: number;
  lesson_count?: number;
  classroom_id?: number;
  already_in_classroom?: boolean;
}

interface CopyProgramDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  classroomId: number;
}

export default function CopyProgramDialog({
  open,
  onClose,
  onSuccess,
  classroomId
}: CopyProgramDialogProps) {
  const [programs, setPrograms] = useState<TeacherProgram[]>([]);
  const [loading, setLoading] = useState(true);
  const [copying, setCopying] = useState(false);
  const [selectedPrograms, setSelectedPrograms] = useState<number[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (open) {
      fetchPrograms();
      setSelectedPrograms([]);
      setSearchTerm('');
    }
  }, [open]);

  const fetchPrograms = async () => {
    try {
      setLoading(true);
      // Get copyable programs (templates + other classroom programs)
      const data = await apiClient.getCopyablePrograms(classroomId) as TeacherProgram[];
      // Filter out programs already in this classroom
      const availablePrograms = data.filter(p => p.classroom_id !== classroomId);
      setPrograms(availablePrograms);
    } catch (error) {
      console.error('Failed to fetch programs:', error);
      toast.error('載入課程失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleProgram = (programId: number) => {
    setSelectedPrograms(prev => {
      if (prev.includes(programId)) {
        return prev.filter(id => id !== programId);
      } else {
        return [...prev, programId];
      }
    });
  };

  const handleCopyPrograms = async () => {
    if (selectedPrograms.length === 0) return;

    setCopying(true);
    try {
      await apiClient.copyProgramToClassroom(classroomId, selectedPrograms);
      toast.success(`成功複製 ${selectedPrograms.length} 個課程到班級`);
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Failed to copy programs:', error);
      toast.error('複製失敗，請稍後再試');
    } finally {
      setCopying(false);
    }
  };

  const filteredPrograms = programs.filter(program =>
    program.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getLevelBadgeClass = (level: string) => {
    const levelColors: Record<string, string> = {
      'beginner': 'bg-green-100 text-green-800',
      'intermediate': 'bg-blue-100 text-blue-800',
      'advanced': 'bg-purple-100 text-purple-800',
      'expert': 'bg-red-100 text-red-800',
    };
    return levelColors[level.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  return (
    <Dialog open={open} onOpenChange={() => onClose()}>
      <DialogContent className="bg-white max-w-3xl max-h-[80vh] flex flex-col" style={{ backgroundColor: 'white' }}>
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Copy className="h-5 w-5" />
            <span>從課程庫複製</span>
          </DialogTitle>
          <DialogDescription>
            選擇要複製到此班級的課程
          </DialogDescription>
        </DialogHeader>

        {/* Search Bar */}
        <div className="relative my-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜尋課程名稱..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Selected Count */}
        {selectedPrograms.length > 0 && (
          <div className="mb-3 px-3 py-2 bg-blue-50 rounded-md">
            <span className="text-sm font-medium text-blue-700">
              已選擇 {selectedPrograms.length} 個課程
            </span>
          </div>
        )}

        {/* Programs List */}
        <div className="flex-1 overflow-y-auto min-h-[300px]">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">載入課程中...</p>
              </div>
            </div>
          ) : filteredPrograms.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <BookOpen className="h-12 w-12 text-gray-400 mb-3" />
              {programs.length === 0 ? (
                <>
                  <p className="text-gray-600 font-medium">目前沒有可複製的課程</p>
                  <p className="text-sm text-gray-500 mt-1">請先到「所有課程」頁面建立課程</p>
                </>
              ) : (
                <>
                  <p className="text-gray-600 font-medium">找不到符合的課程</p>
                  <p className="text-sm text-gray-500 mt-1">請嘗試其他搜尋關鍵字</p>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredPrograms.map((program) => (
                <div
                  key={program.id}
                  className={`border rounded-lg p-4 transition-colors ${
                    program.already_in_classroom
                      ? 'bg-gray-50 opacity-60'
                      : selectedPrograms.includes(program.id)
                        ? 'bg-blue-50 border-blue-300'
                        : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className="pt-1">
                      <input
                        type="checkbox"
                        checked={selectedPrograms.includes(program.id)}
                        onChange={() => handleToggleProgram(program.id)}
                        disabled={program.already_in_classroom}
                        className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium">{program.name}</h4>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelBadgeClass(program.level)}`}>
                          {program.level}
                        </span>
                        {program.already_in_classroom && (
                          <span className="inline-flex items-center space-x-1 text-xs text-green-600">
                            <CheckCircle className="h-3 w-3" />
                            <span>(已存在)</span>
                          </span>
                        )}
                      </div>
                      {program.description && (
                        <p className="text-sm text-gray-600 mt-1">{program.description}</p>
                      )}
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <div className="flex items-center space-x-1">
                          <Layers className="h-3 w-3" />
                          <span>{program.lesson_count || 0} 個課程單元</span>
                        </div>
                        {program.estimated_hours && (
                          <div className="flex items-center space-x-1">
                            <Clock className="h-3 w-3" />
                            <span>{program.estimated_hours} 小時</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={onClose} disabled={copying}>
            取消
          </Button>
          <Button
            onClick={handleCopyPrograms}
            disabled={selectedPrograms.length === 0 || copying}
          >
            {copying ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                複製中...
              </>
            ) : (
              <>
                <Copy className="h-4 w-4 mr-2" />
                複製到班級 ({selectedPrograms.length})
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
