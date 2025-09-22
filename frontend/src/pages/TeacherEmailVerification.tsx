import { useEffect, useState, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';

export function TeacherEmailVerification() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const isVerifyingRef = useRef(false);

  useEffect(() => {
    const verifyEmail = async () => {
      // 防止重複執行 - 使用 ref 立即生效
      if (isVerifyingRef.current) return;
      isVerifyingRef.current = true;

      const token = searchParams.get('token');

      if (!token) {
        // 沒有 token，重導向到提示頁面
        navigate('/teacher/verify-email-prompt');
        return;
      }

      try {
        interface VerifyResponse {
          message?: string;
          status?: string;
        }
        const response = await apiClient.get<VerifyResponse>(`/api/auth/verify-teacher?token=${token}`);

        console.log('驗證 API 回應:', response);

        // 只要 API 回應成功就表示驗證成功，不需要 access_token
        if (response.message || response.status === 'success') {
          setStatus('success');
          setMessage(response.message || 'Email 驗證成功！您的 30 天免費試用已開始。');

          console.log('驗證成功，用戶需要自行登入');
          // 不儲存任何 token，讓用戶自己登入
        } else {
          throw new Error('驗證失敗');
        }
      } catch (error) {
        setStatus('error');
        // Parse error message from apiClient
        let errorMessage = '驗證失敗，請確認連結是否正確或已過期';
        if (error instanceof Error) {
          try {
            const errorData = JSON.parse(error.message);
            errorMessage = errorData.detail || errorMessage;
          } catch {
            errorMessage = error.message || errorMessage;
          }
        }
        setMessage(errorMessage);
      }
    };

    verifyEmail();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Duotopia</h1>
          <p className="text-gray-600">AI 驅動的英語學習平台</p>
        </div>

        <Card>
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4">
              {status === 'loading' && (
                <div className="bg-blue-100">
                  <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
                </div>
              )}
              {status === 'success' && (
                <div className="bg-green-100">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
              )}
              {status === 'error' && (
                <div className="bg-red-100">
                  <XCircle className="h-8 w-8 text-red-600" />
                </div>
              )}
            </div>
            <CardTitle className="text-2xl">
              {status === 'loading' && '正在驗證...'}
              {status === 'success' && '驗證成功！'}
              {status === 'error' && '驗證失敗'}
            </CardTitle>
            <CardDescription>
              {status === 'loading' && '請稍候，正在驗證您的 Email'}
              {status === 'success' && '您的帳號已啟用'}
              {status === 'error' && '無法完成驗證'}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <Alert className={
              status === 'success' ? 'bg-green-50 border-green-200' :
              status === 'error' ? 'bg-red-50 border-red-200' :
              'bg-blue-50 border-blue-200'
            }>
              <AlertDescription className={
                status === 'success' ? 'text-green-800' :
                status === 'error' ? 'text-red-800' :
                'text-blue-800'
              }>
                {message}
              </AlertDescription>
            </Alert>

            {status === 'success' && (
              <div className="space-y-4">
                <div className="text-center text-gray-600">
                  <p>您的帳號已成功啟用！</p>
                  <p className="text-sm mt-2">30天免費試用已開始</p>
                </div>
                <div className="flex justify-center">
                  <button
                    onClick={() => navigate('/teacher/login')}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    前往登入
                  </button>
                </div>
              </div>
            )}

            {status === 'error' && (
              <div className="flex justify-center">
                <button
                  onClick={() => navigate('/teacher/login')}
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  返回登入頁面
                </button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
