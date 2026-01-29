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
}

export interface AdminOrganizationCreateResponse {
  organization_id: string;
  organization_name: string;
  owner_email: string;
  owner_id: number;
  message: string;
}
