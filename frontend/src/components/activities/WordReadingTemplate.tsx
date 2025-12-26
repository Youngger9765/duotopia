/**
 * WordReadingTemplate - 單字朗讀練習元件
 *
 * Phase 2-2: 單字集練習的朗讀功能
 *
 * 功能:
 * - 顯示單字卡片（圖片、單字、翻譯）
 * - 播放例句音檔
 * - 錄音（max 5s, min 0.01s）
 * - Azure Speech AI 評分
 * - 老師批改後完成
 *
 * 流程:
 * 已指派 -> 未開始 -> 已開始 -> 已提交 -> 待訂正 -> 已訂正 -> 已完成
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Brain,
  Star,
  Clock,
  RotateCcw,
  SkipForward,
  Volume2,
  Image as ImageIcon,
} from "lucide-react";
import { toast } from "sonner";
import AudioRecorder from "@/components/shared/AudioRecorder";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import { useAzurePronunciation } from "@/hooks/useAzurePronunciation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface AssessmentResult {
  overallScore: number;
  accuracyScore: number;
  fluencyScore: number;
  completenessScore: number;
  pronunciationScore: number;
  feedback: string;
}

interface WordItem {
  id: number;
  text: string; // The word
  translation?: string;
  audio_url?: string;
  image_url?: string;
  part_of_speech?: string;
  progress_id?: number;
  recording_url?: string;
  ai_assessment?: {
    accuracy_score?: number;
    fluency_score?: number;
    completeness_score?: number;
    pronunciation_score?: number;
  };
  teacher_feedback?: string;
  teacher_passed?: boolean;
  teacher_review_score?: number;
}

interface WordReadingTemplateProps {
  // Current word item to practice
  currentItem: WordItem;
  currentIndex: number;
  totalItems: number;

  // Assignment settings
  showTranslation?: boolean;
  showImage?: boolean;

  // Existing recording state
  existingAudioUrl?: string | null;
  onRecordingComplete?: (blob: Blob, url: string) => void;

  // Progress tracking
  progressId?: number;
  readOnly?: boolean;

  // Time limit (max 5 seconds for word reading)
  timeLimit?: number;

  // Callbacks
  onTimeout?: () => void;
  onRetry?: () => void;
  onSkip?: () => void;
  onAssessmentComplete?: (result: AssessmentResult) => void;
}

export default function WordReadingTemplate({
  currentItem,
  currentIndex,
  totalItems,
  showTranslation = true,
  showImage = true,
  existingAudioUrl,
  onRecordingComplete,
  progressId: _progressId,
  readOnly = false,
  timeLimit = 5, // Default 5 seconds for word reading
  onTimeout,
  onRetry,
  onSkip,
  onAssessmentComplete,
}: WordReadingTemplateProps) {
  const { t } = useTranslation();
  const [audioUrl, setAudioUrl] = useState<string | undefined>(
    existingAudioUrl || undefined,
  );
  const [isPlayingExample, setIsPlayingExample] = useState(false);
  const [isAssessing, setIsAssessing] = useState(false);
  const [assessmentResult, setAssessmentResult] =
    useState<AssessmentResult | null>(null);
  const exampleAudioRef = useRef<HTMLAudioElement>(null);

  // Azure Speech Service hook for direct API calls
  const { analyzePronunciation } = useAzurePronunciation();

  // Timer state
  const [timeRemaining, setTimeRemaining] = useState(timeLimit);
  const [showTimeoutDialog, setShowTimeoutDialog] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Image error handling
  const [imageError, setImageError] = useState(false);

  // Format time helper
  const formatTime = useCallback((seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }, []);

  // Start timer
  const startTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    timerRef.current = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          if (timerRef.current) {
            clearInterval(timerRef.current);
          }
          setShowTimeoutDialog(true);
          onTimeout?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, [onTimeout]);

  // Reset timer
  const resetTimer = useCallback(() => {
    setTimeRemaining(timeLimit);
    setShowTimeoutDialog(false);
    startTimer();
  }, [timeLimit, startTimer]);

  // Initialize timer when component mounts or item changes
  useEffect(() => {
    if (!readOnly && !audioUrl && timeLimit > 0) {
      startTimer();
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [readOnly, timeLimit, startTimer, currentItem.id]);

  // Stop timer when recording is complete
  useEffect(() => {
    if (audioUrl && timerRef.current) {
      clearInterval(timerRef.current);
    }
  }, [audioUrl]);

  // Reset state when item changes
  useEffect(() => {
    setAudioUrl(existingAudioUrl || undefined);
    setAssessmentResult(null);
    setTimeRemaining(timeLimit);
    setImageError(false);

    // Load existing assessment if available
    if (currentItem.ai_assessment) {
      const ai = currentItem.ai_assessment;
      setAssessmentResult({
        overallScore: ai.pronunciation_score || 0,
        accuracyScore: ai.accuracy_score || 0,
        fluencyScore: ai.fluency_score || 0,
        completenessScore: ai.completeness_score || 0,
        pronunciationScore: ai.pronunciation_score || 0,
        feedback: "",
      });
    }
  }, [currentItem.id, existingAudioUrl, timeLimit]);

  // Handle retry
  const handleRetry = () => {
    setShowTimeoutDialog(false);
    setAudioUrl(undefined);
    setAssessmentResult(null);
    resetTimer();
    onRetry?.();
  };

  // Handle skip
  const handleSkip = () => {
    setShowTimeoutDialog(false);
    onSkip?.();
  };

  const isLowTime = timeRemaining <= 2 && timeRemaining > 0;

  // Play example audio
  const handlePlayExample = () => {
    if (!exampleAudioRef.current || !currentItem.audio_url) return;

    if (isPlayingExample) {
      exampleAudioRef.current.pause();
    } else {
      exampleAudioRef.current.play();
    }
    setIsPlayingExample(!isPlayingExample);
  };

  // Upload analysis in background
  const uploadAnalysisInBackground = async (
    audioBlob: Blob,
    analysisResult: AssessmentResult,
  ) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const formData = new FormData();

      const uploadFileExtension = audioBlob.type.includes("mp4")
        ? "recording.mp4"
        : audioBlob.type.includes("webm")
          ? "recording.webm"
          : "recording.audio";

      formData.append("audio_file", audioBlob, uploadFileExtension);
      formData.append(
        "analysis_json",
        JSON.stringify({
          pronunciation_score: analysisResult.pronunciationScore,
          accuracy_score: analysisResult.accuracyScore,
          fluency_score: analysisResult.fluencyScore,
          completeness_score: analysisResult.completenessScore,
          overall_score: analysisResult.overallScore,
        }),
      );

      if (_progressId) {
        formData.append("progress_id", _progressId.toString());
      }

      fetch(`${apiUrl}/api/speech/upload-analysis`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${import.meta.env.VITE_STUDENT_TOKEN || ""}`,
        },
        body: formData,
      })
        .then(async (response) => {
          if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
          }
          console.log("Background upload completed for word reading");
        })
        .catch((error) => {
          console.error("Background upload failed:", error);
        });
    } catch (error) {
      console.error("Failed to prepare background upload:", error);
    }
  };

  // Handle assessment
  const handleAssessment = async () => {
    if (!audioUrl) {
      toast.error(t("wordReading.toast.missingData") || "請先錄音");
      return;
    }

    setIsAssessing(true);
    try {
      const response = await fetch(audioUrl);
      const audioBlob = await response.blob();

      // Use Azure Speech Service for analysis
      const azureResult = await analyzePronunciation(
        audioBlob,
        currentItem.text,
      );

      if (!azureResult) {
        throw new Error("Azure analysis failed");
      }

      const result: AssessmentResult = {
        overallScore: azureResult.pronunciationScore,
        accuracyScore: azureResult.accuracyScore,
        fluencyScore: azureResult.fluencyScore,
        completenessScore: azureResult.completenessScore,
        pronunciationScore: azureResult.pronunciationScore,
        feedback: "",
      };

      setAssessmentResult(result);
      toast.success(t("wordReading.toast.aiComplete") || "AI 評估完成");

      // Background upload
      if (!readOnly && audioUrl.startsWith("blob:")) {
        uploadAnalysisInBackground(audioBlob, result);
      }

      onAssessmentComplete?.(result);
    } catch (error) {
      console.error("Assessment error:", error);
      toast.error(
        error instanceof Error ? error.message : "AI 評估失敗，請重試",
      );
    } finally {
      setIsAssessing(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBadgeVariant = (score: number) => {
    if (score >= 80) return "default";
    if (score >= 60) return "secondary";
    return "destructive";
  };

  return (
    <>
      <div className="flex flex-col lg:flex-row items-start gap-6 lg:gap-8 min-h-[400px]">
        {/* Left Side - Word Card with Image */}
        <div className="flex-shrink-0 w-full lg:w-auto">
          <Card className="p-4 lg:p-6 bg-gradient-to-br from-blue-50 to-purple-50">
            {/* Image Area */}
            {showImage && (
              <div className="w-full lg:w-64 h-48 lg:h-56 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden mb-4">
                {currentItem.image_url && !imageError ? (
                  <img
                    src={currentItem.image_url}
                    alt={currentItem.text}
                    className="w-full h-full object-cover"
                    onError={() => setImageError(true)}
                  />
                ) : (
                  <div className="flex flex-col items-center text-gray-400">
                    <ImageIcon className="w-16 h-16" />
                    <span className="text-sm mt-2">
                      {t("wordReading.noImage") || "No Image"}
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Word Display */}
            <div className="text-center space-y-2">
              {/* Part of Speech */}
              {currentItem.part_of_speech && (
                <Badge variant="outline" className="text-xs">
                  {currentItem.part_of_speech}
                </Badge>
              )}

              {/* The Word */}
              <h2 className="text-3xl lg:text-4xl font-bold text-gray-900">
                {currentItem.text}
              </h2>

              {/* Translation */}
              {showTranslation && currentItem.translation && (
                <p className="text-lg text-gray-600">
                  {currentItem.translation}
                </p>
              )}

              {/* Example Audio Button */}
              {currentItem.audio_url && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePlayExample}
                  className="mt-2"
                >
                  <Volume2
                    className={cn(
                      "w-4 h-4 mr-2",
                      isPlayingExample && "text-blue-600 animate-pulse",
                    )}
                  />
                  {isPlayingExample
                    ? t("wordReading.stopAudio") || "Stop"
                    : t("wordReading.playAudio") || "Play Audio"}
                </Button>
              )}
            </div>

            {/* Progress Indicator */}
            <div className="mt-4 text-center text-sm text-gray-500">
              {t("wordReading.progress", {
                current: currentIndex + 1,
                total: totalItems,
              }) || `${currentIndex + 1} / ${totalItems}`}
            </div>
          </Card>
        </div>

        {/* Right Side - Recording Area */}
        <div className="flex-1 space-y-4 w-full">
          {/* Timer Display */}
          {!readOnly && timeLimit > 0 && !audioUrl && (
            <div className="flex justify-end">
              <div
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium",
                  isLowTime
                    ? "bg-red-100 text-red-700 animate-pulse"
                    : "bg-gray-100 text-gray-700",
                )}
              >
                <Clock className="h-4 w-4" />
                <span>{formatTime(timeRemaining)}</span>
              </div>
            </div>
          )}

          {/* Recording Time Limit Notice */}
          <div className="text-center text-sm text-gray-500">
            <p>
              {t("wordReading.recordingLimit") ||
                "Recording limit: max 5 seconds"}
            </p>
          </div>

          {/* Audio Recorder */}
          <AudioRecorder
            existingAudioUrl={audioUrl}
            onRecordingComplete={(blob, url) => {
              setAudioUrl(url);
              onRecordingComplete?.(blob, url);
            }}
            readOnly={readOnly}
            autoStop={timeLimit}
            variant="default"
            showProgress={true}
            showTimer={true}
          />

          {/* Assessment Button */}
          <div className="flex justify-center pt-4">
            {audioUrl && !readOnly && !assessmentResult && (
              <Button
                onClick={handleAssessment}
                disabled={isAssessing}
                className="bg-blue-500 hover:bg-blue-600 dark:bg-blue-400 dark:hover:bg-blue-500 text-white"
              >
                {isAssessing ? (
                  <>
                    <Brain className="h-4 w-4 mr-2 animate-spin" />
                    {t("wordReading.analyzing") || "AI Analyzing..."}
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4 mr-2" />
                    {t("wordReading.uploadAndAssess") || "Upload & Assess"}
                  </>
                )}
              </Button>
            )}
          </div>

          {/* Assessment Results */}
          {assessmentResult && (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-lg p-6 space-y-6">
              <div className="text-center">
                <h4 className="text-xl font-bold text-blue-900 mb-4 flex items-center justify-center gap-2">
                  <Brain className="h-6 w-6" />
                  {t("wordReading.aiResult") || "AI Assessment Result"}
                </h4>

                {/* Overall Score */}
                <div className="bg-white rounded-lg p-6 shadow-sm mb-4">
                  <div className="text-4xl font-bold text-blue-600 mb-2">
                    {assessmentResult.overallScore}
                    {t("wordReading.points") || " Points"}
                  </div>
                  <Badge
                    variant={getScoreBadgeVariant(
                      assessmentResult.overallScore,
                    )}
                    className="text-sm px-3 py-1"
                  >
                    {t("wordReading.overallScore") || "Overall Score"}
                  </Badge>
                </div>
              </div>

              {/* Detailed Scores */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">
                    {t("wordReading.accuracy") || "Accuracy"}
                  </div>
                  <div
                    className={`text-lg font-bold ${getScoreColor(assessmentResult.accuracyScore)}`}
                  >
                    {assessmentResult.accuracyScore}
                  </div>
                </div>
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">
                    {t("wordReading.fluency") || "Fluency"}
                  </div>
                  <div
                    className={`text-lg font-bold ${getScoreColor(assessmentResult.fluencyScore)}`}
                  >
                    {assessmentResult.fluencyScore}
                  </div>
                </div>
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">
                    {t("wordReading.completeness") || "Completeness"}
                  </div>
                  <div
                    className={`text-lg font-bold ${getScoreColor(assessmentResult.completenessScore)}`}
                  >
                    {assessmentResult.completenessScore}
                  </div>
                </div>
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">
                    {t("wordReading.pronunciation") || "Pronunciation"}
                  </div>
                  <div
                    className={`text-lg font-bold ${getScoreColor(assessmentResult.pronunciationScore)}`}
                  >
                    {assessmentResult.pronunciationScore}
                  </div>
                </div>
              </div>

              {/* Teacher Feedback (if available) */}
              {currentItem.teacher_feedback && (
                <div className="bg-white rounded-lg p-4">
                  <h5 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                    <Star className="h-4 w-4" />
                    {t("wordReading.teacherFeedback") || "Teacher Feedback"}
                  </h5>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    {currentItem.teacher_feedback}
                  </p>
                  {currentItem.teacher_passed !== undefined && (
                    <Badge
                      variant={
                        currentItem.teacher_passed ? "default" : "destructive"
                      }
                      className="mt-2"
                    >
                      {currentItem.teacher_passed
                        ? t("wordReading.passed") || "Passed"
                        : t("wordReading.needsCorrection") ||
                          "Needs Correction"}
                    </Badge>
                  )}
                </div>
              )}

              {/* Re-assess Button */}
              {!readOnly && (
                <div className="text-center">
                  <Button
                    onClick={() => setAssessmentResult(null)}
                    variant="outline"
                    size="sm"
                    className="border-blue-200 text-blue-700 hover:bg-blue-50"
                  >
                    {t("wordReading.reassess") || "Re-assess"}
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Hidden Audio Element for Example Audio */}
      {currentItem.audio_url && (
        <audio
          ref={exampleAudioRef}
          src={currentItem.audio_url}
          onEnded={() => setIsPlayingExample(false)}
        />
      )}

      {/* Timeout Dialog */}
      <Dialog open={showTimeoutDialog} onOpenChange={setShowTimeoutDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-orange-600">
              <Clock className="h-5 w-5" />
              {t("wordReading.timeUp") || "Time's Up!"}
            </DialogTitle>
            <DialogDescription>
              {t("wordReading.timeUpDescription") ||
                "Recording time has ended. You can retry or skip to the next word."}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={handleRetry}
              className="flex items-center gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              {t("wordReading.retry") || "Retry"}
            </Button>
            {onSkip && (
              <Button onClick={handleSkip} className="flex items-center gap-2">
                <SkipForward className="h-4 w-4" />
                {t("wordReading.skip") || "Skip"}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
