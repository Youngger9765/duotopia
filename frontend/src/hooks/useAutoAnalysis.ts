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
 * @param assignmentId 作業 ID
 * @param isPreviewMode 是否為預覽模式（預覽模式不上傳到 GCS）
 */
export function useAutoAnalysis(
  _assignmentId: number,
  isPreviewMode: boolean,
) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzingMessage, setAnalyzingMessage] = useState("");
  const { analyzePronunciation } = useAzurePronunciation();

  /**
   * 自動分析錄音並上傳（如果非預覽模式）
   *
   * @param blobUrl 錄音的 blob URL
   * @param targetText 參考文本
   * @param progressId StudentItemProgress ID（用於上傳）
   * @param contentItemId ContentItem ID（用於上傳）
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

      // 3. 非預覽模式且有 progressId：上傳到 GCS 並更新資料庫（包含 AI 分數）
      if (!isPreviewMode && progressId && contentItemId) {
        setAnalyzingMessage("正在上傳分析結果...");

        const formData = new FormData();

        // 檔案副檔名處理
        const uploadFileExtension = audioBlob.type.includes("mp4")
          ? "recording.mp4"
          : audioBlob.type.includes("webm")
            ? "recording.webm"
            : "recording.audio";
        formData.append("audio_file", audioBlob, uploadFileExtension);

        // Issue #141 Fix: 使用 /api/speech/upload-analysis 並包含 analysis_json
        // 這樣 AI 分數才會被正確儲存到資料庫
        formData.append(
          "analysis_json",
          JSON.stringify({
            pronunciation_score: azureResult.pronunciationScore,
            accuracy_score: azureResult.accuracyScore,
            fluency_score: azureResult.fluencyScore,
            completeness_score: azureResult.completenessScore,
            overall_score: azureResult.pronunciationScore, // 使用 pronunciation 作為 overall
          }),
        );

        // 使用 progress_id 而非 assignment_id + content_item_id
        formData.append("progress_id", progressId.toString());

        const apiUrl = import.meta.env.VITE_API_URL || "";
        const authToken = useStudentAuthStore.getState().token;

        await retryAudioUpload(
          async () => {
            const uploadResponse = await fetch(
              `${apiUrl}/api/speech/upload-analysis`,
              {
                method: "POST",
                headers: {
                  Authorization: `Bearer ${authToken}`,
                },
                body: formData,
              },
            );

            if (!uploadResponse.ok) {
              throw new Error(`Upload failed: ${uploadResponse.status}`);
            }

            return await uploadResponse.json();
          },
          (attempt, error) => {
            console.log(`自動上傳重試 (${attempt}):`, error);
          },
        );
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
