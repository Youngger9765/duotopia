import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';
import {
  Mic,
  MicOff,
  Play,
  Pause,
  RotateCcw,
  Send,
  Clock,
  Target,
  ChevronLeft,
  CheckCircle,
  Upload,
  // Star
} from 'lucide-react';
import { AssignmentDetail as AssignmentDetailType } from '@/types';

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

export default function AssignmentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [assignment, setAssignment] = useState<AssignmentDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [recordings, setRecordings] = useState<Map<number, Blob>>(new Map());
  const [isPlaying, setIsPlaying] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [assessmentResults, setAssessmentResults] = useState<Map<number, AssessmentResult>>(new Map());
  const [assessing, setAssessing] = useState(false);
  const [, setRecordingItemIndex] = useState<number | null>(null); // 記住正在錄音的題目（內部狀態）

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    loadAssignmentDetail();
  }, [id]);

  const loadAssignmentDetail = async () => {
    try {
      setLoading(true);
      // 學生應該使用學生的 API endpoint
      const response = await apiClient.get<{
        data?: {
          title?: string;
          activities?: Array<{
            items?: Array<{
              text?: string;
              translation?: string;
              audio_url?: string;
            }>;
          }>;
        };
      }>(`/api/students/assignments/${id}/activities`);

      // 將 activities API 的資料轉換成 AssignmentDetail 格式
      if (response.data) {
        const responseData = response.data as {
          title?: string;
          status?: string;  // 從 API 獲取作業狀態
          activities?: Array<{
            items?: Array<{
              text?: string;
              translation?: string;
              audio_url?: string;
            }>;
            ai_assessments?: Array<AssessmentResult | null>;
            recordings?: string[];  // 從 API 獲取已保存的錄音
          }>;
        };

        const items = responseData.activities?.flatMap((activity) =>
          (activity.items || []).map(item => ({
            text: item.text || '',
            translation: item.translation,
            audio_url: item.audio_url
          }))
        ) || [];

        // 處理 AI 評分數據 - 使用新的統一陣列格式
        const newAssessmentResults = new Map<number, AssessmentResult>();
        const newRecordings = new Map<number, Blob>();
        let globalItemIndex = 0;

        responseData.activities?.forEach((activity) => {
          // 處理 AI 評估結果
          if (activity.ai_assessments && Array.isArray(activity.ai_assessments)) {
            // 新的陣列格式：每個 index 直接對應題目位置
            activity.ai_assessments.forEach((assessment, localIndex) => {
              if (assessment) {
                const currentGlobalIndex = globalItemIndex + localIndex;
                newAssessmentResults.set(currentGlobalIndex, assessment);
              }
            });
          }

          // 處理已保存的錄音（如果有）
          if (activity.recordings && Array.isArray(activity.recordings)) {
            activity.recordings.forEach((recordingUrl, localIndex) => {
              if (recordingUrl) {
                const currentGlobalIndex = globalItemIndex + localIndex;
                // 將錄音 URL 轉換為 Blob（這裡簡化處理，實際應從 URL 下載）
                // 暫時用佔位符，表示有錄音存在
                newRecordings.set(currentGlobalIndex, new Blob(['saved'], { type: 'audio/webm' }));
              }
            });
          }

          // 更新全局索引
          globalItemIndex += activity.items?.length || 1;
        });

        setAssessmentResults(newAssessmentResults);
        setRecordings(newRecordings);

        const assignmentData: AssignmentDetailType = {
          id: parseInt(id || '0'),
          title: responseData.title || '作業',
          description: '練習作業',
          content: {
            id: parseInt(id || '0'),
            title: responseData.title || '作業內容',
            type: 'reading_assessment',
            items: items,
            items_count: items.length,
            target_wpm: 100,
            target_accuracy: 90
          },
          status: (responseData.status as 'NOT_STARTED' | 'IN_PROGRESS' | 'SUBMITTED' | 'GRADED') || 'NOT_STARTED',
          submissions: [],
          created_at: new Date().toISOString()
        };
        setAssignment(assignmentData);
      }
    } catch (error) {
      console.error('Failed to load assignment:', error);
      toast.error('無法載入作業詳情');
      // 不要自動跳轉，讓用戶可以重試或手動返回
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });

      audioChunksRef.current = [];

      // 記住開始錄音時的題目 index
      const recordingIndex = currentItemIndex;
      setRecordingItemIndex(recordingIndex);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        // 使用錄音時的 index，而不是當前的 index
        setRecordings(prev => new Map(prev).set(recordingIndex, audioBlob));
        setRecordingItemIndex(null);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);

    } catch (error) {
      console.error('Failed to start recording:', error);
      toast.error('無法啟動錄音，請檢查麥克風權限');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      toast.success('錄音已儲存');
    }
  };

  const playRecording = (index: number) => {
    const recording = recordings.get(index);
    if (!recording) return;

    const url = URL.createObjectURL(recording);
    if (audioRef.current) {
      audioRef.current.src = url;
      audioRef.current.play();
      setIsPlaying(true);

      audioRef.current.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(url);
      };
    }
  };

  const deleteRecording = (index: number) => {
    setRecordings(prev => {
      const newMap = new Map(prev);
      newMap.delete(index);
      return newMap;
    });
    setAssessmentResults(prev => {
      const newMap = new Map(prev);
      newMap.delete(index);
      return newMap;
    });
    toast.info('錄音已刪除');
  };

  const assessPronunciation = async (index: number) => {
    const recording = recordings.get(index);
    const currentItemText = assignment?.content.items?.[index]?.text;

    if (!recording || !currentItemText) {
      toast.error('無錄音檔案或參考文本');
      return;
    }

    try {
      setAssessing(true);

      // 創建 FormData
      const formData = new FormData();
      formData.append('audio_file', recording, 'recording.webm');
      formData.append('reference_text', currentItemText);
      formData.append('progress_id', `${index + 1}`); // 暫時使用 index 作為 progress_id
      formData.append('assignment_id', id || ''); // 加入 assignment ID

      const response = await apiClient.post<{ data?: Record<string, unknown> }>('/api/speech/assess', formData);

      if (response.data) {
        setAssessmentResults(prev => new Map(prev).set(index, response.data as AssessmentResult));
        toast.success('AI 發音評測完成！');
      }

    } catch (error) {
      console.error('Assessment failed:', error);
      toast.error('評測失敗，請稍後再試');
    } finally {
      setAssessing(false);
    }
  };

  const submitAssignment = async (e?: React.MouseEvent) => {
    console.log('🔥 [DEBUG] submitAssignment 被呼叫了！');
    console.log('🔥 [DEBUG] Event:', e);

    // 防止預設行為和事件冒泡
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (!assignment) {
      console.log('🔥 [DEBUG] No assignment, returning');
      return;
    }

    // 檢查是否所有項目都有錄音
    const itemsLength = assignment.content.items?.length || 0;
    const missingRecordings = itemsLength - recordings.size;
    console.log('🔥 [DEBUG] Items length:', itemsLength);
    console.log('🔥 [DEBUG] Recordings size:', recordings.size);
    console.log('🔥 [DEBUG] Missing recordings:', missingRecordings);

    if (missingRecordings > 0) {
      toast.warning(`還有 ${missingRecordings} 個項目未錄音`);
      return;
    }

    console.log('🚀 [DEBUG] 開始提交作業');
    console.log('🚀 [DEBUG] Assignment ID:', id);
    console.log('🚀 [DEBUG] 當前 URL:', window.location.href);

    try {
      setSubmitting(true);

      // 這裡應該要上傳錄音檔案到雲端儲存
      // 然後提交作業資料
      const submissionData = {
        recordings: Array.from(recordings.entries()).map(([index]) => ({
          item_index: index,
          audio_url: `mock://recording-${index}`, // 實際應上傳到 GCS
          duration: 5, // 實際應計算錄音長度
          transcript: assignment.content.items?.[index]?.text || ''
        })),
        completed_at: new Date().toISOString()
      };

      console.log('🚀 [DEBUG] 提交數據:', submissionData);
      console.log('🚀 [DEBUG] API endpoint:', `/api/students/assignments/${id}/submit`);

      const response = await apiClient.post(`/api/students/assignments/${id}/submit`, submissionData);

      console.log('🚀 [DEBUG] 提交成功！響應:', response);
      toast.success('作業提交成功！');

      // 直接跳轉到包含 /detail 的正確 URL
      const targetUrl = `/student/assignment/${id}/detail`;
      console.log('🚀 [DEBUG] 準備跳轉到:', targetUrl);
      console.log('🚀 [DEBUG] 目前的 location.href:', window.location.href);
      console.log('🚀 [DEBUG] 目前的 location.pathname:', window.location.pathname);

      // 強制跳轉，使用 setTimeout 確保 toast 顯示
      setTimeout(() => {
        console.log('🚀 [DEBUG] 執行跳轉！');
        console.log('🚀 [DEBUG] window.location.href = ', targetUrl);
        window.location.href = targetUrl;
        console.log('🚀 [DEBUG] 跳轉指令已執行');
      }, 500);

    } catch (error: unknown) {
      console.error('❌ [DEBUG] 提交失敗:', error);
      if (error instanceof Error) {
        console.error('❌ [DEBUG] 錯誤類型:', error.constructor.name);
        console.error('❌ [DEBUG] 錯誤訊息:', error.message);
        console.error('❌ [DEBUG] 錯誤堆疊:', error.stack);
      }
      toast.error('提交失敗，請稍後再試');
    } finally {
      console.log('🚀 [DEBUG] finally 區塊執行');
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">載入中...</p>
        </div>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-gray-600">找不到作業</p>
          <Button onClick={() => navigate('/student/dashboard')} className="mt-4">
            返回作業列表
          </Button>
        </div>
      </div>
    );
  }

  const currentItem = assignment.content.items?.[currentItemIndex];
  const itemsLength = assignment.content.items?.length || 0;
  const progress = itemsLength > 0 ? ((currentItemIndex + 1) / itemsLength) * 100 : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <audio ref={audioRef} className="hidden" />

      {/* Header */}
      <div className="max-w-4xl mx-auto mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate('/student/dashboard')}
          className="mb-4"
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          返回作業列表
        </Button>

        {/* 狀態提示 */}
        {(assignment.status === 'SUBMITTED' || assignment.status === 'GRADED') && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-blue-600" />
            <span className="text-blue-700">
              {assignment.status === 'SUBMITTED' ? '作業已提交，目前為檢視模式' : '作業已評分，目前為檢視模式'}
            </span>
          </div>
        )}

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl">{assignment.title}</CardTitle>
                {assignment.instructions && (
                  <p className="text-gray-600 mt-2">{assignment.instructions}</p>
                )}
              </div>
              <Badge className={
                assignment.status === 'GRADED' ? 'bg-green-100 text-green-800' :
                assignment.status === 'SUBMITTED' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }>
                {assignment.status === 'NOT_STARTED' ? '未開始' :
                 assignment.status === 'IN_PROGRESS' ? '進行中' :
                 assignment.status === 'SUBMITTED' ? '已提交' :
                 assignment.status === 'GRADED' ? '已評分' : assignment.status}
              </Badge>
            </div>

            {/* 目標指標 */}
            <div className="flex gap-4 mt-4">
              {assignment.content.target_wpm && (
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    目標語速: {assignment.content.target_wpm} WPM
                  </span>
                </div>
              )}
              {assignment.content.target_accuracy && (
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    目標準確率: {assignment.content.target_accuracy}%
                  </span>
                </div>
              )}
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">進度</span>
            <span className="text-sm font-medium">
              {currentItemIndex + 1} / {itemsLength}
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Recording Card */}
        <Card className="mb-6">
          <CardContent className="p-8">
            {currentItem ? (
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-2">{currentItem.text}</h3>
                {currentItem.translation && (
                  <p className="text-gray-600">{currentItem.translation}</p>
                )}
              </div>
            ) : (
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-2">無內容項目</h3>
              </div>
            )}

            {/* Recording Controls */}
            <div className="flex justify-center gap-4 mb-6">
              {!isRecording ? (
                <Button
                  size="lg"
                  onClick={startRecording}
                  className="bg-red-500 hover:bg-red-600"
                  disabled={assignment.status === 'GRADED' || assignment.status === 'SUBMITTED'}
                >
                  <Mic className="h-5 w-5 mr-2" />
                  開始錄音
                </Button>
              ) : (
                <Button
                  size="lg"
                  onClick={stopRecording}
                  className="bg-gray-500 hover:bg-gray-600"
                >
                  <MicOff className="h-5 w-5 mr-2" />
                  停止錄音
                </Button>
              )}

              {recordings.has(currentItemIndex) && (
                <>
                  <Button
                    size="lg"
                    variant="outline"
                    onClick={() => playRecording(currentItemIndex)}
                    disabled={isPlaying}
                  >
                    {isPlaying ? <Pause className="h-5 w-5 mr-2" /> : <Play className="h-5 w-5 mr-2" />}
                    播放
                  </Button>
                  <Button
                    size="lg"
                    variant="outline"
                    onClick={() => deleteRecording(currentItemIndex)}
                    className="text-red-600 hover:text-red-700"
                    disabled={assignment.status === 'GRADED' || assignment.status === 'SUBMITTED'}
                  >
                    <RotateCcw className="h-5 w-5 mr-2" />
                    重錄
                  </Button>
                </>
              )}
            </div>

            {/* Recording Status */}
            {recordings.has(currentItemIndex) && (
              <div className="text-center mb-4">
                <div className="text-green-600 mb-4">
                  <CheckCircle className="h-6 w-6 inline-block mr-2" />
                  已錄音
                </div>

                {/* 上傳與評測按鈕 */}
                {!assessmentResults.has(currentItemIndex) && (
                  <Button
                    size="lg"
                    onClick={() => assessPronunciation(currentItemIndex)}
                    disabled={assessing}
                    className="bg-blue-500 hover:bg-blue-600"
                  >
                    <Upload className="h-5 w-5 mr-2" />
                    {assessing ? '評測中...' : '上傳與評測'}
                  </Button>
                )}
              </div>
            )}

            {/* Assessment Results */}
            {assessmentResults.has(currentItemIndex) && (
              <div className="mt-6 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200">
                <div className="text-center mb-4">
                  <h4 className="text-xl font-bold text-blue-800 mb-2">🤖 AI 發音評測結果</h4>
                </div>

                {(() => {
                  const result = assessmentResults.get(currentItemIndex);
                  return (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="text-center p-3 bg-white rounded-lg shadow">
                        <div className="text-2xl font-bold text-blue-600">
                          {result?.pronunciation_score?.toFixed(1) || 0}
                        </div>
                        <div className="text-sm text-gray-600">總體分數</div>
                      </div>

                      <div className="text-center p-3 bg-white rounded-lg shadow">
                        <div className="text-2xl font-bold text-green-600">
                          {result?.accuracy_score?.toFixed(1) || 0}
                        </div>
                        <div className="text-sm text-gray-600">準確度</div>
                      </div>

                      <div className="text-center p-3 bg-white rounded-lg shadow">
                        <div className="text-2xl font-bold text-orange-600">
                          {result?.fluency_score?.toFixed(1) || 0}
                        </div>
                        <div className="text-sm text-gray-600">流暢度</div>
                      </div>

                      <div className="text-center p-3 bg-white rounded-lg shadow">
                        <div className="text-2xl font-bold text-purple-600">
                          {result?.completeness_score?.toFixed(1) || 0}
                        </div>
                        <div className="text-sm text-gray-600">完整度</div>
                      </div>
                    </div>
                  );
                })()}

                {/* 單字詳細評分 */}
                {(() => {
                  const result = assessmentResults.get(currentItemIndex);
                  const words = result?.words || [];

                  if (words.length > 0) {
                    return (
                      <div className="mt-4">
                        <h5 className="font-medium text-gray-700 mb-2">單字評分詳情：</h5>
                        <div className="flex flex-wrap gap-2">
                          {words.map((word, wordIndex: number) => (
                            <span
                              key={wordIndex}
                              className={`px-3 py-1 rounded-full text-sm font-medium ${
                                (word.accuracy_score || 0) >= 90
                                  ? 'bg-green-100 text-green-800 border-green-200 border'
                                  : (word.accuracy_score || 0) >= 70
                                  ? 'bg-yellow-100 text-yellow-800 border-yellow-200 border'
                                  : 'bg-red-100 text-red-800 border-red-200 border'
                              }`}
                            >
                              {word.word} ({word.accuracy_score?.toFixed(0) || 0})
                            </span>
                          ))}
                        </div>
                      </div>
                    );
                  }
                  return null;
                })()}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <Button
            variant="outline"
            onClick={() => setCurrentItemIndex(prev => Math.max(0, prev - 1))}
            disabled={currentItemIndex === 0}
          >
            上一題
          </Button>

          <div className="text-center">
            <p className="text-sm text-gray-600">
              已錄音: {recordings.size} / {itemsLength}
            </p>
          </div>

          {currentItemIndex < itemsLength - 1 ? (
            <Button
              onClick={() => setCurrentItemIndex(prev => prev + 1)}
              disabled={!recordings.has(currentItemIndex)}
            >
              下一題
            </Button>
          ) : (
            <Button
              onClick={submitAssignment}
              disabled={recordings.size !== itemsLength || submitting}
              className="bg-green-600 hover:bg-green-700"
            >
              <Send className="h-4 w-4 mr-2" />
              {submitting ? '提交中...' : '提交作業'}
            </Button>
          )}
        </div>
      </div>

      {/* Score Display (if graded) */}
      {assignment.status === 'GRADED' && assignment.score !== null && (
        <Card className="max-w-4xl mx-auto mt-6">
          <CardHeader>
            <CardTitle>評分結果</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center mb-4">
              <div className="text-4xl font-bold text-blue-600">{assignment.score}</div>
              <div className="text-gray-600">分數</div>
            </div>
            {assignment.feedback && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium mb-2">教師評語</h4>
                <p className="text-gray-700">{assignment.feedback}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
