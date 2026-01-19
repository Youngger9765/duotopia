import { memo } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Shield, Users, Building2, GraduationCap } from "lucide-react";

interface PermissionRow {
  operation: string;
  displayName: string;
  description: string;
  org_owner: boolean | string;
  org_admin: boolean | string;
  school_admin: boolean | string;
  teacher: boolean | string;
}

const PERMISSION_DATA: PermissionRow[] = [
  {
    operation: "create:school",
    displayName: "建立學校",
    description: "建立新的分校",
    org_owner: true,
    org_admin: true,
    school_admin: false,
    teacher: false,
  },
  {
    operation: "manage:all_schools",
    displayName: "管理所有學校",
    description: "管理機構內所有分校",
    org_owner: true,
    org_admin: true,
    school_admin: false,
    teacher: false,
  },
  {
    operation: "manage:own_schools",
    displayName: "管理特定學校",
    description: "僅能管理自己負責的學校",
    org_owner: false,
    org_admin: false,
    school_admin: "✅ (自己的)",
    teacher: false,
  },
  {
    operation: "invite:teacher",
    displayName: "邀請教師",
    description: "邀請新教師加入",
    org_owner: true,
    org_admin: true,
    school_admin: true,
    teacher: false,
  },
  {
    operation: "manage:teacher_permissions",
    displayName: "設定教師權限",
    description: "管理教師的自訂權限",
    org_owner: true,
    org_admin: false,
    school_admin: false,
    teacher: false,
  },
  {
    operation: "view:cross_school_data",
    displayName: "查看跨校資料",
    description: "查看機構內多個學校的資料",
    org_owner: true,
    org_admin: true,
    school_admin: false,
    teacher: false,
  },
  {
    operation: "manage:billing",
    displayName: "管理訂閱付費",
    description: "管理機構的訂閱和付費",
    org_owner: true,
    org_admin: false,
    school_admin: false,
    teacher: false,
  },
  {
    operation: "create:classroom",
    displayName: "建立班級",
    description: "建立新的班級（自訂權限）",
    org_owner: true,
    org_admin: true,
    school_admin: true,
    teacher: "⚙️ 可配置",
  },
];

interface RoleConfig {
  key: keyof Pick<
    PermissionRow,
    "org_owner" | "org_admin" | "school_admin" | "teacher"
  >;
  label: string;
  description: string;
  color: string;
  bgColor: string;
  icon: React.ComponentType<{ className?: string }>;
}

const ROLES: RoleConfig[] = [
  {
    key: "org_owner",
    label: "機構擁有者",
    description: "完整權限",
    color: "text-purple-800",
    bgColor: "bg-purple-50",
    icon: Shield,
  },
  {
    key: "org_admin",
    label: "機構管理員",
    description: "管理權限",
    color: "text-blue-800",
    bgColor: "bg-blue-50",
    icon: Building2,
  },
  {
    key: "school_admin",
    label: "學校管理員",
    description: "學校層級",
    color: "text-green-800",
    bgColor: "bg-green-50",
    icon: GraduationCap,
  },
  {
    key: "teacher",
    label: "教師",
    description: "基礎權限",
    color: "text-gray-800",
    bgColor: "bg-gray-50",
    icon: Users,
  },
];

function PermissionCell({ value }: { value: boolean | string }) {
  if (value === true) {
    return <span className="text-green-600 font-bold text-lg">✅</span>;
  }
  if (value === false) {
    return <span className="text-red-400 text-lg">❌</span>;
  }
  // Custom string values like "✅ (自己的)" or "⚙️ 可配置"
  return <span className="text-sm text-gray-700 font-medium">{value}</span>;
}

export const RolePermissionMatrix = memo(function RolePermissionMatrix() {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg p-6">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Shield className="h-6 w-6 text-purple-600" />
          Casbin 角色權限矩陣
        </h2>
        <p className="text-gray-600 dark:text-gray-400 text-sm">
          此表格顯示機構內各角色的權限範圍。org_owner 和 org_admin 的權限由
          Casbin 管理，teacher 的權限則透過自訂 JSONB 欄位設定。
        </p>
      </div>

      {/* Role Legend */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {ROLES.map((role) => {
          const Icon = role.icon;
          return (
            <div
              key={role.key}
              className={`${role.bgColor} rounded-lg p-4 border border-gray-200 dark:border-gray-700`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon className={`h-5 w-5 ${role.color}`} />
                <span className={`font-semibold ${role.color}`}>
                  {role.label}
                </span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {role.description}
              </p>
            </div>
          );
        })}
      </div>

      {/* Permission Matrix Table */}
      <div className="border rounded-lg overflow-hidden bg-white dark:bg-gray-800">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50 dark:bg-gray-900">
                <TableHead className="font-bold w-48">操作</TableHead>
                <TableHead className="font-bold w-64">說明</TableHead>
                {ROLES.map((role) => {
                  const Icon = role.icon;
                  return (
                    <TableHead
                      key={role.key}
                      className={`text-center font-bold ${role.bgColor} ${role.color}`}
                    >
                      <div className="flex items-center justify-center gap-1">
                        <Icon className="h-4 w-4" />
                        <span>{role.label}</span>
                      </div>
                    </TableHead>
                  );
                })}
              </TableRow>
            </TableHeader>
            <TableBody>
              {PERMISSION_DATA.map((permission, index) => (
                <TableRow
                  key={permission.operation}
                  className={
                    index % 2 === 0
                      ? "bg-white dark:bg-gray-800"
                      : "bg-gray-50 dark:bg-gray-900"
                  }
                >
                  <TableCell className="font-medium">
                    <div className="flex flex-col">
                      <span className="text-sm font-semibold">
                        {permission.displayName}
                      </span>
                      <code className="text-xs text-gray-500 dark:text-gray-400">
                        {permission.operation}
                      </code>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-gray-600 dark:text-gray-400">
                    {permission.description}
                  </TableCell>
                  {ROLES.map((role) => (
                    <TableCell key={role.key} className="text-center">
                      <PermissionCell value={permission[role.key]} />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Footer Notes */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-sm space-y-2">
        <div className="font-semibold text-blue-900 dark:text-blue-300">
          📌 重要說明：
        </div>
        <ul className="list-disc list-inside space-y-1 text-blue-800 dark:text-blue-400">
          <li>
            <strong>org_owner</strong> 和 <strong>org_admin</strong>{" "}
            的權限由後端 Casbin 政策強制執行
          </li>
          <li>
            <strong>school_admin</strong> 只能管理自己被指派的學校
          </li>
          <li>
            <strong>teacher</strong> 的自訂權限（如建立班級）透過 JSONB
            欄位配置，請使用 <em>教師權限管理工具</em> 進行設定
          </li>
          <li>符號說明：✅ = 有權限、❌ = 無權限、⚙️ = 可透過介面配置</li>
        </ul>
      </div>
    </div>
  );
});
