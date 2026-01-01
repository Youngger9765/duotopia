import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import { OrganizationEditDialog } from "@/components/organization/OrganizationEditDialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Edit2, Plus, Building2, School as SchoolIcon } from "lucide-react";

interface Organization {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  owner_name?: string;
  owner_email?: string;
}

interface School {
  id: string;
  organization_id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
}

export default function OrganizationEditPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const token = useTeacherAuthStore((state) => state.token);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  useEffect(() => {
    if (orgId) {
      fetchOrganization();
      fetchSchools();
    }
  }, [orgId]);

  const fetchOrganization = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/organizations/${orgId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setOrganization(data);
      } else {
        setError(`載入機構失敗：${response.status}`);
      }
    } catch (error) {
      console.error("Failed to fetch organization:", error);
      setError("網路連線錯誤");
    } finally {
      setLoading(false);
    }
  };

  const fetchSchools = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/schools?organization_id=${orgId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setSchools(data);
      }
    } catch (error) {
      console.error("Failed to fetch schools:", error);
    }
  };

  const handleEditSuccess = () => {
    fetchOrganization();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !organization) {
    return (
      <div className="space-y-6">
        <ErrorMessage
          message={error || "找不到機構"}
          onRetry={fetchOrganization}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[{ label: "組織管理" }, { label: organization.name }]}
      />

      {/* Organization Info Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Building2 className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <CardTitle className="text-2xl">{organization.name}</CardTitle>
              {organization.display_name && (
                <p className="text-sm text-gray-500 mt-1">
                  {organization.display_name}
                </p>
              )}
            </div>
          </div>
          <Button onClick={() => setEditDialogOpen(true)} className="gap-2">
            <Edit2 className="h-4 w-4" />
            編輯機構
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Description */}
            {organization.description && (
              <div className="col-span-2">
                <h4 className="text-sm font-medium text-gray-500 mb-1">
                  描述
                </h4>
                <p className="text-gray-900">{organization.description}</p>
              </div>
            )}

            {/* Owner */}
            {organization.owner_name && (
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-1">
                  Owner
                </h4>
                <p className="text-gray-900">{organization.owner_name}</p>
                {organization.owner_email && (
                  <p className="text-sm text-gray-600">
                    {organization.owner_email}
                  </p>
                )}
              </div>
            )}

            {/* Contact Email */}
            {organization.contact_email && (
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-1">
                  聯絡信箱
                </h4>
                <p className="text-gray-900">{organization.contact_email}</p>
              </div>
            )}

            {/* Contact Phone */}
            {organization.contact_phone && (
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-1">
                  聯絡電話
                </h4>
                <p className="text-gray-900">{organization.contact_phone}</p>
              </div>
            )}

            {/* Address */}
            {organization.address && (
              <div className="col-span-2">
                <h4 className="text-sm font-medium text-gray-500 mb-1">
                  地址
                </h4>
                <p className="text-gray-900">{organization.address}</p>
              </div>
            )}

            {/* Status */}
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-1">狀態</h4>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  organization.is_active
                    ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {organization.is_active ? "啟用" : "停用"}
              </span>
            </div>

            {/* Created Date */}
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-1">
                建立時間
              </h4>
              <p className="text-gray-900">
                {new Date(organization.created_at).toLocaleDateString("zh-TW")}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Schools Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <SchoolIcon className="h-5 w-5 text-green-600" />
            </div>
            <CardTitle>學校列表</CardTitle>
          </div>
          <Button variant="outline" className="gap-2">
            <Plus className="h-4 w-4" />
            新增學校
          </Button>
        </CardHeader>
        <CardContent>
          {schools.length === 0 ? (
            <div className="text-center py-12">
              <SchoolIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500 mb-2">尚無學校</p>
              <Button variant="outline" className="mt-4 gap-2">
                <Plus className="h-4 w-4" />
                新增第一個學校
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>學校名稱</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead>聯絡信箱</TableHead>
                  <TableHead>狀態</TableHead>
                  <TableHead>建立時間</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schools.map((school) => (
                  <TableRow key={school.id}>
                    <TableCell className="font-medium">
                      {school.display_name || school.name}
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      {school.description || "-"}
                    </TableCell>
                    <TableCell>{school.contact_email || "-"}</TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          school.is_active
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {school.is_active ? "啟用" : "停用"}
                      </span>
                    </TableCell>
                    <TableCell>
                      {new Date(school.created_at).toLocaleDateString("zh-TW")}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        <Edit2 className="h-4 w-4" />
                        編輯
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Edit Organization Dialog */}
      <OrganizationEditDialog
        organization={organization}
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        onSuccess={handleEditSuccess}
      />
    </div>
  );
}
