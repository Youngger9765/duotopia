import AIScoreDisplay from './AIScoreDisplay';
import AIScoreDisplayEnhanced from './AIScoreDisplayEnhanced';

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

interface WordDetail {
  word: string;
  accuracy_score: number;
  error_type?: string;
}

interface DetailedWord extends WordDetail {
  index: number;
  syllables?: SyllableDetail[];
  phonemes?: PhonemeDetail[];
}

interface AIScores {
  accuracy_score?: number;
  fluency_score?: number;
  pronunciation_score?: number;
  completeness_score?: number;
  overall_score?: number;
  prosody_score?: number;
  word_details?: WordDetail[];
  detailed_words?: DetailedWord[];
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
}

interface AIScoreDisplayWrapperProps {
  scores?: AIScores;
  hasRecording?: boolean;
  title?: string;
  forceEnhanced?: boolean;
  forceSimple?: boolean;
}

/**
 * 智能選擇器：根據資料結構自動選擇適合的顯示組件
 * - 如果有 detailed_words，使用增強版
 * - 否則使用簡單版
 * - 可以通過 forceEnhanced 或 forceSimple 強制指定版本
 */
export default function AIScoreDisplayWrapper({
  scores,
  hasRecording = false,
  title = "AI 自動評分結果",
  forceEnhanced = false,
  forceSimple = false
}: AIScoreDisplayWrapperProps) {
  // 判斷是否有詳細資料
  const hasDetailedData = !!(
    scores?.detailed_words &&
    scores.detailed_words.length > 0 &&
    scores.detailed_words.some((w: DetailedWord) => w.phonemes || w.syllables)
  );

  // 決定使用哪個組件
  if (forceSimple) {
    return (
      <AIScoreDisplay
        scores={scores}
        hasRecording={hasRecording}
        title={title}
      />
    );
  }

  if (forceEnhanced || hasDetailedData) {
    return (
      <AIScoreDisplayEnhanced
        scores={scores}
        hasRecording={hasRecording}
        title={title}
        showDetailed={!forceSimple}
      />
    );
  }

  // 預設使用簡單版
  return (
    <AIScoreDisplay
      scores={scores}
      hasRecording={hasRecording}
      title={title}
    />
  );
}

// 導出所有版本供特定使用場景
export { AIScoreDisplay, AIScoreDisplayEnhanced };
