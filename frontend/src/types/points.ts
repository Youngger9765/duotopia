export interface PointsBalance {
  organization_id: string;
  total_points: number;
  used_points: number;
  remaining_points: number;
  last_points_update: string | null;
}

export interface PointsLogItem {
  id: number;
  organization_id: string;
  teacher_id: number | null;
  teacher_name: string | null;
  points_used: number;
  feature_type: string | null;
  description: string | null;
  created_at: string;
}

export interface PointsHistory {
  items: PointsLogItem[];
  total: number;
  limit: number;
  offset: number;
}
