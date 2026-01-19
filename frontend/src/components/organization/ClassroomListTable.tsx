import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Users, Edit2, UserPlus } from "lucide-react";

export interface Classroom {
  id: string;
  name: string;
  program_level: string;
  is_active: boolean;
  created_at: string;
  teacher_name: string | null;
  teacher_email: string | null;
  teacher_id?: number | null;
  student_count: number;
  assignment_count: number;
}

interface ClassroomListTableProps {
  classrooms: Classroom[];
  onEdit?: (classroom: Classroom) => void;
  onAssignTeacher?: (classroom: Classroom) => void;
}

export function ClassroomListTable({
  classrooms,
  onEdit,
  onAssignTeacher,
}: ClassroomListTableProps) {
  const navigate = useNavigate();

  const getLevelBadge = (level: string) => {
    const levelColors: Record<string, string> = {
      PREA: "bg-gray-100 text-gray-800",
      A1: "bg-green-100 text-green-800",
      A2: "bg-blue-100 text-blue-800",
      B1: "bg-purple-100 text-purple-800",
      B2: "bg-indigo-100 text-indigo-800",
      C1: "bg-red-100 text-red-800",
      C2: "bg-orange-100 text-orange-800",
    };
    const color = levelColors[level?.toUpperCase()] || "bg-gray-100 text-gray-800";
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}
      >
        {level || "A1"}
      </span>
    );
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>班級名稱</TableHead>
          <TableHead>語言程度</TableHead>
          <TableHead>導師</TableHead>
          <TableHead>學生數量</TableHead>
          <TableHead>狀態</TableHead>
          {(onEdit || onAssignTeacher) && <TableHead>操作</TableHead>}
        </TableRow>
      </TableHeader>
      <TableBody>
        {classrooms.map((classroom) => (
          <TableRow key={classroom.id}>
            <TableCell className="font-medium">
              <button
                onClick={() =>
                  navigate(`/teacher/classroom/${classroom.id}`)
                }
                className="text-blue-600 hover:text-blue-800 hover:underline transition-colors"
              >
                {classroom.name}
              </button>
            </TableCell>
            <TableCell>{getLevelBadge(classroom.program_level)}</TableCell>
            <TableCell>
              {classroom.teacher_name ? (
                <span className="text-gray-900">{classroom.teacher_name}</span>
              ) : (
                <span className="text-gray-400">未指派</span>
              )}
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-1">
                <Users className="h-4 w-4 text-gray-400" />
                <span>{classroom.student_count}</span>
              </div>
            </TableCell>
            <TableCell>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  classroom.is_active
                    ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {classroom.is_active ? "啟用" : "停用"}
              </span>
            </TableCell>
            {(onEdit || onAssignTeacher) && (
              <TableCell>
                <div className="flex items-center gap-2">
                  {onEdit && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEdit(classroom)}
                      className="gap-1"
                    >
                      <Edit2 className="h-4 w-4" />
                      編輯
                    </Button>
                  )}
                  {onAssignTeacher && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onAssignTeacher(classroom)}
                      className="gap-1"
                    >
                      <UserPlus className="h-4 w-4" />
                      {classroom.teacher_name ? "更換導師" : "指派導師"}
                    </Button>
                  )}
                </div>
              </TableCell>
            )}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
