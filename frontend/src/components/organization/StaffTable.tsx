import { useState } from "react";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Mail } from "lucide-react";
import { toast } from "sonner";

export interface StaffMember {
  id: number;
  email: string;
  name: string;
  role: string; // org_owner, org_admin, teacher, school_admin
  is_active: boolean;
  created_at: string;
}

interface StaffTableProps {
  staff: StaffMember[];
  organizationId: string;
  onRoleUpdated?: () => void;
  showEmail?: boolean;
}

export function StaffTable({
  staff,
  organizationId,
  onRoleUpdated,
  showEmail = true,
}: StaffTableProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const user = useTeacherAuthStore((state) => state.user);
  const [updatingRoleId, setUpdatingRoleId] = useState<number | null>(null);

  // Check if current user can edit roles
  const canEditRoles =
    user?.role === "org_owner" || user?.role === "org_admin";

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case "org_owner":
        return "bg-purple-100 text-purple-800";
      case "org_admin":
        return "bg-blue-100 text-blue-800";
      case "school_admin":
        return "bg-green-100 text-green-800";
      case "teacher":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case "org_owner":
        return "組織擁有者";
      case "org_admin":
        return "組織管理員";
      case "school_admin":
        return "學校管理員";
      case "teacher":
        return "教師";
      default:
        return role;
    }
  };

  const handleRoleChange = async (teacherId: number, newRole: string) => {
    setUpdatingRoleId(teacherId);
    try {
      const response = await fetch(
        `${API_URL}/api/organizations/${organizationId}/teachers/${teacherId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ role: newRole }),
        },
      );

      if (response.ok) {
        toast.success("角色更新成功");
        if (onRoleUpdated) {
          onRoleUpdated();
        }
      } else {
        const data = await response.json();
        toast.error(data.detail || "角色更新失敗");
      }
    } catch (error) {
      console.error("Failed to update teacher role:", error);
      toast.error("網路連線錯誤");
    } finally {
      setUpdatingRoleId(null);
    }
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>姓名</TableHead>
          {showEmail && <TableHead>Email</TableHead>}
          <TableHead>角色</TableHead>
          <TableHead>狀態</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {staff.map((member) => (
          <TableRow key={member.id}>
            <TableCell className="font-medium">{member.name}</TableCell>
            {showEmail && (
              <TableCell>
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-gray-400" />
                  {member.email}
                </div>
              </TableCell>
            )}
            <TableCell>
              {canEditRoles && member.id !== user?.id ? (
                <Select
                  value={member.role}
                  onValueChange={(newRole) =>
                    handleRoleChange(member.id, newRole)
                  }
                  disabled={updatingRoleId === member.id}
                >
                  <SelectTrigger className="w-[180px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="teacher">教師</SelectItem>
                    <SelectItem value="org_admin">組織管理員</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(
                    member.role,
                  )}`}
                >
                  {getRoleLabel(member.role)}
                </span>
              )}
            </TableCell>
            <TableCell>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  member.is_active
                    ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {member.is_active ? "啟用" : "停用"}
              </span>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
