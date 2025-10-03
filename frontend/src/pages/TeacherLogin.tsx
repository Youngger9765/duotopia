import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, User, Lock, Zap, Home } from 'lucide-react';
import { apiClient } from '../lib/api';

export default function TeacherLogin() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    console.log('🔑 [DEBUG] 教師登入開始');
    console.log('🔑 [DEBUG] 登入資料:', { email: formData.email, password: '***' });

    try {
      const result = await apiClient.teacherLogin(formData);
      console.log('🔑 [DEBUG] 登入成功，結果:', result);
      console.log('🔑 [DEBUG] localStorage 檢查:', {
        auth_storage: localStorage.getItem('auth-storage'),
        keys: Object.keys(localStorage)
      });

      navigate('/teacher/dashboard');
    } catch (err) {
      console.error('🔑 [ERROR] 登入失敗:', err);
      setError(err instanceof Error ? err.message : '登入失敗，請檢查帳號密碼');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = async (email: string) => {
    setIsLoading(true);
    setError('');

    console.log('🔑 [DEBUG] 快速登入開始');
    console.log('🔑 [DEBUG] 快速登入資料:', { email, password: 'demo123' });

    try {
      const result = await apiClient.teacherLogin({
        email,
        password: 'demo123',
      });
      console.log('🔑 [DEBUG] 快速登入成功，結果:', result);
      console.log('🔑 [DEBUG] localStorage 檢查:', {
        auth_storage: localStorage.getItem('auth-storage'),
        keys: Object.keys(localStorage)
      });

      navigate('/teacher/dashboard');
    } catch (err) {
      console.error('🔑 [ERROR] 快速登入失敗:', err);
      setError(`${email} 帳號登入失敗`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      {/* Home link */}
      <div className="absolute top-4 left-4">
        <Link to="/">
          <Button variant="ghost" className="flex items-center gap-2 text-gray-600 hover:text-gray-900">
            <Home className="h-4 w-4" />
            <span>返回首頁</span>
          </Button>
        </Link>
      </div>

      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Duotopia</h1>
          <p className="text-gray-600">AI 驅動的英語學習平台</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>教師登入</CardTitle>
            <CardDescription>
              使用您的 Email 帳號登入教師後台
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="teacher@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
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
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="pl-10"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

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

              <div className="text-center">
                <Link
                  to="/teacher/forgot-password"
                  className="text-sm text-blue-600 hover:underline"
                >
                  忘記密碼？
                </Link>
              </div>
            </form>

            {/* Quick Login Buttons */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">測試帳號快速登入</span>
              </div>
            </div>

            <div className="space-y-2">
              <Button
                type="button"
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleQuickLogin('demo@duotopia.com')}
                disabled={isLoading}
              >
                <Zap className="mr-2 h-4 w-4 text-green-600" />
                <div className="flex-1 text-left">
                  <div className="font-medium">Demo 教師（已充值300天）</div>
                  <div className="text-xs text-gray-500">demo@duotopia.com</div>
                </div>
              </Button>

              <Button
                type="button"
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleQuickLogin('trial@duotopia.com')}
                disabled={isLoading}
              >
                <Zap className="mr-2 h-4 w-4 text-blue-600" />
                <div className="flex-1 text-left">
                  <div className="font-medium text-xs sm:text-sm truncate">試用教師（30天試用期）</div>
                  <div className="text-xs text-gray-500">trial@duotopia.com</div>
                </div>
              </Button>

              <Button
                type="button"
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleQuickLogin('expired@duotopia.com')}
                disabled={isLoading}
              >
                <Zap className="mr-2 h-4 w-4 text-red-600" />
                <div className="flex-1 text-left">
                  <div className="font-medium">過期教師（未訂閱）</div>
                  <div className="text-xs text-gray-500">expired@duotopia.com</div>
                </div>
              </Button>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-2">
            <div className="text-sm text-center text-gray-600">
              還沒有帳號？
              <Link to="/teacher/register" className="text-blue-600 hover:underline ml-1">
                立即註冊
              </Link>
            </div>
            <div className="text-sm text-center text-gray-600">
              <Link to="/student/login" className="text-blue-600 hover:underline">
                學生登入入口
              </Link>
            </div>
          </CardFooter>
        </Card>

        <div className="mt-4 p-3 bg-blue-50 rounded-lg text-xs text-gray-600">
          <div className="font-semibold mb-1">🔐 測試帳號密碼均為：demo123</div>
          <div className="space-y-1">
            <div>✅ demo@duotopia.com - 已充值300天</div>
            <div>🎁 trial@duotopia.com - 30天試用期</div>
            <div>❌ expired@duotopia.com - 未訂閱/已過期</div>
          </div>
        </div>
      </div>
    </div>
  );
}
