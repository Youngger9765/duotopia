import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import TeacherLayout from '@/components/TeacherLayout';
import StudentTable, { Student } from '@/components/StudentTable';
import { StudentDialogs } from '@/components/StudentDialogs';
import { ClassroomAssignDialog } from '@/components/ClassroomAssignDialog';
import { Users, RefreshCw, Filter, Plus, UserCheck, UserX, Download, School, Trash2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';

interface Classroom {
  id: number;
  name: string;
  students: Student[];
}

export default function TeacherStudents() {
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [selectedStudentIds, setSelectedStudentIds] = useState<number[]>([]);
  const [allStudents, setAllStudents] = useState<Student[]>([]);
  const [selectedClassroom, setSelectedClassroom] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [dialogType, setDialogType] = useState<'view' | 'create' | 'edit' | 'delete' | null>(null);
  const [showAssignDialog, setShowAssignDialog] = useState(false);

  useEffect(() => {
    fetchClassrooms();
  }, []);

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      
      // Fetch classrooms for the dropdown
      const classroomData = await apiClient.getTeacherClassrooms() as Classroom[];
      setClassrooms(classroomData);
      
      // Fetch all students (including those without classroom)
      const studentsData = await apiClient.getAllStudents();
      
      // Format students data
      const studentsWithDetails = studentsData.map((student: any) => ({
        id: student.id,
        name: student.name,
        email: student.email,
        student_id: student.student_id || '',
        birthdate: student.birthdate || '',
        phone: student.phone || '',
        password_changed: student.password_changed || false,
        enrollment_date: student.enrollment_date || '',
        status: student.status || 'active' as const,
        last_login: student.last_login || null,
        classroom_id: student.classroom_id,
        classroom_name: student.classroom_name || '未分配',
      }));
      
      setAllStudents(studentsWithDetails);
    } catch (err) {
      console.error('Fetch classrooms error:', err);
      // Don't use mock data - show real error
      setAllStudents([]);
    } finally {
      setLoading(false);
    }
  };

  // 過濾並排序學生
  const filteredStudents = allStudents
    .filter(student => {
      // 班級篩選邏輯
      let matchesClassroom = true;
      if (selectedClassroom === null) {
        // 顯示所有學生
        matchesClassroom = true;
      } else if (selectedClassroom === 0) {
        // 只顯示未分配班級的學生
        matchesClassroom = !student.classroom_id;
      } else {
        // 顯示特定班級的學生
        matchesClassroom = student.classroom_id === selectedClassroom;
      }
      
      const matchesSearch = !searchTerm || 
        student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        student.email.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesClassroom && matchesSearch;
    })
    .sort((a, b) => a.id - b.id); // 按 ID 排序

  const handleCreateStudent = () => {
    setSelectedStudent(null);
    setDialogType('create');
  };

  const handleViewStudent = (student: Student) => {
    setSelectedStudent(student);
    setDialogType('view');
  };

  const handleEditStudent = (student: Student) => {
    setSelectedStudent(student);
    setDialogType('edit');
  };

  const handleResetPassword = async (student: Student) => {
    if (!confirm(`確定要將 ${student.name} 的密碼重設為預設密碼嗎？`)) {
      return;
    }
    
    try {
      await apiClient.resetStudentPassword(student.id);
      toast.success(`已重設 ${student.name} 的密碼為預設密碼`);
      // Refresh data
      fetchClassrooms();
    } catch (error) {
      console.error('Failed to reset password:', error);
      toast.error('重設密碼失敗，請稍後再試');
    }
  };

  const handleSaveStudent = () => {
    // Refresh data after save
    fetchClassrooms();
  };

  const handleDeleteStudent = async (student: Student) => {
    try {
      await apiClient.deleteStudent(student.id);
      toast.success(`已刪除學生：${student.name}`);
      // Refresh data after delete
      fetchClassrooms();
    } catch (error) {
      console.error('Failed to delete student:', error);
      toast.error('刪除學生失敗，請稍後再試');
    }
  };

  const handleCloseDialog = () => {
    setSelectedStudent(null);
    setDialogType(null);
  };

  const handleSwitchToEdit = () => {
    // Switch from view to edit mode
    setDialogType('edit');
  };

  const handleExportStudents = () => {
    // 準備 CSV 資料
    const headers = ['姓名', 'Email', '學號', '生日', '班級', '密碼狀態', '最後登入'];
    const rows = filteredStudents.map(student => [
      student.name,
      student.email || '-',
      student.student_id || '-',
      student.birthdate || '-',
      student.classroom_name || '未分配',
      student.password_changed ? '已更改' : '預設密碼',
      student.last_login || '從未登入'
    ]);
    
    // 建立 CSV 內容
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    // 建立下載連結
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `學生名單_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast.success(`已匯出 ${filteredStudents.length} 位學生資料`);
  };
  
  const handleBulkAction = async (action: string, studentIds: number[]) => {
    // Handle selection update
    if (action === 'selection') {
      setSelectedStudentIds(studentIds);
      return;
    }
    
    setSelectedStudentIds(studentIds);
    
    if (action === 'assign') {
      // Show classroom selection dialog
      setShowAssignDialog(true);
    } else if (action === 'delete') {
      if (confirm(`確定要刪除 ${studentIds.length} 位學生嗎？`)) {
        try {
          for (const studentId of studentIds) {
            await apiClient.deleteStudent(studentId);
          }
          toast.success(`成功刪除 ${studentIds.length} 位學生`);
          fetchClassrooms();
        } catch (error) {
          console.error('Failed to delete students:', error);
          toast.error('刪除失敗，請稍後再試');
        }
      }
    }
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
            {selectedStudentIds.length > 0 && (
              <div className="flex items-center space-x-2 px-3 py-1 bg-blue-50 rounded-md">
                <span className="text-sm font-medium text-blue-700">
                  已選擇 {selectedStudentIds.length} 位學生
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleBulkAction('assign', selectedStudentIds)}
                >
                  <School className="h-4 w-4 mr-2" />
                  批量分配班級
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-red-600 hover:bg-red-50"
                  onClick={() => handleBulkAction('delete', selectedStudentIds)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  批量刪除
                </Button>
              </div>
            )}
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
                value={selectedClassroom === null ? '' : (selectedClassroom === 0 ? '0' : selectedClassroom.toString())}
                onChange={(e) => {
                  if (e.target.value === '') {
                    setSelectedClassroom(null); // 所有班級
                  } else if (e.target.value === '0') {
                    setSelectedClassroom(0); // 未分配
                  } else {
                    setSelectedClassroom(Number(e.target.value));
                  }
                }}
                className="px-3 py-2 border rounded-md text-sm"
              >
                <option value="">所有班級</option>
                <option value="0">未分配</option>
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
            <Button variant="outline" size="sm" onClick={handleExportStudents}>
              <Download className="h-4 w-4 mr-2" />
              匯出名單
            </Button>
            <Button size="sm" onClick={handleCreateStudent}>
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
          <StudentTable
            students={filteredStudents}
            showClassroom={true}
            onViewStudent={handleViewStudent}
            onEditStudent={handleEditStudent}
            onResetPassword={handleResetPassword}
            onDeleteStudent={handleDeleteStudent}
            onAddStudent={handleCreateStudent}
            onBulkAction={handleBulkAction}
            emptyMessage={
              searchTerm 
                ? '找不到符合條件的學生'
                : selectedClassroom 
                  ? '此班級暫無學生' 
                  : '尚未建立學生'
            }
          />
        </div>
      </div>

      {/* Student Dialogs */}
      <StudentDialogs
        student={selectedStudent}
        dialogType={dialogType}
        onClose={handleCloseDialog}
        onSave={handleSaveStudent}
        onDelete={() => {}} // 保留但不使用，因為刪除現在直接在列表處理
        onSwitchToEdit={handleSwitchToEdit}
        classrooms={classrooms}
      />
      
      {/* Classroom Assignment Dialog */}
      <ClassroomAssignDialog
        open={showAssignDialog}
        onClose={() => setShowAssignDialog(false)}
        onConfirm={(classroomId) => {
          // Handle classroom assignment
          (async () => {
            try {
              for (const studentId of selectedStudentIds) {
                await apiClient.updateStudent(studentId, { classroom_id: classroomId });
              }
              const classroom = classrooms.find(c => c.id === classroomId);
              toast.success(`成功分配 ${selectedStudentIds.length} 位學生到「${classroom?.name}」`);
              setSelectedStudentIds([]);
              setShowAssignDialog(false);
              fetchClassrooms();
            } catch (error) {
              console.error('Failed to assign students:', error);
              toast.error('分配失敗，請稍後再試');
            }
          })();
        }}
        classrooms={classrooms}
        studentCount={selectedStudentIds.length}
      />
    </TeacherLayout>
  );
}