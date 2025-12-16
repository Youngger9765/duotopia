import { useState } from "react";
import { azureSpeechService } from "@/services/azureSpeechService";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";

// Azure SDK response type definitions
interface AzurePronunciationAssessment {
  AccuracyScore?: number;
  ErrorType?: string;
}

interface AzurePhoneme {
  Phoneme: string;
  PronunciationAssessment?: AzurePronunciationAssessment;
}

interface AzureSyllable {
  Syllable: string;
  PronunciationAssessment?: AzurePronunciationAssessment;
}

interface AzureWordData {
  Word: string;
  PronunciationAssessment?: AzurePronunciationAssessment;
  Syllables?: AzureSyllable[];
  Phonemes?: AzurePhoneme[];
}

interface AzurePrivPronJson {
  Words?: AzureWordData[];
}

interface AzureAnalysisResult {
  privPronJson?: AzurePrivPronJson;
  [key: string]: unknown;
}

interface PhonemeDetail {
  index: number;
  phoneme: string;
  accuracy_score: number;
}

interface SyllableDetail {
  index: number;
  syllable: string;
  accuracy_score: number;
}

interface DetailedWord {
  index: number;
  word: string;
  accuracy_score: number;
  error_type?: string;
  syllables?: SyllableDetail[];
  phonemes?: PhonemeDetail[];
}

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
        detailResult?: {
          NBest?: Array<{
            Words?: Array<{
              Word: string;
              PronunciationAssessment?: {
                AccuracyScore: number;
                ErrorType: string;
              };
              Syllables?: Array<{
                Syllable: string;
                PronunciationAssessment?: {
                  AccuracyScore: number;
                };
              }>;
              Phonemes?: Array<{
                Phoneme: string;
                PronunciationAssessment?: {
                  AccuracyScore: number;
                };
              }>;
            }>;
          }>;
        };
      };

      // Extract detailed words from Azure's privPronJson (which contains NBest data)
      const detailed_words: DetailedWord[] = [];
      const privPronJson = (analysisResult as unknown as AzureAnalysisResult)
        .privPronJson;

      // Azure SDK stores Words directly in privPronJson, not in NBest
      const wordsData = privPronJson?.Words || [];

      if (wordsData.length > 0) {
        wordsData.forEach((wordData: AzureWordData, idx: number) => {
          const word: DetailedWord = {
            index: idx,
            word: wordData.Word,
            accuracy_score:
              wordData.PronunciationAssessment?.AccuracyScore || 0,
            error_type: wordData.PronunciationAssessment?.ErrorType || "None",
            syllables: [],
            phonemes: [],
          };

          // Parse syllables
          if (wordData.Syllables) {
            word.syllables = wordData.Syllables.map(
              (syl: AzureSyllable, sylIdx: number) => ({
                index: sylIdx,
                syllable: syl.Syllable,
                accuracy_score: syl.PronunciationAssessment?.AccuracyScore || 0,
              }),
            );
          }

          // Parse phonemes
          if (wordData.Phonemes) {
            word.phonemes = wordData.Phonemes.map(
              (pho: AzurePhoneme, phoIdx: number) => ({
                index: phoIdx,
                phoneme: pho.Phoneme,
                accuracy_score: pho.PronunciationAssessment?.AccuracyScore || 0,
              }),
            );
          }

          detailed_words.push(word);
        });
      }

      // Collect low score phonemes for analysis summary
      const low_score_phonemes: Array<{
        phoneme: string;
        score: number;
        in_word: string;
      }> = [];

      detailed_words.forEach((word) => {
        word.phonemes?.forEach((phoneme) => {
          if (phoneme.accuracy_score < 70) {
            low_score_phonemes.push({
              phoneme: phoneme.phoneme,
              score: phoneme.accuracy_score,
              in_word: word.word,
            });
          }
        });
      });

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
          low_score_phonemes,
          assessment_time: new Date().toISOString(),
        },
      };

      setResult(pronunciationResult);
      setIsAnalyzing(false);

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
