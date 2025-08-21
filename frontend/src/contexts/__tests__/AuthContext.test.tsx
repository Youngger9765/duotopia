/**
 * AuthContext 單元測試
 * 測試認證相關的 Context 功能
 */
import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AuthProvider, useAuth } from '../AuthContext';
import { authApi } from '@/api/auth';

// Mock API
vi.mock('@/api/auth');

// 測試用元件
const TestComponent = () => {
  const { user, isLoading, login, logout } = useAuth();
  
  const handleLogin = async () => {
    try {
      await login('test@example.com', 'password');
    } catch (error) {
      // 處理錯誤，避免未處理的 rejection
    }
  };
  
  return (
    <div>
      <div data-testid="loading">{isLoading ? 'Loading' : 'Ready'}</div>
      <div data-testid="user">{user ? user.email : 'No user'}</div>
      <button onClick={handleLogin}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    // 清除 localStorage
    localStorage.clear();
    // 重置 mock
    vi.clearAllMocks();
  });

  describe('初始化', () => {
    it('應該提供預設值', () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      expect(screen.getByTestId('loading')).toHaveTextContent('Ready');
      expect(screen.getByTestId('user')).toHaveTextContent('No user');
    });

    it('應該從 localStorage 載入已存在的 token', async () => {
      // 設置 localStorage
      const mockUser = { id: 1, email: 'cached@example.com' };
      const mockToken = 'cached-token';
      localStorage.setItem('token', mockToken);

      // Mock API 驗證
      (authApi.validateToken as vi.Mock).mockResolvedValueOnce(mockUser);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // 等待非同步驗證完成
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('cached@example.com');
      });

      expect(authApi.validateToken).toHaveBeenCalledWith(mockToken);
    });
  });

  describe('登入功能', () => {
    it('應該成功登入並儲存 token', async () => {
      const mockResponse = {
        access_token: 'new-token',
        user: { id: 1, email: 'test@example.com' },
        roles: ['teacher']
      };

      (authApi.login as vi.Mock).mockResolvedValueOnce(mockResponse);

      const user = userEvent.setup();
      
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      const loginButton = screen.getByText('Login');
      await user.click(loginButton);

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
      });

      expect(localStorage.getItem('token')).toBe('new-token');
      expect(authApi.login).toHaveBeenCalledWith('test@example.com', 'password');
    });

    it('應該處理登入錯誤', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      (authApi.login as vi.Mock).mockRejectedValueOnce(new Error('Invalid credentials'));

      const user = userEvent.setup();
      
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      const loginButton = screen.getByText('Login');
      await user.click(loginButton);

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('No user');
      });

      expect(localStorage.getItem('token')).toBeNull();
      
      consoleSpy.mockRestore();
    });
  });

  describe('登出功能', () => {
    it('應該清除使用者資料和 token', async () => {
      // 先設置已登入狀態
      const mockUser = { id: 1, email: 'test@example.com' };
      localStorage.setItem('token', 'test-token');
      
      (authApi.validateToken as vi.Mock).mockResolvedValueOnce(mockUser);

      const user = userEvent.setup();

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // 等待初始化完成
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
      });

      // 執行登出
      const logoutButton = screen.getByText('Logout');
      await user.click(logoutButton);

      expect(screen.getByTestId('user')).toHaveTextContent('No user');
      expect(localStorage.getItem('token')).toBeNull();
    });
  });

  describe('角色管理', () => {
    it('應該正確處理多重角色', async () => {
      const mockResponse = {
        access_token: 'token',
        user: { id: 1, email: 'multi@example.com' },
        roles: ['individual_teacher', 'institutional_teacher']
      };

      (authApi.login as vi.Mock).mockResolvedValueOnce(mockResponse);

      const TestRoleComponent = () => {
        const { user, roles, currentRole, switchRole, login } = useAuth();
        
        return (
          <div>
            <div data-testid="roles">{roles.join(',')}</div>
            <div data-testid="current-role">{currentRole || 'none'}</div>
            <button onClick={() => login('multi@example.com', 'password')}>
              Login
            </button>
            <button onClick={() => switchRole('institutional_teacher')}>
              Switch Role
            </button>
          </div>
        );
      };

      const user = userEvent.setup();

      render(
        <AuthProvider>
          <TestRoleComponent />
        </AuthProvider>
      );

      // 先登入
      const loginButton = screen.getByText('Login');
      await user.click(loginButton);

      await waitFor(() => {
        expect(screen.getByTestId('roles')).toHaveTextContent('individual_teacher,institutional_teacher');
      });

      // 切換角色
      const switchButton = screen.getByText('Switch Role');
      await user.click(switchButton);

      expect(screen.getByTestId('current-role')).toHaveTextContent('institutional_teacher');
    });
  });
});

describe('useAuth Hook', () => {
  it('應該在 AuthProvider 外使用時拋出錯誤', () => {
    const TestErrorComponent = () => {
      useAuth(); // 這應該會拋出錯誤
      return <div>Should not render</div>;
    };

    // 捕獲錯誤避免測試失敗
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestErrorComponent />);
    }).toThrow('useAuth must be used within an AuthProvider');

    spy.mockRestore();
  });
});