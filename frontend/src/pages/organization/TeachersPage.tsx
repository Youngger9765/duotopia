import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { API_URL } from "@/config/api";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
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
import { Users, UserPlus, Mail } from "lucide-react";
import { toast } from "sonner";

interface TeacherInfo {
  id: number;
  email: string;
  name: string;
  role: string; // Organization role: org_owner, org_admin, school_admin, teacher
  is_active: boolean;
  created_at: string;
}

/**
 * TeachersPage - Manage teachers within the organization portal
 */
export default function TeachersPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const token = useTeacherAuthStore((state) => state.token);
  const { selectedNode } = useOrganization();

  const [teachers, setTeachers] = useState<TeacherInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const effectiveOrgId =
    orgId ||
    (selectedNode?.type === "organization" ? selectedNode.id : undefined);

  useEffect(() => {
    if (effectiveOrgId) {
      fetchTeachers();
    }
  }, [effectiveOrgId]);

  const fetchTeachers = async () => {
    if (!effectiveOrgId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_URL}/api/organizations/${effectiveOrgId}/teachers`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setTeachers(data);
      } else {
        setError(`載入教師列表失敗：${response.status}`);
        toast.error("載入教師列表失敗");
      }
    } catch (error) {
      console.error("Failed to fetch teachers:", error);
      setError("網路連線錯誤，請檢查您的網路連線");
      toast.error("網路錯誤");
    } finally {
      setLoading(false);
    }
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

  if (!effectiveOrgId) {
    return (
      <div className="p-8 text-center">
        <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <p className="text-gray-500">請先選擇組織</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb items={[{ label: "組織管理" }, { label: "教師管理" }]} />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">教師管理</h1>
          <p className="text-gray-600 mt-2">管理組織內的教師成員</p>
        </div>
        <Button className="gap-2">
          <UserPlus className="h-4 w-4" />
          邀請教師
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              總教師數
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{teachers.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              活躍教師
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {teachers.filter((t) => t.is_active).length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              管理員
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {
                teachers.filter((t) =>
                  ["org_owner", "org_admin", "school_admin"].includes(t.role),
                ).length
              }
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Teachers Table */}
      <Card>
        <CardHeader>
          <CardTitle>教師列表</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <LoadingSpinner />
          ) : error ? (
            <ErrorMessage message={error} onRetry={fetchTeachers} />
          ) : teachers.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500 mb-2">此組織尚無教師</p>
              <Button
                variant="outline"
                onClick={() => toast.info("邀請教師功能開發中")}
                className="mt-4 gap-2"
              >
                <UserPlus className="h-4 w-4" />
                邀請第一位教師
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>姓名</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>組織角色</TableHead>
                  <TableHead>加入時間</TableHead>
                  <TableHead>狀態</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teachers.map((teacher) => (
                  <TableRow key={teacher.id}>
                    <TableCell className="font-medium">
                      {teacher.name}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-gray-400" />
                        {teacher.email}
                      </div>
                    </TableCell>
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
                      {new Date(teacher.created_at).toLocaleDateString("zh-TW")}
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
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        編輯權限
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
