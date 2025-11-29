import { ReactNode } from 'react';
import { PermissionManager, Teacher, TeacherPermissions } from '@/lib/permissions';

interface PermissionGateProps {
  teacher: Teacher | null;
  permission?: keyof TeacherPermissions;
  action?: string;
  requireOrgOwner?: boolean;
  requireSchoolAdmin?: boolean;
  fallback?: ReactNode;
  children: ReactNode;
}

/**
 * Conditional rendering component based on permissions
 * Only renders children if permission check passes
 */
export function PermissionGate({
  teacher,
  permission,
  action,
  requireOrgOwner = false,
  requireSchoolAdmin = false,
  fallback = null,
  children,
}: PermissionGateProps) {
  // Check org owner requirement
  if (requireOrgOwner && !PermissionManager.isOrgOwner(teacher)) {
    return <>{fallback}</>;
  }

  // Check school admin requirement
  if (requireSchoolAdmin && !PermissionManager.isSchoolAdmin(teacher)) {
    return <>{fallback}</>;
  }

  // Check specific permission
  if (permission && !PermissionManager.hasPermission(teacher, permission)) {
    return <>{fallback}</>;
  }

  // Check action permission
  if (action && !PermissionManager.canPerformAction(teacher, action)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
