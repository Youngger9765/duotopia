/**
 * Admin-related types
 */

export interface AdminOrganizationCreateRequest {
  name: string;
  display_name?: string;
  description?: string;
  tax_id?: string;
  teacher_limit?: number;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  owner_email: string;
  project_staff_emails?: string[];  // NEW
}

export interface AdminOrganizationCreateResponse {
  organization_id: string;
  organization_name: string;
  owner_email: string;
  owner_id: number;
  project_staff_assigned?: string[];  // NEW
  message: string;
}

// NEW: Teacher lookup response
export interface TeacherLookupResponse {
  id: number;
  email: string;
  name: string;
  phone: string | null;
  email_verified: boolean;
}

// NEW: Organization statistics response
export interface OrganizationStatisticsResponse {
  teacher_count: number;
  teacher_limit: number | null;
  usage_percentage: number;
}
