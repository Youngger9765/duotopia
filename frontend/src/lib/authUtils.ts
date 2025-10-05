import { useTeacherAuthStore } from '@/stores/teacherAuthStore';
import { useStudentAuthStore } from '@/stores/studentAuthStore';

/**
 * 統一的登出函數
 * 清除所有認證狀態 (teacher + student)
 */
export function clearAllAuth() {
  useTeacherAuthStore.getState().logout();
  useStudentAuthStore.getState().logout();

  // 清除所有可能殘留的舊 localStorage keys
  const keysToRemove = [
    'token',
    'access_token',
    'user',
    'userInfo',
    'role',
    'username',
    'userType',
    'auth-storage',
    'selectedPlan',
  ];

  keysToRemove.forEach(key => localStorage.removeItem(key));
}

/**
 * Teacher 登出
 */
export function logoutTeacher() {
  useTeacherAuthStore.getState().logout();
}

/**
 * Student 登出
 */
export function logoutStudent() {
  useStudentAuthStore.getState().logout();
}
