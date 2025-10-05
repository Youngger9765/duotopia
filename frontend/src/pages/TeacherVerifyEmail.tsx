import { useLocation, useNavigate } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Mail, CheckCircle, ArrowLeft } from "lucide-react";

export function TeacherVerifyEmail() {
  const location = useLocation();
  const navigate = useNavigate();
  const { email, message } = location.state || {
    email: "",
    message: "註冊成功！請檢查您的 Email 信箱並點擊驗證連結。",
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Duotopia</h1>
          <p className="text-gray-600">AI 驅動的英語學習平台</p>
        </div>

        <Card>
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <CardTitle className="text-2xl">註冊成功！</CardTitle>
            <CardDescription>請驗證您的 Email 地址</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <Alert className="bg-blue-50 border-blue-200">
              <Mail className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-blue-800">
                {message}
              </AlertDescription>
            </Alert>

            <div className="text-center space-y-2">
              <p className="text-gray-600">我們已發送驗證郵件至：</p>
              <p className="font-semibold text-lg">{email}</p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg space-y-2">
              <p className="text-sm text-gray-600">
                <strong>接下來的步驟：</strong>
              </p>
              <ol className="text-sm text-gray-600 list-decimal list-inside space-y-1">
                <li>檢查您的收件匣</li>
                <li>點擊驗證連結</li>
                <li>開始使用您的教師帳號</li>
              </ol>
            </div>

            <div className="space-y-3">
              <p className="text-sm text-gray-500 text-center">
                沒有收到驗證郵件？請檢查垃圾郵件資料夾
              </p>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => navigate("/teacher/login")}
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  返回登入
                </Button>

                <Button className="flex-1" disabled>
                  重新發送郵件
                </Button>
              </div>
            </div>

            <div className="pt-4 border-t">
              <p className="text-xs text-gray-500 text-center">
                驗證後您將獲得 30 天免費試用期
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
