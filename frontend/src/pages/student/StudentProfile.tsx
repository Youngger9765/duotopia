import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { toast } from "sonner";
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
  Loader2,
} from "lucide-react";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, token, logout } = useStudentAuthStore();
  const [studentInfo, setStudentInfo] = useState<StudentInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [showEmailEdit, setShowEmailEdit] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [showUnbindConfirm, setShowUnbindConfirm] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isUnbinding, setIsUnbinding] = useState(false);

  useEffect(() => {
    if (!user || !token) {
      navigate("/student/login");
      return;
    }
    loadStudentInfo();
  }, [user, token, navigate]);

  const loadStudentInfo = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const response = await fetch(`${apiUrl}/api/students/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStudentInfo(data);
        setNewEmail(data.email || "");
      } else {
        toast.error(t("studentProfile.errors.loadFailed"));
      }
    } catch {
      toast.error(t("studentProfile.errors.loadError"));
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateEmail = async () => {
    if (!newEmail || !newEmail.includes("@")) {
      toast.error(t("studentProfile.errors.invalidEmail"));
      return;
    }

    setIsUpdating(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const response = await fetch(`${apiUrl}/api/students/update-email`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: newEmail }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.verification_sent) {
          toast.success(t("studentProfile.success.verificationSent"));
        } else {
          toast.success(t("studentProfile.success.emailUpdated"));
        }
        setShowEmailEdit(false);
        loadStudentInfo();
      } else {
        const error = await response.text();
        toast.error(t("studentProfile.errors.updateFailed", { error }));
      }
    } catch {
      toast.error(t("studentProfile.errors.updateError"));
    } finally {
      setIsUpdating(false);
    }
  };

  const handleUnbindEmail = async () => {
    setIsUnbinding(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const response = await fetch(`${apiUrl}/api/students/unbind-email`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        toast.success(t("studentProfile.success.emailUnbound"));
        setShowUnbindConfirm(false);
        loadStudentInfo();
      } else {
        const error = await response.text();
        toast.error(t("studentProfile.errors.unbindFailed", { error }));
      }
    } catch {
      toast.error(t("studentProfile.errors.unbindError"));
    } finally {
      setIsUnbinding(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return t("studentProfile.basicInfo.notSet");
    const date = new Date(dateString);
    return date.toLocaleDateString("zh-TW");
  };

  if (loading) {
    return (
      <div className="p-3 sm:p-4 lg:p-6">
        <div className="max-w-full mx-auto">
          <Card>
            <CardContent className="p-6 sm:p-8 text-center dark:bg-gray-800">
              {t("studentProfile.loading")}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!studentInfo) {
    return (
      <div className="p-3 sm:p-4 lg:p-6">
        <div className="max-w-full mx-auto">
          <Card>
            <CardContent className="p-6 sm:p-8 text-center dark:bg-gray-800">
              {t("studentProfile.errors.loadFailed")}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 sm:p-4 lg:p-6">
      <div className="max-w-full mx-auto">
        {/* Header */}
        <div className="mb-4 sm:mb-6 flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
          <div className="flex items-center gap-2 sm:gap-4 w-full sm:w-auto">
            <Button
              variant="ghost"
              onClick={() => navigate("/student/dashboard")}
              className="gap-2 h-12 min-h-12 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              <ArrowLeft className="h-4 w-4" />
              <span className="hidden sm:inline">
                {t("studentProfile.header.back")}
              </span>
            </Button>
            <h1 className="text-xl sm:text-2xl font-bold dark:text-gray-100">
              {t("studentProfile.header.title")}
            </h1>
          </div>
        </div>

        {/* Basic Info Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              {t("studentProfile.basicInfo.title")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-500">
                  {t("studentProfile.basicInfo.name")}
                </label>
                <p className="font-medium">{studentInfo.name}</p>
              </div>
              <div>
                <label className="text-sm text-gray-500">
                  {t("studentProfile.basicInfo.birthday")}
                </label>
                <p className="font-medium flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  {formatDate(studentInfo.birthday)}
                </p>
              </div>
              <div>
                <label className="text-sm text-gray-500">
                  {t("studentProfile.basicInfo.classroom")}
                </label>
                <p className="font-medium">
                  {studentInfo.classroom_name ||
                    t("studentProfile.basicInfo.classroomNone")}
                </p>
              </div>
              <div>
                <label className="text-sm text-gray-500">
                  {t("studentProfile.basicInfo.school")}
                </label>
                <p className="font-medium flex items-center gap-2">
                  <School className="h-4 w-4 text-gray-400" />
                  {studentInfo.school_name ||
                    t("studentProfile.basicInfo.schoolNone")}
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
              {t("studentProfile.email.title")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!showEmailEdit ? (
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div>
                      <p className="font-medium">
                        {studentInfo.email || t("studentProfile.email.noEmail")}
                      </p>
                      {studentInfo.email && (
                        <p className="text-xs text-gray-500 mt-1">
                          {studentInfo.email_verified &&
                          studentInfo.email_verified_at
                            ? t("studentProfile.email.verifiedAt", {
                                date: formatDate(studentInfo.email_verified_at),
                              })
                            : t("studentProfile.email.unverified")}
                        </p>
                      )}
                    </div>
                    {studentInfo.email && (
                      <div>
                        {studentInfo.email_verified ? (
                          <Badge className="bg-green-100 text-green-700 flex items-center gap-1">
                            <CheckCircle className="h-3 w-3" />
                            {t("studentProfile.email.verified")}
                          </Badge>
                        ) : (
                          <Badge
                            variant="outline"
                            className="text-orange-600 border-orange-300 flex items-center gap-1"
                          >
                            <AlertCircle className="h-3 w-3" />
                            {t("studentProfile.email.pending")}
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
                      {studentInfo.email
                        ? t("studentProfile.email.update")
                        : t("studentProfile.email.setup")}
                    </Button>
                    {studentInfo.email && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-300 transition-colors"
                        onClick={() => setShowUnbindConfirm(true)}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        {t("studentProfile.email.unbind")}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    {t("studentProfile.email.newEmail")}
                  </label>
                  <Input
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder={t("studentProfile.email.placeholder")}
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleUpdateEmail}
                    disabled={
                      isUpdating || !newEmail || !newEmail.includes("@")
                    }
                    className="min-w-[100px]"
                  >
                    {isUpdating ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        {t("studentProfile.email.updating")}
                      </>
                    ) : (
                      t("studentProfile.email.confirm")
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setShowEmailEdit(false);
                      setNewEmail(studentInfo.email || "");
                    }}
                    disabled={isUpdating}
                  >
                    {t("studentProfile.email.cancel")}
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
                      {t("studentProfile.unbindDialog.title")}
                    </p>
                    <p className="text-xs text-red-700 mt-1">
                      {t("studentProfile.unbindDialog.description")}
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
                            {t("studentProfile.unbindDialog.unbinding")}
                          </>
                        ) : (
                          t("studentProfile.unbindDialog.confirm")
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setShowUnbindConfirm(false)}
                        disabled={isUnbinding}
                      >
                        {t("studentProfile.unbindDialog.cancel")}
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
              {t("studentProfile.account.title")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-500">
                  {t("studentProfile.account.id")}
                </label>
                <p className="font-medium">#{studentInfo.id}</p>
              </div>
              <div>
                <label className="text-sm text-gray-500">
                  {t("studentProfile.account.registeredAt")}
                </label>
                <p className="font-medium">
                  {formatDate(studentInfo.created_at)}
                </p>
              </div>
            </div>
            <div className="pt-4 border-t">
              <Button
                variant="outline"
                className="text-red-600 hover:text-red-700"
                onClick={() => {
                  logout();
                  navigate("/student/login");
                }}
              >
                {t("studentProfile.account.logout")}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
