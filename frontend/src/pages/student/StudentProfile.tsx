import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useStudentAuthStore } from '@/stores/studentAuthStore';
import { toast } from 'sonner';
import {
  User,
  Mail,
  Calendar,
  School,
  CheckCircle,
  XCircle,
  AlertCircle,
  Edit2,
  Trash2,
  ArrowLeft,
  Shield,
  Loader2
} from 'lucide-react';

interface StudentInfo {
  id: number;
  name: string;
  email: string;
  email_verified: boolean;
  email_verified_at: string | null;
  birthday: string;
  classroom_name: string | null;
  school_name: string | null;
  created_at: string;
}

export default function StudentProfile() {
  const navigate = useNavigate();
  const { user, token, logout } = useStudentAuthStore();
  const [studentInfo, setStudentInfo] = useState<StudentInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [showEmailEdit, setShowEmailEdit] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [showUnbindConfirm, setShowUnbindConfirm] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isUnbinding, setIsUnbinding] = useState(false);

  useEffect(() => {
    if (!user || !token) {
      navigate('/student/login');
      return;
    }
    loadStudentInfo();
  }, [user, token, navigate]);

  const loadStudentInfo = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${apiUrl}/api/students/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStudentInfo(data);
        setNewEmail(data.email || '');
      } else {
        toast.error('無法載入個人資料');
      }
    } catch {
      toast.error('載入個人資料失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateEmail = async () => {
    if (!newEmail || !newEmail.includes('@')) {
      toast.error('請輸入有效的 Email 地址');
      return;
    }

    setIsUpdating(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${apiUrl}/api/students/update-email`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: newEmail })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.verification_sent) {
          toast.success('驗證信已發送到新的 Email 地址');
        } else {
          toast.success('Email 已更新');
        }
        setShowEmailEdit(false);
        loadStudentInfo();
      } else {
        const error = await response.text();
        toast.error(`更新失敗：${error}`);
      }
    } catch {
      toast.error('更新 Email 失敗');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleUnbindEmail = async () => {
    setIsUnbinding(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${apiUrl}/api/students/unbind-email`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        toast.success('Email 綁定已解除');
        setShowUnbindConfirm(false);
        loadStudentInfo();
      } else {
        const error = await response.text();
        toast.error(`解除綁定失敗：${error}`);
      }
    } catch {
      toast.error('解除綁定失敗');
    } finally {
      setIsUnbinding(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '未設定';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-TW');
  };

  if (loading) {
    return (
      <div className="p-4 lg:p-8">
        <div className="max-w-3xl mx-auto">
          <Card>
            <CardContent className="p-8 text-center">
              載入中...
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!studentInfo) {
    return (
      <div className="p-4 lg:p-8">
        <div className="max-w-3xl mx-auto">
          <Card>
            <CardContent className="p-8 text-center">
              無法載入個人資料
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/student/dashboard')}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              返回
            </Button>
            <h1 className="text-2xl font-bold">個人資料</h1>
          </div>
        </div>

        {/* Basic Info Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              基本資訊
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-500">姓名</label>
                <p className="font-medium">{studentInfo.name}</p>
              </div>
              <div>
                <label className="text-sm text-gray-500">生日</label>
                <p className="font-medium flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  {formatDate(studentInfo.birthday)}
                </p>
              </div>
              <div>
                <label className="text-sm text-gray-500">班級</label>
                <p className="font-medium">
                  {studentInfo.classroom_name || '未分配班級'}
                </p>
              </div>
              <div>
                <label className="text-sm text-gray-500">學校</label>
                <p className="font-medium flex items-center gap-2">
                  <School className="h-4 w-4 text-gray-400" />
                  {studentInfo.school_name || '未設定學校'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Email Settings Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Email 設定
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!showEmailEdit ? (
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div>
                      <p className="font-medium">{studentInfo.email || '未設定 Email'}</p>
                      {studentInfo.email && (
                        <p className="text-xs text-gray-500 mt-1">
                          {studentInfo.email_verified && studentInfo.email_verified_at
                            ? `已於 ${formatDate(studentInfo.email_verified_at)} 驗證`
                            : '尚未驗證'}
                        </p>
                      )}
                    </div>
                    {studentInfo.email && (
                      <div>
                        {studentInfo.email_verified ? (
                          <Badge className="bg-green-100 text-green-700 flex items-center gap-1">
                            <CheckCircle className="h-3 w-3" />
                            已驗證
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-orange-600 border-orange-300 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            待驗證
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setShowEmailEdit(true)}
                      className="hover:bg-gray-200 transition-colors"
                    >
                      <Edit2 className="h-4 w-4 mr-1" />
                      {studentInfo.email ? '修改' : '設定'}
                    </Button>
                    {studentInfo.email && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-300 transition-colors"
                        onClick={() => setShowUnbindConfirm(true)}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        解除綁定
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    新的 Email 地址
                  </label>
                  <Input
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="請輸入新的 Email 地址"
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleUpdateEmail}
                    disabled={isUpdating || !newEmail || !newEmail.includes('@')}
                    className="min-w-[100px]"
                  >
                    {isUpdating ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        更新中...
                      </>
                    ) : (
                      '確認更新'
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setShowEmailEdit(false);
                      setNewEmail(studentInfo.email || '');
                    }}
                    disabled={isUpdating}
                  >
                    取消
                  </Button>
                </div>
              </div>
            )}

            {/* Unbind Confirmation Dialog */}
            {showUnbindConfirm && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-900">
                      確定要解除 Email 綁定嗎？
                    </p>
                    <p className="text-xs text-red-700 mt-1">
                      解除綁定後，您將無法收到學習提醒和重要通知。
                    </p>
                    <div className="flex gap-2 mt-3">
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={handleUnbindEmail}
                        disabled={isUnbinding}
                        className="min-w-[100px]"
                      >
                        {isUnbinding ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            解除中...
                          </>
                        ) : (
                          '確定解除'
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setShowUnbindConfirm(false)}
                        disabled={isUnbinding}
                      >
                        取消
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Account Info Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              帳號資訊
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-500">帳號 ID</label>
                <p className="font-medium">#{studentInfo.id}</p>
              </div>
              <div>
                <label className="text-sm text-gray-500">註冊時間</label>
                <p className="font-medium">{formatDate(studentInfo.created_at)}</p>
              </div>
            </div>
            <div className="pt-4 border-t">
              <Button
                variant="outline"
                className="text-red-600 hover:text-red-700"
                onClick={() => {
                  logout();
                  navigate('/student/login');
                }}
              >
                登出帳號
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
