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
import {
  Loader2,
  Lock,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  Building2,
} from "lucide-react";
import { apiClient } from "../lib/api";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useTranslation } from "react-i18next";

export default function TeacherSetupPassword() {
  const { t } = useTranslation();
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
    organization_name?: string;
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
      setError("連結無效");
      setIsVerifying(false);
      return;
    }

    // 驗證 token 是否有效（重用密碼重設的驗證 endpoint）
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
              organization_name:
                "organization_name" in response
                  ? (response.organization_name as string | undefined)
                  : undefined,
            });
          }
        }
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message || "連結已過期或無效");
        } else {
          setError("連結已過期或無效");
        }
        setTokenValid(false);
      } finally {
        setIsVerifying(false);
      }
    };

    verifyToken();
  }, [token, t]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // 驗證密碼
    if (formData.newPassword !== formData.confirmPassword) {
      setError("密碼確認不符");
      return;
    }

    if (formData.newPassword.length < 6) {
      setError("密碼長度至少需要 6 個字元");
      return;
    }

    setIsLoading(true);

    try {
      // 重用密碼重設的 endpoint（Token 機制相同）
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
        setError(err.message || "密碼設定失敗");
      } else {
        setError("密碼設定失敗");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // 載入中
  if (isVerifying) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4">
        {/* Language Switcher */}
        <div className="absolute top-4 right-4">
          <LanguageSwitcher />
        </div>

        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-purple-600 mb-4" />
            <p className="text-gray-600">驗證連結中...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 成功設定密碼
  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4">
        {/* Language Switcher */}
        <div className="absolute top-4 right-4">
          <LanguageSwitcher />
        </div>

        <div className="w-full max-w-md">
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl">🎉 密碼設定成功！</CardTitle>
              <CardDescription>
                {userInfo?.organization_name && (
                  <div className="mt-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
                    <div className="flex items-center justify-center gap-2 text-purple-700">
                      <Building2 className="h-4 w-4" />
                      <span className="font-medium">
                        {userInfo.organization_name}
                      </span>
                    </div>
                  </div>
                )}
                <p className="mt-4 text-gray-600">
                  您現在可以使用您的帳號登入 Duotopia 了
                </p>
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <Alert className="bg-green-50 border-green-200">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  您的 Duotopia 帳號已啟用，可以開始使用所有功能！
                </AlertDescription>
              </Alert>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                <p className="font-semibold mb-2">✨ 您現在可以：</p>
                <ul className="space-y-1 ml-4">
                  <li>• 登入 Duotopia 教學平台</li>
                  <li>• 管理班級和學生</li>
                  <li>• 指派和批改作業</li>
                  <li>• 追蹤學生學習進度</li>
                </ul>
              </div>

              <Button
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                onClick={() => navigate("/teacher/login")}
              >
                前往登入頁面
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
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4">
        {/* Language Switcher */}
        <div className="absolute top-4 right-4">
          <LanguageSwitcher />
        </div>

        <div className="w-full max-w-md">
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <XCircle className="h-8 w-8 text-red-600" />
              </div>
              <CardTitle className="text-2xl">連結無效或已過期</CardTitle>
              <CardDescription>此密碼設定連結已失效</CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <Alert className="bg-red-50 border-red-200">
                <XCircle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  {error || "連結可能已過期（48 小時有效期）或已被使用過"}
                </AlertDescription>
              </Alert>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
                <p className="font-semibold mb-2">⏰ 注意事項：</p>
                <ul className="space-y-1 ml-4">
                  <li>• 密碼設定連結有效期為 48 小時</li>
                  <li>• 每個連結只能使用一次</li>
                  <li>• 如需協助，請聯繫您的機構管理員</li>
                </ul>
              </div>

              <div className="space-y-2">
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

  // 設定密碼表單
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4">
      {/* Language Switcher */}
      <div className="absolute top-4 right-4">
        <LanguageSwitcher />
      </div>

      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-2">
            Duotopia
          </h1>
          <p className="text-gray-600">設定您的密碼</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5 text-purple-600" />
              設定您的密碼
            </CardTitle>
            <CardDescription>
              {userInfo && (
                <div className="mt-3 space-y-2">
                  {userInfo.organization_name && (
                    <div className="flex items-center gap-2 p-3 bg-purple-50 rounded-lg border border-purple-200">
                      <Building2 className="h-4 w-4 text-purple-600" />
                      <div className="text-sm">
                        <span className="text-gray-600">機構：</span>
                        <span className="font-medium text-purple-700 ml-1">
                          {userInfo.organization_name}
                        </span>
                      </div>
                    </div>
                  )}
                  <div className="text-sm text-gray-600">
                    <p className="font-medium">帳號：{userInfo.email}</p>
                    <p>姓名：{userInfo.name}</p>
                  </div>
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
                    placeholder="請輸入至少 6 個字元的密碼"
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
                <Label htmlFor="confirmPassword">確認密碼</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="請再次輸入密碼"
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

              <div className="text-sm text-gray-500 bg-gray-50 p-3 rounded-lg">
                <p className="font-medium mb-1">密碼要求：</p>
                <ul className="space-y-1 ml-4">
                  <li>• 至少 6 個字元</li>
                  <li>• 建議包含英文字母和數字</li>
                </ul>
              </div>

              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    設定中...
                  </>
                ) : (
                  "設定密碼並啟用帳號"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p>設定密碼後，您的帳號將立即啟用</p>
          <p className="mt-1">可以開始使用 Duotopia 的所有功能</p>
        </div>
      </div>
    </div>
  );
}
