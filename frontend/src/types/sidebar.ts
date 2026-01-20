/**
 * Sidebar 相關類型定義
 */

export interface SidebarItem {
  id: string;
  label: string;
  icon: React.ElementType;
  path: string;
  adminOnly?: boolean;
  requiredRoles?: string[]; // org_owner, org_admin, school_admin, teacher
}

export interface SidebarGroup {
  id: string;
  label: string;
  icon: React.ElementType;
  items: SidebarItem[];
  requiredRoles?: string[]; // If set, only show this group to users with these roles
}

export interface TeacherRolesResponse {
  teacher_id: number;
  organization_roles: Array<{
    organization_id: string;
    organization_name: string;
    role: string;
  }>;
  school_roles: Array<{
    school_id: string;
    school_name: string;
    organization_id: string;
    organization_name: string;
    roles: string[];
  }>;
  all_roles: string[];
}
