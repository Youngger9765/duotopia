import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

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
}

export function TeacherListTable({ teachers }: TeacherListTableProps) {
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
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(
                  teacher.roles,
                )}`}
              >
                {getRoleLabel(teacher.roles)}
              </span>
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
