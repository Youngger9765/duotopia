import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { studentsApi } from '@/api/students'
import { useToast } from '@/components/ui/use-toast'
import type { Student } from '@/types'

interface UseStudentsOptions {
  search?: string
  classId?: number
  passwordStatus?: 'default' | 'custom'
  page?: number
  pageSize?: number
}

export const useStudents = (options: UseStudentsOptions = {}) => {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: students, isLoading, isError, error } = useQuery({
    queryKey: ['students'],
    queryFn: studentsApi.getStudents,
  })

  const createStudentMutation = useMutation({
    mutationFn: studentsApi.createStudent,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['students'] })
      toast({
        title: '新增成功',
        description: `學生 ${data.name} 已新增`,
      })
    },
    onError: () => {
      toast({
        title: '新增失敗',
        description: '無法新增學生，請稍後再試',
        variant: 'destructive',
      })
    },
  })

  const updateStudentMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Student> }) =>
      studentsApi.updateStudent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] })
      toast({
        title: '更新成功',
        description: '學生資料已更新',
      })
    },
  })

  const deleteStudentMutation = useMutation({
    mutationFn: studentsApi.deleteStudent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['students'] })
      toast({
        title: '刪除成功',
        description: '學生已刪除',
      })
    },
  })

  const resetPasswordMutation = useMutation({
    mutationFn: studentsApi.resetPassword,
    onSuccess: (data) => {
      toast({
        title: '密碼重置成功',
        description: `密碼已重置為生日：${data.default_password}`,
      })
    },
  })

  const bulkAssignToClassMutation = useMutation({
    mutationFn: ({ studentIds, classId }: { studentIds: number[]; classId: number }) =>
      studentsApi.bulkAssignToClass(studentIds, classId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['students'] })
      toast({
        title: '分配成功',
        description: `已將 ${data.assigned_count} 位學生分配到班級`,
      })
    },
    onError: () => {
      toast({
        title: '分配失敗',
        description: '班級已滿或發生錯誤',
        variant: 'destructive',
      })
    },
  })

  // Filter students based on options
  const filteredStudents = students?.filter((student) => {
    if (options.search && !student.name.includes(options.search)) {
      return false
    }
    if (options.classId && student.class_id !== options.classId) {
      return false
    }
    if (options.passwordStatus && student.password_status !== options.passwordStatus) {
      return false
    }
    return true
  })

  // Paginate students
  const paginatedStudents = options.page && options.pageSize
    ? filteredStudents?.slice(
        (options.page - 1) * options.pageSize,
        options.page * options.pageSize
      )
    : filteredStudents

  const totalPages = options.pageSize && filteredStudents
    ? Math.ceil(filteredStudents.length / options.pageSize)
    : 1

  return {
    students,
    filteredStudents,
    paginatedStudents,
    totalPages,
    currentPage: options.page || 1,
    isLoading,
    isError,
    error,
    createStudent: createStudentMutation.mutateAsync,
    updateStudent: (id: number, data: Partial<Student>) =>
      updateStudentMutation.mutateAsync({ id, data }),
    deleteStudent: deleteStudentMutation.mutateAsync,
    resetPassword: resetPasswordMutation.mutateAsync,
    bulkAssignToClass: (studentIds: number[], classId: number) =>
      bulkAssignToClassMutation.mutateAsync({ studentIds, classId }),
  }
}