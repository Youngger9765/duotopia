import { Content } from "@/types";

export interface OrganizationLesson {
  id?: number;
  name: string;
  description?: string;
  order_index?: number;
  estimated_minutes?: number;
  program_id?: number;
  contents?: Content[];
}

export interface OrganizationProgram {
  id: number;
  organization_id: string;
  name: string;
  description?: string;
  level?: string;
  total_hours?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  lessons?: OrganizationLesson[];
}
