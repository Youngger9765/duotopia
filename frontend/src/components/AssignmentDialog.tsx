import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { format } from "date-fns";
import { zhTW } from "date-fns/locale";
import {
  Users,
  ChevronRight,
  ChevronDown,
  BookOpen,
  FileText,
  CheckCircle2,
  Circle,
  Package,
  Layers,
  ChevronLeft,
  ArrowRight,
  Check,
  Calendar as CalendarIconAlt,
  Clock,
  MessageSquare,
  Loader2,
  Gauge,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useTranslation } from "react-i18next";

interface Student {
  id: number;
  name: string;
  email?: string; // Make email optional to match global Student type
}

interface Content {
  id: number;
  title: string;
  type: string;
  lesson_id: number;
  items_count?: number;
  level?: string;
}

interface Lesson {
  id: number;
  name: string;
  description?: string;
  order_index: number;
  contents?: Content[];
}

interface Program {
  id: number;
  name: string;
  description?: string;
  level?: string;
  lessons?: Lesson[];
}

interface AssignmentDialogProps {
  open: boolean;
  onClose: () => void;
  classroomId: number;
  students: Student[];
  onSuccess?: () => void;
}

// Content type labels - using i18n
const useContentTypeLabel = (type: string, t: (key: string) => string) => {
  return t(`dialogs.assignmentDialog.contentTypes.${type}`) || type;
};

interface QuotaInfo {
  quota_total: number;
  quota_used: number;
  quota_remaining: number;
  plan_name: string;
}

export function AssignmentDialog({
  open,
  onClose,
  classroomId,
  students,
  onSuccess,
}: AssignmentDialogProps) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [loadingPrograms, setLoadingPrograms] = useState(false);
  const [loadingLessons, setLoadingLessons] = useState<Record<number, boolean>>(
    {},
  );
  const [currentStep, setCurrentStep] = useState(1);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [expandedPrograms, setExpandedPrograms] = useState<Set<number>>(
    new Set(),
  );
  const [expandedLessons, setExpandedLessons] = useState<Set<number>>(
    new Set(),
  );
  const [selectedContents, setSelectedContents] = useState<Set<number>>(
    new Set(),
  );
  const [quotaInfo, setQuotaInfo] = useState<QuotaInfo | null>(null);

  const [formData, setFormData] = useState({
    title: "",
    instructions: "",
    student_ids: [] as number[],
    assign_to_all: true,
    due_date: undefined as Date | undefined,
  });

  useEffect(() => {
    if (open) {
      loadPrograms();
      loadQuotaInfo();
      // Reset form when dialog opens
      setSelectedContents(new Set());
      setFormData({
        title: "",
        instructions: "",
        student_ids: students.map((s) => s.id), // 預設全選所有學生
        assign_to_all: true,
        due_date: undefined,
      });
      setCurrentStep(1);
    }
  }, [open, classroomId, students]);

  const loadQuotaInfo = async () => {
    try {
      const response = await apiClient.get<{
        subscription_period: {
          quota_total: number;
          quota_used: number;
          plan_name: string;
        };
      }>("/api/teachers/subscription");

      if (response.subscription_period) {
        setQuotaInfo({
          quota_total: response.subscription_period.quota_total,
          quota_used: response.subscription_period.quota_used,
          quota_remaining:
            response.subscription_period.quota_total -
            response.subscription_period.quota_used,
          plan_name: response.subscription_period.plan_name,
        });
      }
    } catch (error) {
      console.error("Failed to load quota info:", error);
    }
  };

  const loadPrograms = async () => {
    try {
      setLoadingPrograms(true);
      // Only load program list, not lessons or contents
      // Filter by classroom_id to show only public templates and classroom-specific programs
      const response = await apiClient.get<Program[]>(
        `/api/teachers/programs?classroom_id=${classroomId}`
      );
      setPrograms(response);
    } catch (error) {
      console.error("Failed to load programs:", error);
      toast.error(t("dialogs.assignmentDialog.errors.loadProgramsFailed"));
      setPrograms([]);
    } finally {
      setLoadingPrograms(false);
    }
  };

  const loadProgramLessons = async (programId: number) => {
    // Check if lessons already loaded
    const program = programs.find((p) => p.id === programId);
    if (program?.lessons && program.lessons.length > 0) {
      return; // Already loaded
    }

    try {
      setLoadingLessons((prev) => ({ ...prev, [programId]: true }));
      const detail = await apiClient.get<Program>(
        `/api/teachers/programs/${programId}`,
      );

      // Update the program with lessons (but without contents)
      setPrograms((prev) =>
        prev.map((p) =>
          p.id === programId ? { ...p, lessons: detail.lessons || [] } : p,
        ),
      );
    } catch (error) {
      console.error(`Failed to load lessons for program ${programId}:`, error);
      toast.error(t("dialogs.assignmentDialog.errors.loadLessonsFailed"));
    } finally {
      setLoadingLessons((prev) => ({ ...prev, [programId]: false }));
    }
  };

  const loadLessonContents = async (lessonId: number) => {
    // Find the lesson and check if contents already loaded
    let foundLesson: Lesson | undefined;
    programs.forEach((program) => {
      const lesson = program.lessons?.find((l) => l.id === lessonId);
      if (lesson) {
        foundLesson = lesson;
      }
    });

    if (foundLesson?.contents && foundLesson.contents.length > 0) {
      return; // Already loaded
    }

    try {
      setLoadingLessons((prev) => ({ ...prev, [lessonId]: true }));
      const contents = await apiClient.get<Content[]>(
        `/api/teachers/lessons/${lessonId}/contents`,
      );

      // Update the lesson with contents
      setPrograms((prev) =>
        prev.map((program) => ({
          ...program,
          lessons: program.lessons?.map((lesson) =>
            lesson.id === lessonId ? { ...lesson, contents } : lesson,
          ),
        })),
      );
    } catch (error) {
      console.error(`Failed to load contents for lesson ${lessonId}:`, error);
      toast.error(t("dialogs.assignmentDialog.errors.loadContentsFailed"));
    } finally {
      setLoadingLessons((prev) => ({ ...prev, [lessonId]: false }));
    }
  };

  const toggleProgram = async (programId: number) => {
    const isExpanding = !expandedPrograms.has(programId);

    setExpandedPrograms((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(programId)) {
        newSet.delete(programId);
      } else {
        newSet.add(programId);
      }
      return newSet;
    });

    // Load lessons when expanding
    if (isExpanding) {
      await loadProgramLessons(programId);
    }
  };

  const toggleLesson = async (lessonId: number) => {
    const isExpanding = !expandedLessons.has(lessonId);

    setExpandedLessons((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(lessonId)) {
        newSet.delete(lessonId);
      } else {
        newSet.add(lessonId);
      }
      return newSet;
    });

    // Load contents when expanding
    if (isExpanding) {
      await loadLessonContents(lessonId);
    }
  };

  const toggleContent = (contentId: number) => {
    setSelectedContents((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(contentId)) {
        newSet.delete(contentId);
      } else {
        newSet.add(contentId);
      }
      return newSet;
    });
  };

  const toggleAllInLesson = (lesson: Lesson) => {
    if (!lesson.contents) return;

    const lessonContentIds = lesson.contents.map((c) => c.id);
    const allSelected = lessonContentIds.every((id) =>
      selectedContents.has(id),
    );

    setSelectedContents((prev) => {
      const newSet = new Set(prev);
      if (allSelected) {
        lessonContentIds.forEach((id) => newSet.delete(id));
      } else {
        lessonContentIds.forEach((id) => newSet.add(id));
      }
      return newSet;
    });
  };

  const toggleStudent = (studentId: number) => {
    setFormData((prev) => {
      const newIds = prev.student_ids.includes(studentId)
        ? prev.student_ids.filter((id) => id !== studentId)
        : [...prev.student_ids, studentId];

      return {
        ...prev,
        student_ids: newIds,
        assign_to_all: newIds.length === students.length,
      };
    });
  };

  const toggleAllStudents = () => {
    setFormData((prev) => ({
      ...prev,
      assign_to_all: !prev.assign_to_all,
      student_ids: !prev.assign_to_all ? students.map((s) => s.id) : [],
    }));
  };

  const handleSubmit = async () => {
    // Validation
    if (selectedContents.size === 0) {
      toast.error(t("dialogs.assignmentDialog.errors.noContentSelected"));
      return;
    }
    if (!formData.title.trim()) {
      toast.error(t("dialogs.assignmentDialog.errors.titleRequired"));
      return;
    }
    if (formData.student_ids.length === 0) {
      toast.error(t("dialogs.assignmentDialog.errors.noStudentSelected"));
      return;
    }

    // 配額檢查
    if (quotaInfo && quotaInfo.quota_remaining <= 0) {
      toast.error(t("dialogs.assignmentDialog.errors.quotaExceeded"), {
        description: t("dialogs.assignmentDialog.errors.quotaExceededDesc"),
        action: {
          label: t("dialogs.assignmentDialog.actions.viewPlans"),
          onClick: () => {
            window.location.href = "/teacher/subscription";
          },
        },
      });
      return;
    }

    setLoading(true);
    try {
      // Create one assignment with multiple contents (新架構)
      const payload = {
        title: formData.title,
        description: formData.instructions || undefined, // 欄位名稱改為 description
        classroom_id: classroomId,
        content_ids: Array.from(selectedContents), // 多個內容 ID
        student_ids: formData.assign_to_all ? [] : formData.student_ids,
        due_date: formData.due_date
          ? formData.due_date.toISOString()
          : undefined,
      };

      const result = await apiClient.post<{ student_count: number }>(
        "/api/teachers/assignments/create",
        payload,
      );

      toast.success(
        t("dialogs.assignmentDialog.success.created", {
          count: result.student_count || 0,
        }),
      );
      onSuccess?.();
      handleClose();
    } catch (error: unknown) {
      console.error("Failed to create assignment:", error);

      // 處理 HTTP 402 配額不足錯誤
      if (
        error &&
        typeof error === "object" &&
        "response" in error &&
        error.response &&
        typeof error.response === "object" &&
        "status" in error.response &&
        error.response.status === 402
      ) {
        const errorData = "data" in error.response ? error.response.data : null;
        const detailMessage =
          errorData &&
          typeof errorData === "object" &&
          "detail" in errorData &&
          errorData.detail &&
          typeof errorData.detail === "object" &&
          "message" in errorData.detail
            ? String(errorData.detail.message)
            : "請升級方案或等待下個計費週期";

        toast.error(t("dialogs.assignmentDialog.errors.quotaExceeded"), {
          description: detailMessage,
          action: {
            label: t("dialogs.assignmentDialog.actions.viewPlans"),
            onClick: () => {
              window.location.href = "/teacher/subscription";
            },
          },
        });
      } else {
        toast.error(t("dialogs.assignmentDialog.errors.createFailed"));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      title: "",
      instructions: "",
      student_ids: [],
      assign_to_all: true,
      due_date: undefined,
    });
    setSelectedContents(new Set());
    setExpandedPrograms(new Set());
    setExpandedLessons(new Set());
    setCurrentStep(1);
    onClose();
  };

  // Get selected content details for summary
  const getSelectedContentsSummary = () => {
    const summary: {
      program: string;
      lesson: string;
      content: string;
      type: string;
    }[] = [];

    programs.forEach((program) => {
      program.lessons?.forEach((lesson) => {
        lesson.contents?.forEach((content) => {
          if (selectedContents.has(content.id)) {
            summary.push({
              program: program.name,
              lesson: lesson.name,
              content: content.title,
              type: content.type,
            });
          }
        });
      });
    });

    return summary;
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return selectedContents.size > 0;
      case 2:
        return formData.student_ids.length > 0;
      case 3:
        return formData.title.trim().length > 0;
      default:
        return false;
    }
  };

  const steps = [
    {
      number: 1,
      title: t("dialogs.assignmentDialog.steps.selectContent"),
      icon: BookOpen,
    },
    {
      number: 2,
      title: t("dialogs.assignmentDialog.steps.selectStudents"),
      icon: Users,
    },
    {
      number: 3,
      title: t("dialogs.assignmentDialog.steps.details"),
      icon: FileText,
    },
  ];

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-5xl h-[92vh] flex flex-col p-0">
        {/* Compact Header with Clear Steps */}
        <div className="px-6 py-3 border-b bg-gray-50">
          <div className="flex items-center">
            <div className="flex-1">
              <DialogTitle className="text-lg font-semibold">
                {t("dialogs.assignmentDialog.title")}
              </DialogTitle>
              {/* Quota display */}
              {quotaInfo && (
                <div className="mt-1 flex items-center gap-2 text-xs">
                  <Gauge
                    className={cn(
                      "h-3 w-3",
                      quotaInfo.quota_remaining <= 0
                        ? "text-red-500"
                        : "text-gray-500",
                    )}
                  />
                  <span className="text-gray-600">
                    {t("dialogs.assignmentDialog.quota.remainingColon")}
                    <span
                      className={cn(
                        "font-semibold ml-1",
                        quotaInfo.quota_remaining > 300
                          ? "text-green-600"
                          : quotaInfo.quota_remaining > 100
                            ? "text-orange-600"
                            : quotaInfo.quota_remaining > 0
                              ? "text-red-600"
                              : "text-red-700",
                      )}
                    >
                      {quotaInfo.quota_remaining}
                    </span>
                    <span className="text-gray-500">
                      {" "}
                      / {quotaInfo.quota_total}{" "}
                      {t("dialogs.assignmentDialog.quota.seconds")}
                    </span>
                  </span>
                  {quotaInfo.quota_remaining <= 0 ? (
                    <Badge
                      variant="destructive"
                      className="text-xs py-0 px-1.5 animate-pulse"
                    >
                      {t("dialogs.assignmentDialog.quota.exhausted")}
                    </Badge>
                  ) : (
                    quotaInfo.quota_remaining <= 100 && (
                      <Badge
                        variant="destructive"
                        className="text-xs py-0 px-1.5"
                      >
                        {t("dialogs.assignmentDialog.quota.low")}
                      </Badge>
                    )
                  )}
                </div>
              )}
            </div>

            {/* Centered Step Indicator with Icons */}
            <div className="flex-1 flex items-center justify-center">
              <div className="flex items-center gap-4">
                {steps.map((s, index) => {
                  const Icon = s.icon;
                  const isActive = s.number === currentStep;
                  const isCompleted = s.number < currentStep;

                  return (
                    <React.Fragment key={s.number}>
                      <div className="flex items-center gap-2">
                        <div
                          className={cn(
                            "w-7 h-7 rounded-full flex items-center justify-center font-medium transition-all",
                            isActive && "bg-blue-600 text-white shadow-sm",
                            isCompleted && "bg-green-500 text-white",
                            !isActive &&
                              !isCompleted &&
                              "bg-gray-200 text-gray-500",
                          )}
                        >
                          {isCompleted ? (
                            <CheckCircle2 className="h-4 w-4" />
                          ) : (
                            <span className="text-sm">{s.number}</span>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <Icon
                            className={cn(
                              "h-4 w-4",
                              isActive && "text-blue-600",
                              isCompleted && "text-green-600",
                              !isActive && !isCompleted && "text-gray-400",
                            )}
                          />
                          <span
                            className={cn(
                              "text-sm",
                              isActive && "text-gray-900 font-semibold",
                              isCompleted && "text-green-700 font-medium",
                              !isActive && !isCompleted && "text-gray-500",
                            )}
                          >
                            {s.title}
                          </span>
                        </div>
                      </div>
                      {index < steps.length - 1 && (
                        <ChevronRight className="h-4 w-4 text-gray-300" />
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Content Area - Maximized Height */}
        <div className="flex-1 overflow-hidden px-6 py-3">
          {/* Step 1: Select Contents */}
          {currentStep === 1 && (
            <div className="h-full flex flex-col">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  {t("dialogs.assignmentDialog.selectContent.description")}
                </p>
                {selectedContents.size > 0 && (
                  <Badge
                    variant="secondary"
                    className="bg-blue-50 text-blue-700"
                  >
                    {t("dialogs.assignmentDialog.selectContent.selected", {
                      count: selectedContents.size,
                    })}
                  </Badge>
                )}
              </div>

              <ScrollArea className="flex-1 border rounded-lg p-3">
                {loadingPrograms ? (
                  <div className="flex flex-col items-center justify-center h-96">
                    <div className="relative">
                      {/* Outer ring */}
                      <div className="absolute inset-0 animate-ping">
                        <div className="h-16 w-16 rounded-full border-4 border-blue-200 opacity-75"></div>
                      </div>
                      {/* Inner spinning circle */}
                      <Loader2 className="h-16 w-16 animate-spin text-blue-600 mx-auto relative" />
                    </div>
                    <p className="mt-6 text-lg font-medium text-gray-700">
                      {t("dialogs.assignmentDialog.selectContent.loading")}
                    </p>
                    <p className="mt-2 text-sm text-gray-500">
                      {t("dialogs.assignmentDialog.selectContent.loadingDesc")}
                    </p>
                  </div>
                ) : programs.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-96">
                    <Package className="h-16 w-16 text-gray-300 mb-4" />
                    <p className="text-gray-500">
                      {t("dialogs.assignmentDialog.selectContent.empty")}
                    </p>
                    <p className="text-sm text-gray-400 mt-2">
                      {t("dialogs.assignmentDialog.selectContent.emptyDesc")}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {programs.map((program) => (
                      <Card key={program.id} className="overflow-hidden">
                        <button
                          onClick={() => toggleProgram(program.id)}
                          className="w-full p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            {loadingLessons[program.id] ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : expandedPrograms.has(program.id) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                            <Package className="h-4 w-4 text-blue-600" />
                            <span className="font-medium">{program.name}</span>
                            {program.level && (
                              <Badge variant="outline" className="ml-2">
                                {program.level}
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-500">
                              {t(
                                "dialogs.assignmentDialog.selectContent.units",
                                { count: program.lessons?.length || 0 },
                              )}
                            </span>
                            {loadingLessons[program.id] && (
                              <span className="text-xs text-blue-600">
                                {t(
                                  "dialogs.assignmentDialog.selectContent.loadingLabel",
                                )}
                              </span>
                            )}
                          </div>
                        </button>

                        {expandedPrograms.has(program.id) &&
                          program.lessons && (
                            <div className="border-t bg-gray-50">
                              {program.lessons.map((lesson) => (
                                <div key={lesson.id} className="ml-6">
                                  <button
                                    onClick={() => toggleLesson(lesson.id)}
                                    className="w-full p-2 flex items-center justify-between hover:bg-gray-100 transition-colors"
                                  >
                                    <div className="flex items-center gap-2">
                                      {loadingLessons[lesson.id] ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                      ) : expandedLessons.has(lesson.id) ? (
                                        <ChevronDown className="h-4 w-4" />
                                      ) : (
                                        <ChevronRight className="h-4 w-4" />
                                      )}
                                      <Layers className="h-4 w-4 text-green-600" />
                                      <span className="text-sm">
                                        {lesson.name}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs text-gray-500">
                                        {t(
                                          "dialogs.assignmentDialog.selectContent.contents",
                                          {
                                            count: lesson.contents?.length || 0,
                                          },
                                        )}
                                      </span>
                                      {loadingLessons[lesson.id] && (
                                        <span className="text-xs text-blue-600">
                                          {t(
                                            "dialogs.assignmentDialog.selectContent.loadingLabel",
                                          )}
                                        </span>
                                      )}
                                      {lesson.contents &&
                                        lesson.contents.length > 0 &&
                                        !loadingLessons[lesson.id] && (
                                          <span
                                            className="h-6 px-2 text-xs cursor-pointer rounded bg-gray-100 hover:bg-gray-200 transition-colors inline-flex items-center"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              toggleAllInLesson(lesson);
                                            }}
                                          >
                                            {lesson.contents.every((c) =>
                                              selectedContents.has(c.id),
                                            )
                                              ? t(
                                                  "dialogs.assignmentDialog.selectContent.deselectAll",
                                                )
                                              : t(
                                                  "dialogs.assignmentDialog.selectContent.selectAll",
                                                )}
                                          </span>
                                        )}
                                    </div>
                                  </button>

                                  {expandedLessons.has(lesson.id) &&
                                    lesson.contents && (
                                      <div className="ml-6 space-y-1 pb-2 bg-white">
                                        {lesson.contents.map((content) => (
                                          <button
                                            key={content.id}
                                            onClick={() =>
                                              toggleContent(content.id)
                                            }
                                            className={cn(
                                              "w-full p-2 flex items-center gap-2 hover:bg-gray-50 rounded transition-colors text-left",
                                              selectedContents.has(
                                                content.id,
                                              ) &&
                                                "bg-blue-50 hover:bg-blue-100",
                                            )}
                                          >
                                            {selectedContents.has(
                                              content.id,
                                            ) ? (
                                              <CheckCircle2 className="h-4 w-4 text-blue-600 flex-shrink-0" />
                                            ) : (
                                              <Circle className="h-4 w-4 text-gray-400 flex-shrink-0" />
                                            )}
                                            <div className="flex-1">
                                              <div className="text-sm font-medium">
                                                {content.title}
                                              </div>
                                              <div className="flex items-center gap-2 text-xs text-gray-500">
                                                <Badge
                                                  variant="outline"
                                                  className="px-1 py-0"
                                                >
                                                  {useContentTypeLabel(
                                                    content.type,
                                                    t,
                                                  )}
                                                </Badge>
                                                {content.items_count && (
                                                  <span>
                                                    {content.items_count}{" "}
                                                    {t(
                                                      "dialogs.assignmentDialog.selectContent.items",
                                                    )}
                                                  </span>
                                                )}
                                              </div>
                                            </div>
                                          </button>
                                        ))}
                                      </div>
                                    )}
                                </div>
                              ))}
                            </div>
                          )}
                      </Card>
                    ))}
                  </div>
                )}
              </ScrollArea>

              {/* Compact Selected Contents Summary */}
              {selectedContents.size > 0 && (
                <div className="mt-2 p-2 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex flex-wrap gap-1">
                    {getSelectedContentsSummary()
                      .slice(0, 8)
                      .map((item, idx) => (
                        <Badge
                          key={idx}
                          variant="secondary"
                          className="bg-white text-xs py-0 h-5"
                        >
                          {item.content}
                        </Badge>
                      ))}
                    {selectedContents.size > 8 && (
                      <Badge
                        variant="secondary"
                        className="bg-white text-xs py-0 h-5"
                      >
                        +{selectedContents.size - 8}
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Select Students */}
          {currentStep === 2 && (
            <div className="h-full flex flex-col">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  {t("dialogs.assignmentDialog.selectStudents.description")}
                </p>
                <Badge variant="secondary" className="bg-blue-50 text-blue-700">
                  {t("dialogs.assignmentDialog.selectStudents.selected", {
                    selected: formData.student_ids.length,
                    total: students.length,
                  })}
                </Badge>
              </div>

              {/* Quick Select All */}
              <Card className="p-2 mb-2 bg-blue-50 border-blue-200">
                <div
                  onClick={toggleAllStudents}
                  className="flex items-center gap-3 w-full cursor-pointer"
                >
                  <Checkbox
                    checked={formData.assign_to_all}
                    className="data-[state=checked]:bg-blue-600 h-5 w-5"
                  />
                  <div className="flex-1 text-left">
                    <p className="text-sm font-semibold text-blue-900">
                      {t("dialogs.assignmentDialog.selectStudents.assignAll")}
                    </p>
                    <p className="text-xs text-blue-700">
                      {t(
                        "dialogs.assignmentDialog.selectStudents.totalStudents",
                        { count: students.length },
                      )}
                    </p>
                  </div>
                  {formData.assign_to_all && (
                    <Badge className="bg-blue-600 text-white">
                      {t("dialogs.assignmentDialog.selectStudents.allSelected")}
                    </Badge>
                  )}
                </div>
              </Card>

              {/* Student Grid - Maximum use of space */}
              <div className="flex-1 border rounded-lg bg-gray-50 p-2 overflow-hidden">
                <ScrollArea className="h-full">
                  <div className="grid grid-cols-3 gap-1.5 p-1">
                    {students.map((student) => (
                      <div
                        key={student.id}
                        onClick={() => toggleStudent(student.id)}
                        className={cn(
                          "p-2 rounded-md border transition-all text-left relative cursor-pointer",
                          formData.student_ids.includes(student.id)
                            ? "bg-blue-50 border-blue-300 shadow-sm"
                            : "bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm",
                        )}
                      >
                        <div className="flex items-start gap-2">
                          <Checkbox
                            checked={formData.student_ids.includes(student.id)}
                            className="data-[state=checked]:bg-blue-600 mt-0.5 h-4 w-4 pointer-events-none"
                          />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-xs truncate">
                              {student.name}
                            </p>
                            <p className="text-[10px] text-gray-500 truncate">
                              {student.email}
                            </p>
                          </div>
                        </div>
                        {formData.student_ids.includes(student.id) && (
                          <div className="absolute top-1 right-1">
                            <CheckCircle2 className="h-3 w-3 text-blue-600" />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>

              {/* Action Buttons for quick selection */}
              <div className="flex gap-2 mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setFormData((prev) => ({
                      ...prev,
                      student_ids: students.map((s) => s.id),
                      assign_to_all: true,
                    }))
                  }
                  className="flex-1"
                >
                  <CheckCircle2 className="h-4 w-4 mr-1" />
                  {t("dialogs.assignmentDialog.selectStudents.selectAllBtn")}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setFormData((prev) => ({
                      ...prev,
                      student_ids: [],
                      assign_to_all: false,
                    }))
                  }
                  className="flex-1"
                >
                  <Circle className="h-4 w-4 mr-1" />
                  {t("dialogs.assignmentDialog.selectStudents.deselectAllBtn")}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const currentIds = formData.student_ids;
                    const allIds = students.map((s) => s.id);
                    const newIds = allIds.filter(
                      (id) => !currentIds.includes(id),
                    );
                    setFormData((prev) => ({
                      ...prev,
                      student_ids: newIds,
                      assign_to_all: false,
                    }));
                  }}
                  className="flex-1"
                >
                  <ArrowRight className="h-4 w-4 mr-1" />
                  {t("dialogs.assignmentDialog.selectStudents.invertSelection")}
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Assignment Details */}
          {currentStep === 3 && (
            <div className="h-full flex flex-col">
              <div className="mb-2">
                <p className="text-sm text-gray-600">
                  {t("dialogs.assignmentDialog.details.description")}
                </p>
              </div>

              <ScrollArea className="flex-1">
                <div className="space-y-4 pr-4">
                  <div className="space-y-1.5">
                    <Label
                      htmlFor="title"
                      className="flex items-center gap-1 text-sm"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      {t("dialogs.assignmentDialog.details.title")}{" "}
                      {t("dialogs.assignmentDialog.details.titleRequired")}
                    </Label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          title: e.target.value,
                        }))
                      }
                      placeholder={t(
                        "dialogs.assignmentDialog.details.titlePlaceholder",
                      )}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label
                      htmlFor="instructions"
                      className="flex items-center gap-1 text-sm"
                    >
                      <MessageSquare className="h-3.5 w-3.5" />
                      {t("dialogs.assignmentDialog.details.instructions")}
                    </Label>
                    <Textarea
                      id="instructions"
                      value={formData.instructions}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          instructions: e.target.value,
                        }))
                      }
                      placeholder={t(
                        "dialogs.assignmentDialog.details.instructionsPlaceholder",
                      )}
                      rows={2}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="flex items-center gap-1 text-sm">
                        <CalendarIconAlt className="h-3.5 w-3.5" />
                        {t("dialogs.assignmentDialog.details.startDate")}
                      </Label>
                      <Input
                        type="date"
                        defaultValue={new Date().toISOString().split("T")[0]}
                        className="text-sm"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="flex items-center gap-1 text-sm">
                        <Clock className="h-3.5 w-3.5" />
                        {t("dialogs.assignmentDialog.details.dueDate")}
                      </Label>
                      <Input
                        type="date"
                        value={
                          formData.due_date
                            ? formData.due_date.toISOString().split("T")[0]
                            : ""
                        }
                        onChange={(e) => {
                          const dateValue = e.target.value
                            ? new Date(e.target.value)
                            : undefined;
                          setFormData((prev) => ({
                            ...prev,
                            due_date: dateValue,
                          }));
                        }}
                        className="text-sm"
                      />
                    </div>
                  </div>

                  {/* Assignment Summary */}
                  <Card className="p-3 bg-blue-50 border-blue-200">
                    <h4 className="text-xs font-medium mb-2 text-blue-900">
                      {t("dialogs.assignmentDialog.details.summary")}
                    </h4>
                    <div className="space-y-1 text-xs">
                      <div className="flex items-center gap-2">
                        <BookOpen className="h-3 w-3 text-blue-600" />
                        <span className="text-gray-700">
                          {t("dialogs.assignmentDialog.details.contentCount")}
                        </span>
                        <span className="font-medium text-blue-900">
                          {t(
                            "dialogs.assignmentDialog.details.contentCountValue",
                            { count: selectedContents.size },
                          )}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Users className="h-3 w-3 text-blue-600" />
                        <span className="text-gray-700">
                          {t("dialogs.assignmentDialog.details.assignTo")}
                        </span>
                        <span className="font-medium text-blue-900">
                          {formData.assign_to_all
                            ? t("dialogs.assignmentDialog.details.assignToAll")
                            : t(
                                "dialogs.assignmentDialog.details.assignToSelected",
                                { count: formData.student_ids.length },
                              )}
                        </span>
                      </div>
                      {formData.due_date && (
                        <div className="flex items-center gap-2">
                          <Clock className="h-3 w-3 text-blue-600" />
                          <span className="text-gray-700">
                            {t("dialogs.assignmentDialog.details.dueDateLabel")}
                          </span>
                          <span className="font-medium text-blue-900">
                            {format(formData.due_date, "yyyy年MM月dd日", {
                              locale: zhTW,
                            })}
                          </span>
                        </div>
                      )}
                    </div>
                  </Card>
                </div>
              </ScrollArea>
            </div>
          )}
        </div>

        {/* Footer with Navigation */}
        <DialogFooter className="px-6 py-3 border-t">
          <div className="flex items-center justify-between w-full">
            <Button
              variant="outline"
              onClick={
                currentStep === 1
                  ? handleClose
                  : () => setCurrentStep(currentStep - 1)
              }
              disabled={loading}
            >
              {currentStep === 1 ? (
                <>{t("dialogs.assignmentDialog.buttons.cancel")}</>
              ) : (
                <>
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  {t("dialogs.assignmentDialog.buttons.previous")}
                </>
              )}
            </Button>

            <div className="flex items-center gap-2">
              {currentStep < 3 ? (
                <Button
                  onClick={() => setCurrentStep(currentStep + 1)}
                  disabled={!canProceed()}
                >
                  {t("dialogs.assignmentDialog.buttons.next")}
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={
                    loading ||
                    !canProceed() ||
                    (quotaInfo !== null && quotaInfo.quota_remaining <= 0)
                  }
                  className={cn(
                    "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600",
                    quotaInfo !== null &&
                      quotaInfo.quota_remaining <= 0 &&
                      "opacity-50 cursor-not-allowed",
                  )}
                  title={
                    quotaInfo !== null && quotaInfo.quota_remaining <= 0
                      ? t("dialogs.assignmentDialog.quota.cannotCreate")
                      : ""
                  }
                >
                  {loading ? (
                    <>{t("dialogs.assignmentDialog.buttons.creating")}</>
                  ) : quotaInfo !== null && quotaInfo.quota_remaining <= 0 ? (
                    <>
                      <Gauge className="h-4 w-4 mr-1" />
                      {t("dialogs.assignmentDialog.buttons.quotaDepleted")}
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-1" />
                      {t("dialogs.assignmentDialog.buttons.create")}
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
