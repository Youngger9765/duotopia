import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useStudentAuthStore } from '@/stores/studentAuthStore';
import {
  Mic,
  MicOff,
  RotateCcw,
  CheckCircle,
  Brain,
  Star
} from 'lucide-react';
import { toast } from 'sonner';

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
  audioUrl?: string | null;
  isRecording: boolean;
  recordingTime: number;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onReRecord: () => void;
  formatTime: (seconds: number) => string;
  exampleAudioUrl?: string;
  progressId?: number;
}

export default function ReadingAssessmentTemplate({
  content,
  targetText,
  audioUrl,
  isRecording,
  recordingTime,
  onStartRecording,
  onStopRecording,
  onReRecord,
  formatTime,
  exampleAudioUrl,
  progressId
}: ReadingAssessmentProps) {
  const [, setIsPlayingExample] = useState(false);
  const [isAssessing, setIsAssessing] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState<AssessmentResult | null>(null);
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
      toast.error('錄音檔案或進度ID不存在');
      return;
    }

    setIsAssessing(true);
    try {
      // Convert audioUrl to blob for upload
      const response = await fetch(audioUrl);
      const audioBlob = await response.blob();

      // Create form data
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      formData.append('reference_text', targetText);
      formData.append('progress_id', progressId.toString());

      // Get authentication token from store
      const { token } = useStudentAuthStore();
      if (!token) {
        toast.error('請重新登入');
        return;
      }

      // Call assessment API
      const apiResponse = await fetch('/api/speech/assess', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!apiResponse.ok) {
        const errorData = await apiResponse.json().catch(() => ({ detail: '評估失敗' }));
        throw new Error(errorData.detail || '評估失敗');
      }

      const result = await apiResponse.json();
      setAssessmentResult({
        overallScore: result.overall_score,
        accuracyScore: result.accuracy_score,
        fluencyScore: result.fluency_score,
        completenessScore: result.completeness_score,
        pronunciationScore: result.pronunciation_score,
        feedback: result.feedback
      });

      toast.success('AI 發音評估完成！');
    } catch (error) {
      console.error('Assessment error:', error);
      toast.error(error instanceof Error ? error.message : 'AI 評估失敗，請重試');
    } finally {
      setIsAssessing(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeVariant = (score: number) => {
    if (score >= 80) return 'default';
    if (score >= 60) return 'secondary';
    return 'destructive';
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
          <p className="text-lg text-gray-600">
            {content}
          </p>
        </div>

        {/* Recording Button */}
        <div className="flex justify-start">
          {!isRecording && !audioUrl ? (
            <button
              onClick={onStartRecording}
              className="bg-blue-400 hover:bg-blue-500 text-white rounded-full p-6 transition-all duration-200 hover:scale-105 shadow-lg"
            >
              <Mic className="h-8 w-8" />
            </button>
          ) : isRecording ? (
            <button
              onClick={onStopRecording}
              className="bg-red-500 hover:bg-red-600 text-white rounded-full p-6 transition-all duration-200 animate-pulse shadow-lg"
            >
              <MicOff className="h-8 w-8" />
            </button>
          ) : null}
        </div>

        {/* Recording Timer */}
        {isRecording && (
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-red-600 font-medium">
              錄音中 {formatTime(recordingTime)}
            </span>
          </div>
        )}

        {/* Audio Player After Recording */}
        {audioUrl && (
          <div className="space-y-4">
            <audio
              controls
              src={audioUrl}
              className="w-full h-10"
            />
          </div>
        )}

        {/* Recording Status */}
        {audioUrl && (
          <div className="bg-green-100 border border-green-300 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="text-green-800 font-medium">已錄音</span>
            </div>
          </div>
        )}

        {/* Bottom Buttons */}
        <div className="flex space-x-4 pt-6">
          {audioUrl && (
            <>
              <Button
                variant="outline"
                onClick={onReRecord}
                className="border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                重新錄音
              </Button>

              {!assessmentResult && (
                <Button
                  onClick={handleAssessment}
                  disabled={isAssessing}
                  className="bg-blue-500 hover:bg-blue-600 text-white"
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
                <div className={`text-lg font-bold ${getScoreColor(assessmentResult.accuracyScore)}`}>
                  {assessmentResult.accuracyScore}分
                </div>
              </div>
              <div className="bg-white rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500 mb-1">流暢度</div>
                <div className={`text-lg font-bold ${getScoreColor(assessmentResult.fluencyScore)}`}>
                  {assessmentResult.fluencyScore}分
                </div>
              </div>
              <div className="bg-white rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500 mb-1">完整度</div>
                <div className={`text-lg font-bold ${getScoreColor(assessmentResult.completenessScore)}`}>
                  {assessmentResult.completenessScore}分
                </div>
              </div>
              <div className="bg-white rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500 mb-1">發音分數</div>
                <div className={`text-lg font-bold ${getScoreColor(assessmentResult.pronunciationScore)}`}>
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
