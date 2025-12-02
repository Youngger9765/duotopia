/**
 * RearrangementActivity - 例句重組練習組件
 *
 * 功能：
 * - 顯示打散的單字，學生依序點選組成正確句子
 * - 即時計分：每個單字 floor(100/字數) 分
 * - 錯誤限制：<=10字 3次, 11-25字 5次
 * - 可選音檔播放（聽力模式）
 * - 計時功能
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Loader2,
  Volume2,
  Clock,
  CheckCircle,
  XCircle,
  RotateCcw,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "react-i18next";

interface RearrangementQuestion {
  content_item_id: number;
  shuffled_words: string[];
  word_count: number;
  max_errors: number;
  time_limit: number;
  play_audio: boolean;
  audio_url?: string;
  translation?: string;
}

interface RearrangementActivityProps {
  studentAssignmentId: number;
  onComplete?: (totalScore: number, totalQuestions: number) => void;
  isPreviewMode?: boolean;
}

interface QuestionState {
  selectedWords: string[]; // 已選擇的單字（按順序）
  remainingWords: string[]; // 剩餘可選的單字
  errorCount: number;
  expectedScore: number;
  completed: boolean;
  challengeFailed: boolean;
  timeRemaining: number;
}

const RearrangementActivity: React.FC<RearrangementActivityProps> = ({
  studentAssignmentId,
  onComplete,
  isPreviewMode = false,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<RearrangementQuestion[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [questionStates, setQuestionStates] = useState<Map<number, QuestionState>>(new Map());
  const [submitting, setSubmitting] = useState(false);
  const [scoreCategory, setScoreCategory] = useState<string>("writing");
  const [totalScore, setTotalScore] = useState(0);
  const [, setCompletedQuestions] = useState(0);

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // 載入題目
  useEffect(() => {
    loadQuestions();
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [studentAssignmentId]);

  const loadQuestions = async () => {
    try {
      setLoading(true);
      // 根據是否為預覽模式選擇不同的 API
      const apiUrl = isPreviewMode
        ? `/api/teachers/assignments/${studentAssignmentId}/preview/rearrangement-questions`
        : `/api/students/assignments/${studentAssignmentId}/rearrangement-questions`;

      const response = await apiClient.get<{
        student_assignment_id: number;
        practice_mode: string;
        score_category: string;
        questions: RearrangementQuestion[];
        total_questions: number;
      }>(apiUrl);

      setQuestions(response.questions);
      setScoreCategory(response.score_category || "writing");

      // 初始化每題狀態
      const initialStates = new Map<number, QuestionState>();
      response.questions.forEach((q) => {
        initialStates.set(q.content_item_id, {
          selectedWords: [],
          remainingWords: [...q.shuffled_words],
          errorCount: 0,
          expectedScore: 100,
          completed: false,
          challengeFailed: false,
          timeRemaining: q.time_limit,
        });
      });
      setQuestionStates(initialStates);

      // 開始計時
      if (response.questions.length > 0) {
        startTimer(response.questions[0].content_item_id);
      }
    } catch (error) {
      console.error("Failed to load rearrangement questions:", error);
      toast.error(t("rearrangement.errors.loadFailed"));
    } finally {
      setLoading(false);
    }
  };

  const startTimer = (contentItemId: number) => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    timerRef.current = setInterval(() => {
      setQuestionStates((prev) => {
        const newStates = new Map(prev);
        const state = newStates.get(contentItemId);
        if (state && !state.completed && !state.challengeFailed) {
          const newTime = state.timeRemaining - 1;
          if (newTime <= 0) {
            // 時間到，自動完成
            handleTimeout(contentItemId);
            return prev; // timeout handler 會更新狀態
          }
          newStates.set(contentItemId, {
            ...state,
            timeRemaining: newTime,
          });
        }
        return newStates;
      });
    }, 1000);
  };

  const handleTimeout = async (contentItemId: number) => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    // 取得目前狀態（在 try 之前取得，避免變數重複宣告）
    const currentState = questionStates.get(contentItemId);

    try {
      // 根據是否為預覽模式選擇不同的 API
      const completeUrl = isPreviewMode
        ? `/api/teachers/assignments/${studentAssignmentId}/preview/rearrangement-complete`
        : `/api/students/assignments/${studentAssignmentId}/rearrangement-complete`;

      await apiClient.post(completeUrl, {
        content_item_id: contentItemId,
        timeout: true,
        expected_score: currentState?.expectedScore || 0,
      });

      setQuestionStates((prev) => {
        const newStates = new Map(prev);
        const stateInMap = newStates.get(contentItemId);
        if (stateInMap) {
          newStates.set(contentItemId, {
            ...stateInMap,
            completed: true,
            timeRemaining: 0,
          });
        }
        return newStates;
      });

      toast.warning(t("rearrangement.messages.timeout"));

      // 計算並更新分數
      if (currentState) {
        setTotalScore((prev) => prev + Math.max(0, currentState.expectedScore));
        setCompletedQuestions((prev) => prev + 1);
      }
    } catch (error) {
      console.error("Failed to complete on timeout:", error);
    }
  };

  const handleWordSelect = async (word: string) => {
    const currentQuestion = questions[currentQuestionIndex];
    const currentState = questionStates.get(currentQuestion.content_item_id);

    if (!currentState || currentState.completed || currentState.challengeFailed || submitting) {
      return;
    }

    setSubmitting(true);

    try {
      // 根據是否為預覽模式選擇不同的 API
      const answerUrl = isPreviewMode
        ? `/api/teachers/assignments/${studentAssignmentId}/preview/rearrangement-answer`
        : `/api/students/assignments/${studentAssignmentId}/rearrangement-answer`;

      const response = await apiClient.post<{
        is_correct: boolean;
        correct_word?: string;
        error_count: number;
        max_errors: number;
        expected_score: number;
        correct_word_count: number;
        total_word_count: number;
        challenge_failed: boolean;
        completed: boolean;
      }>(answerUrl, {
        content_item_id: currentQuestion.content_item_id,
        selected_word: word,
        current_position: currentState.selectedWords.length,
        // 預覽模式需要傳遞目前的 error_count（因為後端不存儲狀態）
        error_count: isPreviewMode ? currentState.errorCount : undefined,
      });

      // 更新狀態
      setQuestionStates((prev) => {
        const newStates = new Map(prev);
        const state = newStates.get(currentQuestion.content_item_id)!;

        let newSelectedWords = [...state.selectedWords];
        let newRemainingWords = [...state.remainingWords];

        if (response.is_correct) {
          // 正確：加入已選擇列表，從剩餘移除
          newSelectedWords.push(word);
          newRemainingWords = newRemainingWords.filter((w, i) => {
            // 只移除第一個匹配的
            if (w === word) {
              newRemainingWords.splice(i, 1);
              return false;
            }
            return true;
          });
          // 重新過濾（因為上面的邏輯可能有問題）
          const firstIndex = state.remainingWords.indexOf(word);
          if (firstIndex !== -1) {
            newRemainingWords = [...state.remainingWords];
            newRemainingWords.splice(firstIndex, 1);
          }
        }

        newStates.set(currentQuestion.content_item_id, {
          ...state,
          selectedWords: newSelectedWords,
          remainingWords: newRemainingWords,
          errorCount: response.error_count,
          expectedScore: response.expected_score,
          completed: response.completed,
          challengeFailed: response.challenge_failed,
        });

        return newStates;
      });

      // 顯示回饋
      if (response.is_correct) {
        // 正確時不顯示 toast，用 UI 顯示
      } else {
        toast.error(t("rearrangement.messages.incorrect", { correct: response.correct_word }));
      }

      // 檢查是否完成或失敗
      if (response.completed) {
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
        setTotalScore((prev) => prev + response.expected_score);
        setCompletedQuestions((prev) => prev + 1);
        toast.success(t("rearrangement.messages.questionComplete", { score: Math.round(response.expected_score) }));
      } else if (response.challenge_failed) {
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
        toast.error(t("rearrangement.messages.challengeFailed"));
      }
    } catch (error) {
      console.error("Failed to submit answer:", error);
      toast.error(t("rearrangement.errors.submitFailed"));
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = async () => {
    const currentQuestion = questions[currentQuestionIndex];

    try {
      setSubmitting(true);

      // 根據是否為預覽模式選擇不同的 API
      const retryUrl = isPreviewMode
        ? `/api/teachers/assignments/${studentAssignmentId}/preview/rearrangement-retry`
        : `/api/students/assignments/${studentAssignmentId}/rearrangement-retry`;

      await apiClient.post(retryUrl, {
        content_item_id: currentQuestion.content_item_id,
      });

      // 重置狀態
      setQuestionStates((prev) => {
        const newStates = new Map(prev);
        newStates.set(currentQuestion.content_item_id, {
          selectedWords: [],
          remainingWords: [...currentQuestion.shuffled_words],
          errorCount: 0,
          expectedScore: 100,
          completed: false,
          challengeFailed: false,
          timeRemaining: currentQuestion.time_limit,
        });
        return newStates;
      });

      // 重新開始計時
      startTimer(currentQuestion.content_item_id);
      toast.info(t("rearrangement.messages.retryStarted"));
    } catch (error) {
      console.error("Failed to retry:", error);
      toast.error(t("rearrangement.errors.retryFailed"));
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      const nextIndex = currentQuestionIndex + 1;
      setCurrentQuestionIndex(nextIndex);
      startTimer(questions[nextIndex].content_item_id);

      // 播放音檔（如果需要）
      if (questions[nextIndex].play_audio && questions[nextIndex].audio_url) {
        playAudio(questions[nextIndex].audio_url!);
      }
    } else {
      // 所有題目完成
      if (onComplete) {
        onComplete(totalScore, questions.length);
      }
      toast.success(t("rearrangement.messages.allComplete", {
        score: Math.round(totalScore),
        total: questions.length * 100,
      }));
    }
  };

  const playAudio = useCallback((url: string) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    audioRef.current = new Audio(url);
    audioRef.current.play().catch((e) => {
      console.error("Failed to play audio:", e);
    });
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Loading 狀態
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600 mb-4" />
        <p className="text-gray-600">{t("rearrangement.loading")}</p>
      </div>
    );
  }

  // 沒有題目
  if (questions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <p className="text-gray-600 mb-4">{t("rearrangement.noQuestions")}</p>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const currentState = questionStates.get(currentQuestion.content_item_id);

  if (!currentState) {
    return null;
  }

  const isLowTime = currentState.timeRemaining <= 10;
  const progressPercent = ((currentQuestionIndex + (currentState.completed ? 1 : 0)) / questions.length) * 100;

  return (
    <div className="rearrangement-activity space-y-4">
      {/* 進度與統計 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <Badge variant="outline">
            {t("rearrangement.progress", {
              current: currentQuestionIndex + 1,
              total: questions.length,
            })}
          </Badge>
          <Badge variant="secondary" className={cn(
            scoreCategory === "listening" && "bg-purple-100 text-purple-800",
            scoreCategory === "writing" && "bg-green-100 text-green-800",
            scoreCategory === "speaking" && "bg-blue-100 text-blue-800",
          )}>
            {scoreCategory === "listening" && t("rearrangement.scoreCategories.listening")}
            {scoreCategory === "writing" && t("rearrangement.scoreCategories.writing")}
            {scoreCategory === "speaking" && t("rearrangement.scoreCategories.speaking")}
          </Badge>
        </div>
        <div className="text-sm text-gray-600">
          {t("rearrangement.totalScore")}: <span className="font-bold text-blue-600">{Math.round(totalScore)}</span>
        </div>
      </div>

      <Progress value={progressPercent} className="h-2" />

      {/* 題目卡片 */}
      <Card className="mt-4">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">
              {t("rearrangement.questionTitle", { number: currentQuestionIndex + 1 })}
            </CardTitle>
            <div className="flex items-center gap-3">
              {/* 計時器 */}
              <div className={cn(
                "flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium",
                isLowTime ? "bg-red-100 text-red-700 animate-pulse" : "bg-gray-100 text-gray-700"
              )}>
                <Clock className="h-4 w-4" />
                {formatTime(currentState.timeRemaining)}
              </div>

              {/* 音檔按鈕 */}
              {currentQuestion.play_audio && currentQuestion.audio_url && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => playAudio(currentQuestion.audio_url!)}
                  disabled={submitting}
                >
                  <Volume2 className="h-4 w-4 mr-1" />
                  {t("rearrangement.playAudio")}
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* 翻譯提示（如果有且不是聽力模式） */}
          {currentQuestion.translation && !currentQuestion.play_audio && (
            <div className="p-3 bg-blue-50 rounded-lg text-blue-800 text-sm">
              <span className="font-medium">{t("rearrangement.hint")}:</span> {currentQuestion.translation}
            </div>
          )}

          {/* 錯誤計數 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {Array.from({ length: currentQuestion.max_errors }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "w-3 h-3 rounded-full",
                    i < currentState.errorCount ? "bg-red-500" : "bg-gray-200"
                  )}
                />
              ))}
              <span className="text-sm text-gray-500 ml-2">
                {t("rearrangement.errorsRemaining", {
                  remaining: currentQuestion.max_errors - currentState.errorCount,
                })}
              </span>
            </div>
            <div className="text-sm">
              {t("rearrangement.expectedScore")}: <span className="font-bold">{Math.round(currentState.expectedScore)}</span>
            </div>
          </div>

          {/* 已選擇的單字（句子構建區） */}
          <div className="min-h-[60px] p-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            {currentState.selectedWords.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {currentState.selectedWords.map((word, index) => (
                  <span
                    key={index}
                    className="px-3 py-1.5 bg-green-100 text-green-800 rounded-md font-medium"
                  >
                    {word}
                  </span>
                ))}
                {!currentState.completed && !currentState.challengeFailed && (
                  <span className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-md animate-pulse">
                    ?
                  </span>
                )}
              </div>
            ) : (
              <p className="text-gray-400 text-center">
                {t("rearrangement.selectWordsHint")}
              </p>
            )}
          </div>

          {/* 可選單字區 */}
          {!currentState.completed && !currentState.challengeFailed && (
            <div className="flex flex-wrap gap-2 justify-center">
              {currentState.remainingWords.map((word, index) => (
                <Button
                  key={`${word}-${index}`}
                  variant="outline"
                  size="lg"
                  onClick={() => handleWordSelect(word)}
                  disabled={submitting}
                  className="text-lg font-medium hover:bg-blue-50 hover:border-blue-400"
                >
                  {word}
                </Button>
              ))}
            </div>
          )}

          {/* 完成或失敗狀態 */}
          {(currentState.completed || currentState.challengeFailed) && (
            <div className={cn(
              "p-4 rounded-lg text-center",
              currentState.completed ? "bg-green-50" : "bg-red-50"
            )}>
              {currentState.completed ? (
                <>
                  <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-600" />
                  <p className="text-lg font-bold text-green-800">
                    {t("rearrangement.messages.correct")}
                  </p>
                  <p className="text-green-600">
                    {t("rearrangement.messages.scoreEarned", { score: Math.round(currentState.expectedScore) })}
                  </p>
                </>
              ) : (
                <>
                  <XCircle className="h-12 w-12 mx-auto mb-2 text-red-600" />
                  <p className="text-lg font-bold text-red-800">
                    {t("rearrangement.messages.tooManyErrors")}
                  </p>
                  <p className="text-red-600 mb-4">
                    {t("rearrangement.messages.tryAgain")}
                  </p>
                  <Button onClick={handleRetry} disabled={submitting}>
                    <RotateCcw className="h-4 w-4 mr-2" />
                    {t("rearrangement.buttons.retry")}
                  </Button>
                </>
              )}
            </div>
          )}

          {/* 下一題按鈕 */}
          {currentState.completed && (
            <div className="flex justify-center pt-4">
              <Button
                size="lg"
                onClick={handleNextQuestion}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {currentQuestionIndex < questions.length - 1 ? (
                  <>
                    {t("rearrangement.buttons.next")}
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </>
                ) : (
                  t("rearrangement.buttons.finish")
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default RearrangementActivity;
