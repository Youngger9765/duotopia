import { useState, useEffect } from "react";
import TeacherLayout from "@/components/TeacherLayout";
import { RecursiveTreeAccordion } from "@/components/shared/RecursiveTreeAccordion";
import { programTreeConfig } from "@/components/shared/programTreeConfig";
import { ProgramDialog } from "@/components/ProgramDialog";
import { LessonDialog } from "@/components/LessonDialog";
import ContentTypeDialog from "@/components/ContentTypeDialog";
import ReadingAssessmentPanel from "@/components/ReadingAssessmentPanel";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { Program, Lesson, Content } from "@/types";

export default function TeacherTemplateProgramsNew() {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [isReordering, setIsReordering] = useState(false);

  // Program dialog states
  const [programDialogType, setProgramDialogType] = useState<
    "create" | "edit" | "delete" | null
  >(null);
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);

  // Lesson dialog states
  const [lessonDialogType, setLessonDialogType] = useState<
    "create" | "edit" | "delete" | null
  >(null);
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null);
  const [lessonProgramId, setLessonProgramId] = useState<number | undefined>(
    undefined,
  );

  // Content dialog states
  const [showContentTypeDialog, setShowContentTypeDialog] = useState(false);
  const [contentLessonInfo, setContentLessonInfo] = useState<{
    programName: string;
    lessonName: string;
    lessonId: number;
  } | null>(null);

  // Reading assessment modal
  const [showReadingEditor, setShowReadingEditor] = useState(false);
  const [editorLessonId, setEditorLessonId] = useState<number | null>(null);
  const [editorContentId, setEditorContentId] = useState<number | null>(null);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);

  useEffect(() => {
    fetchTemplatePrograms();
  }, []);

  const fetchTemplatePrograms = async () => {
    try {
      setLoading(true);
      // 使用 teachers API，已包含完整的 lessons/contents 和排序（teachers.py Line 300, 304）
      const response = await apiClient.getTeacherPrograms(true);
      setPrograms(response as Program[]);
    } catch (err) {
      console.error("Failed to fetch template programs:", err);
      toast.error("載入公版課程失敗");
    } finally {
      setLoading(false);
    }
  };

  // Program handlers
  const handleCreateProgram = () => {
    setSelectedProgram(null);
    setProgramDialogType("create");
  };

  const handleEditProgram = (programId: number) => {
    const program = programs.find((p) => p.id === programId);
    if (program) {
      setSelectedProgram(program);
      setProgramDialogType("edit");
    }
  };

  const handleDeleteProgram = (programId: number) => {
    const program = programs.find((p) => p.id === programId);
    if (program) {
      setSelectedProgram(program);
      setProgramDialogType("delete");
    }
  };

  const handleSaveProgram = (program: Program) => {
    setPrograms(programs.map((p) => (p.id === program.id ? program : p)));
    fetchTemplatePrograms();
  };

  const handleDeleteProgramConfirm = (programId: number) => {
    setPrograms(programs.filter((p) => p.id !== programId));
    fetchTemplatePrograms();
  };

  // Lesson handlers
  const handleCreateLesson = (programId: number) => {
    setSelectedLesson(null);
    setLessonProgramId(programId);
    setLessonDialogType("create");
  };

  const handleEditLesson = (programId: number, lessonId: number) => {
    const program = programs.find((p) => p.id === programId);
    const lesson = program?.lessons?.find((l) => l.id === lessonId);
    if (lesson && program) {
      setSelectedLesson(lesson);
      setLessonProgramId(program.id);
      setLessonDialogType("edit");
    }
  };

  const handleDeleteLesson = (programId: number, lessonId: number) => {
    const program = programs.find((p) => p.id === programId);
    const lesson = program?.lessons?.find((l) => l.id === lessonId);
    if (lesson && program) {
      setSelectedLesson(lesson);
      setLessonProgramId(program.id);
      setLessonDialogType("delete");
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleSaveLesson = (lesson: any) => {
    if (lessonDialogType === "create" && lessonProgramId) {
      setPrograms((prevPrograms) =>
        prevPrograms.map((program) => {
          if (program.id === lessonProgramId) {
            return {
              ...program,
              lessons: [...(program.lessons || []), lesson],
            };
          }
          return program;
        }),
      );
      toast.success(`單元「${lesson.name}」已新增`);
    } else if (lessonDialogType === "edit") {
      setPrograms((prevPrograms) =>
        prevPrograms.map((program) => ({
          ...program,
          lessons:
            program.lessons?.map((l) => (l.id === lesson.id ? lesson : l)) ||
            [],
        })),
      );
      toast.success(`單元「${lesson.name}」已更新`);
    }
  };

  const handleDeleteLessonConfirm = async (lessonId: number) => {
    try {
      await apiClient.deleteLesson(lessonId);
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
    } catch (err) {
      console.error("Failed to delete lesson:", err);
      toast.error("刪除單元失敗");
    }
  };

  // Content handlers
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

  const handleContentClick = (
    content: Content & {
      lessonName?: string;
      programName?: string;
      lesson_id?: number;
    },
  ) => {
    if (content.type === "reading_assessment") {
      setSelectedContent(content);
      setEditorLessonId(content.lesson_id || null);
      setEditorContentId(content.id);
      setShowReadingEditor(true);
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
      await apiClient.deleteContent(contentId);
      const updatedPrograms = programs.map((program) => ({
        ...program,
        lessons: program.lessons?.map((lesson) => {
          if (lesson.id === lessonId) {
            return {
              ...lesson,
              contents: lesson.contents?.filter((c) => c.id !== contentId),
            };
          }
          return lesson;
        }),
      }));
      setPrograms(updatedPrograms);
      toast.success("內容已刪除");
    } catch (err) {
      console.error("Failed to delete content:", err);
      toast.error("刪除內容失敗");
    }
  };

  // Reorder handlers
  const handleReorderPrograms = async (fromIndex: number, toIndex: number) => {
    if (isReordering) {
      toast.warning("正在排序中，請稍候...");
      return;
    }

    setIsReordering(true);
    const originalPrograms = [...programs];

    // Immediate UI update
    const newPrograms = [...programs];
    const [movedItem] = newPrograms.splice(fromIndex, 1);
    newPrograms.splice(toIndex, 0, movedItem);
    setPrograms(newPrograms);

    try {
      // Prepare order data
      const orderData = newPrograms.map((program, index) => ({
        id: program.id,
        order_index: index,
      }));

      console.log("[Programs Reorder] Calling API with:", orderData);
      await apiClient.reorderPrograms(orderData);
      console.log("[Programs Reorder] API call succeeded");

      toast.success("排序成功");
      setIsReordering(false);
    } catch (err) {
      console.error("[Programs Reorder] Failed to reorder programs:", err);
      toast.error("排序失敗");
      // Revert on error
      setPrograms(originalPrograms);
      setIsReordering(false);
    }
  };

  const handleReorderLessons = async (
    programId: number,
    fromIndex: number,
    toIndex: number,
  ) => {
    if (isReordering) {
      toast.warning("正在排序中，請稍候...");
      return;
    }

    // Find the program
    const program = programs.find((p) => p.id === programId);
    if (!program || !program.lessons) return;

    setIsReordering(true);
    const originalPrograms = [...programs];

    // Immediate UI update
    const newLessons = [...program.lessons];
    const [movedItem] = newLessons.splice(fromIndex, 1);
    newLessons.splice(toIndex, 0, movedItem);

    setPrograms((prevPrograms) =>
      prevPrograms.map((p) =>
        p.id === programId ? { ...p, lessons: newLessons } : p,
      ),
    );

    try {
      // Prepare order data
      const orderData = newLessons.map((lesson, index) => ({
        id: lesson.id,
        order_index: index,
      }));

      console.log(
        `[Lessons Reorder] Program ${programId}, Calling API with:`,
        orderData,
      );
      await apiClient.reorderLessons(programId, orderData);
      console.log(`[Lessons Reorder] API call succeeded`);

      toast.success("排序成功");
      setIsReordering(false);
    } catch (err) {
      console.error(`[Lessons Reorder] Failed to reorder lessons:`, err);
      toast.error("排序失敗");
      // Revert on error
      setPrograms(originalPrograms);
      setIsReordering(false);
    }
  };

  const handleReorderContents = async (
    lessonId: number,
    fromIndex: number,
    toIndex: number,
  ) => {
    if (isReordering) {
      toast.warning("正在排序中，請稍候...");
      return;
    }

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

    setIsReordering(true);
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

      console.log(
        `[Contents Reorder] Lesson ${lessonId}, Calling API with:`,
        orderData,
      );
      await apiClient.reorderContents(lessonId, orderData);
      console.log(`[Contents Reorder] API call succeeded`);

      toast.success("排序成功");
      setIsReordering(false);
    } catch (err) {
      console.error(`[Contents Reorder] Failed to reorder contents:`, err);
      toast.error("排序失敗");
      // Revert on error
      setPrograms(originalPrograms);
      setIsReordering(false);
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

  return (
    <TeacherLayout>
      <div className="relative h-full bg-gray-50">
        <div
          className={`p-6 space-y-4 transition-all duration-300 ${
            showReadingEditor && editorContentId !== null
              ? "pr-[calc(50%+2rem)]"
              : ""
          }`}
        >
          <RecursiveTreeAccordion
            data={programs}
            config={programTreeConfig}
            title="公版課程"
            showCreateButton
            createButtonText="新增課程"
            onCreateClick={handleCreateProgram}
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
                handleDeleteContent(parentId as number, item.id, item.title);
            }}
            onClick={(item, level, parentId) => {
              if (level === 2) {
                const program = programs.find((p) =>
                  p.lessons?.some((l) => l.id === parentId),
                );
                const lesson = program?.lessons?.find((l) => l.id === parentId);
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
                // Creating lesson inside program
                handleCreateLesson(parentId as number);
              } else if (level === 2) {
                // Creating content inside lesson - need to find program
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
                handleReorderLessons(parentId as number, fromIndex, toIndex);
              else if (level === 2)
                handleReorderContents(parentId as number, fromIndex, toIndex);
            }}
          />
        </div>

        {/* Reading Assessment Modal (新增模式) */}
        {showReadingEditor && editorLessonId && editorContentId === null && (
          <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="relative w-full max-w-7xl max-h-[90vh] bg-white rounded-lg p-6 flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold">新增朗讀內容</h2>
                <button
                  onClick={() => {
                    setShowReadingEditor(false);
                    setEditorLessonId(null);
                    setEditorContentId(null);
                    setSelectedContent(null);
                  }}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  aria-label="關閉"
                >
                  <svg
                    className="w-5 h-5 text-gray-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
              <div className="flex-1 overflow-hidden">
                <ReadingAssessmentPanel
                  lessonId={editorLessonId}
                  isCreating={true}
                  onSave={async (
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    newContent?: any,
                  ) => {
                    // 如果有返回新內容，直接更新前端狀態，不重整頁面
                    if (newContent && editorLessonId) {
                      setPrograms(
                        programs.map((program) => ({
                          ...program,
                          lessons: program.lessons?.map((lesson) => {
                            if (lesson.id === editorLessonId) {
                              return {
                                ...lesson,
                                contents: [
                                  ...(lesson.contents || []),
                                  newContent,
                                ],
                              };
                            }
                            return lesson;
                          }),
                        })),
                      );
                    }
                    setShowReadingEditor(false);
                    setEditorLessonId(null);
                    setEditorContentId(null);
                    setSelectedContent(null);
                    toast.success("內容已成功儲存");
                  }}
                  onCancel={() => {
                    setShowReadingEditor(false);
                    setEditorLessonId(null);
                    setEditorContentId(null);
                    setSelectedContent(null);
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Reading Assessment Panel (編輯模式 - 側邊欄) */}
        {showReadingEditor &&
          editorLessonId &&
          editorContentId !== null &&
          selectedContent && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 bg-black bg-opacity-20 z-40 transition-opacity"
                onClick={() => {
                  setShowReadingEditor(false);
                  setEditorLessonId(null);
                  setEditorContentId(null);
                  setSelectedContent(null);
                }}
              />

              {/* Panel */}
              <div className="fixed top-0 right-0 h-screen w-1/2 bg-white shadow-2xl border-l border-gray-200 z-50 overflow-auto animate-in slide-in-from-right duration-300">
                <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
                  <h2 className="text-lg font-semibold text-gray-900">
                    編輯內容
                  </h2>
                  <button
                    onClick={() => {
                      setShowReadingEditor(false);
                      setEditorLessonId(null);
                      setEditorContentId(null);
                      setSelectedContent(null);
                    }}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    aria-label="關閉"
                  >
                    <svg
                      className="w-5 h-5 text-gray-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>

                <div className="p-6">
                  <ReadingAssessmentPanel
                    lessonId={editorLessonId}
                    contentId={editorContentId}
                    content={{
                      id: selectedContent.id,
                      title: selectedContent.title,
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      items: (selectedContent.items || []) as any,
                    }}
                    onSave={async () => {
                      // 只顯示成功訊息，不重整 tree
                      toast.success("內容已成功儲存");
                    }}
                    onCancel={() => {
                      setShowReadingEditor(false);
                      setEditorLessonId(null);
                      setEditorContentId(null);
                      setSelectedContent(null);
                    }}
                  />
                </div>
              </div>
            </>
          )}

        {/* Dialogs */}
        <ProgramDialog
          program={selectedProgram}
          dialogType={programDialogType}
          isTemplate={true}
          onClose={() => {
            setProgramDialogType(null);
            setSelectedProgram(null);
          }}
          onSave={handleSaveProgram}
          onDelete={handleDeleteProgramConfirm}
        />

        <LessonDialog
          lesson={selectedLesson}
          dialogType={lessonDialogType}
          programId={lessonProgramId}
          onClose={() => {
            setLessonDialogType(null);
            setSelectedLesson(null);
            setLessonProgramId(undefined);
          }}
          onSave={handleSaveLesson}
          onDelete={handleDeleteLessonConfirm}
        />

        {contentLessonInfo && (
          <ContentTypeDialog
            open={showContentTypeDialog}
            lessonInfo={contentLessonInfo}
            onClose={() => {
              setShowContentTypeDialog(false);
              setContentLessonInfo(null);
            }}
            onSelect={(selection) => {
              setShowContentTypeDialog(false);
              setContentLessonInfo(null);

              // Handle different content types
              if (selection.type === "reading_assessment") {
                // Open modal for new content
                setEditorLessonId(selection.lessonId);
                setEditorContentId(null); // null = new content
                setSelectedContent(null); // No existing content
                setShowReadingEditor(true);
              } else {
                toast.info(`${selection.type} 功能開發中`);
              }
            }}
          />
        )}
      </div>
    </TeacherLayout>
  );
}
