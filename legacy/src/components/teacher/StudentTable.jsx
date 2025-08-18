import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Edit, Trash2, Eye } from "lucide-react";
import { format } from "date-fns";

export default function StudentTable({ students, onEdit, onDelete, showClassColumn = false }) {
    // **核心修正：增加安全檢查**
    const handleEdit = (student) => {
        if (typeof onEdit === 'function') {
            onEdit(student);
        } else {
            console.warn('onEdit 函數未正確傳遞');
        }
    };

    const handleDelete = (studentId) => {
        if (typeof onDelete === 'function') {
            onDelete(studentId);
        } else {
            console.warn('onDelete 函數未正確傳遞');
        }
    };

    if (!students || students.length === 0) {
        return (
            <div className="text-center py-8 text-gray-500">
                <p>目前沒有學生資料。</p>
            </div>
        );
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="border border-gray-200 px-4 py-2 text-left">姓名</th>
                        <th className="border border-gray-200 px-4 py-2 text-left">Email</th>
                        <th className="border border-gray-200 px-4 py-2 text-left">學號</th>
                        {showClassColumn && (
                            <th className="border border-gray-200 px-4 py-2 text-left">班級</th>
                        )}
                        <th className="border border-gray-200 px-4 py-2 text-left">生日</th>
                        <th className="border border-gray-200 px-4 py-2 text-left">狀態</th>
                        <th className="border border-gray-200 px-4 py-2 text-center">操作</th>
                    </tr>
                </thead>
                <tbody>
                    {students.map((student) => (
                        <tr key={student.id} className="hover:bg-gray-50">
                            <td className="border border-gray-200 px-4 py-2 font-medium">
                                {student.student_name}
                            </td>
                            <td className="border border-gray-200 px-4 py-2">
                                {student.email}
                            </td>
                            <td className="border border-gray-200 px-4 py-2">
                                {student.student_id || 'N/A'}
                            </td>
                            {showClassColumn && (
                                <td className="border border-gray-200 px-4 py-2">
                                    {student.class_name || 'N/A'}
                                </td>
                            )}
                            <td className="border border-gray-200 px-4 py-2">
                                {student.birth_date ? format(new Date(student.birth_date), 'yyyy-MM-dd') : 'N/A'}
                            </td>
                            <td className="border border-gray-200 px-4 py-2">
                                <Badge variant={student.is_active ? "default" : "secondary"}>
                                    {student.is_active ? "在學" : "離校"}
                                </Badge>
                            </td>
                            <td className="border border-gray-200 px-4 py-2 text-center">
                                <div className="flex justify-center gap-2">
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleEdit(student)}
                                        className="h-8 w-8 p-0"
                                        title="編輯學生"
                                    >
                                        <Edit className="h-4 w-4" />
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleDelete(student.id)}
                                        className="h-8 w-8 p-0 hover:bg-red-50 hover:text-red-600"
                                        title="刪除學生"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}