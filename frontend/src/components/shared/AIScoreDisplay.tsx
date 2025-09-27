import { Brain, Star, AlertCircle, Mic } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

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
    assessment_time?: string;
  };
}

interface AIScoreDisplayEnhancedProps {
  scores?: AIScores;
  hasRecording?: boolean;
  title?: string;
  showDetailed?: boolean;
}

export default function AIScoreDisplay({
  scores,
  hasRecording = false,
  title = "AI 自動評分結果",
  showDetailed = true
}: AIScoreDisplayEnhancedProps) {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'detailed' | 'phoneme'>('overview');

  if (!scores) return null;

  // 使用詳細資料（如果有）或舊版資料
  const wordsToDisplay = scores.detailed_words || scores.word_details || [];
  const hasDetailedData = !!(scores.detailed_words && scores.detailed_words.length > 0);

  // Calculate overall score if not provided
  const overallScore = scores.overall_score ||
    Math.round(
      ((scores.accuracy_score || 0) +
       (scores.fluency_score || 0) +
       (scores.pronunciation_score || 0)) / 3
    );

  // 評分門檻
  const thresholds = {
    word: 80,
    syllable: 75,
    phoneme: 70
  };

  // 評分顏色
  const getScoreColor = (score: number, type: 'word' | 'syllable' | 'phoneme' = 'word') => {
    const threshold = thresholds[type];
    if (score >= threshold) return { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300' };
    if (score >= threshold * 0.75) return { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-300' };
    return { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300' };
  };

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-600" />
          {title}
        </h4>
        <div className="flex gap-2">
          {hasRecording && (
            <Badge className="bg-green-100 text-green-700">
              <Mic className="w-3 h-3 mr-1" />
              已錄製
            </Badge>
          )}
          {hasDetailedData && (
            <Badge className="bg-blue-100 text-blue-700">
              詳細分析
            </Badge>
          )}
        </div>
      </div>

      {/* 總體分數 */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
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

        {/* 韻律（如果有） */}
        {scores.prosody_score !== undefined && (
          <div className="bg-white rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-indigo-600">
              {Math.round(scores.prosody_score)}
            </div>
            <div className="text-xs text-gray-600 mt-1">韻律</div>
          </div>
        )}
      </div>

      {/* 文本對比（如果有） */}
      {scores.reference_text && scores.recognized_text && (
        <Card className="mb-4 p-3">
          <div className="space-y-2">
            <div>
              <span className="text-xs font-medium text-gray-600">參考文本：</span>
              <p className="text-sm text-gray-800">{scores.reference_text}</p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-600">識別文本：</span>
              <p className="text-sm text-gray-800">{scores.recognized_text}</p>
            </div>
          </div>
        </Card>
      )}

      {/* 切換視圖標籤 */}
      {showDetailed && hasDetailedData && (
        <Tabs value={selectedTab} onValueChange={(v) => setSelectedTab(v as 'overview' | 'detailed' | 'phoneme')} className="mb-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">總覽</TabsTrigger>
            <TabsTrigger value="detailed">詳細分析</TabsTrigger>
            <TabsTrigger value="phoneme">音素層級</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-4">
            {/* 單字總覽 */}
            <div className="space-y-2">
              <h5 className="text-sm font-semibold text-gray-700">單字發音詳情：</h5>
              <div className="flex flex-wrap gap-2">
                {wordsToDisplay.map((word, index) => {
                  const score = word.accuracy_score || 0;
                  const colors = getScoreColor(score, 'word');

                  return (
                    <div
                      key={index}
                      className={cn(
                        "border rounded-lg px-3 py-1.5 text-sm font-medium",
                        colors.bg,
                        colors.border,
                        colors.text
                      )}
                      title={word.error_type || `準確度: ${score}`}
                    >
                      <span className="font-semibold">{word.word}</span>
                      <span className="ml-2 text-xs opacity-80">({Math.round(score)})</span>
                      {word.error_type && word.error_type !== 'None' && (
                        <span className="ml-1 text-xs">⚠️</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="detailed" className="mt-4 space-y-3">
            {/* Word → Syllable → Phoneme 鑽取視圖 */}
            <Accordion type="single" collapsible className="w-full">
              {scores.detailed_words?.map((word) => (
                <AccordionItem key={word.index} value={`word-${word.index}`}>
                  <AccordionTrigger className="hover:no-underline">
                    <div className="flex items-center justify-between w-full pr-2">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{word.word}</span>
                        <Badge
                          variant={word.accuracy_score >= thresholds.word ? 'default' : 'destructive'}
                          className="text-xs"
                        >
                          {Math.round(word.accuracy_score)}
                        </Badge>
                        {word.error_type && word.error_type !== 'None' && (
                          <Badge variant="outline" className="text-xs">
                            {word.error_type}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-3 pl-4">
                      {/* 音節分析 */}
                      {word.syllables && word.syllables.length > 0 && (
                        <div>
                          <div className="text-xs font-medium text-gray-600 mb-2">音節分析：</div>
                          <div className="flex flex-wrap gap-2">
                            {word.syllables.map(syllable => {
                              const colors = getScoreColor(syllable.accuracy_score, 'syllable');
                              return (
                                <Badge
                                  key={syllable.index}
                                  className={cn("text-xs", colors.bg, colors.text)}
                                >
                                  {syllable.syllable}: {Math.round(syllable.accuracy_score)}
                                </Badge>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* 音素分析 */}
                      {word.phonemes && word.phonemes.length > 0 && (
                        <div>
                          <div className="text-xs font-medium text-gray-600 mb-2">音素分析：</div>
                          <div className="flex flex-wrap gap-1">
                            {word.phonemes.map(phoneme => {
                              const score = phoneme.accuracy_score;
                              const colors = getScoreColor(score, 'phoneme');

                              return (
                                <div
                                  key={phoneme.index}
                                  className={cn(
                                    "px-2 py-1 rounded text-xs font-mono",
                                    colors.bg,
                                    colors.text
                                  )}
                                  title={`音素: ${phoneme.phoneme}, 分數: ${Math.round(score)}`}
                                >
                                  /{phoneme.phoneme}/ {Math.round(score)}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </TabsContent>

          <TabsContent value="phoneme" className="mt-4">
            {/* 音素層級總覽 */}
            <div className="space-y-4">
              {/* 低分音素 */}
              {scores.analysis_summary?.low_score_phonemes && scores.analysis_summary.low_score_phonemes.length > 0 && (
                <Card className="p-3">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-orange-600 mt-0.5" />
                    <div className="space-y-2 flex-1">
                      <div className="text-sm font-medium text-orange-800">需要加強的音素：</div>
                      <div className="space-y-1">
                        {scores.analysis_summary.low_score_phonemes.map((item, idx) => (
                          <div key={idx} className="flex items-center justify-between text-xs">
                            <span className="font-mono">/{item.phoneme}/</span>
                            <span className="text-gray-600">在 "{item.in_word}" 中</span>
                            <Badge variant="destructive" className="text-xs">
                              {Math.round(item.score)}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              )}

              {/* 所有音素列表 */}
              <div>
                <h5 className="text-sm font-semibold text-gray-700 mb-2">所有音素評分：</h5>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {scores.detailed_words?.map(word =>
                    word.phonemes?.map(phoneme => {
                      const colors = getScoreColor(phoneme.accuracy_score, 'phoneme');
                      return (
                        <div
                          key={`${word.index}-${phoneme.index}`}
                          className={cn(
                            "flex items-center justify-between p-2 rounded text-xs",
                            colors.bg
                          )}
                        >
                          <span className={cn("font-mono", colors.text)}>
                            /{phoneme.phoneme}/
                          </span>
                          <span className={cn("font-bold", colors.text)}>
                            {Math.round(phoneme.accuracy_score)}
                          </span>
                        </div>
                      );
                    })
                  ).flat().filter(Boolean)}
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      )}

      {/* 簡單視圖（當沒有詳細資料時） */}
      {(!showDetailed || !hasDetailedData) && wordsToDisplay.length > 0 && (
        <div className="space-y-2">
          <h5 className="text-sm font-semibold text-gray-700">單字發音詳情：</h5>
          <div className="flex flex-wrap gap-2">
            {wordsToDisplay.map((word, index) => {
              const score = word.accuracy_score || 0;
              const colors = getScoreColor(score, 'word');

              return (
                <div
                  key={index}
                  className={cn(
                    "border rounded-lg px-3 py-1.5 text-sm font-medium",
                    colors.bg,
                    colors.border,
                    colors.text
                  )}
                  title={word.error_type || `準確度: ${score}`}
                >
                  <span className="font-semibold">{word.word}</span>
                  <span className="ml-2 text-xs opacity-80">({Math.round(score)})</span>
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
            {overallScore >= 80 ? (
              <span className="font-medium text-green-700">
                表現優秀！繼續保持這樣的發音水準。
                {scores.analysis_summary?.problematic_words?.length === 0 && " 所有單字都發音正確！"}
              </span>
            ) : overallScore >= 60 ? (
              <span className="font-medium text-yellow-700">
                不錯！注意準確度和流暢度的平衡。
                {scores.analysis_summary?.problematic_words && scores.analysis_summary.problematic_words.length > 0 && (
                  <span> 特別注意：{scores.analysis_summary.problematic_words.join('、')}</span>
                )}
              </span>
            ) : (
              <span className="font-medium text-red-700">
                需要更多練習，特別注意標示的單字發音。
                {scores.analysis_summary?.low_score_phonemes && scores.analysis_summary.low_score_phonemes.length > 0 && (
                  <span> 重點加強音素：{scores.analysis_summary.low_score_phonemes.slice(0, 3).map(p => `/${p.phoneme}/`).join('、')}</span>
                )}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* AI 評語提示 */}
      <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-blue-700">
        💡 提示：AI 評分僅供參考，請根據學生實際表現進行最終評分
        {hasDetailedData && " | 🎯 點擊單字查看詳細音素分析"}
      </div>
    </div>
  );
}
