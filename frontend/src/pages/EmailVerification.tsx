import { useState, useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle, XCircle, Loader2, Mail } from "lucide-react";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export default function EmailVerification() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading",
  );
  const [message, setMessage] = useState("");
  const [studentInfo, setStudentInfo] = useState<{
    name: string;
    email: string;
  } | null>(null);
  const hasVerifiedRef = useRef(false);

  useEffect(() => {
    const token = searchParams.get("token");

    if (!token) {
      setStatus("error");
      setMessage("缺少驗證 token");
      return;
    }

    // 防止 React StrictMode 重複呼叫
    if (!hasVerifiedRef.current) {
      hasVerifiedRef.current = true;
      verifyEmail(token);
    }
  }, [searchParams]);

  const verifyEmail = async (token: string) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const response = await fetch(
        `${apiUrl}/api/students/verify-email/${token}`,
        {
          method: "GET",
        },
      );

      const data = await response.json();

      if (response.ok) {
        setStatus("success");
        setMessage(data.message || "Email 驗證成功！");
        setStudentInfo({
          name: data.student_name,
          email: data.email,
        });
      } else {
        setStatus("error");
        setMessage(data.detail || "驗證失敗");
      }
    } catch {
      setStatus("error");
      setMessage("網路連線錯誤，請稍後再試");
    }
  };

  const handleGoToLogin = () => {
    navigate("/student/login");
  };

  const handleGoHome = () => {
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="absolute top-4 right-4">
        <LanguageSwitcher />
      </div>
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4">
            {status === "loading" && (
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
            )}
            {status === "success" && (
              <CheckCircle className="w-12 h-12 text-green-500" />
            )}
            {status === "error" && (
              <XCircle className="w-12 h-12 text-red-500" />
            )}
          </div>
          <CardTitle className="text-xl">
            {status === "loading" && "驗證中..."}
            {status === "success" && "驗證成功！"}
            {status === "error" && "驗證失敗"}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4 text-center">
          <p className="text-gray-600">{message}</p>

          {status === "success" && studentInfo && (
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="flex items-center justify-center mb-2">
                <Mail className="w-5 h-5 text-green-600 mr-2" />
                <span className="text-sm text-green-700">帳號資訊</span>
              </div>
              <p className="text-sm text-green-800">
                <strong>學生：</strong>
                {studentInfo.name}
              </p>
              <p className="text-sm text-green-800">
                <strong>Email：</strong>
                {studentInfo.email}
              </p>
            </div>
          )}

          <div className="space-y-2 pt-4">
            {status === "success" && (
              <Button onClick={handleGoToLogin} className="w-full">
                前往學生登入
              </Button>
            )}

            <Button onClick={handleGoHome} variant="outline" className="w-full">
              回到首頁
            </Button>
          </div>

          {status === "error" && (
            <div className="bg-yellow-50 p-3 rounded border border-yellow-200">
              <p className="text-xs text-yellow-700">
                如果持續遇到問題，請聯繫系統管理員或重新登入後再次設定 Email。
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
