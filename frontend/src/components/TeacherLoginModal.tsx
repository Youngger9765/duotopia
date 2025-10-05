import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Mail, Lock, AlertCircle } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';
import SubscriptionProgressBanner from './SubscriptionProgressBanner';

interface SelectedPlan {
  id: string;
  name: string;
  monthlyPrice: number;
}

interface User {
  id: number | string;
  email: string;
  name?: string;
  role?: string;
  is_demo?: boolean;
}

interface TeacherLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: User) => void;
  selectedPlan?: SelectedPlan;
}

export default function TeacherLoginModal({
  isOpen,
  onClose,
  onLoginSuccess,
  selectedPlan
}: TeacherLoginModalProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await apiClient.teacherLogin({ email, password });

      // Store auth data
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('role', 'teacher');
      localStorage.setItem('username', response.user?.name || email);

      // Store teacher auth in Zustand format
      const teacherAuthData = {
        state: {
          isAuthenticated: true,
          user: response.user,
          token: response.access_token
        },
        version: 0
      };
      localStorage.setItem('teacher-auth-storage', JSON.stringify(teacherAuthData));

      // If there was a selected plan, store it for auto-open after login
      if (selectedPlan) {
        localStorage.setItem('selectedPlan', JSON.stringify({
          id: selectedPlan.id,
          name: selectedPlan.name,
          price: selectedPlan.monthlyPrice
        }));
      }

      toast.success('登入成功！');
      onLoginSuccess(response.user);
      onClose();
    } catch (err: unknown) {
      const error = err as { response?: { status?: number; data?: { detail?: string } }; message?: string };
      console.error('Login error:', err);
      if (error.response?.status === 401) {
        setError('電子郵件或密碼錯誤，請檢查您的登入資訊');
      } else if (error.response?.status === 500) {
        setError('伺服器錯誤，請稍後再試');
      } else if (error.message?.includes('Network')) {
        setError('網路連線錯誤，請檢查網路連線');
      } else {
        setError(`登入失敗：${error.response?.data?.detail || error.message || '請稍後再試'}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (demoEmail: string, demoPassword: string) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setError('');

    // Auto-submit with demo credentials
    setTimeout(() => {
      const form = document.getElementById('login-form') as HTMLFormElement;
      if (form) {
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
      }
    }, 100);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        {selectedPlan && (
          <div className="-m-6 mb-4">
            <SubscriptionProgressBanner
              currentStep="login"
              selectedPlan={selectedPlan.name}
            />
          </div>
        )}

        <DialogHeader>
          <DialogTitle>教師登入</DialogTitle>
          <DialogDescription>
            {selectedPlan ? (
              <span className="text-blue-600">
                登入後即可訂閱 {selectedPlan.name} 方案
              </span>
            ) : (
              '請輸入您的教師帳號資訊'
            )}
          </DialogDescription>
        </DialogHeader>

        <form id="login-form" onSubmit={handleSubmit} className="space-y-4 mt-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">電子郵件</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                id="email"
                type="email"
                placeholder="teacher@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-10"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">密碼</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                登入中...
              </>
            ) : (
              '登入'
            )}
          </Button>
        </form>

        <div className="mt-4 pt-4 border-t">
          <p className="text-sm text-gray-600 mb-3 text-center">試用帳號（密碼: demo123）</p>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              className="flex-1"
              onClick={() => handleDemoLogin('demo@duotopia.com', 'demo123')}
              disabled={isLoading}
            >
              Demo (有訂閱)
            </Button>
            <Button
              type="button"
              variant="outline"
              className="flex-1"
              onClick={() => handleDemoLogin('expired@duotopia.com', 'demo123')}
              disabled={isLoading}
            >
              Expired (已過期)
            </Button>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t text-center">
          <p className="text-sm text-gray-600">
            還沒有帳號？
            <a
              href="/teacher/register"
              className="text-blue-600 hover:text-blue-700 ml-1"
              onClick={(e) => {
                e.preventDefault();
                window.location.href = '/teacher/register';
              }}
            >
              立即註冊
            </a>
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
