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
import { Mail, Edit, Users, Plus, Eye } from 'lucide-react';

export interface Student {
  id: number;
  name: string;
  email: string;
  student_id?: string;
  birthdate?: string;
  password_changed?: boolean;
  last_login?: string | null;
  status?: string;
  classroom_id?: number;
  classroom_name?: string;
  phone?: string;
  enrollment_date?: string;
}

interface StudentTableProps {
  students: Student[];
  showClassroom?: boolean; // Show classroom column in all students view
  onAddStudent?: () => void;
  onEditStudent?: (student: Student) => void;
  onEmailStudent?: (student: Student) => void;
  onViewStudent?: (student: Student) => void;
  emptyMessage?: string;
  emptyDescription?: string;
}

export default function StudentTable({
  students,
  showClassroom = false,
  onAddStudent,
  onEditStudent,
  onEmailStudent,
  onViewStudent,
  emptyMessage = '尚無學生',
  emptyDescription
}: StudentTableProps) {
  const formatDate = (dateString?: string | null) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-TW', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit' 
    });
  };

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

  if (students.length === 0) {
    return (
      <div className="text-center py-12">
        <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500">{emptyMessage}</p>
        {emptyDescription && (
          <p className="text-sm text-gray-400 mt-2">{emptyDescription}</p>
        )}
        {onAddStudent && (
          <Button className="mt-4" size="sm" onClick={onAddStudent}>
            <Plus className="h-4 w-4 mr-2" />
            新增第一位學生
          </Button>
        )}
      </div>
    );
  }

  return (
    <Table>
      <TableCaption>
        共 {students.length} 位學生
      </TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[50px] text-left">ID</TableHead>
          <TableHead className="text-left">學生姓名</TableHead>
          <TableHead className="text-left">Email</TableHead>
          {showClassroom && (
            <TableHead className="text-left">班級</TableHead>
          )}
          <TableHead className="text-left">學號</TableHead>
          <TableHead className="text-left">密碼狀態</TableHead>
          <TableHead className="text-left">狀態</TableHead>
          <TableHead className="text-left">最後登入</TableHead>
          <TableHead className="text-left">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {students.map((student) => (
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
            {showClassroom && (
              <TableCell>{student.classroom_name || '-'}</TableCell>
            )}
            <TableCell>{student.student_id || '-'}</TableCell>
            <TableCell>
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
            </TableCell>
            <TableCell>{getStatusBadge(student.status)}</TableCell>
            <TableCell>
              {student.last_login ? (
                <>
                  <p className="text-sm">{formatDate(student.last_login)}</p>
                  <p className="text-xs text-gray-500">
                    {Math.floor((Date.now() - new Date(student.last_login).getTime()) / (1000 * 60 * 60 * 24))} 天前
                  </p>
                </>
              ) : '-'}
            </TableCell>
            <TableCell>
              <div className="flex items-center space-x-2">
                {onViewStudent && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    title="查看詳情"
                    onClick={() => onViewStudent(student)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                )}
                {onEditStudent && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    title="編輯"
                    onClick={() => onEditStudent(student)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                )}
                {onEmailStudent && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    title="發送郵件"
                    onClick={() => onEmailStudent(student)}
                  >
                    <Mail className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}