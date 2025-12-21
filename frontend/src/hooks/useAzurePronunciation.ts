import { useState } from "react";
import { azureSpeechService } from "@/services/azureSpeechService";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";

// Azure SDK response type definitions
// 🎯 Issue #118: 簡化類型定義，移除 Phoneme/Syllable 層級（加快分析速度）
interface AzurePronunciationAssessment {
  AccuracyScore?: number;
  ErrorType?: string;
}

interface AzureWordData {
  Word: string;
  PronunciationAssessment?: AzurePronunciationAssessment;
}

interface AzurePrivPronJson {
  Words?: AzureWordData[];
}

interface AzureAnalysisResult {
  privPronJson?: AzurePrivPronJson;
  [key: string]: unknown;
}

// 🎯 Issue #118: 簡化 DetailedWord，只保留 Word 層級資訊
interface DetailedWord {
  index: number;
  word: string;
  accuracy_score: number;
  error_type?: string;
}

// 🎯 Issue #118: Upload status for retry mechanism
export type UploadStatus = "success" | "pending_retry" | "failed";

interface PronunciationResult {
  pronunciationScore: number;
  accuracyScore: number;
  fluencyScore: number;
  completenessScore: number;
  words?: Array<{
    word: string;
    accuracyScore: number;
    errorType: string;
  }>;
  detailed_words?: DetailedWord[];
  // 🎯 Issue #118: 簡化 analysis_summary，移除 low_score_phonemes
  analysis_summary?: {
    total_words: number;
    problematic_words: string[];
    assessment_time?: string;
  };
  // 🎯 Issue #118: Upload status tracking for retry mechanism
  uploadStatus?: UploadStatus;
  uploadId?: string;
}

export function useAzurePronunciation() {
  const { t } = useTranslation();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<PronunciationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  /**
   * Analyze pronunciation using Azure Speech Service
   * @param audioBlob - The recorded audio blob
   * @param referenceText - The reference text to compare against
   * @returns The analysis result or null if failed
   */
  const analyzePronunciation = async (
    audioBlob: Blob,
    referenceText: string,
  ): Promise<PronunciationResult | null> => {
    setIsAnalyzing(true);
    setError(null);

    try {
      // Call Azure Speech Service directly - fast!
      const { result: analysisResult, latencyMs } =
        await azureSpeechService.analyzePronunciation(audioBlob, referenceText);

      // Convert Azure result to our format
      // 🎯 Issue #118: 簡化類型，只保留 Word 層級
      const azureResult = analysisResult as unknown as {
        pronunciationScore: number;
        accuracyScore: number;
        fluencyScore: number;
        completenessScore: number;
        words?: Array<{
          word: string;
          accuracyScore: number;
          errorType: string;
        }>;
      };

      // 🎯 Issue #118: 簡化解析邏輯，只處理 Word 層級（不解析 Syllables/Phonemes）
      const detailed_words: DetailedWord[] = [];
      const privPronJson = (analysisResult as unknown as AzureAnalysisResult)
        .privPronJson;

      // Azure SDK stores Words directly in privPronJson
      const wordsData = privPronJson?.Words || [];

      if (wordsData.length > 0) {
        wordsData.forEach((wordData: AzureWordData, idx: number) => {
          detailed_words.push({
            index: idx,
            word: wordData.Word,
            accuracy_score:
              wordData.PronunciationAssessment?.AccuracyScore || 0,
            error_type: wordData.PronunciationAssessment?.ErrorType || "None",
          });
        });
      }

      // 🎯 Issue #118: Upload with retry mechanism (non-blocking)
      const uploadResult = await azureSpeechService.uploadWithRetry(
        audioBlob,
        analysisResult,
        latencyMs,
      );

      const pronunciationResult: PronunciationResult = {
        pronunciationScore: azureResult.pronunciationScore,
        accuracyScore: azureResult.accuracyScore,
        fluencyScore: azureResult.fluencyScore,
        completenessScore: azureResult.completenessScore,
        words: azureResult.words,
        detailed_words: detailed_words.length > 0 ? detailed_words : undefined,
        analysis_summary: {
          total_words: detailed_words.length,
          problematic_words: detailed_words
            .filter((w) => w.accuracy_score < 80)
            .map((w) => w.word),
          assessment_time: new Date().toISOString(),
        },
        // 🎯 Issue #118: Track upload status
        uploadStatus: uploadResult.success ? "success" : "pending_retry",
        uploadId: uploadResult.uploadId,
      };

      setResult(pronunciationResult);
      setIsAnalyzing(false);

      return pronunciationResult;
    } catch (err) {
      console.error("Pronunciation analysis failed:", err);
      const errorMessage =
        err instanceof Error ? err.message : t("errors.analysisFailedRetry");

      setError(errorMessage);
      setIsAnalyzing(false);

      toast.error(t("errors.analysisFailed"), {
        description: errorMessage,
      });

      return null;
    }
  };

  /**
   * Reset the analysis state
   */
  const reset = () => {
    setResult(null);
    setError(null);
    setIsAnalyzing(false);
  };

  return {
    isAnalyzing,
    result,
    error,
    analyzePronunciation,
    reset,
  };
}
