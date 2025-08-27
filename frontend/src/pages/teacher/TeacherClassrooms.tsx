import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import TeacherLayout from '@/components/TeacherLayout';
import { Users, BookOpen, Clock, Plus, Edit, Eye, Settings, RefreshCw, GraduationCap } from 'lucide-react';
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
  const navigate = useNavigate();
  const [classrooms, setClassrooms] = useState<ClassroomDetail[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClassrooms();
  }, []);

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTeacherClassrooms() as ClassroomDetail[];
      setClassrooms(data);
    } catch (err) {
      console.error('Fetch classrooms error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClassroomClick = (classroomId: number) => {
    navigate(`/teacher/classroom/${classroomId}`);
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
        <div className="grid grid-cols-4 gap-4 mb-6">
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
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">平均班級人數</p>
                <p className="text-2xl font-bold">
                  {classrooms.length > 0 
                    ? Math.round(classrooms.reduce((sum, c) => sum + c.student_count, 0) / classrooms.length)
                    : 0}
                </p>
              </div>
              <Clock className="h-8 w-8 text-orange-500" />
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
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleClassroomClick(classroom.id)}
                >
                  <TableCell className="font-medium">{classroom.id}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <GraduationCap className="h-4 w-4 text-blue-600" />
                      </div>
                      <p className="font-medium">{classroom.name}</p>
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
                    <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        title="進入班級"
                        onClick={() => handleClassroomClick(classroom.id)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" title="編輯">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" title="設定">
                        <Settings className="h-4 w-4" />
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
      </div>
    </TeacherLayout>
  );
}