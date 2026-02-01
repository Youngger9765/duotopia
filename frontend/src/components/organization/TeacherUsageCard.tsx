import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { OrganizationStatisticsResponse } from "@/types/admin";

interface TeacherUsageCardProps {
  organizationId: string;
}

export default function TeacherUsageCard({ organizationId }: TeacherUsageCardProps) {
  const [stats, setStats] = useState<OrganizationStatisticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get<OrganizationStatisticsResponse>(
          `/api/admin/organizations/${organizationId}/statistics`
        );
        setStats(response);
        setError("");
      } catch (err) {
        console.error("Failed to fetch teacher statistics:", err);
        setError("無法載入教師統計");
      } finally {
        setLoading(false);
      }
    };

    if (organizationId) {
      fetchStats();
    }
  }, [organizationId]);

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-6">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        </CardContent>
      </Card>
    );
  }

  if (error || !stats) {
    return (
      <Card>
        <CardContent className="py-6">
          <p className="text-sm text-red-600">{error || "載入失敗"}</p>
        </CardContent>
      </Card>
    );
  }

  const isUnlimited = stats.teacher_limit === null;
  const isNearLimit = !isUnlimited && stats.usage_percentage >= 80;
  const isAtLimit = !isUnlimited && stats.usage_percentage >= 100;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">教師授權使用</CardTitle>
        <Users className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {stats.teacher_count} {!isUnlimited && `/ ${stats.teacher_limit}`}
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {isUnlimited ? (
            "無限制"
          ) : (
            <>
              使用率 {stats.usage_percentage.toFixed(1)}%
              {isAtLimit && <span className="text-red-600 ml-2">已達上限</span>}
              {isNearLimit && !isAtLimit && (
                <span className="text-amber-600 ml-2">接近上限</span>
              )}
            </>
          )}
        </p>
      </CardContent>
    </Card>
  );
}
