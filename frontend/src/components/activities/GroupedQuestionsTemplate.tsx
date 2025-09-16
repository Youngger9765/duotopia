import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { useStudentAuthStore } from '@/stores/studentAuthStore';
import {
  CheckCircle,
  Mic,
  Square,
  Play,
  Pause,
  Volume2,
  Brain,
  Loader2,
  Star
} from 'lucide-react';

interface Question {
  text?: string;
  translation?: string;
  audio_url?: string;
  [key: string]: unknown;
}

interface AssessmentResult {
  pronunciation_score?: number;
  accuracy_score?: number;
  fluency_score?: number;
  completeness_score?: number;
  words?: Array<{
    accuracy_score?: number;
    word?: string;
    error_type?: string;
  }>;
  word_details?: Array<{
    accuracy_score?: number;
    word?: string;
    error_type?: string;
  }>;
  error_type?: string;
}

interface GroupedQuestionsTemplateProps {
  items: Question[];
  recordings?: string[];
  answers?: string[];
  currentQuestionIndex?: number;
  isRecording?: boolean;
  recordingTime?: number;
  onStartRecording?: () => void;
  onStopRecording?: () => void;
  formatTime?: (seconds: number) => string;
  progressId?: number | string;
  initialAssessmentResults?: Record<string, unknown>; // AI 評估結果
}

export default function GroupedQuestionsTemplate({
  items,
  recordings = [],
  answers = [],
  currentQuestionIndex = 0,
  isRecording = false,
  recordingTime = 0,
  onStartRecording,
  onStopRecording,
  formatTime = (s) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`,
  progressId,
  initialAssessmentResults
}: GroupedQuestionsTemplateProps) {
  const currentQuestion = items[currentQuestionIndex];
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isAssessing, setIsAssessing] = useState(false);
  const [assessmentResults, setAssessmentResults] = useState<Record<number, AssessmentResult>>(() => {
    // 如果有初始 AI 評分，處理多題目的評分結構
    if (initialAssessmentResults && Object.keys(initialAssessmentResults).length > 0) {
      // 檢查是否有多題目的評分結構 (items)
      if (initialAssessmentResults.items && typeof initialAssessmentResults.items === 'object') {
        const itemsResults: Record<number, AssessmentResult> = {};
        const items = initialAssessmentResults.items as Record<string, unknown>;

        // 將 items 中的評分轉換為數字索引的結果
        Object.keys(items).forEach(key => {
          const index = parseInt(key);
          if (!isNaN(index) && items[key]) {
            itemsResults[index] = items[key] as AssessmentResult;
          }
        });

        return itemsResults;
      }
      // 如果這是一個單獨的評分結果（不是分組的）
      else if (!Object.prototype.hasOwnProperty.call(initialAssessmentResults, '0')) {
        return { 0: initialAssessmentResults as AssessmentResult };
      }
      return initialAssessmentResults as Record<number, AssessmentResult>;
    }
    return {};
  });
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const { token } = useStudentAuthStore();

  // 檢查題目是否已完成
  const isQuestionCompleted = (index: number) => {
    return recordings[index] || answers[index];
  };

  // 播放/暫停音檔
  const togglePlayback = () => {
    if (!recordings[currentQuestionIndex]) return;

    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    } else {
      if (audioRef.current) {
        audioRef.current.pause();
      }

      const audio = new Audio(recordings[currentQuestionIndex]);
      audioRef.current = audio;

      audio.addEventListener('loadedmetadata', () => {
        const dur = audio.duration;
        if (dur && isFinite(dur) && !isNaN(dur)) {
          setDuration(dur);
        }
      });

      audio.addEventListener('ended', () => {
        setIsPlaying(false);
        setCurrentTime(0);
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      });

      audio.play();
      setIsPlaying(true);

      progressIntervalRef.current = setInterval(() => {
        if (audioRef.current) {
          setCurrentTime(audioRef.current.currentTime);
        }
      }, 100);
    }
  };

  // 清理音檔播放和重置狀態
  useEffect(() => {
    // Reset states when switching questions
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);

    // Clean up previous audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }

    // Preload duration for current recording if it exists
    if (recordings[currentQuestionIndex]) {
      const tempAudio = new Audio(recordings[currentQuestionIndex]);
      tempAudio.addEventListener('loadedmetadata', () => {
        const dur = tempAudio.duration;
        if (dur && isFinite(dur) && !isNaN(dur)) {
          setDuration(dur);
        } else {
          setDuration(0);
        }
      });
      // Trigger load
      tempAudio.load();
    }

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, [currentQuestionIndex, recordings]);

  // 格式化時間
  const formatAudioTime = (seconds: number) => {
    if (!seconds || !isFinite(seconds) || isNaN(seconds)) {
      return '0:00';
    }
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // AI 發音評估
  const handleAssessment = async () => {
    const audioUrl = recordings[currentQuestionIndex];
    const referenceText = currentQuestion?.text;

    if (!audioUrl || !referenceText) {
      toast.error('請先錄音並確保有參考文本');
      return;
    }

    setIsAssessing(true);
    try {
      // Convert blob URL to blob
      const response = await fetch(audioUrl);
      const audioBlob = await response.blob();

      // Create form data
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      formData.append('reference_text', referenceText);
      formData.append('progress_id', String(progressId || '1')); // Use actual progress ID
      formData.append('item_index', String(currentQuestionIndex)); // 傳遞題目索引

      // Get authentication token from store
      if (!token) {
        toast.error('請重新登入');
        return;
      }

      // Call API
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const assessResponse = await fetch(`${apiUrl}/api/speech/assess`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!assessResponse.ok) {
        throw new Error('評估失敗');
      }

      const result = await assessResponse.json();

      // Store result
      setAssessmentResults(prev => ({
        ...prev,
        [currentQuestionIndex]: result
      }));

      toast.success('AI 發音評估完成！');
    } catch (error) {
      console.error('Assessment error:', error);
      toast.error('AI 評估失敗，請稍後再試');
    } finally {
      setIsAssessing(false);
    }
  };


  return (
    <div className="space-y-6">
      {/* 題目狀態標籤 */}
      <div className="flex items-center justify-between">
        <Badge className="bg-blue-100 text-blue-800">
          第 {currentQuestionIndex + 1} 題 / 共 {items.length} 題
        </Badge>
        {isQuestionCompleted(currentQuestionIndex) && (
          <Badge className="bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3 mr-1" />
            已完成
          </Badge>
        )}
      </div>

      {/* 題目內容區 - 左右分欄 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 bg-gray-50 rounded-lg">
        {/* 左側：圖片區域 */}
        <div className="flex items-center justify-center">
          <div className="w-full max-w-md aspect-square bg-gray-200 rounded-lg flex items-center justify-center">
            <div className="text-center text-gray-500">
              <svg className="w-24 h-24 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-sm font-medium">圖片預留位置</p>
              <p className="text-xs mt-1">Mock Image Placeholder</p>
            </div>
          </div>
        </div>

        {/* 右側：題目資訊 */}
        <div className="space-y-4">
          {/* 1. 題目文字 - 永遠顯示 */}
          <div className="relative p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="absolute -top-3 left-4 px-2 bg-white">
              <span className="text-sm font-semibold text-blue-600 flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                題目
              </span>
            </div>
            <div className="text-xl font-medium text-gray-800 leading-relaxed mt-2">
              {currentQuestion?.text || <span className="text-gray-400 italic">無題目文字</span>}
            </div>
          </div>

          {/* 2. 老師的參考音檔 - 永遠顯示 */}
          <div className="relative p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="absolute -top-3 left-4 px-2 bg-white">
              <span className="text-sm font-semibold text-green-600 flex items-center gap-1">
                <Volume2 className="w-4 h-4" />
                參考音檔
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (currentQuestion?.audio_url) {
                  const audio = new Audio(currentQuestion.audio_url);
                  audio.play();
                }
              }}
              disabled={!currentQuestion?.audio_url}
              className="w-full mt-2"
            >
              <Volume2 className="w-4 h-4 mr-2" />
              {currentQuestion?.audio_url ? '播放老師錄音' : '無參考音檔'}
            </Button>
          </div>

          {/* 3. 翻譯 - 永遠顯示 */}
          <div className="relative p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="absolute -top-3 left-4 px-2 bg-white">
              <span className="text-sm font-semibold text-purple-600 flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                </svg>
                中文翻譯
              </span>
            </div>
            <div className="text-lg text-gray-600 mt-2">
              {currentQuestion?.translation || <span className="text-gray-400 italic">無翻譯</span>}
            </div>
          </div>
        </div>
      </div>

      {/* 學生作答錄音區 */}
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">學生作答區</h3>
        <div className="flex items-center justify-center">
          {!isRecording ? (
            <Button
              size="lg"
              className="bg-red-600 hover:bg-red-700 text-white"
              onClick={() => {
                // Clear AI assessment results when starting new recording
                setAssessmentResults(prev => {
                  const newResults = { ...prev };
                  delete newResults[currentQuestionIndex];
                  return newResults;
                });
                onStartRecording?.();
              }}
            >
              <Mic className="w-5 h-5 mr-2" />
              開始錄音
            </Button>
          ) : (
            <div className="flex flex-col items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
                <span className="text-lg font-medium">{formatTime(recordingTime)}</span>
              </div>
              <Button
                size="lg"
                variant="outline"
                onClick={onStopRecording}
                className="border-red-600 text-red-600 hover:bg-red-50"
              >
                <Square className="w-5 h-5 mr-2" />
                停止錄音
              </Button>
            </div>
          )}
        </div>

        {/* 2. 錄音結果區 - 固定顯示 */}
        <div className="mt-6">
          {recordings[currentQuestionIndex] ? (
            <div className="max-w-lg mx-auto">
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 border border-green-200 shadow-sm">
                <div className="flex items-center gap-4">
                  {/* 播放/暫停按鈕 */}
                  <button
                    onClick={togglePlayback}
                    className="flex-shrink-0 w-14 h-14 bg-green-600 hover:bg-green-700 transition-colors rounded-full flex items-center justify-center text-white shadow-md"
                  >
                    {isPlaying ? (
                      <Pause className="w-6 h-6" fill="currentColor" />
                    ) : (
                      <Play className="w-6 h-6 ml-1" fill="currentColor" />
                    )}
                  </button>

                  {/* 音檔資訊與時間軸 */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-gray-800">已錄製音檔</span>
                    </div>

                    {/* 時間軸 */}
                    <div className="flex items-center gap-3">
                      <div className="flex-1 relative h-2 bg-green-200 rounded-full overflow-hidden">
                        <div
                          className="absolute h-full bg-green-500 rounded-full transition-all duration-100"
                          style={{
                            width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%'
                          }}
                        />
                        {/* 播放點 */}
                        {duration > 0 && isPlaying && (
                          <div
                            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-green-600 rounded-full shadow-sm"
                            style={{
                              left: `calc(${(currentTime / duration) * 100}% - 6px)`
                            }}
                          />
                        )}
                      </div>

                      {/* 只顯示總時長 */}
                      <span className="text-xs text-gray-600 font-medium min-w-[35px]">
                        {formatAudioTime(duration || 0)}
                      </span>
                    </div>
                  </div>

                  {/* 重錄按鈕 */}
                  <button
                    onClick={() => {
                      if (audioRef.current) {
                        audioRef.current.pause();
                      }
                      setIsPlaying(false);
                      setCurrentTime(0);
                      if (onStartRecording) {
                        // Clear current recording
                        recordings[currentQuestionIndex] = '';
                        onStartRecording();
                      }
                    }}
                    className="flex-shrink-0 w-10 h-10 flex items-center justify-center text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full transition-all"
                    title="重新錄音"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-lg mx-auto min-h-[100px] bg-gray-50 rounded-xl border-2 border-dashed border-gray-200 flex items-center justify-center">
              <div className="text-center text-gray-400">
                <Mic className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm font-medium">錄音結果將顯示於此</p>
                <p className="text-xs mt-1">點擊上方錄音按鈕開始錄音</p>
              </div>
            </div>
          )}
        </div>

        {/* 3. AI 評估按鈕區 - 智慧顯示 */}
        <div className="mt-6 flex justify-center min-h-[60px] items-center">
          {!recordings[currentQuestionIndex] ? (
            <div className="text-gray-400 text-sm">請先錄音後進行 AI 評估</div>
          ) : assessmentResults[currentQuestionIndex] ? (
            <div className="text-center">
              <div className="text-green-600 text-sm flex items-center justify-center mb-1">
                <Brain className="w-4 h-4 mr-1" />
                AI 評估已完成
              </div>
              <div className="text-xs text-gray-500">重新錄音將清除評估結果</div>
            </div>
          ) : (
            <Button
              size="lg"
              onClick={handleAssessment}
              disabled={isAssessing}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
            >
              {isAssessing ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  AI 評估中...
                </>
              ) : (
                <>
                  <Brain className="w-5 h-5 mr-2" />
                  AI 發音評估
                </>
              )}
            </Button>
          )}
        </div>

        {/* 4. AI 評估結果區 - 固定顯示 */}
        <div className="mt-6">
          {assessmentResults[currentQuestionIndex] ? (
            <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-600" />
                  AI 發音評估結果
                </h4>
                <button
                  onClick={() => {
                    setAssessmentResults(prev => {
                      const newResults = { ...prev };
                      delete newResults[currentQuestionIndex];
                      return newResults;
                    });
                  }}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  清除結果
                </button>
              </div>

              {/* 總體分數 */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {assessmentResults[currentQuestionIndex].pronunciation_score?.toFixed(1) || '0'}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">總體發音</div>
                </div>
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {assessmentResults[currentQuestionIndex].accuracy_score?.toFixed(1) || '0'}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">準確度</div>
                </div>
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {assessmentResults[currentQuestionIndex].fluency_score?.toFixed(1) || '0'}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">流暢度</div>
                </div>
                <div className="bg-white rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {assessmentResults[currentQuestionIndex].completeness_score?.toFixed(1) || '0'}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">完整度</div>
                </div>
              </div>

              {/* 單字詳細評分 */}
              {assessmentResults[currentQuestionIndex] && (assessmentResults[currentQuestionIndex].words || assessmentResults[currentQuestionIndex].word_details) &&
               ((assessmentResults[currentQuestionIndex].words?.length || 0) > 0 || (assessmentResults[currentQuestionIndex].word_details?.length || 0) > 0) && (
                <div className="space-y-2">
                  <h5 className="text-sm font-semibold text-gray-700 mb-2">單字發音詳情：</h5>
                  <div className="flex flex-wrap gap-2">
                    {(assessmentResults[currentQuestionIndex].words || assessmentResults[currentQuestionIndex].word_details)?.map((word, idx: number) => {
                      const score = word.accuracy_score || 0;
                      // const scoreColor = score >= 80 ? 'green' : score >= 60 ? 'yellow' : 'red';
                      const bgColor = score >= 80 ? 'bg-green-100' : score >= 60 ? 'bg-yellow-100' : 'bg-red-100';
                      const borderColor = score >= 80 ? 'border-green-300' : score >= 60 ? 'border-yellow-300' : 'border-red-300';
                      const textColor = score >= 80 ? 'text-green-800' : score >= 60 ? 'text-yellow-800' : 'text-red-800';

                      return (
                        <div
                          key={idx}
                          className={`${bgColor} ${borderColor} ${textColor} border rounded-lg px-3 py-1.5 text-sm font-medium`}
                        >
                          <span className="font-semibold">{word.word}</span>
                          <span className="ml-2 text-xs opacity-80">({score})</span>
                          {word.error_type && word.error_type !== 'None' && (
                            <span className="ml-1 text-xs">⚠️</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 建議區域 */}
              <div className="mt-4 pt-4 border-t border-purple-200">
                <div className="flex items-start gap-2">
                  <Star className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-gray-700">
                    {(assessmentResults[currentQuestionIndex]?.pronunciation_score || 0) >= 80 ? (
                      <span className="font-medium text-green-700">表現優秀！繼續保持這樣的發音水準。</span>
                    ) : (assessmentResults[currentQuestionIndex]?.pronunciation_score || 0) >= 60 ? (
                      <span className="font-medium text-yellow-700">不錯！注意準確度和流暢度的平衡。</span>
                    ) : (
                      <span className="font-medium text-red-700">需要更多練習，特別注意標示的單字發音。</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="min-h-[300px] bg-gray-50 rounded-xl border-2 border-dashed border-gray-200 flex items-center justify-center">
              <div className="text-center text-gray-400">
                <Brain className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm font-medium">等待 AI 評估結果</p>
                <p className="text-xs mt-1">錄音後點擊評估按鈕</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
