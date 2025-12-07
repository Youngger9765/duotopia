/**
 * 學生作業活動內容元件（可重用）
 *
 * 此元件包含完整的學生作業活動介面，可被以下場景使用：
 * 1. 學生作業頁面 (StudentActivityPage)
 * 2. 老師預覽示範頁面 (TeacherAssignmentPreviewPage)
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import ReadingAssessmentTemplate from "@/components/activities/ReadingAssessmentTemplate";
import ListeningClozeTemplate from "@/components/activities/ListeningClozeTemplate";
import GroupedQuestionsTemplate from "@/components/activities/GroupedQuestionsTemplate";
import {
  ChevronLeft,
  ChevronRight,
  Send,
  CheckCircle,
  Circle,
  Clock,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getRecordingStrategy,
  selectSupportedMimeType,
  validateDuration,
} from "@/utils/audioRecordingStrategy";
import { retryAudioUpload, retryAIAnalysis } from "@/utils/retryHelper";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { useTranslation } from "react-i18next";

// Activity type from API
export interface Activity {
  id: number;
  content_id: number;
  order: number;
  type: string;
  title: string;
  content: string;
  target_text: string;
  duration: number;
  points: number;
  status: string;
  score: number | null;
  audio_url?: string | null;
  completed_at: string | null;
  items?: Array<{
    id?: number;
    text?: string;
    translation?: string;
    audio_url?: string;
    recording_url?: string;
    progress_id?: number;
    ai_assessment?: {
      accuracy_score?: number;
      fluency_score?: number;
      completeness_score?: number;
      pronunciation_score?: number;
      prosody_score?: number;
      word_details?: Array<{
        word: string;
        accuracy_score: number;
        error_type?: string;
      }>;
      detailed_words?: unknown[];
      reference_text?: string;
      recognized_text?: string;
      analysis_summary?: unknown;
    };
    [key: string]: unknown;
  }>;
  item_count?: number;
  answers?: string[];
  blanks?: string[];
  prompts?: string[];
  example_audio_url?: string;
  ai_scores?: {
    accuracy_score?: number;
    fluency_score?: number;
    completeness_score?: number;
    pronunciation_score?: number;
    word_details?: Array<{
      word: string;
      accuracy_score: number;
      error_type?: string;
    }>;
    items?: Record<
      number,
      {
        accuracy_score?: number;
        fluency_score?: number;
        completeness_score?: number;
        pronunciation_score?: number;
        prosody_score?: number;
        word_details?: Array<{
          word: string;
          accuracy_score: number;
          error_type?: string;
        }>;
        detailed_words?: unknown[];
        reference_text?: string;
        recognized_text?: string;
        analysis_summary?: unknown;
      }
    >;
  };
}

interface Answer {
  progressId: number;
  progressIds?: number[];
  audioBlob?: Blob;
  audioUrl?: string;
  textAnswer?: string;
  userAnswers?: string[];
  answers?: string[];
  startTime: Date;
  endTime?: Date;
  status: "not_started" | "in_progress" | "completed";
}

interface StudentActivityPageContentProps {
  activities: Activity[];
  assignmentTitle: string;
  assignmentId: number;
  isPreviewMode?: boolean;
  authToken?: string; // 認證 token（預覽模式用）
  onBack?: () => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSubmit?: (data: { answers: any[] }) => Promise<void>;
  assignmentStatus?: string;
}

export default function StudentActivityPageContent({
  activities: initialActivities,
  assignmentTitle,
  assignmentId,
  isPreviewMode = false,
  authToken,
  onBack,
  onSubmit,
  assignmentStatus = "",
}: StudentActivityPageContentProps) {
  const { t } = useTranslation();

  // State management
  const [activities, setActivities] = useState<Activity[]>(initialActivities);
  const [currentActivityIndex, setCurrentActivityIndex] = useState(0);
  const [currentSubQuestionIndex, setCurrentSubQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Map<number, Answer>>(new Map());
  const [saving] = useState(false);
  const [submitting] = useState(false);
  const [showSubmitDialog, setShowSubmitDialog] = useState(false);
  const [incompleteItems, setIncompleteItems] = useState<string[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false); // 🔒 錄音分析中狀態

  // 🎯 背景分析狀態管理
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

  const [itemAnalysisStates, setItemAnalysisStates] = useState<
    Map<string, ItemAnalysisState>
  >(new Map());
  const [pendingAnalysisCount, setPendingAnalysisCount] = useState(0); // 🔒 追蹤背景分析數量以觸發 UI 更新
  const pendingAnalysisRef = useRef<Map<string, Promise<void>>>(new Map());
  const failedItemsRef = useRef<Set<string>>(new Set());

  // Read-only mode (for submitted/graded assignments)
  // Note: isPreviewMode is NOT read-only - it allows all operations but doesn't save to DB
  const isReadOnly =
    assignmentStatus === "SUBMITTED" || assignmentStatus === "GRADED";

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null,
  );
  const recordingInterval = useRef<NodeJS.Timeout | null>(null);
  const recordingTimeRef = useRef<number>(0);
  const hasRecordedData = useRef<boolean>(false);
  const isReRecording = useRef<boolean>(false);
  const streamRef = useRef<MediaStream | null>(null); // 🔧 追蹤 MediaStream 以便清理

  // Initialize answers
  useEffect(() => {
    const initialAnswers = new Map<number, Answer>();
    initialActivities.forEach((activity) => {
      let audioUrl: string | undefined = undefined;
      if (activity.type === "reading_assessment" && activity.items?.[0]) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        audioUrl = (activity.items[0] as any).recording_url || "";
      }

      initialAnswers.set(activity.id, {
        progressId: activity.id,
        status:
          activity.status === "NOT_STARTED"
            ? "not_started"
            : activity.status === "IN_PROGRESS"
              ? "in_progress"
              : "completed",
        startTime: new Date(),
        audioUrl: audioUrl,
        answers: activity.answers || [],
        userAnswers: [],
      });
    });
    setAnswers(initialAnswers);
  }, [initialActivities]);

  // Scroll to top when switching questions
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [currentActivityIndex, currentSubQuestionIndex]);

  // 🎯 使用統一的錄音策略
  const strategyRef = useRef(getRecordingStrategy());

  // 🔧 清理錄音資源（避免重用舊的 MediaRecorder 和 Stream）
  const cleanupRecording = () => {
    // 停止舊的 MediaRecorder
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      console.log("🧹 Stopping old MediaRecorder");
      mediaRecorder.stop();
    }
    setMediaRecorder(null);

    // 停止舊的 MediaStream
    if (streamRef.current) {
      console.log("🧹 Stopping old MediaStream tracks");
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    // 清理 timer
    if (recordingInterval.current) {
      clearInterval(recordingInterval.current);
      recordingInterval.current = null;
    }

    setIsRecording(false);
  };

  const startRecording = async (isReRecord: boolean = false) => {
    if (isReadOnly) {
      toast.warning(
        isPreviewMode
          ? t("studentActivityPage.warnings.previewNoRecord")
          : t("studentActivityPage.warnings.readonlyNoRecord"),
      );
      return;
    }

    isReRecording.current = isReRecord;

    try {
      // 🔧 先清理舊的錄音資源（關鍵！避免重用壞掉的 recorder）
      cleanupRecording();

      const currentActivity = activities[currentActivityIndex];

      // Clear previous recording and AI scores for grouped questions
      if (currentActivity.items && currentActivity.items.length > 0) {
        setActivities((prevActivities) => {
          const newActivities = [...prevActivities];
          const activityIndex = newActivities.findIndex(
            (a) => a.id === currentActivity.id,
          );
          if (activityIndex !== -1 && newActivities[activityIndex].items) {
            const newItems = [...newActivities[activityIndex].items!];
            if (newItems[currentSubQuestionIndex]) {
              newItems[currentSubQuestionIndex] = {
                ...newItems[currentSubQuestionIndex],
                recording_url: "",
              };
            }
            newActivities[activityIndex] = {
              ...newActivities[activityIndex],
              items: newItems,
              ai_scores: undefined,
            };
          }
          return newActivities;
        });
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream; // 🔧 儲存 stream reference

      // 🎯 使用統一錄音策略選擇 MIME type
      const strategy = strategyRef.current;
      const mimeType = selectSupportedMimeType(strategy);
      const options = mimeType ? { mimeType } : {};
      const recorder = new MediaRecorder(stream, options);
      const chunks: Blob[] = [];

      console.log(
        `🎙️ MediaRecorder initialized with MIME type: ${recorder.mimeType} (platform: ${strategy.platformName})`,
      );

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
          hasRecordedData.current = true;
          console.log("✅ Audio data collected");
        }
      };

      recorder.onstop = async () => {
        const actualRecordingDuration = recordingTimeRef.current;
        console.log("🎙️ 實際錄音時長:", actualRecordingDuration, "秒");

        await new Promise((resolve) => setTimeout(resolve, 800)); // 500→800ms

        const audioBlob = new Blob(chunks, {
          type: recorder.mimeType || "audio/webm",
        });
        const currentActivity = activities[currentActivityIndex];

        console.log("🎤 Recording completed:", {
          size: audioBlob.size,
          type: audioBlob.type,
          hasData: hasRecordedData.current,
          chunksCount: chunks.length,
        });

        // 🎯 使用統一驗證策略
        const strategy = strategyRef.current;
        const localAudioUrl = URL.createObjectURL(audioBlob);

        // 🔍 雙重檢查：chunks 和 blob 都太小才報錯
        const chunksSize = chunks.reduce((sum, chunk) => sum + chunk.size, 0);
        const blobSize = audioBlob.size;

        if (
          chunksSize < strategy.minFileSize &&
          blobSize < strategy.minFileSize
        ) {
          console.error(
            `⚠️ Recording file too small (both checks failed): chunks=${chunksSize}B, blob=${blobSize}B, min=${strategy.minFileSize}B`,
          );

          const { logAudioError } = await import("@/utils/audioErrorLogger");
          await logAudioError({
            errorType: "recording_too_small",
            audioUrl: localAudioUrl,
            audioSize: blobSize,
            audioDuration: actualRecordingDuration,
            contentType: audioBlob.type,
            assignmentId: assignmentId,
            errorMessage: `Both chunks (${chunksSize}B) and blob (${blobSize}B) below minimum ${strategy.minFileSize}B`,
          });

          toast.error(t("studentActivityPage.recording.failed"), {
            description: t("studentActivityPage.recording.fileAbnormal"),
          });

          // 🔧 清理所有錄音狀態
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          setMediaRecorder(null);
          setIsRecording(false);
          setRecordingTime(0);
          return;
        }

        // ✅ 至少一個通過 - 記錄診斷資訊
        console.log(
          `✅ Recording size check passed: chunks=${chunksSize}B, blob=${blobSize}B (min: ${strategy.minFileSize}B)`,
        );

        // 使用策略驗證 duration
        try {
          const validationResult = await validateDuration(
            audioBlob,
            localAudioUrl,
            strategy,
          );

          if (!validationResult.valid) {
            console.error("⚠️ Recording validation failed");

            const { logAudioError } = await import("@/utils/audioErrorLogger");
            await logAudioError({
              errorType: "recording_validation_failed",
              audioUrl: localAudioUrl,
              audioSize: audioBlob.size,
              audioDuration: validationResult.duration,
              contentType: audioBlob.type,
              assignmentId: assignmentId,
              errorMessage: `Validation failed (method: ${validationResult.method})`,
            });

            toast.error(t("studentActivityPage.recording.validationFailed"), {
              description: t("studentActivityPage.recording.fileAbnormal"),
            });

            // 🔧 清理 stream
            if (streamRef.current) {
              streamRef.current.getTracks().forEach((track) => track.stop());
              streamRef.current = null;
            }
            return;
          }

          console.log(
            `✅ Recording validation passed (${validationResult.method}): ${validationResult.duration.toFixed(1)}s`,
          );

          if (!isPreviewMode) {
            toast.success(t("studentActivityPage.recording.complete"), {
              description: t("studentActivityPage.recording.duration", {
                duration: validationResult.duration.toFixed(1),
              }),
            });
          } else {
            toast.success(t("studentActivityPage.recording.completePreview"), {
              description: t("studentActivityPage.recording.duration", {
                duration: validationResult.duration.toFixed(1),
              }),
            });
          }
        } catch (error) {
          console.error("⚠️ Recording validation error:", error);

          const { logAudioError } = await import("@/utils/audioErrorLogger");
          await logAudioError({
            errorType: "recording_validation_error",
            audioUrl: localAudioUrl,
            audioSize: audioBlob.size,
            audioDuration: actualRecordingDuration,
            contentType: audioBlob.type,
            assignmentId: assignmentId,
            errorMessage: String(error),
          });

          toast.error(t("studentActivityPage.recording.processingFailed"), {
            description: t("studentActivityPage.recording.cannotValidate"),
          });

          // 🔧 清理所有錄音狀態
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          setMediaRecorder(null);
          setIsRecording(false);
          setRecordingTime(0);
          return;
        }

        // Update local state immediately for playback
        setAnswers((prev) => {
          const newAnswers = new Map(prev);
          const answer = newAnswers.get(currentActivity.id) || {
            progressId: currentActivity.id,
            status: "not_started",
            startTime: new Date(),
            recordings: [],
            answers: [],
          };

          if (currentActivity.items && currentActivity.items.length > 0) {
            // Will update activities state instead
          } else {
            (answer as Answer).audioBlob = audioBlob;
            (answer as Answer).audioUrl = localAudioUrl;
          }

          answer.status = "in_progress";
          (answer as Answer).endTime = new Date();

          newAnswers.set(currentActivity.id, answer);
          return newAnswers;
        });

        // Update activity's item recording_url for display
        if (currentActivity.items && currentActivity.items.length > 0) {
          setActivities((prevActivities) => {
            const newActivities = [...prevActivities];
            const activityIndex = newActivities.findIndex(
              (a) => a.id === currentActivity.id,
            );
            if (activityIndex !== -1 && newActivities[activityIndex].items) {
              const newItems = [...newActivities[activityIndex].items!];
              if (newItems[currentSubQuestionIndex]) {
                newItems[currentSubQuestionIndex] = {
                  ...newItems[currentSubQuestionIndex],
                  recording_url: localAudioUrl,
                };
              }
              newActivities[activityIndex] = {
                ...newActivities[activityIndex],
                items: newItems,
              };
            }
            return newActivities;
          });
        }

        console.log("✅ 錄音完成，可以播放或上傳");
        isReRecording.current = false;

        // 🔧 錄音完成後清理所有錄音狀態
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
        setMediaRecorder(null);
        setIsRecording(false);
        setRecordingTime(0);
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0);
      recordingTimeRef.current = 0;
      hasRecordedData.current = false;
      console.log("🎙️ Recording started, waiting for audio data...");

      // Start recording timer with 45 second limit
      let hasReachedLimit = false;
      recordingInterval.current = setInterval(() => {
        recordingTimeRef.current += 1;
        const newTime = recordingTimeRef.current;
        setRecordingTime(newTime);

        if (newTime >= 45 && !hasReachedLimit) {
          hasReachedLimit = true;
          if (recordingInterval.current) {
            clearInterval(recordingInterval.current);
            recordingInterval.current = null;
          }
          setTimeout(() => {
            if (mediaRecorder && mediaRecorder.state === "recording") {
              mediaRecorder.stop();
              setMediaRecorder(null);
              setIsRecording(false);
              toast.info(t("studentActivityPage.warnings.recordingLimit"));
            }
          }, 0);
        }
      }, 1000);
    } catch (error) {
      console.error("Failed to start recording:", error);
      toast.error(t("studentActivity.toast.cannotStartRecording"));
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      // cleanupRecording 會在 recorder.onstop 之後自動被呼叫
      // 這裡只清理 timer，避免干擾 onstop 事件
      if (recordingInterval.current) {
        clearInterval(recordingInterval.current);
        recordingInterval.current = null;
      }
    }
  };

  const handleRecordingComplete = useCallback(
    (blob: Blob, url: string) => {
      const currentActivity = activities[currentActivityIndex];

      setAnswers((prev) => {
        const newAnswers = new Map(prev);
        const answer = newAnswers.get(currentActivity.id) || {
          progressId: currentActivity.id,
          status: "not_started",
          startTime: new Date(),
          recordings: [],
          answers: [],
        };

        (answer as Answer).audioBlob = blob;
        (answer as Answer).audioUrl = url;
        answer.status = "in_progress";
        (answer as Answer).endTime = new Date();

        newAnswers.set(currentActivity.id, answer);
        return newAnswers;
      });

      if (currentActivity.items && currentActivity.items.length > 0) {
        setActivities((prevActivities) => {
          const newActivities = [...prevActivities];
          const activityIndex = newActivities.findIndex(
            (a) => a.id === currentActivity.id,
          );
          if (activityIndex !== -1 && newActivities[activityIndex].items) {
            const newItems = [...newActivities[activityIndex].items!];
            if (newItems[currentSubQuestionIndex]) {
              newItems[currentSubQuestionIndex] = {
                ...newItems[currentSubQuestionIndex],
                recording_url: url,
              };
            }
            newActivities[activityIndex] = {
              ...newActivities[activityIndex],
              items: newItems,
            };
          }
          return newActivities;
        });
      }
    },
    [activities, currentActivityIndex, currentSubQuestionIndex],
  );

  const handleFileUpload = async (file: File) => {
    if (isReadOnly) {
      toast.warning(
        isPreviewMode
          ? t("studentActivityPage.warnings.previewNoUpload")
          : t("studentActivityPage.warnings.readonlyNoUpload"),
      );
      return;
    }

    console.log("📁 File upload:", {
      name: file.name,
      size: file.size,
      type: file.type,
    });

    const MAX_FILE_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_FILE_SIZE) {
      toast.error(t("studentActivity.toast.fileTooLarge"), {
        description: t("studentActivity.toast.fileSizeLimit"),
      });
      return;
    }

    const ALLOWED_TYPES = [
      "audio/mpeg",
      "audio/mp3",
      "audio/mp4",
      "audio/x-m4a",
      "audio/m4a",
      "video/mp4",
      "audio/webm",
      "audio/wav",
      "audio/wave",
      "audio/x-wav",
      "audio/ogg",
      "audio/aac",
    ];
    if (!ALLOWED_TYPES.includes(file.type)) {
      toast.error(t("studentActivity.toast.unsupportedFormat"), {
        description: t("studentActivity.toast.supportedFormats"),
      });
      return;
    }

    try {
      const audio = new Audio();
      const tempUrl = URL.createObjectURL(file);

      const duration = await new Promise<number>((resolve, reject) => {
        audio.addEventListener("loadedmetadata", () => {
          const dur = audio.duration;
          if (isNaN(dur) || dur === Infinity) {
            reject(new Error("無法讀取音檔長度"));
          } else {
            resolve(dur);
          }
        });
        audio.addEventListener("error", () =>
          reject(new Error("音檔格式錯誤")),
        );
        audio.src = tempUrl;
      });

      URL.revokeObjectURL(tempUrl);

      if (duration < 1) {
        toast.error(t("studentActivity.toast.recordingTooShort"), {
          description: t("studentActivity.toast.minDuration", { duration: 1 }),
        });
        return;
      }

      if (duration > 45) {
        toast.error(t("studentActivity.toast.recordingTooLong"), {
          description: t("studentActivity.toast.maxDuration", { duration: 45 }),
        });
        return;
      }

      const audioBlob = new Blob([file], { type: file.type });
      const audioUrl = URL.createObjectURL(audioBlob);
      const currentActivity = activities[currentActivityIndex];

      setAnswers((prev) => {
        const newAnswers = new Map(prev);
        const answer = newAnswers.get(currentActivity.id) || {
          progressId: currentActivity.id,
          status: "not_started",
          startTime: new Date(),
          recordings: [],
          answers: [],
        };

        if (currentActivity.items && currentActivity.items.length > 0) {
          // Will update activities state
        } else {
          (answer as Answer).audioBlob = audioBlob;
          (answer as Answer).audioUrl = audioUrl;
        }

        answer.status = "in_progress";
        (answer as Answer).endTime = new Date();

        newAnswers.set(currentActivity.id, answer);
        return newAnswers;
      });

      if (currentActivity.items && currentActivity.items.length > 0) {
        setActivities((prevActivities) => {
          const newActivities = [...prevActivities];
          const activityIndex = newActivities.findIndex(
            (a) => a.id === currentActivity.id,
          );
          if (activityIndex !== -1 && newActivities[activityIndex].items) {
            const newItems = [...newActivities[activityIndex].items!];
            if (newItems[currentSubQuestionIndex]) {
              newItems[currentSubQuestionIndex] = {
                ...newItems[currentSubQuestionIndex],
                recording_url: audioUrl,
              };
            }
            newActivities[activityIndex] = {
              ...newActivities[activityIndex],
              items: newItems,
            };
          }
          return newActivities;
        });
      }

      toast.success(t("studentActivity.toast.uploadSuccess"), {
        description: `${file.name}（${duration.toFixed(1)} 秒）`,
      });

      console.log("✅ File uploaded successfully");
    } catch (error) {
      console.error("❌ File upload failed:", error);
      toast.error(t("studentActivity.toast.validationFailed"), {
        description: error instanceof Error ? error.message : "未知錯誤",
      });
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // 🎯 生成項目唯一 key (activityId-itemIndex)
  const getItemKey = (activityId: number, itemIndex: number) =>
    `${activityId}-${itemIndex}`;

  // 🎯 背景分析函數
  const analyzeInBackground = useCallback(
    async (activityId: number, itemIndex: number) => {
      const itemKey = getItemKey(activityId, itemIndex);
      const activity = activities.find((a) => a.id === activityId);
      if (!activity || !activity.items || !activity.items[itemIndex]) {
        console.error("Activity or item not found for background analysis");
        return;
      }

      const item = activity.items[itemIndex];
      const audioUrl = item.recording_url;
      const referenceText = item.text;
      const contentItemId = item.id;

      if (!audioUrl || !referenceText || !contentItemId) {
        console.warn("Missing data for background analysis:", {
          audioUrl,
          referenceText,
          contentItemId,
        });
        return;
      }

      // 檢查是否已經在分析中或已完成
      const currentState = itemAnalysisStates.get(itemKey);
      if (
        currentState?.status === "analyzing" ||
        currentState?.status === "analyzed"
      ) {
        console.log(`Item ${itemKey} already ${currentState.status}, skipping`);
        return;
      }

      // 更新狀態為 analyzing
      setItemAnalysisStates((prev) => {
        const next = new Map(prev);
        next.set(itemKey, { status: "analyzing", retryCount: 0 });
        return next;
      });

      const token = useStudentAuthStore.getState().token;
      const apiUrl = import.meta.env.VITE_API_URL || "";

      const analysisPromise = (async () => {
        try {
          let gcsAudioUrl = audioUrl as string;
          const answer = answers.get(activityId);
          let currentProgressId =
            answer?.progressIds && answer.progressIds[itemIndex]
              ? answer.progressIds[itemIndex]
              : item.progress_id || null;

          // 🔍 上傳音檔（如果是 blob URL）
          if (typeof audioUrl === "string" && audioUrl.startsWith("blob:")) {
            const response = await fetch(audioUrl);
            const audioBlob = await response.blob();

            const formData = new FormData();
            formData.append("assignment_id", assignmentId!.toString());
            formData.append("content_item_id", contentItemId.toString());
            const uploadFileExtension = audioBlob.type.includes("mp4")
              ? "recording.mp4"
              : audioBlob.type.includes("webm")
                ? "recording.webm"
                : "recording.audio";
            formData.append("audio_file", audioBlob, uploadFileExtension);

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
                    `Upload failed: ${uploadResponse.status}`,
                  );
                  throw error;
                }

                return await uploadResponse.json();
              },
              (attempt, error) => {
                console.log(`Background upload retrying (${attempt}):`, error);
              },
            );

            if (uploadResult) {
              gcsAudioUrl = uploadResult.audio_url;
              currentProgressId = uploadResult.progress_id;
            }
          }

          if (!currentProgressId) {
            throw new Error("No progress_id available for analysis");
          }

          // 🤖 AI 分析
          const aiFormData = new FormData();
          const audioResponse = await fetch(gcsAudioUrl);
          const audioBlob = await audioResponse.blob();
          const fileExtension = audioBlob.type.includes("mp4")
            ? "recording.mp4"
            : audioBlob.type.includes("webm")
              ? "recording.webm"
              : "recording.audio";
          aiFormData.append("audio_file", audioBlob, fileExtension);
          aiFormData.append("reference_text", referenceText!);
          aiFormData.append("progress_id", String(currentProgressId));
          aiFormData.append("item_index", String(itemIndex));
          if (assignmentId) {
            aiFormData.append("assignment_id", String(assignmentId));
          }

          const analysisResult = await retryAIAnalysis(
            async () => {
              const analysisResponse = await fetch(
                `${apiUrl}/api/speech/assess`,
                {
                  method: "POST",
                  headers: {
                    Authorization: `Bearer ${token}`,
                  },
                  body: aiFormData,
                },
              );

              if (!analysisResponse.ok) {
                throw new Error(`Analysis failed: ${analysisResponse.status}`);
              }

              return await analysisResponse.json();
            },
            (attempt, error) => {
              console.log(`Background analysis retrying (${attempt}):`, error);
            },
          );

          // 更新 activity 的 ai_scores
          setActivities((prevActivities) => {
            const newActivities = [...prevActivities];
            const activityIndex = newActivities.findIndex(
              (a) => a.id === activityId,
            );
            if (activityIndex !== -1) {
              const updatedActivity = { ...newActivities[activityIndex] };
              if (!updatedActivity.ai_scores) {
                updatedActivity.ai_scores = { items: {} };
              }
              if (!updatedActivity.ai_scores.items) {
                updatedActivity.ai_scores.items = {};
              }
              updatedActivity.ai_scores.items[itemIndex] = analysisResult;

              // Also update item's ai_assessment
              if (updatedActivity.items && updatedActivity.items[itemIndex]) {
                const newItems = [...updatedActivity.items];
                newItems[itemIndex] = {
                  ...newItems[itemIndex],
                  ai_assessment: analysisResult,
                };
                updatedActivity.items = newItems;
              }

              newActivities[activityIndex] = updatedActivity;
            }
            return newActivities;
          });

          // 更新狀態為 analyzed
          setItemAnalysisStates((prev) => {
            const next = new Map(prev);
            next.set(itemKey, { status: "analyzed" });
            return next;
          });

          pendingAnalysisRef.current.delete(itemKey);
          failedItemsRef.current.delete(itemKey);
          setPendingAnalysisCount(pendingAnalysisRef.current.size); // 🔒 更新計數

          console.log(`✅ Background analysis completed for ${itemKey}`);
        } catch (error) {
          console.error(`❌ Background analysis failed for ${itemKey}:`, error);

          // 更新狀態為 failed
          setItemAnalysisStates((prev) => {
            const next = new Map(prev);
            const current = next.get(itemKey) || {
              status: "failed" as const,
              retryCount: 0,
            };
            next.set(itemKey, {
              status: "failed",
              error: error instanceof Error ? error.message : String(error),
              retryCount: (current.retryCount || 0) + 1,
            });
            return next;
          });

          failedItemsRef.current.add(itemKey);
          pendingAnalysisRef.current.delete(itemKey);
          setPendingAnalysisCount(pendingAnalysisRef.current.size); // 🔒 更新計數
        }
      })();

      pendingAnalysisRef.current.set(itemKey, analysisPromise);
      setPendingAnalysisCount(pendingAnalysisRef.current.size); // 🔒 更新計數
    },
    [activities, answers, assignmentId, itemAnalysisStates],
  );

  // 🎯 共用 helper function - 檢查並觸發背景分析
  const checkAndTriggerBackgroundAnalysis = useCallback(
    (activityId: number, itemIndex: number) => {
      const activity = activities.find((a) => a.id === activityId);
      if (!activity || !activity.items || !activity.items[itemIndex]) {
        return;
      }

      const currentItem = activity.items[itemIndex];
      const itemKey = getItemKey(activityId, itemIndex);
      const hasRecording =
        currentItem.recording_url && currentItem.recording_url !== "";
      const currentState = itemAnalysisStates.get(itemKey);
      const hasAiAssessment =
        currentItem.ai_assessment ||
        (activity.ai_scores?.items && activity.ai_scores.items[itemIndex]);

      // 只有在有錄音、未分析、且未在背景分析中時，才觸發背景分析
      if (
        hasRecording &&
        !hasAiAssessment &&
        currentState?.status !== "analyzing" &&
        currentState?.status !== "analyzed" &&
        !isPreviewMode // 預覽模式不執行分析
      ) {
        console.log(`🚀 Triggering background analysis for ${itemKey}`);
        analyzeInBackground(activityId, itemIndex);
      }
    },
    [activities, itemAnalysisStates, isPreviewMode, analyzeInBackground],
  );

  const handleNextActivity = async () => {
    const currentActivity = activities[currentActivityIndex];

    // 🎯 觸發背景分析（使用共用 helper）
    if (currentActivity.items && currentActivity.items.length > 0) {
      checkAndTriggerBackgroundAnalysis(
        currentActivity.id,
        currentSubQuestionIndex,
      );

      // 切換到下一題
      if (currentSubQuestionIndex < currentActivity.items.length - 1) {
        setCurrentSubQuestionIndex(currentSubQuestionIndex + 1);
        setRecordingTime(0);
        recordingTimeRef.current = 0;
        return;
      }
    }

    if (currentActivityIndex < activities.length - 1) {
      setCurrentActivityIndex(currentActivityIndex + 1);
      setCurrentSubQuestionIndex(0);
      setRecordingTime(0);
      recordingTimeRef.current = 0;
    }
  };

  const handlePreviousActivity = async () => {
    const currentActivity = activities[currentActivityIndex];

    // 🎯 觸發背景分析（使用共用 helper）
    if (currentActivity.items && currentActivity.items.length > 0) {
      checkAndTriggerBackgroundAnalysis(
        currentActivity.id,
        currentSubQuestionIndex,
      );

      if (currentSubQuestionIndex > 0) {
        setCurrentSubQuestionIndex(currentSubQuestionIndex - 1);
        setRecordingTime(0);
        recordingTimeRef.current = 0;
        return;
      }
    }

    if (currentActivityIndex > 0) {
      const prevActivityIndex = currentActivityIndex - 1;
      const prevActivity = activities[prevActivityIndex];
      setCurrentActivityIndex(prevActivityIndex);

      if (prevActivity.items && prevActivity.items.length > 0) {
        setCurrentSubQuestionIndex(prevActivity.items.length - 1);
      } else {
        setCurrentSubQuestionIndex(0);
      }
      setRecordingTime(0);
      recordingTimeRef.current = 0;
    }
  };

  const handleActivitySelect = async (
    index: number,
    subQuestionIndex: number = 0,
  ) => {
    // 🎯 觸發背景分析（使用共用 helper）- 離開當前題目前
    const currentActivity = activities[currentActivityIndex];
    if (currentActivity.items && currentActivity.items.length > 0) {
      checkAndTriggerBackgroundAnalysis(
        currentActivity.id,
        currentSubQuestionIndex,
      );
    }

    setCurrentActivityIndex(index);
    setCurrentSubQuestionIndex(subQuestionIndex);
    setRecordingTime(0);
    recordingTimeRef.current = 0;
  };

  const handleSubmit = async (e?: React.MouseEvent, force = false) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (isPreviewMode) {
      toast.info(t("studentActivityPage.preview.cannotSubmit"));
      return;
    }

    // 🎯 收集所有未錄音的題目（警告） - 只在未強制提交時檢查
    if (!force) {
      const notRecorded: {
        activity: Activity;
        itemIndex?: number;
        itemLabel: string;
      }[] = [];

      activities.forEach((activity) => {
        // 檢查是否是需要錄音的題型
        const needsRecording = [
          "reading_assessment",
          "grouped_questions",
          "speaking",
        ].includes(activity.type);

        if (needsRecording && activity.items && activity.items.length > 0) {
          // 逐題檢查
          activity.items.forEach((item, itemIndex) => {
            const hasRecording =
              item.recording_url && item.recording_url !== "";
            const isBlob =
              hasRecording && item.recording_url!.startsWith("blob:");
            const itemLabel = `${activity.title} - ${t("studentActivityPage.validation.itemNumber", { number: itemIndex + 1 })}`;

            if (!hasRecording || isBlob) {
              const warning = isBlob
                ? `${itemLabel}${t("studentActivityPage.validation.notUploaded")}`
                : `${itemLabel}${t("studentActivityPage.validation.notRecorded")}`;

              notRecorded.push({
                activity,
                itemIndex,
                itemLabel: warning,
              });
            }
          });
        } else if (needsRecording && !activity.items) {
          // 單一錄音題目（如 reading_assessment）
          const hasRecording = activity.audio_url && activity.audio_url !== "";
          const isBlob =
            hasRecording && activity.audio_url!.startsWith("blob:");

          if (!hasRecording || isBlob) {
            const warning = isBlob
              ? `${activity.title}${t("studentActivityPage.validation.notUploaded")}`
              : activity.title;

            notRecorded.push({
              activity,
              itemLabel: warning,
            });
          }
        }
      });

      // 🎯 如果有未錄音的題目，顯示警告 dialog
      if (notRecorded.length > 0) {
        // itemLabel already contains the complete warning message
        const incompleteList = notRecorded.map((item) => item.itemLabel);
        setIncompleteItems(incompleteList);
        setShowSubmitDialog(true);
        return;
      }
    }

    // 🎯 立即提交（只上傳音檔，不執行分析）
    if (onSubmit) {
      try {
        setIsAnalyzing(true);
        await onSubmit({
          answers: [], // Will be filled by parent component
        });
        setIsAnalyzing(false);

        toast.success(
          t("studentActivityPage.messages.submitSuccess") || "提交成功！",
        );
      } catch (error) {
        setIsAnalyzing(false);
        console.error("Submission error:", error);
        const errorMessage =
          error instanceof Error ? error.message : "提交失敗";
        toast.error(
          t("studentActivityPage.messages.submitError") || errorMessage,
        );
      }
    }
  };

  const handleConfirmSubmit = async () => {
    setShowSubmitDialog(false);
    // 用戶確認提交，強制提交跳過驗證（已經在 dialog 確認過了）
    await handleSubmit(undefined, true);
  };

  const getStatusIcon = (activity: Activity, answer?: Answer) => {
    const status = answer?.status || "not_started";

    if (status === "completed" || activity.status === "SUBMITTED") {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    } else if (status === "in_progress" || activity.status === "IN_PROGRESS") {
      return <Clock className="h-4 w-4 text-yellow-500" />;
    } else {
      return <Circle className="h-4 w-4" />;
    }
  };

  const getActivityTypeBadge = (type: string) => {
    switch (type) {
      case "reading_assessment":
        return (
          <Badge variant="outline">
            {t("studentActivityPage.activityTypes.reading")}
          </Badge>
        );
      case "listening_cloze":
        return (
          <Badge variant="outline">
            {t("studentActivityPage.activityTypes.listening")}
          </Badge>
        );
      case "speaking_practice":
        return (
          <Badge variant="outline">
            {t("studentActivityPage.activityTypes.speaking")}
          </Badge>
        );
      case "speaking_scenario":
        return (
          <Badge variant="outline">
            {t("studentActivityPage.activityTypes.speaking")}
          </Badge>
        );
      case "sentence_making":
        return (
          <Badge variant="outline">
            {t("studentActivityPage.activityTypes.speaking")}
          </Badge>
        );
      case "speaking_quiz":
        return (
          <Badge variant="outline">
            {t("studentActivityPage.activityTypes.speaking")}
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            {t("studentActivityPage.activityTypes.reading")}
          </Badge>
        );
    }
  };

  const handleUpdateItemRecording = useCallback(
    (activityId: number, index: number, url: string) => {
      setActivities((prevActivities) => {
        const newActivities = [...prevActivities];
        const activityIndex = newActivities.findIndex(
          (a) => a.id === activityId,
        );
        if (activityIndex !== -1 && newActivities[activityIndex].items) {
          const newItems = [...newActivities[activityIndex].items!];
          if (newItems[index]) {
            newItems[index] = {
              ...newItems[index],
              recording_url: url,
            };
          }
          newActivities[activityIndex] = {
            ...newActivities[activityIndex],
            items: newItems,
          };
        }
        return newActivities;
      });
    },
    [],
  );

  const renderActivityContent = (activity: Activity) => {
    const answer = answers.get(activity.id);

    if (activity.items && activity.items.length > 0) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const aiAssessments: Record<number, any> = {};
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      activity.items.forEach((item: any, index: number) => {
        if (item.ai_assessment) {
          aiAssessments[index] = {
            accuracy_score: item.ai_assessment.accuracy_score,
            fluency_score: item.ai_assessment.fluency_score,
            pronunciation_score: item.ai_assessment.pronunciation_score,
            completeness_score: item.ai_assessment.completeness_score || 0,
            prosody_score: item.ai_assessment.prosody_score,
            word_details: item.ai_assessment.word_details || [],
            detailed_words: item.ai_assessment.detailed_words || [],
            reference_text: item.ai_assessment.reference_text || "",
            recognized_text: item.ai_assessment.recognized_text || "",
            analysis_summary: item.ai_assessment.analysis_summary || {},
          };
        }
      });

      const assessmentResults =
        Object.keys(aiAssessments).length > 0
          ? { items: aiAssessments }
          : activity.ai_scores;

      return (
        <GroupedQuestionsTemplate
          items={activity.items}
          currentQuestionIndex={currentSubQuestionIndex}
          isRecording={isRecording}
          recordingTime={recordingTime}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          onUpdateItemRecording={(index, url) =>
            handleUpdateItemRecording(activity.id, index, url)
          }
          onFileUpload={handleFileUpload}
          formatTime={formatTime}
          progressIds={
            answer?.progressIds ||
            activity.items
              ?.map((item) => item.progress_id)
              .filter((id): id is number => typeof id === "number") ||
            []
          }
          initialAssessmentResults={assessmentResults}
          readOnly={isReadOnly}
          assignmentId={assignmentId.toString()}
          isPreviewMode={isPreviewMode}
          authToken={authToken}
          itemAnalysisState={itemAnalysisStates.get(
            getItemKey(activity.id, currentSubQuestionIndex),
          )}
          onUploadSuccess={(index, gcsUrl, progressId) => {
            setActivities((prevActivities) => {
              const newActivities = [...prevActivities];
              const activityIndex = newActivities.findIndex(
                (a) => a.id === activity.id,
              );
              if (activityIndex !== -1 && newActivities[activityIndex].items) {
                const newItems = [...newActivities[activityIndex].items!];
                if (newItems[index]) {
                  newItems[index] = {
                    ...newItems[index],
                    recording_url: gcsUrl,
                  };
                }
                newActivities[activityIndex] = {
                  ...newActivities[activityIndex],
                  items: newItems,
                };
              }
              return newActivities;
            });

            setAnswers((prev) => {
              const newAnswers = new Map(prev);
              const answer = newAnswers.get(activity.id);
              if (answer) {
                if (!answer.progressIds) answer.progressIds = [];
                while (answer.progressIds.length <= index) {
                  answer.progressIds.push(0);
                }
                answer.progressIds[index] = progressId;
                answer.status = "completed";
              }
              newAnswers.set(activity.id, answer!);
              return newAnswers;
            });
          }}
          onAssessmentComplete={(index, assessmentResult) => {
            setActivities((prevActivities) => {
              const newActivities = [...prevActivities];
              const activityIndex = newActivities.findIndex(
                (a) => a.id === activity.id,
              );
              if (
                activityIndex !== -1 &&
                newActivities[activityIndex].items &&
                assessmentResult
              ) {
                const newItems = [...newActivities[activityIndex].items!];
                if (newItems[index]) {
                  newItems[index] = {
                    ...newItems[index],
                    ai_assessment: assessmentResult,
                  };
                }
                newActivities[activityIndex] = {
                  ...newActivities[activityIndex],
                  items: newItems,
                };
              }
              return newActivities;
            });
          }}
          onAnalyzingStateChange={setIsAnalyzing} // 🔒 接收分析狀態變化
        />
      );
    }

    switch (activity.type) {
      case "reading_assessment":
        return (
          <ReadingAssessmentTemplate
            content={activity.content}
            targetText={activity.target_text}
            existingAudioUrl={answer?.audioUrl}
            onRecordingComplete={handleRecordingComplete}
            exampleAudioUrl={activity.example_audio_url}
            progressId={activity.id}
            readOnly={isReadOnly}
          />
        );

      case "listening_cloze":
        return (
          <ListeningClozeTemplate
            content={activity.content}
            audioUrl={activity.audio_url || ""}
            blanks={activity.blanks || []}
            userAnswers={answer?.userAnswers || []}
            onAnswerChange={(index, value) => {
              if (isReadOnly) return;

              setAnswers((prev) => {
                const newAnswers = new Map(prev);
                const ans = newAnswers.get(activity.id) || {
                  progressId: activity.id,
                  status: "not_started",
                  startTime: new Date(),
                  userAnswers: [],
                };
                if (!ans.userAnswers) ans.userAnswers = [];
                ans.userAnswers[index] = value;
                ans.status = "in_progress";
                newAnswers.set(activity.id, ans);
                return newAnswers;
              });
            }}
            showAnswers={activity.status === "SUBMITTED"}
          />
        );

      case "speaking_practice":
      case "speaking_scenario":
        return (
          <div className="text-center p-8 text-gray-500">
            <p>此活動類型目前不可用</p>
          </div>
        );

      default:
        return (
          <ReadingAssessmentTemplate
            content={activity.content}
            targetText={activity.target_text || activity.content}
            existingAudioUrl={answer?.audioUrl}
            onRecordingComplete={handleRecordingComplete}
            progressId={activity.id}
            readOnly={isReadOnly}
          />
        );
    }
  };

  if (activities.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-gray-600 mb-4">此作業尚無題目</p>
          {onBack && <Button onClick={onBack}>返回作業詳情</Button>}
        </div>
      </div>
    );
  }

  const currentActivity = activities[currentActivityIndex];
  const progress = ((currentActivityIndex + 1) / activities.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Read-only mode banner */}
      {isReadOnly && !isPreviewMode && (
        <div className="bg-blue-50 border-b border-blue-200 px-2 sm:px-4 py-2">
          <div className="max-w-6xl mx-auto flex items-center gap-2">
            <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600 flex-shrink-0" />
            <span className="text-xs sm:text-sm text-blue-700 truncate">
              {assignmentStatus === "SUBMITTED"
                ? "作業已提交，目前為檢視模式"
                : assignmentStatus === "GRADED"
                  ? "作業已評分，目前為檢視模式"
                  : "檢視模式"}
            </span>
          </div>
        </div>
      )}

      {/* Header with progress */}
      <div className="sticky top-0 bg-white border-b z-10">
        <div className="max-w-6xl mx-auto px-2 sm:px-4 py-2">
          {/* Mobile header layout */}
          <div className="flex flex-row items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
              {onBack && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onBack}
                  className="flex-shrink-0 px-2 sm:px-3"
                >
                  <ChevronLeft className="h-3 w-3 sm:h-4 sm:w-4 mr-1" />
                  <span className="hidden sm:inline">
                    {t("studentActivityPage.buttons.back")}
                  </span>
                  <span className="sm:hidden">
                    {t("studentActivityPage.buttons.backShort")}
                  </span>
                </Button>
              )}
              <div className="h-4 sm:h-6 w-px bg-gray-300 flex-shrink-0" />
              <h1 className="text-sm sm:text-base font-semibold truncate min-w-0">
                {assignmentTitle}
              </h1>
            </div>

            <div className="flex items-center gap-2 sm:gap-3 justify-end flex-shrink-0">
              {saving && (
                <div className="flex items-center gap-1 sm:gap-2 text-xs text-gray-600">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span className="hidden sm:inline">
                    {t("studentActivityPage.status.saving")}
                  </span>
                  <span className="sm:hidden">
                    {t("studentActivityPage.status.savingShort")}
                  </span>
                </div>
              )}
              {!isReadOnly && !isPreviewMode && (
                <Button
                  onClick={handleSubmit}
                  disabled={submitting}
                  size="sm"
                  variant="default"
                  className="px-2 sm:px-3"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                      <span className="hidden sm:inline">
                        {t("studentActivityPage.buttons.submitting")}
                      </span>
                      <span className="sm:hidden">
                        {t("studentActivityPage.buttons.submittingShort")}
                      </span>
                    </>
                  ) : (
                    <>
                      <Send className="h-3 w-3 mr-1" />
                      <span className="hidden sm:inline">
                        {t("studentActivityPage.buttons.submit")}
                      </span>
                      <span className="sm:hidden">
                        {t("studentActivityPage.buttons.submitShort")}
                      </span>
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>

          {/* Activity navigation */}
          <div className="flex gap-2 sm:gap-4 overflow-x-auto pb-2 scrollbar-hide">
            {activities.map((activity, activityIndex) => {
              const answer = answers.get(activity.id);
              const isActiveActivity = activityIndex === currentActivityIndex;

              if (activity.items && activity.items.length > 0) {
                return (
                  <div
                    key={activity.id}
                    className="flex items-center gap-1 sm:gap-2 flex-shrink-0"
                  >
                    <div className="flex items-center gap-1">
                      <span className="text-sm sm:text-xs font-medium text-gray-600 whitespace-nowrap max-w-[120px] sm:max-w-none truncate sm:truncate-none">
                        {activity.title}
                      </span>
                      <Badge
                        variant="outline"
                        className="text-sm sm:text-xs px-1.5 sm:px-1 py-0 h-5 sm:h-5 min-w-[35px] sm:min-w-[30px] text-center"
                      >
                        {t("studentActivityPage.labels.itemCount", {
                          count: activity.items.length,
                        })}
                      </Badge>
                    </div>

                    <div className="flex gap-0.5 sm:gap-1">
                      {activity.items.map((item, itemIndex) => {
                        const isActiveItem =
                          isActiveActivity &&
                          currentSubQuestionIndex === itemIndex;

                        const isCompleted =
                          ("recording_url" in item && item.recording_url) ||
                          activity.answers?.[itemIndex];
                        const teacherFeedback =
                          "teacher_feedback" in item
                            ? item.teacher_feedback
                            : undefined;
                        const teacherPassed =
                          "teacher_passed" in item
                            ? item.teacher_passed
                            : undefined;

                        const hasTeacherGraded =
                          teacherFeedback !== undefined &&
                          teacherFeedback !== null;
                        const isTeacherPassed =
                          hasTeacherGraded && teacherPassed === true;
                        const needsCorrection =
                          hasTeacherGraded && teacherPassed === false;

                        return (
                          <button
                            key={itemIndex}
                            onClick={() => {
                              if (isAnalyzing) return; // 🔒 分析中禁止切換
                              if (activityIndex !== currentActivityIndex) {
                                // 切換 activity，handleActivitySelect 已處理背景分析
                                handleActivitySelect(activityIndex, itemIndex);
                              } else {
                                // 🎯 同一 activity 內切換，需觸發背景分析
                                checkAndTriggerBackgroundAnalysis(
                                  activity.id,
                                  currentSubQuestionIndex,
                                );
                                setCurrentSubQuestionIndex(itemIndex);
                              }
                            }}
                            disabled={isAnalyzing} // 🔒 分析中禁用
                            className={cn(
                              "relative w-8 h-8 sm:w-8 sm:h-8 rounded border transition-all",
                              "flex items-center justify-center text-sm sm:text-xs font-medium",
                              "min-w-[32px] sm:min-w-[32px]",
                              // 保持學生原本的完成狀態樣式
                              isCompleted
                                ? "bg-green-100 text-green-800 border-green-400"
                                : "bg-white text-gray-600 border-gray-300 hover:border-blue-400",
                              isActiveItem && "border-2 border-blue-600",
                            )}
                            title={
                              needsCorrection
                                ? "老師要求訂正"
                                : isTeacherPassed
                                  ? "老師已通過"
                                  : isCompleted
                                    ? "已完成"
                                    : "未完成"
                            }
                          >
                            {itemIndex + 1}
                            {/* 老師評分圖標 - 右上角圓點徽章 */}
                            {hasTeacherGraded && (
                              <span
                                className={cn(
                                  "absolute top-0 right-0 w-3 h-3 rounded-full border border-white",
                                  teacherPassed ? "bg-green-500" : "bg-red-500",
                                )}
                                aria-label={
                                  teacherPassed
                                    ? t("studentActivityPage.feedback.passed")
                                    : t("studentActivityPage.feedback.failed")
                                }
                              />
                            )}
                          </button>
                        );
                      })}
                    </div>

                    {activityIndex < activities.length - 1 && (
                      <div className="w-px h-8 bg-gray-300 ml-2" />
                    )}
                  </div>
                );
              }

              return (
                <Button
                  key={activity.id}
                  variant={isActiveActivity ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleActivitySelect(activityIndex)}
                  disabled={isAnalyzing} // 🔒 分析中禁用
                  className="flex-shrink-0 h-8"
                >
                  <div className="flex items-center gap-2">
                    {getStatusIcon(activity, answer)}
                    <span className="text-xs">{activity.title}</span>
                  </div>
                </Button>
              );
            })}
          </div>

          <Progress value={progress} className="h-1 mt-1" />
        </div>
      </div>

      {/* Main content */}
      <div className="w-full px-2 sm:px-4 mt-3">
        <Card>
          <CardHeader className="py-2 sm:py-3">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 min-w-0">
              <CardTitle className="text-base sm:text-lg leading-tight">
                {t("studentActivityPage.labels.questionNumber", {
                  number: currentActivity.order,
                })}{" "}
                {currentActivity.title}
              </CardTitle>
              {getActivityTypeBadge(currentActivity.type)}
            </div>
          </CardHeader>

          <CardContent className="p-2 sm:p-3">
            {renderActivityContent(currentActivity)}

            {/* Navigation buttons */}
            {(() => {
              let isAssessed = false;

              if (currentActivity.items && currentActivity.items.length > 0) {
                const currentItem =
                  currentActivity.items[currentSubQuestionIndex];
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                isAssessed = !!(currentItem as any)?.ai_assessment;
              } else if (currentActivity.type === "reading_assessment") {
                isAssessed = !!currentActivity.ai_scores;
              } else if (currentActivity.type === "listening_cloze") {
                const answer = answers.get(currentActivity.id);
                isAssessed = !!(
                  answer?.userAnswers && answer.userAnswers.length > 0
                );
              }

              if (!isAssessed && !isPreviewMode) {
                return null;
              }

              return (
                <div className="flex items-center justify-center gap-2 sm:gap-3 mt-6 pt-4 border-t border-gray-200">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePreviousActivity}
                    disabled={
                      isAnalyzing || // 🔒 分析中禁用
                      (currentActivityIndex === 0 &&
                        currentSubQuestionIndex === 0)
                    }
                    className="flex-1 sm:flex-none min-w-0"
                  >
                    <ChevronLeft className="h-3 w-3 sm:h-4 sm:w-4 mr-1" />
                    <span className="hidden sm:inline">
                      {t("studentActivityPage.buttons.previous")}
                    </span>
                    <span className="sm:hidden">
                      {t("studentActivityPage.buttons.previous")}
                    </span>
                  </Button>

                  {(() => {
                    const isLastActivity =
                      currentActivityIndex === activities.length - 1;
                    const isLastSubQuestion = currentActivity.items
                      ? currentSubQuestionIndex ===
                        currentActivity.items.length - 1
                      : true;

                    if (isLastActivity && isLastSubQuestion && !isPreviewMode) {
                      return (
                        <Button
                          variant="default"
                          size="sm"
                          onClick={handleSubmit}
                          disabled={isAnalyzing || submitting} // 🔒 分析中禁用
                          className="flex-1 sm:flex-none min-w-0"
                        >
                          <span className="hidden sm:inline">
                            {submitting
                              ? t("studentActivityPage.buttons.submitting")
                              : t("studentActivityPage.buttons.submit")}
                          </span>
                          <span className="sm:hidden">
                            {submitting
                              ? t("studentActivityPage.buttons.submittingShort")
                              : t("studentActivityPage.buttons.submitShort")}
                          </span>
                          <Send className="h-3 w-3 sm:h-4 sm:w-4 ml-1" />
                        </Button>
                      );
                    }

                    return (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleNextActivity}
                        disabled={isAnalyzing} // 🔒 分析中禁用
                        className="flex-1 sm:flex-none min-w-0"
                      >
                        <span className="hidden sm:inline">
                          {t("studentActivityPage.buttons.next")}
                        </span>
                        <span className="sm:hidden">
                          {t("studentActivityPage.buttons.next")}
                        </span>
                        <ChevronRight className="h-3 w-3 sm:h-4 sm:w-4 ml-1" />
                      </Button>
                    );
                  })()}
                </div>
              );
            })()}
          </CardContent>
        </Card>

        {/* Status summary */}
        <Card className="mt-4 sm:mt-6">
          <CardContent className="pt-4 sm:pt-6">
            <div className="grid grid-cols-3 gap-2 sm:gap-4 text-center">
              <div>
                <div className="text-xl sm:text-2xl font-bold text-green-600">
                  {
                    Array.from(answers.values()).filter(
                      (a) => a.status === "completed",
                    ).length
                  }
                </div>
                <p className="text-xs sm:text-sm text-gray-600">
                  {t("studentActivityPage.status.completed")}
                </p>
              </div>
              <div>
                <div className="text-xl sm:text-2xl font-bold text-yellow-600">
                  {
                    Array.from(answers.values()).filter(
                      (a) => a.status === "in_progress",
                    ).length
                  }
                </div>
                <p className="text-xs sm:text-sm text-gray-600">
                  {t("studentActivityPage.status.inProgress")}
                </p>
              </div>
              <div>
                <div className="text-xl sm:text-2xl font-bold text-gray-400">
                  {
                    Array.from(answers.values()).filter(
                      (a) => a.status === "not_started",
                    ).length
                  }
                </div>
                <p className="text-xs sm:text-sm text-gray-600">
                  {t("studentActivityPage.status.notStarted")}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 提交確認 Dialog */}
      <Dialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-600">
              <AlertTriangle className="h-5 w-5" />
              {t("studentActivityPage.validation.title")}
            </DialogTitle>
            <DialogDescription className="text-base pt-2">
              {t("studentActivityPage.validation.incompleteItems")}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 max-h-[300px] overflow-y-auto">
              <ul className="space-y-2">
                {incompleteItems.map((item, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <span className="text-amber-600 mt-0.5">•</span>
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowSubmitDialog(false)}
            >
              {t("studentActivityPage.buttons.cancel")}
            </Button>
            <Button
              type="button"
              variant="default"
              onClick={handleConfirmSubmit}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {t("studentActivityPage.buttons.confirm")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 🔒 全屏分析遮罩 */}
      {isAnalyzing && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-white rounded-2xl p-8 shadow-2xl max-w-md mx-4 text-center">
            <div className="relative w-24 h-24 mx-auto mb-6">
              {/* 外圈脈動動畫 */}
              <div className="absolute inset-0 rounded-full bg-purple-100 animate-ping opacity-75"></div>
              {/* 中圈脈動動畫 */}
              <div className="absolute inset-2 rounded-full bg-purple-200 animate-pulse"></div>
              {/* 大腦圖示 - 旋轉動畫 */}
              <Loader2
                className="w-24 h-24 absolute inset-0 animate-spin text-purple-600"
                style={{ animationDuration: "2s" }}
              />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              {t("studentActivityPage.messages.analyzingRecording")}
            </h3>
            <p className="text-gray-600 mb-4">
              {t("studentActivityPage.messages.pleaseWait")}
            </p>
            <p className="text-sm text-gray-500">
              {t("studentActivityPage.messages.doNotLeave")}
            </p>
          </div>
        </div>
      )}

      {/* 🎯 背景分析進度指示器（輕量版，右下角浮動提示） */}
      {!isAnalyzing && pendingAnalysisCount > 0 && (
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-3 rounded-lg shadow-lg z-40 flex items-center gap-3 max-w-xs">
          <Loader2 className="h-5 w-5 animate-spin flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">
              {t("studentActivityPage.messages.backgroundAnalyzing") ||
                "背景分析中"}
            </p>
            <p className="text-xs text-blue-100">
              {t("studentActivityPage.messages.backgroundAnalyzingCount", {
                count: pendingAnalysisCount,
              }) || `${pendingAnalysisCount} 題進行中...`}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
