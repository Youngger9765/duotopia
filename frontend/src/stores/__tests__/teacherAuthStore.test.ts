import { describe, it, expect, beforeEach } from 'vitest';
import { useTeacherAuthStore } from '../teacherAuthStore';

describe('TeacherAuthStore - 🔴 RED Phase', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Store 存在性測試', () => {
    it('🔴 應該存在 useTeacherAuthStore', () => {
      // 這會失敗，因為目前沒有這個 store
      expect(useTeacherAuthStore).toBeDefined();
      expect(typeof useTeacherAuthStore).toBe('function');
    });

    it('🔴 Store 應該有正確的初始狀態', () => {
      const state = useTeacherAuthStore.getState();

      expect(state).toHaveProperty('token');
      expect(state).toHaveProperty('user');
      expect(state).toHaveProperty('isAuthenticated');
      expect(state).toHaveProperty('login');
      expect(state).toHaveProperty('logout');

      expect(state.token).toBe(null);
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('Login 功能測試', () => {
    it('🔴 應該能正確登入並儲存 token', () => {
      const mockToken = 'mock-jwt-token-12345';
      const mockUser = {
        id: 1,
        name: 'Test Teacher',
        email: 'teacher@test.com'
      };

      const { login } = useTeacherAuthStore.getState();
      login(mockToken, mockUser);

      const state = useTeacherAuthStore.getState();
      expect(state.token).toBe(mockToken);
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
    });

    it('🔴 應該將資料持久化到 localStorage (teacher-auth-storage)', () => {
      const mockToken = 'test-token-123';
      const mockUser = {
        id: 1,
        name: 'Teacher Test',
        email: 'test@example.com'
      };

      const { login } = useTeacherAuthStore.getState();
      login(mockToken, mockUser);

      const stored = localStorage.getItem('teacher-auth-storage');
      expect(stored).toBeDefined();
      expect(stored).not.toBeNull();

      const parsed = JSON.parse(stored!);
      expect(parsed.state.token).toBe(mockToken);
      expect(parsed.state.user).toEqual(mockUser);
      expect(parsed.state.isAuthenticated).toBe(true);
    });

    it('🔴 不應該儲存到其他 localStorage keys', () => {
      const { login } = useTeacherAuthStore.getState();
      login('test-token', { id: 1, name: 'Teacher', email: 'test@example.com' });

      // 檢查不應該存在的舊 keys
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('auth-storage')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
      expect(localStorage.getItem('userInfo')).toBeNull();
    });
  });

  describe('Logout 功能測試', () => {
    it('🔴 應該清除所有認證資料', () => {
      const { login, logout } = useTeacherAuthStore.getState();

      // 先登入
      login('test-token', { id: 1, name: 'Teacher', email: 'test@example.com' });

      // 確認已登入
      expect(useTeacherAuthStore.getState().isAuthenticated).toBe(true);

      // 登出
      logout();

      const state = useTeacherAuthStore.getState();
      expect(state.token).toBe(null);
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(false);
    });

    it('🔴 Logout 應該清除 localStorage', () => {
      const { login, logout } = useTeacherAuthStore.getState();

      login('test-token', { id: 1, name: 'Teacher', email: 'test@example.com' });
      expect(localStorage.getItem('teacher-auth-storage')).toBeDefined();

      logout();

      const stored = localStorage.getItem('teacher-auth-storage');
      if (stored) {
        const parsed = JSON.parse(stored);
        expect(parsed.state.token).toBe(null);
        expect(parsed.state.user).toBe(null);
      }
    });
  });

  describe('UpdateUser 功能測試', () => {
    it('🔴 應該能更新用戶資料', () => {
      const { login, updateUser } = useTeacherAuthStore.getState();

      // 先登入
      login('test-token', { id: 1, name: 'Teacher', email: 'old@example.com' });

      // 更新資料
      updateUser({ email: 'new@example.com', name: 'Updated Teacher' });

      const state = useTeacherAuthStore.getState();
      expect(state.user?.email).toBe('new@example.com');
      expect(state.user?.name).toBe('Updated Teacher');
      expect(state.user?.id).toBe(1); // ID 不變
    });
  });
});
