import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import TeacherLayout from "@/components/TeacherLayout";
import {
  Users,
  BookOpen,
  Plus,
  Edit,
  RefreshCw,
  GraduationCap,
  Trash2,
  AlertTriangle,
} from "lucide-react";
import { apiClient } from "@/lib/api";

interface ClassroomDetail {
  id: number;
  name: string;
  description?: string;
  level?: string;
  student_count: number;
  students: Array<{
    id: number;
    name: string;
    email: string;
  }>;
  program_count?: number;
  created_at?: string;
}

export default function TeacherClassrooms() {
  const [classrooms, setClassrooms] = useState<ClassroomDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingClassroom, setEditingClassroom] =
    useState<ClassroomDetail | null>(null);
  const [editFormData, setEditFormData] = useState({
    name: "",
    description: "",
    level: "",
  });
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createFormData, setCreateFormData] = useState({
    name: "",
    description: "",
    level: "A1",
  });

  useEffect(() => {
    fetchClassrooms();
  }, []);

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      const data =
        (await apiClient.getTeacherClassrooms()) as ClassroomDetail[];
      // Sort by ID to maintain consistent order
      const sortedData = data.sort((a, b) => a.id - b.id);
      setClassrooms(sortedData);
    } catch (err) {
      console.error("Fetch classrooms error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (classroom: ClassroomDetail) => {
    setEditingClassroom(classroom);
    setEditFormData({
      name: classroom.name,
      description: classroom.description || "",
      level: classroom.level || "A1",
    });
  };

  const handleSaveEdit = async () => {
    if (!editingClassroom) return;

    try {
      // API call to update classroom
      await apiClient.updateClassroom(editingClassroom.id, editFormData);

      // Refresh classrooms list
      await fetchClassrooms();
      setEditingClassroom(null);
    } catch (err) {
      console.error("Failed to update classroom:", err);
      alert("更新班級失敗，請稍後再試");
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirmId) return;

    try {
      // API call to delete classroom
      await apiClient.deleteClassroom(deleteConfirmId);

      // Refresh classrooms list
      await fetchClassrooms();
      setDeleteConfirmId(null);
    } catch (err) {
      console.error("Failed to delete classroom:", err);
      alert("刪除班級失敗，請稍後再試");
    }
  };

  const handleCreate = async () => {
    // Check if name is provided
    if (!createFormData.name.trim()) {
      alert("請輸入班級名稱");
      return;
    }

    try {
      await apiClient.createClassroom(createFormData);

      // Refresh the list after creation
      await fetchClassrooms();
      setShowCreateDialog(false);
      setCreateFormData({ name: "", description: "", level: "A1" });
    } catch (error) {
      console.error("Error creating classroom:", error);
      // Show error to user
      const errorMessage =
        error instanceof Error ? error.message : "建立班級失敗";
      alert(`錯誤: ${errorMessage}`);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "-";
    const date = new Date(dateString);
    return date.toLocaleDateString("zh-TW", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  };

  const getLevelBadge = (level?: string) => {
    const levelColors: Record<string, string> = {
      PREA: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
      A1: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
      A2: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
      B1: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
      B2: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300",
      C1: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
      C2: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
    };
    const color =
      levelColors[level?.toUpperCase() || "A1"] ||
      "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}
      >
        {level || "A1"}
      </span>
    );
  };

  if (loading) {
    return (
      <TeacherLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 dark:border-blue-400 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">載入中...</p>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div>
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6 space-y-4 sm:space-y-0">
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100">
            我的班級
          </h2>
          <div className="flex items-center space-x-2 sm:space-x-4 w-full sm:w-auto">
            <Button
              onClick={fetchClassrooms}
              variant="outline"
              size="sm"
              className="flex-1 sm:flex-none"
            >
              <RefreshCw className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">重新載入</span>
            </Button>
            <Button
              size="sm"
              onClick={() => setShowCreateDialog(true)}
              className="flex-1 sm:flex-none"
            >
              <Plus className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">新增班級</span>
              <span className="sm:hidden">新增</span>
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-4 sm:mb-6">
          <div className="bg-white dark:bg-gray-800 p-3 sm:p-4 rounded-lg shadow-sm border dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  總班級數
                </p>
                <p className="text-xl sm:text-2xl font-bold dark:text-gray-100">
                  {classrooms.length}
                </p>
              </div>
              <GraduationCap className="h-6 w-6 sm:h-8 sm:w-8 text-blue-500 dark:text-blue-400" />
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-3 sm:p-4 rounded-lg shadow-sm border dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  總學生數
                </p>
                <p className="text-xl sm:text-2xl font-bold dark:text-gray-100">
                  {classrooms.reduce((sum, c) => sum + c.student_count, 0)}
                </p>
              </div>
              <Users className="h-6 w-6 sm:h-8 sm:w-8 text-green-500 dark:text-green-400" />
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-3 sm:p-4 rounded-lg shadow-sm border dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  活躍班級
                </p>
                <p className="text-xl sm:text-2xl font-bold dark:text-gray-100">
                  {classrooms.length}
                </p>
              </div>
              <BookOpen className="h-6 w-6 sm:h-8 sm:w-8 text-purple-500 dark:text-purple-400" />
            </div>
          </div>
        </div>

        {/* Classrooms Table */}
        <>
          {/* Mobile Card View */}
          <div className="md:hidden space-y-4">
            {classrooms.map((classroom) => (
              <div
                key={classroom.id}
                className="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg p-4 space-y-3"
              >
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center flex-shrink-0">
                      <GraduationCap className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          ID: {classroom.id}
                        </span>
                        {getLevelBadge(classroom.level)}
                      </div>
                      <Link
                        to={`/teacher/classroom/${classroom.id}`}
                        className="font-medium text-lg text-blue-600 dark:text-blue-400 hover:underline block mt-1"
                      >
                        {classroom.name}
                      </Link>
                      {classroom.description && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          {classroom.description}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Info */}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-400">
                      學生:
                    </span>
                    <span className="font-medium dark:text-gray-200">
                      {classroom.student_count}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <BookOpen className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-400">
                      課程:
                    </span>
                    <span className="font-medium dark:text-gray-200">
                      {classroom.program_count || 0}
                    </span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-600 dark:text-gray-400">
                      建立時間:{" "}
                    </span>
                    <span className="dark:text-gray-200">
                      {formatDate(classroom.created_at)}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2 border-t dark:border-gray-700">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(classroom)}
                    className="flex-1"
                  >
                    <Edit className="h-4 w-4 mr-2" />
                    編輯
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setDeleteConfirmId(classroom.id)}
                    className="flex-1 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    刪除
                  </Button>
                </div>
              </div>
            ))}
            <div className="text-center py-4 text-sm text-gray-500 dark:text-gray-400">
              共 {classrooms.length} 個班級
            </div>
          </div>

          {/* Desktop Table View */}
          <div className="hidden md:block bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 overflow-hidden">
            <div className="overflow-x-auto">
              <Table>
                <TableCaption className="dark:text-gray-400">
                  共 {classrooms.length} 個班級
                </TableCaption>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px] text-left text-xs sm:text-sm">
                      ID
                    </TableHead>
                    <TableHead className="text-left text-xs sm:text-sm min-w-[120px]">
                      班級名稱
                    </TableHead>
                    <TableHead className="text-left text-xs sm:text-sm min-w-[100px]">
                      描述
                    </TableHead>
                    <TableHead className="text-left text-xs sm:text-sm min-w-[60px]">
                      等級
                    </TableHead>
                    <TableHead className="text-left text-xs sm:text-sm min-w-[80px]">
                      學生數
                    </TableHead>
                    <TableHead className="text-left text-xs sm:text-sm min-w-[80px]">
                      課程數
                    </TableHead>
                    <TableHead className="text-left text-xs sm:text-sm min-w-[100px]">
                      建立時間
                    </TableHead>
                    <TableHead className="text-left text-xs sm:text-sm min-w-[80px]">
                      操作
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {classrooms.map((classroom) => (
                    <TableRow
                      key={classroom.id}
                      className="hover:bg-gray-50 dark:hover:bg-gray-700/50"
                    >
                      <TableCell className="font-medium text-xs sm:text-sm">
                        {classroom.id}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1 sm:space-x-2">
                          <div className="w-6 h-6 sm:w-8 sm:h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center flex-shrink-0">
                            <GraduationCap className="h-3 w-3 sm:h-4 sm:w-4 text-blue-600 dark:text-blue-400" />
                          </div>
                          <Link
                            to={`/teacher/classroom/${classroom.id}`}
                            className="font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:underline text-xs sm:text-sm truncate"
                          >
                            {classroom.name}
                          </Link>
                        </div>
                      </TableCell>
                      <TableCell>
                        <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">
                          {classroom.description || "暫無描述"}
                        </p>
                      </TableCell>
                      <TableCell>{getLevelBadge(classroom.level)}</TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <Users className="h-3 w-3 sm:h-4 sm:w-4 mr-1 text-gray-400 dark:text-gray-500" />
                          <span className="text-xs sm:text-sm dark:text-gray-200">
                            {classroom.student_count}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <BookOpen className="h-3 w-3 sm:h-4 sm:w-4 mr-1 text-gray-400 dark:text-gray-500" />
                          <span className="text-xs sm:text-sm dark:text-gray-200">
                            {classroom.program_count || 0}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs sm:text-sm dark:text-gray-200">
                        {formatDate(classroom.created_at)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            title="編輯"
                            onClick={() => handleEdit(classroom)}
                            className="p-1 sm:p-2"
                          >
                            <Edit className="h-3 w-3 sm:h-4 sm:w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            title="刪除"
                            onClick={() => setDeleteConfirmId(classroom.id)}
                            className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 p-1 sm:p-2"
                          >
                            <Trash2 className="h-3 w-3 sm:h-4 sm:w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </>

        {/* Empty State */}
        {classrooms.length === 0 && (
          <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700">
            <GraduationCap className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">尚未建立班級</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
              建立您的第一個班級，開始管理學生和課程
            </p>
            <Button className="mt-4" onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              建立第一個班級
            </Button>
          </div>
        )}

        {/* Edit Dialog */}
        <Dialog
          open={!!editingClassroom}
          onOpenChange={(open) => !open && setEditingClassroom(null)}
        >
          <DialogContent
            className="bg-white"
            style={{ backgroundColor: "white" }}
          >
            <DialogHeader>
              <DialogTitle>編輯班級</DialogTitle>
              <DialogDescription>修改班級資訊</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-1 sm:grid-cols-4 items-start sm:items-center gap-2 sm:gap-4">
                <label
                  htmlFor="name"
                  className="text-left sm:text-right text-sm font-medium"
                >
                  班級名稱
                </label>
                <input
                  id="name"
                  value={editFormData.name}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, name: e.target.value })
                  }
                  className="col-span-1 sm:col-span-3 px-3 py-2 border rounded-md text-sm"
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-4 items-start gap-2 sm:gap-4">
                <label
                  htmlFor="description"
                  className="text-left sm:text-right text-sm font-medium"
                >
                  描述
                </label>
                <textarea
                  id="description"
                  value={editFormData.description}
                  onChange={(e) =>
                    setEditFormData({
                      ...editFormData,
                      description: e.target.value,
                    })
                  }
                  className="col-span-1 sm:col-span-3 px-3 py-2 border rounded-md text-sm"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-4 items-start sm:items-center gap-2 sm:gap-4">
                <label
                  htmlFor="level"
                  className="text-left sm:text-right text-sm font-medium"
                >
                  等級
                </label>
                <select
                  id="level"
                  value={editFormData.level}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, level: e.target.value })
                  }
                  className="col-span-1 sm:col-span-3 px-3 py-2 border rounded-md text-sm"
                >
                  <option value="preA">Pre-A</option>
                  <option value="A1">A1</option>
                  <option value="A2">A2</option>
                  <option value="B1">B1</option>
                  <option value="B2">B2</option>
                  <option value="C1">C1</option>
                  <option value="C2">C2</option>
                </select>
              </div>
            </div>
            <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-0">
              <Button
                variant="outline"
                onClick={() => setEditingClassroom(null)}
                className="w-full sm:w-auto"
              >
                取消
              </Button>
              <Button onClick={handleSaveEdit} className="w-full sm:w-auto">
                儲存
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog
          open={!!deleteConfirmId}
          onOpenChange={(open) => !open && setDeleteConfirmId(null)}
        >
          <DialogContent
            className="bg-white"
            style={{ backgroundColor: "white" }}
          >
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <span>確認刪除班級</span>
              </DialogTitle>
              <DialogDescription>
                確定要刪除這個班級嗎？此操作無法復原。
                班級內的學生和課程資料將會保留，但不再與此班級關聯。
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-0">
              <Button
                variant="outline"
                onClick={() => setDeleteConfirmId(null)}
                className="w-full sm:w-auto"
              >
                取消
              </Button>
              <Button
                variant="destructive"
                onClick={handleDelete}
                className="w-full sm:w-auto"
              >
                確認刪除
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Create Classroom Dialog */}
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent
            className="bg-white"
            style={{ backgroundColor: "white" }}
          >
            <DialogHeader>
              <DialogTitle>新增班級</DialogTitle>
              <DialogDescription>建立新的班級</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-1">
                  班級名稱
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border rounded-md text-sm"
                  value={createFormData.name}
                  onChange={(e) =>
                    setCreateFormData({
                      ...createFormData,
                      name: e.target.value,
                    })
                  }
                  placeholder="例如：五年級A班"
                />
              </div>
              <div>
                <label className="text-sm font-medium block mb-1">描述</label>
                <textarea
                  className="w-full px-3 py-2 border rounded-md text-sm"
                  value={createFormData.description}
                  onChange={(e) =>
                    setCreateFormData({
                      ...createFormData,
                      description: e.target.value,
                    })
                  }
                  placeholder="班級描述（選填）"
                  rows={3}
                />
              </div>
              <div>
                <label className="text-sm font-medium block mb-1">級別</label>
                <select
                  className="w-full px-3 py-2 border rounded-md text-sm"
                  value={createFormData.level}
                  onChange={(e) =>
                    setCreateFormData({
                      ...createFormData,
                      level: e.target.value,
                    })
                  }
                >
                  <option value="A1">A1 - 初級</option>
                  <option value="A2">A2 - 基礎</option>
                  <option value="B1">B1 - 中級</option>
                  <option value="B2">B2 - 中高級</option>
                  <option value="C1">C1 - 高級</option>
                  <option value="C2">C2 - 精通</option>
                </select>
              </div>
            </div>
            <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-0">
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
                className="w-full sm:w-auto"
              >
                取消
              </Button>
              <Button onClick={handleCreate} className="w-full sm:w-auto">
                建立
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TeacherLayout>
  );
}
