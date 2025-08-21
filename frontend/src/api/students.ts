import type { Student } from '@/types'

export const studentsApi = {
  getStudents: async (): Promise<Student[]> => {
    // Mock implementation
    return []
  },

  createStudent: async (student: Omit<Student, 'id'>): Promise<Student> => {
    // Mock implementation
    return { ...student, id: 1 } as Student
  },

  updateStudent: async (_id: number, student: Partial<Student>): Promise<Student> => {
    // Mock implementation
    return { ...student, id: _id } as Student
  },

  deleteStudent: async (_id: number): Promise<void> => {
    // Mock implementation
  },

  resetPassword: async (_id: number) => {
    // Mock implementation
    return {
      message: '密碼已重置',
      default_password: '20100101',
    }
  },

  bulkAssignToClass: async (studentIds: number[], classId: number) => {
    // Mock implementation
    console.log(`Assigning ${studentIds.length} students to class ${classId}`)
    return {
      success: true,
      assigned_count: studentIds.length,
      class_id: classId,
    }
  },
}