import { Content } from "@/types";

export interface OrganizationLesson {
  id?: number;
  name: string;
  description?: string;
  order_index?: number;
  estimated_minutes?: number;
  program_id?: number;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  contents?: Content[];
}

export interface OrganizationProgram {
  id: number;
  organization_id: string;
  name: string;
  description?: string;
  level?: string;
  estimated_hours?: number;
  total_hours?: number;
  tags?: string[];
  is_template?: boolean;
  is_active: boolean;
  classroom_id?: number;
  teacher_id?: number;
  school_id?: string;
  source_type?: string;
  source_metadata?: Record<string, unknown>;
  classroom_name?: string;
  teacher_name?: string;
  lesson_count?: number;
  is_duplicate?: boolean;
  created_at: string;
  updated_at?: string;
  lessons?: OrganizationLesson[];
}
