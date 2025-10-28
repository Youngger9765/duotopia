import { useState, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import TeacherLayout from "@/components/TeacherLayout";
import StudentTable, { Student } from "@/components/StudentTable";
import { StudentDialogs } from "@/components/StudentDialogs";
import { ProgramDialog } from "@/components/ProgramDialog";
import { LessonDialog } from "@/components/LessonDialog";
import CreateProgramDialog from "@/components/CreateProgramDialog";
import ContentTypeDialog from "@/components/ContentTypeDialog";
import ReadingAssessmentPanel from "@/components/ReadingAssessmentPanel";
import { AssignmentDialog } from "@/components/AssignmentDialog";
import { StudentCompletionDashboard } from "@/components/StudentCompletionDashboard";
import { RecursiveTreeAccordion } from "@/components/shared/RecursiveTreeAccordion";
import { programTreeConfig } from "@/components/shared/programTreeConfig";
import {
  ArrowLeft,
  Users,
  BookOpen,
  Plus,
  Edit,
  FileText,
  X,
  Save,
  Mic,
  Trash2,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import {
  Content,
  Assignment,
  Lesson,
  Program,
  ClassroomInfo,
  ContentItem,
  DialogType,
} from "@/types";

// Type compatibility for ReadingAssessmentPanel
interface ReadingAssessmentContent {
  id?: number;
  title?: string;
  items?: Array<{
    id: string | number;
    text: string;
    definition: string;
    audioUrl?: string;
    audio_url?: string;
    translation?: string;
    audioSettings?: {
      accent: string;
      gender: string;
      speed: string;
    };
  }>;
  target_wpm?: number;
  target_accuracy?: number;
  time_limit_seconds?: number;
}

interface ClassroomDetailProps {
  isTemplateMode?: boolean;
}

export default function ClassroomDetail({
  isTemplateMode = false,
}: ClassroomDetailProps) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [classroom, setClassroom] = useState<ClassroomInfo | null>(null);
  const [templateProgram, setTemplateProgram] = useState<Program | null>(null);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(
    isTemplateMode ? "programs" : "students",
  );

  // Teacher subscription state
  const [canAssignHomework, setCanAssignHomework] = useState<boolean>(false);
  const [teacherData, setTeacherData] = useState<{
    subscription_status?: string;
    days_remaining?: number;
  } | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);
  const [editingContent, setEditingContent] = useState<Content | null>(null);

  // Student dialog states
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [dialogType, setDialogType] = useState<DialogType>(null);

  // Program dialog states
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const [programDialogType, setProgramDialogType] = useState<
    "create" | "edit" | "delete" | null
  >(null);

  // Lesson dialog states
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null);
  const [lessonDialogType, setLessonDialogType] = useState<
    "create" | "edit" | "delete" | null
  >(null);
  const [lessonProgramId, setLessonProgramId] = useState<number | undefined>(
    undefined,
  );

  // Copy program dialog state
  const [showCopyDialog, setShowCopyDialog] = useState(false);

  // Content type dialog state
  const [showContentTypeDialog, setShowContentTypeDialog] = useState(false);
  const [contentLessonInfo, setContentLessonInfo] = useState<{
    programName: string;
    lessonName: string;
    lessonId: number;
  } | null>(null);

  // Reading Assessment Editor state
  const [showReadingEditor, setShowReadingEditor] = useState(false);
  const [editorLessonId, setEditorLessonId] = useState<number | null>(null);
  const [editorContentId, setEditorContentId] = useState<number | null>(null);

  // Assignment states
  const [showAssignmentDialog, setShowAssignmentDialog] = useState(false);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [selectedAssignment] = useState<Assignment | null>(null);
  const [showAssignmentDetails, setShowAssignmentDetails] = useState(false);

  useEffect(() => {
    if (id) {
      if (isTemplateMode) {
        fetchTemplateProgramData();
      } else {
        fetchClassroomDetail();
        fetchPrograms();
        fetchStudents();
        fetchAssignments();
        fetchTeacherPermissions();
      }
    }
  }, [id, isTemplateMode]);

  useEffect(() => {
    // Check URL parameters for tab switching
    const searchParams = new URLSearchParams(location.search);
    const tab = searchParams.get("tab");
    if (tab === "assignments") {
      setActiveTab("assignments");
    }
  }, [location.search]);

  const fetchClassroomDetail = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      const classrooms =
        (await apiClient.getTeacherClassrooms()) as ClassroomInfo[];
      const currentClassroom = classrooms.find((c) => c.id === Number(id));

      if (currentClassroom) {
        setClassroom(currentClassroom);
      } else {
        console.error("Classroom not found");
        navigate("/teacher/classrooms");
      }
    } catch (err) {
      console.error("Fetch classroom error:", err);
      navigate("/teacher/classrooms");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const refreshPrograms = async () => {
    if (isTemplateMode) {
      await fetchTemplateProgramData();
    } else {
      await fetchPrograms();
    }
  };

  const fetchTemplateProgramData = async () => {
    try {
      setLoading(true);

      const response = (await apiClient.getTemplateProgramDetail(
        Number(id),
      )) as Program;

      if (response) {
        // Convert template program data to match programs structure
        const programWithLessons: Program = {
          id: response.id,
          name: response.name,
          description: response.description,
          level: response.level,
          estimated_hours: response.estimated_hours,
          lessons: response.lessons || [],
        };

        setPrograms([programWithLessons]);
        setTemplateProgram(programWithLessons);

        // Set a mock classroom for UI consistency
        setClassroom({
          id: response.id,
          name: response.name,
          description: response.description,
          level: response.level || "A1",
          student_count: 0,
          students: [],
        });
      }
    } catch (err) {
      console.error("Fetch template program error:", err);
      navigate("/teacher/programs");
    } finally {
      setLoading(false);
    }
  };

  const fetchPrograms = async () => {
    try {
      // Use new API to get programs for this specific classroom
      const classroomPrograms = (await apiClient.getClassroomPrograms(
        Number(id),
      )) as Program[];

      // Fetch detailed info including lessons for each program
      const programsWithLessons = await Promise.all(
        classroomPrograms.map(async (program) => {
          try {
            const detail = (await apiClient.getProgramDetail(
              program.id,
            )) as Program;
            return {
              ...program,
              lessons: detail.lessons
                ? detail.lessons.sort(
                    (a: Lesson, b: Lesson) => a.order_index - b.order_index,
                  )
                : [],
            };
          } catch (err) {
            console.error(
              `Failed to fetch lessons for program ${program.id}:`,
              err,
            );
            return { ...program, lessons: [] };
          }
        }),
      );

      // Sort programs by order_index
      programsWithLessons.sort(
        (a, b) => (a.order_index || 0) - (b.order_index || 0),
      );
      setPrograms(programsWithLessons);
    } catch (err) {
      console.error("Fetch programs error:", err);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get(
        `/api/teachers/classrooms/${id}/students`,
      );
      setStudents(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error("Failed to fetch students:", err);
      setStudents([]);
    }
  };

  const fetchAssignments = async () => {
    try {
      const response = await apiClient.get(
        `/api/teachers/assignments?classroom_id=${id}`,
      );
      setAssignments(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error("Failed to fetch assignments:", err);
      setAssignments([]);
    }
  };

  const fetchTeacherPermissions = async () => {
    try {
      const dashboardData = (await apiClient.getTeacherDashboard()) as {
        can_assign_homework?: boolean;
        subscription_status?: string;
        days_remaining?: number;
      };
      setCanAssignHomework(dashboardData.can_assign_homework || false);
      setTeacherData({
        subscription_status: dashboardData.subscription_status,
        days_remaining: dashboardData.days_remaining,
      });
    } catch (err) {
      console.error("Failed to fetch teacher permissions:", err);
      setCanAssignHomework(false);
    }
  };

  const handleEditAssignment = (assignment: Assignment) => {
    // TODO: Open edit dialog with assignment data
    toast.info(`準備編輯作業: ${assignment.title}`);
    setShowAssignmentDetails(false);
    // In production: open edit dialog
    // setEditingAssignment(assignment);
    // setShowEditAssignmentDialog(true);
  };

  const handleDeleteAssignment = async (assignment: Assignment) => {
    if (
      confirm(
        `確定要刪除作業「${assignment.title}」嗎？此操作將進行軟刪除，資料仍會保留。`,
      )
    ) {
      try {
        await apiClient.delete(`/api/teachers/assignments/${assignment.id}`);
        toast.success(`作業「${assignment.title}」已刪除`);
        setShowAssignmentDetails(false);
        fetchAssignments(); // Refresh the list
      } catch (error) {
        console.error("Failed to delete assignment:", error);
        toast.error("刪除作業失敗，請稍後再試");
      }
    }
  };

  const handleContentClick = (content: Content) => {
    // 如果點擊的是同一個 content，則關閉 panel
    if (isPanelOpen && selectedContent?.id === content.id) {
      setIsPanelOpen(false);
      setSelectedContent(null);
      setEditingContent(null);
      return;
    }

    // For reading_assessment type, use side panel for viewing/editing
    if (content.type === "reading_assessment") {
      setSelectedContent(content);
      setEditingContent({
        id: content.id,
        title: content.title,
        items_count: content.items_count,
        items: content.items || [],
        lesson_id: content.lesson_id,
        type: content.type,
        estimated_time: content.estimated_time,
        target_wpm: content.target_wpm,
        target_accuracy: content.target_accuracy,
        time_limit_seconds: content.time_limit_seconds,
        programName: content.programName,
        lessonName: content.lessonName,
      });
      setIsPanelOpen(true);
    } else {
      // For other content types, use the existing panel
      setSelectedContent(content);
      setEditingContent({
        id: content.id,
        title: content.title,
        items_count: content.items_count,
        items: content.items || [],
        lesson_id: content.lesson_id,
        type: content.type,
        estimated_time: content.estimated_time,
        target_wpm: content.target_wpm || 60,
        target_accuracy: content.target_accuracy || 0.8,
        time_limit_seconds: content.time_limit_seconds || 600,
        programName: content.programName,
        lessonName: content.lessonName,
      });
      setIsPanelOpen(true);
    }
  };

  const closePanel = () => {
    setIsPanelOpen(false);
    setTimeout(() => {
      setSelectedContent(null);
      setEditingContent(null);
    }, 300);
  };

  const handleAddContentItem = () => {
    if (!editingContent) return;

    const newItem = {
      text: "",
      translation: "",
    };

    setEditingContent({
      ...editingContent,
      items: [...(editingContent.items || []), newItem],
    });
  };

  const handleUpdateContentItem = (
    index: number,
    field: "text" | "translation",
    value: string,
  ) => {
    if (!editingContent) return;

    const updatedItems = [...(editingContent.items || [])];
    updatedItems[index] = {
      ...updatedItems[index],
      [field]: value,
    };

    setEditingContent({
      ...editingContent,
      items: updatedItems,
    });
  };

  const handleDeleteContentItem = (index: number) => {
    if (!editingContent) return;

    const updatedItems =
      editingContent.items?.filter(
        (_: ContentItem, i: number) => i !== index,
      ) || [];
    setEditingContent({
      ...editingContent,
      items: updatedItems,
    });
  };

  const handleSaveContent = async () => {
    if (!editingContent || !selectedContent) return;

    try {
      // Update content via API
      await apiClient.updateContent(editingContent.id, {
        title: editingContent.title,
        items: editingContent.items,
        target_wpm: parseInt(String(editingContent.target_wpm || 60)),
        target_accuracy:
          parseFloat(String(editingContent.target_accuracy || 80)) / 100,
        time_limit_seconds: parseInt(
          String(editingContent.time_limit_seconds || 180),
        ),
      });

      toast.success("內容已更新成功");
      await refreshPrograms();
      closePanel();
    } catch (error) {
      console.error("Failed to update content:", error);
      toast.error("更新內容失敗，請稍後再試");
    }
  };

  // Student CRUD handlers
  const handleCreateStudent = () => {
    setSelectedStudent(null);
    setDialogType("create");
  };

  const handleViewStudent = (student: Student) => {
    setSelectedStudent(student);
    setDialogType("view");
  };

  const handleEditStudent = (student: Student) => {
    setSelectedStudent(student);
    setDialogType("edit");
  };

  const handleResetPassword = async (student: Student) => {
    if (!confirm(`確定要將 ${student.name} 的密碼重設為預設密碼嗎？`)) {
      return;
    }

    try {
      await apiClient.resetStudentPassword(student.id);
      // Refresh data
      fetchClassroomDetail();
    } catch (error) {
      console.error("Failed to reset password:", error);
      alert("重設密碼失敗，請稍後再試");
    }
  };

  const handleSaveStudent = async () => {
    // Refresh data after save (parallel requests, no loading spinner)
    await Promise.all([
      fetchStudents(), // 更新學生列表（派作業需要）
      fetchClassroomDetail(false), // 更新班級資訊（學生數統計），不顯示載入畫面
    ]);
  };

  const handleDeleteStudent = async () => {
    // Refresh data after delete (parallel requests, no loading spinner)
    await Promise.all([
      fetchStudents(), // 更新學生列表（派作業需要）
      fetchClassroomDetail(false), // 更新班級資訊（學生數統計），不顯示載入畫面
    ]);
  };

  const handleCloseDialog = () => {
    setSelectedStudent(null);
    setDialogType(null);
  };

  const handleSwitchToEdit = () => {
    // Switch from view to edit mode
    setDialogType("edit");
  };

  const handleAddLesson = (programId: number) => {
    setSelectedLesson(null);
    setLessonProgramId(programId);
    setLessonDialogType("create");
  };

  const handleEditProgram = (programId: number) => {
    const program = programs.find((p) => p.id === programId);
    if (program) {
      setSelectedProgram(program);
      setProgramDialogType("edit");
    }
  };

  const handleEditLesson = (programId: number, lessonId: number) => {
    const program = programs.find((p) => p.id === programId);
    const lesson = program?.lessons?.find((l: Lesson) => l.id === lessonId);
    if (lesson) {
      setSelectedLesson(lesson);
      setLessonProgramId(programId);
      setLessonDialogType("edit");
    }
  };

  const handleDeleteProgram = (programId: number) => {
    const program = programs.find((p) => p.id === programId);
    if (program) {
      setSelectedProgram(program);
      setProgramDialogType("delete");
    }
  };

  const handleDeleteLesson = (programId: number, lessonId: number) => {
    const program = programs.find((p) => p.id === programId);
    const lesson = program?.lessons?.find((l: Lesson) => l.id === lessonId);
    if (lesson) {
      setSelectedLesson(lesson);
      setLessonProgramId(programId);
      setLessonDialogType("delete");
    }
  };

  const handleSaveProgram = (program: Program) => {
    if (programDialogType === "create") {
      setPrograms([...programs, program]);
    } else if (programDialogType === "edit") {
      setPrograms(programs.map((p) => (p.id === program.id ? program : p)));
    }
    fetchPrograms(); // Refresh data
  };

  const handleDeleteProgramConfirm = (programId: number) => {
    setPrograms(programs.filter((p) => p.id !== programId));
    fetchPrograms(); // Refresh data
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleSaveLesson = (lesson: any) => {
    const savedLesson = lesson;
    // 直接更新 state 而不是重新載入整個頁面
    if (lessonDialogType === "create" && lessonProgramId) {
      // 新增單元：找到對應的 program 並加入新單元
      setPrograms((prevPrograms) =>
        prevPrograms.map((program) => {
          if (program.id === lessonProgramId) {
            return {
              ...program,
              lessons: [...(program.lessons || []), savedLesson],
            };
          }
          return program;
        }),
      );
      toast.success(`單元「${savedLesson.name}」已新增`);
    } else if (lessonDialogType === "edit") {
      // 編輯單元：更新對應的單元
      setPrograms((prevPrograms) =>
        prevPrograms.map((program) => ({
          ...program,
          lessons:
            program.lessons?.map((lesson) =>
              lesson.id === savedLesson.id ? savedLesson : lesson,
            ) || [],
        })),
      );
      toast.success(`單元「${savedLesson.name}」已更新`);
    }
  };

  const handleDeleteContent = async (
    lessonId: number,
    contentId: number,
    contentTitle: string,
  ) => {
    if (!confirm(`確定要刪除內容「${contentTitle}」嗎？此操作無法復原。`)) {
      return;
    }

    try {
      // 呼叫 API 刪除內容
      await apiClient.deleteContent(contentId);

      // 更新本地狀態 - 從對應的 lesson 中移除該 content
      setPrograms((prevPrograms) =>
        prevPrograms.map((program) => ({
          ...program,
          lessons: program.lessons?.map((lesson: Lesson) => {
            if (lesson.id === lessonId) {
              return {
                ...lesson,
                contents: lesson.contents?.filter((c) => c.id !== contentId),
              };
            }
            return lesson;
          }),
        })),
      );

      toast.success(`內容「${contentTitle}」已刪除`);
    } catch (error) {
      console.error("Failed to delete content:", error);
      toast.error("刪除內容失敗，請稍後再試");
    }
  };

  const handleDeleteLessonConfirm = async (lessonId: number) => {
    try {
      // 找到包含這個 lesson 的 program
      const programWithLesson = programs.find((p) =>
        p.lessons?.some((l) => l.id === lessonId),
      );

      if (!programWithLesson) {
        toast.error("找不到單元所屬的課程");
        return;
      }

      // 公版課程使用不同的 API endpoint
      if (isTemplateMode) {
        // 公版課程直接使用 lesson ID 刪除
        await apiClient.deleteTemplateLesson(lessonId);
      } else {
        // 一般課程使用 lesson ID 刪除
        await apiClient.deleteLesson(lessonId);
      }

      // 更新本地狀態
      const updatedPrograms = programs.map((program) => {
        if (program.lessons) {
          return {
            ...program,
            lessons: program.lessons.filter((l) => l.id !== lessonId),
          };
        }
        return program;
      });
      setPrograms(updatedPrograms);

      toast.success("單元已刪除");
    } catch (error) {
      console.error("Failed to delete lesson:", error);
      toast.error("刪除單元失敗，請稍後再試");
    }
  };

  const handleReorderPrograms = async (
    dragIndex: number,
    dropIndex: number,
  ) => {
    const newPrograms = [...programs];
    const [draggedItem] = newPrograms.splice(dragIndex, 1);
    newPrograms.splice(dropIndex, 0, draggedItem);

    // Update order_index for each program
    const updatedPrograms = newPrograms.map((program, index) => ({
      ...program,
      order_index: index + 1,
    }));

    setPrograms(updatedPrograms);

    // Save new order to backend
    try {
      const orderData = updatedPrograms.map((program, index) => ({
        id: program.id,
        order_index: index + 1,
      }));
      await apiClient.reorderPrograms(orderData);
      console.log("Programs reordered and saved");
    } catch (error) {
      console.error("Failed to save program order:", error);
      // 可選：恢復原始順序
      fetchPrograms();
    }
  };

  const handleReorderLessons = async (
    programId: number,
    dragIndex: number,
    dropIndex: number,
  ) => {
    const programIndex = programs.findIndex((p) => p.id === programId);
    if (programIndex !== -1 && programs[programIndex].lessons) {
      const updatedPrograms = [...programs];
      const lessons = [...updatedPrograms[programIndex].lessons!];

      // Reorder lessons
      const [draggedItem] = lessons.splice(dragIndex, 1);
      lessons.splice(dropIndex, 0, draggedItem);

      // Update order_index for each lesson
      const reorderedLessons = lessons.map((lesson, index) => ({
        ...lesson,
        order_index: index + 1,
      }));

      updatedPrograms[programIndex].lessons = reorderedLessons;
      setPrograms(updatedPrograms);

      // Save new order to backend
      try {
        const orderData = reorderedLessons.map((lesson, index) => ({
          id: lesson.id,
          order_index: index + 1,
        }));
        await apiClient.reorderLessons(programId, orderData);
        console.log(`Lessons reordered and saved for program ${programId}`);
      } catch (error) {
        console.error("Failed to save lesson order:", error);
        // 可選：恢復原始順序
        fetchPrograms();
      }
    }
  };

  const handleReorderContents = async (
    lessonId: number,
    fromIndex: number,
    toIndex: number,
  ) => {
    // Find the lesson
    let targetLesson: Lesson | undefined;
    let targetProgram: Program | undefined;

    for (const program of programs) {
      const lesson = program.lessons?.find((l) => l.id === lessonId);
      if (lesson) {
        targetLesson = lesson;
        targetProgram = program;
        break;
      }
    }

    if (!targetLesson || !targetLesson.contents || !targetProgram) return;

    const originalPrograms = [...programs];

    // Immediate UI update
    const newContents = [...targetLesson.contents];
    const [movedItem] = newContents.splice(fromIndex, 1);
    newContents.splice(toIndex, 0, movedItem);

    setPrograms((prevPrograms) =>
      prevPrograms.map((p) => {
        if (p.id === targetProgram!.id) {
          return {
            ...p,
            lessons: p.lessons?.map((l) =>
              l.id === lessonId ? { ...l, contents: newContents } : l,
            ),
          };
        }
        return p;
      }),
    );

    try {
      // Prepare order data
      const orderData = newContents.map((content, index) => ({
        id: content.id,
        order_index: index,
      }));

      await apiClient.reorderContents(lessonId, orderData);
      toast.success("排序成功");
    } catch (err) {
      console.error("Failed to reorder contents:", err);
      toast.error("排序失敗");
      // Revert on error
      setPrograms(originalPrograms);
    }
  };

  const handleCreateContent = (programId: number, lessonId: number) => {
    const program = programs.find((p) => p.id === programId);
    const lesson = program?.lessons?.find((l) => l.id === lessonId);
    if (lesson && program) {
      setContentLessonInfo({
        programName: program.name,
        lessonName: lesson.name,
        lessonId: lesson.id,
      });
      setShowContentTypeDialog(true);
    }
  };

  const handleContentTypeSelect = async (selection: {
    type: string;
    lessonId: number;
    programName: string;
    lessonName: string;
  }) => {
    // For reading_assessment, use popup for new content creation
    if (selection.type === "reading_assessment") {
      setEditorLessonId(selection.lessonId);
      setEditorContentId(null); // null for new content
      setShowReadingEditor(true);
      setShowContentTypeDialog(false);
    } else {
      // For other content types, create directly
      try {
        const contentTypeNames: Record<string, string> = {
          reading_assessment: "朗讀錄音練習",
        };

        const title = contentTypeNames[selection.type] || "新內容";
        const items: Array<{ text: string; translation?: string }> = [];

        await apiClient.createContent(selection.lessonId, {
          type: selection.type,
          title: title,
          items: items,
          target_wpm: 60,
          target_accuracy: 0.8,
        });

        toast.success("內容已創建成功");
        await refreshPrograms();
      } catch (error) {
        console.error("Failed to create content:", error);
        toast.error("創建內容失敗，請稍後再試");
      }
    }
  };

  if (loading) {
    return (
      <TeacherLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">載入中...</p>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  if (!classroom && !isTemplateMode) {
    return (
      <TeacherLayout>
        <div className="text-center py-12">
          <p className="text-gray-500">找不到班級資料</p>
          <Button
            className="mt-4"
            onClick={() => navigate("/teacher/classrooms")}
          >
            返回班級列表
          </Button>
        </div>
      </TeacherLayout>
    );
  }

  if (isTemplateMode && !templateProgram) {
    return (
      <TeacherLayout>
        <div className="text-center py-12">
          <p className="text-gray-500">找不到模板課程資料</p>
          <Button
            className="mt-4"
            onClick={() => navigate("/teacher/programs")}
          >
            返回模板課程列表
          </Button>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div className="relative">
        <div
          className={`transition-all duration-300 ${isPanelOpen ? "mr-[50%]" : ""}`}
        >
          {/* Header */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6 space-y-4 sm:space-y-0">
            <div className="flex items-center space-x-2 sm:space-x-4 w-full sm:w-auto">
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  navigate(
                    isTemplateMode
                      ? "/teacher/programs"
                      : "/teacher/classrooms",
                  )
                }
                className="flex-shrink-0"
              >
                <ArrowLeft className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">返回</span>
              </Button>
              <div className="min-w-0 flex-1">
                <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 truncate">
                  {isTemplateMode ? templateProgram?.name : classroom?.name}
                </h2>
                {(isTemplateMode
                  ? templateProgram?.description
                  : classroom?.description) && (
                  <p className="text-sm sm:text-base text-gray-600 mt-1 truncate">
                    {isTemplateMode
                      ? templateProgram?.description
                      : classroom?.description}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Stats - only show for classroom mode */}
          {!isTemplateMode && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-4 sm:mb-6">
              <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs sm:text-sm text-gray-600">學生數</p>
                    <p className="text-xl sm:text-2xl font-bold">
                      {classroom?.student_count || 0}
                    </p>
                  </div>
                  <Users className="h-6 w-6 sm:h-8 sm:w-8 text-blue-500" />
                </div>
              </div>
              <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs sm:text-sm text-gray-600">課程數</p>
                    <p className="text-xl sm:text-2xl font-bold">
                      {programs.length}
                    </p>
                  </div>
                  <BookOpen className="h-6 w-6 sm:h-8 sm:w-8 text-green-500" />
                </div>
              </div>
              <div className="bg-white p-3 sm:p-4 rounded-lg shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs sm:text-sm text-gray-600">等級</p>
                    <p className="text-xl sm:text-2xl font-bold">
                      {classroom?.level || "A1"}
                    </p>
                  </div>
                  <div className="h-6 w-6 sm:h-8 sm:w-8 bg-purple-100 rounded-full flex items-center justify-center">
                    <span className="text-purple-600 font-bold text-sm sm:text-base">
                      L
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow-sm border">
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              <div className="border-b bg-gray-50 px-3 sm:px-6 py-3">
                {isTemplateMode ? (
                  /* Template mode - no tabs, just show programs */
                  <div className="h-12" />
                ) : (
                  <TabsList className="grid w-full max-w-[700px] grid-cols-3 h-auto sm:h-12 bg-white dark:bg-gray-800 border dark:border-gray-700 gap-2 p-2">
                    <TabsTrigger
                      value="students"
                      className="data-[state=active]:bg-blue-500 data-[state=active]:text-white dark:data-[state=active]:bg-blue-600 dark:text-gray-300 dark:data-[state=active]:text-white text-xs sm:text-base font-medium py-3 sm:py-2 flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2"
                    >
                      <Users className="h-5 w-5 sm:h-5 sm:w-5" />
                      <span className="hidden sm:inline">學生列表</span>
                      <span className="sm:hidden text-[10px]">學生</span>
                    </TabsTrigger>
                    <TabsTrigger
                      value="programs"
                      className="data-[state=active]:bg-blue-500 data-[state=active]:text-white dark:data-[state=active]:bg-blue-600 dark:text-gray-300 dark:data-[state=active]:text-white text-xs sm:text-base font-medium py-3 sm:py-2 flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2"
                    >
                      <BookOpen className="h-5 w-5 sm:h-5 sm:w-5" />
                      <span className="hidden sm:inline">課程列表</span>
                      <span className="sm:hidden text-[10px]">課程</span>
                    </TabsTrigger>
                    <TabsTrigger
                      value="assignments"
                      className={`data-[state=active]:bg-blue-500 data-[state=active]:text-white dark:data-[state=active]:bg-blue-600 dark:text-gray-300 dark:data-[state=active]:text-white text-xs sm:text-base font-medium py-3 sm:py-2 flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 ${
                        !canAssignHomework
                          ? "opacity-50 cursor-not-allowed"
                          : ""
                      }`}
                      disabled={!canAssignHomework}
                      onClick={(e) => {
                        if (!canAssignHomework) {
                          e.preventDefault();
                          toast.error(
                            "您的訂閱已過期，無法使用作業管理功能。請先充值續訂。",
                          );
                        }
                      }}
                    >
                      <FileText className="h-5 w-5 sm:h-5 sm:w-5" />
                      <span className="hidden sm:inline">作業管理</span>
                      <span className="sm:hidden text-[10px]">作業</span>
                    </TabsTrigger>
                  </TabsList>
                )}
              </div>

              {/* Students Tab - only show for classroom mode */}
              {!isTemplateMode && (
                <TabsContent value="students" className="p-3 sm:p-6">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 space-y-2 sm:space-y-0">
                    <h3 className="text-base sm:text-lg font-semibold">
                      班級學生
                    </h3>
                    <Button
                      size="sm"
                      onClick={handleCreateStudent}
                      className="w-full sm:w-auto"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      新增學生
                    </Button>
                  </div>

                  <StudentTable
                    students={classroom?.students || []}
                    showClassroom={false}
                    onAddStudent={handleCreateStudent}
                    onViewStudent={handleViewStudent}
                    onEditStudent={handleEditStudent}
                    onResetPassword={handleResetPassword}
                    emptyMessage="此班級尚無學生"
                  />
                </TabsContent>
              )}

              {/* Programs Tab */}
              <TabsContent value="programs" className="p-3 sm:p-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-3">
                  <h3 className="text-base sm:text-lg font-semibold dark:text-gray-100">
                    {isTemplateMode ? "模板課程內容" : "班級課程"}
                  </h3>
                  {!isTemplateMode && (
                    <Button
                      size="sm"
                      onClick={() => setShowCopyDialog(true)}
                      className="w-full sm:w-auto"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      建立課程
                    </Button>
                  )}
                </div>

                <RecursiveTreeAccordion
                  data={programs}
                  config={programTreeConfig}
                  title=""
                  showCreateButton={false}
                  onEdit={(item, level, parentId) => {
                    if (level === 0) handleEditProgram(item.id);
                    else if (level === 1)
                      handleEditLesson(parentId as number, item.id);
                  }}
                  onDelete={(item, level, parentId) => {
                    if (level === 0) handleDeleteProgram(item.id);
                    else if (level === 1)
                      handleDeleteLesson(parentId as number, item.id);
                    else if (level === 2)
                      handleDeleteContent(
                        parentId as number,
                        item.id,
                        item.title,
                      );
                  }}
                  onClick={(item, level, parentId) => {
                    if (level === 2) {
                      const program = programs.find((p) =>
                        p.lessons?.some((l) => l.id === parentId),
                      );
                      const lesson = program?.lessons?.find(
                        (l) => l.id === parentId,
                      );
                      handleContentClick({
                        ...item,
                        lesson_id: parentId as number,
                        lessonName: lesson?.name,
                        programName: program?.name,
                      });
                    }
                  }}
                  onCreate={(level, parentId) => {
                    if (level === 1) {
                      handleAddLesson(parentId as number);
                    } else if (level === 2) {
                      const program = programs.find((p) =>
                        p.lessons?.some((l) => l.id === parentId),
                      );
                      if (program) {
                        handleCreateContent(program.id, parentId as number);
                      }
                    }
                  }}
                  onReorder={(fromIndex, toIndex, level, parentId) => {
                    if (level === 0) handleReorderPrograms(fromIndex, toIndex);
                    else if (level === 1)
                      handleReorderLessons(
                        parentId as number,
                        fromIndex,
                        toIndex,
                      );
                    else if (level === 2)
                      handleReorderContents(
                        parentId as number,
                        fromIndex,
                        toIndex,
                      );
                  }}
                />
              </TabsContent>

              {/* Assignments Tab - only show for classroom mode */}
              {!isTemplateMode && (
                <TabsContent value="assignments" className="p-3 sm:p-6">
                  <div className="space-y-4 sm:space-y-6">
                    {/* Header with Create Button */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <h3 className="text-base sm:text-lg font-semibold dark:text-gray-100">
                        作業列表
                      </h3>
                      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
                        {!canAssignHomework && teacherData && (
                          <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 bg-yellow-50 dark:bg-yellow-900/20 px-3 py-2 rounded-lg border border-yellow-200 dark:border-yellow-800">
                            <span className="font-medium">⚠️ 訂閱已過期</span>
                            <span className="text-xs ml-2">
                              {teacherData.subscription_status === "subscribed"
                                ? `剩餘 ${teacherData.days_remaining || 0} 天`
                                : "需要訂閱才能指派作業"}
                            </span>
                          </div>
                        )}
                        <Button
                          onClick={() => {
                            if (!canAssignHomework) {
                              toast.error(
                                "您的訂閱已過期，無法指派作業。請先充值續訂。",
                              );
                              return;
                            }
                            setShowAssignmentDialog(true);
                          }}
                          disabled={!canAssignHomework}
                          className={`w-full sm:w-auto h-12 min-h-12 ${
                            canAssignHomework
                              ? "bg-blue-500 hover:bg-blue-600 text-white"
                              : "bg-gray-300 text-gray-500 cursor-not-allowed"
                          }`}
                        >
                          <Plus className="h-4 w-4 mr-2" />
                          指派新作業
                        </Button>
                      </div>
                    </div>

                    {/* Assignment Stats - Using Real Data */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 sm:p-4 border dark:border-blue-800">
                        <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                          總作業數
                        </div>
                        <div className="text-xl sm:text-2xl font-bold text-blue-600 dark:text-blue-400">
                          {assignments.length}
                        </div>
                      </div>
                      <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 sm:p-4 border dark:border-green-800">
                        <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                          已完成
                        </div>
                        <div className="text-xl sm:text-2xl font-bold text-green-600 dark:text-green-400">
                          {
                            assignments.filter((a) => a.status === "completed")
                              .length
                          }
                        </div>
                      </div>
                      <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 sm:p-4 border dark:border-yellow-800">
                        <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                          進行中
                        </div>
                        <div className="text-xl sm:text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                          {
                            assignments.filter(
                              (a) =>
                                a.status === "in_progress" ||
                                a.status === "not_started",
                            ).length
                          }
                        </div>
                      </div>
                      <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 sm:p-4 border dark:border-red-800">
                        <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                          已逾期
                        </div>
                        <div className="text-xl sm:text-2xl font-bold text-red-600 dark:text-red-400">
                          {
                            assignments.filter((a) => a.status === "overdue")
                              .length
                          }
                        </div>
                      </div>
                    </div>

                    {/* Assignment List */}
                    {assignments.length > 0 ? (
                      <>
                        {/* Mobile: Card Layout */}
                        <div className="md:hidden space-y-3">
                          {assignments.map((assignment) => {
                            const completionRate =
                              assignment.completion_rate || 0;
                            const contentTypeLabels: Record<
                              string,
                              { label: string; color: string }
                            > = {
                              READING_ASSESSMENT: {
                                label: "朗讀評測",
                                color:
                                  "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
                              },
                              SPEAKING_PRACTICE: {
                                label: "口說練習",
                                color:
                                  "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
                              },
                              SPEAKING_SCENARIO: {
                                label: "情境對話",
                                color:
                                  "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
                              },
                              LISTENING_CLOZE: {
                                label: "聽力填空",
                                color:
                                  "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
                              },
                              SENTENCE_MAKING: {
                                label: "造句練習",
                                color:
                                  "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300",
                              },
                              SPEAKING_QUIZ: {
                                label: "口說測驗",
                                color:
                                  "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
                              },
                            };
                            const typeInfo = contentTypeLabels[
                              assignment.content_type || ""
                            ] || {
                              label: assignment.content_type || "未知類型",
                              color:
                                "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
                            };

                            return (
                              <div
                                key={assignment.id}
                                className="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg p-4 space-y-3"
                              >
                                {/* Title & Type */}
                                <div className="flex items-start justify-between gap-3">
                                  <div className="flex-1 min-w-0">
                                    <h4 className="font-medium text-gray-900 dark:text-gray-100 truncate">
                                      {assignment.title}
                                    </h4>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 truncate mt-1">
                                      {assignment.instructions || "無說明"}
                                    </p>
                                  </div>
                                  <span
                                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap flex-shrink-0 ${typeInfo.color}`}
                                  >
                                    {typeInfo.label}
                                  </span>
                                </div>

                                {/* Details Grid */}
                                <div className="grid grid-cols-2 gap-3 text-sm">
                                  <div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400">
                                      指派對象
                                    </div>
                                    <div className="font-medium text-gray-900 dark:text-gray-100 mt-1">
                                      {assignment.student_count
                                        ? `${assignment.student_count} 人`
                                        : "全班"}
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400">
                                      截止日期
                                    </div>
                                    <div className="font-medium text-gray-900 dark:text-gray-100 mt-1">
                                      {assignment.due_date
                                        ? new Date(
                                            assignment.due_date,
                                          ).toLocaleDateString("zh-TW")
                                        : "無期限"}
                                    </div>
                                  </div>
                                </div>

                                {/* Progress Bar */}
                                <div>
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs text-gray-500 dark:text-gray-400">
                                      完成進度
                                    </span>
                                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                      {completionRate}%
                                    </span>
                                  </div>
                                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                    <div
                                      className="bg-green-500 dark:bg-green-600 h-2 rounded-full transition-all"
                                      style={{ width: `${completionRate}%` }}
                                    ></div>
                                  </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="flex gap-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    className="flex-1 h-12 min-h-12 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-800 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                                    onClick={() => {
                                      navigate(
                                        `/teacher/classroom/${id}/assignment/${assignment.id}`,
                                      );
                                    }}
                                  >
                                    查看詳情
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    className="flex-1 h-12 min-h-12 text-green-600 dark:text-green-400 border-green-200 dark:border-green-800 hover:bg-green-50 dark:hover:bg-green-900/20"
                                    onClick={() => {
                                      navigate(
                                        `/teacher/classroom/${id}/assignment/${assignment.id}/preview`,
                                      );
                                    }}
                                  >
                                    預覽示範
                                  </Button>
                                </div>
                              </div>
                            );
                          })}
                        </div>

                        {/* Desktop: Table Layout */}
                        <div className="hidden md:block border dark:border-gray-700 rounded-lg overflow-hidden">
                          <table className="w-full">
                            <thead className="bg-gray-50 dark:bg-gray-700 border-b dark:border-gray-600">
                              <tr>
                                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-200">
                                  作業標題
                                </th>
                                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-200">
                                  內容類型
                                </th>
                                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-200">
                                  指派對象
                                </th>
                                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-200">
                                  截止日期
                                </th>
                                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-200">
                                  完成狀態
                                </th>
                                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-200">
                                  操作
                                </th>
                              </tr>
                            </thead>
                            <tbody>
                              {assignments.map((assignment) => {
                                const completionRate =
                                  assignment.completion_rate || 0;
                                const contentTypeLabels: Record<
                                  string,
                                  { label: string; color: string }
                                > = {
                                  READING_ASSESSMENT: {
                                    label: "朗讀評測",
                                    color:
                                      "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
                                  },
                                  SPEAKING_PRACTICE: {
                                    label: "口說練習",
                                    color:
                                      "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
                                  },
                                  SPEAKING_SCENARIO: {
                                    label: "情境對話",
                                    color:
                                      "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
                                  },
                                  LISTENING_CLOZE: {
                                    label: "聽力填空",
                                    color:
                                      "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
                                  },
                                  SENTENCE_MAKING: {
                                    label: "造句練習",
                                    color:
                                      "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300",
                                  },
                                  SPEAKING_QUIZ: {
                                    label: "口說測驗",
                                    color:
                                      "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
                                  },
                                };
                                const typeInfo = contentTypeLabels[
                                  assignment.content_type || ""
                                ] || {
                                  label: assignment.content_type || "未知類型",
                                  color:
                                    "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
                                };

                                return (
                                  <tr
                                    key={assignment.id}
                                    className="border-b hover:bg-gray-50 dark:hover:bg-gray-700/50 dark:border-gray-600"
                                  >
                                    <td className="px-4 py-3">
                                      <div className="font-medium dark:text-gray-100">
                                        {assignment.title}
                                      </div>
                                      <div className="text-sm text-gray-500 dark:text-gray-400 line-clamp-1">
                                        {assignment.instructions || "無說明"}
                                      </div>
                                    </td>
                                    <td className="px-4 py-3">
                                      <span
                                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${typeInfo.color}`}
                                      >
                                        {typeInfo.label}
                                      </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm dark:text-gray-300">
                                      {assignment.student_count
                                        ? `${assignment.student_count} 人`
                                        : "全班"}
                                    </td>
                                    <td className="px-4 py-3 text-sm dark:text-gray-300">
                                      {assignment.due_date
                                        ? new Date(
                                            assignment.due_date,
                                          ).toLocaleDateString("zh-TW")
                                        : "無期限"}
                                    </td>
                                    <td className="px-4 py-3">
                                      <div className="flex items-center gap-2">
                                        <div className="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                          <div
                                            className="bg-green-500 dark:bg-green-600 h-2 rounded-full"
                                            style={{
                                              width: `${completionRate}%`,
                                            }}
                                          ></div>
                                        </div>
                                        <span className="text-sm text-gray-600 dark:text-gray-400 w-10">
                                          {completionRate}%
                                        </span>
                                      </div>
                                    </td>
                                    <td className="px-4 py-3">
                                      <div className="flex gap-2">
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          className="text-blue-600 hover:text-blue-700 dark:text-blue-400 h-10 min-h-10"
                                          onClick={() => {
                                            navigate(
                                              `/teacher/classroom/${id}/assignment/${assignment.id}`,
                                            );
                                          }}
                                        >
                                          查看詳情
                                        </Button>
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          className="text-green-600 hover:text-green-700 dark:text-green-400 h-10 min-h-10"
                                          onClick={() => {
                                            navigate(
                                              `/teacher/classroom/${id}/assignment/${assignment.id}/preview`,
                                            );
                                          }}
                                        >
                                          預覽示範
                                        </Button>
                                      </div>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </>
                    ) : (
                      <div className="border dark:border-gray-700 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
                        尚未指派任何作業
                      </div>
                    )}
                  </div>
                </TabsContent>
              )}
            </Tabs>
          </div>
        </div>

        {/* Right Sliding Panel */}
        <div
          className={`fixed right-0 top-0 h-full w-1/2 bg-white shadow-xl border-l transform transition-transform duration-300 z-50 ${
            isPanelOpen ? "translate-x-0" : "translate-x-full"
          }`}
        >
          {selectedContent && (
            <div className="h-full flex flex-col">
              {/* Panel Header */}
              <div className="flex items-center justify-between p-4 border-b bg-gray-50">
                <div className="flex-1 mr-4">
                  <h3 className="font-semibold text-sm text-gray-600 mb-2">
                    內容編輯器
                  </h3>
                  <input
                    type="text"
                    value={editingContent?.title || selectedContent.title || ""}
                    onChange={(e) => {
                      if (editingContent) {
                        setEditingContent({
                          ...editingContent,
                          title: e.target.value,
                        });
                      }
                    }}
                    className="w-full px-3 py-1.5 border rounded-md text-lg font-medium"
                    placeholder="輸入標題"
                  />
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={closePanel}
                  className="hover:bg-gray-200"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>

              {/* Panel Content */}
              <div className="flex-1 overflow-y-auto p-4">
                {selectedContent.type === "reading_assessment" ? (
                  /* ReadingAssessmentPanel has its own save button */
                  <ReadingAssessmentPanel
                    content={selectedContent as ReadingAssessmentContent}
                    editingContent={
                      editingContent as ReadingAssessmentContent | undefined
                    }
                    onUpdateContent={(
                      updatedContent: Record<string, unknown>,
                    ) => {
                      setEditingContent(updatedContent as unknown as Content);
                    }}
                    onSave={handleSaveContent}
                  />
                ) : (
                  /* Other Content Types */
                  <div className="space-y-4">
                    {/* Content Info */}
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-sm font-medium text-blue-900">
                        {selectedContent.programName}
                      </p>
                      <p className="text-xs text-blue-700 mt-1">
                        {selectedContent.lessonName}
                      </p>
                    </div>

                    {/* Content Type Badge */}
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                        <FileText className="h-4 w-4 text-purple-600" />
                      </div>
                      <div>
                        <p className="font-medium">{selectedContent.type}</p>
                        <p className="text-sm text-gray-500">
                          {Array.isArray(selectedContent.items)
                            ? selectedContent.items.length
                            : selectedContent.items_count || 0}{" "}
                          個項目 • {selectedContent.estimated_time || "10 分鐘"}
                        </p>
                      </div>
                    </div>

                    {/* Content Items - 真實內容編輯介面 */}
                    <div className="space-y-3">
                      <h4 className="font-medium text-sm">內容項目</h4>
                      {editingContent &&
                      editingContent.items &&
                      editingContent.items.length > 0 ? (
                        editingContent.items.map(
                          (
                            item: {
                              text?: string;
                              translation?: string;
                              question?: string;
                              answer?: string;
                              options?: string[];
                            },
                            index: number,
                          ) => (
                            <div
                              key={index}
                              className="border rounded-lg p-3 space-y-2"
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">
                                  項目 {index + 1}
                                </span>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleDeleteContentItem(index)}
                                >
                                  <Trash2 className="h-3 w-3 text-red-500" />
                                </Button>
                              </div>
                              <input
                                type="text"
                                className="w-full px-3 py-2 border rounded-md text-sm"
                                placeholder="英文內容"
                                value={item.text || ""}
                                onChange={(e) =>
                                  handleUpdateContentItem(
                                    index,
                                    "text",
                                    e.target.value,
                                  )
                                }
                              />
                              <input
                                type="text"
                                className="w-full px-3 py-2 border rounded-md text-sm"
                                placeholder="中文翻譯"
                                value={item.translation || ""}
                                onChange={(e) =>
                                  handleUpdateContentItem(
                                    index,
                                    "translation",
                                    e.target.value,
                                  )
                                }
                              />
                              <div className="flex items-center space-x-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="flex-1"
                                >
                                  <Mic className="h-4 w-4 mr-1" />
                                  錄音
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="text-red-600"
                                  onClick={() => handleDeleteContentItem(index)}
                                >
                                  刪除
                                </Button>
                              </div>
                            </div>
                          ),
                        )
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <p>尚無內容項目</p>
                          <Button
                            size="sm"
                            variant="outline"
                            className="mt-2"
                            onClick={handleAddContentItem}
                          >
                            <Plus className="h-4 w-4 mr-1" />
                            新增項目
                          </Button>
                        </div>
                      )}
                    </div>

                    {/* Add Item Button - only show if there are items */}
                    {editingContent &&
                      editingContent.items &&
                      editingContent.items.length > 0 && (
                        <Button
                          variant="outline"
                          className="w-full"
                          onClick={handleAddContentItem}
                        >
                          <Plus className="h-4 w-4 mr-2" />
                          新增項目
                        </Button>
                      )}
                  </div>
                )}
              </div>

              {/* Panel Footer - Only show for non-reading_assessment types */}
              {selectedContent.type !== "reading_assessment" && (
                <div className="p-4 border-t bg-gray-50">
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={closePanel}
                    >
                      取消
                    </Button>
                    <Button className="flex-1" onClick={handleSaveContent}>
                      <Save className="h-4 w-4 mr-2" />
                      儲存變更
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Student Dialogs */}
      <StudentDialogs
        student={selectedStudent}
        dialogType={dialogType}
        onClose={handleCloseDialog}
        onSave={handleSaveStudent}
        onDelete={handleDeleteStudent}
        onSwitchToEdit={handleSwitchToEdit}
        classrooms={classroom ? [classroom] : []}
      />

      {/* Program Dialog */}
      <ProgramDialog
        program={selectedProgram}
        dialogType={programDialogType}
        classroomId={Number(id)}
        onClose={() => {
          setSelectedProgram(null);
          setProgramDialogType(null);
        }}
        onSave={handleSaveProgram}
        onDelete={handleDeleteProgramConfirm}
      />

      {/* Lesson Dialog */}
      <LessonDialog
        lesson={selectedLesson}
        dialogType={lessonDialogType}
        programId={lessonProgramId}
        currentLessonCount={
          lessonProgramId
            ? programs.find((p) => p.id === lessonProgramId)?.lessons?.length ||
              0
            : 0
        }
        onClose={() => {
          setSelectedLesson(null);
          setLessonDialogType(null);
          setLessonProgramId(undefined);
        }}
        onSave={handleSaveLesson}
        onDelete={handleDeleteLessonConfirm}
      />

      {/* Create Program Dialog - Three Ways */}
      <CreateProgramDialog
        open={showCopyDialog}
        onClose={() => setShowCopyDialog(false)}
        onSuccess={() => {
          fetchPrograms(); // Refresh programs after creating
        }}
        classroomId={Number(id)}
        classroomName={classroom?.name || ""}
      />

      {/* Assignment Dialog */}
      <AssignmentDialog
        open={showAssignmentDialog}
        onClose={() => setShowAssignmentDialog(false)}
        classroomId={Number(id)}
        students={students}
        onSuccess={() => {
          fetchAssignments(); // Refresh assignments after creating
        }}
      />

      {/* Assignment Details Dialog */}
      {showAssignmentDetails && selectedAssignment && (
        <Dialog
          open={showAssignmentDetails}
          onOpenChange={setShowAssignmentDetails}
        >
          <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold">
                作業詳情：{selectedAssignment.title}
              </DialogTitle>
            </DialogHeader>

            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm text-gray-600">內容類型</Label>
                  <p className="font-medium">
                    {(() => {
                      const contentTypeLabels: Record<string, string> = {
                        READING_ASSESSMENT: "朗讀評測",
                        SPEAKING_PRACTICE: "口說練習",
                        SPEAKING_SCENARIO: "情境對話",
                        LISTENING_CLOZE: "聽力填空",
                        SENTENCE_MAKING: "造句練習",
                        SPEAKING_QUIZ: "口說測驗",
                      };
                      return (
                        contentTypeLabels[
                          selectedAssignment.content_type || ""
                        ] ||
                        selectedAssignment.content_type ||
                        "未知類型"
                      );
                    })()}
                  </p>
                </div>
                <div>
                  <Label className="text-sm text-gray-600">指派日期</Label>
                  <p className="font-medium">
                    {selectedAssignment.assigned_at
                      ? new Date(
                          selectedAssignment.assigned_at,
                        ).toLocaleDateString("zh-TW")
                      : "未設定"}
                  </p>
                </div>
                <div>
                  <Label className="text-sm text-gray-600">截止日期</Label>
                  <p className="font-medium">
                    {selectedAssignment.due_date
                      ? new Date(
                          selectedAssignment.due_date,
                        ).toLocaleDateString("zh-TW")
                      : "無期限"}
                  </p>
                </div>
                <div>
                  <Label className="text-sm text-gray-600">指派學生數</Label>
                  <p className="font-medium">
                    {selectedAssignment.student_count || 0} 人
                  </p>
                </div>
              </div>

              {/* Instructions */}
              {selectedAssignment.instructions && (
                <div>
                  <Label className="text-sm text-gray-600">作業說明</Label>
                  <Card className="p-4 mt-2 bg-gray-50">
                    <p className="text-sm">{selectedAssignment.instructions}</p>
                  </Card>
                </div>
              )}

              {/* Progress */}
              <div>
                <Label className="text-sm text-gray-600 mb-3 block">
                  完成進度
                </Label>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">整體完成率</span>
                    <span className="text-2xl font-bold text-blue-600">
                      {selectedAssignment.completion_rate || 0}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all"
                      style={{
                        width: `${selectedAssignment.completion_rate || 0}%`,
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Student Completion Dashboard */}
              <div>
                <Label className="text-sm text-gray-600 mb-3 block">
                  學生列表
                </Label>
                <StudentCompletionDashboard
                  assignmentId={selectedAssignment.id}
                  classroomId={Number(id)}
                  onRefresh={fetchAssignments}
                />
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => {
                    // TODO: Implement view student submissions
                    toast.info("查看學生提交功能尚在開發中");
                  }}
                >
                  <Users className="h-4 w-4 mr-2" />
                  查看學生提交
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleEditAssignment(selectedAssignment)}
                >
                  <Edit className="h-4 w-4 mr-2" />
                  編輯作業
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => handleDeleteAssignment(selectedAssignment)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  刪除作業
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Content Type Dialog */}
      {contentLessonInfo && (
        <ContentTypeDialog
          open={showContentTypeDialog}
          onClose={() => {
            setShowContentTypeDialog(false);
            setContentLessonInfo(null);
          }}
          onSelect={handleContentTypeSelect}
          lessonInfo={contentLessonInfo}
        />
      )}

      {/* Reading Assessment Editor */}
      {showReadingEditor && editorLessonId && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="relative w-full max-w-7xl max-h-[90vh] bg-white rounded-lg p-6 flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">朗讀評測設定</h2>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  setShowReadingEditor(false);
                  setEditorLessonId(null);
                  setEditorContentId(null);
                }}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <div className="flex-1 overflow-hidden">
              <ReadingAssessmentPanel
                content={undefined}
                editingContent={{ id: editorContentId || undefined }}
                lessonId={editorLessonId}
                onUpdateContent={(updatedContent) => {
                  // Handle content update if needed
                  console.log("Content updated:", updatedContent);
                }}
                onSave={async () => {
                  // ReadingAssessmentPanel handles save internally
                  // Just close the editor on successful save
                  setShowReadingEditor(false);
                  setEditorLessonId(null);
                  setEditorContentId(null);
                  await refreshPrograms();
                  toast.success("內容已成功儲存");
                }}
                onCancel={() => {
                  setShowReadingEditor(false);
                  setEditorLessonId(null);
                  setEditorContentId(null);
                }}
                isCreating={!editorContentId}
              />
            </div>
          </div>
        </div>
      )}
    </TeacherLayout>
  );
}
