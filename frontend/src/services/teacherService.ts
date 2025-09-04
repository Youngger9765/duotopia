import api from './api';

export const teacherService = {
  async getDashboard() {
    const response = await api.get('/api/teacher/dashboard');
    return response.data;
  },

  async getClassrooms() {
    const response = await api.get('/api/teacher/classrooms');
    return response.data;
  },

  async getStudents(classroomId?: number) {
    const params = classroomId ? `?classroom_id=${classroomId}` : '';
    const response = await api.get(`/api/teacher/students${params}`);
    return response.data;
  },

  async getPrograms(classroomId?: number) {
    const params = classroomId ? `?classroom_id=${classroomId}` : '';
    const response = await api.get(`/api/teacher/programs${params}`);
    return response.data;
  },

  // Public endpoints for student login flow
  async validateTeacher(email: string) {
    const response = await api.post('/api/public/validate-teacher', { email });
    return response.data;
  },

  async getPublicClassrooms(teacherEmail: string) {
    const response = await api.get(`/api/public/teacher-classrooms?email=${teacherEmail}`);
    return response.data;
  },

  async getClassroomStudents(classroomId: number) {
    const response = await api.get(`/api/public/classroom-students/${classroomId}`);
    return response.data;
  }
};
