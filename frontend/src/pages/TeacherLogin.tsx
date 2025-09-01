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

    try {
      await apiClient.teacherLogin(formData);
      navigate('/teacher/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : '登入失敗，請檢查帳號密碼');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setIsLoading(true);
    setError('');

    try {
      await apiClient.teacherLogin({
        email: 'demo@duotopia.com',
        password: 'demo123',
      });
      navigate('/teacher/dashboard');
    } catch {
      setError('Demo 帳號登入失敗');
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
            </form>

            {/* Demo Login Button */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">或</span>
              </div>
            </div>

            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={handleDemoLogin}
              disabled={isLoading}
            >
              <Zap className="mr-2 h-4 w-4" />
              Demo 教師快速登入
            </Button>
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

        <div className="mt-4 text-center text-xs text-gray-500">
          Demo 帳號：demo@duotopia.com / demo123
        </div>
      </div>
    </div>
  );
}
