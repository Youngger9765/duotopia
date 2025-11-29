/**
 * Permission Management Utilities
 * Handles teacher permission checking and management for multi-tenant organization hierarchy
 */

export interface TeacherPermissions {
  can_create_classrooms?: boolean;
  can_view_other_teachers?: boolean;
  can_manage_students?: boolean;
  can_view_all_classrooms?: boolean;
  can_edit_school_settings?: boolean;
  max_classrooms?: number;
  allowed_actions?: string[];
}

export interface Teacher {
  id: number;
  email: string;
  name: string;
  is_org_owner?: boolean;
  is_school_admin?: boolean;
  permissions?: TeacherPermissions;
  organization_id?: string;
  school_ids?: string[];
}

/**
 * Permission Template Definitions
 */
export const PERMISSION_TEMPLATES = {
  ORGANIZATION_ADMIN: {
    name: "Organization Admin",
    description: "Full administrative access across all schools",
    permissions: {
      can_create_classrooms: true,
      can_view_other_teachers: true,
      can_manage_students: true,
      can_view_all_classrooms: true,
      can_edit_school_settings: true,
      max_classrooms: -1, // unlimited
      allowed_actions: ["*"] as string[], // all actions
    } as TeacherPermissions,
  },
  SCHOOL_ADMIN: {
    name: "School Admin",
    description: "Administrative access within assigned schools",
    permissions: {
      can_create_classrooms: true,
      can_view_other_teachers: true,
      can_manage_students: true,
      can_view_all_classrooms: true,
      can_edit_school_settings: true,
      max_classrooms: -1,
      allowed_actions: [
        "manage_classrooms",
        "manage_students",
        "view_reports",
        "manage_teachers",
      ] as string[],
    } as TeacherPermissions,
  },
  SENIOR_TEACHER: {
    name: "Senior Teacher",
    description: "Create and manage classrooms, view other teachers",
    permissions: {
      can_create_classrooms: true,
      can_view_other_teachers: true,
      can_manage_students: true,
      can_view_all_classrooms: true,
      can_edit_school_settings: false,
      max_classrooms: 10,
      allowed_actions: [
        "create_classroom",
        "manage_own_classrooms",
        "view_other_classrooms",
        "manage_students",
      ] as string[],
    } as TeacherPermissions,
  },
  TEACHER: {
    name: "Teacher",
    description: "Basic classroom management",
    permissions: {
      can_create_classrooms: true,
      can_view_other_teachers: false,
      can_manage_students: true,
      can_view_all_classrooms: false,
      can_edit_school_settings: false,
      max_classrooms: 5,
      allowed_actions: [
        "create_classroom",
        "manage_own_classrooms",
        "manage_students",
      ] as string[],
    } as TeacherPermissions,
  },
  LIMITED_TEACHER: {
    name: "Limited Teacher",
    description: "View-only with specific classroom access",
    permissions: {
      can_create_classrooms: false,
      can_view_other_teachers: false,
      can_manage_students: false,
      can_view_all_classrooms: false,
      can_edit_school_settings: false,
      max_classrooms: 0,
      allowed_actions: [
        "view_assigned_classrooms",
        "view_students",
      ] as string[],
    } as TeacherPermissions,
  },
  CUSTOM: {
    name: "Custom",
    description: "Fully customizable permissions",
    permissions: {
      can_create_classrooms: false,
      can_view_other_teachers: false,
      can_manage_students: false,
      can_view_all_classrooms: false,
      can_edit_school_settings: false,
      max_classrooms: 0,
      allowed_actions: [] as string[],
    } as TeacherPermissions,
  },
};

export type PermissionTemplateName = keyof typeof PERMISSION_TEMPLATES;

/**
 * Permission Manager Class
 */
export class PermissionManager {
  /**
   * Check if teacher has a specific permission
   */
  static hasPermission(
    teacher: Teacher | null,
    permission: keyof TeacherPermissions,
  ): boolean {
    if (!teacher) return false;

    // Organization owners have all permissions
    if (this.isOrgOwner(teacher)) return true;

    // School admins have all permissions within their schools
    if (
      this.isSchoolAdmin(teacher) &&
      permission !== "can_edit_school_settings"
    ) {
      return true;
    }

    // Check explicit permission
    return teacher.permissions?.[permission] === true;
  }

  /**
   * Check if teacher can perform a specific action
   */
  static canPerformAction(teacher: Teacher | null, action: string): boolean {
    if (!teacher) return false;

    // Organization owners can perform all actions
    if (this.isOrgOwner(teacher)) return true;

    const allowedActions = teacher.permissions?.allowed_actions || [];

    // Check for wildcard permission
    if (allowedActions.includes("*")) return true;

    // Check for specific action
    return allowedActions.includes(action);
  }

  /**
   * Get all permissions for a teacher
   */
  static getAllPermissions(teacher: Teacher | null): TeacherPermissions {
    if (!teacher) {
      return {
        can_create_classrooms: false,
        can_view_other_teachers: false,
        can_manage_students: false,
        can_view_all_classrooms: false,
        can_edit_school_settings: false,
        max_classrooms: 0,
        allowed_actions: [],
      };
    }

    // Organization owners get all permissions
    if (this.isOrgOwner(teacher)) {
      return PERMISSION_TEMPLATES.ORGANIZATION_ADMIN.permissions;
    }

    // School admins get school admin permissions
    if (this.isSchoolAdmin(teacher)) {
      return PERMISSION_TEMPLATES.SCHOOL_ADMIN.permissions;
    }

    // Return teacher's explicit permissions or default
    return (
      teacher.permissions || PERMISSION_TEMPLATES.LIMITED_TEACHER.permissions
    );
  }

  /**
   * Check if teacher is organization owner
   */
  static isOrgOwner(teacher: Teacher | null): boolean {
    return teacher?.is_org_owner === true;
  }

  /**
   * Check if teacher is school admin
   */
  static isSchoolAdmin(teacher: Teacher | null): boolean {
    return teacher?.is_school_admin === true;
  }

  /**
   * Check if teacher can create more classrooms
   */
  static canCreateClassroom(
    teacher: Teacher | null,
    currentClassroomCount: number,
  ): boolean {
    if (!teacher) return false;

    // Check basic permission
    if (!this.hasPermission(teacher, "can_create_classrooms")) {
      return false;
    }

    const maxClassrooms = teacher.permissions?.max_classrooms || 0;

    // -1 means unlimited
    if (maxClassrooms === -1) return true;

    // Check against limit
    return currentClassroomCount < maxClassrooms;
  }

  /**
   * Get permission template by name
   */
  static getTemplate(templateName: PermissionTemplateName): TeacherPermissions {
    return PERMISSION_TEMPLATES[templateName].permissions;
  }

  /**
   * Apply permission template to teacher
   */
  static applyTemplate(
    templateName: PermissionTemplateName,
  ): TeacherPermissions {
    return { ...this.getTemplate(templateName) };
  }

  /**
   * Get user-friendly permission description
   */
  static getPermissionDescription(
    permission: keyof TeacherPermissions,
  ): string {
    const descriptions: Record<keyof TeacherPermissions, string> = {
      can_create_classrooms: "Create new classrooms",
      can_view_other_teachers: "View other teachers in the organization",
      can_manage_students: "Add, edit, and remove students",
      can_view_all_classrooms: "View all classrooms in assigned schools",
      can_edit_school_settings: "Edit school settings and configuration",
      max_classrooms: "Maximum number of classrooms (-1 for unlimited)",
      allowed_actions: "List of allowed actions",
    };

    return descriptions[permission] || permission;
  }

  /**
   * Validate permission object
   */
  static validatePermissions(
    permissions: Partial<TeacherPermissions>,
  ): boolean {
    // Check if max_classrooms is valid
    if (
      permissions.max_classrooms !== undefined &&
      permissions.max_classrooms !== -1 &&
      permissions.max_classrooms < 0
    ) {
      return false;
    }

    // If can't create classrooms, max should be 0
    if (
      permissions.can_create_classrooms === false &&
      (permissions.max_classrooms || 0) > 0
    ) {
      return false;
    }

    return true;
  }

  /**
   * Merge permissions (useful for combining role-based and custom permissions)
   */
  static mergePermissions(
    base: TeacherPermissions,
    override: Partial<TeacherPermissions>,
  ): TeacherPermissions {
    return {
      ...base,
      ...override,
      allowed_actions: [
        ...(base.allowed_actions || []),
        ...(override.allowed_actions || []),
      ],
    };
  }

  /**
   * Check if permission set is more restrictive
   */
  static isMoreRestrictive(
    permissions1: TeacherPermissions,
    permissions2: TeacherPermissions,
  ): boolean {
    const p1 = permissions1;
    const p2 = permissions2;

    // Count permissions
    const count1 = Object.values(p1).filter((v) => v === true).length;
    const count2 = Object.values(p2).filter((v) => v === true).length;

    return count1 < count2;
  }
}
