import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
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
  BookOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { retryAudioUpload } from "@/utils/retryHelper";
import {
  setErrorLoggingContext,
  clearErrorLoggingContext,
} from "@/contexts/ErrorLoggingContext";

// Activity type from API
interface Activity {
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
  // For activities with multiple items (questions)
  items?: Array<{
    id?: number;
    text?: string;
    translation?: string;
    audio_url?: string;
    recording_url?: string; // Direct recording URL from StudentItemProgress
    [key: string]: unknown;
  }>;
  item_count?: number;
  answers?: string[];
  // Additional fields for different activity types
  blanks?: string[];
  prompts?: string[];
  example_audio_url?: string;
  // AI evaluation results
  ai_scores?: {
    accuracy_score?: number;
    fluency_score?: number;
    completeness_score?: number;
    pronunciation_score?: number;
    word_details?: Array<{
      word: string;
      accuracy_score: number;
      error_type: string;
    }>;
    // For grouped_questions with multiple items
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
          error_type: string;
        }>;
        detailed_words?: unknown[];
        reference_text?: string;
        recognized_text?: string;
        analysis_summary?: unknown;
      }
    >;
  };
}

interface ActivityResponse {
  assignment_id: number;
  title: string;
  status?: string; // 加入作業狀態
  total_activities: number;
  activities: Activity[];
}

interface Answer {
  progressId: number;
  progressIds?: number[]; // For grouped questions with multiple progress records
  audioBlob?: Blob;
  audioUrl?: string;
  textAnswer?: string;
  userAnswers?: string[]; // For listening cloze
  answers?: string[]; // For grouped questions answers
  startTime: Date;
  endTime?: Date;
  status: "not_started" | "in_progress" | "completed";
}

export default function StudentActivityPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const navigate = useNavigate();
  const { token, user } = useStudentAuthStore();

  // State management
  const [activities, setActivities] = useState<Activity[]>([]);
  const [assignmentTitle, setAssignmentTitle] = useState("");
  const [assignmentStatus, setAssignmentStatus] = useState<string>(""); // 作業狀態
  const [isReadOnly, setIsReadOnly] = useState(false); // 唯讀模式
  const [currentActivityIndex, setCurrentActivityIndex] = useState(0);
  const [currentSubQuestionIndex, setCurrentSubQuestionIndex] = useState(0); // For activities with multiple items
  const [answers, setAnswers] = useState<Map<number, Answer>>(new Map());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null,
  );
  const recordingInterval = useRef<NodeJS.Timeout | null>(null);
  const isReRecording = useRef<boolean>(false); // Track if this is a re-recording
  const [isAutoAssessing, setIsAutoAssessing] = useState(false); // Auto AI assessment loading state
  const autoPlayAudioRef = useRef<HTMLAudioElement | null>(null); // For auto-playing recorded audio

  // Set error logging context for audio error tracking
  useEffect(() => {
    if (assignmentId) {
      setErrorLoggingContext({
        assignmentId: parseInt(assignmentId),
        studentId: user?.id, // 從 auth store 取得 studentId
      });
    }

    return () => {
      clearErrorLoggingContext();
    };
  }, [assignmentId, user]);

  // Load activities from API
  useEffect(() => {
    if (assignmentId && token) {
      loadActivities();
    }
  }, [assignmentId, token]);

  const loadActivities = async () => {
    try {
      setLoading(true);
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const response = await fetch(
        `${apiUrl}/api/students/assignments/${assignmentId}/activities`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to load activities: ${response.status}`);
      }

      const data: ActivityResponse = await response.json();
      console.log("Loaded activities from API:", data.activities);

      // Log AI assessment data from items
      data.activities.forEach((activity, idx) => {
        if (activity.items && activity.items.length > 0) {
          console.log(
            `Activity ${idx} items with AI assessment:`,
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            activity.items.map((item: any) => ({
              id: item.id,
              text: item.text?.substring(0, 20),
              has_ai: !!item.ai_assessment,
              scores: item.ai_assessment
                ? {
                    accuracy: item.ai_assessment.accuracy_score,
                    fluency: item.ai_assessment.fluency_score,
                    pronunciation: item.ai_assessment.pronunciation_score,
                  }
                : null,
            })),
          );

          // Debug teacher feedback
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const teacherFeedbackData = activity.items.map((item: any) => ({
            id: item.id,
            text: item.text?.substring(0, 30),
            teacher_feedback: item.teacher_feedback,
            teacher_passed: item.teacher_passed,
            teacher_review_score: item.teacher_review_score,
          }));

          console.log(
            `[DEBUG] Activity ${idx} teacher feedback:`,
            teacherFeedbackData,
          );

          // 詳細顯示每個 item 的評語
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          teacherFeedbackData.forEach((item: any, i: number) => {
            if (item.teacher_feedback) {
              console.log(
                `  ✅ Item ${i + 1} (ID: ${item.id}) 有評語: "${item.teacher_feedback}"`,
              );
            } else {
              console.log(`  ❌ Item ${i + 1} (ID: ${item.id}) 沒有評語`);
            }
          });
        }
      });

      setActivities(data.activities);
      setAssignmentTitle(data.title);

      // 設置作業狀態和唯讀模式
      if (data.status) {
        setAssignmentStatus(data.status);
        // 如果作業已提交或已評分，設為唯讀模式
        const readOnlyStatuses = ["SUBMITTED", "GRADED"];
        setIsReadOnly(readOnlyStatuses.includes(data.status));

        if (readOnlyStatuses.includes(data.status)) {
          console.log("🔒 Assignment is in read-only mode:", data.status);
        }
      }

      // Initialize answers for all activities
      const initialAnswers = new Map<number, Answer>();
      data.activities.forEach((activity) => {
        // For reading_assessment with single item, extract audioUrl directly
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
          audioUrl: audioUrl, // Only for reading_assessment single recording
          answers: activity.answers || [], // Text answers for grouped questions
          userAnswers: [], // For listening cloze
        });
      });
      setAnswers(initialAnswers);
    } catch (error) {
      console.error("Failed to load activities:", error);
      toast.error("無法載入題目，請稍後再試");
      navigate(`/student/assignment/${assignmentId}`);
    } finally {
      setLoading(false);
    }
  };

  // Recording controls
  // TODO: 重構錄音邏輯 - 代碼重複問題
  // 1. 抽出 useMediaRecorder hook 共用邏輯
  // 2. AudioRecorder.tsx 使用這個 hook
  // 3. StudentActivityPage.tsx 使用這個 hook
  // 4. 避免 300+ 行重複代碼
  // See: AudioRecorder.tsx 有相同的邏輯

  // 🎯 跨瀏覽器格式偵測
  const getSupportedMimeType = () => {
    const types = [
      "audio/webm;codecs=opus", // Chrome/Firefox 首選
      "audio/webm", // Chrome/Firefox 備用
      "audio/mp4", // Safari/iOS 必須
      "audio/ogg;codecs=opus", // Firefox 備用
    ];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        console.log(`✅ Using MIME type: ${type}`);
        return type;
      }
    }

    console.warn("⚠️ No supported MIME type found, using default");
    return ""; // 讓瀏覽器自動選擇
  };

  const startRecording = async (isReRecord: boolean = false) => {
    // 唯讀模式下不允許錄音
    if (isReadOnly) {
      toast.warning("檢視模式下無法錄音");
      return;
    }

    // Set re-recording flag
    isReRecording.current = isReRecord;

    try {
      // Clear old recordings and AI scores when starting new recording
      const currentActivity = activities[currentActivityIndex];

      // Clear previous recording and AI scores for grouped questions
      if (currentActivity.items && currentActivity.items.length > 0) {
        setActivities((prevActivities) => {
          const newActivities = [...prevActivities];
          const activityIndex = newActivities.findIndex(
            (a) => a.id === currentActivity.id,
          );
          if (activityIndex !== -1 && newActivities[activityIndex].items) {
            // Clear the recording_url for the current item
            const newItems = [...newActivities[activityIndex].items!];
            if (newItems[currentSubQuestionIndex]) {
              newItems[currentSubQuestionIndex] = {
                ...newItems[currentSubQuestionIndex],
                recording_url: "", // Clear current recording
              };
            }
            newActivities[activityIndex] = {
              ...newActivities[activityIndex],
              items: newItems,
              ai_scores: undefined, // Clear AI scores
            };
          }
          return newActivities;
        });
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // 🎯 自動偵測支援的 MIME type
      const mimeType = getSupportedMimeType();
      const options = mimeType ? { mimeType } : {};
      const recorder = new MediaRecorder(stream, options);
      const chunks: Blob[] = [];

      // 記錄實際使用的格式
      console.log(
        `🎙️ MediaRecorder initialized with MIME type: ${recorder.mimeType}`,
      );

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = async () => {
        // 使用 MediaRecorder 實際的 MIME type（支援跨瀏覽器）
        const audioBlob = new Blob(chunks, {
          type: recorder.mimeType || "audio/webm",
        });
        const currentActivity = activities[currentActivityIndex];

        // 🎯 驗證錄音檔案
        console.log("🎤 Recording completed:", {
          size: audioBlob.size,
          type: audioBlob.type,
        });

        // 檢查檔案大小（小於 1KB 可能有問題）
        if (audioBlob.size < 1000) {
          console.error("⚠️ Recording file too small:", audioBlob.size);

          // 記錄到 BigQuery
          const { logAudioError } = await import("@/utils/audioErrorLogger");
          await logAudioError({
            errorType: "recording_too_small",
            audioUrl: "blob:local",
            audioSize: audioBlob.size,
            audioDuration: 0,
            contentType: audioBlob.type,
            assignmentId: parseInt(assignmentId || "0"),
          });

          toast.error("錄音失敗", {
            description: "錄音檔案異常，請重新錄音",
          });
          return;
        }

        // Create local audio URL for playback
        const localAudioUrl = URL.createObjectURL(audioBlob);

        // 🎯 關鍵：驗證錄音是否可以播放
        try {
          const testAudio = new Audio(localAudioUrl);

          // 等待 metadata 載入（最多等 5 秒）
          const loadPromise = new Promise<boolean>((resolve) => {
            const timeout = setTimeout(() => {
              console.error("⏱️ Audio metadata load timeout");
              resolve(false);
            }, 5000);

            testAudio.addEventListener("loadedmetadata", () => {
              clearTimeout(timeout);
              console.log(
                "✅ Audio metadata loaded, duration:",
                testAudio.duration,
              );

              // 檢查 duration 是否有效（至少 1 秒）
              // 處理 Safari iOS 的 Infinity 和 NaN 問題
              if (
                isNaN(testAudio.duration) ||
                !isFinite(testAudio.duration) || // 排除 Infinity
                testAudio.duration < 1
              ) {
                console.error("❌ Invalid audio duration:", testAudio.duration);
                resolve(false);
              } else {
                resolve(true);
              }
            });

            testAudio.addEventListener("error", (e) => {
              clearTimeout(timeout);
              console.error("❌ Audio load error:", e);
              resolve(false);
            });

            // 強制載入
            testAudio.load();
          });

          const isValid = await loadPromise;

          if (!isValid) {
            console.error("⚠️ Recording validation failed");

            // 記錄到 BigQuery
            const { logAudioError } = await import("@/utils/audioErrorLogger");
            await logAudioError({
              errorType: "recording_validation_failed",
              audioUrl: localAudioUrl,
              audioSize: audioBlob.size,
              audioDuration: 0,
              contentType: audioBlob.type,
              assignmentId: parseInt(assignmentId || "0"),
              errorMessage: "Duration less than 1 second",
            });

            toast.error("錄音驗證失敗", {
              description:
                "錄音時長必須至少 1 秒。請重新錄音並確保說話時間足夠長。",
            });
            return;
          }

          // ✅ 驗證通過
          console.log("✅ Recording validation passed");
          toast.success("錄音完成", {
            description: "錄音已通過驗證，可以正常播放",
          });
        } catch (error) {
          console.error("❌ Recording validation error:", error);
          toast.error("錄音處理失敗", {
            description: "無法驗證錄音，請重新錄音",
          });
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

          // For grouped questions, update item's recording_url locally
          if (currentActivity.items && currentActivity.items.length > 0) {
            // We'll update the items in activities state instead
          } else {
            // For single questions, store directly
            (answer as Answer).audioBlob = audioBlob;
            (answer as Answer).audioUrl = localAudioUrl;
          }

          answer.status = "in_progress"; // Keep as in_progress until uploaded
          (answer as Answer).endTime = new Date();

          newAnswers.set(currentActivity.id, answer);
          return newAnswers;
        });

        // Update activity's item recording_url for display
        if (currentActivity.items && currentActivity.items.length > 0) {
          // Update activities state to trigger re-render
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

        // Upload to GCS (skip if this is for re-recording)
        const skipUpload = isReRecording.current;
        isReRecording.current = false; // Reset flag

        if (!skipUpload) {
          try {
            // 獲取當前 item 的 ID
            const currentItem =
              currentActivity.items?.[currentSubQuestionIndex];
            if (!currentItem?.id) {
              throw new Error("Content item ID not found");
            }

            const formData = new FormData();
            formData.append("assignment_id", assignmentId || "");
            formData.append("content_item_id", currentItem.id.toString()); // 使用 ContentItem 的 ID！
            formData.append("audio_file", audioBlob, "recording.webm");

            const apiUrl = import.meta.env.VITE_API_URL || "";
            console.log(
              "Uploading recording to:",
              `${apiUrl}/api/students/upload-recording`,
            );

            const result = await retryAudioUpload(
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
                    // Server errors are retryable
                    throw error;
                  }
                  // Client errors (4xx) should not be retried
                  throw Object.assign(error, { noRetry: true });
                }

                return await uploadResponse.json();
              },
              (attempt, error) => {
                console.log(
                  `上傳失敗，正在重試... (第 ${attempt}/3 次)`,
                  error,
                );
                toast.warning(`上傳失敗，正在重試... (第 ${attempt}/3 次)`);
              },
            );

            const { audio_url, message, progress_id } = result;
            console.log("Recording uploaded successfully:", {
              url: audio_url,
              message: message,
              progress_id: progress_id,
            });

            // 錄音成功上傳到雲端
            toast.success("錄音已上傳到雲端");

            // Update with the GCS URL and progress_id
            setAnswers((prev) => {
              const newAnswers = new Map(prev);
              const answer = newAnswers.get(currentActivity.id);
              if (answer) {
                if (currentActivity.items && currentActivity.items.length > 0) {
                  if (!answer.progressIds) answer.progressIds = [];

                  // Ensure progressIds array is long enough
                  while (answer.progressIds.length <= currentSubQuestionIndex) {
                    answer.progressIds.push(0);
                  }

                  // 🔥 關鍵修復：存儲 progress_id 到對應的子問題索引
                  if (progress_id) {
                    answer.progressIds[currentSubQuestionIndex] = progress_id;
                  }
                } else {
                  answer.audioUrl = audio_url;
                  if (progress_id) {
                    answer.progressId = progress_id;
                  }
                }
                answer.status = "completed";
              }
              newAnswers.set(currentActivity.id, answer!);
              return newAnswers;
            });

            // Also update activities state with GCS URL
            if (currentActivity.items && currentActivity.items.length > 0) {
              setActivities((prevActivities) => {
                const newActivities = [...prevActivities];
                const activityIndex = newActivities.findIndex(
                  (a) => a.id === currentActivity.id,
                );
                if (
                  activityIndex !== -1 &&
                  newActivities[activityIndex].items
                ) {
                  const newItems = [...newActivities[activityIndex].items!];
                  if (newItems[currentSubQuestionIndex]) {
                    newItems[currentSubQuestionIndex] = {
                      ...newItems[currentSubQuestionIndex],
                      recording_url: audio_url,
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

            // Save to server with the URL - autoSave will handle the updated recordings array
            await autoSave();

            // 🎯 自動觸發 AI 評估 (新功能)
            const referenceText = currentItem.text;
            if (progress_id && referenceText && audio_url) {
              console.log("🤖 自動開始 AI 評估...", {
                progress_id,
                referenceText,
                audio_url,
              });

              try {
                // 開始播放剛錄好的錄音
                if (autoPlayAudioRef.current) {
                  autoPlayAudioRef.current.pause();
                  autoPlayAudioRef.current = null;
                }

                const playbackAudio = new Audio(audio_url);
                autoPlayAudioRef.current = playbackAudio;

                playbackAudio.play().catch((err) => {
                  console.warn("無法自動播放錄音:", err);
                });

                // 設置評估中狀態（顯示動畫）
                setIsAutoAssessing(true);
                const startTime = Date.now();

                // Convert audio URL to blob for assessment
                const audioResponse = await fetch(audio_url);
                const audioBlob = await audioResponse.blob();

                // Create form data for AI assessment
                const assessFormData = new FormData();
                assessFormData.append(
                  "audio_file",
                  audioBlob,
                  "recording.webm",
                );
                assessFormData.append("reference_text", referenceText);
                assessFormData.append("progress_id", progress_id.toString());

                toast.info("AI 正在分析您的發音...");

                const assessResponse = await fetch(
                  `${apiUrl}/api/speech/assess`,
                  {
                    method: "POST",
                    headers: {
                      Authorization: `Bearer ${token}`,
                    },
                    body: assessFormData,
                  },
                );

                if (!assessResponse.ok) {
                  throw new Error(`AI 評估失敗: ${assessResponse.status}`);
                }

                const assessResult = await assessResponse.json();
                console.log("✅ AI 評估完成:", assessResult);

                // 確保至少顯示 2 秒動畫
                const elapsedTime = Date.now() - startTime;
                const remainingTime = Math.max(0, 2000 - elapsedTime);

                await new Promise((resolve) =>
                  setTimeout(resolve, remainingTime),
                );

                toast.success("AI 發音評估完成！");

                // Update activities with AI assessment result
                setActivities((prevActivities) => {
                  const newActivities = [...prevActivities];
                  const activityIndex = newActivities.findIndex(
                    (a) => a.id === currentActivity.id,
                  );
                  if (
                    activityIndex !== -1 &&
                    newActivities[activityIndex].items
                  ) {
                    // Store AI result in the specific item's ai_assessment
                    const newItems = [...newActivities[activityIndex].items!];
                    if (newItems[currentSubQuestionIndex]) {
                      newItems[currentSubQuestionIndex] = {
                        ...newItems[currentSubQuestionIndex],
                        ai_assessment: assessResult,
                      };
                    }
                    newActivities[activityIndex] = {
                      ...newActivities[activityIndex],
                      items: newItems,
                    };
                  }
                  return newActivities;
                });

                // 結束評估狀態
                setIsAutoAssessing(false);
              } catch (assessError) {
                console.error("AI 評估失敗:", assessError);
                toast.error("AI 評估失敗，但錄音已保存");
                setIsAutoAssessing(false);
              }
            }
          } catch (error) {
            console.error("Failed to upload recording:", error);

            // 處理錯誤
            if (
              error instanceof TypeError &&
              error.message === "Failed to fetch"
            ) {
              console.error("Network error - cannot upload recording");
              toast.error("網絡連接失敗，無法上傳錄音");
            } else {
              toast.error("錄音上傳失敗，請稍後再試");
            }
          }
        } // End of if (!skipUpload)
      }; // End of recorder.onstop

      // Start recording
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0);

      // Start recording timer with 45 second limit
      let hasReachedLimit = false;
      recordingInterval.current = setInterval(() => {
        setRecordingTime((prev) => {
          const newTime = prev + 1;
          // Auto stop at 45 seconds
          if (newTime >= 45 && !hasReachedLimit) {
            hasReachedLimit = true;
            // Clear interval first to prevent further updates
            if (recordingInterval.current) {
              clearInterval(recordingInterval.current);
              recordingInterval.current = null;
            }
            // Stop recording after state update
            setTimeout(() => {
              if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop();
                setMediaRecorder(null);
                setIsRecording(false);
                toast.info("錄音已達 45 秒上限，自動停止");
              }
            }, 0);
            return 45; // Keep time at 45
          }
          return newTime;
        });
      }, 1000);
    } catch (error) {
      console.error("Failed to start recording:", error);
      toast.error("無法啟動錄音，請檢查麥克風權限");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setMediaRecorder(null);
      setIsRecording(false);

      if (recordingInterval.current) {
        clearInterval(recordingInterval.current);
        recordingInterval.current = null;
      }
    }
  };

  const reRecord = () => {
    const currentActivity = activities[currentActivityIndex];
    setAnswers((prev) => {
      const newAnswers = new Map(prev);
      const answer = newAnswers.get(currentActivity.id);
      if (answer) {
        answer.audioBlob = undefined;
        answer.audioUrl = undefined;
        answer.status = "in_progress";
      }
      newAnswers.set(currentActivity.id, answer!);
      return newAnswers;
    });
    startRecording();
  };

  // Format time display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Navigation - handles both activities and sub-questions
  const handleNextActivity = async () => {
    await autoSave();
    const currentActivity = activities[currentActivityIndex];

    // If current activity has sub-questions and we're not at the last one
    if (currentActivity.items && currentActivity.items.length > 0) {
      if (currentSubQuestionIndex < currentActivity.items.length - 1) {
        // Move to next sub-question
        setCurrentSubQuestionIndex(currentSubQuestionIndex + 1);
        setRecordingTime(0);
        return;
      }
    }

    // Move to next activity if available
    if (currentActivityIndex < activities.length - 1) {
      setCurrentActivityIndex(currentActivityIndex + 1);
      setCurrentSubQuestionIndex(0);
      setRecordingTime(0);
    }
  };

  const handlePreviousActivity = async () => {
    await autoSave();
    const currentActivity = activities[currentActivityIndex];

    // If current activity has sub-questions and we're not at the first one
    if (currentActivity.items && currentActivity.items.length > 0) {
      if (currentSubQuestionIndex > 0) {
        // Move to previous sub-question
        setCurrentSubQuestionIndex(currentSubQuestionIndex - 1);
        setRecordingTime(0);
        return;
      }
    }

    // Move to previous activity if available
    if (currentActivityIndex > 0) {
      const prevActivityIndex = currentActivityIndex - 1;
      const prevActivity = activities[prevActivityIndex];
      setCurrentActivityIndex(prevActivityIndex);

      // If previous activity has sub-questions, go to the last one
      if (prevActivity.items && prevActivity.items.length > 0) {
        setCurrentSubQuestionIndex(prevActivity.items.length - 1);
      } else {
        setCurrentSubQuestionIndex(0);
      }
      setRecordingTime(0);
    }
  };

  const handleActivitySelect = async (
    index: number,
    subQuestionIndex: number = 0,
  ) => {
    await autoSave();
    setCurrentActivityIndex(index);
    setCurrentSubQuestionIndex(subQuestionIndex); // Set to specific sub-question
    setRecordingTime(0);
  };

  // Auto-save functionality
  const autoSave = async (audioUrl?: string) => {
    if (!token || !assignmentId) return;

    try {
      setSaving(true);
      const currentActivity = activities[currentActivityIndex];
      const answer = answers.get(currentActivity.id);

      if (!answer || !currentActivity.id) return;

      const apiUrl = import.meta.env.VITE_API_URL || "";

      // Prepare save data based on activity type
      const saveData: Record<string, unknown> = {
        text_answer: answer.textAnswer,
        user_answers: answer.userAnswers, // For listening activities
      };

      // For activities with multiple items (grouped questions)
      if (currentActivity.items && currentActivity.items.length > 0) {
        // Save current item index and answers
        saveData.answers = answer.answers || [];
        saveData.item_index = currentSubQuestionIndex;
        // Note: recordings are now saved via upload-recording API, not here
      } else {
        // For single activities, save single audio_url
        saveData.audio_url = audioUrl || answer.audioUrl;
      }

      await fetch(
        `${apiUrl}/api/students/assignments/${assignmentId}/activities/${currentActivity.id}/save`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(saveData),
        },
      );

      console.log("Auto-saved activity progress");
    } catch (error) {
      console.error("Failed to auto-save:", error);
    } finally {
      setSaving(false);
    }
  };

  // Final submission
  const handleSubmit = async (e?: React.MouseEvent) => {
    console.log("🔥 [DEBUG] handleSubmit called in StudentActivityPage!");
    console.log("🔥 [DEBUG] Event:", e);

    // 防止預設行為和事件冒泡
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    const unanswered = Array.from(answers.values()).filter(
      (a) => a.status === "not_started",
    );

    if (unanswered.length > 0) {
      const confirm = window.confirm(
        `還有 ${unanswered.length} 題未作答，確定要提交嗎？`,
      );
      if (!confirm) {
        console.log("🔥 [DEBUG] User cancelled submission");
        return;
      }
    }

    try {
      console.log("🔥 [DEBUG] Starting submission...");
      setSubmitting(true);
      const apiUrl = import.meta.env.VITE_API_URL || "";
      console.log(
        "🔥 [DEBUG] Calling API:",
        `${apiUrl}/api/students/assignments/${assignmentId}/submit`,
      );

      const response = await fetch(
        `${apiUrl}/api/students/assignments/${assignmentId}/submit`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      );

      console.log("🔥 [DEBUG] API Response status:", response.status);

      if (!response.ok) {
        throw new Error("Failed to submit assignment");
      }

      toast.success("作業提交成功！");
      console.log(
        "🔥 [DEBUG] Submission successful, redirecting to detail page...",
      );

      // 使用 window.location.href 確保完全重新載入並跳轉到正確的 detail 頁面
      setTimeout(() => {
        const detailUrl = `/student/assignment/${assignmentId}/detail`;
        console.log("🔥 [DEBUG] Redirecting to:", detailUrl);
        window.location.href = detailUrl;
      }, 500);
    } catch (error) {
      console.error("🔥 [DEBUG] Failed to submit:", error);
      toast.error("提交失敗，請稍後再試");
    } finally {
      setSubmitting(false);
    }
  };

  // Get status display
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

  // Get activity type badge
  const getActivityTypeBadge = (type: string) => {
    switch (type) {
      case "reading_assessment":
        return <Badge variant="outline">朗讀錄音</Badge>;
      case "listening_cloze":
        return <Badge variant="outline">聽力填空</Badge>;
      case "speaking_practice":
        return <Badge variant="outline">口說練習</Badge>;
      case "speaking_scenario":
        return <Badge variant="outline">情境對話</Badge>;
      case "sentence_making":
        return <Badge variant="outline">造句練習</Badge>;
      case "speaking_quiz":
        return <Badge variant="outline">口說測驗</Badge>;
      default:
        return <Badge variant="outline">學習活動</Badge>;
    }
  };

  // 🔧 Memoize callback to prevent re-renders
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

  // Render activity content based on type
  const renderActivityContent = (activity: Activity) => {
    const answer = answers.get(activity.id);

    // Check if activity has multiple items (grouped questions)
    if (activity.items && activity.items.length > 0) {
      // Extract AI assessments from items and format for GroupedQuestionsTemplate
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
            // 🔥 傳遞完整的詳細分析資料
            word_details: item.ai_assessment.word_details || [],
            detailed_words: item.ai_assessment.detailed_words || [],
            reference_text: item.ai_assessment.reference_text || "",
            recognized_text: item.ai_assessment.recognized_text || "",
            analysis_summary: item.ai_assessment.analysis_summary || {},
          };
        }
      });

      // Use the extracted AI assessments if available, otherwise fallback to activity.ai_scores
      const assessmentResults =
        Object.keys(aiAssessments).length > 0
          ? { items: aiAssessments }
          : activity.ai_scores;

      return (
        <GroupedQuestionsTemplate
          items={activity.items}
          // answers={activity.answers} // 目前未使用
          currentQuestionIndex={currentSubQuestionIndex}
          isRecording={isRecording}
          recordingTime={recordingTime}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          onUpdateItemRecording={(index, url) =>
            handleUpdateItemRecording(activity.id, index, url)
          }
          formatTime={formatTime}
          progressId={activity.id}
          progressIds={answer?.progressIds}
          initialAssessmentResults={assessmentResults}
          readOnly={isReadOnly}
          externalIsAssessing={isAutoAssessing}
        />
      );
    }

    switch (activity.type) {
      case "reading_assessment":
        return (
          <ReadingAssessmentTemplate
            content={activity.content}
            targetText={activity.target_text}
            audioUrl={answer?.audioUrl}
            isRecording={isRecording}
            recordingTime={recordingTime}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onReRecord={reRecord}
            formatTime={formatTime}
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
        // 這些活動類型目前已禁用
        return (
          <div className="text-center p-8 text-gray-500">
            <p>此活動類型目前不可用</p>
          </div>
        );

      default:
        // Default to reading assessment template
        return (
          <ReadingAssessmentTemplate
            content={activity.content}
            targetText={activity.target_text || activity.content}
            audioUrl={answer?.audioUrl}
            isRecording={isRecording}
            recordingTime={recordingTime}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onReRecord={reRecord}
            formatTime={formatTime}
            progressId={activity.id}
            readOnly={isReadOnly}
          />
        );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="text-center">
          <div className="relative">
            {/* Outer ring */}
            <div className="absolute inset-0 animate-ping">
              <div className="h-16 w-16 rounded-full border-4 border-blue-200 opacity-75"></div>
            </div>
            {/* Inner spinning circle */}
            <Loader2 className="h-16 w-16 animate-spin text-blue-600 mx-auto relative" />
          </div>
          <p className="mt-6 text-lg font-medium text-gray-700">
            載入作業中...
          </p>
          <p className="mt-2 text-sm text-gray-500">
            請稍候，正在準備您的學習內容
          </p>
        </div>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">此作業尚無題目</p>
          <Button
            onClick={() =>
              navigate(`/student/assignment/${assignmentId}/detail`)
            }
          >
            返回作業詳情
          </Button>
        </div>
      </div>
    );
  }

  const currentActivity = activities[currentActivityIndex];
  const progress = ((currentActivityIndex + 1) / activities.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* 唯讀模式提示 */}
      {isReadOnly && (
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
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0 mb-2">
            <div className="flex items-center gap-2 sm:gap-3 min-w-0">
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  navigate(`/student/assignment/${assignmentId}/detail`)
                }
                className="flex-shrink-0 px-2 sm:px-3"
              >
                <ChevronLeft className="h-3 w-3 sm:h-4 sm:w-4 mr-1" />
                <span className="hidden sm:inline">返回作業</span>
                <span className="sm:hidden">返回</span>
              </Button>
              <div className="h-4 sm:h-6 w-px bg-gray-300 flex-shrink-0" />
              <h1 className="text-sm sm:text-base font-semibold truncate min-w-0">
                {assignmentTitle}
              </h1>
            </div>

            <div className="flex items-center gap-2 sm:gap-3 justify-end">
              {saving && (
                <div className="flex items-center gap-1 sm:gap-2 text-xs text-gray-600">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span className="hidden sm:inline">自動儲存中...</span>
                  <span className="sm:hidden">儲存中</span>
                </div>
              )}
              {!isReadOnly && (
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
                      <span className="hidden sm:inline">提交中...</span>
                      <span className="sm:hidden">提交</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-3 w-3 mr-1" />
                      <span className="hidden sm:inline">提交作業</span>
                      <span className="sm:hidden">提交</span>
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>

          {/* Activity navigation - Mobile-optimized horizontal scrolling */}
          <div className="flex gap-2 sm:gap-4 overflow-x-auto pb-2 scrollbar-hide">
            {activities.map((activity, activityIndex) => {
              const answer = answers.get(activity.id);
              const isActiveActivity = activityIndex === currentActivityIndex;

              // If activity has items, show them as sub-questions
              if (activity.items && activity.items.length > 0) {
                return (
                  <div
                    key={activity.id}
                    className="flex items-center gap-1 sm:gap-2 flex-shrink-0"
                  >
                    {/* Content title - Compact for mobile */}
                    <div className="flex items-center gap-1">
                      <span className="text-xs font-medium text-gray-600 whitespace-nowrap max-w-[80px] sm:max-w-none truncate sm:truncate-none">
                        {activity.title}
                      </span>
                      <Badge
                        variant="outline"
                        className="text-xs px-1 py-0 h-4 sm:h-5 min-w-[30px] text-center"
                      >
                        {activity.items.length}題
                      </Badge>
                    </div>

                    {/* Question buttons - Smaller on mobile */}
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

                        // 判斷狀態
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
                              if (activityIndex !== currentActivityIndex) {
                                handleActivitySelect(activityIndex, itemIndex);
                              } else {
                                setCurrentSubQuestionIndex(itemIndex);
                              }
                            }}
                            className={cn(
                              "relative w-6 h-6 sm:w-8 sm:h-8 rounded border transition-all",
                              "flex items-center justify-center text-xs font-medium",
                              "min-w-[24px] sm:min-w-[32px]", // Ensure minimum width
                              // 老師批改的顏色優先級最高
                              needsCorrection
                                ? "bg-red-100 text-red-800 border-red-400" // 老師批改未通過 - 紅色
                                : isTeacherPassed
                                  ? "bg-green-100 text-green-800 border-green-400" // 老師批改通過 - 綠色
                                  : isCompleted
                                    ? "bg-yellow-100 text-yellow-800 border-yellow-400" // 學生已完成但未批改 - 黃色
                                    : "bg-white text-gray-600 border-gray-300 hover:border-blue-400", // 未作答 - 白色
                              // 當前選中的題目用粗邊框
                              isActiveItem && "border-2 border-blue-600",
                            )}
                            title={needsCorrection ? "需要訂正" : ""}
                          >
                            {itemIndex + 1}
                          </button>
                        );
                      })}
                    </div>

                    {/* Separator between content groups */}
                    {activityIndex < activities.length - 1 && (
                      <div className="w-px h-8 bg-gray-300 ml-2" />
                    )}
                  </div>
                );
              }

              // For activities without items, show single button
              return (
                <Button
                  key={activity.id}
                  variant={isActiveActivity ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleActivitySelect(activityIndex)}
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

          {/* Overall progress */}
          <Progress value={progress} className="h-1 mt-1" />
        </div>
      </div>

      {/* Main content */}
      <div className="w-full px-2 sm:px-4 mt-3">
        <Card>
          <CardHeader className="py-2 sm:py-3">
            {/* Mobile: Stack title and buttons vertically */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 min-w-0">
                <CardTitle className="text-base sm:text-lg leading-tight">
                  第 {currentActivity.order} 題：{currentActivity.title}
                </CardTitle>
                {getActivityTypeBadge(currentActivity.type)}
              </div>

              {/* Navigation buttons - Mobile: horizontal layout */}
              <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePreviousActivity}
                  disabled={
                    currentActivityIndex === 0 && currentSubQuestionIndex === 0
                  }
                  className="flex-1 sm:flex-none min-w-0"
                >
                  <ChevronLeft className="h-3 w-3 sm:h-4 sm:w-4 mr-1" />
                  <span className="hidden sm:inline">上一題</span>
                  <span className="sm:hidden">上一題</span>
                </Button>

                {(() => {
                  // Check if it's the last activity
                  const isLastActivity =
                    currentActivityIndex === activities.length - 1;
                  const isLastSubQuestion = currentActivity.items
                    ? currentSubQuestionIndex ===
                      currentActivity.items.length - 1
                    : true;

                  if (isLastActivity && isLastSubQuestion) {
                    return (
                      <Button
                        variant="default"
                        size="sm"
                        onClick={handleSubmit}
                        disabled={submitting}
                        className="flex-1 sm:flex-none min-w-0"
                      >
                        <span className="hidden sm:inline">
                          {submitting ? "提交中..." : "提交作業"}
                        </span>
                        <span className="sm:hidden">
                          {submitting ? "提交中" : "提交"}
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
                      className="flex-1 sm:flex-none min-w-0"
                    >
                      <span className="hidden sm:inline">下一題</span>
                      <span className="sm:hidden">下一題</span>
                      <ChevronRight className="h-3 w-3 sm:h-4 sm:w-4 ml-1" />
                    </Button>
                  );
                })()}
              </div>
            </div>
          </CardHeader>

          <CardContent className="p-2 sm:p-3">
            {/* Render activity-specific content */}
            {renderActivityContent(currentActivity)}
          </CardContent>
        </Card>

        {/* Status summary - Mobile-optimized */}
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
                <p className="text-xs sm:text-sm text-gray-600">已完成</p>
              </div>
              <div>
                <div className="text-xl sm:text-2xl font-bold text-yellow-600">
                  {
                    Array.from(answers.values()).filter(
                      (a) => a.status === "in_progress",
                    ).length
                  }
                </div>
                <p className="text-xs sm:text-sm text-gray-600">進行中</p>
              </div>
              <div>
                <div className="text-xl sm:text-2xl font-bold text-gray-400">
                  {
                    Array.from(answers.values()).filter(
                      (a) => a.status === "not_started",
                    ).length
                  }
                </div>
                <p className="text-xs sm:text-sm text-gray-600">未開始</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
