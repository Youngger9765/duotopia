import { useEffect, useState } from "react";
import { RecursiveTreeAccordion } from "./RecursiveTreeAccordion";
import { programTreeConfig } from "./programTreeConfig";
import ReadingAssessmentPanel from "@/components/ReadingAssessmentPanel";
import SentenceMakingPanel from "@/components/activities/SentenceMakingActivity";
import VocabularySetPanel from "@/components/VocabularySetPanel";
import ContentTypeDialog from "@/components/ContentTypeDialog";
import {
  ProgramTreeLesson,
  ProgramTreeProgram,
  useProgramTree,
} from "@/hooks/useProgramTree";
import { useContentEditor } from "@/hooks/useContentEditor";
import { useProgramAPI } from "@/hooks/useProgramAPI";
import { Content, ContentItem } from "@/types";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

type TreeItem = ProgramTreeProgram | ProgramTreeLesson | Content;
type ReadingPanelRow = {
  id: string | number;
  text: string;
  definition: string;
  translation?: string;
  audio_url?: string;
  audioUrl?: string;
  example_sentence?: string;
  example_sentence_translation?: string;
};

/**
 * Props for the ProgramTreeView component.
 *
 * This component provides a hierarchical tree view for Programs, Lessons, and Content
 * with full CRUD operations at all three levels.
 *
 * **Required Props:**
 * - `programs`: The tree data to display
 * - `scope`: The authorization scope (teacher/organization/school)
 *
 * **Optional CRUD Props (with internal fallbacks):**
 * All CRUD-related props are optional. If not provided, the component uses internal
 * handlers that call the API directly via useProgramAPI:
 *
 * - `onCreateClick`: Create new program at root level
 *   - Fallback: Creates program via API and refreshes
 *
 * - `onEdit`: Edit program/lesson at any level
 *   - Fallback: Updates via API based on level (0=program, 1=lesson)
 *
 * - `onDelete`: Delete program/lesson/content at any level
 *   - Fallback: Deletes via API based on level (0=program, 1=lesson, 2=content)
 *
 * - `onCreate`: Create new lesson/content (level 1-2)
 *   - Fallback: For lessons only; content creation uses internal dialog
 *
 * - `onReorder`: Reorder items at any level
 *   - Fallback: Calls reorder API and updates local state optimistically
 *
 * **Why provide CRUD props?**
 * Override the internal handlers if you need custom behavior (e.g., show custom dialog,
 * additional validation, different API calls).
 *
 * **Recommended Usage:**
 * ```tsx
 * // Minimal usage (all CRUD handled internally)
 * <ProgramTreeView
 *   programs={programs}
 *   scope="teacher"
 *   onRefresh={() => refetch()}
 * />
 *
 * // With custom create handler
 * <ProgramTreeView
 *   programs={programs}
 *   scope="organization"
 *   organizationId={orgId}
 *   onCreateClick={handleCustomCreate}
 *   onRefresh={() => refetch()}
 * />
 * ```
 */
interface ProgramTreeViewProps {
  /** Required: The program tree data to display */
  programs: ProgramTreeProgram[];

  /** Optional: Callback when internal state changes (for syncing with parent) */
  onProgramsChange?: (programs: ProgramTreeProgram[]) => void;

  /** Optional: Show the root-level "Create Program" button */
  showCreateButton?: boolean;

  /** Optional: Custom text for the create button */
  createButtonText?: string;

  /** Optional: Custom handler for root-level program creation. Fallback: Internal API call */
  onCreateClick?: () => void;

  /** Optional: Custom handler for editing programs/lessons. Fallback: Internal API call */
  onEdit?: (item: TreeItem, level: number, parentId?: string | number) => void;

  /** Optional: Custom handler for deleting programs/lessons/content. Fallback: Internal API call */
  onDelete?: (
    item: TreeItem,
    level: number,
    parentId?: string | number,
  ) => void;

  /** Optional: Custom handler for creating lessons. Fallback: Internal API call (content uses dialog) */
  onCreate?: (level: number, parentId: string | number) => void;

  /** Optional: Custom handler for reordering at any level. Fallback: Internal API call with optimistic updates */
  onReorder?: (
    fromIndex: number,
    toIndex: number,
    level: number,
    parentId?: string | number,
  ) => void;

  /** Optional: Callback to refresh data after mutations (called by internal handlers) */
  onRefresh?: () => void;

  /** Required: Authorization scope for API calls (teacher/organization/school) */
  scope: "teacher" | "organization" | "school";

  /** Optional: Organization ID (required when scope='organization' or scope='school') */
  organizationId?: string;

  /** Optional: School ID (required when scope='school') */
  schoolId?: string;
}

export function ProgramTreeView({
  programs: externalPrograms,
  onProgramsChange,
  showCreateButton = false,
  createButtonText,
  onCreateClick,
  onEdit,
  onDelete,
  onCreate,
  onReorder,
  onRefresh,
  scope,
  organizationId,
  schoolId,
}: ProgramTreeViewProps) {
  const { programs, setPrograms, updateProgramContent, addContentToLesson } =
    useProgramTree(externalPrograms);

  const programAPI = useProgramAPI({ scope, organizationId, schoolId });

  // 🔥 Helper: 根據 lessonId 找到對應的 Program level
  const getProgramLevelByLessonId = (lessonId: number | undefined): string | undefined => {
    if (!lessonId) return undefined;

    for (const program of programs) {
      const lesson = program.lessons?.find((l) => l.id === lessonId);
      if (lesson) {
        console.log(`[ProgramTreeView] Found Program level for lesson ${lessonId}:`, program.level);
        return program.level;
      }
    }

    console.warn(`[ProgramTreeView] No Program found for lesson ${lessonId}`);
    return undefined;
  };

  const {
    showReadingEditor,
    editorLessonId,
    editorContentId,
    selectedContent,
    showSentenceMakingEditor,
    sentenceMakingLessonId,
    sentenceMakingContentId,
    showVocabularySetEditor,
    vocabularySetLessonId,
    vocabularySetContentId,
    openContentEditor,
    openReadingCreateEditor,
    openSentenceMakingCreateEditor,
    openVocabularySetCreateEditor,
    closeReadingEditor,
    closeSentenceMakingEditor,
    closeVocabularySetEditor,
  } = useContentEditor();

  const [showContentTypeDialog, setShowContentTypeDialog] = useState(false);
  const [contentLessonInfo, setContentLessonInfo] = useState<{
    programName: string;
    lessonName: string;
    lessonId: number;
  } | null>(null);

  // Edit dialog states
  const [programEditDialog, setProgramEditDialog] = useState<{
    open: boolean;
    program: ProgramTreeProgram | null;
  }>({ open: false, program: null });

  const [lessonEditDialog, setLessonEditDialog] = useState<{
    open: boolean;
    lesson: ProgramTreeLesson | null;
    programId: number | null;
  }>({ open: false, lesson: null, programId: null });

  // Notify parent of changes (one-way: child -> parent)
  // Note: We do NOT sync externalPrograms back to avoid infinite loop
  // Parent should use a key prop to force refresh if needed
  useEffect(() => {
    if (onProgramsChange && programs !== externalPrograms) {
      onProgramsChange(programs);
    }
  }, [programs]); // Deliberately exclude onProgramsChange and externalPrograms from deps

  // Internal reorder handler
  const handleInternalReorder = async (
    fromIndex: number,
    toIndex: number,
    level: number,
    parentId?: string | number,
  ) => {
    console.log("🔍 [ProgramTreeView] handleInternalReorder called:", {
      fromIndex,
      toIndex,
      level,
      parentId,
      scope,
      organizationId,
      schoolId,
    });
    try {
      if (level === 0) {
        // Reorder programs - use INSERT logic (splice)
        const newPrograms = [...programs];
        const [movedItem] = newPrograms.splice(fromIndex, 1); // Remove from old position
        newPrograms.splice(toIndex, 0, movedItem); // Insert at new position

        const orderData = newPrograms
          .filter((p) => p.id !== undefined)
          .map((program, index) => ({
            id: program.id!,
            order_index: index, // Use the new index directly
          }));
        console.log("📤 [ProgramTreeView] Sending reorder request:", {
          orderData,
          scope,
          organizationId,
        });
        await programAPI.reorderPrograms(orderData);

        // Update local state immediately (no refresh)
        setPrograms(newPrograms);
        if (onProgramsChange) {
          onProgramsChange(newPrograms);
        }
      } else if (level === 1) {
        // Reorder lessons within a program
        const programId =
          typeof parentId === "string" ? parseInt(parentId) : parentId;
        if (!programId)
          throw new Error("Program ID is required for lesson reorder");

        const program = programs.find((p) => p.id === programId);
        if (!program?.lessons) throw new Error("Program or lessons not found");

        // Use INSERT logic
        const newLessons = [...program.lessons];
        const [movedItem] = newLessons.splice(fromIndex, 1);
        newLessons.splice(toIndex, 0, movedItem);

        const orderData = newLessons
          .filter((l) => l.id !== undefined)
          .map((lesson, index) => ({
            id: lesson.id!,
            order_index: index, // Use the new index directly
          }));
        await programAPI.reorderLessons(programId, orderData);

        // Update local state immediately (no refresh)
        const updatedPrograms = programs.map((p) =>
          p.id === programId ? { ...p, lessons: newLessons } : p,
        );
        setPrograms(updatedPrograms);
        if (onProgramsChange) {
          onProgramsChange(updatedPrograms);
        }
      } else if (level === 2) {
        // Reorder contents within a lesson
        const lessonId =
          typeof parentId === "string" ? parseInt(parentId) : parentId;
        if (!lessonId)
          throw new Error("Lesson ID is required for content reorder");

        const program = programs.find((p) =>
          p.lessons?.some((l) => l.id === lessonId),
        );
        const lesson = program?.lessons?.find((l) => l.id === lessonId);
        if (!lesson?.contents) throw new Error("Lesson or contents not found");

        // Use INSERT logic
        const newContents = [...lesson.contents];
        const [movedItem] = newContents.splice(fromIndex, 1);
        newContents.splice(toIndex, 0, movedItem);

        const orderData = newContents
          .filter((c) => c.id !== undefined)
          .map((content, index) => ({
            id: content.id!,
            order_index: index, // Use the new index directly
          }));
        await programAPI.reorderContents(lessonId, orderData);

        // Update local state immediately (no refresh)
        const updatedPrograms = programs.map((p) => {
          if (p.lessons?.some((l) => l.id === lessonId)) {
            return {
              ...p,
              lessons: p.lessons.map((l) =>
                l.id === lessonId ? { ...l, contents: newContents } : l,
              ),
            };
          }
          return p;
        });
        setPrograms(updatedPrograms);
        if (onProgramsChange) {
          onProgramsChange(updatedPrograms);
        }
      }

      toast.success("順序已更新");
    } catch (error) {
      console.error("Reorder failed:", error);
      toast.error("更新順序失敗");
      // Rollback UI by refreshing
      if (onRefresh) {
        await onRefresh();
      }
    }
  };

  // Internal Program CRUD handlers
  const handleCreateProgram = async () => {
    // Open dialog for user to input name and description
    setProgramEditDialog({
      open: true,
      program: { name: "", description: "" } as ProgramTreeProgram, // Empty program for create
    });
  };

  const handleEditProgram = (item: TreeItem, level: number) => {
    if (level !== 0) return; // Only handle program level
    setProgramEditDialog({ open: true, program: item as ProgramTreeProgram });
  };

  const handleDeleteProgram = async (item: TreeItem, level: number) => {
    if (level !== 0) return; // Only handle program level

    const program = item as ProgramTreeProgram;

    // Confirmation dialog
    const confirmed = window.confirm(
      `確定要刪除教材「${program.name}」嗎？\n\n⚠️ 此操作將同時刪除所有課程和內容，且無法復原。`,
    );

    if (!confirmed) return;

    try {
      await programAPI.deleteProgram(program.id!);

      toast.success("Program deleted successfully");

      // Local update: remove from programs array
      const updatedPrograms = programs.filter((p) => p.id !== program.id);
      setPrograms(updatedPrograms);
      if (onProgramsChange) {
        onProgramsChange(updatedPrograms);
      }
    } catch (error) {
      console.error("Failed to delete program:", error);
      toast.error("Failed to delete program");
    }
  };

  // Internal Lesson CRUD handlers
  const handleCreateLesson = async (
    level: number,
    parentId: string | number,
  ) => {
    if (level !== 1) return; // Only handle lesson level

    const programId =
      typeof parentId === "string" ? parseInt(parentId) : parentId;

    // Open dialog for user to input name and description
    setLessonEditDialog({
      open: true,
      lesson: { name: "", description: "" } as ProgramTreeLesson, // Empty lesson for create
      programId,
    });
  };

  const handleEditLesson = (
    item: TreeItem,
    level: number,
    parentId?: string | number,
  ) => {
    if (level !== 1) return; // Only handle lesson level

    const lesson = item as ProgramTreeLesson;
    const programId =
      typeof parentId === "string" ? parseInt(parentId) : (parentId ?? null);

    if (!programId) {
      console.error("Program ID is required for lesson edit");
      return;
    }

    setLessonEditDialog({
      open: true,
      lesson,
      programId,
    });
  };

  const handleDeleteLesson = async (
    item: TreeItem,
    level: number,
    parentId?: string | number,
  ) => {
    if (level !== 1) return; // Only handle lesson level

    const lesson = item as ProgramTreeLesson;
    const programId =
      typeof parentId === "string" ? parseInt(parentId) : parentId;

    if (!programId) {
      console.error("Program ID is required for lesson delete");
      return;
    }

    // Confirmation dialog
    const confirmed = window.confirm(
      `確定要刪除課程「${lesson.name}」嗎？\n\n⚠️ 此操作將同時刪除所有內容，且無法復原。`,
    );

    if (!confirmed) return;

    try {
      await programAPI.deleteLesson(lesson.id!);

      toast.success("Lesson deleted successfully");

      // Local update: remove lesson from program
      const updatedPrograms = programs.map((program) => {
        if (program.id === programId) {
          return {
            ...program,
            lessons: program.lessons?.filter((l) => l.id !== lesson.id) || [],
          };
        }
        return program;
      });
      setPrograms(updatedPrograms);
      if (onProgramsChange) {
        onProgramsChange(updatedPrograms);
      }
    } catch (error) {
      console.error("Failed to delete lesson:", error);
      toast.error("Failed to delete lesson");
    }
  };

  // Internal Content Delete handler
  const handleDeleteContent = async (
    item: TreeItem,
    level: number,
    parentId?: string | number,
  ) => {
    if (level !== 2) return; // Only handle content level

    const content = item as Content;
    const lessonId =
      typeof parentId === "string" ? parseInt(parentId) : parentId;

    if (!lessonId) {
      console.error("Lesson ID is required for content delete");
      return;
    }

    // Confirmation dialog
    const confirmed = window.confirm(
      `確定要刪除內容「${content.title}」嗎？\n\n⚠️ 此操作無法復原。`,
    );

    if (!confirmed) return;

    try {
      await programAPI.deleteContent(content.id!);

      toast.success("Content deleted successfully");

      // Local update: remove content from lesson
      const updatedPrograms = programs.map((program) => {
        const updatedLessons = program.lessons?.map((lesson) => {
          if (lesson.id === lessonId) {
            return {
              ...lesson,
              contents:
                lesson.contents?.filter((c) => c.id !== content.id) || [],
            };
          }
          return lesson;
        });
        return { ...program, lessons: updatedLessons };
      });
      setPrograms(updatedPrograms);
      if (onProgramsChange) {
        onProgramsChange(updatedPrograms);
      }
    } catch (error) {
      console.error("Failed to delete content:", error);
      toast.error("Failed to delete content");
    }
  };

  const handleContentClick = (
    item: TreeItem,
    level: number,
    parentId?: string | number,
  ) => {
    if (level === 2) {
      // Content level
      const content = item as Content;
      const numericParentId =
        typeof parentId === "string" ? parseInt(parentId) : parentId;
      const program = programs.find((p) =>
        p.lessons?.some((l) => l.id === numericParentId),
      );
      const lesson = program?.lessons?.find((l) => l.id === numericParentId);

      // Transform content items to match ReadingAssessmentPanel format
      const transformedItems: ContentItem[] | undefined = content.items?.map(
        (contentItem, index) => ({
          id: contentItem.id ?? index + 1,
          text: contentItem.text || "",
          definition: contentItem.translation || "", // Map translation to definition
          translation: contentItem.translation || "",
          audioUrl: contentItem.audio_url,
          audio_url: contentItem.audio_url,
          example_sentence: contentItem.example_sentence,
          example_sentence_translation:
            contentItem.example_sentence_translation,
        }),
      );

      openContentEditor({
        ...content,
        items: transformedItems,
        lesson_id: numericParentId as number,
        lessonName: lesson?.name,
        programName: program?.name,
      });
    }
  };

  const handleCreate = (level: number, parentId: string | number) => {
    // Level 2: Content creation
    if (level === 2) {
      const numericParentId =
        typeof parentId === "string" ? parseInt(parentId) : parentId;
      const program = programs.find((p) =>
        p.lessons?.some((l) => l.id === numericParentId),
      );
      const lesson = program?.lessons?.find((l) => l.id === numericParentId);

      if (program && lesson && lesson.id) {
        setContentLessonInfo({
          programName: program.name,
          lessonName: lesson.name,
          lessonId: lesson.id,
        });
        setShowContentTypeDialog(true);
        return;
      }
    }

    // Level 1: Lesson creation (use internal handler if no onCreate prop)
    if (level === 1) {
      if (onCreate) {
        onCreate(level, parentId);
      } else {
        handleCreateLesson(level, parentId);
      }
      return;
    }

    // Level 0 or others: Use onCreate prop if provided
    if (onCreate) {
      onCreate(level, parentId);
    }
  };

  const readingPanelContent:
    | {
        id?: number;
        title?: string;
        items?: ReadingPanelRow[];
      }
    | undefined = selectedContent
    ? {
        id: selectedContent.id,
        title: selectedContent.title,
        items: selectedContent.items?.map((contentItem, index) => ({
          id: contentItem.id ?? index + 1,
          text: contentItem.text || "",
          definition: contentItem.translation || "",
          translation: contentItem.translation || "",
          audio_url: contentItem.audio_url,
          audioUrl: contentItem.audio_url,
          example_sentence: contentItem.example_sentence,
          example_sentence_translation:
            contentItem.example_sentence_translation,
        })),
      }
    : undefined;

  // Combined handlers that delegate to Program or Lesson handlers based on level
  const handleInternalEdit = (
    item: TreeItem,
    level: number,
    parentId?: string | number,
  ) => {
    if (level === 0) {
      handleEditProgram(item, level);
    } else if (level === 1) {
      handleEditLesson(item, level, parentId);
    }
  };

  const handleInternalDelete = (
    item: TreeItem,
    level: number,
    parentId?: string | number,
  ) => {
    if (level === 0) {
      handleDeleteProgram(item, level);
    } else if (level === 1) {
      handleDeleteLesson(item, level, parentId);
    } else if (level === 2) {
      handleDeleteContent(item, level, parentId);
    }
  };

  return (
    <>
      <RecursiveTreeAccordion
        data={programs}
        config={programTreeConfig}
        showCreateButton={showCreateButton}
        createButtonText={createButtonText}
        onCreateClick={onCreateClick || handleCreateProgram}
        onEdit={onEdit || handleInternalEdit}
        onDelete={onDelete || handleInternalDelete}
        onClick={handleContentClick}
        onCreate={handleCreate}
        onReorder={onReorder || handleInternalReorder}
      />

      {/* Reading Assessment Modal */}
      {showReadingEditor && editorLessonId && editorContentId === null && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="relative w-full max-w-7xl max-h-[90vh] bg-white rounded-lg p-6 flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">新增內容</h2>
              <button
                onClick={closeReadingEditor}
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
            <div className="flex-1 overflow-hidden flex flex-col min-h-0">
              <div className="flex-1 overflow-auto p-6 min-h-0">
                <ReadingAssessmentPanel
                  lessonId={editorLessonId}
                  programLevel={getProgramLevelByLessonId(editorLessonId)}
                  isCreating={true}
                  onSave={async (newContent?: Content) => {
                    if (newContent && editorLessonId) {
                      addContentToLesson(editorLessonId, newContent);
                    }
                    toast.success("內容已儲存");
                    closeReadingEditor(); // Close dialog after save to prevent duplicate creation
                  }}
                  onCancel={closeReadingEditor}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reading Assessment Panel */}
      {showReadingEditor &&
        editorLessonId &&
        editorContentId !== null &&
        selectedContent && (
          <>
            <div
              className="fixed inset-0 bg-black bg-opacity-20 z-40 transition-opacity"
              onClick={closeReadingEditor}
            />
            <div className="fixed top-0 right-0 h-screen w-1/2 bg-white shadow-2xl border-l border-gray-200 z-50 flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200 flex-shrink-0">
                <h2 className="text-xl font-semibold text-gray-900">
                  編輯內容
                </h2>
                <button
                  onClick={closeReadingEditor}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
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
              {/* Content */}
              <div className="flex-1 overflow-hidden flex flex-col min-h-0">
                <div className="flex-1 overflow-auto p-6 min-h-0">
                  <ReadingAssessmentPanel
                    content={readingPanelContent}
                    lessonId={editorLessonId}
                    programLevel={getProgramLevelByLessonId(editorLessonId)}
                    contentId={editorContentId}
                    isCreating={false}
                    onSave={async (updatedContent?: Content) => {
                      if (updatedContent && editorContentId) {
                        updateProgramContent(editorContentId, updatedContent);
                      }
                      // Keep editor open after save for continued editing
                      toast.success("內容已儲存");
                      // Local update already done by updateProgramContent, no need to refresh
                    }}
                    onCancel={closeReadingEditor}
                  />
                </div>
              </div>
            </div>
          </>
        )}

      {/* Sentence Making Modal */}
      {showSentenceMakingEditor &&
        sentenceMakingLessonId &&
        sentenceMakingContentId === null && (
          <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="relative w-full max-w-7xl max-h-[90vh] bg-white rounded-lg p-6 flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold">句子模組設定</h2>
                <button
                  onClick={closeSentenceMakingEditor}
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
              <div className="flex-1 overflow-hidden min-h-0 flex flex-col">
                {/* TODO: Fix SentenceMakingPanel props interface mismatch */}
                <SentenceMakingPanel
                  {...({
                    content: undefined,
                    editingContent: {
                      id: sentenceMakingContentId || undefined,
                    },
                    lessonId: sentenceMakingLessonId,
                    onSave: async (newContent?: Content) => {
                      if (newContent && sentenceMakingLessonId) {
                        addContentToLesson(sentenceMakingLessonId, newContent);
                      }
                      closeSentenceMakingEditor();
                      toast.success("內容已儲存");
                      // Local update already done by addContentToLesson, no need to refresh
                    },
                    onCancel: closeSentenceMakingEditor,
                    isCreating: true,
                  } as unknown as React.ComponentProps<
                    typeof SentenceMakingPanel
                  >)}
                />
              </div>
            </div>
          </div>
        )}

      {/* Sentence Making Panel */}
      {showSentenceMakingEditor &&
        sentenceMakingLessonId &&
        sentenceMakingContentId !== null && (
          <>
            <div
              className="fixed inset-0 bg-black bg-opacity-20 z-40 transition-opacity"
              onClick={closeSentenceMakingEditor}
            />
            <div className="fixed top-0 right-0 h-screen w-1/2 bg-white shadow-2xl border-l border-gray-200 z-50 flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200 flex-shrink-0">
                <h2 className="text-xl font-semibold text-gray-900">
                  編輯內容
                </h2>
                <button
                  onClick={closeSentenceMakingEditor}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
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
              {/* Content */}
              <div className="flex-1 overflow-hidden flex flex-col min-h-0">
                <div className="flex-1 overflow-auto p-6 min-h-0">
                  {/* TODO: Fix SentenceMakingPanel props interface mismatch */}
                  <SentenceMakingPanel
                    {...({
                      lessonId: sentenceMakingLessonId,
                      contentId: sentenceMakingContentId,
                      onSave: async () => {
                        closeSentenceMakingEditor();
                        toast.success("內容已儲存");
                        // Note: SentenceMakingPanel edit doesn't provide updated data in callback,
                        // so we keep onRefresh here for edit operations
                        if (onRefresh) onRefresh();
                      },
                      onCancel: closeSentenceMakingEditor,
                    } as unknown as React.ComponentProps<
                      typeof SentenceMakingPanel
                    >)}
                  />
                </div>
              </div>
            </div>
          </>
        )}

      {/* Vocabulary Set Modal - Create Mode */}
      {showVocabularySetEditor &&
        vocabularySetLessonId &&
        vocabularySetContentId === null && (
          <Dialog open={true} onOpenChange={() => closeVocabularySetEditor()}>
            <DialogContent className="max-w-7xl max-h-[90vh] flex flex-col">
              <DialogHeader className="flex-shrink-0">
                <DialogTitle>新增單字集</DialogTitle>
              </DialogHeader>
              <div className="flex-1 overflow-y-auto min-h-0">
                <VocabularySetPanel
                  lessonId={vocabularySetLessonId}
                  programLevel={getProgramLevelByLessonId(vocabularySetLessonId)}
                  isCreating={true}
                  onSave={async () => {
                    closeVocabularySetEditor();
                    toast.success("內容已儲存");
                    if (onRefresh) onRefresh();
                  }}
                />
              </div>
            </DialogContent>
          </Dialog>
        )}

      {/* Vocabulary Set Panel - Edit Mode */}
      {showVocabularySetEditor &&
        vocabularySetLessonId &&
        vocabularySetContentId !== null && (
          <>
            <div
              className="fixed inset-0 bg-black bg-opacity-20 z-40 transition-opacity"
              onClick={closeVocabularySetEditor}
            />
            <div className="fixed top-0 right-0 h-screen w-1/2 bg-white shadow-2xl border-l border-gray-200 z-50 flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200 flex-shrink-0">
                <h2 className="text-xl font-semibold text-gray-900">
                  編輯單字集
                </h2>
                <button
                  onClick={closeVocabularySetEditor}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
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
              {/* Content */}
              <div className="flex-1 overflow-hidden flex flex-col min-h-0">
                <div className="flex-1 overflow-auto p-6 min-h-0">
                  <VocabularySetPanel
                    content={
                      vocabularySetContentId
                        ? { id: vocabularySetContentId }
                        : undefined
                    }
                    editingContent={
                      vocabularySetContentId
                        ? { id: vocabularySetContentId }
                        : undefined
                    }
                    lessonId={vocabularySetLessonId}
                    programLevel={getProgramLevelByLessonId(vocabularySetLessonId)}
                    isCreating={false}
                    onSave={async () => {
                      closeVocabularySetEditor();
                      toast.success("內容已儲存");
                      if (onRefresh) onRefresh();
                    }}
                  />
                </div>
              </div>
            </div>
          </>
        )}

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

            if (
              selection.type === "reading_assessment" ||
              selection.type === "example_sentences" ||
              selection.type === "EXAMPLE_SENTENCES"
            ) {
              openReadingCreateEditor(selection.lessonId);
            } else if (
              selection.type === "SENTENCE_MAKING" ||
              selection.type === "sentence_making"
            ) {
              openSentenceMakingCreateEditor(selection.lessonId);
            } else if (
              selection.type === "vocabulary_set" ||
              selection.type === "VOCABULARY_SET"
            ) {
              openVocabularySetCreateEditor(selection.lessonId);
            } else {
              toast.info("此內容類型仍在開發中");
            }
          }}
        />
      )}

      {/* Program Edit Dialog */}
      <Dialog
        open={programEditDialog.open}
        onOpenChange={(open) => setProgramEditDialog({ open, program: null })}
      >
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {programEditDialog.program?.id ? "編輯教材" : "新增教材"}
            </DialogTitle>
            <DialogDescription>
              {programEditDialog.program?.id
                ? "修改教材的名稱和描述"
                : "輸入新教材的名稱和描述"}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="program-name">名稱</Label>
              <Input
                id="program-name"
                value={programEditDialog.program?.name || ""}
                onChange={(e) => {
                  if (programEditDialog.program) {
                    setProgramEditDialog({
                      ...programEditDialog,
                      program: {
                        ...programEditDialog.program,
                        name: e.target.value,
                      },
                    });
                  }
                }}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="program-description">描述</Label>
              <Textarea
                id="program-description"
                value={programEditDialog.program?.description || ""}
                onChange={(e) => {
                  if (programEditDialog.program) {
                    setProgramEditDialog({
                      ...programEditDialog,
                      program: {
                        ...programEditDialog.program,
                        description: e.target.value,
                      },
                    });
                  }
                }}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() =>
                setProgramEditDialog({ open: false, program: null })
              }
            >
              取消
            </Button>
            <Button
              onClick={async () => {
                if (!programEditDialog.program) return;

                try {
                  if (programEditDialog.program.id) {
                    // Update existing program
                    const updatedProgram = await programAPI.updateProgram(
                      programEditDialog.program.id,
                      {
                        name: programEditDialog.program.name,
                        description: programEditDialog.program.description,
                      },
                    );
                    toast.success("教材更新成功");

                    // Local update: replace updated program in array
                    const updatedPrograms = programs.map((p) =>
                      p.id === programEditDialog.program!.id
                        ? { ...p, ...updatedProgram }
                        : p,
                    );
                    setPrograms(updatedPrograms);
                    if (onProgramsChange) {
                      onProgramsChange(updatedPrograms);
                    }
                  } else {
                    // Create new program - get server response with ID
                    const newProgram = await programAPI.createProgram({
                      name: programEditDialog.program.name,
                      description: programEditDialog.program.description,
                    });
                    toast.success("教材建立成功");

                    // Local update: append new program to end
                    const updatedPrograms = [...programs, newProgram];
                    setPrograms(updatedPrograms); // Update internal state
                    if (onProgramsChange) {
                      onProgramsChange(updatedPrograms);
                    }
                  }

                  setProgramEditDialog({ open: false, program: null });
                } catch (error) {
                  console.error("Failed to save program:", error);
                  toast.error(
                    programEditDialog.program.id
                      ? "更新教材失敗"
                      : "建立教材失敗",
                  );
                }
              }}
            >
              {programEditDialog.program?.id ? "儲存" : "建立"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Lesson Edit Dialog */}
      <Dialog
        open={lessonEditDialog.open}
        onOpenChange={(open) =>
          setLessonEditDialog({ open, lesson: null, programId: null })
        }
      >
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {lessonEditDialog.lesson?.id ? "編輯課程" : "新增課程"}
            </DialogTitle>
            <DialogDescription>
              {lessonEditDialog.lesson?.id
                ? "修改課程的名稱和描述"
                : "輸入新課程的名稱和描述"}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="lesson-name">名稱</Label>
              <Input
                id="lesson-name"
                value={lessonEditDialog.lesson?.name || ""}
                onChange={(e) => {
                  if (lessonEditDialog.lesson) {
                    setLessonEditDialog({
                      ...lessonEditDialog,
                      lesson: {
                        ...lessonEditDialog.lesson,
                        name: e.target.value,
                      },
                    });
                  }
                }}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="lesson-description">描述</Label>
              <Textarea
                id="lesson-description"
                value={lessonEditDialog.lesson?.description || ""}
                onChange={(e) => {
                  if (lessonEditDialog.lesson) {
                    setLessonEditDialog({
                      ...lessonEditDialog,
                      lesson: {
                        ...lessonEditDialog.lesson,
                        description: e.target.value,
                      },
                    });
                  }
                }}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() =>
                setLessonEditDialog({
                  open: false,
                  lesson: null,
                  programId: null,
                })
              }
            >
              取消
            </Button>
            <Button
              onClick={async () => {
                if (!lessonEditDialog.lesson || !lessonEditDialog.programId)
                  return;

                try {
                  if (lessonEditDialog.lesson.id) {
                    // Update existing lesson
                    const updatedLesson = await programAPI.updateLesson(
                      lessonEditDialog.lesson.id,
                      {
                        name: lessonEditDialog.lesson.name,
                        description: lessonEditDialog.lesson.description || "",
                      },
                    );
                    toast.success("課程更新成功");

                    // Local update: replace updated lesson in program
                    const updatedPrograms = programs.map((program) => {
                      if (program.id === lessonEditDialog.programId) {
                        return {
                          ...program,
                          lessons: (program.lessons || []).map((lesson) =>
                            lesson.id === lessonEditDialog.lesson!.id
                              ? { ...lesson, ...updatedLesson }
                              : lesson,
                          ),
                        };
                      }
                      return program;
                    });
                    setPrograms(updatedPrograms);
                    if (onProgramsChange) {
                      onProgramsChange(updatedPrograms);
                    }
                  } else {
                    // Create new lesson - get server response with ID
                    const newLesson = await programAPI.createLesson(
                      lessonEditDialog.programId,
                      {
                        name: lessonEditDialog.lesson.name,
                        description: lessonEditDialog.lesson.description || "",
                      },
                    );
                    toast.success("課程建立成功");

                    // Local update: add new lesson to program
                    const updatedPrograms = programs.map((program) => {
                      if (program.id === lessonEditDialog.programId) {
                        return {
                          ...program,
                          lessons: [...(program.lessons || []), newLesson],
                        };
                      }
                      return program;
                    });
                    setPrograms(updatedPrograms);
                    if (onProgramsChange) {
                      onProgramsChange(updatedPrograms);
                    }
                  }

                  setLessonEditDialog({
                    open: false,
                    lesson: null,
                    programId: null,
                  });
                } catch (error) {
                  console.error("Failed to save lesson:", error);
                  toast.error(
                    lessonEditDialog.lesson.id
                      ? "更新課程失敗"
                      : "建立課程失敗",
                  );
                }
              }}
            >
              {lessonEditDialog.lesson?.id ? "儲存" : "建立"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
