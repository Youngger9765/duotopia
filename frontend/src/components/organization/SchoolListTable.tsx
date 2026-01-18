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
import { Edit2, UserPlus } from "lucide-react";

export interface School {
  id: string;
  organization_id: string;
  name: string;
  display_name?: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
  created_at: string;
  principal_name?: string;
  principal_email?: string;
}

interface SchoolListTableProps {
  schools: School[];
  onEdit: (school: School) => void;
  onAssignPrincipal: (school: School) => void;
}

export function SchoolListTable({
  schools,
  onEdit,
  onAssignPrincipal,
}: SchoolListTableProps) {
  const navigate = useNavigate();

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>學校名稱</TableHead>
          <TableHead>聯絡信箱</TableHead>
          <TableHead>校長</TableHead>
          <TableHead>狀態</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {schools.map((school) => (
          <TableRow key={school.id}>
            <TableCell className="font-medium">
              <button
                onClick={() =>
                  navigate(`/organization/schools/${school.id}`)
                }
                className="text-blue-600 hover:text-blue-800 hover:underline transition-colors"
              >
                {school.display_name || school.name}
              </button>
            </TableCell>
            <TableCell>{school.contact_email || "-"}</TableCell>
            <TableCell>
              {school.principal_name ? (
                <div className="flex items-center gap-2">
                  <span className="text-gray-900">{school.principal_name}</span>
                  <button
                    onClick={() => onAssignPrincipal(school)}
                    className="text-gray-400 hover:text-blue-600 transition-colors"
                    title="更換校長"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onAssignPrincipal(school)}
                  className="text-blue-600 hover:text-blue-700"
                >
                  <UserPlus className="h-4 w-4 mr-1" />
                  指派校長
                </Button>
              )}
            </TableCell>
            <TableCell>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  school.is_active
                    ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {school.is_active ? "啟用" : "停用"}
              </span>
            </TableCell>
            <TableCell className="text-right">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onEdit(school)}
              >
                <Edit2 className="h-4 w-4" />
                編輯
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
