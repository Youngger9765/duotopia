import { useState, useRef, useEffect } from "react";
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
} from "@/types/admin";

export default function CreateOrganization() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const redirectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
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
  });

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (redirectTimeoutRef.current) {
        clearTimeout(redirectTimeoutRef.current);
      }
    };
  }, []);

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

      const response = await apiClient.post<AdminOrganizationCreateResponse>(
        "/api/admin/organizations",
        requestData
      );

      toast.success(
        `機構創建成功！機構名稱：${response.organization_name}，擁有人：${response.owner_email}`
      );

      // Redirect to organizations list with cleanup
      redirectTimeoutRef.current = setTimeout(() => {
        navigate("/admin/organizations");
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
                    onChange={(e) =>
                      setFormData({ ...formData, owner_email: e.target.value })
                    }
                    className="pl-10"
                    required
                    disabled={isLoading}
                  />
                </div>
                <p className="text-sm text-gray-500">
                  請確認該 Email 已在平台註冊並完成驗證
                </p>
              </div>
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
