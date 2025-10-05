import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
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
import { Loader2, Mail, ArrowLeft, CheckCircle } from "lucide-react";
import { apiClient } from "../lib/api";

export default function TeacherForgotPassword() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [email, setEmail] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setSuccess(false);

    try {
      const response = await apiClient.post(
        "/api/auth/teacher/forgot-password",
        {
          email,
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
        // 檢查是否是太頻繁的請求
        if (err.message.includes("429")) {
          setError("請稍後再試，密碼重設郵件每5分鐘只能發送一次");
        } else {
          setError(err.message || "發送失敗，請稍後再試");
        }
      } else {
        setError("發送失敗，請稍後再試");
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl">郵件已發送</CardTitle>
              <CardDescription>請檢查您的郵件信箱</CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <Alert className="bg-blue-50 border-blue-200">
                <Mail className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  如果 {email} 是註冊過的帳號，您將會收到密碼重設連結。
                  請檢查您的收件匣和垃圾郵件資料夾。
                </AlertDescription>
              </Alert>

              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <p className="text-sm text-gray-600">
                  <strong>接下來的步驟：</strong>
                </p>
                <ol className="text-sm text-gray-600 list-decimal list-inside space-y-1">
                  <li>檢查您的郵件信箱</li>
                  <li>點擊郵件中的重設連結</li>
                  <li>設定新密碼</li>
                </ol>
              </div>

              <div className="pt-4 space-y-2">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => navigate("/teacher/login")}
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  返回登入頁面
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Duotopia</h1>
          <p className="text-gray-600">AI 驅動的英語學習平台</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>忘記密碼</CardTitle>
            <CardDescription>
              輸入您的註冊郵件地址，我們會發送密碼重設連結給您
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
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

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    發送中...
                  </>
                ) : (
                  "發送重設連結"
                )}
              </Button>

              <div className="pt-4 text-center">
                <Link
                  to="/teacher/login"
                  className="text-sm text-blue-600 hover:underline inline-flex items-center"
                >
                  <ArrowLeft className="h-3 w-3 mr-1" />
                  返回登入頁面
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>

        <div className="mt-4 text-center text-xs text-gray-500">
          密碼重設連結將在 2 小時後失效
        </div>
      </div>
    </div>
  );
}
