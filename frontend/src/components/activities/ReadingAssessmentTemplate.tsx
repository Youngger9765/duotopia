import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Mic,
  MicOff,
  RotateCcw,
  CheckCircle,
  BookOpen,
  Volume2,
  Play,
  Pause
} from 'lucide-react';

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
  exampleAudioUrl
}: ReadingAssessmentProps) {
  const [isPlayingExample, setIsPlayingExample] = useState(false);
  const exampleAudioRef = useRef<HTMLAudioElement>(null);

  const handlePlayExample = () => {
    if (!exampleAudioRef.current) return;

    if (isPlayingExample) {
      exampleAudioRef.current.pause();
    } else {
      exampleAudioRef.current.play();
    }
    setIsPlayingExample(!isPlayingExample);
  };

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="font-medium mb-3 flex items-center gap-2">
          <BookOpen className="h-5 w-5" />
          題目說明
        </h3>
        <p className="text-lg leading-relaxed mb-4">{content}</p>

        {/* Target text for reading */}
        <div className="mt-4 p-6 bg-white rounded-lg border-2 border-blue-200">
          <h4 className="text-sm font-medium text-gray-600 mb-3">請朗讀以下內容：</h4>
          <p className="text-xl font-medium text-blue-900 leading-relaxed">
            {targetText}
          </p>
        </div>

        {/* Example audio if available */}
        {exampleAudioUrl && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-blue-900 flex items-center gap-2">
                <Volume2 className="h-4 w-4" />
                範例發音
              </h4>
              <Button
                size="sm"
                variant="outline"
                onClick={handlePlayExample}
              >
                {isPlayingExample ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" />
                    暫停
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    播放範例
                  </>
                )}
              </Button>
            </div>
            <audio
              ref={exampleAudioRef}
              src={exampleAudioUrl}
              onEnded={() => setIsPlayingExample(false)}
              className="hidden"
            />
          </div>
        )}
      </div>

      <Separator />

      {/* Recording section */}
      <div>
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <Mic className="h-5 w-5" />
          錄音作答
        </h3>

        <div className="space-y-4">
          <div className="flex items-center justify-center gap-4">
            {!isRecording && !audioUrl ? (
              <Button
                onClick={onStartRecording}
                size="lg"
                className="bg-red-600 hover:bg-red-700"
              >
                <Mic className="h-5 w-5 mr-2" />
                開始錄音
              </Button>
            ) : isRecording ? (
              <>
                <Button
                  onClick={onStopRecording}
                  size="lg"
                  variant="outline"
                >
                  <MicOff className="h-5 w-5 mr-2" />
                  停止錄音
                </Button>
                <Badge variant="destructive" className="animate-pulse">
                  錄音中 {formatTime(recordingTime)}
                </Badge>
              </>
            ) : audioUrl ? (
              <div className="w-full space-y-4">
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-green-800 font-medium flex items-center gap-2">
                      <CheckCircle className="h-5 w-5" />
                      已完成錄音
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={onReRecord}
                    >
                      <RotateCcw className="h-4 w-4 mr-2" />
                      重新錄音
                    </Button>
                  </div>
                  <audio
                    controls
                    src={audioUrl}
                    className="w-full"
                  />
                </div>
              </div>
            ) : null}
          </div>

          {/* Recording tips */}
          {isRecording && (
            <div className="bg-yellow-50 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                💡 提示：請清晰地朗讀題目中的內容，注意發音和語調
              </p>
            </div>
          )}

          {/* Instructions for recording */}
          {!isRecording && !audioUrl && (
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                請點擊「開始錄音」按鈕，然後清晰地朗讀上方的英文內容。
                錄音完成後，系統會自動儲存您的答案。
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
