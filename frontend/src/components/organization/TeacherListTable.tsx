import { useState } from "react";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { API_URL } from "@/config/api";
import { logError } from "@/utils/errorLogger";
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
import { toast } from "sonner";

export interface Teacher {
  id: number;
  email: string;
  name: string;
  roles: string[];
  is_active: boolean;
  created_at: string;
}

interface TeacherListTableProps {
  teachers: Teacher[];
  schoolId: string;
  onRoleUpdated?: () => void;
}

export function TeacherListTable({ teachers, schoolId, onRoleUpdated }: TeacherListTableProps) {
  const token = useTeacherAuthStore((state) => state.token);
  const currentUser = useTeacherAuthStore((state) => state.user);
  const [updatingRoleId, setUpdatingRoleId] = useState<number | null>(null);

  // Check if current user can edit roles (org_owner, org_admin, school_admin)
  const canEditRoles =
    currentUser?.role === "org_owner" ||
    currentUser?.role === "org_admin" ||
    currentUser?.role === "school_admin";
  const getRoleBadgeColor = (roles: string[]) => {
    if (roles.includes("school_admin")) {
      return "bg-purple-100 text-purple-800";
    } else if (roles.includes("school_director")) {
      return "bg-amber-100 text-amber-800";
    } else if (roles.includes("teacher")) {
      return "bg-gray-100 text-gray-800";
    }
    return "bg-gray-100 text-gray-800";
  };

  const getRoleLabel = (roles: string[]) => {
    if (roles.includes("school_admin")) return "校長";
    if (roles.includes("school_director")) return "主任";
    if (roles.includes("teacher")) return "教師";
    return roles.join(", ");
  };

  // Get primary role (first role in array)
  const getPrimaryRole = (roles: string[]): string => {
    if (roles.includes("school_admin")) return "school_admin";
    if (roles.includes("school_director")) return "school_director";
    if (roles.includes("teacher")) return "teacher";
    return roles[0] || "teacher";
  };

  const handleRoleChange = async (teacherId: number, newRole: string) => {
    try {
      setUpdatingRoleId(teacherId);
      
      const response = await fetch(
        `${API_URL}/api/schools/${schoolId}/teachers/${teacherId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ roles: [newRole] }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "更新角色失敗");
      }

      toast.success("角色已更新");
      onRoleUpdated?.();
    } catch (error) {
      logError("Failed to update teacher role", error, { teacherId, newRole, schoolId });
      toast.error("更新角色失敗，請稍後再試");
    } finally {
      setUpdatingRoleId(null);
    }
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>姓名</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>角色</TableHead>
          <TableHead>狀態</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {teachers.map((teacher) => (
          <TableRow key={teacher.id}>
            <TableCell className="font-medium">{teacher.name}</TableCell>
            <TableCell>{teacher.email}</TableCell>
            <TableCell>
              {canEditRoles && teacher.id !== currentUser?.id ? (
                <Select
                  value={getPrimaryRole(teacher.roles)}
                  onValueChange={(newRole) => handleRoleChange(teacher.id, newRole)}
                  disabled={updatingRoleId === teacher.id}
                >
                  <SelectTrigger className="w-[150px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="school_admin">校長</SelectItem>
                    <SelectItem value="school_director">主任</SelectItem>
                    <SelectItem value="teacher">教師</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(
                    teacher.roles,
                  )}`}
                >
                  {getRoleLabel(teacher.roles)}
                </span>
              )}
            </TableCell>
            <TableCell>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  teacher.is_active
                    ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {teacher.is_active ? "啟用" : "停用"}
              </span>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
