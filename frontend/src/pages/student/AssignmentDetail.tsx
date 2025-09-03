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
  CheckCircle
} from 'lucide-react';

interface AssignmentContent {
  id: number;
  type: string;
  title: string;
  items: Array<{
    text: string;
    translation?: string;
    audio_url?: string;
  }>;
  target_wpm?: number;
  target_accuracy?: number;
}

interface AssignmentDetailData {
  id: number;
  title: string;
  instructions?: string;
  status: string;
  due_date?: string;
  score?: number;
  feedback?: string;
  content: AssignmentContent;
}

export default function AssignmentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [assignment, setAssignment] = useState<AssignmentDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentItemIndex, setCurrentItemIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [recordings, setRecordings] = useState<Map<number, Blob>>(new Map());
  const [isPlaying, setIsPlaying] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    loadAssignmentDetail();
  }, [id]);

  const loadAssignmentDetail = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/api/teachers/assignments/${id}/detail`);
      setAssignment(response.data);
    } catch (error) {
      console.error('Failed to load assignment:', error);
      toast.error('無法載入作業詳情');
      navigate('/student/dashboard');
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

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setRecordings(prev => new Map(prev).set(currentItemIndex, audioBlob));
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
    toast.info('錄音已刪除');
  };

  const submitAssignment = async () => {
    if (!assignment) return;

    // 檢查是否所有項目都有錄音
    const missingRecordings = assignment.content.items.length - recordings.size;
    if (missingRecordings > 0) {
      toast.warning(`還有 ${missingRecordings} 個項目未錄音`);
      return;
    }

    try {
      setSubmitting(true);

      // 這裡應該要上傳錄音檔案到雲端儲存
      // 然後提交作業資料
      const submissionData = {
        recordings: Array.from(recordings.entries()).map(([index, blob]) => ({
          item_index: index,
          audio_url: `mock://recording-${index}`, // 實際應上傳到 GCS
          duration: 5, // 實際應計算錄音長度
          transcript: assignment.content.items[index].text
        })),
        completed_at: new Date().toISOString()
      };

      await apiClient.post(`/api/teachers/assignments/${id}/submit`, submissionData);

      toast.success('作業提交成功！');
      navigate('/student/dashboard');

    } catch (error) {
      console.error('Failed to submit assignment:', error);
      toast.error('提交失敗，請稍後再試');
    } finally {
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

  const currentItem = assignment.content.items[currentItemIndex];
  const progress = ((currentItemIndex + 1) / assignment.content.items.length) * 100;

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
              {currentItemIndex + 1} / {assignment.content.items.length}
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Recording Card */}
        <Card className="mb-6">
          <CardContent className="p-8">
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold mb-2">{currentItem.text}</h3>
              {currentItem.translation && (
                <p className="text-gray-600">{currentItem.translation}</p>
              )}
            </div>

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
                  >
                    <RotateCcw className="h-5 w-5 mr-2" />
                    重錄
                  </Button>
                </>
              )}
            </div>

            {/* Recording Status */}
            {recordings.has(currentItemIndex) && (
              <div className="text-center text-green-600">
                <CheckCircle className="h-6 w-6 inline-block mr-2" />
                已完成錄音
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
              已錄音: {recordings.size} / {assignment.content.items.length}
            </p>
          </div>

          {currentItemIndex < assignment.content.items.length - 1 ? (
            <Button
              onClick={() => setCurrentItemIndex(prev => prev + 1)}
              disabled={!recordings.has(currentItemIndex)}
            >
              下一題
            </Button>
          ) : (
            <Button
              onClick={submitAssignment}
              disabled={recordings.size !== assignment.content.items.length || submitting}
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
