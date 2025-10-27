import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Search, CheckCircle, Mail, Calendar, XCircle } from "lucide-react";

const ADMIN_SECRET = import.meta.env.VITE_ADMIN_SECRET || "";
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface TeacherInfo {
  id: number;
  email: string;
  name: string;
  phone?: string;
  email_verified: boolean;
  is_active: boolean;
  created_at: string;
  email_verified_at?: string;
  subscription_end_date?: string;
  subscription_status: string;
  days_remaining?: number;
  email_verification_token?: string;
}

export function AdminTeacherManagement() {
  const [email, setEmail] = useState("");
  const [teacher, setTeacher] = useState<TeacherInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [adjustDays, setAdjustDays] = useState(0);

  const queryTeacher = async () => {
    setLoading(true);
    setError("");
    setSuccess("");
    setTeacher(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/admin/teacher-management/query?email=${email}`,
        {
          headers: {
            "X-Admin-Secret": ADMIN_SECRET,
          },
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "查詢失敗");
      }

      const data = await response.json();
      setTeacher(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const activateTeacher = async () => {
    if (!teacher) return;

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(
        `${API_BASE}/api/admin/teacher-management/activate?email=${teacher.email}`,
        {
          method: "POST",
          headers: {
            "X-Admin-Secret": ADMIN_SECRET,
          },
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "開通失敗");
      }

      const data = await response.json();
      setSuccess(data.message);
      // 重新查詢
      await queryTeacher();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resendVerification = async () => {
    if (!teacher) return;

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(
        `${API_BASE}/api/admin/teacher-management/resend-verification?email=${teacher.email}`,
        {
          method: "POST",
          headers: {
            "X-Admin-Secret": ADMIN_SECRET,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "發送失敗");
      }

      const data = await response.json();
      setSuccess(`${data.message}\n驗證連結: ${data.verification_url}`);
      // 重新查詢
      await queryTeacher();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const adjustSubscription = async () => {
    if (!teacher || adjustDays === 0) return;

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(
        `${API_BASE}/api/admin/teacher-management/adjust-subscription`,
        {
          method: "POST",
          headers: {
            "X-Admin-Secret": ADMIN_SECRET,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: teacher.email,
            days: adjustDays,
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "調整失敗");
      }

      const data = await response.json();
      setSuccess(data.message);
      setAdjustDays(0);
      // 重新查詢
      await queryTeacher();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            教師帳號管理後台
          </h1>
          <p className="text-gray-600 mt-2">查詢與管理教師帳號狀態</p>
        </div>

        {/* 查詢區 */}
        <Card>
          <CardHeader>
            <CardTitle>查詢教師帳號</CardTitle>
            <CardDescription>輸入 Email 查詢帳號資訊</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="teacher@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && queryTeacher()}
                />
              </div>
              <div className="flex items-end">
                <Button
                  onClick={queryTeacher}
                  disabled={loading || !email}
                >
                  <Search className="h-4 w-4 mr-2" />
                  查詢
                </Button>
              </div>
            </div>

            {error && (
              <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="bg-green-50 border-green-200">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800 whitespace-pre-line">
                  {success}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* 教師資訊 */}
        {teacher && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>帳號資訊</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">ID</p>
                    <p className="font-medium">{teacher.id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">姓名</p>
                    <p className="font-medium">{teacher.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Email</p>
                    <p className="font-medium">{teacher.email}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">電話</p>
                    <p className="font-medium">{teacher.phone || "未設定"}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Email 驗證</p>
                    <p className="font-medium">
                      {teacher.email_verified ? (
                        <span className="text-green-600">✓ 已驗證</span>
                      ) : (
                        <span className="text-red-600">✗ 未驗證</span>
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">帳號狀態</p>
                    <p className="font-medium">
                      {teacher.is_active ? (
                        <span className="text-green-600">✓ 啟用</span>
                      ) : (
                        <span className="text-red-600">✗ 未啟用</span>
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">訂閱狀態</p>
                    <p className="font-medium">{teacher.subscription_status}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">剩餘天數</p>
                    <p className="font-medium">
                      {teacher.days_remaining ?? "N/A"} 天
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">註冊時間</p>
                    <p className="font-medium">
                      {new Date(teacher.created_at).toLocaleString("zh-TW")}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">驗證時間</p>
                    <p className="font-medium">
                      {teacher.email_verified_at
                        ? new Date(teacher.email_verified_at).toLocaleString(
                            "zh-TW"
                          )
                        : "未驗證"}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 操作區 */}
            <Card>
              <CardHeader>
                <CardTitle>管理操作</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 開通帳號 */}
                {!teacher.email_verified && (
                  <div className="p-4 bg-blue-50 rounded-lg space-y-3">
                    <div>
                      <h4 className="font-medium text-blue-900">開通帳號</h4>
                      <p className="text-sm text-blue-700">
                        直接開通帳號（跳過 Email 驗證並給予 30 天訂閱）
                      </p>
                    </div>
                    <Button
                      onClick={activateTeacher}
                      disabled={loading}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      開通帳號
                    </Button>
                  </div>
                )}

                {/* 重新發送驗證信 */}
                {!teacher.email_verified && (
                  <div className="p-4 bg-purple-50 rounded-lg space-y-3">
                    <div>
                      <h4 className="font-medium text-purple-900">
                        重新發送驗證信
                      </h4>
                      <p className="text-sm text-purple-700">
                        發送新的驗證連結到教師 Email
                      </p>
                    </div>
                    <Button
                      onClick={resendVerification}
                      disabled={loading}
                      variant="outline"
                      className="border-purple-300 text-purple-700 hover:bg-purple-50"
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      重新發送驗證信
                    </Button>
                  </div>
                )}

                {/* 調整訂閱天數 */}
                <div className="p-4 bg-green-50 rounded-lg space-y-3">
                  <div>
                    <h4 className="font-medium text-green-900">調整訂閱天數</h4>
                    <p className="text-sm text-green-700">
                      增加或減少訂閱天數（正數增加，負數減少）
                    </p>
                  </div>
                  <div className="flex gap-4 items-end">
                    <div className="flex-1">
                      <Label htmlFor="days">天數</Label>
                      <Input
                        id="days"
                        type="number"
                        placeholder="例: 30 或 -7"
                        value={adjustDays || ""}
                        onChange={(e) =>
                          setAdjustDays(parseInt(e.target.value) || 0)
                        }
                      />
                    </div>
                    <Button
                      onClick={adjustSubscription}
                      disabled={loading || adjustDays === 0}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Calendar className="h-4 w-4 mr-2" />
                      調整天數
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
