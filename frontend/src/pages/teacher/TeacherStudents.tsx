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
import { Users, RefreshCw, Filter, Plus, Edit, Eye, Mail, UserCheck, UserX, Download } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Student {
  id: number;
  name: string;
  email: string;
  classroom_id?: number;
  classroom_name?: string;
  phone?: string;
  birthdate?: string;  // 生日 (YYYY-MM-DD 格式，用於產生預設密碼 YYYYMMDD)
  password_changed?: boolean;  // 是否已更改密碼
  enrollment_date?: string;
  status?: 'active' | 'inactive' | 'suspended';
  last_login?: string | null;
  total_assignments?: number;
  completed_assignments?: number;
  average_score?: number;
  study_hours?: number;
}

interface Classroom {
  id: number;
  name: string;
  students: Student[];
}

export default function TeacherStudents() {
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [allStudents, setAllStudents] = useState<Student[]>([]);
  const [selectedClassroom, setSelectedClassroom] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchClassrooms();
  }, []);

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTeacherClassrooms() as Classroom[];
      setClassrooms(data);
      
      // Extract real students from classrooms data
      const studentsWithDetails = data.flatMap(classroom => 
        classroom.students.map(student => ({
          ...student,
          classroom_id: classroom.id,
          classroom_name: classroom.name,
          // Set default values for fields that might be missing
          phone: student.phone || '',
          birthdate: student.birthdate || '',
          password_changed: student.password_changed || false,
          enrollment_date: student.enrollment_date || '',
          status: student.status || 'active' as const,
          last_login: student.last_login || null,
        }))
      );
      
      setAllStudents(studentsWithDetails);
    } catch (err) {
      console.error('Fetch classrooms error:', err);
      // Don't use mock data - show real error
      setAllStudents([]);
    } finally {
      setLoading(false);
    }
  };

  // 過濾學生
  const filteredStudents = allStudents.filter(student => {
    const matchesClassroom = !selectedClassroom || student.classroom_id === selectedClassroom;
    const matchesSearch = !searchTerm || 
      student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      student.email.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesClassroom && matchesSearch;
  });

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'active':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">活躍</span>;
      case 'inactive':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">未活躍</span>;
      case 'suspended':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">已停權</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">未知</span>;
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
          <h2 className="text-3xl font-bold text-gray-900">所有學生</h2>
          <div className="flex items-center space-x-4">
            {/* Search Input */}
            <input
              type="text"
              placeholder="搜尋學生姓名或 Email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-2 border rounded-md text-sm w-64"
            />
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
            {/* Action Buttons */}
            <Button onClick={fetchClassrooms} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              重新載入
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              匯出名單
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              新增學生
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">總學生數</p>
                <p className="text-2xl font-bold">{filteredStudents.length}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">活躍學生</p>
                <p className="text-2xl font-bold">{filteredStudents.filter(s => s.status === 'active').length}</p>
              </div>
              <UserCheck className="h-8 w-8 text-green-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">未活躍</p>
                <p className="text-2xl font-bold">{filteredStudents.filter(s => s.status === 'inactive').length}</p>
              </div>
              <UserX className="h-8 w-8 text-yellow-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">已停權</p>
                <p className="text-2xl font-bold">{filteredStudents.filter(s => s.status === 'suspended').length}</p>
              </div>
              <div className="h-8 w-8 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-red-600 font-bold">!</span>
              </div>
            </div>
          </div>
        </div>

        {/* Students Table */}
        <div className="bg-white rounded-lg shadow-sm border">
          <Table>
            <TableCaption>
              共 {filteredStudents.length} 位學生
            </TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px] text-left">ID</TableHead>
                <TableHead className="text-left">學生姓名</TableHead>
                <TableHead className="text-left">Email</TableHead>
                <TableHead className="text-left">班級</TableHead>
                <TableHead className="text-left">密碼狀態</TableHead>
                <TableHead className="text-left">狀態</TableHead>
                <TableHead className="text-left">最後登入</TableHead>
                <TableHead className="text-left">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredStudents.map((student) => (
                  <TableRow key={student.id}>
                    <TableCell className="font-medium">{student.id}</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">
                            {student.name.charAt(0)}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium">{student.name}</p>
                          {student.phone && (
                            <p className="text-xs text-gray-500">{student.phone}</p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        <Mail className="h-3 w-3 text-gray-400" />
                        <span className="text-sm">{student.email}</span>
                      </div>
                    </TableCell>
                    <TableCell>{student.classroom_name || '-'}</TableCell>
                    <TableCell>
                      {/* 密碼狀態顯示 */}
                      <div className="space-y-1">
                        {student.password_changed ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            已更改
                          </span>
                        ) : (
                          <div>
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                              預設密碼
                            </span>
                            {student.birthdate && (
                              <p className="text-xs text-gray-500 mt-1">
                                {student.birthdate.replace(/-/g, '')}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(student.status)}</TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {student.last_login ? (
                          <>
                            <p>{formatDate(student.last_login)}</p>
                            <p className="text-xs text-gray-500">
                              {Math.floor((Date.now() - new Date(student.last_login).getTime()) / (1000 * 60 * 60 * 24))} 天前
                            </p>
                          </>
                        ) : '-'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button variant="ghost" size="sm" title="查看詳情">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" title="編輯">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" title="發送郵件">
                          <Mail className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Empty State */}
        {filteredStudents.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow-sm border">
            <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">
              {searchTerm 
                ? '找不到符合條件的學生'
                : selectedClassroom 
                  ? '此班級暫無學生' 
                  : '尚未建立學生'}
            </p>
            {!searchTerm && (
              <Button className="mt-4">
                <Plus className="h-4 w-4 mr-2" />
                新增第一位學生
              </Button>
            )}
          </div>
        )}
      </div>
    </TeacherLayout>
  );
}