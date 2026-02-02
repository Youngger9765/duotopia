import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import { InviteTeacherToSchoolDialog } from "@/components/organization/InviteTeacherToSchoolDialog";
import {
  TeacherListTable,
  Teacher,
} from "@/components/organization/TeacherListTable";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Users, UserPlus } from "lucide-react";

interface School {
  id: string;
  name: string;
  organization_id: string;
}

interface Organization {
  id: string;
  name: string;
}

export default function SchoolTeachersPage() {
  const { schoolId } = useParams<{ schoolId: string }>();
  const token = useTeacherAuthStore((state) => state.token);

  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [school, setSchool] = useState<School | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);

  useEffect(() => {
    if (schoolId) {
      fetchSchool();
    }
  }, [schoolId]);

  const fetchSchool = async () => {
    try {
      const response = await fetch(`${API_URL}/api/schools/${schoolId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setSchool(data);
        fetchOrganization(data.organization_id);
        fetchTeachers();
      } else {
        setError(`載入學校失敗：${response.status}`);
      }
    } catch (error) {
      console.error("Failed to fetch school:", error);
      setError("網路連線錯誤");
    }
  };

  const fetchOrganization = async (orgId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/organizations/${orgId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setOrganization(data);
      }
    } catch (error) {
      console.error("Failed to fetch organization:", error);
    }
  };

  const fetchTeachers = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_URL}/api/schools/${schoolId}/teachers`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        const data = await response.json();

        // Sort teachers by role priority: school_admin > school_director > teacher
        const sortedTeachers = data.sort((a: Teacher, b: Teacher) => {
          const getRolePriority = (roles: string[]) => {
            if (roles.includes("school_admin")) return 1;
            if (roles.includes("school_director")) return 2;
            if (roles.includes("teacher")) return 3;
            return 4;
          };

          return getRolePriority(a.roles) - getRolePriority(b.roles);
        });

        setTeachers(sortedTeachers);
      } else {
        setError(`載入教師列表失敗：${response.status}`);
      }
    } catch (error) {
      console.error("Failed to fetch teachers:", error);
      setError("網路連線錯誤");
    } finally {
      setLoading(false);
    }
  };

  const handleInviteSuccess = () => {
    fetchTeachers();
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: "組織管理" },
          ...(organization
            ? [
                {
                  label: organization.name,
                  href: `/organization/${organization.id}`,
                },
              ]
            : []),
          ...(school
            ? [
                {
                  label: school.name,
                  href: `/organization/schools/${school.id}`,
                },
              ]
            : []),
          { label: "教師管理" },
        ]}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">教師管理</h1>
          <p className="text-gray-600 mt-2">
            {school?.name} - 管理學校內的所有教師
          </p>
        </div>
      </div>

      {/* Teachers Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-purple-100 rounded-lg">
              <Users className="h-4 w-4 text-purple-600" />
            </div>
            <CardTitle className="text-base">教師團隊</CardTitle>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => setInviteDialogOpen(true)}
          >
            <UserPlus className="h-4 w-4" />
            邀請教師
          </Button>
        </CardHeader>
        <CardContent className="pt-0">
          {loading ? (
            <LoadingSpinner />
          ) : error ? (
            <ErrorMessage message={error} onRetry={fetchTeachers} />
          ) : teachers.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500 mb-2">尚無教師</p>
              <p className="text-sm text-gray-400">點擊上方按鈕邀請教師加入</p>
            </div>
          ) : (
            <TeacherListTable
              teachers={teachers}
              schoolId={schoolId || ""}
              onRoleUpdated={fetchTeachers}
            />
          )}
        </CardContent>
      </Card>

      {/* Invite Teacher Dialog */}
      {school?.organization_id && (
        <InviteTeacherToSchoolDialog
          schoolId={school.id}
          organizationId={school.organization_id}
          open={inviteDialogOpen}
          onOpenChange={setInviteDialogOpen}
          onSuccess={handleInviteSuccess}
        />
      )}
    </div>
  );
}
