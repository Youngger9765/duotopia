import { Brain, Star } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

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
  syllables?: SyllableDetail[];
  phonemes?: PhonemeDetail[];
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
    low_score_phonemes: Array<{
      phoneme: string;
      score: number;
      in_word: string;
    }>;
  };
}

interface AIScoreDisplayProps {
  scores?: AIScores;
  hasRecording?: boolean;
  title?: string;
}

export default function AIScoreDisplay({
  scores,
  hasRecording = false,
  title = "AI 自動評分結果"
}: AIScoreDisplayProps) {
  if (!scores) return null;

  // Calculate overall score if not provided
  const overallScore = scores.overall_score ||
    Math.round(
      ((scores.accuracy_score || 0) +
       (scores.fluency_score || 0) +
       (scores.pronunciation_score || 0)) / 3
    );

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-600" />
          {title}
        </h4>
        {hasRecording && (
          <Badge className="bg-green-100 text-green-700">
            已錄製音檔
          </Badge>
        )}
      </div>

      {/* 總體分數 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* 總體發音 */}
        <div className="bg-white rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-purple-600">
            {Math.round(overallScore || 0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">總體發音</div>
        </div>

        {/* 準確度 */}
        <div className="bg-white rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-600">
            {Math.round(scores.accuracy_score || 0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">準確度</div>
        </div>

        {/* 流暢度 */}
        <div className="bg-white rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-600">
            {Math.round(scores.fluency_score || 0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">流暢度</div>
        </div>

        {/* 完整度 */}
        <div className="bg-white rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-orange-600">
            {Math.round(scores.completeness_score || scores.pronunciation_score || 0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">完整度</div>
        </div>
      </div>

      {/* 單字詳細評分 */}
      {scores.word_details && scores.word_details.length > 0 && (
        <div className="space-y-2">
          <h5 className="text-sm font-semibold text-gray-700 mb-2">單字發音詳情：</h5>
          <div className="flex flex-wrap gap-2">
            {scores.word_details.map((word, index) => {
              const score = word.accuracy_score || 0;
              const bgColor = score >= 80 ? 'bg-green-100' : score >= 60 ? 'bg-yellow-100' : 'bg-red-100';
              const borderColor = score >= 80 ? 'border-green-300' : score >= 60 ? 'border-yellow-300' : 'border-red-300';
              const textColor = score >= 80 ? 'text-green-800' : score >= 60 ? 'text-yellow-800' : 'text-red-800';

              return (
                <div
                  key={index}
                  className={cn(
                    "border rounded-lg px-3 py-1.5 text-sm font-medium",
                    bgColor,
                    borderColor,
                    textColor
                  )}
                  title={word.error_type || `準確度: ${score}`}
                >
                  <span className="font-semibold">{word.word}</span>
                  <span className="ml-2 text-xs opacity-80">({score})</span>
                  {word.error_type && word.error_type !== 'None' && (
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
            {(overallScore || 0) >= 80 ? (
              <span className="font-medium text-green-700">表現優秀！繼續保持這樣的發音水準。</span>
            ) : (overallScore || 0) >= 60 ? (
              <span className="font-medium text-yellow-700">不錯！注意準確度和流暢度的平衡。</span>
            ) : (
              <span className="font-medium text-red-700">需要更多練習，特別注意標示的單字發音。</span>
            )}
          </div>
        </div>
      </div>

      {/* AI 評語提示 */}
      <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-blue-700">
        💡 提示：AI 評分僅供參考，請根據學生實際表現進行最終評分
      </div>
    </div>
  );
}
