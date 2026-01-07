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

import { useState, useEffect, useCallback, useRef } from "react";
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
} from "lucide-react";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { cn } from "@/lib/utils";

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
  onComplete?: () => void;
}

export default function WordSelectionActivity({
  assignmentId,
  isPreviewMode = false,
  onComplete,
}: WordSelectionActivityProps) {
  const { t } = useTranslation();
  const { token } = useStudentAuthStore();

  // State
  const [loading, setLoading] = useState(true);
  const [words, setWords] = useState<WordOption[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [_sessionId, setSessionId] = useState<number | null>(null); // Kept for future session tracking
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [submitting, setSubmitting] = useState(false);

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
  const [completingAssignment, setCompletingAssignment] = useState(false);

  // Round tracking
  const [roundCompleted, setRoundCompleted] = useState(false);

  // Audio ref
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Start practice session
  const startPractice = useCallback(async () => {
    try {
      setLoading(true);
      const apiUrl = import.meta.env.VITE_API_URL || "";

      const response = await fetch(
        `${apiUrl}/api/students/assignments/${assignmentId}/vocabulary/selection/start`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to start practice: ${response.status}`);
      }

      const data = await response.json();
      setWords(data.words || []);
      setSessionId(data.session_id);
      setShowWord(data.show_word ?? true);
      setShowImage(data.show_image ?? true);
      setPlayAudio(data.play_audio ?? false);
      setProficiency({
        current_mastery: data.current_proficiency || 0,
        target_mastery: data.target_proficiency || 80,
        achieved: false,
        words_mastered: 0,
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
  }, [assignmentId, token, t]);

  // Fetch current proficiency
  const fetchProficiency = useCallback(async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";

      const response = await fetch(
        `${apiUrl}/api/students/assignments/${assignmentId}/vocabulary/selection/proficiency`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch proficiency: ${response.status}`);
      }

      const data = await response.json();
      setProficiency(data);

      // Note: Achievement check moved to round completed view
      // Dialog will only show after clicking "完成本輪", not during practice
    } catch (error) {
      console.error("Error fetching proficiency:", error);
    }
  }, [assignmentId, token]);

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

  // Handle answer selection
  const handleSelectAnswer = async (answer: string) => {
    if (showResult || submitting) return;

    const currentWord = words[currentIndex];
    const correct = answer === currentWord.translation;

    setSelectedAnswer(answer);
    setIsCorrect(correct);
    setShowResult(true);
    setSubmitting(true);

    // Skip API call in preview mode
    if (isPreviewMode) {
      setSubmitting(false);
      return;
    }

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";

      const response = await fetch(
        `${apiUrl}/api/students/assignments/${assignmentId}/vocabulary/selection/answer`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            content_item_id: currentWord.content_item_id,
            selected_answer: answer,
            is_correct: correct,
            time_spent_seconds: 0,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to submit answer: ${response.status}`);
      }

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

  // Complete assignment
  const handleCompleteAssignment = async () => {
    if (isPreviewMode) {
      toast.info(
        t("wordSelection.toast.cannotCompletePreview") ||
          "Cannot complete in preview mode",
      );
      setShowAchievementDialog(false);
      return;
    }

    try {
      setCompletingAssignment(true);
      const apiUrl = import.meta.env.VITE_API_URL || "";

      const response = await fetch(
        `${apiUrl}/api/students/assignments/${assignmentId}/vocabulary/selection/complete`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to complete assignment: ${response.status}`);
      }

      toast.success(
        t("wordSelection.toast.completed") || "Assignment completed!",
      );
      setShowAchievementDialog(false);
      onComplete?.();
    } catch (error) {
      console.error("Error completing assignment:", error);
      toast.error(
        t("wordSelection.toast.completeFailed") ||
          "Failed to complete assignment",
      );
    } finally {
      setCompletingAssignment(false);
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
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-gray-600">
              <span>
                {t("wordSelection.currentProficiency") || "Proficiency"}
              </span>
              <span>
                {proficiency.current_mastery.toFixed(1)}% /{" "}
                {proficiency.target_mastery}%
              </span>
            </div>
            <Progress
              value={proficiency.current_mastery}
              max={100}
              className="h-3"
            />
          </div>

          <div className="text-gray-600">
            <p>
              {t("wordSelection.wordsMastered", {
                mastered: proficiency.words_mastered,
                total: proficiency.total_words,
              }) ||
                `${proficiency.words_mastered} / ${proficiency.total_words} words mastered`}
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
                <Button variant="outline" onClick={handleContinuePractice}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  {t("wordSelection.continuePractice") || "Continue Practice"}
                </Button>
                <Button
                  onClick={handleCompleteAssignment}
                  disabled={completingAssignment}
                >
                  {completingAssignment ? (
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
      {/* Header with proficiency */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            {t("wordSelection.wordSelection") || "Word Selection"}
          </Badge>
          <span className="text-sm text-gray-600">
            {t("wordSelection.itemProgress", {
              current: currentIndex + 1,
              total: words.length,
            }) || `${currentIndex + 1} / ${words.length}`}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-600">
            {t("wordSelection.proficiency") || "Proficiency"}:
          </span>
          <span className="font-medium text-blue-600">
            {proficiency.current_mastery.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Word Card */}
      <Card className="p-6">
        <CardContent className="space-y-6">
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

          {/* Audio Button */}
          {currentWord.audio_url && (
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

          {/* Answer Options */}
          <div className="grid grid-cols-2 gap-4">
            {currentWord.options.map((option, index) => {
              const isSelected = selectedAnswer === option;
              const isCorrectAnswer = option === currentWord.translation;
              const showCorrect = showResult && isCorrectAnswer;
              const showIncorrect =
                showResult && isSelected && !isCorrectAnswer;

              return (
                <Button
                  key={index}
                  variant="outline"
                  className={cn(
                    "h-16 text-lg font-medium transition-all",
                    !showResult && "hover:bg-blue-50 hover:border-blue-400",
                    showCorrect &&
                      "bg-green-100 border-green-500 text-green-800",
                    showIncorrect && "bg-red-100 border-red-500 text-red-800",
                    isSelected && !showResult && "border-blue-500 bg-blue-50",
                  )}
                  onClick={() => handleSelectAnswer(option)}
                  disabled={showResult || submitting}
                >
                  {showCorrect && (
                    <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
                  )}
                  {showIncorrect && (
                    <XCircle className="h-5 w-5 mr-2 text-red-600" />
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
              {!isCorrect && (
                <p className="text-gray-600 mt-1">
                  {t("wordSelection.correctAnswerIs") || "Correct answer:"}{" "}
                  <span className="font-medium">{currentWord.translation}</span>
                </p>
              )}
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
        </CardContent>
      </Card>

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
                    {proficiency.current_mastery.toFixed(1)}%
                  </span>
                </p>
                <p>
                  {t("wordSelection.wordsMastered", {
                    mastered: proficiency.words_mastered,
                    total: proficiency.total_words,
                  }) ||
                    `Words Mastered: ${proficiency.words_mastered} / ${proficiency.total_words}`}
                </p>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={handleContinuePractice}>
              <RefreshCw className="h-4 w-4 mr-2" />
              {t("wordSelection.continuePractice") || "Continue Practice"}
            </Button>
            <Button
              onClick={handleCompleteAssignment}
              disabled={completingAssignment}
            >
              {completingAssignment ? (
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
