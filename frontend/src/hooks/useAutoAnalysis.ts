import { useState } from "react";
import { useAzurePronunciation } from "@/hooks/useAzurePronunciation";
import { retryAudioUpload } from "@/utils/retryHelper";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { toast } from "sonner";

/**
 * Issue #141: 例句朗讀自動分析 Hook
 *
 * 當學生點擊題號跳題時，如果當前題目有錄音但未分析，自動觸發 Azure 分析
 *
 * @param assignmentId 作業 ID（用於上傳錄音時建立 progress 記錄）
 * @param isPreviewMode 是否為預覽模式（預覽模式不上傳到 GCS）
 */
export function useAutoAnalysis(assignmentId: number, isPreviewMode: boolean) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzingMessage, setAnalyzingMessage] = useState("");
  const { analyzePronunciation } = useAzurePronunciation();

  /**
   * 自動分析錄音並上傳（如果非預覽模式）
   *
   * Issue #141 Fix:
   * - 如果有 progressId：直接使用 /api/speech/upload-analysis 上傳分析結果
   * - 如果沒有 progressId：先上傳錄音取得 progressId，再上傳分析結果
   *
   * @param blobUrl 錄音的 blob URL
   * @param targetText 參考文本
   * @param progressId StudentItemProgress ID（用於上傳，可選）
   * @param contentItemId ContentItem ID（用於建立 progress 記錄）
   * @returns 分析結果，失敗時返回 null
   */
  const analyzeAndUpload = async (
    blobUrl: string,
    targetText: string,
    progressId?: number,
    contentItemId?: number,
  ) => {
    setIsAnalyzing(true);
    setAnalyzingMessage("正在分析錄音...");

    try {
      // 1. 從 blob URL 取得音檔
      const response = await fetch(blobUrl);
      const audioBlob = await response.blob();

      // 2. 呼叫 Azure 分析
      const azureResult = await analyzePronunciation(audioBlob, targetText);

      if (!azureResult) {
        throw new Error("Azure 分析失敗");
      }

      // 3. 非預覽模式且有 contentItemId：上傳到 GCS 並更新資料庫（包含 AI 分數）
      if (!isPreviewMode && contentItemId) {
        setAnalyzingMessage("正在上傳分析結果...");

        const apiUrl = import.meta.env.VITE_API_URL || "";
        const authToken = useStudentAuthStore.getState().token;

        // 檔案副檔名處理
        const uploadFileExtension = audioBlob.type.includes("mp4")
          ? "recording.mp4"
          : audioBlob.type.includes("webm")
            ? "recording.webm"
            : "recording.audio";

        let currentProgressId = progressId;

        // Issue #141 Fix: 如果沒有 progressId，先上傳錄音取得 progressId
        if (!currentProgressId) {
          console.log(
            "No progressId, uploading recording first to get progressId...",
          );

          const uploadFormData = new FormData();
          uploadFormData.append("assignment_id", assignmentId.toString());
          uploadFormData.append("content_item_id", contentItemId.toString());
          uploadFormData.append("audio_file", audioBlob, uploadFileExtension);

          const uploadResult = await retryAudioUpload(
            async () => {
              const uploadResponse = await fetch(
                `${apiUrl}/api/students/upload-recording`,
                {
                  method: "POST",
                  headers: {
                    Authorization: `Bearer ${authToken}`,
                  },
                  body: uploadFormData,
                },
              );

              if (!uploadResponse.ok) {
                throw new Error(
                  `Upload recording failed: ${uploadResponse.status}`,
                );
              }

              return await uploadResponse.json();
            },
            (attempt, error) => {
              console.log(`錄音上傳重試 (${attempt}):`, error);
            },
          );

          currentProgressId = uploadResult?.progress_id;
          console.log("Got progressId from upload:", currentProgressId);
        }

        if (!currentProgressId) {
          throw new Error("無法取得 progress_id，無法儲存分析結果");
        }

        // 使用 /api/speech/upload-analysis 上傳分析結果
        const analysisFormData = new FormData();
        analysisFormData.append("audio_file", audioBlob, uploadFileExtension);
        analysisFormData.append(
          "analysis_json",
          JSON.stringify({
            pronunciation_score: azureResult.pronunciationScore,
            accuracy_score: azureResult.accuracyScore,
            fluency_score: azureResult.fluencyScore,
            completeness_score: azureResult.completenessScore,
            overall_score: azureResult.pronunciationScore,
          }),
        );
        analysisFormData.append("progress_id", currentProgressId.toString());

        // 🎯 Issue #208: Generate unique analysis_id for deduction
        const analysisId = crypto.randomUUID();
        analysisFormData.append("analysis_id", analysisId);

        await retryAudioUpload(
          async () => {
            const uploadResponse = await fetch(
              `${apiUrl}/api/speech/upload-analysis`,
              {
                method: "POST",
                headers: {
                  Authorization: `Bearer ${authToken}`,
                },
                body: analysisFormData,
              },
            );

            if (!uploadResponse.ok) {
              throw new Error(
                `Upload analysis failed: ${uploadResponse.status}`,
              );
            }

            return await uploadResponse.json();
          },
          (attempt, error) => {
            console.log(`分析結果上傳重試 (${attempt}):`, error);
          },
        );

        console.log("✅ Analysis result uploaded successfully");
      }

      // 4. 回傳分析結果
      return {
        accuracy_score: azureResult.accuracyScore,
        fluency_score: azureResult.fluencyScore,
        completeness_score: azureResult.completenessScore,
        pronunciation_score: azureResult.pronunciationScore,
        prosody_score: 0, // Azure 不提供此項
        word_details: azureResult.words?.map((w) => ({
          word: w.word,
          accuracy_score: w.accuracyScore,
          error_type: w.errorType,
        })),
        detailed_words: azureResult.detailed_words,
        reference_text: targetText,
        recognized_text: "", // Azure 結果中可能沒有此項
        analysis_summary: azureResult.analysis_summary,
      };
    } catch (error) {
      console.error("自動分析失敗:", error);
      toast.error("自動分析失敗", {
        description: error instanceof Error ? error.message : "請稍後重試",
      });
      return null;
    } finally {
      setIsAnalyzing(false);
      setAnalyzingMessage("");
    }
  };

  return {
    isAnalyzing,
    analyzingMessage,
    analyzeAndUpload,
  };
}
