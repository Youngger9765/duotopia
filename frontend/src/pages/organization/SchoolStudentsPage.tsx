import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { apiClient } from "@/lib/api";
import { logError } from "@/utils/errorLogger";
import { Breadcrumb } from "@/components/organization/Breadcrumb";
import { LoadingSpinner } from "@/components/organization/LoadingSpinner";
import { ErrorMessage } from "@/components/organization/ErrorMessage";
import { StudentListTable, Student } from "@/components/organization/StudentListTable";
import { CreateStudentDialog } from "@/components/organization/CreateStudentDialog";
import { AssignClassroomDialog } from "@/components/organization/AssignClassroomDialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Users, Plus, Search } from "lucide-react";
import { toast } from "sonner";

interface School {
  id: string;
  name: string;
  organization_id: string;
}

interface Organization {
  id: string;
  name: string;
}

export default function SchoolStudentsPage() {
  const { schoolId } = useParams<{ schoolId: string }>();
  const token = useTeacherAuthStore((state) => state.token);

  const [students, setStudents] = useState<Student[]>([]);
  const [school, setSchool] = useState<School | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (schoolId && token) {
      fetchSchool();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [schoolId]);

  const fetchSchool = async () => {
    if (!schoolId) return;

    try {
      const response = await fetch(`${apiClient.baseURL}/api/schools/${schoolId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setSchool(data);
        fetchOrganization(data.organization_id);
        fetchStudents();
      } else {
        setError(`載入學校失敗：${response.status}`);
      }
    } catch (error) {
      logError("Failed to fetch school", error, { schoolId });
      setError("網路連線錯誤");
    }
  };

  const fetchOrganization = async (orgId: string) => {
    try {
      const response = await fetch(`${apiClient.baseURL}/api/organizations/${orgId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setOrganization(data);
      }
    } catch (error) {
      logError("Failed to fetch organization", error, { orgId });
    }
  };

  const fetchStudents = async () => {
    if (!schoolId) return;

    try {
      setLoading(true);
      setError(null);

      const params: any = {};
      if (searchTerm) {
        params.search = searchTerm;
      }

      const data = await apiClient.getSchoolStudents(schoolId, params);
      setStudents(data);
    } catch (error) {
      logError("Failed to fetch students", error, { schoolId });
      setError("載入學生列表失敗");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (schoolId) {
      const debounceTimer = setTimeout(() => {
        fetchStudents();
      }, 300);

      return () => clearTimeout(debounceTimer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, schoolId]);

  const handleCreateSuccess = () => {
    fetchStudents();
  };

  const handleEdit = (student: Student) => {
    toast.info("編輯功能開發中");
    // TODO: 實現編輯對話框
  };

  const handleAssignClassroom = (student: Student) => {
    setSelectedStudent(student);
    setShowAssignDialog(true);
  };

  const handleRemove = async (studentId: number) => {
    if (!schoolId) return;

    if (!confirm("確定要將此學生從學校移除嗎？")) {
      return;
    }

    try {
      await apiClient.removeStudentFromSchool(schoolId, studentId);
      toast.success("學生已從學校移除");
      fetchStudents();
    } catch (error) {
      logError("Failed to remove student from school", error, { schoolId, studentId });
      toast.error("移除學生失敗，請稍後再試");
    }
  };

  if (loading && !students.length) {
    return <LoadingSpinner />;
  }

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
          { label: "學生管理" },
        ]}
      />

      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Users className="h-6 w-6 text-blue-600" />
              <CardTitle>
                {school?.name ? `${school.name} 的學生名冊` : "學生管理"}
              </CardTitle>
            </div>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              建立學生
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Search */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜尋學生（姓名、學號、Email）"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Error Message */}
          {error && <ErrorMessage message={error} />}

          {/* Student List */}
          {!loading && (
            <StudentListTable
              students={students}
              onEdit={handleEdit}
              onAssignClassroom={handleAssignClassroom}
              onRemove={handleRemove}
            />
          )}
        </CardContent>
      </Card>

      {/* Create Student Dialog */}
      <CreateStudentDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        schoolId={schoolId || ""}
        onSuccess={handleCreateSuccess}
      />

      {/* Assign Classroom Dialog */}
      {selectedStudent && schoolId && (
        <AssignClassroomDialog
          open={showAssignDialog}
          onOpenChange={setShowAssignDialog}
          student={selectedStudent}
          schoolId={schoolId}
          onSuccess={handleCreateSuccess}
        />
      )}
    </div>
  );
}

