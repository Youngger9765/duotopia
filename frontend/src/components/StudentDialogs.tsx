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
import { AlertTriangle, Eye, Edit, Trash2, Plus, Mail, Phone, Calendar, School } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';

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

interface StudentDialogsProps {
  student: Student | null;
  dialogType: 'view' | 'create' | 'edit' | 'delete' | null;
  onClose: () => void;
  onSave: (student: Student) => void;
  onDelete: (studentId: number) => void;
  onSwitchToEdit?: () => void;
  classrooms?: Array<{ id: number; name: string; }>;
}

export function StudentDialogs({
  student,
  dialogType,
  onClose,
  onSave,
  onDelete,
  onSwitchToEdit,
  classrooms = []
}: StudentDialogsProps) {
  const [formData, setFormData] = useState<Partial<Student>>({
    name: '',
    email: '',
    student_id: '',
    birthdate: '',
    phone: '',
    // 如果只有一個班級（從班級頁面新增），自動設定為該班級
    classroom_id: classrooms.length === 1 ? classrooms[0].id : undefined,
    status: 'active'
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (student && (dialogType === 'edit' || dialogType === 'view')) {
      setFormData({
        name: student.name,
        email: student.email,
        student_id: student.student_id || '',
        birthdate: student.birthdate || '',
        phone: student.phone || '',
        classroom_id: student.classroom_id,
        status: student.status || 'active'
      });
    } else if (dialogType === 'create') {
      setFormData({
        name: '',
        email: '',
        student_id: '',
        birthdate: '',
        phone: '',
        // 如果只有一個班級（從班級頁面新增），自動設定為該班級
        classroom_id: classrooms.length === 1 ? classrooms[0].id : undefined,
        status: 'active'
      });
    }
  }, [student, dialogType, classrooms]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name?.trim()) {
      newErrors.name = '姓名為必填';
    }

    // Email 是選填，但如果有填寫則檢查格式
    if (formData.email?.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email 格式不正確';
    }

    if (!formData.birthdate) {
      newErrors.birthdate = '生日為必填（用作預設密碼）';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      if (dialogType === 'create') {
        // Create new student - ensure required fields are present
        const createData: Partial<Student> & { classroom_id?: number } = {
          name: formData.name || '',
          email: formData.email || undefined,  // 如果沒有填寫，傳 undefined 而非空字串
          birthdate: formData.birthdate || '',
          student_id: formData.student_id,
          phone: formData.phone
        };

        // classroom_id 是可選的，只有在選擇了班級時才傳送
        if (formData.classroom_id) {
          createData.classroom_id = formData.classroom_id;
        }

        const response = await apiClient.createStudent(createData);
        // 如果有生日，顯示預設密碼
        if (formData.birthdate) {
          const defaultPassword = formData.birthdate.replace(/-/g, '');
          toast.success(
            <div>
              <p>學生「{formData.name}」已成功新增</p>
              <p className="text-sm mt-1">預設密碼：<code className="bg-gray-100 px-1 rounded">{defaultPassword}</code></p>
            </div>,
            { duration: 5000 }
          );
        } else {
          toast.success(`學生「${formData.name}」已成功新增`);
        }
        // 只傳遞 Student interface 需要的字段
        const newStudent: Student = {
          id: response.id,
          name: response.name,
          email: response.email,
          student_id: response.student_id,
          birthdate: response.birthdate,
          password_changed: response.password_changed,
          classroom_id: response.classroom_id,
          status: 'active'
        };
        onSave(newStudent);
      } else if (dialogType === 'edit' && student) {
        // Update existing student
        const response = await apiClient.updateStudent(student.id, formData);
        toast.success(`學生「${student.name}」資料已更新`);
        onSave({ ...student, ...(response as Partial<Student>) });
      }
      onClose();
    } catch (error) {
      console.error('Error saving student:', error);

      // Parse error message
      let errorMessage = '儲存失敗，請稍後再試';

      if (error.message) {
        try {
          // Try to parse JSON error response
          const errorData = JSON.parse(error.message);

          // Handle Pydantic validation errors
          if (Array.isArray(errorData.detail)) {
            const validationErrors = errorData.detail;
            const fieldErrors: Record<string, string> = {};

            validationErrors.forEach((err: { loc?: string[]; msg: string }) => {
              const field = err.loc?.[1]; // Get field name from location
              const msg = err.msg;

              if (field === 'classroom_id') {
                // classroom_id is optional, skip this error
                return;
              } else if (field === 'name') {
                fieldErrors.name = '姓名為必填';
              } else if (field === 'birthdate') {
                fieldErrors.birthdate = '生日為必填（用作預設密碼）';
              } else if (field === 'email') {
                fieldErrors.email = err.msg || 'Email格式錯誤';
              } else {
                errorMessage = msg || '資料驗證失敗';
              }
            });

            if (Object.keys(fieldErrors).length > 0) {
              setErrors(fieldErrors);
              errorMessage = '請修正標示的欄位';
            }
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else {
            errorMessage = errorData.detail || errorMessage;
          }
        } catch {
          // If not JSON, use the message directly
          errorMessage = error.message;
        }
      }

      // Handle specific error cases
      if (typeof errorMessage === 'string') {
        if (errorMessage.includes('already registered')) {
          errorMessage = 'Email已被使用，請使用其他Email';
          setErrors({ email: errorMessage });
        } else if (errorMessage.includes('Invalid birthdate format')) {
          errorMessage = '生日格式錯誤，請使用YYYY-MM-DD格式';
          setErrors({ birthdate: errorMessage });
        } else if (errorMessage.includes('Field required')) {
          errorMessage = '請填寫所有必填欄位';
        }
      }

      // Ensure errorMessage is a string before showing toast
      if (typeof errorMessage === 'string') {
        toast.error(errorMessage);
      } else {
        toast.error('儲存失敗，請稍後再試');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!student) return;

    setLoading(true);
    try {
      await apiClient.deleteStudent(student.id);
      toast.success(`學生「${student.name}」已刪除`);
      onDelete(student.id);
      onClose();
    } catch (error) {
      console.error('Error deleting student:', error);
      toast.error('刪除失敗，請稍後再試');
      setErrors({ submit: '刪除失敗，請稍後再試' });
    } finally {
      setLoading(false);
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

  // View Dialog
  if (dialogType === 'view' && student) {
    return (
      <Dialog open={true} onOpenChange={() => onClose()}>
        <DialogContent className="bg-white max-w-2xl" style={{ backgroundColor: 'white' }}>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Eye className="h-5 w-5" />
              <span>學生詳細資料</span>
            </DialogTitle>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Student Avatar and Basic Info */}
            <div className="flex items-start space-x-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-2xl font-medium text-blue-600">
                  {student.name.charAt(0)}
                </span>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold">{student.name}</h3>
                <p className="text-sm text-gray-500">ID: {student.id}</p>
                {student.student_id && (
                  <p className="text-sm text-gray-500">學號: {student.student_id}</p>
                )}
              </div>
              <div>{getStatusBadge(student.status)}</div>
            </div>

            {/* Detailed Information */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">Email</p>
                    <p className="text-sm font-medium">{student.email}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Phone className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">電話</p>
                    <p className="text-sm font-medium">{student.phone || '-'}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">生日</p>
                    <p className="text-sm font-medium">{formatDate(student.birthdate)}</p>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <School className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-500">班級</p>
                    <p className="text-sm font-medium">{student.classroom_name || '-'}</p>
                  </div>
                </div>

                <div>
                  <p className="text-xs text-gray-500">密碼狀態</p>
                  <p className="text-sm font-medium">
                    {student.password_changed ? (
                      <span className="text-green-600">已更改</span>
                    ) : (
                      <span className="text-yellow-600">預設密碼 ({student.birthdate?.replace(/-/g, '')})</span>
                    )}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-gray-500">最後登入</p>
                  <p className="text-sm font-medium">
                    {student.last_login ? formatDate(student.last_login) : '從未登入'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={onClose}>關閉</Button>
            <Button onClick={() => {
              if (onSwitchToEdit) {
                onSwitchToEdit();
              }
            }}>
              <Edit className="h-4 w-4 mr-2" />
              編輯
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  // Create/Edit Dialog
  if (dialogType === 'create' || dialogType === 'edit') {
    return (
      <Dialog open={true} onOpenChange={() => onClose()}>
        <DialogContent className="bg-white max-w-2xl" style={{ backgroundColor: 'white' }}>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              {dialogType === 'create' ? (
                <>
                  <Plus className="h-5 w-5" />
                  <span>新增學生</span>
                </>
              ) : (
                <>
                  <Edit className="h-5 w-5" />
                  <span>編輯學生資料</span>
                </>
              )}
            </DialogTitle>
            <DialogDescription>
              {dialogType === 'create'
                ? '填寫學生資料以新增學生。生日將作為預設密碼。'
                : '更新學生資料'}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="name" className="text-sm font-medium">
                  姓名 <span className="text-red-500">*</span>
                </label>
                <input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className={`w-full mt-1 px-3 py-2 border rounded-md ${errors.name ? 'border-red-500' : ''}`}
                  placeholder="請輸入學生姓名"
                />
                {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name}</p>}
              </div>

              <div>
                <label htmlFor="student_id" className="text-sm font-medium">
                  學號
                </label>
                <input
                  id="student_id"
                  value={formData.student_id}
                  onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                  placeholder="請輸入學號（選填）"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="email" className="text-sm font-medium">
                  Email <span className="text-gray-400">(選填)</span>
                </label>
                <input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className={`w-full mt-1 px-3 py-2 border rounded-md ${errors.email ? 'border-red-500' : ''}`}
                  placeholder="student@example.com (選填)"
                />
                {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email}</p>}
              </div>

              <div>
                <label htmlFor="phone" className="text-sm font-medium">
                  電話
                </label>
                <input
                  id="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                  placeholder="0912345678"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="birthdate" className="text-sm font-medium">
                  生日 <span className="text-red-500">*</span>
                </label>
                <input
                  id="birthdate"
                  type="date"
                  value={formData.birthdate}
                  onChange={(e) => setFormData({ ...formData, birthdate: e.target.value })}
                  className={`w-full mt-1 px-3 py-2 border rounded-md ${errors.birthdate ? 'border-red-500' : ''}`}
                />
                {errors.birthdate && <p className="text-xs text-red-500 mt-1">{errors.birthdate}</p>}
                {formData.birthdate && (
                  <p className="text-xs text-gray-500 mt-1">
                    預設密碼: {formData.birthdate.replace(/-/g, '')}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="classroom" className="text-sm font-medium">
                  班級
                </label>
                <select
                  id="classroom"
                  value={formData.classroom_id || ''}
                  onChange={(e) => setFormData({ ...formData, classroom_id: e.target.value ? Number(e.target.value) : undefined })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                >
                  <option value="">未分配班級</option>
                  {classrooms.map((classroom) => (
                    <option key={classroom.id} value={classroom.id}>
                      {classroom.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {dialogType === 'edit' && (
              <div>
                <label htmlFor="status" className="text-sm font-medium">
                  狀態
                </label>
                <select
                  id="status"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                >
                  <option value="active">活躍</option>
                  <option value="inactive">未活躍</option>
                  <option value="suspended">已停權</option>
                </select>
              </div>
            )}

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
  if (dialogType === 'delete' && student) {
    return (
      <Dialog open={true} onOpenChange={() => onClose()}>
        <DialogContent className="bg-white" style={{ backgroundColor: 'white' }}>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <span>確認刪除學生</span>
            </DialogTitle>
            <DialogDescription>
              確定要刪除學生「{student.name}」嗎？此操作無法復原。
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">學生資料：</p>
              <p className="font-medium">{student.name}</p>
              <p className="text-sm text-gray-500">{student.email}</p>
              {student.classroom_name && (
                <p className="text-sm text-gray-500">班級：{student.classroom_name}</p>
              )}
            </div>

            {errors.submit && (
              <p className="text-sm text-red-500 mt-4">{errors.submit}</p>
            )}
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
              <Trash2 className="h-4 w-4 mr-2" />
              {loading ? '刪除中...' : '確認刪除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return null;
}
