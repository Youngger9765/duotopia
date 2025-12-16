import { useState } from "react";
import { azureSpeechService } from "@/services/azureSpeechService";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";

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

      const pronunciationResult: PronunciationResult = {
        pronunciationScore: azureResult.pronunciationScore,
        accuracyScore: azureResult.accuracyScore,
        fluencyScore: azureResult.fluencyScore,
        completenessScore: azureResult.completenessScore,
        words: azureResult.words,
      };

      setResult(pronunciationResult);
      setIsAnalyzing(false);

      // Log latency in development
      if (import.meta.env.DEV) {
        console.log(`✅ Azure Speech analysis completed in ${latencyMs}ms`);
      }

      // Background upload - non-blocking
      azureSpeechService.uploadAnalysisInBackground(
        audioBlob,
        analysisResult,
        latencyMs,
      );

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
