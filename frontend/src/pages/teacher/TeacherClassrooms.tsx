import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import TeacherLayout from '@/components/TeacherLayout';
import { Users, BookOpen, Plus, Edit, RefreshCw, GraduationCap, Trash2, AlertTriangle } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface ClassroomDetail {
  id: number;
  name: string;
  description?: string;
  level?: string;
  student_count: number;
  students: Array<{
    id: number;
    name: string;
    email: string;
  }>;
  program_count?: number;
  created_at?: string;
}

export default function TeacherClassrooms() {
  const [classrooms, setClassrooms] = useState<ClassroomDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingClassroom, setEditingClassroom] = useState<ClassroomDetail | null>(null);
  const [editFormData, setEditFormData] = useState({ name: '', description: '', level: '' });
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  useEffect(() => {
    fetchClassrooms();
  }, []);

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTeacherClassrooms() as ClassroomDetail[];
      // Sort by ID to maintain consistent order
      const sortedData = data.sort((a, b) => a.id - b.id);
      setClassrooms(sortedData);
    } catch (err) {
      console.error('Fetch classrooms error:', err);
    } finally {
      setLoading(false);
    }
  };


  const handleEdit = (classroom: ClassroomDetail) => {
    setEditingClassroom(classroom);
    setEditFormData({
      name: classroom.name,
      description: classroom.description || '',
      level: classroom.level || 'A1'
    });
  };

  const handleSaveEdit = async () => {
    if (!editingClassroom) return;
    
    try {
      // API call to update classroom
      await apiClient.updateClassroom(editingClassroom.id, editFormData);
      
      // Refresh classrooms list
      await fetchClassrooms();
      setEditingClassroom(null);
    } catch (err) {
      console.error('Failed to update classroom:', err);
      alert('更新班級失敗，請稍後再試');
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirmId) return;
    
    try {
      // API call to delete classroom
      await apiClient.deleteClassroom(deleteConfirmId);
      
      // Refresh classrooms list
      await fetchClassrooms();
      setDeleteConfirmId(null);
    } catch (err) {
      console.error('Failed to delete classroom:', err);
      alert('刪除班級失敗，請稍後再試');
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-TW', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit' 
    });
  };

  const getLevelBadge = (level?: string) => {
    const levelColors: Record<string, string> = {
      'PREA': 'bg-gray-100 text-gray-800',
      'A1': 'bg-green-100 text-green-800',
      'A2': 'bg-blue-100 text-blue-800',
      'B1': 'bg-purple-100 text-purple-800',
      'B2': 'bg-indigo-100 text-indigo-800',
      'C1': 'bg-red-100 text-red-800',
      'C2': 'bg-orange-100 text-orange-800',
    };
    const color = levelColors[level?.toUpperCase() || 'A1'] || 'bg-gray-100 text-gray-800';
    return <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>{level || 'A1'}</span>;
  };

  if (loading) {
    return (
      <TeacherLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">載入中...</p>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-gray-900">我的班級</h2>
          <div className="flex items-center space-x-4">
            <Button onClick={fetchClassrooms} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              重新載入
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              新增班級
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">總班級數</p>
                <p className="text-2xl font-bold">{classrooms.length}</p>
              </div>
              <GraduationCap className="h-8 w-8 text-blue-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">總學生數</p>
                <p className="text-2xl font-bold">
                  {classrooms.reduce((sum, c) => sum + c.student_count, 0)}
                </p>
              </div>
              <Users className="h-8 w-8 text-green-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">活躍班級</p>
                <p className="text-2xl font-bold">{classrooms.length}</p>
              </div>
              <BookOpen className="h-8 w-8 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Classrooms Table */}
        <div className="bg-white rounded-lg shadow-sm border">
          <Table>
            <TableCaption>
              共 {classrooms.length} 個班級
            </TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px] text-left">ID</TableHead>
                <TableHead className="text-left">班級名稱</TableHead>
                <TableHead className="text-left">描述</TableHead>
                <TableHead className="text-left">等級</TableHead>
                <TableHead className="text-left">學生數</TableHead>
                <TableHead className="text-left">課程數</TableHead>
                <TableHead className="text-left">建立時間</TableHead>
                <TableHead className="text-left">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {classrooms.map((classroom) => (
                <TableRow 
                  key={classroom.id}
                  className="hover:bg-gray-50"
                >
                  <TableCell className="font-medium">{classroom.id}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <GraduationCap className="h-4 w-4 text-blue-600" />
                      </div>
                      <Link 
                        to={`/teacher/classroom/${classroom.id}`}
                        className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                      >
                        {classroom.name}
                      </Link>
                    </div>
                  </TableCell>
                  <TableCell>
                    <p className="text-sm text-gray-500 max-w-xs truncate">
                      {classroom.description || '暫無描述'}
                    </p>
                  </TableCell>
                  <TableCell>
                    {getLevelBadge(classroom.level)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center">
                      <Users className="h-4 w-4 mr-1 text-gray-400" />
                      {classroom.student_count}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center">
                      <BookOpen className="h-4 w-4 mr-1 text-gray-400" />
                      {classroom.program_count || 0}
                    </div>
                  </TableCell>
                  <TableCell>{formatDate(classroom.created_at)}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        title="編輯"
                        onClick={() => handleEdit(classroom)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        title="刪除"
                        onClick={() => setDeleteConfirmId(classroom.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Empty State */}
        {classrooms.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow-sm border">
            <GraduationCap className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">尚未建立班級</p>
            <p className="text-sm text-gray-400 mt-2">建立您的第一個班級，開始管理學生和課程</p>
            <Button className="mt-4">
              <Plus className="h-4 w-4 mr-2" />
              建立第一個班級
            </Button>
          </div>
        )}

        {/* Edit Dialog */}
        <Dialog open={!!editingClassroom} onOpenChange={(open) => !open && setEditingClassroom(null)}>
          <DialogContent className="bg-white" style={{ backgroundColor: 'white' }}>
            <DialogHeader>
              <DialogTitle>編輯班級</DialogTitle>
              <DialogDescription>
                修改班級資訊
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <label htmlFor="name" className="text-right">
                  班級名稱
                </label>
                <input
                  id="name"
                  value={editFormData.name}
                  onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                  className="col-span-3 px-3 py-2 border rounded-md"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <label htmlFor="description" className="text-right">
                  描述
                </label>
                <textarea
                  id="description"
                  value={editFormData.description}
                  onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                  className="col-span-3 px-3 py-2 border rounded-md"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <label htmlFor="level" className="text-right">
                  等級
                </label>
                <select
                  id="level"
                  value={editFormData.level}
                  onChange={(e) => setEditFormData({ ...editFormData, level: e.target.value })}
                  className="col-span-3 px-3 py-2 border rounded-md"
                >
                  <option value="preA">Pre-A</option>
                  <option value="A1">A1</option>
                  <option value="A2">A2</option>
                  <option value="B1">B1</option>
                  <option value="B2">B2</option>
                  <option value="C1">C1</option>
                  <option value="C2">C2</option>
                </select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditingClassroom(null)}>
                取消
              </Button>
              <Button onClick={handleSaveEdit}>
                儲存
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={!!deleteConfirmId} onOpenChange={(open) => !open && setDeleteConfirmId(null)}>
          <DialogContent className="bg-white" style={{ backgroundColor: 'white' }}>
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <span>確認刪除班級</span>
              </DialogTitle>
              <DialogDescription>
                確定要刪除這個班級嗎？此操作無法復原。
                班級內的學生和課程資料將會保留，但不再與此班級關聯。
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteConfirmId(null)}>
                取消
              </Button>
              <Button 
                variant="destructive" 
                onClick={handleDelete}
              >
                確認刪除
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TeacherLayout>
  );
}