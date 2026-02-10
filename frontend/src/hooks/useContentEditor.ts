import { useState } from "react";
import { Content } from "@/types";

export function useContentEditor() {
  // Reading Assessment Editor
  const [showReadingEditor, setShowReadingEditor] = useState(false);
  const [editorLessonId, setEditorLessonId] = useState<number | null>(null);
  const [editorContentId, setEditorContentId] = useState<number | null>(null);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);

  // Sentence Making Editor
  const [showSentenceMakingEditor, setShowSentenceMakingEditor] =
    useState(false);
  const [sentenceMakingLessonId, setSentenceMakingLessonId] = useState<
    number | null
  >(null);
  const [sentenceMakingContentId, setSentenceMakingContentId] = useState<
    number | null
  >(null);

  // Vocabulary Set Editor
  const [showVocabularySetEditor, setShowVocabularySetEditor] = useState(false);
  const [vocabularySetLessonId, setVocabularySetLessonId] = useState<
    number | null
  >(null);
  const [vocabularySetContentId, setVocabularySetContentId] = useState<
    number | null
  >(null);

  const openContentEditor = (
    content: Content & {
      lessonName?: string;
      programName?: string;
      lesson_id?: number;
    },
  ) => {
    const contentType = content.type?.toLowerCase();

    if (
      contentType === "reading_assessment" ||
      contentType === "example_sentences"
    ) {
      setSelectedContent(content);
      setEditorLessonId(content.lesson_id || null);
      setEditorContentId(content.id);
      setShowReadingEditor(true);
    } else if (contentType === "sentence_making") {
      setSentenceMakingLessonId(content.lesson_id || null);
      setSentenceMakingContentId(content.id);
      setShowSentenceMakingEditor(true);
    } else if (contentType === "vocabulary_set") {
      setVocabularySetLessonId(content.lesson_id || null);
      setVocabularySetContentId(content.id);
      setShowVocabularySetEditor(true);
    }
  };

  const openReadingCreateEditor = (lessonId: number) => {
    setSelectedContent(null);
    setEditorLessonId(lessonId);
    setEditorContentId(null);
    setShowReadingEditor(true);
  };

  const openSentenceMakingCreateEditor = (lessonId: number) => {
    setSentenceMakingLessonId(lessonId);
    setSentenceMakingContentId(null);
    setShowSentenceMakingEditor(true);
  };

  const openVocabularySetCreateEditor = (lessonId: number) => {
    setVocabularySetLessonId(lessonId);
    setVocabularySetContentId(null);
    setShowVocabularySetEditor(true);
  };

  const closeReadingEditor = () => {
    setShowReadingEditor(false);
    setEditorLessonId(null);
    setEditorContentId(null);
    setSelectedContent(null);
  };

  const closeSentenceMakingEditor = () => {
    setShowSentenceMakingEditor(false);
    setSentenceMakingLessonId(null);
    setSentenceMakingContentId(null);
  };

  const closeVocabularySetEditor = () => {
    setShowVocabularySetEditor(false);
    setVocabularySetLessonId(null);
    setVocabularySetContentId(null);
  };

  return {
    // Reading Editor State
    showReadingEditor,
    editorLessonId,
    editorContentId,
    selectedContent,

    // Sentence Making Editor State
    showSentenceMakingEditor,
    sentenceMakingLessonId,
    sentenceMakingContentId,

    // Vocabulary Set Editor State
    showVocabularySetEditor,
    vocabularySetLessonId,
    vocabularySetContentId,

    // Actions
    openContentEditor,
    openReadingCreateEditor,
    openSentenceMakingCreateEditor,
    openVocabularySetCreateEditor,
    closeReadingEditor,
    closeSentenceMakingEditor,
    closeVocabularySetEditor,
  };
}
