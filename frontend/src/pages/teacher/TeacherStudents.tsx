import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import TeacherLayout from '@/components/TeacherLayout';
import StudentTable, { Student } from '@/components/StudentTable';
import { StudentDialogs } from '@/components/StudentDialogs';
import { Users, RefreshCw, Filter, Plus, UserCheck, UserX, Download } from 'lucide-react';
import { apiClient } from '@/lib/api';

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
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [dialogType, setDialogType] = useState<'view' | 'create' | 'edit' | 'delete' | null>(null);

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

  // 過濾並排序學生
  const filteredStudents = allStudents
    .filter(student => {
      const matchesClassroom = !selectedClassroom || student.classroom_id === selectedClassroom;
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

  const handleEmailStudent = (student: Student) => {
    // TODO: Implement email functionality
    console.log('Email student:', student);
  };

  const handleResetPassword = async (student: Student) => {
    if (!confirm(`確定要將 ${student.name} 的密碼重設為預設密碼嗎？`)) {
      return;
    }
    
    try {
      await apiClient.resetStudentPassword(student.id);
      // Refresh data
      fetchClassrooms();
    } catch (error) {
      console.error('Failed to reset password:', error);
      alert('重設密碼失敗，請稍後再試');
    }
  };

  const handleSaveStudent = () => {
    // Refresh data after save
    fetchClassrooms();
  };

  const handleDeleteStudent = () => {
    // Refresh data after delete
    fetchClassrooms();
  };

  const handleCloseDialog = () => {
    setSelectedStudent(null);
    setDialogType(null);
  };

  const handleSwitchToEdit = () => {
    // Switch from view to edit mode
    setDialogType('edit');
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
            onEmailStudent={handleEmailStudent}
            onResetPassword={handleResetPassword}
            onAddStudent={handleCreateStudent}
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
        onDelete={handleDeleteStudent}
        onSwitchToEdit={handleSwitchToEdit}
        classrooms={classrooms}
      />
    </TeacherLayout>
  );
}