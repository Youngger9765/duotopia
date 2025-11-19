import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import TeacherLayout from "@/components/TeacherLayout";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import {
  User,
  Mail,
  Phone,
  Shield,
  Loader2,
  Edit2,
  Save,
  X,
  Lock,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { validatePasswordStrength } from "@/utils/passwordValidation";

interface TeacherInfo {
  id: number;
  name: string;
  email: string;
  phone?: string;
  is_demo: boolean;
  is_active: boolean;
  is_admin?: boolean;
}

export default function TeacherProfile() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [teacherInfo, setTeacherInfo] = useState<TeacherInfo | null>(null);
  const [loading, setLoading] = useState(true);

  // Name update states
  const [showNameEdit, setShowNameEdit] = useState(false);
  const [newName, setNewName] = useState("");
  const [isUpdatingName, setIsUpdatingName] = useState(false);

  // Phone update states
  const [showPhoneEdit, setShowPhoneEdit] = useState(false);
  const [newPhone, setNewPhone] = useState("");
  const [isUpdatingPhone, setIsUpdatingPhone] = useState(false);

  // Password update states
  const [showPasswordEdit, setShowPasswordEdit] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);

  useEffect(() => {
    loadTeacherInfo();
  }, []);

  const loadTeacherInfo = async () => {
    try {
      const data = (await apiClient.getTeacherDashboard()) as {
        teacher: TeacherInfo;
      };
      setTeacherInfo(data.teacher);
      setNewPhone(data.teacher.phone || "");
    } catch (err) {
      console.error("Failed to fetch teacher profile:", err);
      toast.error(t("teacherProfile.errors.loadFailed"));
      if (err instanceof Error && err.message.includes("401")) {
        navigate("/teacher/login");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateName = async () => {
    if (!newName || newName.trim().length === 0) {
      toast.error(t("teacherProfile.errors.nameEmpty"));
      return;
    }

    setIsUpdatingName(true);
    try {
      await apiClient.updateTeacherProfile({ name: newName });
      toast.success(t("teacherProfile.success.nameUpdated"));
      setShowNameEdit(false);
      loadTeacherInfo();
    } catch (err) {
      console.error("Failed to update name:", err);
      toast.error(t("teacherProfile.errors.updateFailed"));
    } finally {
      setIsUpdatingName(false);
    }
  };

  const handleUpdatePhone = async () => {
    setIsUpdatingPhone(true);
    try {
      await apiClient.updateTeacherProfile({ phone: newPhone || undefined });
      toast.success(t("teacherProfile.success.phoneUpdated"));
      setShowPhoneEdit(false);
      loadTeacherInfo();
    } catch (err) {
      console.error("Failed to update phone:", err);
      toast.error(t("teacherProfile.errors.updateFailed"));
    } finally {
      setIsUpdatingPhone(false);
    }
  };

  const handleUpdatePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error(t("teacherProfile.password.errors.allFieldsRequired"));
      return;
    }

    // Bug3 Fix: Check if new password is same as current password FIRST
    // This prevents confusing UX where user thinks they should enter same password
    if (currentPassword === newPassword) {
      toast.error(t("teacherProfile.password.errors.passwordSameAsCurrent"));
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error(t("teacherProfile.password.errors.passwordMismatch"));
      return;
    }

    // Validate password strength (comprehensive check)
    const validation = validatePasswordStrength(newPassword);
    if (!validation.valid && validation.errorKey) {
      toast.error(t(`teacherProfile.password.errors.${validation.errorKey}`));
      return;
    }

    setIsUpdatingPassword(true);
    try {
      await apiClient.updateTeacherPassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      toast.success(t("teacherProfile.password.success.passwordUpdated"));
      setShowPasswordEdit(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      console.error("Failed to update password:", err);
      toast.error(t("teacherProfile.password.errors.updateFailed"));
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  if (loading) {
    return (
      <TeacherLayout>
        <div className="max-w-4xl mx-auto">
          <Card>
            <CardContent className="p-6 sm:p-8 text-center dark:bg-gray-800">
              {t("teacherProfile.loading")}
            </CardContent>
          </Card>
        </div>
      </TeacherLayout>
    );
  }

  if (!teacherInfo) {
    return (
      <TeacherLayout>
        <div className="max-w-4xl mx-auto">
          <Card>
            <CardContent className="p-6 sm:p-8 text-center dark:bg-gray-800">
              {t("teacherProfile.errors.loadFailed")}
            </CardContent>
          </Card>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-4 sm:mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100">
            {t("teacherProfile.header.title")}
          </h1>
        </div>

        {/* Basic Info Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              {t("teacherProfile.basicInfo.title")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-500">
                  {t("teacherProfile.basicInfo.name")}
                </label>
                {!showNameEdit ? (
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{teacherInfo.name}</p>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setNewName(teacherInfo.name);
                        setShowNameEdit(true);
                      }}
                      className="h-6 px-2"
                    >
                      <Edit2 className="h-3 w-3" />
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 mt-1">
                    <Input
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      className="h-9"
                      placeholder={t(
                        "teacherProfile.basicInfo.namePlaceholder",
                      )}
                    />
                    <Button
                      size="sm"
                      onClick={handleUpdateName}
                      disabled={isUpdatingName || !newName.trim()}
                      className="h-9 px-3"
                    >
                      {isUpdatingName ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Save className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setShowNameEdit(false);
                        setNewName("");
                      }}
                      disabled={isUpdatingName}
                      className="h-9 px-3"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>
              <div>
                <label className="text-sm text-gray-500">
                  {t("teacherProfile.basicInfo.email")}
                </label>
                <p className="font-medium flex items-center gap-2">
                  <Mail className="h-4 w-4 text-gray-400" />
                  {teacherInfo.email}
                </p>
              </div>
              <div>
                <label className="text-sm text-gray-500">
                  {t("teacherProfile.basicInfo.phone")}
                </label>
                {!showPhoneEdit ? (
                  <div className="flex items-center gap-2">
                    <p className="font-medium flex items-center gap-2">
                      <Phone className="h-4 w-4 text-gray-400" />
                      {teacherInfo.phone ||
                        t("teacherProfile.basicInfo.phoneNone")}
                    </p>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setNewPhone(teacherInfo.phone || "");
                        setShowPhoneEdit(true);
                      }}
                      className="h-6 px-2"
                    >
                      <Edit2 className="h-3 w-3" />
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 mt-1">
                    <Input
                      value={newPhone}
                      onChange={(e) => setNewPhone(e.target.value)}
                      className="h-9"
                      placeholder={t(
                        "teacherProfile.basicInfo.phonePlaceholder",
                      )}
                    />
                    <Button
                      size="sm"
                      onClick={handleUpdatePhone}
                      disabled={isUpdatingPhone}
                      className="h-9 px-3"
                    >
                      {isUpdatingPhone ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Save className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setShowPhoneEdit(false);
                        setNewPhone(teacherInfo.phone || "");
                      }}
                      disabled={isUpdatingPhone}
                      className="h-9 px-3"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>
              <div>
                <label className="text-sm text-gray-500">
                  {t("teacherProfile.basicInfo.accountType")}
                </label>
                <p className="font-medium flex items-center gap-2">
                  <Shield className="h-4 w-4 text-gray-400" />
                  {teacherInfo.is_admin
                    ? t("teacherProfile.basicInfo.admin")
                    : t("teacherProfile.basicInfo.teacher")}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Password Settings Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5" />
              {t("teacherProfile.password.title")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!showPasswordEdit ? (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {t("teacherProfile.password.description")}
                </p>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setShowPasswordEdit(true)}
                  className="hover:bg-gray-200 transition-colors"
                >
                  <Lock className="h-4 w-4 mr-2" />
                  {t("teacherProfile.password.changeButton")}
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {/* Password Requirements */}
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    {t("teacherProfile.password.requirements")}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    {t("teacherProfile.password.currentPassword")}
                  </label>
                  <Input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder={t(
                      "teacherProfile.password.currentPasswordPlaceholder",
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    {t("teacherProfile.password.newPassword")}
                  </label>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder={t(
                      "teacherProfile.password.newPasswordPlaceholder",
                    )}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    {t("teacherProfile.password.confirmPassword")}
                  </label>
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder={t(
                      "teacherProfile.password.confirmPasswordPlaceholder",
                    )}
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleUpdatePassword}
                    disabled={
                      isUpdatingPassword ||
                      !currentPassword ||
                      !newPassword ||
                      !confirmPassword
                    }
                    className="min-w-[100px]"
                  >
                    {isUpdatingPassword ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        {t("teacherProfile.password.updating")}
                      </>
                    ) : (
                      t("teacherProfile.password.updateButton")
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setShowPasswordEdit(false);
                      setCurrentPassword("");
                      setNewPassword("");
                      setConfirmPassword("");
                    }}
                    disabled={isUpdatingPassword}
                  >
                    {t("teacherProfile.password.cancel")}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </TeacherLayout>
  );
}
