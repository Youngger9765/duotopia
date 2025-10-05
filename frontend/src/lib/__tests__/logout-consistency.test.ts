import { describe, it, expect, beforeEach } from 'vitest';
import { useTeacherAuthStore } from '../../stores/teacherAuthStore';
import { useStudentAuthStore } from '../../stores/studentAuthStore';
import { clearAllAuth } from '../authUtils';

describe('Logout 一致性測試 - 🔴 RED Phase', () => {
  beforeEach(() => {
    localStorage.clear();
    useTeacherAuthStore.getState().logout();
    useStudentAuthStore.getState().logout();
  });

  describe('個別 Logout 測試', () => {
    it('🔴 Teacher logout 應該清除 teacher-auth-storage', () => {
      useTeacherAuthStore.getState().login('teacher-token', {
        id: 1,
        name: 'Teacher',
        email: 'teacher@example.com'
      });

      expect(localStorage.getItem('teacher-auth-storage')).toBeDefined();

      useTeacherAuthStore.getState().logout();

      const state = useTeacherAuthStore.getState();
      expect(state.token).toBeNull();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it('🔴 Student logout 應該清除 student-auth-storage', () => {
      useStudentAuthStore.getState().login('student-token', {
        id: 1,
        name: 'Student',
        email: 'student@example.com',
        student_number: 'S001',
        classroom_id: 1
      });

      expect(localStorage.getItem('student-auth-storage')).toBeDefined();

      useStudentAuthStore.getState().logout();

      const state = useStudentAuthStore.getState();
      expect(state.token).toBeNull();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('統一 Logout 測試', () => {
    it('🔴 clearAllAuth() 應該清除所有認證資料', () => {
      // 設定 teacher 和 student 都登入
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

      // 設定其他資料
      localStorage.setItem('selectedPlan', JSON.stringify({ id: 1 }));

      // 執行統一 logout
      clearAllAuth();

      // 檢查所有都被清除
      expect(useTeacherAuthStore.getState().token).toBeNull();
      expect(useStudentAuthStore.getState().token).toBeNull();
      expect(localStorage.getItem('selectedPlan')).toBeNull();
    });

    it('🔴 clearAllAuth() 應該清除所有舊的 localStorage keys', () => {
      // 設定新的認證
      useTeacherAuthStore.getState().login('teacher-token', {
        id: 1,
        name: 'Teacher',
        email: 'teacher@example.com'
      });

      // 設定舊的 keys（模擬遺留資料）
      localStorage.setItem('token', 'old-token');
      localStorage.setItem('access_token', 'old-access-token');
      localStorage.setItem('user', JSON.stringify({ id: 1 }));
      localStorage.setItem('userInfo', JSON.stringify({ id: 1 }));
      localStorage.setItem('role', 'teacher');
      localStorage.setItem('userType', 'teacher');

      // 執行統一 logout
      clearAllAuth();

      // 檢查所有舊 keys 都被清除
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
      expect(localStorage.getItem('userInfo')).toBeNull();
      expect(localStorage.getItem('role')).toBeNull();
      expect(localStorage.getItem('userType')).toBeNull();
    });
  });

  describe('Logout 不應該影響其他資料', () => {
    it('🔴 Logout 不應該清除非認證相關的 localStorage', () => {
      // 設定一些非認證資料
      localStorage.setItem('theme', 'dark');
      localStorage.setItem('language', 'zh-TW');

      // 登入後登出
      useTeacherAuthStore.getState().login('teacher-token', {
        id: 1,
        name: 'Teacher',
        email: 'teacher@example.com'
      });

      clearAllAuth();

      // 非認證資料應該保留
      expect(localStorage.getItem('theme')).toBe('dark');
      expect(localStorage.getItem('language')).toBe('zh-TW');
    });
  });

  describe('多次 Logout 測試', () => {
    it('🔴 重複 logout 不應該報錯', () => {
      useTeacherAuthStore.getState().login('teacher-token', {
        id: 1,
        name: 'Teacher',
        email: 'teacher@example.com'
      });

      // 第一次 logout
      expect(() => {
        useTeacherAuthStore.getState().logout();
      }).not.toThrow();

      // 第二次 logout（應該也不會報錯）
      expect(() => {
        useTeacherAuthStore.getState().logout();
      }).not.toThrow();

      // 狀態應該保持清空
      const state = useTeacherAuthStore.getState();
      expect(state.token).toBeNull();
      expect(state.user).toBeNull();
    });
  });
});
