import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { API_URL } from "@/config/api";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import { OrganizationEditDialog } from "@/components/organization/OrganizationEditDialog";
import { SchoolCreateDialog } from "@/components/organization/SchoolCreateDialog";
import { SchoolEditDialog } from "@/components/organization/SchoolEditDialog";
import { AssignPrincipalDialog } from "@/components/organization/AssignPrincipalDialog";
import { InviteTeacherDialog } from "@/components/organization/InviteTeacherDialog";
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
import {
  Edit2,
  Plus,
  Building2,
  School as SchoolIcon,
  UserPlus,
  Users,
} from "lucide-react";

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
  principal_name?: string;
  principal_email?: string;
}

interface Teacher {
  id: number;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export default function OrganizationEditPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const navigate = useNavigate();
  const token = useTeacherAuthStore((state) => state.token);
  const { setSelectedNode, setExpandedOrgs, refreshSchools } =
    useOrganization();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [schools, setSchools] = useState<School[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [createSchoolDialogOpen, setCreateSchoolDialogOpen] = useState(false);
  const [editSchoolDialogOpen, setEditSchoolDialogOpen] = useState(false);
  const [assignPrincipalDialogOpen, setAssignPrincipalDialogOpen] =
    useState(false);
  const [inviteTeacherDialogOpen, setInviteTeacherDialogOpen] = useState(false);
  const [selectedSchool, setSelectedSchool] = useState<School | null>(null);

  useEffect(() => {
    if (orgId) {
      fetchOrganization();
      fetchSchools();
      fetchTeachers();
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

        // Set selected node in sidebar tree
        setSelectedNode({ type: "organization", id: data.id, data });

        // Expand this organization in sidebar tree
        setExpandedOrgs((prev) => {
          const newExpanded = new Set([...prev, data.id]);
          return Array.from(newExpanded);
        });
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
        },
      );

      if (response.ok) {
        const data = await response.json();

        // Fetch principal for each school
        const schoolsWithPrincipals = await Promise.all(
          data.map(async (school: School) => {
            try {
              const teachersResponse = await fetch(
                `${API_URL}/api/schools/${school.id}/teachers`,
                {
                  headers: { Authorization: `Bearer ${token}` },
                },
              );

              if (teachersResponse.ok) {
                const teachers = await teachersResponse.json();
                const principal = teachers.find(
                  (t: { name?: string; email?: string; roles?: string[] }) =>
                    t.roles?.includes("school_admin"),
                );

                return {
                  ...school,
                  principal_name: principal?.name,
                  principal_email: principal?.email,
                };
              }
            } catch (error) {
              console.error(
                `Failed to fetch principal for school ${school.id}:`,
                error,
              );
            }
            return school;
          }),
        );

        setSchools(schoolsWithPrincipals);
      }
    } catch (error) {
      console.error("Failed to fetch schools:", error);
    }
  };

  const fetchTeachers = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/organizations/${orgId}/teachers`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setTeachers(data);
      }
    } catch (error) {
      console.error("Failed to fetch teachers:", error);
    }
  };

  const handleEditSuccess = () => {
    fetchOrganization();
  };

  const handleSchoolCreateSuccess = useCallback(() => {
    fetchSchools();
    // Sync sidebar schools data in OrganizationContext
    if (orgId && token) {
      refreshSchools(token, orgId);
    }
  }, [orgId, token, refreshSchools]);

  const handleSchoolEditSuccess = useCallback(() => {
    fetchSchools();
    // Sync sidebar schools data in OrganizationContext
    if (orgId && token) {
      refreshSchools(token, orgId);
    }
  }, [orgId, token, refreshSchools]);

  const handleEditSchool = (school: School) => {
    setSelectedSchool(school);
    setEditSchoolDialogOpen(true);
  };

  const handleAssignPrincipal = (school: School) => {
    setSelectedSchool(school);
    setAssignPrincipalDialogOpen(true);
  };

  const handleAssignPrincipalSuccess = useCallback(() => {
    fetchSchools();
    // Sync sidebar schools data in OrganizationContext
    if (orgId && token) {
      refreshSchools(token, orgId);
    }
  }, [orgId, token, refreshSchools]);

  const handleInviteTeacherSuccess = () => {
    fetchTeachers();
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case "org_owner":
        return "bg-purple-100 text-purple-800";
      case "org_admin":
        return "bg-blue-100 text-blue-800";
      case "school_admin":
        return "bg-green-100 text-green-800";
      case "teacher":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case "org_owner":
        return "組織擁有者";
      case "org_admin":
        return "組織管理員";
      case "school_admin":
        return "學校管理員";
      case "teacher":
        return "教師";
      default:
        return role;
    }
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
    <div className="space-y-4">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[{ label: "組織管理" }, { label: organization.name }]}
      />

      {/* Organization Info Card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3 flex-1">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Building2 className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <CardTitle className="text-xl">{organization.name}</CardTitle>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      organization.is_active
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {organization.is_active ? "啟用" : "停用"}
                  </span>
                  <span className="text-sm text-gray-500">
                    建立時間：
                    {new Date(organization.created_at).toLocaleDateString(
                      "zh-TW",
                    )}
                  </span>
                </div>
                {organization.description && (
                  <p className="text-sm text-gray-600">
                    {organization.description}
                  </p>
                )}
              </div>
            </div>
            <Button
              onClick={() => setEditDialogOpen(true)}
              size="sm"
              className="gap-2 ml-4"
            >
              <Edit2 className="h-4 w-4" />
              編輯機構
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 pt-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {/* Owner - 優先顯示 */}
            {organization.owner_name && (
              <div className="col-span-2 p-3 bg-blue-50 rounded-lg">
                <h4 className="text-sm font-medium text-blue-900 mb-2">
                  機構 Owner
                </h4>
                <div className="flex items-center gap-4">
                  <div>
                    <p className="font-semibold text-blue-900">
                      {organization.owner_name}
                    </p>
                    {organization.owner_email && (
                      <p className="text-sm text-blue-700">
                        {organization.owner_email}
                      </p>
                    )}
                  </div>
                </div>
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
                <h4 className="text-sm font-medium text-gray-500 mb-1">地址</h4>
                <p className="text-gray-900">{organization.address}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Teachers/Staff Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-purple-100 rounded-lg">
              <Users className="h-4 w-4 text-purple-600" />
            </div>
            <CardTitle className="text-base">工作人員</CardTitle>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => setInviteTeacherDialogOpen(true)}
          >
            <UserPlus className="h-4 w-4" />
            新增工作人員
          </Button>
        </CardHeader>
        <CardContent className="pt-0">
          {teachers.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500 mb-2">尚無工作人員</p>
              <Button
                variant="outline"
                className="mt-4 gap-2"
                onClick={() => setInviteTeacherDialogOpen(true)}
              >
                <UserPlus className="h-4 w-4" />
                新增第一位工作人員
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>姓名</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>角色</TableHead>
                  <TableHead>狀態</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teachers.map((teacher) => (
                  <TableRow key={teacher.id}>
                    <TableCell className="font-medium">
                      {teacher.name}
                    </TableCell>
                    <TableCell>{teacher.email}</TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(
                          teacher.role,
                        )}`}
                      >
                        {getRoleLabel(teacher.role)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          teacher.is_active
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {teacher.is_active ? "啟用" : "停用"}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Schools Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-green-100 rounded-lg">
              <SchoolIcon className="h-4 w-4 text-green-600" />
            </div>
            <CardTitle className="text-base">學校列表</CardTitle>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => setCreateSchoolDialogOpen(true)}
          >
            <Plus className="h-4 w-4" />
            新增學校
          </Button>
        </CardHeader>
        <CardContent className="pt-0">
          {schools.length === 0 ? (
            <div className="text-center py-12">
              <SchoolIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500 mb-2">尚無學校</p>
              <Button
                variant="outline"
                className="mt-4 gap-2"
                onClick={() => setCreateSchoolDialogOpen(true)}
              >
                <Plus className="h-4 w-4" />
                新增第一個學校
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>學校名稱</TableHead>
                  <TableHead>聯絡信箱</TableHead>
                  <TableHead>校長</TableHead>
                  <TableHead>狀態</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schools.map((school) => (
                  <TableRow key={school.id}>
                    <TableCell className="font-medium">
                      <button
                        onClick={() =>
                          navigate(`/organization/schools/${school.id}`)
                        }
                        className="text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                      >
                        {school.display_name || school.name}
                      </button>
                    </TableCell>
                    <TableCell>{school.contact_email || "-"}</TableCell>
                    <TableCell>
                      {school.principal_name || (
                        <span className="text-gray-400 text-sm">未指派</span>
                      )}
                    </TableCell>
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
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleAssignPrincipal(school)}
                        >
                          <UserPlus className="h-4 w-4" />
                          指派校長
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditSchool(school)}
                        >
                          <Edit2 className="h-4 w-4" />
                          編輯
                        </Button>
                      </div>
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

      {/* Create School Dialog */}
      <SchoolCreateDialog
        organizationId={orgId!}
        open={createSchoolDialogOpen}
        onOpenChange={setCreateSchoolDialogOpen}
        onSuccess={handleSchoolCreateSuccess}
      />

      {/* Edit School Dialog */}
      <SchoolEditDialog
        school={selectedSchool}
        open={editSchoolDialogOpen}
        onOpenChange={setEditSchoolDialogOpen}
        onSuccess={handleSchoolEditSuccess}
      />

      {/* Assign Principal Dialog */}
      {selectedSchool && organization && (
        <AssignPrincipalDialog
          schoolId={selectedSchool.id}
          organizationId={organization.id}
          open={assignPrincipalDialogOpen}
          onOpenChange={setAssignPrincipalDialogOpen}
          onSuccess={handleAssignPrincipalSuccess}
        />
      )}

      {/* Invite Teacher Dialog */}
      <InviteTeacherDialog
        organizationId={orgId!}
        open={inviteTeacherDialogOpen}
        onOpenChange={setInviteTeacherDialogOpen}
        onSuccess={handleInviteTeacherSuccess}
      />
    </div>
  );
}
