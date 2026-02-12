import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Brain, Star, Mic, Clock, RotateCcw, SkipForward } from "lucide-react";
import { toast } from "sonner";
import AudioRecorder from "@/components/shared/AudioRecorder";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import { useAzurePronunciation } from "@/hooks/useAzurePronunciation";
import { useDemoAzurePronunciation } from "@/hooks/useDemoAzurePronunciation";
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

interface ReadingAssessmentProps {
  content: string;
  targetText: string;
  existingAudioUrl?: string | null; // 現有的錄音（例如重刷頁面後）
  onRecordingComplete?: (blob: Blob, url: string) => void; // 錄音完成回調
  exampleAudioUrl?: string;
  progressId?: number;
  readOnly?: boolean; // 唯讀模式
  isDemoMode?: boolean; // Demo mode - uses public demo API endpoints
  timeLimit?: number; // 作答時間限制（秒）
  onTimeout?: () => void; // 超時回調
  onRetry?: () => void; // 重試回調
  onSkip?: () => void; // 跳過回調
}

export default function ReadingAssessmentTemplate({
  content,
  targetText,
  existingAudioUrl,
  onRecordingComplete,
  exampleAudioUrl,
  progressId: _progressId, // Legacy prop (not used with Azure direct calls)
  readOnly = false,
  isDemoMode = false,
  timeLimit = 30, // 預設 30 秒
  onTimeout,
  onRetry,
  onSkip,
}: ReadingAssessmentProps) {
  const { t } = useTranslation();
  const [audioUrl, setAudioUrl] = useState<string | undefined>(
    existingAudioUrl || undefined,
  );
  const [, setIsPlayingExample] = useState(false);
  const [isAssessing, setIsAssessing] = useState(false);
  const [assessmentResult, setAssessmentResult] =
    useState<AssessmentResult | null>(null);
  const exampleAudioRef = useRef<HTMLAudioElement>(null);

  // 🚀 Azure Speech Service hook for direct API calls
  // Use demo hook when in demo mode (no authentication required)
  const regularHook = useAzurePronunciation();
  const demoHook = useDemoAzurePronunciation();
  const { analyzePronunciation } = isDemoMode ? demoHook : regularHook;

  // 計時器狀態
  const [timeRemaining, setTimeRemaining] = useState(timeLimit);
  const [showTimeoutDialog, setShowTimeoutDialog] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // 格式化時間
  const formatTime = useCallback((seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }, []);

  // 啟動計時器
  const startTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    timerRef.current = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          // 時間到
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

  // 重置計時器
  const resetTimer = useCallback(() => {
    setTimeRemaining(timeLimit);
    setShowTimeoutDialog(false);
    startTimer();
  }, [timeLimit, startTimer]);

  // 初始化計時器
  useEffect(() => {
    if (!readOnly && !audioUrl && timeLimit > 0) {
      startTimer();
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [readOnly, timeLimit, startTimer]);

  // 錄音完成時停止計時器
  useEffect(() => {
    if (audioUrl && timerRef.current) {
      clearInterval(timerRef.current);
    }
  }, [audioUrl]);

  // 處理重試
  const handleRetry = () => {
    setShowTimeoutDialog(false);
    setAudioUrl(undefined);
    setAssessmentResult(null);
    resetTimer();
    onRetry?.();
  };

  // 處理跳過
  const handleSkip = () => {
    setShowTimeoutDialog(false);
    onSkip?.();
  };

  const isLowTime = timeRemaining <= 10 && timeRemaining > 0;

  // const handlePlayExample = () => {
  //   if (!exampleAudioRef.current) return;

  //   if (isPlayingExample) {
  //     exampleAudioRef.current.pause();
  //   } else {
  //     exampleAudioRef.current.play();
  //   }
  //   setIsPlayingExample(!isPlayingExample);
  // };

  /**
   * 背景上傳音檔和分析結果（不阻塞 UI）
   */
  const uploadAnalysisInBackground = async (
    audioBlob: Blob,
    analysisResult: AssessmentResult,
  ) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "";
      const formData = new FormData();

      // 決定檔案副檔名
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

      // 🎯 Issue #208: Generate unique analysis_id for deduction
      const analysisId = crypto.randomUUID();
      formData.append("analysis_id", analysisId);

      // 背景上傳（不等待結果）
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
          console.log("✅ Background upload completed");
        })
        .catch((error) => {
          console.error("❌ Background upload failed:", error);
        });
    } catch (error) {
      console.error("Failed to prepare background upload:", error);
    }
  };

  const handleAssessment = async () => {
    if (!audioUrl) {
      toast.error(t("readingAssessment.toast.missingData"));
      return;
    }

    setIsAssessing(true);
    try {
      // Convert audioUrl to blob for analysis
      const response = await fetch(audioUrl);
      const audioBlob = await response.blob();

      // 🚀 先分析（快速顯示結果）
      const azureResult = await analyzePronunciation(audioBlob, targetText);

      if (!azureResult) {
        throw new Error("Azure analysis failed");
      }

      // ⚡ 立即顯示結果（用戶無需等待上傳）
      const result: AssessmentResult = {
        overallScore: azureResult.pronunciationScore,
        accuracyScore: azureResult.accuracyScore,
        fluencyScore: azureResult.fluencyScore,
        completenessScore: azureResult.completenessScore,
        pronunciationScore: azureResult.pronunciationScore,
        feedback: "", // Azure doesn't provide feedback text
      };

      setAssessmentResult(result);
      toast.success(t("readingAssessment.toast.aiComplete"));

      // 🎯 背景上傳（不阻塞 UI）
      if (!readOnly && audioUrl.startsWith("blob:")) {
        uploadAnalysisInBackground(audioBlob, result);
      }
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
      <div className="flex items-start space-x-8 min-h-[500px]">
        {/* Left Side - Avatar/Icon Circle */}
        <div className="flex-shrink-0">
          <div className="w-48 h-48 bg-gray-200 rounded-full flex items-center justify-center">
            <div className="w-24 h-24 bg-gray-400 rounded-full flex items-center justify-center">
              <Mic className="h-12 w-12 text-gray-600" />
            </div>
          </div>
        </div>

        {/* Right Side - Content Area */}
        <div className="flex-1 space-y-6">
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

          {/* Example Audio Section */}
          {exampleAudioUrl && (
            <div className="space-y-2">
              <audio
                ref={exampleAudioRef}
                src={exampleAudioUrl}
                controls
                className="w-full h-10"
                onEnded={() => setIsPlayingExample(false)}
              />
            </div>
          )}

          {/* Main Content */}
          <div className="space-y-4">
            <h2 className="text-3xl font-medium text-gray-900 leading-relaxed">
              {targetText}
            </h2>
            <p className="text-lg text-gray-600">{content}</p>
          </div>

          {/* 🎯 錄音元件 - 使用統一的 AudioRecorder */}
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

          {/* Bottom Buttons */}
          <div className="flex space-x-4 pt-6">
            {audioUrl && !readOnly && (
              <>
                {!assessmentResult && (
                  <Button
                    onClick={handleAssessment}
                    disabled={isAssessing}
                    className="bg-blue-500 hover:bg-blue-600 dark:bg-blue-400 dark:hover:bg-blue-500 text-white"
                  >
                    {isAssessing ? (
                      <>
                        <Brain className="h-4 w-4 mr-2 animate-spin" />
                        AI 評估中...
                      </>
                    ) : (
                      <>
                        <Brain className="h-4 w-4 mr-2" />
                        上傳與評測
                      </>
                    )}
                  </Button>
                )}
              </>
            )}
          </div>

          {/* Assessment Results */}
          {assessmentResult && (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-lg p-6 space-y-6 mt-6">
              <div className="text-center">
                <h4 className="text-xl font-bold text-blue-900 mb-4 flex items-center justify-center gap-2">
                  <Brain className="h-6 w-6" />
                  AI 評估結果
                </h4>

                {/* Overall Score */}
                <div className="bg-white rounded-lg p-6 shadow-sm mb-4">
                  <div className="text-4xl font-bold text-blue-600 mb-2">
                    {assessmentResult.overallScore}分
                  </div>
                  <Badge
                    variant={getScoreBadgeVariant(
                      assessmentResult.overallScore,
                    )}
                    className="text-sm px-3 py-1"
                  >
                    總體評分
                  </Badge>
                </div>
              </div>

              {/* Detailed Scores */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">準確度</div>
                  <div
                    className={`text-lg font-bold ${getScoreColor(assessmentResult.accuracyScore)}`}
                  >
                    {assessmentResult.accuracyScore}分
                  </div>
                </div>
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">流暢度</div>
                  <div
                    className={`text-lg font-bold ${getScoreColor(assessmentResult.fluencyScore)}`}
                  >
                    {assessmentResult.fluencyScore}分
                  </div>
                </div>
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">完整度</div>
                  <div
                    className={`text-lg font-bold ${getScoreColor(assessmentResult.completenessScore)}`}
                  >
                    {assessmentResult.completenessScore}分
                  </div>
                </div>
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">發音分數</div>
                  <div
                    className={`text-lg font-bold ${getScoreColor(assessmentResult.pronunciationScore)}`}
                  >
                    {assessmentResult.pronunciationScore}分
                  </div>
                </div>
              </div>

              {/* AI Feedback */}
              {assessmentResult.feedback && (
                <div className="bg-white rounded-lg p-4">
                  <h5 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                    <Star className="h-4 w-4" />
                    AI 建議
                  </h5>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    {assessmentResult.feedback}
                  </p>
                </div>
              )}

              <div className="text-center">
                <Button
                  onClick={() => setAssessmentResult(null)}
                  variant="outline"
                  size="sm"
                  className="border-blue-200 text-blue-700 hover:bg-blue-50"
                >
                  重新評估
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Timeout Dialog */}
      <Dialog open={showTimeoutDialog} onOpenChange={setShowTimeoutDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-orange-600">
              <Clock className="h-5 w-5" />
              時間到了！
            </DialogTitle>
            <DialogDescription>
              作答時間已結束。您可以選擇重新作答此題，或跳到下一題繼續。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={handleRetry}
              className="flex items-center gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              重新作答
            </Button>
            {onSkip && (
              <Button onClick={handleSkip} className="flex items-center gap-2">
                <SkipForward className="h-4 w-4" />
                跳到下一題
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
