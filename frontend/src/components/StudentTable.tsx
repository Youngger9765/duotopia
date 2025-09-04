import React from 'react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Edit, Users, Plus, Eye, RotateCcw, Trash2, Copy, CheckSquare, Square } from 'lucide-react';

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
  onViewStudent?: (student: Student) => void;
  onResetPassword?: (student: Student) => void;
  onDeleteStudent?: (student: Student) => void;
  onBulkAction?: (action: string, studentIds: number[]) => void;
  emptyMessage?: string;
  emptyDescription?: string;
  selectedIds?: Set<number>;
  onSelectionChange?: (ids: Set<number>) => void;
}

export default function StudentTable({
  students,
  showClassroom = false,
  onAddStudent,
  onEditStudent,
  onViewStudent,
  onResetPassword,
  onDeleteStudent,
  onBulkAction,
  emptyMessage = '尚無學生',
  emptyDescription,
  selectedIds: externalSelectedIds,
  onSelectionChange
}: StudentTableProps) {
  const [internalSelectedIds, setInternalSelectedIds] = React.useState<Set<number>>(new Set());
  const selectedIds = externalSelectedIds || internalSelectedIds;
  const setSelectedIds = onSelectionChange || setInternalSelectedIds;

  const toggleSelect = (id: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
    if (onBulkAction && newSelected.size > 0) {
      // Notify parent about selection
      onBulkAction('selection', Array.from(newSelected));
    }
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === students.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(students.map(s => s.id)));
    }
  };

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
          {onBulkAction && (
            <TableHead className="w-[40px]">
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleSelectAll}
                className="p-0 h-8 w-8"
              >
                {selectedIds.size === students.length && students.length > 0 ? (
                  <CheckSquare className="h-4 w-4" />
                ) : (
                  <Square className="h-4 w-4" />
                )}
              </Button>
            </TableHead>
          )}
          <TableHead className="w-[50px] text-left">ID</TableHead>
          <TableHead className="text-left min-w-[120px]">學生姓名</TableHead>
          <TableHead className="text-left min-w-[250px]">聯絡資訊</TableHead>
          <TableHead className="text-left min-w-[100px] whitespace-nowrap">密碼狀態</TableHead>
          <TableHead className="text-left w-[80px]">狀態</TableHead>
          <TableHead className="text-left min-w-[100px] whitespace-nowrap">最後登入</TableHead>
          <TableHead className="text-left w-[120px]">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {students.map((student) => (
          <TableRow key={student.id}>
            {onBulkAction && (
              <TableCell>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleSelect(student.id)}
                  className="p-0 h-8 w-8"
                >
                  {selectedIds.has(student.id) ? (
                    <CheckSquare className="h-4 w-4" />
                  ) : (
                    <Square className="h-4 w-4" />
                  )}
                </Button>
              </TableCell>
            )}
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
              <div>
                <div className="text-sm">{student.email || '-'}</div>
                <div className="flex items-center gap-2 mt-1">
                  {showClassroom && (
                    student.classroom_name ? (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                        {student.classroom_name}
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                        未分配
                      </span>
                    )
                  )}
                  {student.student_id && (
                    <span className="text-xs text-gray-500">#{student.student_id}</span>
                  )}
                </div>
              </div>
            </TableCell>
            <TableCell className="whitespace-nowrap">
              <div className="inline-flex items-center space-x-1">
                {student.password_changed ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-50 text-green-700 whitespace-nowrap">
                    已更改
                  </span>
                ) : (
                  <>
                    <span
                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-50 text-yellow-700 cursor-help whitespace-nowrap"
                      title={student.birthdate ? `預設: ${student.birthdate.replace(/-/g, '')}` : '預設密碼'}
                    >
                      預設
                    </span>
                    {student.birthdate && (
                      <Button
                        variant="ghost"
                        size="sm"
                        title={`複製密碼: ${student.birthdate?.replace(/-/g, '')}`}
                        onClick={() => {
                          const password = student.birthdate.replace(/-/g, '');
                          navigator.clipboard.writeText(password);
                          toast.success(`密碼已複製`);
                        }}
                        className="h-6 w-6 p-0"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    )}
                  </>
                )}
                {student.password_changed && onResetPassword && (
                  <Button
                    variant="ghost"
                    size="sm"
                    title="重設為預設密碼"
                    onClick={() => onResetPassword(student)}
                    className="h-7 px-2"
                  >
                    <RotateCcw className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </TableCell>
            <TableCell className="whitespace-nowrap">{getStatusBadge(student.status)}</TableCell>
            <TableCell className="whitespace-nowrap">
              {student.last_login ? (
                <div>
                  <div className="text-sm">{formatDate(student.last_login)}</div>
                  <div className="text-xs text-gray-500">
                    {Math.floor((Date.now() - new Date(student.last_login).getTime()) / (1000 * 60 * 60 * 24))} 天前
                  </div>
                </div>
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
                {onDeleteStudent && (
                  <Button
                    variant="ghost"
                    size="sm"
                    title="刪除"
                    onClick={() => {
                      if (confirm(`確定要刪除學生「${student.name}」嗎？此操作無法復原。`)) {
                        onDeleteStudent(student);
                      }
                    }}
                    className="hover:bg-red-50 hover:text-red-600"
                  >
                    <Trash2 className="h-4 w-4" />
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
