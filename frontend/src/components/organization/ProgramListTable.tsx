import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Edit2, Trash2, FileText, Loader2 } from "lucide-react";

export interface Program {
  id: number;
  organization_id?: string;
  name: string;
  description?: string;
  level?: string;
  total_hours?: number;
  estimated_hours?: number;
  tags?: string[];
  is_active: boolean;
  is_template?: boolean;
  created_at: string;
  updated_at?: string;
}

interface ProgramListTableProps {
  programs: Program[];
  onEdit?: (program: Program) => void;
  onDelete?: (programId: number) => void;
  canManage?: boolean;
  deletingId?: number | null;
  showCreatedAt?: boolean;
  showStatus?: boolean;
}

export function ProgramListTable({
  programs,
  onEdit,
  onDelete,
  canManage = true,
  deletingId = null,
  showCreatedAt = true,
  showStatus = true,
}: ProgramListTableProps) {
  const getLevelBadgeColor = (level?: string) => {
    if (!level) return "bg-gray-100 text-gray-800";
    switch (level.toUpperCase()) {
      case "PREA":
      case "PRE_A":
        return "bg-gray-100 text-gray-800";
      case "A1":
        return "bg-green-100 text-green-800";
      case "A2":
        return "bg-blue-100 text-blue-800";
      case "B1":
        return "bg-yellow-100 text-yellow-800";
      case "B2":
        return "bg-orange-100 text-orange-800";
      case "C1":
        return "bg-purple-100 text-purple-800";
      case "C2":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getLevelLabel = (level?: string) => {
    if (!level) return "-";
    return level.toUpperCase().replace("_", "");
  };

  const getHours = (program: Program) => {
    return program.total_hours || program.estimated_hours || "-";
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>課程名稱</TableHead>
          <TableHead>描述</TableHead>
          <TableHead>等級</TableHead>
          <TableHead>時數</TableHead>
          {showCreatedAt && <TableHead>建立時間</TableHead>}
          {showStatus && <TableHead>狀態</TableHead>}
          {canManage && onEdit && onDelete && (
            <TableHead className="text-right">操作</TableHead>
          )}
        </TableRow>
      </TableHeader>
      <TableBody>
        {programs.map((program) => (
          <TableRow key={program.id}>
            <TableCell className="font-medium">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-gray-400" />
                {program.name}
              </div>
            </TableCell>
            <TableCell className="max-w-xs truncate">
              {program.description || "-"}
            </TableCell>
            <TableCell>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelBadgeColor(
                  program.level,
                )}`}
              >
                {getLevelLabel(program.level)}
              </span>
            </TableCell>
            <TableCell>{getHours(program)}</TableCell>
            {showCreatedAt && (
              <TableCell>
                {new Date(program.created_at).toLocaleDateString("zh-TW")}
              </TableCell>
            )}
            {showStatus && (
              <TableCell>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    program.is_active
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {program.is_active ? "啟用" : "停用"}
                </span>
              </TableCell>
            )}
            {canManage && onEdit && onDelete && (
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(program)}
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(program.id)}
                    disabled={deletingId === program.id}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    {deletingId === program.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </TableCell>
            )}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
