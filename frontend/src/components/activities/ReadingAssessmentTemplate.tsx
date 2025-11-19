import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { Brain, Star, Mic } from "lucide-react";
import { toast } from "sonner";
import { retryAIAnalysis } from "@/utils/retryHelper";
import AudioRecorder from "@/components/shared/AudioRecorder";
import { useTranslation } from "react-i18next";

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
}

export default function ReadingAssessmentTemplate({
  content,
  targetText,
  existingAudioUrl,
  onRecordingComplete,
  exampleAudioUrl,
  progressId,
  readOnly = false,
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

  // const handlePlayExample = () => {
  //   if (!exampleAudioRef.current) return;

  //   if (isPlayingExample) {
  //     exampleAudioRef.current.pause();
  //   } else {
  //     exampleAudioRef.current.play();
  //   }
  //   setIsPlayingExample(!isPlayingExample);
  // };

  const handleAssessment = async () => {
    if (!audioUrl || !progressId) {
      toast.error(t("readingAssessment.toast.missingData"));
      return;
    }

    setIsAssessing(true);
    try {
      // Convert audioUrl to blob for upload
      const response = await fetch(audioUrl);
      const audioBlob = await response.blob();

      // Create form data
      const formData = new FormData();
      // 根據 blob 的 MIME type 決定檔案副檔名
      const fileExtension = audioBlob.type.includes("mp4")
        ? "recording.mp4"
        : audioBlob.type.includes("webm")
          ? "recording.webm"
          : "recording.audio";
      formData.append("audio_file", audioBlob, fileExtension);
      formData.append("reference_text", targetText);
      formData.append("progress_id", progressId.toString());

      // Get authentication token from store
      const { token } = useStudentAuthStore();
      if (!token) {
        toast.error(t("readingAssessment.toast.reloginRequired"));
        return;
      }

      // Call assessment API with retry mechanism
      const result = await retryAIAnalysis(
        async () => {
          const apiResponse = await fetch("/api/speech/assess", {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
            },
            body: formData,
          });

          if (!apiResponse.ok) {
            const errorData = await apiResponse
              .json()
              .catch(() => ({ detail: "AI Analysis failed" }));
            const error = new Error(
              errorData.detail || `AI Analysis failed: ${apiResponse.status}`,
            );
            if (apiResponse.status >= 500 || apiResponse.status === 429) {
              // Server errors and rate limits are retryable
              throw error;
            }
            // Client errors (4xx except 429) should not be retried
            throw Object.assign(error, { noRetry: true });
          }

          return await apiResponse.json();
        },
        (attempt, error) => {
          console.log(`AI 分析失敗，正在重試... (第 ${attempt}/3 次)`, error);
          toast.warning(t("readingAssessment.toast.aiRetrying", { attempt }));
        },
      );
      setAssessmentResult({
        overallScore: result.overall_score,
        accuracyScore: result.accuracy_score,
        fluencyScore: result.fluency_score,
        completenessScore: result.completeness_score,
        pronunciationScore: result.pronunciation_score,
        feedback: result.feedback,
      });

      toast.success(t("readingAssessment.toast.aiComplete"));
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
          autoStop={45}
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
                  variant={getScoreBadgeVariant(assessmentResult.overallScore)}
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
  );
}
