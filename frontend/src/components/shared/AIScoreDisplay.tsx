import { Star } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "react-i18next";

// 🎯 Issue #118: 簡化類型定義，移除 Phoneme/Syllable 層級
interface WordDetail {
  word: string;
  accuracy_score: number;
  error_type?: string;
}

interface DetailedWord extends WordDetail {
  index: number;
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
    assessment_time?: string;
  };
}

interface AIScoreDisplayEnhancedProps {
  scores?: AIScores;
  hasRecording?: boolean;
  title?: string;
  showDetailed?: boolean;
  isStudentView?: boolean; // 🔧 Issue #118: 控制是否為學生視角（隱藏 AI 提示）
}

export default function AIScoreDisplay({
  scores,
  showDetailed = true,
  isStudentView = false, // 預設為老師視角
}: AIScoreDisplayEnhancedProps) {
  const { t } = useTranslation();

  if (!scores) return null;

  // 使用詳細資料（如果有）或舊版資料
  const wordsToDisplay = scores.detailed_words || scores.word_details || [];

  // Calculate overall score if not provided
  const overallScore =
    scores.overall_score ||
    Math.round(
      ((scores.accuracy_score || 0) +
        (scores.fluency_score || 0) +
        (scores.pronunciation_score || 0)) /
        3,
    );

  // 評分門檻
  const threshold = 80;

  // 評分顏色
  const getScoreColor = (score: number) => {
    if (score >= threshold)
      return {
        bg: "bg-green-100",
        text: "text-green-700",
        border: "border-green-300",
      };
    if (score >= threshold * 0.75)
      return {
        bg: "bg-yellow-100",
        text: "text-yellow-700",
        border: "border-yellow-300",
      };
    return { bg: "bg-red-100", text: "text-red-700", border: "border-red-300" };
  };

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200 shadow-lg">
      {/* 總體分數 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {/* 總體發音 */}
        <div className="bg-white rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-purple-600">
            {Math.round(overallScore || 0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {t("aiScoreDisplay.scores.overall")}
          </div>
        </div>

        {/* 準確度 */}
        <div className="bg-white rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-600">
            {Math.round(scores.accuracy_score || 0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {t("aiScoreDisplay.scores.accuracy")}
          </div>
        </div>

        {/* 流暢度 */}
        <div className="bg-white rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-600">
            {Math.round(scores.fluency_score || 0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {t("aiScoreDisplay.scores.fluency")}
          </div>
        </div>

        {/* 完整度 */}
        <div className="bg-white rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-orange-600">
            {Math.round(
              scores.completeness_score || scores.pronunciation_score || 0,
            )}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {t("aiScoreDisplay.scores.completeness")}
          </div>
        </div>
      </div>

      {/* 🔧 Issue #118: 移除 tabs，直接顯示單字發音詳情 */}
      {showDetailed && wordsToDisplay.length > 0 && (
        <div className="space-y-2">
          <h5 className="text-sm font-semibold text-gray-700">
            {t("aiScoreDisplay.sections.wordDetails")}
          </h5>
          <div className="flex flex-wrap gap-2">
            {wordsToDisplay.map((word, index) => {
              const score = word.accuracy_score || 0;
              const colors = getScoreColor(score);

              return (
                <div
                  key={index}
                  className={cn(
                    "border rounded-lg px-3 py-1.5 text-sm font-medium",
                    colors.bg,
                    colors.border,
                    colors.text,
                  )}
                  title={
                    word.error_type ||
                    t("aiScoreDisplay.labels.accuracyLabel", { score })
                  }
                >
                  <span className="font-semibold">{word.word}</span>
                  <span className="ml-2 text-xs opacity-80">
                    ({Math.round(score)})
                  </span>
                  {word.error_type && word.error_type !== "None" && (
                    <span className="ml-1 text-xs">⚠️</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 建議區域 */}
      <div className="mt-4 pt-4 border-t border-purple-200">
        <div className="flex items-start gap-2">
          <Star className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-gray-700">
            {overallScore >= 80 ? (
              <span className="font-medium text-green-700">
                {t("aiScoreDisplay.feedback.excellent")}
                {scores.analysis_summary?.problematic_words?.length === 0 &&
                  ` ${t("aiScoreDisplay.feedback.excellentPerfect")}`}
              </span>
            ) : overallScore >= 60 ? (
              <span className="font-medium text-yellow-700">
                {t("aiScoreDisplay.feedback.good")}
                {scores.analysis_summary?.problematic_words &&
                  scores.analysis_summary.problematic_words.length > 0 && (
                    <span>
                      {" "}
                      {t("aiScoreDisplay.feedback.goodFocus", {
                        words:
                          scores.analysis_summary.problematic_words.join("、"),
                      })}
                    </span>
                  )}
              </span>
            ) : (
              <span className="font-medium text-red-700">
                {t("aiScoreDisplay.feedback.needsPractice")}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 🔧 Issue #118: AI 提示只在老師端顯示，學生端不需要 */}
      {!isStudentView && (
        <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-blue-700">
          {t("aiScoreDisplay.hints.aiReference")}
        </div>
      )}
    </div>
  );
}
