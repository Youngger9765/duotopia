import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Building, Mail, Phone, Hash } from "lucide-react";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import {
  AdminOrganizationCreateRequest,
  AdminOrganizationCreateResponse,
  TeacherLookupResponse,
} from "@/types/admin";

export default function CreateOrganization() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const redirectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [ownerInfo, setOwnerInfo] = useState<{
    name: string;
    phone: string | null;
    email_verified: boolean;
  } | null>(null);
  const [ownerLookupError, setOwnerLookupError] = useState("");
  const [staffEmailInput, setStaffEmailInput] = useState("");
  const [formData, setFormData] = useState<AdminOrganizationCreateRequest>({
    name: "",
    display_name: "",
    description: "",
    tax_id: "",
    teacher_limit: undefined,
    contact_email: "",
    contact_phone: "",
    address: "",
    owner_email: "",
    project_staff_emails: [],
  });

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (redirectTimeoutRef.current) {
        clearTimeout(redirectTimeoutRef.current);
      }
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  // Email validation helper
  const isValidEmail = (email: string): boolean => {
    // Simple but effective email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Actual API lookup function
  const performLookup = useCallback(async (email: string) => {
    if (!email || !isValidEmail(email)) {
      setOwnerInfo(null);
      setOwnerLookupError("");
      return;
    }

    try {
      const response = await apiClient.get<TeacherLookupResponse>(
        `/api/admin/teachers/lookup?email=${encodeURIComponent(email)}`
      );
      setOwnerInfo({
        name: response.name,
        phone: response.phone,
        email_verified: response.email_verified,
      });
      setOwnerLookupError("");

      // Show warning if not verified
      if (!response.email_verified) {
        setOwnerLookupError("警告：此教師尚未驗證 Email");
      }
    } catch (err) {
      setOwnerInfo(null);
      console.error("Owner lookup error:", err); // Log error details for debugging

      // ApiError has status property directly
      if (err && typeof err === "object" && "status" in err) {
        const apiError = err as { status?: number; message?: string };
        if (apiError.status === 404) {
          setOwnerLookupError("此 Email 尚未註冊");
        } else {
          // Preserve error details in the message
          const errorMsg = apiError.message
            ? `查詢失敗: ${apiError.message}`
            : `查詢失敗 (HTTP ${apiError.status || "Unknown"})`;
          setOwnerLookupError(errorMsg);
        }
      } else {
        setOwnerLookupError("查詢失敗：網路錯誤");
      }
    }
  }, []);

  // Debounced lookup wrapper (300ms delay)
  const lookupOwner = useCallback((email: string) => {
    // Clear previous timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Set new timeout
    debounceTimeoutRef.current = setTimeout(() => {
      performLookup(email);
    }, 300);
  }, [performLookup]);

  const addStaffEmail = () => {
    const email = staffEmailInput.trim().toLowerCase();
    if (!email || !isValidEmail(email)) {
      toast.error("請輸入有效的 Email 格式");
      return;
    }

    // Prevent duplicates (case-insensitive)
    if (formData.project_staff_emails?.some(e => e.toLowerCase() === email)) {
      toast.error("此 Email 已在列表中");
      return;
    }

    // Prevent adding owner as staff (case-insensitive)
    if (email === formData.owner_email.toLowerCase()) {
      toast.error("擁有人不能同時是專案服務人員");
      return;
    }

    setFormData({
      ...formData,
      project_staff_emails: [...(formData.project_staff_emails || []), email],
    });
    setStaffEmailInput("");
  };

  const removeStaffEmail = (email: string) => {
    setFormData({
      ...formData,
      project_staff_emails: formData.project_staff_emails?.filter(e => e !== email),
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Basic validation
    if (!formData.name || !formData.owner_email) {
      setError("機構名稱和擁有人 Email 為必填");
      return;
    }

    setIsLoading(true);

    try {
      // Prepare request data (remove empty strings)
      const requestData: AdminOrganizationCreateRequest = {
        name: formData.name,
        owner_email: formData.owner_email,
      };

      if (formData.display_name)
        requestData.display_name = formData.display_name;
      if (formData.description) requestData.description = formData.description;
      if (formData.tax_id) requestData.tax_id = formData.tax_id;
      if (formData.teacher_limit)
        requestData.teacher_limit = formData.teacher_limit;
      if (formData.contact_email)
        requestData.contact_email = formData.contact_email;
      if (formData.contact_phone)
        requestData.contact_phone = formData.contact_phone;
      if (formData.address) requestData.address = formData.address;

      // Add project staff if any
      if (formData.project_staff_emails && formData.project_staff_emails.length > 0) {
        requestData.project_staff_emails = formData.project_staff_emails;
      }

      const response = await apiClient.post<AdminOrganizationCreateResponse>(
        "/api/admin/organizations",
        requestData
      );

      toast.success(
        `機構創建成功！機構名稱：${response.organization_name}，擁有人：${response.owner_email}`
      );

      // Redirect to admin dashboard with cleanup
      redirectTimeoutRef.current = setTimeout(() => {
        navigate("/admin");
      }, 2000);
    } catch (err) {
      console.error("Failed to create organization:", err);

      // Type-safe error handling
      if (err && typeof err === "object" && "response" in err) {
        const apiError = err as {
          response?: { status?: number; data?: { detail?: string } };
        };

        if (apiError.response?.status === 403) {
          setError("權限不足：您必須是平台管理員才能創建機構");
        } else if (apiError.response?.status === 404) {
          setError(
            "找不到指定的擁有人 Email，請確認該用戶已註冊並完成驗證"
          );
        } else if (apiError.response?.status === 400) {
          setError(
            apiError.response.data?.detail || "創建失敗：機構名稱可能已存在"
          );
        } else {
          setError("創建機構失敗，請稍後再試");
        }
      } else {
        setError("創建機構失敗，請稍後再試");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">創建機構</h1>
        <p className="text-gray-600 mt-2">
          平台管理員可以創建新機構並指定已註冊的老師為機構擁有人
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>機構資訊</CardTitle>
          <CardDescription>請填寫機構的基本資訊和擁有人</CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">基本資訊</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">
                    機構英文名稱 <span className="text-red-500">*</span>
                  </Label>
                  <div className="relative">
                    <Building className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="name"
                      type="text"
                      placeholder="Example Organization"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      className="pl-10"
                      required
                      disabled={isLoading}
                      maxLength={100}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="display_name">機構顯示名稱（中文）</Label>
                  <Input
                    id="display_name"
                    type="text"
                    placeholder="範例機構"
                    value={formData.display_name}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        display_name: e.target.value,
                      })
                    }
                    disabled={isLoading}
                    maxLength={200}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">機構描述</Label>
                <Textarea
                  id="description"
                  placeholder="請輸入機構描述..."
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  disabled={isLoading}
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tax_id">統一編號</Label>
                  <div className="relative">
                    <Hash className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="tax_id"
                      type="text"
                      placeholder="12345678"
                      value={formData.tax_id}
                      onChange={(e) =>
                        setFormData({ ...formData, tax_id: e.target.value })
                      }
                      className="pl-10"
                      disabled={isLoading}
                      maxLength={20}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="teacher_limit">教師授權總數</Label>
                  <Input
                    id="teacher_limit"
                    type="number"
                    placeholder="10"
                    value={formData.teacher_limit || ""}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        teacher_limit: e.target.value
                          ? parseInt(e.target.value)
                          : undefined,
                      })
                    }
                    disabled={isLoading}
                    min={1}
                  />
                </div>
              </div>
            </div>

            {/* Contact Info Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">聯絡資訊</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="contact_email">聯絡 Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="contact_email"
                      type="email"
                      placeholder="contact@example.com"
                      value={formData.contact_email}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          contact_email: e.target.value,
                        })
                      }
                      className="pl-10"
                      disabled={isLoading}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="contact_phone">聯絡電話</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="contact_phone"
                      type="tel"
                      placeholder="02-12345678"
                      value={formData.contact_phone}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          contact_phone: e.target.value,
                        })
                      }
                      className="pl-10"
                      disabled={isLoading}
                      maxLength={50}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="address">地址</Label>
                <Input
                  id="address"
                  type="text"
                  placeholder="台北市..."
                  value={formData.address}
                  onChange={(e) =>
                    setFormData({ ...formData, address: e.target.value })
                  }
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Owner Assignment Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">機構擁有人</h3>

              <Alert>
                <AlertDescription>
                  請輸入已註冊並完成驗證的老師 Email。該老師將被指派為機構擁有人（org_owner）。
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <Label htmlFor="owner_email">
                  擁有人 Email <span className="text-red-500">*</span>
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="owner_email"
                    type="email"
                    placeholder="owner@example.com"
                    value={formData.owner_email}
                    onChange={(e) => {
                      setFormData({ ...formData, owner_email: e.target.value });
                      lookupOwner(e.target.value);
                    }}
                    className="pl-10"
                    required
                    disabled={isLoading}
                  />
                </div>
                {ownerInfo && (
                  <div className="mt-2 p-3 bg-blue-50 rounded-md border border-blue-200">
                    <p className="text-sm font-medium text-blue-900">教師資訊</p>
                    <p className="text-sm text-blue-700 mt-1">
                      姓名：{ownerInfo.name}
                    </p>
                    {ownerInfo.phone && (
                      <p className="text-sm text-blue-700">
                        手機：{ownerInfo.phone}
                      </p>
                    )}
                    {ownerInfo.email_verified && (
                      <p className="text-xs text-green-600 mt-1">✓ Email 已驗證</p>
                    )}
                  </div>
                )}
                {ownerLookupError && (
                  <p className="text-sm text-amber-600 mt-1">
                    {ownerLookupError}
                  </p>
                )}
                <p className="text-sm text-gray-500">
                  請確認該 Email 已在平台註冊並完成驗證
                </p>
              </div>
            </div>

            {/* Project Staff Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">專案服務人員（可選）</h3>

              <Alert>
                <AlertDescription>
                  專案服務人員將被指派為 org_admin 角色，協助管理機構。可加入多位服務人員。
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <Label htmlFor="staff_email">服務人員 Email</Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="staff_email"
                      type="email"
                      placeholder="staff@duotopia.com"
                      value={staffEmailInput}
                      onChange={(e) => setStaffEmailInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addStaffEmail();
                        }
                      }}
                      className="pl-10"
                      disabled={isLoading}
                    />
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={addStaffEmail}
                    disabled={isLoading || !staffEmailInput}
                  >
                    新增
                  </Button>
                </div>
              </div>

              {formData.project_staff_emails && formData.project_staff_emails.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">已加入的服務人員（{formData.project_staff_emails.length}）</p>
                  <div className="space-y-2">
                    {formData.project_staff_emails.map((email) => (
                      <div
                        key={email}
                        className="flex items-center justify-between p-2 bg-gray-50 rounded-md border"
                      >
                        <span className="text-sm">{email}</span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeStaffEmail(email)}
                          disabled={isLoading}
                        >
                          移除
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-4 pt-4">
              <Button type="submit" disabled={isLoading}>
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isLoading ? "創建中..." : "創建機構"}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/admin/organizations")}
                disabled={isLoading}
              >
                取消
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
