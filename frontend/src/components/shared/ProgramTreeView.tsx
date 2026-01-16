import { useEffect, useState } from "react";
import { RecursiveTreeAccordion } from "./RecursiveTreeAccordion";
import { programTreeConfig } from "./programTreeConfig";
import ReadingAssessmentPanel from "@/components/ReadingAssessmentPanel";
import SentenceMakingPanel from "@/components/SentenceMakingPanel";
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

interface ProgramTreeViewProps {
  programs: ProgramTreeProgram[];
  onProgramsChange?: (programs: ProgramTreeProgram[]) => void;
  showCreateButton?: boolean;
  createButtonText?: string;
  onCreateClick?: () => void;
  onEdit?: (item: TreeItem, level: number, parentId?: string | number) => void;
  onDelete?: (item: TreeItem, level: number, parentId?: string | number) => void;
  onCreate?: (level: number, parentId: string | number) => void;
  onReorder?: (fromIndex: number, toIndex: number, level: number, parentId?: string | number) => void;
  onRefresh?: () => void;
  // Scope props for reorder functionality
  scope: 'teacher' | 'organization' | 'school';
  organizationId?: string;
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

  const {
    showReadingEditor,
    editorLessonId,
    editorContentId,
    selectedContent,
    showSentenceMakingEditor,
    sentenceMakingLessonId,
    sentenceMakingContentId,
    openContentEditor,
    openReadingCreateEditor,
    openSentenceMakingCreateEditor,
    closeReadingEditor,
    closeSentenceMakingEditor,
  } = useContentEditor();

  const [showContentTypeDialog, setShowContentTypeDialog] = useState(false);
  const [contentLessonInfo, setContentLessonInfo] = useState<{
    programName: string;
    lessonName: string;
    lessonId: number;
  } | null>(null);

  // Sync external programs to internal state
  useEffect(() => {
    setPrograms(externalPrograms);
  }, [externalPrograms, setPrograms]);

  // Notify parent of changes
  useEffect(() => {
    if (onProgramsChange) {
      onProgramsChange(programs);
    }
  }, [programs, onProgramsChange]);

  // Internal reorder handler
  const handleInternalReorder = async (
    fromIndex: number,
    toIndex: number,
    level: number,
    parentId?: string | number
  ) => {
    try {
      if (level === 0) {
        // Reorder programs
        const orderData = programs
          .filter((p) => p.id !== undefined)
          .map((program, index) => ({
            id: program.id!,
            order_index: index === fromIndex ? toIndex : index === toIndex ? fromIndex : index,
          }));
        await programAPI.reorderPrograms(orderData);
      } else if (level === 1) {
        // Reorder lessons within a program
        const programId = typeof parentId === 'string' ? parseInt(parentId) : parentId;
        if (!programId) throw new Error('Program ID is required for lesson reorder');

        const program = programs.find((p) => p.id === programId);
        if (!program?.lessons) throw new Error('Program or lessons not found');

        const orderData = program.lessons
          .filter((l) => l.id !== undefined)
          .map((lesson, index) => ({
            id: lesson.id!,
            order_index: index === fromIndex ? toIndex : index === toIndex ? fromIndex : index,
          }));
        await programAPI.reorderLessons(programId, orderData);
      } else if (level === 2) {
        // Reorder contents within a lesson
        const lessonId = typeof parentId === 'string' ? parseInt(parentId) : parentId;
        if (!lessonId) throw new Error('Lesson ID is required for content reorder');

        const program = programs.find((p) => p.lessons?.some((l) => l.id === lessonId));
        const lesson = program?.lessons?.find((l) => l.id === lessonId);
        if (!lesson?.contents) throw new Error('Lesson or contents not found');

        const orderData = lesson.contents
          .filter((c) => c.id !== undefined)
          .map((content, index) => ({
            id: content.id!,
            order_index: index === fromIndex ? toIndex : index === toIndex ? fromIndex : index,
          }));
        await programAPI.reorderContents(lessonId, orderData);
      }

      // Refresh data after successful reorder
      if (onRefresh) {
        await onRefresh();
      }
      toast.success('順序已更新');
    } catch (error) {
      console.error('Reorder failed:', error);
      toast.error('更新順序失敗');
      // Rollback UI by refreshing
      if (onRefresh) {
        await onRefresh();
      }
    }
  };

  const handleContentClick = (item: TreeItem, level: number, parentId?: string | number) => {
    if (level === 2) {
      // Content level
      const content = item as Content;
      const numericParentId =
        typeof parentId === "string" ? parseInt(parentId) : parentId;
      const program = programs.find((p) =>
        p.lessons?.some((l) => l.id === numericParentId)
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
          example_sentence_translation: contentItem.example_sentence_translation,
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
    if (level === 2) {
      const numericParentId =
        typeof parentId === "string" ? parseInt(parentId) : parentId;
      const program = programs.find((p) =>
        p.lessons?.some((l) => l.id === numericParentId)
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

    if (onCreate) {
      onCreate(level, parentId);
    }
  };

  const readingPanelContent: {
    id?: number;
    title?: string;
    items?: ReadingPanelRow[];
  } | undefined = selectedContent
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

  return (
    <>
      <RecursiveTreeAccordion
        data={programs}
        config={programTreeConfig}
        showCreateButton={showCreateButton}
        createButtonText={createButtonText}
        onCreateClick={onCreateClick}
        onEdit={onEdit}
        onDelete={onDelete}
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
            <div className="flex-1 overflow-hidden flex flex-col">
              <div className="flex-1 overflow-auto p-6 min-h-0">
                <ReadingAssessmentPanel
                  lessonId={editorLessonId}
                  isCreating={true}
                  onSave={async (newContent?: Content) => {
                    if (newContent && editorLessonId) {
                      addContentToLesson(editorLessonId, newContent);
                    }
                    closeReadingEditor();
                    toast.success("內容已儲存");
                    if (onRefresh) onRefresh();
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
                <h2 className="text-xl font-semibold text-gray-900">編輯內容</h2>
                <button
                  onClick={closeReadingEditor}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              {/* Content */}
              <div className="flex-1 overflow-hidden flex flex-col">
                <div className="flex-1 overflow-auto p-6 min-h-0">
                  <ReadingAssessmentPanel
                    content={readingPanelContent}
                    lessonId={editorLessonId}
                    contentId={editorContentId}
                    isCreating={false}
                    onSave={async (updatedContent?: Content) => {
                      if (updatedContent && editorContentId) {
                        updateProgramContent(editorContentId, updatedContent);
                      }
                      closeReadingEditor();
                      toast.success("內容已儲存");
                      if (onRefresh) onRefresh();
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
              <div className="flex-1 overflow-hidden">
                <SentenceMakingPanel
                  content={undefined}
                  editingContent={{ id: sentenceMakingContentId || undefined }}
                  lessonId={sentenceMakingLessonId}
                  onSave={async (newContent?: Content) => {
                    if (newContent && sentenceMakingLessonId) {
                      addContentToLesson(sentenceMakingLessonId, newContent);
                    }
                    closeSentenceMakingEditor();
                    toast.success("內容已儲存");
                    if (onRefresh) onRefresh();
                  }}
                  onCancel={closeSentenceMakingEditor}
                  isCreating={true}
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
                <h2 className="text-xl font-semibold text-gray-900">編輯內容</h2>
                <button
                  onClick={closeSentenceMakingEditor}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              {/* Content */}
              <div className="flex-1 overflow-hidden flex flex-col">
                <div className="flex-1 overflow-auto p-6 min-h-0">
                  <SentenceMakingPanel
                    lessonId={sentenceMakingLessonId}
                    contentId={sentenceMakingContentId}
                    onSave={async () => {
                      closeSentenceMakingEditor();
                      toast.success("內容已儲存");
                      if (onRefresh) onRefresh();
                    }}
                    onCancel={closeSentenceMakingEditor}
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
              selection.type === "sentence_making" ||
              selection.type === "vocabulary_set" ||
              selection.type === "VOCABULARY_SET"
            ) {
              openSentenceMakingCreateEditor(selection.lessonId);
            } else {
              toast.info("此內容類型仍在開發中");
            }
          }}
        />
      )}
    </>
  );
}
