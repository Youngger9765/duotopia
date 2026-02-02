import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
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
import {
  OrganizationInfoCard,
  Organization,
  School,
  QuickActionsCards,
  SchoolsSection,
  StaffSection,
} from "@/pages/organization/OrganizationEditSections";
import { StaffMember } from "@/components/organization/StaffTable";

export default function OrganizationEditPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const token = useTeacherAuthStore((state) => state.token);
  const {
    setSelectedNode,
    setExpandedOrgs,
    refreshSchools,
    refreshOrganizations,
  } = useOrganization();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [schools, setSchools] = useState<School[]>([]);
  const [teachers, setTeachers] = useState<StaffMember[]>([]);
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
        const mappedSchools = data.map((school: School) => ({
          ...school,
          principal_name: school.principal_name ?? school.admin_name,
          principal_email: school.principal_email ?? school.admin_email,
        }));
        setSchools(mappedSchools);
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

  const handleEditSuccess = useCallback(() => {
    fetchOrganization();
    // Sync sidebar organization data in OrganizationContext
    if (token) {
      refreshOrganizations(token);
    }
  }, [token, refreshOrganizations]);

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

  // Role management is now handled by StaffTable component

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

      <OrganizationInfoCard
        organization={organization}
        onEdit={() => setEditDialogOpen(true)}
      />

      <QuickActionsCards
        orgId={orgId!}
        schoolsCount={schools.length}
        teachersCount={teachers.length}
      />

      <SchoolsSection
        orgId={orgId!}
        schools={schools}
        onCreate={() => setCreateSchoolDialogOpen(true)}
        onEdit={handleEditSchool}
        onAssignPrincipal={handleAssignPrincipal}
      />

      <StaffSection
        orgId={orgId!}
        teachers={teachers}
        onInvite={() => setInviteTeacherDialogOpen(true)}
        onRoleUpdated={fetchTeachers}
      />

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
