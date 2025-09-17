import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import {
  Mic,
  MicOff,
  RotateCcw,
  CheckCircle,
  MessageCircle,
  Lightbulb,
  Clock
} from 'lucide-react';

interface SpeakingPracticeProps {
  topic: string;
  prompts: string[];
  suggestedDuration: number;
  audioUrl?: string | null;
  isRecording: boolean;
  recordingTime: number;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onReRecord: () => void;
  formatTime: (seconds: number) => string;
  readOnly?: boolean; // 唯讀模式
}

export default function SpeakingPracticeTemplate({
  topic,
  prompts,
  suggestedDuration,
  audioUrl,
  isRecording,
  recordingTime,
  onStartRecording,
  onStopRecording,
  onReRecord,
  formatTime,
  readOnly = false
}: SpeakingPracticeProps) {
  const [showHints, setShowHints] = useState(false);

  return (
    <div className="space-y-6">
      {/* Topic and Instructions */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6">
        <h3 className="font-medium mb-3 flex items-center gap-2">
          <MessageCircle className="h-5 w-5" />
          口說練習主題
        </h3>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">{topic}</h2>

        <div className="space-y-3">
          <p className="text-gray-700">請根據以下提示進行口說練習：</p>
          <ul className="space-y-2">
            {prompts.map((prompt, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-blue-600 font-bold">{index + 1}.</span>
                <span className="text-gray-700">{prompt}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-4 flex items-center gap-4">
          <Badge variant="secondary" className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            建議時長：{suggestedDuration} 秒
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowHints(!showHints)}
          >
            <Lightbulb className="h-4 w-4 mr-2" />
            {showHints ? '隱藏提示' : '顯示提示'}
          </Button>
        </div>

        {/* Speaking hints */}
        {showHints && (
          <Card className="mt-4 p-4 bg-yellow-50 border-yellow-200">
            <h4 className="font-medium mb-2 flex items-center gap-2 text-yellow-900">
              <Lightbulb className="h-4 w-4" />
              口說提示
            </h4>
            <ul className="space-y-1 text-sm text-yellow-800">
              <li>• 先組織你的想法，再開始說話</li>
              <li>• 使用連接詞讓語句更流暢</li>
              <li>• 注意時態的正確使用</li>
              <li>• 保持自然的語速和語調</li>
            </ul>
          </Card>
        )}
      </div>

      {/* Recording Section */}
      <div className="bg-white rounded-lg border p-6">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <Mic className="h-5 w-5" />
          錄音作答
        </h3>

        <div className="space-y-4">
          {/* Recording controls */}
          <div className="flex flex-col items-center gap-4">
            {!isRecording && !audioUrl ? (
              <>
                <Button
                  onClick={onStartRecording}
                  size="lg"
                  className="bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={readOnly}
                >
                  <Mic className="h-5 w-5 mr-2" />
                  {readOnly ? '檢視模式' : '開始錄音'}
                </Button>
                <p className="text-sm text-gray-600">
                  {readOnly ? '檢視模式中無法錄音' : '準備好後，點擊開始錄音進行口說練習'}
                </p>
              </>
            ) : isRecording ? (
              <>
                <div className="flex items-center gap-4">
                  <Button
                    onClick={onStopRecording}
                    size="lg"
                    variant="outline"
                  >
                    <MicOff className="h-5 w-5 mr-2" />
                    停止錄音
                  </Button>
                  <Badge variant="destructive" className="animate-pulse text-lg px-4 py-2">
                    錄音中 {formatTime(recordingTime)}
                  </Badge>
                </div>

                {/* Progress indicator */}
                <div className="w-full max-w-md">
                  <div className="relative pt-1">
                    <div className="flex mb-2 items-center justify-between">
                      <div>
                        <span className="text-xs font-semibold inline-block text-red-600">
                          正在錄音
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-semibold inline-block text-gray-600">
                          {Math.min(100, Math.round((recordingTime / suggestedDuration) * 100))}%
                        </span>
                      </div>
                    </div>
                    <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-red-100">
                      <div
                        style={{ width: `${Math.min(100, (recordingTime / suggestedDuration) * 100)}%` }}
                        className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-red-500 transition-all duration-500"
                      />
                    </div>
                  </div>
                </div>
              </>
            ) : audioUrl ? (
              <div className="w-full space-y-4">
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-green-800 font-medium flex items-center gap-2">
                      <CheckCircle className="h-5 w-5" />
                      已完成錄音
                    </span>
                    {!readOnly && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={onReRecord}
                      >
                        <RotateCcw className="h-4 w-4 mr-2" />
                        重新錄音
                      </Button>
                    )}
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

          {/* Tips during recording */}
          {isRecording && (
            <Card className="p-4 bg-blue-50 border-blue-200">
              <p className="text-sm text-blue-800">
                💡 請根據題目提示進行口說，注意：
                <span className="block mt-1">• 保持流暢，不要長時間停頓</span>
                <span className="block">• 清晰表達你的想法</span>
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
