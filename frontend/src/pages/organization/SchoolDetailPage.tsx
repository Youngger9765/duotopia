import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useOrganization } from "@/contexts/OrganizationContext";
import { API_URL } from "@/config/api";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import { SchoolEditDialog } from "@/components/organization/SchoolEditDialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Edit2, School as SchoolIcon, Users, BookOpen, ArrowRight, GraduationCap, UserCheck } from "lucide-react";

interface School {
  id: string;
  organization_id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

interface Organization {
  id: string;
  name: string;
}

interface Teacher {
  id: number;
  email: string;
  name: string;
  roles: string[];
  is_active: boolean;
  created_at: string;
}

interface Classroom {
  id: string;
  name: string;
  program_level: string;
  is_active: boolean;
  created_at: string;
  teacher_name: string | null;
  teacher_email: string | null;
  student_count: number;
  assignment_count: number;
}

export default function SchoolDetailPage() {
  const { schoolId } = useParams<{ schoolId: string }>();
  const navigate = useNavigate();
  const token = useTeacherAuthStore((state) => state.token);
  const { setSelectedNode, setExpandedOrgs } = useOrganization();
  const [school, setSchool] = useState<School | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  useEffect(() => {
    if (schoolId) {
      fetchSchool();
    }
  }, [schoolId]);

  const fetchSchool = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/schools/${schoolId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setSchool(data);

        // Set selected node in sidebar tree
        setSelectedNode({ type: "school", id: data.id, data });

        // Expand parent organization in sidebar tree
        setExpandedOrgs((prev) => {
          const newExpanded = new Set([...prev, data.organization_id]);
          return Array.from(newExpanded);
        });

        // Fetch organization info, teachers, and classrooms
        fetchOrganization(data.organization_id);
        fetchTeachers();
        fetchClassrooms();
      } else {
        setError(`載入學校失敗：${response.status}`);
      }
    } catch (error) {
      console.error("Failed to fetch school:", error);
      setError("網路連線錯誤");
    } finally {
      setLoading(false);
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
      }
    } catch (error) {
      console.error("Failed to fetch teachers:", error);
    }
  };

  const fetchClassrooms = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/schools/${schoolId}/classrooms`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setClassrooms(data);
      }
    } catch (error) {
      console.error("Failed to fetch classrooms:", error);
    }
  };

  const getPrincipal = () => {
    return teachers.find((t) => t.roles.includes("school_admin"));
  };

  const handleEditSuccess = () => {
    fetchSchool();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !school) {
    return (
      <div className="space-y-6">
        <ErrorMessage message={error || "找不到學校"} onRetry={fetchSchool} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
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
          { label: school.name },
        ]}
      />

      {/* School Info Card - Compact layout like Organization */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3 flex-1">
              <div className="p-2 bg-green-100 rounded-lg">
                <SchoolIcon className="h-5 w-5 text-green-600" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <CardTitle className="text-xl">{school.name}</CardTitle>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      school.is_active
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {school.is_active ? "啟用" : "停用"}
                  </span>
                  <span className="text-sm text-gray-500">
                    建立時間：
                    {new Date(school.created_at).toLocaleDateString("zh-TW")}
                  </span>
                  {(() => {
                    const principal = getPrincipal();
                    return principal ? (
                      <span className="text-sm text-gray-500">
                        | 校長：{principal.name}
                      </span>
                    ) : null;
                  })()}
                </div>
                {school.description && (
                  <p className="text-sm text-gray-600">{school.description}</p>
                )}
              </div>
            </div>
            <Button
              onClick={() => setEditDialogOpen(true)}
              size="sm"
              className="gap-2 ml-4"
            >
              <Edit2 className="h-4 w-4" />
              編輯學校
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 pt-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {/* Organization */}
            {organization && (
              <div className="col-span-2 p-3 bg-green-50 rounded-lg">
                <h4 className="text-sm font-medium text-green-900 mb-2">
                  所屬機構
                </h4>
                <button
                  onClick={() => navigate(`/organization/${organization.id}`)}
                  className="text-green-700 hover:text-green-900 hover:underline transition-colors font-semibold"
                >
                  {organization.name}
                </button>
              </div>
            )}

            {/* Contact Info */}
            {school.contact_email && (
              <div className="p-2 bg-gray-50 rounded-lg">
                <h4 className="text-xs font-medium text-gray-500 mb-1">
                  聯絡信箱
                </h4>
                <p className="text-sm text-gray-900">{school.contact_email}</p>
              </div>
            )}

            {school.contact_phone && (
              <div className="p-2 bg-gray-50 rounded-lg">
                <h4 className="text-xs font-medium text-gray-500 mb-1">
                  聯絡電話
                </h4>
                <p className="text-sm text-gray-900">{school.contact_phone}</p>
              </div>
            )}

            {school.address && (
              <div className="col-span-2 p-2 bg-gray-50 rounded-lg">
                <h4 className="text-xs font-medium text-gray-500 mb-1">地址</h4>
                <p className="text-sm text-gray-900">{school.address}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="hover:shadow-md transition-shadow cursor-pointer">
          <CardContent
            className="p-6"
            onClick={() => navigate(`/organization/schools/${schoolId}/classrooms`)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-100 rounded-lg">
                  <GraduationCap className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">班級管理</h3>
                  <p className="text-sm text-gray-500">{classrooms.length} 個班級</p>
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-gray-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer">
          <CardContent
            className="p-6"
            onClick={() => navigate(`/organization/schools/${schoolId}/teachers`)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Users className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">教師管理</h3>
                  <p className="text-sm text-gray-500">{teachers.length} 位教師</p>
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-gray-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer">
          <CardContent
            className="p-6"
            onClick={() => navigate(`/organization/schools/${schoolId}/materials`)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <BookOpen className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">學校教材</h3>
                  <p className="text-sm text-gray-500">教材與課程</p>
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-gray-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer">
          <CardContent
            className="p-6"
            onClick={() => navigate(`/organization/schools/${schoolId}/students`)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <UserCheck className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">學生管理</h3>
                  <p className="text-sm text-gray-500">學生名冊</p>
                </div>
              </div>
              <ArrowRight className="h-5 w-5 text-gray-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Edit School Dialog */}
      <SchoolEditDialog
        school={school}
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        onSuccess={handleEditSuccess}
      />

    </div>
  );
}
