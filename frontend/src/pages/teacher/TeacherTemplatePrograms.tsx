import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  TagInputWithSuggestions,
  TagSuggestion,
} from "@/components/ui/tag-input";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import TeacherLayout from "@/components/TeacherLayout";
import {
  BookOpen,
  RefreshCw,
  Plus,
  Edit,
  Eye,
  Trash2,
  Copy,
  Archive,
} from "lucide-react";
import LoadingSpinner from "@/components/LoadingSpinner";
import TableSkeleton from "@/components/TableSkeleton";
import { apiClient } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Program {
  id: number;
  name: string;
  description?: string;
  is_template: boolean;
  classroom_id?: number;
  classroom_name?: string;
  estimated_hours?: number;
  level?: string;
  created_at?: string;
  updated_at?: string;
  lesson_count?: number;
  tags?: string[];
  source_type?: string;
  source_metadata?: Record<string, unknown>;
}

interface Classroom {
  id: number;
  name: string;
}

export default function TeacherTemplatePrograms() {
  const navigate = useNavigate();
  const [programs, setPrograms] = useState<Program[]>([]);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const [dialogType, setDialogType] = useState<
    "view" | "create" | "edit" | "delete" | "copy" | null
  >(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    level: "A1",
    estimated_hours: "",
    tags: [] as string[],
  });
  const [copyData, setCopyData] = useState({
    targetClassroomId: "",
    newName: "",
  });

  // 標籤建議
  const tagSuggestions: TagSuggestion[] = [
    // 程度相關
    { value: "beginner", label: "初級", category: "level" },
    { value: "intermediate", label: "中級", category: "level" },
    { value: "advanced", label: "進階", category: "level" },

    // 技能相關
    { value: "speaking", label: "口說", category: "skill" },
    { value: "listening", label: "聽力", category: "skill" },
    { value: "reading", label: "閱讀", category: "skill" },
    { value: "writing", label: "寫作", category: "skill" },
    { value: "grammar", label: "文法", category: "skill" },
    { value: "vocabulary", label: "詞彙", category: "skill" },
    { value: "pronunciation", label: "發音", category: "skill" },

    // 主題相關
    { value: "daily", label: "日常生活", category: "topic" },
    { value: "business", label: "商務", category: "topic" },
    { value: "travel", label: "旅遊", category: "topic" },
    { value: "exam", label: "考試準備", category: "topic" },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [templatesData, classroomsData] = await Promise.all([
        apiClient.getTemplatePrograms() as Promise<Program[]>,
        apiClient.getTeacherClassrooms() as Promise<
          Array<{ id: number; name: string; [key: string]: unknown }>
        >,
      ]);

      // 按 ID 排序（升序）
      const sortedPrograms = templatesData.sort((a, b) => a.id - b.id);
      setPrograms(sortedPrograms);
      setClassrooms(classroomsData.map((c) => ({ id: c.id, name: c.name })));
    } catch (err) {
      console.error("Fetch data error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProgram = () => {
    setFormData({
      name: "",
      description: "",
      level: "A1",
      estimated_hours: "",
      tags: [],
    });
    setDialogType("create");
  };

  const handleViewProgram = (program: Program) => {
    setSelectedProgram(program);
    setDialogType("view");
  };

  const handleCopyProgram = (program: Program) => {
    setSelectedProgram(program);
    setCopyData({
      targetClassroomId: "",
      newName: `${program.name} (複製)`,
    });
    setDialogType("copy");
  };

  const handleDeleteProgram = (program: Program) => {
    setSelectedProgram(program);
    setDialogType("delete");
  };

  const handleSaveProgram = async () => {
    try {
      const data = {
        name: formData.name,
        description: formData.description,
        level: formData.level,
        estimated_hours: formData.estimated_hours
          ? Number(formData.estimated_hours)
          : undefined,
        tags: formData.tags,
      };

      if (dialogType === "create") {
        await apiClient.createTemplateProgram(data);
      } else if (dialogType === "edit" && selectedProgram) {
        await apiClient.updateTemplateProgram(selectedProgram.id, data);
      }

      setDialogType(null);
      fetchData();
    } catch (err) {
      console.error("Save program error:", err);
      alert("儲存失敗，請稍後再試");
    }
  };

  const handleConfirmCopy = async () => {
    if (!selectedProgram || !copyData.targetClassroomId) return;

    try {
      await apiClient.copyFromTemplate({
        template_id: selectedProgram.id,
        classroom_id: Number(copyData.targetClassroomId),
        name: copyData.newName || undefined,
      });

      setDialogType(null);
      // Show success message
      alert("課程已成功複製到班級！");
    } catch (err) {
      console.error("Copy program error:", err);
      alert("複製失敗，請稍後再試");
    }
  };

  const handleConfirmDelete = async () => {
    if (!selectedProgram) return;

    try {
      await apiClient.softDeleteProgram(selectedProgram.id);
      setDialogType(null);
      fetchData();
    } catch (err) {
      console.error("Delete program error:", err);
    }
  };

  const getLevelBadge = (level?: string) => {
    if (!level) return null;
    const levelColors: Record<string, string> = {
      A1: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
      A2: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
      B1: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
      B2: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
      C1: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
      C2: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
    };
    const color =
      levelColors[level.toUpperCase()] ||
      "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}
      >
        {level}
      </span>
    );
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

  if (loading) {
    return (
      <TeacherLayout>
        <div>
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100">
              課程範本庫
            </h2>
          </div>

          {/* Stats Cards Skeleton */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border dark:border-gray-700 animate-pulse"
              >
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <div className="h-3 w-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="h-8 w-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  </div>
                  <div className="h-8 w-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                </div>
              </div>
            ))}
          </div>

          {/* Loading Spinner */}
          <LoadingSpinner message="正在載入課程範本..." size="lg" />

          {/* Table Skeleton */}
          <TableSkeleton rows={5} columns={6} />
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div>
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100">
              公版課程模板
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              建立可複製到任何班級的課程模板
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Refresh Button */}
            <Button
              onClick={fetchData}
              variant="outline"
              size="sm"
              className="flex-1 sm:flex-none"
            >
              <RefreshCw className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">重新載入</span>
            </Button>
            {/* Add New Template Button */}
            <Button
              size="sm"
              onClick={handleCreateProgram}
              className="flex-1 sm:flex-none"
            >
              <Plus className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">建立公版課程</span>
              <span className="sm:hidden">新增</span>
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  公版課程總數
                </p>
                <p className="text-2xl font-bold dark:text-gray-100">
                  {programs.length}
                </p>
              </div>
              <BookOpen className="h-8 w-8 text-blue-500 dark:text-blue-400" />
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  可用班級數
                </p>
                <p className="text-2xl font-bold dark:text-gray-100">
                  {classrooms.length}
                </p>
              </div>
              <Archive className="h-8 w-8 text-green-500 dark:text-green-400" />
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  本月新增
                </p>
                <p className="text-2xl font-bold dark:text-gray-100">
                  {
                    programs.filter((p) => {
                      if (!p.created_at) return false;
                      const created = new Date(p.created_at);
                      const now = new Date();
                      return (
                        created.getMonth() === now.getMonth() &&
                        created.getFullYear() === now.getFullYear()
                      );
                    }).length
                  }
                </p>
              </div>
              <Plus className="h-8 w-8 text-purple-500 dark:text-purple-400" />
            </div>
          </div>
        </div>

        {/* Programs Table */}
        <>
          {/* Mobile Card View */}
          <div className="md:hidden space-y-4">
            {programs.map((program) => (
              <div
                key={program.id}
                className="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg p-4 space-y-3"
              >
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        ID: {program.id}
                      </span>
                      {getLevelBadge(program.level)}
                    </div>
                    <p className="font-medium text-lg mt-1 dark:text-gray-100">
                      {program.name}
                    </p>
                    {program.description && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {program.description}
                      </p>
                    )}
                  </div>
                </div>

                {/* Info */}
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">
                      預計時數:
                    </span>
                    <span className="dark:text-gray-200">
                      {program.estimated_hours
                        ? `${program.estimated_hours} 小時`
                        : "-"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">
                      課程數:
                    </span>
                    <span className="dark:text-gray-200">
                      {program.lesson_count || "-"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">
                      建立時間:
                    </span>
                    <span className="dark:text-gray-200">
                      {formatDate(program.created_at)}
                    </span>
                  </div>
                  {program.tags && program.tags.length > 0 && (
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">
                        標籤:
                      </span>
                      <div className="flex gap-1 flex-wrap mt-1">
                        {program.tags.map((tag, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2 border-t dark:border-gray-700">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewProgram(program)}
                    className="flex-1"
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    查看
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCopyProgram(program)}
                    className="flex-1 text-blue-600 dark:text-blue-400"
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    複製
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      navigate(`/teacher/template-programs/${program.id}`)
                    }
                    className="flex-1"
                  >
                    <Edit className="h-4 w-4 mr-2" />
                    編輯
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeleteProgram(program)}
                    className="hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
            <div className="text-center py-4 text-sm text-gray-500 dark:text-gray-400">
              共 {programs.length} 個公版課程模板
            </div>
          </div>

          {/* Desktop Table View */}
          <div className="hidden md:block bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700">
            <Table>
              <TableCaption className="dark:text-gray-400">
                共 {programs.length} 個公版課程模板
              </TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px] text-left">ID</TableHead>
                  <TableHead className="text-left">課程名稱</TableHead>
                  <TableHead className="text-left">等級</TableHead>
                  <TableHead className="text-left">預計時數</TableHead>
                  <TableHead className="text-left">課程數</TableHead>
                  <TableHead className="text-left">標籤</TableHead>
                  <TableHead className="text-left">建立時間</TableHead>
                  <TableHead className="text-left">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {programs.map((program) => (
                  <TableRow key={program.id}>
                    <TableCell className="font-medium">{program.id}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium dark:text-gray-100">
                          {program.name}
                        </p>
                        {program.description && (
                          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">
                            {program.description}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{getLevelBadge(program.level)}</TableCell>
                    <TableCell className="dark:text-gray-200">
                      {program.estimated_hours
                        ? `${program.estimated_hours} 小時`
                        : "-"}
                    </TableCell>
                    <TableCell className="dark:text-gray-200">
                      {program.lesson_count || "-"}
                    </TableCell>
                    <TableCell>
                      {program.tags && program.tags.length > 0 ? (
                        <div className="flex gap-1 flex-wrap">
                          {program.tags.slice(0, 3).map((tag, index) => (
                            <span
                              key={index}
                              className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                            >
                              {tag}
                            </span>
                          ))}
                          {program.tags.length > 3 && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              +{program.tags.length - 3}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="dark:text-gray-400">-</span>
                      )}
                    </TableCell>
                    <TableCell className="dark:text-gray-200">
                      {formatDate(program.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          title="查看"
                          onClick={() => handleViewProgram(program)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          title="複製到班級"
                          onClick={() => handleCopyProgram(program)}
                          className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          title="編輯課程內容"
                          onClick={() =>
                            navigate(`/teacher/template-programs/${program.id}`)
                          }
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                          title="刪除"
                          onClick={() => handleDeleteProgram(program)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </>

        {/* Empty State */}
        {programs.length === 0 && (
          <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700">
            <BookOpen className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">
              尚未建立公版課程模板
            </p>
            <Button className="mt-4" onClick={handleCreateProgram}>
              <Plus className="h-4 w-4 mr-2" />
              建立第一個公版課程
            </Button>
          </div>
        )}
      </div>

      {/* View Dialog */}
      {dialogType === "view" && selectedProgram && (
        <Dialog open={true} onOpenChange={() => setDialogType(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>課程詳情</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>課程名稱</Label>
                <p className="mt-1">{selectedProgram.name}</p>
              </div>
              <div>
                <Label>課程描述</Label>
                <p className="mt-1">
                  {selectedProgram.description || "無描述"}
                </p>
              </div>
              <div>
                <Label>等級</Label>
                <p className="mt-1">{selectedProgram.level || "-"}</p>
              </div>
              <div>
                <Label>預計時數</Label>
                <p className="mt-1">
                  {selectedProgram.estimated_hours
                    ? `${selectedProgram.estimated_hours} 小時`
                    : "-"}
                </p>
              </div>
              <div>
                <Label>標籤</Label>
                <p className="mt-1">
                  {selectedProgram.tags?.join(", ") || "-"}
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogType(null)}>
                關閉
              </Button>
              <Button onClick={() => handleCopyProgram(selectedProgram)}>
                <Copy className="h-4 w-4 mr-2" />
                複製到班級
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Create/Edit Dialog */}
      {(dialogType === "create" || dialogType === "edit") && (
        <Dialog open={true} onOpenChange={() => setDialogType(null)}>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle>
                {dialogType === "create" ? "建立公版課程" : "編輯公版課程"}
              </DialogTitle>
              <DialogDescription>
                建立可在任何班級中重複使用的課程模板
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div>
                <Label htmlFor="name">課程名稱 *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  placeholder="例如：初級英語會話"
                />
              </div>
              <div>
                <Label htmlFor="description">課程描述</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="描述這個課程的內容和目標"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="level">等級</Label>
                  <Select
                    value={formData.level}
                    onValueChange={(value) =>
                      setFormData({ ...formData, level: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="A1">A1 - 入門</SelectItem>
                      <SelectItem value="A2">A2 - 基礎</SelectItem>
                      <SelectItem value="B1">B1 - 中級</SelectItem>
                      <SelectItem value="B2">B2 - 中高級</SelectItem>
                      <SelectItem value="C1">C1 - 高級</SelectItem>
                      <SelectItem value="C2">C2 - 精通</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="hours">預計時數</Label>
                  <Input
                    id="hours"
                    type="number"
                    value={formData.estimated_hours}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        estimated_hours: e.target.value,
                      })
                    }
                    placeholder="20"
                  />
                </div>
              </div>
              <div>
                <Label>標籤</Label>
                <TagInputWithSuggestions
                  value={formData.tags}
                  onChange={(tags) => setFormData({ ...formData, tags })}
                  placeholder="輸入標籤後按 Enter 新增"
                  maxTags={10}
                  suggestions={tagSuggestions}
                  showSuggestions={true}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogType(null)}>
                取消
              </Button>
              <Button onClick={handleSaveProgram}>
                {dialogType === "create" ? "建立" : "儲存"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Copy Dialog */}
      {dialogType === "copy" && selectedProgram && (
        <Dialog open={true} onOpenChange={() => setDialogType(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>複製課程到班級</DialogTitle>
              <DialogDescription>
                將「{selectedProgram.name}」複製到指定班級
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div>
                <Label htmlFor="classroom">目標班級 *</Label>
                <Select
                  value={copyData.targetClassroomId}
                  onValueChange={(value) =>
                    setCopyData({ ...copyData, targetClassroomId: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="選擇班級" />
                  </SelectTrigger>
                  <SelectContent>
                    {classrooms.map((classroom) => (
                      <SelectItem
                        key={classroom.id}
                        value={classroom.id.toString()}
                      >
                        {classroom.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="newName">新課程名稱</Label>
                <Input
                  id="newName"
                  value={copyData.newName}
                  onChange={(e) =>
                    setCopyData({ ...copyData, newName: e.target.value })
                  }
                  placeholder="保留原名或輸入新名稱"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogType(null)}>
                取消
              </Button>
              <Button
                onClick={handleConfirmCopy}
                disabled={!copyData.targetClassroomId}
              >
                確認複製
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Delete Dialog */}
      {dialogType === "delete" && selectedProgram && (
        <Dialog open={true} onOpenChange={() => setDialogType(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>確認刪除</DialogTitle>
              <DialogDescription>
                確定要刪除「{selectedProgram.name}
                」嗎？此操作將進行軟刪除，資料仍會保留在系統中。
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogType(null)}>
                取消
              </Button>
              <Button variant="destructive" onClick={handleConfirmDelete}>
                確認刪除
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </TeacherLayout>
  );
}
