/**
 * WordSelectionActivity - Word Selection Practice Activity
 *
 * Phase 2-3: Vocabulary selection quiz with Ebbinghaus memory curve tracking
 *
 * Features:
 * - Display word card (image, word text, audio playback)
 * - 4-choice selection UI (1 correct + 3 AI-generated distractors)
 * - Proficiency progress bar at top
 * - Visual feedback on correct/incorrect selection
 * - Achievement dialog when target_proficiency is reached
 */

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Loader2,
  Volume2,
  CheckCircle,
  XCircle,
  Trophy,
  RefreshCw,
  Clock,
} from "lucide-react";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api";

interface WordOption {
  content_item_id: number;
  text: string;
  translation: string;
  audio_url?: string;
  image_url?: string;
  memory_strength: number;
  options: string[];
}

interface ProficiencyStatus {
  current_mastery: number;
  target_mastery: number;
  achieved: boolean;
  words_mastered: number;
  total_words: number;
}

interface WordSelectionActivityProps {
  assignmentId: number;
  isPreviewMode?: boolean;
  isDemoMode?: boolean; // Demo mode - uses public demo API endpoints
  onComplete?: () => void;
}

export default function WordSelectionActivity({
  assignmentId,
  isPreviewMode = false,
  isDemoMode = false,
  onComplete,
}: WordSelectionActivityProps) {
  const { t } = useTranslation();
  // Note: Using apiClient which auto-detects token (student or teacher)

  // State
  const [loading, setLoading] = useState(true);
  const [words, setWords] = useState<WordOption[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [_sessionId, setSessionId] = useState<number | null>(null); // Kept for future session tracking
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [completing, setCompleting] = useState(false);

  // Settings
  const [showWord, setShowWord] = useState(true);
  const [showImage, setShowImage] = useState(true);
  const [playAudio, setPlayAudio] = useState(false);

  // Proficiency
  const [proficiency, setProficiency] = useState<ProficiencyStatus>({
    current_mastery: 0,
    target_mastery: 80,
    achieved: false,
    words_mastered: 0,
    total_words: 0,
  });
  const [showAchievementDialog, setShowAchievementDialog] = useState(false);

  // Round tracking
  const [roundCompleted, setRoundCompleted] = useState(false);

  // Preview mode local proficiency tracking (不存入資料庫，離開後重置)
  // 模擬學生模式的 SM-2 算法：追蹤每個單字的 memory_strength
  const [previewWordStrengths, setPreviewWordStrengths] = useState<
    Record<number, number>
  >({});

  // SM-2 簡化版：計算新的 memory_strength
  const calculateNewStrength = (
    currentStrength: number | undefined,
    isCorrect: boolean,
  ): number => {
    if (currentStrength === undefined) {
      // 第一次作答
      return isCorrect ? 0.5 : 0.2;
    }
    // 後續作答：答對 +0.15，答錯 -0.2（但不低於 0.1）
    if (isCorrect) {
      return Math.min(1.0, currentStrength + 0.15);
    } else {
      return Math.max(0.1, currentStrength - 0.2);
    }
  };

  // Computed: 預覽模式的平均熟練度（模擬學生模式）
  const previewProficiency = useMemo(() => {
    const strengths = Object.values(previewWordStrengths);
    if (strengths.length === 0) return 0;
    const totalWords = proficiency.total_words || strengths.length;
    // 未練習的單字視為 0 強度
    const sum = strengths.reduce((acc, s) => acc + s, 0);
    return (sum / totalWords) * 100;
  }, [previewWordStrengths, proficiency.total_words]);

  // Computed: 預覽模式的已熟練單字數（memory_strength >= target * 0.8）
  const previewWordsMastered = useMemo(() => {
    const targetThreshold = ((proficiency.target_mastery || 80) / 100) * 0.8;
    return Object.values(previewWordStrengths).filter(
      (s) => s >= targetThreshold,
    ).length;
  }, [previewWordStrengths, proficiency.target_mastery]);

  // Computed: 顯示用的熟練度（預覽模式和 demo 模式用本地計算，學生模式用 API 回傳）
  const displayProficiency =
    isPreviewMode || isDemoMode
      ? previewProficiency
      : proficiency.current_mastery;

  // Computed: 顯示用的已熟練單字數（預覽模式和 demo 模式用本地計算）
  const displayWordsMastered =
    isPreviewMode || isDemoMode
      ? previewWordsMastered
      : proficiency.words_mastered;

  // Timer
  const [timeLimit, setTimeLimit] = useState<number | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Audio ref
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Start practice session
  const startPractice = useCallback(async () => {
    try {
      setLoading(true);

      // 根據模式選擇不同的 API
      const apiEndpoint = isDemoMode
        ? `/api/demo/assignments/${assignmentId}/preview/word-selection-start`
        : isPreviewMode
          ? `/api/teachers/assignments/${assignmentId}/preview/word-selection-start`
          : `/api/students/assignments/${assignmentId}/vocabulary/selection/start`;

      const data = await apiClient.get<{
        session_id: number | null;
        words: WordOption[];
        total_words: number;
        current_proficiency: number;
        target_proficiency: number;
        words_mastered: number;
        achieved: boolean;
        show_word: boolean;
        show_image: boolean;
        play_audio: boolean;
        time_limit_per_question: number | null;
      }>(apiEndpoint);

      setWords(data.words || []);
      setSessionId(data.session_id);
      setShowWord(data.show_word ?? true);
      setShowImage(data.show_image ?? true);
      setPlayAudio(data.play_audio ?? false);
      setTimeLimit(data.time_limit_per_question || null);
      setTimeRemaining(data.time_limit_per_question || null);
      setProficiency({
        current_mastery: data.current_proficiency || 0,
        target_mastery: data.target_proficiency || 80,
        achieved: data.achieved ?? false,
        words_mastered: data.words_mastered ?? 0,
        total_words: data.total_words || 0,
      });
      setCurrentIndex(0);
      setRoundCompleted(false);
      setSelectedAnswer(null);
      setShowResult(false);
    } catch (error) {
      console.error("Error starting practice:", error);
      toast.error(
        t("wordSelection.toast.startFailed") || "Failed to start practice",
      );
    } finally {
      setLoading(false);
    }
  }, [assignmentId, isPreviewMode, isDemoMode, t]);

  // Fetch current proficiency
  const fetchProficiency = useCallback(async () => {
    // Skip in preview mode and demo mode - no proficiency tracking
    if (isPreviewMode || isDemoMode) return;

    try {
      const data = await apiClient.get<ProficiencyStatus>(
        `/api/students/assignments/${assignmentId}/vocabulary/selection/proficiency`,
      );
      setProficiency(data);

      // Note: Achievement check moved to round completed view
      // Dialog will only show after clicking "完成本輪", not during practice
    } catch (error) {
      console.error("Error fetching proficiency:", error);
    }
  }, [assignmentId, isPreviewMode, isDemoMode]);

  useEffect(() => {
    startPractice();
  }, [startPractice]);

  // Play audio for current word
  const playWordAudio = useCallback(() => {
    const currentWord = words[currentIndex];
    if (currentWord?.audio_url) {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      audioRef.current = new Audio(currentWord.audio_url);
      audioRef.current.play().catch(console.error);
    }
  }, [words, currentIndex]);

  // Auto-play audio when word changes if play_audio is enabled
  // Don't play when round is completed (to avoid extra playback on "Finish Round")
  useEffect(() => {
    if (
      playAudio &&
      words[currentIndex]?.audio_url &&
      !showResult &&
      !roundCompleted
    ) {
      playWordAudio();
    }
  }, [
    currentIndex,
    playAudio,
    playWordAudio,
    words,
    showResult,
    roundCompleted,
  ]);

  // Timer countdown effect
  useEffect(() => {
    // Clear existing timer
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    // Don't run timer if no time limit, showing result, or round completed
    if (!timeLimit || showResult || roundCompleted || loading) {
      return;
    }

    // Reset timer for new question
    setTimeRemaining(timeLimit);

    // Start countdown
    timerRef.current = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev === null || prev <= 1) {
          // Time's up - clear timer
          if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [currentIndex, timeLimit, showResult, roundCompleted, loading]);

  // Handle timeout - auto-fail when time expires
  useEffect(() => {
    if (timeRemaining === 0 && !showResult && !submitting && words.length > 0) {
      // Time expired - trigger wrong answer
      handleTimeoutAnswer();
    }
  }, [timeRemaining, showResult, submitting, words.length]);

  // Handle timeout answer (separate from regular answer to avoid loops)
  const handleTimeoutAnswer = async () => {
    if (showResult || submitting) return;

    const currentWord = words[currentIndex];

    setSelectedAnswer(null); // No selection made
    setIsCorrect(false);
    setShowResult(true);
    setSubmitting(true);

    // Skip API call in preview mode and demo mode, but track local stats (SM-2 simulation)
    if (isPreviewMode || isDemoMode) {
      const wordId = currentWord.content_item_id;
      setPreviewWordStrengths((prev) => ({
        ...prev,
        [wordId]: calculateNewStrength(prev[wordId], false), // timeout = incorrect
      }));
      setSubmitting(false);
      return;
    }

    try {
      await apiClient.post(
        `/api/students/assignments/${assignmentId}/vocabulary/selection/answer`,
        {
          content_item_id: currentWord.content_item_id,
          selected_answer: "", // Empty answer for timeout
          is_correct: false,
          time_spent_seconds: timeLimit || 0,
        },
      );

      // Fetch updated proficiency
      await fetchProficiency();
    } catch (error) {
      console.error("Error submitting timeout:", error);
    } finally {
      setSubmitting(false);
    }
  };

  // Handle answer selection
  const handleSelectAnswer = async (answer: string) => {
    if (showResult || submitting) return;

    const currentWord = words[currentIndex];
    const correct = answer === currentWord.translation;

    setSelectedAnswer(answer);
    setIsCorrect(correct);
    setShowResult(true);
    setSubmitting(true);

    // Skip API call in preview mode and demo mode, but track local stats (SM-2 simulation)
    if (isPreviewMode || isDemoMode) {
      const wordId = currentWord.content_item_id;
      setPreviewWordStrengths((prev) => ({
        ...prev,
        [wordId]: calculateNewStrength(prev[wordId], correct),
      }));
      setSubmitting(false);
      return;
    }

    try {
      await apiClient.post(
        `/api/students/assignments/${assignmentId}/vocabulary/selection/answer`,
        {
          content_item_id: currentWord.content_item_id,
          selected_answer: answer,
          is_correct: correct,
          time_spent_seconds: 0,
        },
      );

      // Fetch updated proficiency
      await fetchProficiency();
    } catch (error) {
      console.error("Error submitting answer:", error);
      toast.error(
        t("wordSelection.toast.submitFailed") || "Failed to submit answer",
      );
    } finally {
      setSubmitting(false);
    }
  };

  // Handle next word
  const handleNext = () => {
    setSelectedAnswer(null);
    setShowResult(false);
    // Reset timer immediately to prevent timeout effect from triggering on next question
    // This fixes race condition where timeRemaining is still 0 when showResult becomes false
    if (timeLimit) {
      setTimeRemaining(timeLimit);
    }

    if (currentIndex < words.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      // Round completed
      setRoundCompleted(true);
    }
  };

  // Start next round
  const handleStartNextRound = () => {
    startPractice();
  };

  // Complete assignment - 呼叫 API 完成作業並更新狀態
  const handleCompleteAssignment = async () => {
    // 預覽模式和 demo 模式不需要呼叫 API
    if (isPreviewMode || isDemoMode) {
      toast.success(
        t("wordSelection.toast.completed") || "Assignment completed!",
      );
      setShowAchievementDialog(false);
      onComplete?.();
      return;
    }

    // 防止重複點擊
    if (completing) return;

    setCompleting(true);
    try {
      // 呼叫提交 API 來更新狀態為 GRADED 並記錄分數
      await apiClient.post(`/api/students/assignments/${assignmentId}/submit`);

      toast.success(
        t("wordSelection.toast.completed") || "Assignment completed!",
      );
      setShowAchievementDialog(false);
      onComplete?.();
    } catch (error) {
      console.error("Error completing assignment:", error);
      toast.error(
        t("wordSelection.toast.completeFailed") ||
          "Failed to complete assignment. Please try again.",
      );
      // 保持 dialog 開啟，讓使用者可以重試
    } finally {
      setCompleting(false);
    }
  };

  // Continue practice after achievement
  const handleContinuePractice = () => {
    setShowAchievementDialog(false);
    startPractice();
  };

  // Loading state
  if (loading) {
    return (
      <Card className="p-8">
        <CardContent className="flex flex-col items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
          <p className="text-gray-600">
            {t("wordSelection.loading") || "Loading vocabulary items..."}
          </p>
        </CardContent>
      </Card>
    );
  }

  // No words
  if (words.length === 0) {
    return (
      <Card className="p-8">
        <CardContent className="text-center">
          <p className="text-gray-600">
            {t("wordSelection.noItems") || "No vocabulary items found"}
          </p>
        </CardContent>
      </Card>
    );
  }

  // Round completed view
  if (roundCompleted) {
    return (
      <Card className="p-8">
        <CardContent className="text-center space-y-6">
          <div className="flex justify-center">
            <CheckCircle className="h-16 w-16 text-green-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800">
            {t("wordSelection.roundComplete") || "Round Complete!"}
          </h2>

          {/* Proficiency Progress */}
          <div className="space-y-2 max-w-md mx-auto">
            <div className="flex justify-between text-sm text-gray-600">
              <span>
                {t("wordSelection.currentProficiency") || "Proficiency"}
              </span>
              <span>
                {displayProficiency.toFixed(1)}% / {proficiency.target_mastery}%
              </span>
            </div>
            <Progress value={displayProficiency} max={100} className="h-3" />
          </div>

          <div className="text-gray-600">
            <p>
              {t("wordSelection.wordsMastered", {
                mastered: displayWordsMastered,
                total: proficiency.total_words,
              }) ||
                `${displayWordsMastered} / ${proficiency.total_words} words mastered`}
            </p>
          </div>

          {proficiency.achieved ? (
            <div className="space-y-4">
              <div className="flex justify-center">
                <Trophy className="h-12 w-12 text-yellow-500" />
              </div>
              <p className="text-green-600 font-medium">
                {t("wordSelection.targetReached") ||
                  "Congratulations! You've reached the target proficiency!"}
              </p>
              <div className="flex gap-4 justify-center">
                <Button
                  variant="outline"
                  onClick={handleContinuePractice}
                  disabled={completing}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  {t("wordSelection.continuePractice") || "Continue Practice"}
                </Button>
                <Button
                  onClick={handleCompleteAssignment}
                  disabled={completing}
                >
                  {completing ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <CheckCircle className="h-4 w-4 mr-2" />
                  )}
                  {t("wordSelection.close") || "Close"}
                </Button>
              </div>
            </div>
          ) : (
            <Button onClick={handleStartNextRound}>
              <RefreshCw className="h-4 w-4 mr-2" />
              {t("wordSelection.nextRound") || "Start Next Round"}
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  const currentWord = words[currentIndex];

  return (
    <div className="space-y-6">
      {/* Simplified header: [單字選擇] 第 N 題 + 熟悉度 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            {t("wordSelection.wordSelection") || "Word Selection"}
          </Badge>
          <span className="text-sm text-gray-600">
            {t("wordSelection.questionProgress", {
              current: currentIndex + 1,
              total: words.length,
            }) || `第 ${currentIndex + 1}/${words.length} 題`}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-600">
            {t("wordSelection.proficiency") || "Proficiency"}:
          </span>
          <span className="font-medium text-blue-600">
            {displayProficiency.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Separator line */}
      <hr className="border-gray-200" />

      {/* Question content */}
      <div className="space-y-6">
        {/* Image */}
        {showImage && currentWord.image_url && (
          <div className="flex justify-center">
            <img
              src={currentWord.image_url}
              alt={currentWord.text}
              className="max-h-48 object-contain rounded-lg"
            />
          </div>
        )}

        {/* Word Text - hide when in audio mode */}
        {!playAudio && (
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-800">
              {currentWord.text}
            </h2>
          </div>
        )}

        {/* Audio Button - only show if playAudio setting is enabled */}
        {playAudio && currentWord.audio_url && (
          <div className="flex justify-center">
            <Button
              variant="outline"
              size="lg"
              onClick={playWordAudio}
              className="gap-2"
            >
              <Volume2 className="h-5 w-5" />
              {t("wordSelection.playAudio") || "Play Audio"}
            </Button>
          </div>
        )}

        {/* Question */}
        <div className="text-center text-gray-600">
          {showWord
            ? t("wordSelection.selectTranslation") ||
              "Select the correct translation:"
            : t("wordSelection.selectTranslationAudio") ||
              "Listen and select the correct translation:"}
        </div>

        {/* Timer Display - stays visible when time is up to prevent visual jump */}
        {timeLimit && timeRemaining !== null && (
          <div className="flex justify-center">
            <div
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-full text-lg font-medium",
                timeRemaining === 0
                  ? "bg-red-100 text-red-700"
                  : timeRemaining <= 5
                    ? "bg-red-100 text-red-700"
                    : timeRemaining <= 10
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-gray-100 text-gray-700",
              )}
            >
              <Clock className="h-5 w-5" />
              {timeRemaining === 0 ? (
                <span>{t("wordSelection.timeUp") || "Time's up!"}</span>
              ) : (
                <>
                  <span>{timeRemaining}</span>
                  <span className="text-sm">
                    {t("wordSelection.seconds") || "s"}
                  </span>
                </>
              )}
            </div>
          </div>
        )}

        {/* Answer Options - grid-rows-2 + 1fr ensures all 4 buttons are equal height */}
        <div
          className="grid grid-cols-2 grid-rows-2 gap-3 sm:gap-4"
          style={{ gridAutoRows: "1fr" }}
        >
          {currentWord.options.map((option, index) => {
            const isSelected = selectedAnswer === option;
            const isCorrectAnswer = option === currentWord.translation;
            // Only show correct highlight if user answered correctly
            const showCorrect = showResult && isCorrectAnswer && isCorrect;
            // Show incorrect highlight only for the selected wrong option
            const showIncorrect = showResult && isSelected && !isCorrectAnswer;

            return (
              <Button
                key={index}
                variant="outline"
                className={cn(
                  "h-full min-h-16 py-3 px-4 text-base sm:text-lg font-medium transition-all whitespace-normal text-center break-words",
                  !showResult && "hover:bg-blue-50 hover:border-blue-400",
                  showCorrect && "bg-green-100 border-green-500 text-green-800",
                  showIncorrect && "bg-red-100 border-red-500 text-red-800",
                  isSelected && !showResult && "border-blue-500 bg-blue-50",
                )}
                onClick={() => handleSelectAnswer(option)}
                disabled={showResult || submitting}
              >
                {showCorrect && (
                  <CheckCircle className="h-5 w-5 mr-2 shrink-0 text-green-600" />
                )}
                {showIncorrect && (
                  <XCircle className="h-5 w-5 mr-2 shrink-0 text-red-600" />
                )}
                {option}
              </Button>
            );
          })}
        </div>

        {/* Result Feedback */}
        {showResult && (
          <div
            className={cn(
              "text-center p-4 rounded-lg",
              isCorrect ? "bg-green-50" : "bg-red-50",
            )}
          >
            <p
              className={cn(
                "font-medium text-lg",
                isCorrect ? "text-green-700" : "text-red-700",
              )}
            >
              {isCorrect
                ? t("wordSelection.correct") || "Correct!"
                : t("wordSelection.incorrect") || "Incorrect"}
            </p>
            {/* Note: Correct answer is intentionally NOT shown when wrong to encourage learning */}
          </div>
        )}

        {/* Next Button */}
        {showResult && (
          <div className="flex justify-center pt-4">
            <Button onClick={handleNext} size="lg">
              {currentIndex < words.length - 1
                ? t("wordSelection.next") || "Next"
                : t("wordSelection.finishRound") || "Finish Round"}
            </Button>
          </div>
        )}
      </div>

      {/* Achievement Dialog */}
      <Dialog
        open={showAchievementDialog}
        onOpenChange={setShowAchievementDialog}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <Trophy className="h-6 w-6 text-yellow-500" />
              {t("wordSelection.achievementTitle") || "Congratulations!"}
            </DialogTitle>
            <DialogDescription className="space-y-4 pt-4">
              <p className="text-lg">
                {t("wordSelection.achievementMessage", {
                  target: proficiency.target_mastery,
                }) ||
                  `You've reached the target proficiency of ${proficiency.target_mastery}%!`}
              </p>
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <p>
                  {t("wordSelection.currentProficiency") ||
                    "Current Proficiency"}
                  :{" "}
                  <span className="font-bold text-blue-600">
                    {displayProficiency.toFixed(1)}%
                  </span>
                </p>
                <p>
                  {t("wordSelection.wordsMastered", {
                    mastered: displayWordsMastered,
                    total: proficiency.total_words,
                  }) ||
                    `Words Mastered: ${displayWordsMastered} / ${proficiency.total_words}`}
                </p>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={handleContinuePractice}
              disabled={completing}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              {t("wordSelection.continuePractice") || "Continue Practice"}
            </Button>
            <Button onClick={handleCompleteAssignment} disabled={completing}>
              {completing ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : null}
              {t("wordSelection.close") || "Close"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
