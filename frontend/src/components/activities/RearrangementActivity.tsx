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

export interface RearrangementQuestion {
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
  // 受控導航 props（由父組件控制題目切換）
  currentQuestionIndex?: number;
  onQuestionIndexChange?: (index: number) => void;
  onQuestionsLoaded?: (
    questions: RearrangementQuestion[],
    questionStates: Map<number, RearrangementQuestionState>,
  ) => void;
  onQuestionStateChange?: (
    questionStates: Map<number, RearrangementQuestionState>,
  ) => void;
}

export interface RearrangementQuestionState {
  selectedWords: string[]; // 已選擇的單字（按順序）
  remainingWords: string[]; // 剩餘可選的單字
  errorCount: number;
  expectedScore: number;
  completed: boolean;
  challengeFailed: boolean;
  timeRemaining: number;
}

// 內部使用的別名
type QuestionState = RearrangementQuestionState;

const RearrangementActivity: React.FC<RearrangementActivityProps> = ({
  studentAssignmentId,
  onComplete,
  isPreviewMode = false,
  currentQuestionIndex: controlledIndex,
  onQuestionIndexChange,
  onQuestionsLoaded,
  onQuestionStateChange,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<RearrangementQuestion[]>([]);
  const [internalQuestionIndex, setInternalQuestionIndex] = useState(0);
  const [questionStates, setQuestionStates] = useState<
    Map<number, QuestionState>
  >(new Map());
  const [submitting, setSubmitting] = useState(false);
  const [scoreCategory, setScoreCategory] = useState<string>("writing");
  const [totalScore, setTotalScore] = useState(0);
  const [, setCompletedQuestions] = useState(0);
  // 追蹤第一題音檔是否因瀏覽器限制而無法自動播放
  const [showAudioPrompt, setShowAudioPrompt] = useState(false);

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // 使用受控或內部索引
  const currentQuestionIndex = controlledIndex ?? internalQuestionIndex;
  const setCurrentQuestionIndex = (index: number) => {
    if (onQuestionIndexChange) {
      onQuestionIndexChange(index);
    } else {
      setInternalQuestionIndex(index);
    }
  };

  // 通知父組件題目狀態變更
  useEffect(() => {
    if (onQuestionStateChange && questionStates.size > 0) {
      onQuestionStateChange(questionStates);
    }
  }, [questionStates, onQuestionStateChange]);

  // 追蹤是否已播放第一題音檔
  const hasPlayedFirstAudioRef = useRef(false);

  // 載入題目
  useEffect(() => {
    hasPlayedFirstAudioRef.current = false; // 重置狀態
    loadQuestions();
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [studentAssignmentId]);

  // 第一題音檔自動播放（題目載入完成後）
  useEffect(() => {
    if (
      questions.length > 0 &&
      !hasPlayedFirstAudioRef.current &&
      !loading
    ) {
      const firstQuestion = questions[0];
      if (firstQuestion.play_audio && firstQuestion.audio_url) {
        // 延遲播放，確保 UI 渲染完成
        const timer = setTimeout(async () => {
          try {
            await playAudioAsync(firstQuestion.audio_url!);
            hasPlayedFirstAudioRef.current = true;
            setShowAudioPrompt(false);
          } catch (error) {
            // 瀏覽器阻擋自動播放，顯示提示讓用戶點擊
            if (error instanceof Error && error.name === "NotAllowedError") {
              setShowAudioPrompt(true);
            }
            hasPlayedFirstAudioRef.current = true;
          }
        }, 500);
        return () => clearTimeout(timer);
      }
      hasPlayedFirstAudioRef.current = true;
    }
  }, [questions, loading]);

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

      // 通知父組件題目已載入
      if (onQuestionsLoaded) {
        onQuestionsLoaded(response.questions, initialStates);
      }

      // 開始計時（音檔播放由 useEffect 處理，避免重複播放）
      if (response.questions.length > 0) {
        const firstQuestion = response.questions[0];
        startTimer(firstQuestion.content_item_id);
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

    // 找到當前題目
    const currentQuestion = questions.find(
      (q) => q.content_item_id === contentItemId
    );

    // 計算實際分數：根據已正確回答的單字數量
    // 如果沒有回答任何單字，給予最低分（100 - max_errors * 每字分數）
    const correctWordCount = currentState?.selectedWords.length || 0;
    const totalWordCount = currentQuestion?.word_count || currentQuestion?.shuffled_words.length || 1;
    const maxErrors = currentQuestion?.max_errors || 3;
    const pointsPerWord = Math.floor(100 / totalWordCount);

    // 計算實際分數
    let actualScore: number;
    if (correctWordCount > 0) {
      // 有回答一些單字：計算已回答的分數
      actualScore = Math.floor((correctWordCount / totalWordCount) * 100);
    } else {
      // 完全沒有回答：給予最低分（如同錯了 max_errors 次）
      actualScore = Math.max(0, 100 - maxErrors * pointsPerWord);
    }

    try {
      // 根據是否為預覽模式選擇不同的 API
      const completeUrl = isPreviewMode
        ? `/api/teachers/assignments/${studentAssignmentId}/preview/rearrangement-complete`
        : `/api/students/assignments/${studentAssignmentId}/rearrangement-complete`;

      await apiClient.post(completeUrl, {
        content_item_id: contentItemId,
        timeout: true,
        expected_score: actualScore,
      });

      setQuestionStates((prev) => {
        const newStates = new Map(prev);
        const stateInMap = newStates.get(contentItemId);
        if (stateInMap) {
          newStates.set(contentItemId, {
            ...stateInMap,
            completed: true,
            timeRemaining: 0,
            expectedScore: actualScore, // 更新為實際分數
          });
        }
        return newStates;
      });

      toast.warning(t("rearrangement.messages.timeout"));

      // 計算並更新分數（使用實際分數）
      setTotalScore((prev) => prev + actualScore);
      setCompletedQuestions((prev) => prev + 1);

      // 時間到後顯示分數和下一題按鈕，讓用戶自行點擊
      // （不自動進入下一題）
    } catch (error) {
      console.error("Failed to complete on timeout:", error);
    }
  };

  const handleWordSelect = async (word: string) => {
    const currentQuestion = questions[currentQuestionIndex];
    const currentState = questionStates.get(currentQuestion.content_item_id);

    if (
      !currentState ||
      currentState.completed ||
      currentState.challengeFailed ||
      submitting
    ) {
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
        toast.error(
          t("rearrangement.messages.incorrect", {
            correct: response.correct_word,
          }),
        );
      }

      // 檢查是否完成或失敗
      if (response.completed) {
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
        setTotalScore((prev) => prev + response.expected_score);
        setCompletedQuestions((prev) => prev + 1);
        toast.success(
          t("rearrangement.messages.questionComplete", {
            score: Math.round(response.expected_score),
          }),
        );
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

  // 處理受控索引變更（當父組件改變 currentQuestionIndex 時）
  const prevControlledIndexRef = useRef<number | undefined>(controlledIndex);
  useEffect(() => {
    // 只有在 controlledIndex 真正改變時才處理
    if (
      controlledIndex !== undefined &&
      controlledIndex !== prevControlledIndexRef.current &&
      questions.length > 0
    ) {
      const targetIndex = controlledIndex;
      if (targetIndex < 0 || targetIndex >= questions.length) return;

      // 判斷是否是初始載入（從 undefined 變成 0）
      const isInitialLoad =
        prevControlledIndexRef.current === undefined && targetIndex === 0;

      // 停止當前計時器
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }

      const targetQuestion = questions[targetIndex];
      const targetState = questionStates.get(targetQuestion.content_item_id);

      // 如果目標題目尚未完成，啟動計時器
      if (targetState && !targetState.completed && !targetState.challengeFailed) {
        startTimer(targetQuestion.content_item_id);
      }

      // 播放音檔（如果需要）
      // 跳過初始載入時的第一題（由 useEffect 處理）
      // 跳過已完成的題目（不自動播放）
      if (
        targetQuestion.play_audio &&
        targetQuestion.audio_url &&
        !isInitialLoad &&
        targetState &&
        !targetState.completed &&
        !targetState.challengeFailed
      ) {
        playAudio(targetQuestion.audio_url);
      }

      prevControlledIndexRef.current = controlledIndex;
    }
  }, [controlledIndex, questions, questionStates]);

  const handleNextQuestion = () => {
    // 找到下一個尚未完成的題目（跳過已完成或挑戰失敗的題目）
    let nextIndex = -1;

    // 先從當前題目之後找
    for (let i = currentQuestionIndex + 1; i < questions.length; i++) {
      const state = questionStates.get(questions[i].content_item_id);
      if (state && !state.completed && !state.challengeFailed) {
        nextIndex = i;
        break;
      }
    }

    // 如果後面沒有，從頭開始找（到當前題目為止）
    if (nextIndex === -1) {
      for (let i = 0; i < currentQuestionIndex; i++) {
        const state = questionStates.get(questions[i].content_item_id);
        if (state && !state.completed && !state.challengeFailed) {
          nextIndex = i;
          break;
        }
      }
    }

    if (nextIndex !== -1) {
      // 找到下一個未完成的題目
      setCurrentQuestionIndex(nextIndex);
      startTimer(questions[nextIndex].content_item_id);

      // 播放音檔（如果需要）
      if (questions[nextIndex].play_audio && questions[nextIndex].audio_url) {
        playAudio(questions[nextIndex].audio_url!);
      }
    } else {
      // 所有題目都已完成
      if (onComplete) {
        onComplete(totalScore, questions.length);
      }
      toast.success(
        t("rearrangement.messages.allComplete", {
          score: Math.round(totalScore),
          total: questions.length * 100,
        }),
      );
    }
  };

  // 異步播放音檔（返回 Promise，可以捕捉錯誤）
  const playAudioAsync = useCallback(async (url: string): Promise<void> => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    audioRef.current = new Audio(url);
    await audioRef.current.play();
  }, []);

  // 同步播放音檔（忽略錯誤）
  const playAudio = useCallback((url: string) => {
    playAudioAsync(url).catch((e) => {
      console.error("Failed to play audio:", e);
    });
  }, [playAudioAsync]);

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
  const progressPercent =
    ((currentQuestionIndex + (currentState.completed ? 1 : 0)) /
      questions.length) *
    100;

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
          <Badge
            variant="secondary"
            className={cn(
              scoreCategory === "listening" && "bg-purple-100 text-purple-800",
              scoreCategory === "writing" && "bg-green-100 text-green-800",
              scoreCategory === "speaking" && "bg-blue-100 text-blue-800",
            )}
          >
            {scoreCategory === "listening" &&
              t("rearrangement.scoreCategories.listening")}
            {scoreCategory === "writing" &&
              t("rearrangement.scoreCategories.writing")}
            {scoreCategory === "speaking" &&
              t("rearrangement.scoreCategories.speaking")}
          </Badge>
        </div>
        <div className="text-sm text-gray-600">
          {t("rearrangement.totalScore")}:{" "}
          <span className="font-bold text-blue-600">
            {Math.round(totalScore)}
          </span>
        </div>
      </div>

      <Progress value={progressPercent} className="h-2" />

      {/* 音檔自動播放被阻擋時顯示的提示 */}
      {showAudioPrompt && currentQuestion.play_audio && currentQuestion.audio_url && (
        <div className="mt-4 p-4 bg-purple-50 border-2 border-purple-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Volume2 className="h-5 w-5 text-purple-600" />
              <span className="text-purple-800 font-medium">
                {t("rearrangement.audioPrompt")}
              </span>
            </div>
            <Button
              variant="default"
              size="sm"
              className="bg-purple-600 hover:bg-purple-700"
              onClick={() => {
                playAudio(currentQuestion.audio_url!);
                setShowAudioPrompt(false);
              }}
            >
              <Volume2 className="h-4 w-4 mr-1" />
              {t("rearrangement.playAudio")}
            </Button>
          </div>
        </div>
      )}

      {/* 題目卡片 */}
      <Card className="mt-4">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">
              {t("rearrangement.questionTitle", {
                number: currentQuestionIndex + 1,
              })}
            </CardTitle>
            <div className="flex items-center gap-3">
              {/* 計時器 */}
              <div
                className={cn(
                  "flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium",
                  isLowTime
                    ? "bg-red-100 text-red-700 animate-pulse"
                    : "bg-gray-100 text-gray-700",
                )}
              >
                <Clock className="h-4 w-4" />
                {formatTime(currentState.timeRemaining)}
              </div>

              {/* 音檔按鈕 - 已完成的題目不能播放 */}
              {currentQuestion.play_audio && currentQuestion.audio_url && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => playAudio(currentQuestion.audio_url!)}
                  disabled={submitting || currentState.completed || currentState.challengeFailed}
                  title={currentState.completed || currentState.challengeFailed ? t("rearrangement.audioDisabledCompleted") : undefined}
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
              <span className="font-medium">{t("rearrangement.hint")}:</span>{" "}
              {currentQuestion.translation}
            </div>
          )}

          {/* 錯誤計數 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {Array.from({ length: currentQuestion.max_errors }).map(
                (_, i) => (
                  <div
                    key={i}
                    className={cn(
                      "w-3 h-3 rounded-full",
                      i < currentState.errorCount
                        ? "bg-red-500"
                        : "bg-gray-200",
                    )}
                  />
                ),
              )}
              <span className="text-sm text-gray-500 ml-2">
                {t("rearrangement.errorsRemaining", {
                  remaining:
                    currentQuestion.max_errors - currentState.errorCount,
                })}
              </span>
            </div>
            <div className="text-sm">
              {t("rearrangement.expectedScore")}:{" "}
              <span className="font-bold">
                {Math.round(currentState.expectedScore)}
              </span>
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
            <div
              className={cn(
                "p-4 rounded-lg text-center",
                currentState.completed && currentState.expectedScore === 100
                  ? "bg-green-50"
                  : currentState.completed
                    ? "bg-blue-50"
                    : "bg-red-50",
              )}
            >
              {currentState.completed ? (
                currentState.expectedScore === 100 ? (
                  // 全對：顯示打勾和「答對了！」
                  <>
                    <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-600" />
                    <p className="text-lg font-bold text-green-800">
                      {t("rearrangement.messages.correct")}
                    </p>
                    <p className="text-green-600">
                      {t("rearrangement.messages.scoreEarned", {
                        score: Math.round(currentState.expectedScore),
                      })}
                    </p>
                  </>
                ) : (
                  // 非全對：只顯示分數
                  <p className="text-lg font-bold text-blue-800">
                    {t("rearrangement.messages.scoreEarned", {
                      score: Math.round(currentState.expectedScore),
                    })}
                  </p>
                )
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
                {/* 檢查是否還有未完成的題目（排除當前題目） */}
                {questions.some((q, idx) => {
                  if (idx === currentQuestionIndex) return false;
                  const state = questionStates.get(q.content_item_id);
                  return state && !state.completed && !state.challengeFailed;
                }) ? (
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
