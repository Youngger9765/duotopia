import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Lock, CheckCircle, XCircle, Eye, EyeOff } from "lucide-react";
import { apiClient } from "../lib/api";

export default function TeacherResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [tokenValid, setTokenValid] = useState(false);
  const [userInfo, setUserInfo] = useState<{
    email: string;
    name: string;
  } | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [formData, setFormData] = useState({
    newPassword: "",
    confirmPassword: "",
  });

  const token = searchParams.get("token");

  useEffect(() => {
    if (!token) {
      setError("無效的重設連結");
      setIsVerifying(false);
      return;
    }

    // 驗證 token 是否有效
    const verifyToken = async () => {
      try {
        const response = await apiClient.get(
          `/api/auth/teacher/verify-reset-token?token=${token}`,
        );
        if (
          response &&
          typeof response === "object" &&
          "valid" in response &&
          response.valid
        ) {
          setTokenValid(true);
          if ("email" in response && "name" in response) {
            setUserInfo({
              email: response.email as string,
              name: response.name as string,
            });
          }
        }
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message || "無效或過期的重設連結");
        } else {
          setError("無效或過期的重設連結");
        }
        setTokenValid(false);
      } finally {
        setIsVerifying(false);
      }
    };

    verifyToken();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // 驗證密碼
    if (formData.newPassword !== formData.confirmPassword) {
      setError("密碼不一致");
      return;
    }

    if (formData.newPassword.length < 6) {
      setError("密碼至少需要6個字元");
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiClient.post(
        "/api/auth/teacher/reset-password",
        {
          token,
          new_password: formData.newPassword,
        },
      );

      if (
        response &&
        typeof response === "object" &&
        "success" in response &&
        response.success
      ) {
        setSuccess(true);
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message || "重設失敗，請稍後再試");
      } else {
        setError("重設失敗，請稍後再試");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // 載入中
  if (isVerifying) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
            <p className="text-gray-600">驗證連結中...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 成功重設密碼
  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl">密碼重設成功！</CardTitle>
              <CardDescription>您的密碼已成功更新</CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <Alert className="bg-green-50 border-green-200">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  您現在可以使用新密碼登入系統
                </AlertDescription>
              </Alert>

              <Button
                className="w-full"
                onClick={() => navigate("/teacher/login")}
              >
                前往登入
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Token 無效
  if (!tokenValid) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <XCircle className="h-8 w-8 text-red-600" />
              </div>
              <CardTitle className="text-2xl">連結無效或已過期</CardTitle>
              <CardDescription>此密碼重設連結無效或已過期</CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <Alert className="bg-red-50 border-red-200">
                <XCircle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  {error || "密碼重設連結已過期或無效，請重新申請"}
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <Button
                  className="w-full"
                  onClick={() => navigate("/teacher/forgot-password")}
                >
                  重新申請密碼重設
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => navigate("/teacher/login")}
                >
                  返回登入頁面
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // 重設密碼表單
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Duotopia</h1>
          <p className="text-gray-600">重設您的密碼</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>設定新密碼</CardTitle>
            <CardDescription>
              {userInfo && (
                <div className="mt-2">
                  <p>帳號：{userInfo.email}</p>
                  <p>姓名：{userInfo.name}</p>
                </div>
              )}
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="newPassword">新密碼</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="newPassword"
                    type={showPassword ? "text" : "password"}
                    placeholder="請輸入新密碼"
                    value={formData.newPassword}
                    onChange={(e) =>
                      setFormData({ ...formData, newPassword: e.target.value })
                    }
                    className="pl-10 pr-10"
                    required
                    disabled={isLoading}
                    minLength={6}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">確認新密碼</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="請再次輸入新密碼"
                    value={formData.confirmPassword}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        confirmPassword: e.target.value,
                      })
                    }
                    className="pl-10 pr-10"
                    required
                    disabled={isLoading}
                    minLength={6}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="text-sm text-gray-500">
                • 密碼至少需要 6 個字元
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    重設中...
                  </>
                ) : (
                  "重設密碼"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
