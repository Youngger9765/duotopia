import { useState, useEffect } from 'react';
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
import { BookOpen, RefreshCw, Filter, Plus, Edit, Eye, Trash2 } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Program {
  id: number;
  name: string;
  description?: string;
  classroom_id: number;
  classroom_name: string;
  estimated_hours?: number;
  level: string;
  created_at?: string;
  updated_at?: string;
  student_count?: number;
  lesson_count?: number;
  status?: 'active' | 'draft' | 'archived';
}

interface Classroom {
  id: number;
  name: string;
}

export default function TeacherPrograms() {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [selectedClassroom, setSelectedClassroom] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [programsData, classroomsData] = await Promise.all([
        apiClient.getTeacherPrograms() as Promise<Program[]>,
        apiClient.getTeacherClassrooms() as Promise<any[]>
      ]);
      
      // TODO: Replace with real data from API
      // MOCK DATA START - 以下為模擬資料，需要從後端 API 取得真實資料
      const enrichedPrograms = programsData.map(p => ({
        ...p,
        // MOCK: 模擬學生數量
        student_count: Math.floor(Math.random() * 30) + 5,
        // MOCK: 模擬課程單元數
        lesson_count: Math.floor(Math.random() * 20) + 1,
        // MOCK: 模擬課程狀態
        status: (['active', 'draft', 'archived'] as const)[Math.floor(Math.random() * 3)],
        // MOCK: 模擬建立時間
        created_at: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000).toISOString(),
        // MOCK: 模擬更新時間
        updated_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      }));
      // MOCK DATA END
      
      setPrograms(enrichedPrograms);
      setClassrooms(classroomsData.map(c => ({ id: c.id, name: c.name })));
    } catch (err) {
      console.error('Fetch data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredPrograms = selectedClassroom
    ? programs.filter(p => p.classroom_id === selectedClassroom)
    : programs;

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'active':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">進行中</span>;
      case 'draft':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">草稿</span>;
      case 'archived':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">已封存</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">未知</span>;
    }
  };

  const getLevelBadge = (level: string) => {
    const levelColors: Record<string, string> = {
      'beginner': 'bg-green-100 text-green-800',
      'intermediate': 'bg-blue-100 text-blue-800',
      'advanced': 'bg-purple-100 text-purple-800',
      'expert': 'bg-red-100 text-red-800',
    };
    const color = levelColors[level.toLowerCase()] || 'bg-gray-100 text-gray-800';
    return <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>{level}</span>;
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
          <h2 className="text-3xl font-bold text-gray-900">所有課程</h2>
          <div className="flex items-center space-x-4">
            {/* Filter Dropdown */}
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <select
                value={selectedClassroom || ''}
                onChange={(e) => setSelectedClassroom(e.target.value ? Number(e.target.value) : null)}
                className="px-3 py-2 border rounded-md text-sm"
              >
                <option value="">所有班級</option>
                {classrooms.map((classroom) => (
                  <option key={classroom.id} value={classroom.id}>
                    {classroom.name}
                  </option>
                ))}
              </select>
            </div>
            {/* Refresh Button */}
            <Button onClick={fetchData} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              重新載入
            </Button>
            {/* Add New Program Button */}
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              新增課程
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">總課程數</p>
                <p className="text-2xl font-bold">{filteredPrograms.length}</p>
              </div>
              <BookOpen className="h-8 w-8 text-blue-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">進行中</p>
                <p className="text-2xl font-bold">{filteredPrograms.filter(p => p.status === 'active').length}</p>
              </div>
              <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 font-bold">A</span>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">草稿</p>
                <p className="text-2xl font-bold">{filteredPrograms.filter(p => p.status === 'draft').length}</p>
              </div>
              <div className="h-8 w-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 font-bold">D</span>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">已封存</p>
                <p className="text-2xl font-bold">{filteredPrograms.filter(p => p.status === 'archived').length}</p>
              </div>
              <div className="h-8 w-8 bg-gray-100 rounded-full flex items-center justify-center">
                <span className="text-gray-600 font-bold">X</span>
              </div>
            </div>
          </div>
        </div>

        {/* Programs Table */}
        <div className="bg-white rounded-lg shadow-sm border">
          <Table>
            <TableCaption>
              共 {filteredPrograms.length} 個課程
            </TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px] text-left">ID</TableHead>
                <TableHead className="text-left">課程名稱</TableHead>
                <TableHead className="text-left">所屬班級</TableHead>
                <TableHead className="text-left">等級</TableHead>
                <TableHead className="text-left">狀態</TableHead>
                <TableHead className="text-left">課程數</TableHead>
                <TableHead className="text-left">學生數</TableHead>
                <TableHead className="text-left">預計時數</TableHead>
                <TableHead className="text-left">更新時間</TableHead>
                <TableHead className="text-left">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPrograms.map((program) => (
                <TableRow key={program.id}>
                  <TableCell className="font-medium">{program.id}</TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">{program.name}</p>
                      {program.description && (
                        <p className="text-sm text-gray-500 max-w-xs truncate">{program.description}</p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{program.classroom_name}</TableCell>
                  <TableCell>{getLevelBadge(program.level)}</TableCell>
                  <TableCell>{getStatusBadge(program.status)}</TableCell>
                  <TableCell>{program.lesson_count || '-'}</TableCell>
                  <TableCell>{program.student_count || '-'}</TableCell>
                  <TableCell>
                    {program.estimated_hours ? `${program.estimated_hours} 小時` : '-'}
                  </TableCell>
                  <TableCell>{formatDate(program.updated_at)}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700">
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
        {filteredPrograms.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow-sm border">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">
              {selectedClassroom ? '此班級暫無課程' : '尚未建立課程'}
            </p>
            <Button className="mt-4">
              <Plus className="h-4 w-4 mr-2" />
              建立第一個課程
            </Button>
          </div>
        )}
      </div>
    </TeacherLayout>
  );
}