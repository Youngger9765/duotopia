/**
 * WordReadingActivity - 單字朗讀練習活動容器
 *
 * Phase 2-2: 管理單字朗讀練習的完整流程
 *
 * 功能:
 * - 載入單字集的所有單字
 * - 管理練習進度
 * - 處理錄音上傳
 * - 顯示 AI 評估結果
 * - 提交作業
 */

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  ChevronLeft,
  ChevronRight,
  Loader2,
  Send,
  CheckCircle,
} from "lucide-react";
import { toast } from "sonner";
import WordReadingTemplate from "./WordReadingTemplate";
import { useTranslation } from "react-i18next";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { cn } from "@/lib/utils";
import { useAzurePronunciation } from "@/hooks/useAzurePronunciation";
import { retryAudioUpload } from "@/utils/retryHelper";

interface WordItem {
  id: number;
  text: string;
  translation?: string;
  audio_url?: string;
  image_url?: string;
  part_of_speech?: string;
  progress_id?: number;
  recording_url?: string;
  ai_assessment?: {
    accuracy_score?: number;
    fluency_score?: number;
    completeness_score?: number;
    pronunciation_score?: number;
  };
  teacher_feedback?: string;
  teacher_passed?: boolean;
  teacher_review_score?: number;
  review_status?: string;
}

interface WordReadingActivityProps {
  assignmentId: number;
  isPreviewMode?: boolean;
  isDemoMode?: boolean; // Demo mode - uses public demo API endpoints
  authToken?: string; // 認證 token（預覽模式用老師 token）
  showTranslation?: boolean;
  showImage?: boolean;
  onComplete?: () => void;
  canUseAiAnalysis?: boolean; // 教師/機構是否有 AI 分析額度
}

export default function WordReadingActivity({
  assignmentId,
  isPreviewMode = false,
  isDemoMode = false,
  authToken,
  showTranslation: _showTranslationProp = true, // 保留 prop 但使用 API 返回的值
  showImage: _showImageProp = true, // 保留 prop 但使用 API 返回的值
  onComplete,
  canUseAiAnalysis: canUseAiAnalysisProp,
}: WordReadingActivityProps) {
  const { t } = useTranslation();
  const { token: studentToken } = useStudentAuthStore();
  // 預覽模式使用傳入的 authToken（老師 token），否則使用學生 token
  const token = isPreviewMode && authToken ? authToken : studentToken;

  // State
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<WordItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [timeLimitPerQuestion, setTimeLimitPerQuestion] = useState(0); // 0 = 不限時
  // 從 API 讀取的顯示設定（解決圖片不顯示的 bug）
  const [showImageFromApi, setShowImageFromApi] = useState(true);
  const [showTranslationFromApi, setShowTranslationFromApi] = useState(true);
  // AI 分析額度（從 API 讀取，或使用 prop 傳入的值）
  const [canUseAiAnalysisFromApi, setCanUseAiAnalysisFromApi] = useState(true);
  const canUseAiAnalysis = canUseAiAnalysisProp ?? canUseAiAnalysisFromApi;
  const { analyzePronunciation } = useAzurePronunciation();

  // Load vocabulary items from backend
  const loadItems = useCallback(async () => {
    try {
      setLoading(true);
      const apiUrl = import.meta.env.VITE_API_URL || "";

      // 根據模式選擇不同的端點
      const endpoint = isDemoMode
        ? `${apiUrl}/api/demo/assignments/${assignmentId}/preview/vocabulary/activities`
        : isPreviewMode
          ? `${apiUrl}/api/teachers/assignments/${assignmentId}/preview/vocabulary/activities`
          : `${apiUrl}/api/students/assignments/${assignmentId}/vocabulary/activities`;

      const response = await fetch(endpoint, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load vocabulary items: ${response.status}`);
      }

      const data = await response.json();
      setItems(data.items || []);
      setTimeLimitPerQuestion(data.time_limit_per_question || 0);
      // 讀取 API 返回的顯示設定
      setShowImageFromApi(data.show_image ?? true);
      setShowTranslationFromApi(data.show_translation ?? true);
      setCanUseAiAnalysisFromApi(data.can_use_ai_analysis ?? true);

      // Find first incomplete item
      const firstIncomplete = (data.items || []).findIndex(
        (item: WordItem) => !item.recording_url,
      );
      if (firstIncomplete >= 0) {
        setCurrentIndex(firstIncomplete);
      }
    } catch (error) {
      console.error("Error loading vocabulary items:", error);
      toast.error(
        t("wordReading.toast.loadFailed") || "Failed to load vocabulary items",
      );
    } finally {
      setLoading(false);
    }
  }, [assignmentId, token, isPreviewMode, isDemoMode, t]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  // Handle recording complete
  const handleRecordingComplete = async (blob: Blob, url: string) => {
    const currentItem = items[currentIndex];

    // Update local state immediately
    setItems((prev) => {
      const updated = [...prev];
      updated[currentIndex] = {
        ...updated[currentIndex],
        recording_url: url,
      };
      return updated;
    });

    // Skip upload in preview mode or demo mode
    if (isPreviewMode || isDemoMode) {
      toast.success(
        t("wordReading.toast.recordedPreview") ||
          "Recording saved (preview mode)",
      );
      return;
    }

    // Upload to server
    try {
      setUploading(true);
      const apiUrl = import.meta.env.VITE_API_URL || "";

      const formData = new FormData();
      formData.append("assignment_id", assignmentId.toString());
      formData.append("content_item_id", currentItem.id.toString());

      const uploadFileExtension = blob.type.includes("mp4")
        ? "recording.mp4"
        : blob.type.includes("webm")
          ? "recording.webm"
          : "recording.audio";
      formData.append("audio_file", blob, uploadFileExtension);

      const response = await fetch(`${apiUrl}/api/students/upload-recording`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const result = await response.json();

      // Update with server URL
      setItems((prev) => {
        const updated = [...prev];
        updated[currentIndex] = {
          ...updated[currentIndex],
          recording_url: result.audio_url,
          progress_id: result.progress_id,
        };
        return updated;
      });

      toast.success(t("wordReading.toast.uploaded") || "Recording uploaded");

      // 🎯 Issue #227: 上傳成功後，有額度時自動背景分析
      if (canUseAiAnalysis && currentItem.text) {
        (async () => {
          try {
            const azureResult = await analyzePronunciation(
              blob,
              currentItem.text,
            );
            if (!azureResult) return;

            const assessment = {
              accuracy_score: azureResult.accuracyScore,
              fluency_score: azureResult.fluencyScore,
              completeness_score: azureResult.completenessScore,
              pronunciation_score: azureResult.pronunciationScore,
            };

            setItems((prev) => {
              const updated = [...prev];
              updated[currentIndex] = {
                ...updated[currentIndex],
                ai_assessment: assessment,
              };
              return updated;
            });

            // 儲存到後端
            if (result.progress_id) {
              fetch(
                `${apiUrl}/api/students/assignments/${assignmentId}/vocabulary/save-assessment`,
                {
                  method: "POST",
                  headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({
                    progress_id: result.progress_id,
                    ai_assessment: assessment,
                  }),
                },
              ).catch((err) =>
                console.error("Save assessment failed:", err),
              );

              // 上傳分析結果（含配額扣除）
              const analysisForm = new FormData();
              analysisForm.append("audio_file", blob, uploadFileExtension);
              analysisForm.append(
                "analysis_json",
                JSON.stringify({
                  pronunciation_score: azureResult.pronunciationScore,
                  accuracy_score: azureResult.accuracyScore,
                  fluency_score: azureResult.fluencyScore,
                  completeness_score: azureResult.completenessScore,
                  overall_score: azureResult.pronunciationScore,
                }),
              );
              analysisForm.append(
                "progress_id",
                result.progress_id.toString(),
              );
              analysisForm.append("analysis_id", crypto.randomUUID());

              fetch(`${apiUrl}/api/speech/upload-analysis`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: analysisForm,
              }).catch((err) =>
                console.error("Upload analysis failed:", err),
              );
            }
          } catch (err) {
            console.error("Background analysis after upload failed:", err);
          }
        })();
      }
    } catch (error) {
      console.error("Upload error:", error);
      toast.error(t("wordReading.toast.uploadFailed") || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  // Handle assessment complete
  const handleAssessmentComplete = async (result: {
    overallScore: number;
    accuracyScore: number;
    fluencyScore: number;
    completenessScore: number;
    pronunciationScore: number;
  }) => {
    const currentItem = items[currentIndex];

    // Update local state
    setItems((prev) => {
      const updated = [...prev];
      updated[currentIndex] = {
        ...updated[currentIndex],
        ai_assessment: {
          accuracy_score: result.accuracyScore,
          fluency_score: result.fluencyScore,
          completeness_score: result.completenessScore,
          pronunciation_score: result.pronunciationScore,
        },
      };
      return updated;
    });

    // Save to server (skip in preview and demo mode)
    if (!isPreviewMode && !isDemoMode && currentItem.progress_id) {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || "";

        await fetch(
          `${apiUrl}/api/students/assignments/${assignmentId}/vocabulary/save-assessment`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              progress_id: currentItem.progress_id,
              ai_assessment: {
                accuracy_score: result.accuracyScore,
                fluency_score: result.fluencyScore,
                completeness_score: result.completenessScore,
                pronunciation_score: result.pronunciationScore,
              },
            }),
          },
        );
      } catch (error) {
        console.error("Failed to save assessment:", error);
      }
    }
  };

  // Navigate to next item
  const handleNext = () => {
    // 🎯 Issue #227: 切換到下一題時，背景分析當前未分析的題目
    if (canUseAiAnalysis && !isPreviewMode && !isDemoMode) {
      const currentItem = items[currentIndex];
      const hasRecording =
        currentItem?.recording_url && currentItem.recording_url !== "";
      if (hasRecording && !currentItem?.ai_assessment && currentItem.text) {
        // fire-and-forget：背景分析不阻塞導航
        (async () => {
          try {
            const resp = await fetch(currentItem.recording_url!);
            const audioBlob = await resp.blob();
            const azureResult = await analyzePronunciation(
              audioBlob,
              currentItem.text,
            );
            if (!azureResult) return;

            const assessment = {
              accuracy_score: azureResult.accuracyScore,
              fluency_score: azureResult.fluencyScore,
              completeness_score: azureResult.completenessScore,
              pronunciation_score: azureResult.pronunciationScore,
            };

            setItems((prev) => {
              const updated = [...prev];
              updated[currentIndex] = {
                ...updated[currentIndex],
                ai_assessment: assessment,
              };
              return updated;
            });

            // 儲存到後端
            const apiUrl = import.meta.env.VITE_API_URL || "";
            if (currentItem.progress_id) {
              fetch(
                `${apiUrl}/api/students/assignments/${assignmentId}/vocabulary/save-assessment`,
                {
                  method: "POST",
                  headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({
                    progress_id: currentItem.progress_id,
                    ai_assessment: assessment,
                  }),
                },
              ).catch((err) =>
                console.error("Save assessment failed:", err),
              );

              // 上傳分析結果（含配額扣除）
              const ext = audioBlob.type.includes("mp4")
                ? "recording.mp4"
                : audioBlob.type.includes("webm")
                  ? "recording.webm"
                  : "recording.audio";
              const analysisForm = new FormData();
              analysisForm.append("audio_file", audioBlob, ext);
              analysisForm.append(
                "analysis_json",
                JSON.stringify({
                  pronunciation_score: azureResult.pronunciationScore,
                  accuracy_score: azureResult.accuracyScore,
                  fluency_score: azureResult.fluencyScore,
                  completeness_score: azureResult.completenessScore,
                  overall_score: azureResult.pronunciationScore,
                }),
              );
              analysisForm.append(
                "progress_id",
                currentItem.progress_id.toString(),
              );
              analysisForm.append("analysis_id", crypto.randomUUID());

              fetch(`${apiUrl}/api/speech/upload-analysis`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: analysisForm,
              }).catch((err) =>
                console.error("Upload analysis failed:", err),
              );
            }
          } catch (err) {
            console.error("Background analysis on next failed:", err);
          }
        })();
      }
    }

    if (currentIndex < items.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  // Navigate to previous item
  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  // Handle skip
  const handleSkip = () => {
    handleNext();
  };

  // Submit assignment
  const handleSubmit = async () => {
    if (isPreviewMode || isDemoMode) {
      toast.info(
        t("wordReading.toast.cannotSubmitPreview") ||
          "Cannot submit in preview mode",
      );
      return;
    }

    // Check for incomplete items
    const incompleteCount = items.filter((item) => !item.recording_url).length;
    if (incompleteCount > 0) {
      toast.warning(
        t("wordReading.toast.incompleteItems", { count: incompleteCount }) ||
          `${incompleteCount} items not recorded`,
      );
      return;
    }

    try {
      setSubmitting(true);
      const apiUrl = import.meta.env.VITE_API_URL || "";

      // 🎯 Issue #227: 提交前確保所有 blob URL 上傳到 GCS
      const blobItems = items
        .map((item, index) => ({ item, index }))
        .filter(({ item }) => item.recording_url?.startsWith("blob:"));

      if (blobItems.length > 0) {
        for (const { item, index } of blobItems) {
          try {
            const resp = await fetch(item.recording_url!);
            const audioBlob = await resp.blob();
            const ext = audioBlob.type.includes("mp4")
              ? "recording.mp4"
              : audioBlob.type.includes("webm")
                ? "recording.webm"
                : "recording.audio";

            const formData = new FormData();
            formData.append("assignment_id", assignmentId.toString());
            formData.append("content_item_id", item.id.toString());
            formData.append("audio_file", audioBlob, ext);

            const uploadResult = await retryAudioUpload(
              async () => {
                const uploadResp = await fetch(
                  `${apiUrl}/api/students/upload-recording`,
                  {
                    method: "POST",
                    headers: { Authorization: `Bearer ${token}` },
                    body: formData,
                  },
                );
                if (!uploadResp.ok)
                  throw new Error(`Upload failed: ${uploadResp.status}`);
                return await uploadResp.json();
              },
              () => {},
            );

            setItems((prev) => {
              const updated = [...prev];
              updated[index] = {
                ...updated[index],
                recording_url: uploadResult.audio_url,
                progress_id: uploadResult.progress_id,
              };
              return updated;
            });
          } catch (error) {
            console.error(`Failed to upload blob for item ${index + 1}:`, error);
          }
        }
      }

      // 🎯 Issue #227: 提交前補分析所有有錄音但未分析的題目
      if (canUseAiAnalysis) {
        const unanalyzedItems = items
          .map((item, index) => ({ item, index }))
          .filter(
            ({ item }) =>
              item.recording_url &&
              item.recording_url !== "" &&
              !item.ai_assessment,
          );

        if (unanalyzedItems.length > 0) {
          for (const { item, index } of unanalyzedItems) {
            try {
              const audioResp = await fetch(item.recording_url!);
              const audioBlob = await audioResp.blob();

              const azureResult = await analyzePronunciation(
                audioBlob,
                item.text,
              );
              if (!azureResult) continue;

              const assessment = {
                accuracy_score: azureResult.accuracyScore,
                fluency_score: azureResult.fluencyScore,
                completeness_score: azureResult.completenessScore,
                pronunciation_score: azureResult.pronunciationScore,
              };

              // 更新本地 state
              setItems((prev) => {
                const updated = [...prev];
                updated[index] = {
                  ...updated[index],
                  ai_assessment: assessment,
                };
                return updated;
              });

              // 儲存分析結果到後端
              if (item.progress_id) {
                await fetch(
                  `${apiUrl}/api/students/assignments/${assignmentId}/vocabulary/save-assessment`,
                  {
                    method: "POST",
                    headers: {
                      Authorization: `Bearer ${token}`,
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                      progress_id: item.progress_id,
                      ai_assessment: assessment,
                    }),
                  },
                ).catch((err) =>
                  console.error("Save assessment failed:", err),
                );

                // 上傳分析結果（含配額扣除）
                const ext = audioBlob.type.includes("mp4")
                  ? "recording.mp4"
                  : audioBlob.type.includes("webm")
                    ? "recording.webm"
                    : "recording.audio";

                const analysisForm = new FormData();
                analysisForm.append("audio_file", audioBlob, ext);
                analysisForm.append(
                  "analysis_json",
                  JSON.stringify({
                    pronunciation_score: azureResult.pronunciationScore,
                    accuracy_score: azureResult.accuracyScore,
                    fluency_score: azureResult.fluencyScore,
                    completeness_score: azureResult.completenessScore,
                    overall_score: azureResult.pronunciationScore,
                  }),
                );
                analysisForm.append(
                  "progress_id",
                  item.progress_id.toString(),
                );
                analysisForm.append("analysis_id", crypto.randomUUID());

                fetch(`${apiUrl}/api/speech/upload-analysis`, {
                  method: "POST",
                  headers: { Authorization: `Bearer ${token}` },
                  body: analysisForm,
                }).catch((err) =>
                  console.error("Upload analysis failed:", err),
                );
              }
            } catch (error) {
              console.error(
                `Failed to analyze item ${index + 1}:`,
                error,
              );
            }
          }
        }
      }

      // 提交作業
      const response = await fetch(
        `${apiUrl}/api/students/assignments/${assignmentId}/vocabulary/submit`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Submit failed: ${response.status}`);
      }

      toast.success(t("wordReading.toast.submitted") || "Assignment submitted");
      onComplete?.();
    } catch (error) {
      console.error("Submit error:", error);
      toast.error(t("wordReading.toast.submitFailed") || "Submit failed");
    } finally {
      setSubmitting(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <Card className="p-8">
        <CardContent className="flex flex-col items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
          <p className="text-gray-600">
            {t("wordReading.loading") || "Loading vocabulary items..."}
          </p>
        </CardContent>
      </Card>
    );
  }

  // No items
  if (items.length === 0) {
    return (
      <Card className="p-8">
        <CardContent className="text-center">
          <p className="text-gray-600">
            {t("wordReading.noItems") || "No vocabulary items found"}
          </p>
        </CardContent>
      </Card>
    );
  }

  const currentItem = items[currentIndex];
  const completedCount = items.filter((item) => item.recording_url).length;
  const progress = (completedCount / items.length) * 100;
  const isLastItem = currentIndex === items.length - 1;
  const allCompleted = completedCount === items.length;

  return (
    <div className="space-y-6">
      {/* Progress Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            {t("wordReading.wordReading") || "Word Reading"}
          </Badge>
          <span className="text-sm text-gray-600">
            {t("wordReading.itemProgress", {
              current: currentIndex + 1,
              total: items.length,
            }) || `${currentIndex + 1} / ${items.length}`}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <CheckCircle className="h-4 w-4 text-green-500" />
          <span>
            {t("wordReading.completedCount", { count: completedCount }) ||
              `${completedCount} completed`}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <Progress value={progress} className="h-2" />

      {/* Item Navigation Dots */}
      <div className="flex gap-1 flex-wrap justify-center">
        {items.map((item, index) => {
          const isActive = index === currentIndex;
          const isCompleted = !!item.recording_url;
          const hasAssessment = !!item.ai_assessment;

          return (
            <button
              key={item.id}
              onClick={() => setCurrentIndex(index)}
              className={cn(
                "w-8 h-8 rounded border transition-all flex items-center justify-center text-xs font-medium",
                isActive && "border-2 border-blue-600",
                hasAssessment
                  ? "bg-green-100 text-green-800 border-green-400"
                  : isCompleted
                    ? "bg-yellow-100 text-yellow-800 border-yellow-400"
                    : "bg-white text-gray-600 border-gray-300 hover:border-blue-400",
              )}
              title={
                hasAssessment
                  ? t("wordReading.assessed") || "Assessed"
                  : isCompleted
                    ? t("wordReading.recorded") || "Recorded"
                    : t("wordReading.notRecorded") || "Not recorded"
              }
            >
              {index + 1}
            </button>
          );
        })}
      </div>

      {/* Word Reading Template */}
      <WordReadingTemplate
        currentItem={currentItem}
        currentIndex={currentIndex}
        totalItems={items.length}
        showTranslation={showTranslationFromApi}
        showImage={showImageFromApi}
        existingAudioUrl={currentItem.recording_url}
        onRecordingComplete={handleRecordingComplete}
        progressId={currentItem.progress_id}
        readOnly={false}
        isDemoMode={isDemoMode}
        timeLimit={timeLimitPerQuestion}
        onSkip={handleSkip}
        onAssessmentComplete={handleAssessmentComplete}
        canUseAiAnalysis={canUseAiAnalysisProp ?? canUseAiAnalysisFromApi}
      />

      {/* Navigation Buttons */}
      <div className="flex items-center justify-center gap-4 pt-4 border-t">
        <Button
          variant="outline"
          onClick={handlePrevious}
          disabled={currentIndex === 0 || uploading}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          {t("wordReading.previous") || "Previous"}
        </Button>

        {isLastItem && allCompleted ? (
          <Button
            onClick={handleSubmit}
            disabled={submitting || uploading}
            className="bg-green-600 hover:bg-green-700"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                {t("wordReading.submitting") || "Submitting..."}
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-1" />
                {t("wordReading.submit") || "Submit"}
              </>
            )}
          </Button>
        ) : (
          <Button
            variant="outline"
            onClick={handleNext}
            disabled={currentIndex === items.length - 1 || uploading}
          >
            {t("wordReading.next") || "Next"}
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        )}
      </div>
    </div>
  );
}
