import { useState, useRef, useEffect, memo } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import AIScoreDisplay from "@/components/shared/AIScoreDisplay";
import {
  Mic,
  Square,
  Volume2,
  Brain,
  Loader2,
  MessageSquare,
  Languages,
  X,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { retryAIAnalysis, retryAudioUpload } from "@/utils/retryHelper";

interface Question {
  text?: string;
  translation?: string;
  audio_url?: string;
  image_url?: string; // 新增圖片URL
  teacher_feedback?: string;
  teacher_passed?: boolean;
  teacher_review_score?: number;
  teacher_reviewed_at?: string;
  review_status?: string;
  [key: string]: unknown;
}

interface AssessmentResult {
  pronunciation_score?: number;
  accuracy_score?: number;
  fluency_score?: number;
  completeness_score?: number;
  overall_score?: number;
  prosody_score?: number;
  words?: Array<{
    accuracy_score?: number;
    word: string;
    error_type?: string;
  }>;
  word_details?: Array<{
    accuracy_score: number;
    word: string;
    error_type?: string;
  }>;
  detailed_words?: Array<{
    index: number;
    word: string;
    accuracy_score: number;
    error_type?: string;
    syllables?: Array<{
      index: number;
      syllable: string;
      accuracy_score: number;
    }>;
    phonemes?: Array<{
      index: number;
      phoneme: string;
      accuracy_score: number;
    }>;
  }>;
  reference_text?: string;
  recognized_text?: string;
  analysis_summary?: {
    total_words: number;
    problematic_words: string[];
    low_score_phonemes: Array<{
      phoneme: string;
      score: number;
      in_word: string;
    }>;
    assessment_time?: string;
  };
  error_type?: string;
}

type ItemAnalysisStatus =
  | "not_recorded"
  | "recorded"
  | "analyzing"
  | "analyzed"
  | "failed";

interface ItemAnalysisState {
  status: ItemAnalysisStatus;
  error?: string;
  retryCount?: number;
}

interface GroupedQuestionsTemplateProps {
  items: Question[];
  // answers?: string[]; // 目前未使用
  currentQuestionIndex?: number;
  isRecording?: boolean;
  recordingTime?: number;
  onStartRecording?: () => void;
  onStopRecording?: () => void;
  onUpdateItemRecording?: (index: number, recordingUrl: string) => void; // 更新單一 item 的錄音
  // onFileUpload?: (file: File) => void; // 🎯 Issue #74: Removed - no longer used after UI redesign
  formatTime?: (seconds: number) => string;
  progressId?: number | string;
  progressIds?: number[]; // 每個子問題的 progress_id 數組
  initialAssessmentResults?: Record<string, unknown>; // AI 評估結果
  readOnly?: boolean; // 唯讀模式
  assignmentId?: string; // 作業 ID，用於上傳錄音
  isPreviewMode?: boolean; // 預覽模式（老師端預覽）
  authToken?: string; // 認證 token（預覽模式用 teacher token）
  itemAnalysisState?: ItemAnalysisState; // 🎯 當前項目的分析狀態
  onUploadSuccess?: (index: number, gcsUrl: string, progressId: number) => void; // 上傳成功回調
  onAssessmentComplete?: (
    index: number,
    assessmentResult: AssessmentResult | null,
  ) => void; // AI 評估完成回調
  onAnalyzingStateChange?: (isAnalyzing: boolean) => void; // 🔒 分析狀態變化回調
}

const GroupedQuestionsTemplate = memo(function GroupedQuestionsTemplate({
  items,
  // answers = [], // 目前未使用
  currentQuestionIndex = 0,
  isRecording = false,
  recordingTime = 0,
  onStartRecording,
  onStopRecording,
  onUpdateItemRecording,
  // onFileUpload, // 🎯 Issue #74: Removed
  formatTime = (s) =>
    `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, "0")}`,
  progressId,
  progressIds = [], // 接收 progress_id 數組
  initialAssessmentResults,
  readOnly = false, // 唯讀模式
  assignmentId,
  isPreviewMode = false, // 預覽模式
  authToken, // 認證 token
  itemAnalysisState, // 🎯 當前項目的分析狀態
  onUploadSuccess,
  onAssessmentComplete,
  onAnalyzingStateChange, // 🔒 分析狀態變化回調
}: GroupedQuestionsTemplateProps) {
  const { t } = useTranslation();
  const currentQuestion = items[currentQuestionIndex];

  // 🎯 Issue #74: Removed unused playback state (moved to Zone D redesign)
  // const [isPlaying, setIsPlaying] = useState(false);
  // const [currentTime, setCurrentTime] = useState(0);
  // const [duration, setDuration] = useState(0);
  const [isAssessing, setIsAssessing] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0); // 播放倍速
  const questionAudioRef = useRef<HTMLAudioElement | null>(null); // 題目音檔播放器
  const [assessmentResults, setAssessmentResults] = useState<
    Record<number, AssessmentResult>
  >(() => {
    // 如果有初始 AI 評分，處理多題目的評分結構
    if (
      initialAssessmentResults &&
      Object.keys(initialAssessmentResults).length > 0
    ) {
      // 檢查是否有多題目的評分結構 (items)
      if (
        initialAssessmentResults.items &&
        typeof initialAssessmentResults.items === "object"
      ) {
        const itemsResults: Record<number, AssessmentResult> = {};
        const items = initialAssessmentResults.items as Record<string, unknown>;

        // 將 items 中的評分轉換為數字索引的結果
        Object.keys(items).forEach((key) => {
          const index = parseInt(key);
          if (!isNaN(index) && items[key]) {
            itemsResults[index] = items[key] as AssessmentResult;
          }
        });

        return itemsResults;
      }
      // 如果這是一個單獨的評分結果（不是分組的）
      else if (
        !Object.prototype.hasOwnProperty.call(initialAssessmentResults, "0")
      ) {
        return { 0: initialAssessmentResults as AssessmentResult };
      }
      return initialAssessmentResults as Record<number, AssessmentResult>;
    }
    return {};
  });
  // 🎯 Issue #74: Removed unused refs (audioRef, progressIntervalRef) after Zone D redesign
  const uploadButtonRef = useRef<HTMLButtonElement | null>(null);

  // 使用傳入的 token（預覽模式）或從 student store 取得（正常模式）
  const { token: studentToken } = useStudentAuthStore();
  const token = authToken || studentToken;

  // Update assessmentResults when initialAssessmentResults changes
  useEffect(() => {
    // 🔴 BUG FIX: 如果沒有 initialAssessmentResults，清空舊的評分結果
    if (
      !initialAssessmentResults ||
      Object.keys(initialAssessmentResults).length === 0
    ) {
      setAssessmentResults({});
      return;
    }

    // Check if it has items structure
    if (
      initialAssessmentResults.items &&
      typeof initialAssessmentResults.items === "object"
    ) {
      const itemsResults: Record<number, AssessmentResult> = {};
      const items = initialAssessmentResults.items as Record<string, unknown>;

      Object.keys(items).forEach((key) => {
        const index = parseInt(key);
        if (!isNaN(index) && items[key]) {
          itemsResults[index] = items[key] as AssessmentResult;
        }
      });

      setAssessmentResults(itemsResults);
    } else if (
      !Object.prototype.hasOwnProperty.call(initialAssessmentResults, "0")
    ) {
      setAssessmentResults({
        0: initialAssessmentResults as AssessmentResult,
      });
    } else {
      setAssessmentResults(
        initialAssessmentResults as Record<number, AssessmentResult>,
      );
    }
  }, [initialAssessmentResults]);

  // 手機版：錄音完成後自動滾動到上傳按鈕
  useEffect(() => {
    const hasRecording = items[currentQuestionIndex]?.recording_url;
    const hasNoAssessment = !assessmentResults[currentQuestionIndex];
    const isMobile = window.innerWidth < 640; // Tailwind sm breakpoint

    if (hasRecording && hasNoAssessment && !isAssessing && isMobile) {
      // 延遲一點時間確保按鈕已渲染
      setTimeout(() => {
        if (uploadButtonRef.current) {
          uploadButtonRef.current.scrollIntoView({
            behavior: "smooth",
            block: "center",
          });
        }
      }, 300);
    }
  }, [items, currentQuestionIndex, assessmentResults, isAssessing]);

  // 🎯 Issue #74: Removed togglePlayback - no longer needed after Zone D redesign

  // 更新播放速度
  const updatePlaybackRate = (newRate: number) => {
    setPlaybackRate(newRate);
    // 🎯 Issue #74: Updated to use questionAudioRef instead of removed audioRef
    if (questionAudioRef.current && !questionAudioRef.current.paused) {
      questionAudioRef.current.playbackRate = newRate;
    }
  };

  // 自動播放題目音檔
  useEffect(() => {
    // 清理之前的題目音檔
    if (questionAudioRef.current) {
      questionAudioRef.current.pause();
      questionAudioRef.current = null;
    }

    // 如果當前題目有音檔，自動播放
    const questionAudio = currentQuestion?.audio_url;
    if (questionAudio) {
      const audio = new Audio(questionAudio as string);
      audio.playbackRate = playbackRate;
      questionAudioRef.current = audio;

      // 播放音檔
      audio.play().catch((err) => {
        console.log(t("groupedQuestionsTemplate.messages.autoplayFailed"), err);
      });
    }

    // 清理函數
    return () => {
      if (questionAudioRef.current) {
        questionAudioRef.current.pause();
        questionAudioRef.current = null;
      }
    };
  }, [currentQuestionIndex, currentQuestion?.audio_url, playbackRate, t]);

  // 🎯 Issue #74: Removed formatAudioTime - no longer needed after Zone D redesign

  // AI 發音評估
  const handleAssessment = async () => {
    const audioUrl = items[currentQuestionIndex]?.recording_url;
    const referenceText = currentQuestion?.text;
    const contentItemId = items[currentQuestionIndex]?.id;

    if (!audioUrl || !referenceText) {
      toast.error(t("groupedQuestionsTemplate.messages.recordingRequired"));
      return;
    }

    if (!assignmentId || !contentItemId) {
      toast.error(t("groupedQuestionsTemplate.messages.missingInfo"));
      return;
    }

    setIsAssessing(true);
    onAnalyzingStateChange?.(true); // 🔒 通知父元件開始分析
    try {
      let gcsAudioUrl = audioUrl as string;
      let currentProgressId =
        progressIds && progressIds[currentQuestionIndex]
          ? progressIds[currentQuestionIndex]
          : null;

      // 🔍 檢查是否需要上傳（如果是 blob URL）
      // 預覽模式跳過上傳到資料庫
      if (
        typeof audioUrl === "string" &&
        audioUrl.startsWith("blob:") &&
        !isPreviewMode
      ) {
        toast.info(t("groupedQuestionsTemplate.messages.uploadingRecording"));

        // Convert blob URL to blob
        const response = await fetch(audioUrl as string);
        const audioBlob = await response.blob();

        // 上傳到 GCS
        const formData = new FormData();
        formData.append("assignment_id", assignmentId);
        formData.append("content_item_id", contentItemId.toString());
        // 根據 blob 的 MIME type 決定檔案副檔名
        const uploadFileExtension = audioBlob.type.includes("mp4")
          ? "recording.mp4"
          : audioBlob.type.includes("webm")
            ? "recording.webm"
            : "recording.audio";
        formData.append("audio_file", audioBlob, uploadFileExtension);

        const apiUrl = import.meta.env.VITE_API_URL || "";
        const uploadResult = await retryAudioUpload(
          async () => {
            const uploadResponse = await fetch(
              `${apiUrl}/api/students/upload-recording`,
              {
                method: "POST",
                headers: {
                  Authorization: `Bearer ${token}`,
                },
                body: formData,
              },
            );

            if (!uploadResponse.ok) {
              const error = new Error(
                `Upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`,
              );
              if (uploadResponse.status >= 500) {
                throw error;
              }
              throw Object.assign(error, { noRetry: true });
            }

            return await uploadResponse.json();
          },
          (attempt, error) => {
            console.log(
              t("groupedQuestionsTemplate.messages.uploadRetrying", {
                attempt,
              }),
              error,
            );
            toast.warning(
              t("groupedQuestionsTemplate.messages.uploadRetrying", {
                attempt,
              }),
            );
          },
        );

        gcsAudioUrl = uploadResult.audio_url;
        currentProgressId = uploadResult.progress_id;

        // 通知父元件上傳成功
        if (onUploadSuccess && currentProgressId) {
          onUploadSuccess(currentQuestionIndex, gcsAudioUrl, currentProgressId);
        }

        toast.success(t("groupedQuestionsTemplate.messages.uploadSuccess"));
      }

      // 🤖 開始 AI 分析
      toast.info(t("groupedQuestionsTemplate.messages.aiAnalyzing"));

      // Convert audio URL to blob for AI analysis
      const response = await fetch(
        isPreviewMode ? (audioUrl as string) : gcsAudioUrl,
      );
      const audioBlob = await response.blob();

      // Create form data
      const formData = new FormData();
      // 根據 blob 的 MIME type 決定檔案副檔名
      const fileExtension = audioBlob.type.includes("mp4")
        ? "recording.mp4"
        : audioBlob.type.includes("webm")
          ? "recording.webm"
          : "recording.audio";
      formData.append("audio_file", audioBlob, fileExtension);
      formData.append("reference_text", referenceText);

      // Get authentication token from store
      if (!token) {
        toast.error(t("groupedQuestionsTemplate.messages.relogin"));
        return;
      }

      const apiUrl = import.meta.env.VITE_API_URL || "";
      let result;

      // 預覽模式使用預覽 API，正常模式使用學生 API
      if (isPreviewMode) {
        // 預覽模式：使用老師的預覽 API，不需要 progress_id
        result = await retryAIAnalysis(
          async () => {
            const assessResponse = await fetch(
              `${apiUrl}/api/teachers/assignments/preview/assess-speech`,
              {
                method: "POST",
                headers: {
                  Authorization: `Bearer ${token}`,
                },
                body: formData,
              },
            );

            if (!assessResponse.ok) {
              const error = new Error(
                `AI Analysis failed: ${assessResponse.status} ${assessResponse.statusText}`,
              );
              if (
                assessResponse.status >= 500 ||
                assessResponse.status === 429
              ) {
                throw error;
              }
              throw Object.assign(error, { noRetry: true });
            }

            const data = await assessResponse.json();
            // 預覽 API 返回格式：{ success: true, preview_mode: true, assessment: {...} }
            return data.assessment;
          },
          (attempt, error) => {
            console.log(
              t("groupedQuestionsTemplate.messages.aiRetrying", { attempt }),
              error,
            );
            toast.warning(
              t("groupedQuestionsTemplate.messages.aiRetrying", { attempt }),
            );
          },
        );
      } else {
        // 正常模式：使用學生 API，需要 progress_id
        // 🔥 如果還沒有 progress_id，使用 fallback
        if (!currentProgressId) {
          currentProgressId = (progressId as number) || 1;
        }

        console.log("🔍 AI評估使用 progress_id:", {
          currentQuestionIndex,
          progressIds,
          progressId,
          currentProgressId,
        });

        formData.append("progress_id", String(currentProgressId));
        formData.append("item_index", String(currentQuestionIndex));
        // 🔥 加上 assignment_id 以便後端扣除配額
        if (assignmentId) {
          formData.append("assignment_id", String(assignmentId));
        }

        result = await retryAIAnalysis(
          async () => {
            const assessResponse = await fetch(`${apiUrl}/api/speech/assess`, {
              method: "POST",
              headers: {
                Authorization: `Bearer ${token}`,
              },
              body: formData,
            });

            if (!assessResponse.ok) {
              const error = new Error(
                `AI Analysis failed: ${assessResponse.status} ${assessResponse.statusText}`,
              );
              if (
                assessResponse.status >= 500 ||
                assessResponse.status === 429
              ) {
                throw error;
              }
              throw Object.assign(error, { noRetry: true });
            }

            return await assessResponse.json();
          },
          (attempt, error) => {
            console.log(
              t("groupedQuestionsTemplate.messages.aiRetrying", { attempt }),
              error,
            );
            toast.warning(
              t("groupedQuestionsTemplate.messages.aiRetrying", { attempt }),
            );
          },
        );
      }

      // 🔍 詳細記錄AI評估結果
      console.log("🎯 AI評估完整回應:", JSON.stringify(result, null, 2));
      console.log("🔍 詳細分析 - detailed_words:", result.detailed_words);
      console.log("🔍 basic word_details:", result.word_details);
      console.log(
        "🔍 有detailed_words嗎?",
        !!(result.detailed_words && result.detailed_words.length > 0),
      );

      if (result.detailed_words && result.detailed_words.length > 0) {
        result.detailed_words.forEach(
          (
            word: {
              word: string;
              syllables?: Array<{
                index: number;
                syllable: string;
                accuracy_score: number;
              }>;
              phonemes?: Array<{
                index: number;
                phoneme: string;
                accuracy_score: number;
              }>;
            },
            idx: number,
          ) => {
            console.log(`🔍 Word ${idx}:`, word.word);
            console.log(
              `   - syllables:`,
              word.syllables?.length || 0,
              word.syllables,
            );
            console.log(
              `   - phonemes:`,
              word.phonemes?.length || 0,
              word.phonemes,
            );
          },
        );
      }

      // Store result
      setAssessmentResults((prev) => ({
        ...prev,
        [currentQuestionIndex]: result,
      }));

      // Notify parent component about assessment completion
      if (onAssessmentComplete) {
        onAssessmentComplete(currentQuestionIndex, result);
      }

      toast.success(t("groupedQuestionsTemplate.messages.assessmentComplete"));
    } catch (error) {
      console.error("Assessment error:", error);
      toast.error(t("groupedQuestionsTemplate.messages.assessmentFailed"));
    } finally {
      setIsAssessing(false);
      onAnalyzingStateChange?.(false); // 🔓 通知父元件分析結束
    }
  };

  return (
    <div className="w-full">
      {/* 響應式佈局 - 手機垂直堆疊，桌面三欄式 */}
      <div className="flex flex-col sm:grid sm:grid-cols-12 gap-3 sm:gap-4 w-full">
        {/* 圖片區域 - 手機全寬，桌面3欄 */}
        {currentQuestion?.image_url && (
          <div className="w-full sm:col-span-3">
            <div className="w-full aspect-square rounded-lg overflow-hidden bg-gray-100">
              <img
                src={currentQuestion.image_url}
                alt={t("groupedQuestionsTemplate.labels.questionImage")}
                className="w-full h-full object-cover"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.parentElement!.innerHTML = `
                    <div class="w-full h-full flex items-center justify-center bg-gray-100">
                      <div class="text-center text-gray-400">
                        <svg class="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                        </svg>
                        <p class="text-sm">${t("groupedQuestionsTemplate.labels.imageLoadFailed")}</p>
                      </div>
                    </div>
                  `;
                }}
              />
            </div>
          </div>
        )}

        {/* 題目和學生作答區 - 手機全寬，桌面根據是否有圖片調整 */}
        <div
          className={`w-full ${currentQuestion?.image_url ? "sm:col-span-5" : "sm:col-span-6"} space-y-3`}
        >
          {/* 題目區域 - 更精簡版 */}
          <div className="bg-white rounded-lg border border-gray-200 p-3">
            {/* 題目文字與音檔 - 手機優化間距 */}
            <div className="flex items-center gap-2 sm:gap-3 mb-2">
              <button
                onClick={() => {
                  if (questionAudioRef.current) {
                    // 如果已有音檔，直接播放或暫停
                    if (questionAudioRef.current.paused) {
                      questionAudioRef.current.play();
                    } else {
                      questionAudioRef.current.pause();
                    }
                  } else if (currentQuestion?.audio_url) {
                    // 如果沒有音檔引用，創建新的
                    const audio = new Audio(currentQuestion.audio_url);
                    audio.playbackRate = playbackRate;
                    questionAudioRef.current = audio;
                    audio.play();
                  }
                }}
                disabled={!currentQuestion?.audio_url}
                className={`p-1.5 rounded-full transition-colors flex-shrink-0 ${
                  currentQuestion?.audio_url
                    ? "bg-green-100 hover:bg-green-200 text-green-600 cursor-pointer"
                    : "bg-gray-100 text-gray-400 cursor-not-allowed"
                }`}
                title={
                  currentQuestion?.audio_url ? "播放參考音檔" : "無參考音檔"
                }
              >
                <Volume2 className="w-4 h-4" />
              </button>

              {/* 🎯 Issue #74 Zone C: 題目文字 - 主文本顏色 #000000 */}
              <div className="text-base sm:text-lg font-medium text-[#000000] flex-1">
                {currentQuestion?.text ? (
                  <div className="flex flex-wrap gap-1">
                    {currentQuestion.text.split(" ").map((word, index) => (
                      <span
                        key={index}
                        className="cursor-pointer hover:text-blue-600 hover:underline transition-colors px-1"
                        onClick={() => {
                          // 使用 Web Speech API 發音
                          if ("speechSynthesis" in window) {
                            // 取消之前的發音
                            window.speechSynthesis.cancel();

                            const utterance = new SpeechSynthesisUtterance(
                              word,
                            );
                            utterance.lang = "en-US"; // 設定為英文發音
                            utterance.rate = 1.0; // 正常速度
                            utterance.pitch = 1.0; // 正常音調
                            utterance.volume = 1.0; // 最大音量

                            window.speechSynthesis.speak(utterance);
                          }
                        }}
                        title={`${t("groupedQuestionsTemplate.labels.clickToPronounciate")}: ${word}`}
                      >
                        {word}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-gray-400 italic">
                    {t("groupedQuestionsTemplate.labels.noQuestionText")}
                  </span>
                )}
              </div>

              {/* 倍速控制 */}
              <select
                value={playbackRate}
                onChange={(e) => updatePlaybackRate(parseFloat(e.target.value))}
                className="text-xs border border-gray-300 rounded px-1 py-0.5 bg-white"
                title={t("groupedQuestionsTemplate.labels.playbackSpeed")}
              >
                <option value={0.5}>0.5x</option>
                <option value={0.75}>0.75x</option>
                <option value={1.0}>1.0x</option>
                <option value={1.25}>1.25x</option>
                <option value={1.5}>1.5x</option>
                <option value={2.0}>2.0x</option>
              </select>
            </div>

            {/* 🎯 Issue #74 Zone C: 翻譯文本顏色 #545454 */}
            {currentQuestion?.translation && (
              <div className="flex items-center gap-2 text-sm sm:text-base text-[#545454] bg-gray-50 rounded px-2 sm:px-3 py-1.5 sm:py-2">
                <Languages className="w-4 h-4" />
                <span>{currentQuestion.translation}</span>
              </div>
            )}
          </div>

          {/* 🎯 Issue #74 Zone D: 學生錄音區 - 重新設計 */}
          <div className="bg-[#f0f0f0] rounded-t-lg p-4">
            <div className="text-sm sm:text-base font-medium text-gray-700 mb-3">
              {t("groupedQuestionsTemplate.labels.studentAnswer")}
            </div>

            {/* 🎯 Issue #74: 錄音控制區 - 左側錄音按鈕 + 右側播放控制 */}
            <div className="flex items-center gap-4">
              {/* 左側: 錄音控制按鈕 (重疊邏輯) */}
              <div className="flex items-center gap-2">
                {!isRecording && !items[currentQuestionIndex]?.recording_url ? (
                  // 錄音按鈕 (初始狀態)
                  <button
                    className="w-16 h-16 rounded-full bg-gradient-to-br from-[#cdffd8] to-[#94b9ff] flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transition-all"
                    disabled={readOnly}
                    onClick={() => {
                      setAssessmentResults((prev) => {
                        const newResults = { ...prev };
                        delete newResults[currentQuestionIndex];
                        return newResults;
                      });
                      onStartRecording?.();
                    }}
                    title={
                      readOnly
                        ? t("groupedQuestionsTemplate.labels.viewOnlyMode")
                        : t("groupedQuestionsTemplate.labels.startRecording")
                    }
                  >
                    <Mic className="w-7 h-7 text-[#545454]" />
                  </button>
                ) : isRecording ? (
                  // 停止按鈕 (錄音中)
                  <button
                    className="w-16 h-16 rounded-full bg-gradient-to-br from-[#cdffd8] to-[#94b9ff] flex items-center justify-center shadow-lg hover:shadow-xl transition-all"
                    onClick={onStopRecording}
                    title={t("groupedQuestionsTemplate.labels.stopping")}
                  >
                    <Square
                      className="w-7 h-7 text-[#ff3131]"
                      fill="currentColor"
                    />
                  </button>
                ) : items[currentQuestionIndex]?.recording_url ? (
                  // 重置按鈕 (有錄音)
                  <button
                    className="w-16 h-16 rounded-full bg-gradient-to-br from-[#cdffd8] to-[#94b9ff] flex items-center justify-center shadow-lg hover:shadow-xl transition-all"
                    onClick={async () => {
                      // 🎯 Issue #75: 呼叫後端 DELETE API 清空 DB (僅在非預覽模式)
                      if (
                        !isPreviewMode &&
                        assignmentId &&
                        currentQuestionIndex !== undefined
                      ) {
                        try {
                          const apiUrl = import.meta.env.VITE_API_URL || "";
                          const token = useStudentAuthStore.getState().token;

                          const response = await fetch(
                            `${apiUrl}/api/speech/assessment/${assignmentId}/item/${currentQuestionIndex}`,
                            {
                              method: "DELETE",
                              headers: {
                                Authorization: `Bearer ${token}`,
                                "Content-Type": "application/json",
                              },
                            },
                          );

                          if (!response.ok) {
                            throw new Error(`HTTP ${response.status}`);
                          }

                          toast.success(
                            t(
                              "groupedQuestionsTemplate.messages.deletionSuccess",
                            ),
                          );
                        } catch (error) {
                          console.error("刪除 DB 記錄失敗:", error);
                          // 🎯 測試環境下不報錯，允許繼續清除前端狀態
                          if (!import.meta.env.VITE_TEST_MODE) {
                            toast.error(
                              t(
                                "groupedQuestionsTemplate.messages.deletionFailed",
                              ),
                            );
                          }
                          // 繼續執行前端清除（測試環境需要）
                        }
                      }

                      // 清除前端狀態 - 必須創建新物件才能觸發重新渲染
                      setAssessmentResults((prev) => {
                        // Remove the key using destructuring
                        // eslint-disable-next-line @typescript-eslint/no-unused-vars
                        const { [currentQuestionIndex]: _, ...newResults } =
                          prev;
                        return newResults;
                      });

                      // 清空 items 中的 recording_url，觸發學生作答區塊 reset
                      if (
                        onUpdateItemRecording &&
                        currentQuestionIndex !== undefined
                      ) {
                        onUpdateItemRecording(currentQuestionIndex, "");
                      }

                      // 也要清空 items 的 ai_assessment，確保重新整理後不會殘留
                      if (
                        onAssessmentComplete &&
                        currentQuestionIndex !== undefined
                      ) {
                        onAssessmentComplete(currentQuestionIndex, null);
                      }
                    }}
                    title={t("groupedQuestionsTemplate.labels.clearRecording")}
                  >
                    <svg
                      className="w-7 h-7 text-[#545454]"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                  </button>
                ) : null}

                {/* 錄音時間顯示 */}
                {isRecording && (
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse" />
                    <span className="text-base font-medium text-red-600">
                      {formatTime(recordingTime)} / 0:45
                    </span>
                  </div>
                )}
              </div>

              {/* 右側: 題目音檔播放控制 */}
              {currentQuestion?.audio_url && (
                <div className="flex-1 flex items-center gap-2 bg-[#273755] rounded-lg px-3 py-2">
                  <button
                    onClick={() => {
                      if (questionAudioRef.current) {
                        // 如果已有音檔，直接播放或暫停
                        if (questionAudioRef.current.paused) {
                          questionAudioRef.current.play();
                        } else {
                          questionAudioRef.current.pause();
                        }
                      } else if (currentQuestion?.audio_url) {
                        // 如果沒有音檔引用，創建新的
                        const audio = new Audio(currentQuestion.audio_url);
                        audio.playbackRate = playbackRate;
                        questionAudioRef.current = audio;
                        audio.play();
                      }
                    }}
                    className="w-8 h-8 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center text-white flex-shrink-0 transition-colors"
                  >
                    <Volume2 className="w-4 h-4" />
                  </button>
                  <select
                    value={playbackRate}
                    onChange={(e) =>
                      updatePlaybackRate(parseFloat(e.target.value))
                    }
                    className="text-xs bg-white/10 text-white border-none rounded px-2 py-1"
                  >
                    <option value={0.5} className="text-gray-900">
                      0.5x
                    </option>
                    <option value={0.75} className="text-gray-900">
                      0.75x
                    </option>
                    <option value={1.0} className="text-gray-900">
                      1.0x
                    </option>
                    <option value={1.5} className="text-gray-900">
                      1.5x
                    </option>
                    <option value={2.0} className="text-gray-900">
                      2.0x
                    </option>
                  </select>
                </div>
              )}
            </div>
          </div>

          {/* 老師評語 - 始終顯示，無評語時禁用狀態 */}
          {
            <div
              className={`rounded-lg border-2 p-3 ${
                currentQuestion?.teacher_feedback
                  ? currentQuestion.teacher_passed === true
                    ? "border-green-400 bg-green-50"
                    : currentQuestion.teacher_passed === false
                      ? "border-red-400 bg-red-50"
                      : "border-blue-400 bg-blue-50"
                  : "border-gray-200 bg-gray-50 opacity-50"
              }`}
            >
              <div
                className={`text-sm sm:text-base font-medium mb-1 flex items-center gap-1 ${
                  currentQuestion?.teacher_feedback
                    ? currentQuestion.teacher_passed === true
                      ? "text-green-600"
                      : currentQuestion.teacher_passed === false
                        ? "text-red-600"
                        : "text-blue-600"
                    : "text-gray-400"
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                {t("groupedQuestionsTemplate.labels.teacherFeedback")}
                {currentQuestion?.teacher_feedback &&
                  currentQuestion.teacher_passed !== null &&
                  currentQuestion.teacher_passed !== undefined && (
                    <span
                      className={
                        currentQuestion.teacher_passed
                          ? "text-green-600"
                          : "text-red-600"
                      }
                    >
                      {currentQuestion.teacher_passed
                        ? t("groupedQuestionsTemplate.labels.passed")
                        : t("groupedQuestionsTemplate.labels.notPassed")}
                    </span>
                  )}
              </div>
              <div className="text-sm sm:text-base text-gray-700">
                {currentQuestion?.teacher_feedback || (
                  <span className="text-gray-400">
                    {t("groupedQuestionsTemplate.labels.noTeacherFeedback")}
                  </span>
                )}
              </div>
              {currentQuestion?.teacher_reviewed_at && (
                <div className="text-sm text-gray-500 mt-1">
                  {new Date(currentQuestion.teacher_reviewed_at).toLocaleString(
                    "zh-TW",
                  )}
                </div>
              )}
            </div>
          }
        </div>

        {/* AI分析 - 手機全寬，桌面根據是否有圖片調整 */}
        <div
          className={`w-full ${currentQuestion?.image_url ? "sm:col-span-4" : "sm:col-span-6"} space-y-4`}
        >
          {/* AI 評估結果 */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            {/* 🎯 Issue #74 Zone C-1: 分析按鈕 + Issue #75: 只為 GCS URL 顯示 (不為 blob URL 顯示) */}
            {items[currentQuestionIndex]?.recording_url &&
            !assessmentResults[currentQuestionIndex] &&
            !(items[currentQuestionIndex]?.recording_url as string).startsWith(
              "blob:",
            ) ? (
              <div className="flex justify-center mb-4 py-6">
                <Button
                  ref={uploadButtonRef}
                  size="lg"
                  onClick={handleAssessment}
                  disabled={
                    isAssessing || itemAnalysisState?.status === "analyzing"
                  }
                  className={`relative h-16 px-10 text-xl font-bold rounded-2xl shadow-2xl transition-all ${
                    itemAnalysisState?.status === "analyzing"
                      ? "bg-[#5e17eb] cursor-not-allowed opacity-70"
                      : itemAnalysisState?.status === "analyzed"
                        ? "bg-green-600 hover:bg-green-700 cursor-not-allowed"
                        : itemAnalysisState?.status === "failed"
                          ? "bg-red-600 hover:bg-red-700"
                          : "bg-[#5e17eb] hover:bg-[#5e17eb]/90 text-white"
                  }`}
                  style={{
                    animation:
                      isAssessing || itemAnalysisState?.status === "analyzing"
                        ? "none"
                        : "pulse-scale 1.5s ease-in-out infinite",
                  }}
                >
                  {itemAnalysisState?.status === "analyzing" ? (
                    <>
                      <Loader2 className="w-7 h-7 mr-3 animate-spin" />
                      {t("groupedQuestionsTemplate.labels.analyzing")}
                    </>
                  ) : itemAnalysisState?.status === "analyzed" ? (
                    <>
                      <CheckCircle2 className="w-7 h-7 mr-3" />
                      {t("groupedQuestionsTemplate.labels.analyzed")}
                    </>
                  ) : itemAnalysisState?.status === "failed" ? (
                    <>
                      <XCircle className="w-7 h-7 mr-3" />
                      {t("groupedQuestionsTemplate.labels.analysisFailed")}
                    </>
                  ) : isAssessing ? (
                    <>
                      <Loader2 className="w-7 h-7 mr-3 animate-spin" />
                      {t("groupedQuestionsTemplate.labels.analyzing")}
                    </>
                  ) : (
                    <>
                      <Brain className="w-7 h-7 mr-3 animate-pulse" />
                      {t("groupedQuestionsTemplate.labels.uploadAndAnalyze")}
                    </>
                  )}
                </Button>
                <style
                  dangerouslySetInnerHTML={{
                    __html: `
                    @keyframes pulse-scale {
                      0%, 100% {
                        transform: scale(1);
                      }
                      50% {
                        transform: scale(1.08);
                      }
                    }
                  `,
                  }}
                />
              </div>
            ) : null}
            {assessmentResults[currentQuestionIndex] ? (
              <div className="relative">
                {/* 評估結果 - 在分析時會被模糊 */}
                <div
                  className={`transition-all duration-300 ${isAssessing ? "blur-sm opacity-30" : ""}`}
                >
                  <button
                    onClick={async () => {
                      // 🎯 Issue #75: 呼叫後端 DELETE API 清空 DB (僅在非預覽模式)
                      if (
                        !isPreviewMode &&
                        assignmentId &&
                        currentQuestionIndex !== undefined
                      ) {
                        try {
                          const apiUrl = import.meta.env.VITE_API_URL || "";
                          const token = useStudentAuthStore.getState().token;

                          const response = await fetch(
                            `${apiUrl}/api/speech/assessment/${assignmentId}/item/${currentQuestionIndex}`,
                            {
                              method: "DELETE",
                              headers: {
                                Authorization: `Bearer ${token}`,
                                "Content-Type": "application/json",
                              },
                            },
                          );

                          if (!response.ok) {
                            throw new Error(`HTTP ${response.status}`);
                          }

                          toast.success(
                            t(
                              "groupedQuestionsTemplate.messages.deletionSuccess",
                            ),
                          );
                        } catch (error) {
                          console.error("刪除 DB 記錄失敗:", error);
                          // 🎯 測試環境下不報錯，允許繼續清除前端狀態
                          if (!import.meta.env.VITE_TEST_MODE) {
                            toast.error(
                              t(
                                "groupedQuestionsTemplate.messages.deletionFailed",
                              ),
                            );
                          }
                          // 繼續執行前端清除（測試環境需要）
                        }
                      }

                      // 清除前端狀態 - 必須創建新物件才能觸發重新渲染
                      setAssessmentResults((prev) => {
                        // Remove the key using destructuring
                        // eslint-disable-next-line @typescript-eslint/no-unused-vars
                        const { [currentQuestionIndex]: _, ...newResults } =
                          prev;
                        return newResults;
                      });

                      // 清空 items 中的 recording_url，觸發學生作答區塊 reset
                      if (
                        onUpdateItemRecording &&
                        currentQuestionIndex !== undefined
                      ) {
                        onUpdateItemRecording(currentQuestionIndex, "");
                      }

                      // 也要清空 items 的 ai_assessment，確保重新整理後不會殘留
                      if (
                        onAssessmentComplete &&
                        currentQuestionIndex !== undefined
                      ) {
                        onAssessmentComplete(currentQuestionIndex, null);
                      }
                    }}
                    className="absolute top-0 right-0 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors z-10"
                    title={t("groupedQuestionsTemplate.labels.deleteRecording")}
                    disabled={isAssessing}
                  >
                    <X className="w-4 h-4" />
                  </button>

                  {/* 🎯 Issue #74 Zone C-1: 星級評分顯示 */}
                  {(() => {
                    const result = assessmentResults[currentQuestionIndex];
                    // 計算平均分數
                    const scores = [
                      result?.pronunciation_score,
                      result?.accuracy_score,
                      result?.fluency_score,
                      result?.completeness_score,
                    ].filter(
                      (score): score is number => typeof score === "number",
                    );

                    const averageScore =
                      scores.length > 0
                        ? scores.reduce((sum, score) => sum + score, 0) /
                          scores.length
                        : 0;

                    // 根據平均分數確定星星數量
                    let filledStars = 0;
                    let emptyStars = 3;

                    if (averageScore > 90) {
                      filledStars = 3;
                      emptyStars = 0;
                    } else if (averageScore >= 60) {
                      filledStars = 2;
                      emptyStars = 1;
                    } else if (averageScore >= 40) {
                      filledStars = 1;
                      emptyStars = 2;
                    } else {
                      filledStars = 0;
                      emptyStars = 3;
                    }

                    return (
                      <div className="flex items-center justify-center gap-1 mb-4">
                        {[...Array(filledStars)].map((_, i) => (
                          <svg
                            key={`filled-${i}`}
                            className="w-8 h-8 text-yellow-400"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        ))}
                        {[...Array(emptyStars)].map((_, i) => (
                          <svg
                            key={`empty-${i}`}
                            className="w-8 h-8 text-gray-300"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        ))}
                        <span className="ml-2 text-sm font-medium text-gray-600">
                          ({averageScore.toFixed(0)}分)
                        </span>
                      </div>
                    );
                  })()}

                  <AIScoreDisplay
                    key={`assessment-${currentQuestionIndex}`}
                    scores={assessmentResults[currentQuestionIndex]}
                    hasRecording={true}
                    title=""
                  />
                </div>

                {/* 思考動畫覆蓋層 - 在分析時顯示在最上層 */}
                {isAssessing && (
                  <div className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm z-20 rounded-lg">
                    <div className="text-center text-purple-500">
                      <div className="relative w-16 h-16 mx-auto mb-4">
                        {/* 外圈脈動動畫 */}
                        <div className="absolute inset-0 rounded-full bg-purple-100 animate-ping opacity-75"></div>
                        {/* 中圈脈動動畫 */}
                        <div className="absolute inset-2 rounded-full bg-purple-200 animate-pulse"></div>
                        {/* 大腦圖示 - 旋轉動畫 */}
                        <Brain
                          className="w-16 h-16 absolute inset-0 animate-spin"
                          style={{ animationDuration: "3s" }}
                        />
                      </div>
                      <p className="text-base font-medium text-purple-600 animate-pulse">
                        {t("groupedQuestionsTemplate.labels.aiAnalyzing")}
                      </p>
                      <p className="text-xs text-purple-400 mt-1">
                        {t("groupedQuestionsTemplate.labels.pleaseWait")}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : isAssessing ? (
              <div className="text-center text-purple-500 py-8">
                <div className="relative w-16 h-16 mx-auto mb-4">
                  {/* 外圈脈動動畫 */}
                  <div className="absolute inset-0 rounded-full bg-purple-100 animate-ping opacity-75"></div>
                  {/* 中圈脈動動畫 */}
                  <div className="absolute inset-2 rounded-full bg-purple-200 animate-pulse"></div>
                  {/* 大腦圖示 - 旋轉動畫 */}
                  <Brain
                    className="w-16 h-16 absolute inset-0 animate-spin"
                    style={{ animationDuration: "3s" }}
                  />
                </div>
                <p className="text-base font-medium text-purple-600 animate-pulse">
                  {t("groupedQuestionsTemplate.labels.aiAnalyzing")}
                </p>
                <p className="text-xs text-purple-400 mt-1">
                  {t("groupedQuestionsTemplate.labels.pleaseWait")}
                </p>
              </div>
            ) : (
              <div className="text-center text-gray-400 py-8">
                <Brain className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  {items[currentQuestionIndex]?.recording_url
                    ? t("groupedQuestionsTemplate.labels.clickToAssess")
                    : t("groupedQuestionsTemplate.labels.pleaseRecordFirst")}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});

export default GroupedQuestionsTemplate;
