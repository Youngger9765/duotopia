import { describe, it, expect, beforeEach } from 'vitest';
import { useTeacherAuthStore } from '../../stores/teacherAuthStore';
import { useStudentAuthStore } from '../../stores/studentAuthStore';

describe('認證系統一致性測試 - 🔴 RED Phase', () => {
  beforeEach(() => {
    // Reset stores first
    useTeacherAuthStore.getState().logout();
    useStudentAuthStore.getState().logout();
    // Then clear localStorage to remove persisted logout state
    localStorage.clear();
  });

  describe('Token 儲存一致性', () => {
    it('🟢 只應該使用 teacher-auth-storage 和 student-auth-storage', () => {
      // 檢查所有可能的 token keys
      const tokenKeys = [
        'token',
        'access_token',
        'auth-storage',
        'teacher-auth-storage',
        'student-auth-storage'
      ];

      const existingKeys = tokenKeys.filter(key => localStorage.getItem(key));

      // 初始狀態應該沒有任何 keys
      expect(existingKeys.length).toBe(0);

      // 登入後應該只有正確的 keys
      useTeacherAuthStore.getState().login('test-token', {
        id: 1,
        name: 'Teacher',
        email: 'test@example.com'
      });

      const keysAfterLogin = tokenKeys.filter(key => localStorage.getItem(key));

      // 只有 teacher-auth-storage
      expect(keysAfterLogin.length).toBe(1);
      expect(keysAfterLogin[0]).toBe('teacher-auth-storage');

      // 而且只能是 teacher-auth-storage
      const validKeys = keysAfterLogin.filter(key =>
        key === 'teacher-auth-storage' || key === 'student-auth-storage'
      );
      expect(validKeys.length).toBe(keysAfterLogin.length);
    });

    it('🔴 Teacher 登入應該只儲存在 teacher-auth-storage', () => {
      const { login } = useTeacherAuthStore.getState();
      login('teacher-token', {
        id: 1,
        name: 'Teacher',
        email: 'teacher@example.com'
      });

      // 檢查只有 teacher-auth-storage 存在
      expect(localStorage.getItem('teacher-auth-storage')).toBeDefined();
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('auth-storage')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
      expect(localStorage.getItem('userInfo')).toBeNull();
    });

    it('🔴 Student 登入應該只儲存在 student-auth-storage', () => {
      const { login } = useStudentAuthStore.getState();
      login('student-token', {
        id: 1,
        name: 'Student',
        email: 'student@example.com',
        student_number: 'S001',
        classroom_id: 1
      });

      // 檢查只有 student-auth-storage 存在
      expect(localStorage.getItem('student-auth-storage')).toBeDefined();
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('auth-storage')).toBeNull();
    });
  });

  describe('用戶資料一致性', () => {
    it('🔴 不應該有多個用戶資料 keys', () => {
      const { login } = useTeacherAuthStore.getState();
      login('test-token', {
        id: 1,
        name: 'Teacher',
        email: 'test@example.com'
      });

      // 檢查不應該存在的用戶資料 keys
      const userKeys = ['user', 'userInfo', 'username', 'role', 'userType'];
      const existingUserKeys = userKeys.filter(key => localStorage.getItem(key));

      // 應該沒有任何舊的用戶資料 keys
      expect(existingUserKeys.length).toBe(0);
    });
  });

  describe('跨角色登入測試', () => {
    it('🔴 Teacher 和 Student 可以同時登入（不同 storage）', () => {
      useTeacherAuthStore.getState().login('teacher-token', {
        id: 1,
        name: 'Teacher',
        email: 'teacher@example.com'
      });

      useStudentAuthStore.getState().login('student-token', {
        id: 1,
        name: 'Student',
        email: 'student@example.com',
        student_number: 'S001',
        classroom_id: 1
      });

      // 兩個 store 都應該有資料
      expect(useTeacherAuthStore.getState().isAuthenticated).toBe(true);
      expect(useStudentAuthStore.getState().isAuthenticated).toBe(true);

      // 兩個 localStorage keys 都應該存在
      expect(localStorage.getItem('teacher-auth-storage')).toBeDefined();
      expect(localStorage.getItem('student-auth-storage')).toBeDefined();
    });

    it('🔴 Teacher logout 不應該影響 Student', () => {
      useTeacherAuthStore.getState().login('teacher-token', {
        id: 1,
        name: 'Teacher',
        email: 'teacher@example.com'
      });

      useStudentAuthStore.getState().login('student-token', {
        id: 1,
        name: 'Student',
        email: 'student@example.com',
        student_number: 'S001',
        classroom_id: 1
      });

      // Teacher logout
      useTeacherAuthStore.getState().logout();

      // Teacher 應該登出
      expect(useTeacherAuthStore.getState().isAuthenticated).toBe(false);

      // Student 不受影響
      expect(useStudentAuthStore.getState().isAuthenticated).toBe(true);
      expect(useStudentAuthStore.getState().token).toBe('student-token');
    });
  });
});
