import { memo, useMemo } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { PermissionManager, Teacher } from "@/lib/permissions";
import {
  Shield,
  Users,
  Eye,
  Settings,
  BookOpen,
  CheckCircle2,
  XCircle,
} from "lucide-react";

interface PermissionSummaryProps {
  teacher: Teacher;
  showDetails?: boolean;
  compact?: boolean;
}

/**
 * Visual summary component displaying teacher permissions
 * Optimized with React.memo for better performance
 */
export const PermissionSummary = memo(function PermissionSummary({
  teacher,
  showDetails = true,
  compact = false,
}: PermissionSummaryProps) {
  const permissions = useMemo(
    () => PermissionManager.getAllPermissions(teacher),
    [teacher],
  );

  const isOrgOwner = useMemo(
    () => PermissionManager.isOrgOwner(teacher),
    [teacher],
  );

  const isSchoolAdmin = useMemo(
    () => PermissionManager.isSchoolAdmin(teacher),
    [teacher],
  );

  // Calculate permission score (percentage of permissions enabled) - memoized
  const permissionScore = useMemo(() => {
    const booleanPermissions = [
      permissions.can_create_classrooms,
      permissions.can_view_other_teachers,
      permissions.can_manage_students,
      permissions.can_view_all_classrooms,
      permissions.can_edit_school_settings,
    ];
    const enabledCount = booleanPermissions.filter(Boolean).length;
    return (enabledCount / booleanPermissions.length) * 100;
  }, [permissions]);

  const getScoreColor = (score: number): string => {
    if (score >= 80) return "text-green-600";
    if (score >= 50) return "text-orange-600";
    return "text-gray-600";
  };

  const getRoleBadge = () => {
    if (isOrgOwner) {
      return (
        <Badge variant="default" className="bg-purple-600">
          <Shield className="h-3 w-3 mr-1" />
          Organization Owner
        </Badge>
      );
    }
    if (isSchoolAdmin) {
      return (
        <Badge variant="default" className="bg-blue-600">
          <Shield className="h-3 w-3 mr-1" />
          School Admin
        </Badge>
      );
    }
    return (
      <Badge variant="secondary">
        <Users className="h-3 w-3 mr-1" />
        Teacher
      </Badge>
    );
  };

  if (compact) {
    return (
      <Card className="w-full">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="text-sm font-medium">{teacher.name}</div>
              {getRoleBadge()}
            </div>
            <div
              className={`text-2xl font-bold ${getScoreColor(permissionScore)}`}
            >
              {permissionScore.toFixed(0)}%
            </div>
          </div>
          <Progress value={permissionScore} className="h-2" />
        </CardContent>
      </Card>
    );
  }

  const permissionItems = [
    {
      icon: <BookOpen className="h-4 w-4" />,
      label: "Create Classrooms",
      enabled: permissions.can_create_classrooms,
      detail:
        permissions.max_classrooms === -1
          ? "Unlimited"
          : `Max: ${permissions.max_classrooms || 0}`,
    },
    {
      icon: <Users className="h-4 w-4" />,
      label: "View Other Teachers",
      enabled: permissions.can_view_other_teachers,
    },
    {
      icon: <Users className="h-4 w-4" />,
      label: "Manage Students",
      enabled: permissions.can_manage_students,
    },
    {
      icon: <Eye className="h-4 w-4" />,
      label: "View All Classrooms",
      enabled: permissions.can_view_all_classrooms,
    },
    {
      icon: <Settings className="h-4 w-4" />,
      label: "Edit School Settings",
      enabled: permissions.can_edit_school_settings,
    },
  ];

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{teacher.name}</CardTitle>
            <CardDescription>{teacher.email}</CardDescription>
          </div>
          {getRoleBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Permission Score */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Permission Level</span>
            <span
              className={`text-xl font-bold ${getScoreColor(permissionScore)}`}
            >
              {permissionScore.toFixed(0)}%
            </span>
          </div>
          <Progress value={permissionScore} className="h-2" />
        </div>

        {/* Detailed Permissions */}
        {showDetails && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">Permissions:</h4>
            <div className="space-y-1">
              {permissionItems.map((item, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={
                        item.enabled ? "text-green-600" : "text-gray-400"
                      }
                    >
                      {item.icon}
                    </div>
                    <span className="text-sm">{item.label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {item.detail && (
                      <span className="text-xs text-gray-500">
                        {item.detail}
                      </span>
                    )}
                    {item.enabled ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-gray-300" />
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Allowed Actions */}
            {permissions.allowed_actions &&
              permissions.allowed_actions.length > 0 && (
                <div className="pt-2 border-t">
                  <h4 className="text-sm font-semibold mb-2">
                    Allowed Actions:
                  </h4>
                  <div className="flex flex-wrap gap-1">
                    {permissions.allowed_actions.map((action, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {action}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
          </div>
        )}
      </CardContent>
    </Card>
  );
});
