import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { useStudentAuthStore } from '@/stores/studentAuthStore';
import { toast } from 'sonner';
import {
  ChevronLeft,
  ChevronRight,
  Play,
  Pause,
  Mic,
  MicOff,
  RotateCcw,
  Send,
  Volume2,
  CheckCircle,
  Circle,
  Clock,
  Loader2
} from 'lucide-react';

interface Question {
  id: number;
  order: number;
  type: 'reading' | 'listening' | 'speaking';
  title: string;
  content: string;
  audioUrl?: string;
  targetText?: string;
  duration?: number;
  points: number;
}

interface Answer {
  questionId: number;
  audioBlob?: Blob;
  audioUrl?: string;
  textAnswer?: string;
  startTime: Date;
  endTime?: Date;
  status: 'not_started' | 'in_progress' | 'completed';
}

export default function StudentActivityPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const navigate = useNavigate();
  useStudentAuthStore(); // Will use token when API is connected

  // State management
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Map<number, Answer>>(new Map());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Audio playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackTime, setPlaybackTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const recordingInterval = useRef<NodeJS.Timeout | null>(null);

  // Mock questions for demonstration
  useEffect(() => {
    loadQuestions();
  }, [assignmentId]);

  const loadQuestions = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API call
      const mockQuestions: Question[] = [
        {
          id: 1,
          order: 1,
          type: 'listening',
          title: '聽力測驗 - 日常對話',
          content: 'Listen to the conversation and answer the questions.',
          audioUrl: '/audio/conversation1.mp3',
          duration: 120,
          points: 20
        },
        {
          id: 2,
          order: 2,
          type: 'reading',
          title: '朗讀測驗 - 短文朗讀',
          content: 'The quick brown fox jumps over the lazy dog. This pangram contains all letters of the English alphabet.',
          targetText: 'The quick brown fox jumps over the lazy dog.',
          duration: 60,
          points: 15
        },
        {
          id: 3,
          order: 3,
          type: 'speaking',
          title: '口說測驗 - 自我介紹',
          content: 'Please introduce yourself in English. Include your name, age, hobbies, and favorite subject.',
          duration: 90,
          points: 25
        },
        {
          id: 4,
          order: 4,
          type: 'listening',
          title: '聽力測驗 - 短文理解',
          content: 'Listen to the passage and summarize the main points.',
          audioUrl: '/audio/passage1.mp3',
          duration: 180,
          points: 20
        },
        {
          id: 5,
          order: 5,
          type: 'reading',
          title: '朗讀測驗 - 詩歌朗讀',
          content: 'Roses are red, violets are blue. Sugar is sweet, and so are you.',
          targetText: 'Roses are red, violets are blue.',
          duration: 45,
          points: 20
        }
      ];

      setQuestions(mockQuestions);

      // Initialize answers for all questions
      const initialAnswers = new Map<number, Answer>();
      mockQuestions.forEach(q => {
        initialAnswers.set(q.id, {
          questionId: q.id,
          status: 'not_started',
          startTime: new Date()
        });
      });
      setAnswers(initialAnswers);
    } catch (error) {
      console.error('Failed to load questions:', error);
      toast.error('無法載入題目');
    } finally {
      setLoading(false);
    }
  };

  // Audio playback controls
  const handlePlayPause = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleReplay = () => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = 0;
    audioRef.current.play();
    setIsPlaying(true);
  };

  // Recording controls
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          setAudioChunks(prev => [...prev, event.data]);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const currentQuestion = questions[currentQuestionIndex];

        setAnswers(prev => {
          const newAnswers = new Map(prev);
          const answer = newAnswers.get(currentQuestion.id) || {
            questionId: currentQuestion.id,
            status: 'not_started',
            startTime: new Date()
          };

          answer.audioBlob = audioBlob;
          answer.audioUrl = URL.createObjectURL(audioBlob);
          answer.status = 'completed';
          answer.endTime = new Date();

          newAnswers.set(currentQuestion.id, answer);
          return newAnswers;
        });

        // Clean up
        stream.getTracks().forEach(track => track.stop());
        setAudioChunks([]);
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0);

      // Start recording timer
      recordingInterval.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Failed to start recording:', error);
      toast.error('無法啟動錄音，請檢查麥克風權限');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setMediaRecorder(null);
      setIsRecording(false);

      if (recordingInterval.current) {
        clearInterval(recordingInterval.current);
        recordingInterval.current = null;
      }
    }
  };

  const reRecord = () => {
    const currentQuestion = questions[currentQuestionIndex];
    setAnswers(prev => {
      const newAnswers = new Map(prev);
      const answer = newAnswers.get(currentQuestion.id);
      if (answer) {
        answer.audioBlob = undefined;
        answer.audioUrl = undefined;
        answer.status = 'in_progress';
      }
      newAnswers.set(currentQuestion.id, answer!);
      return newAnswers;
    });
    startRecording();
  };

  // Navigation
  const handleNextQuestion = async () => {
    await autoSave();
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePreviousQuestion = async () => {
    await autoSave();
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleQuestionSelect = async (index: number) => {
    await autoSave();
    setCurrentQuestionIndex(index);
  };

  // Auto-save functionality
  const autoSave = async () => {
    try {
      setSaving(true);
      // API call to save current answer
      await new Promise(resolve => setTimeout(resolve, 500)); // Mock save
      console.log('Auto-saved answer for question', currentQuestionIndex + 1);
    } catch (error) {
      console.error('Failed to auto-save:', error);
    } finally {
      setSaving(false);
    }
  };

  // Final submission
  const handleSubmit = async () => {
    const unanswered = Array.from(answers.values()).filter(
      a => a.status === 'not_started'
    );

    if (unanswered.length > 0) {
      const confirm = window.confirm(
        `還有 ${unanswered.length} 題未作答，確定要提交嗎？`
      );
      if (!confirm) return;
    }

    try {
      setSubmitting(true);
      // API call to submit all answers
      await new Promise(resolve => setTimeout(resolve, 1000)); // Mock submit
      toast.success('作業提交成功！');
      navigate(`/student/assignment/${assignmentId}`);
    } catch (error) {
      console.error('Failed to submit:', error);
      toast.error('提交失敗，請稍後再試');
    } finally {
      setSubmitting(false);
    }
  };

  // Format time display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600">載入題目中...</p>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const currentAnswer = answers.get(currentQuestion.id);
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header with progress */}
      <div className="sticky top-0 bg-white border-b z-10">
        <div className="max-w-6xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <Button
              variant="ghost"
              onClick={() => navigate(`/student/assignment/${assignmentId}`)}
            >
              <ChevronLeft className="h-4 w-4 mr-2" />
              返回作業
            </Button>

            <div className="flex items-center gap-4">
              {saving && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  自動儲存中...
                </div>
              )}
              <Button
                onClick={handleSubmit}
                disabled={submitting}
                variant="default"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    提交中...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    提交作業
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Question navigation tabs */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {questions.map((q, index) => {
              const answer = answers.get(q.id);
              const isActive = index === currentQuestionIndex;
              const isCompleted = answer?.status === 'completed';

              return (
                <Button
                  key={q.id}
                  variant={isActive ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleQuestionSelect(index)}
                  className="flex-shrink-0"
                >
                  <div className="flex items-center gap-2">
                    {isCompleted ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : answer?.status === 'in_progress' ? (
                      <Clock className="h-4 w-4 text-yellow-500" />
                    ) : (
                      <Circle className="h-4 w-4" />
                    )}
                    <span>第 {q.order} 題</span>
                  </div>
                </Button>
              );
            })}
          </div>

          {/* Overall progress */}
          <Progress value={progress} className="h-2" />
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-4xl mx-auto p-4 mt-6">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-2xl mb-2">
                  第 {currentQuestion.order} 題：{currentQuestion.title}
                </CardTitle>
                <Badge variant="outline">
                  {currentQuestion.type === 'listening' && '聽力測驗'}
                  {currentQuestion.type === 'reading' && '朗讀測驗'}
                  {currentQuestion.type === 'speaking' && '口說測驗'}
                </Badge>
              </div>
              <Badge className="bg-blue-100 text-blue-800">
                {currentQuestion.points} 分
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Question content */}
            <div className="bg-gray-50 rounded-lg p-6">
              <p className="text-lg leading-relaxed">{currentQuestion.content}</p>

              {/* Display target text for reading questions */}
              {currentQuestion.type === 'reading' && currentQuestion.targetText && (
                <div className="mt-4 p-4 bg-white rounded-lg border-2 border-blue-200">
                  <p className="text-xl font-medium text-blue-900 leading-relaxed">
                    {currentQuestion.targetText}
                  </p>
                </div>
              )}
            </div>

            {/* Audio player for listening questions */}
            {currentQuestion.type === 'listening' && currentQuestion.audioUrl && (
              <div className="bg-blue-50 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium flex items-center gap-2">
                    <Volume2 className="h-5 w-5" />
                    音檔播放
                  </h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleReplay}
                  >
                    <RotateCcw className="h-4 w-4 mr-2" />
                    重播
                  </Button>
                </div>

                <div className="flex items-center gap-4">
                  <Button
                    onClick={handlePlayPause}
                    size="lg"
                    className="rounded-full"
                  >
                    {isPlaying ? (
                      <Pause className="h-6 w-6" />
                    ) : (
                      <Play className="h-6 w-6" />
                    )}
                  </Button>

                  <div className="flex-1">
                    <Progress
                      value={(playbackTime / audioDuration) * 100}
                      className="h-2"
                    />
                    <div className="flex justify-between text-xs text-gray-600 mt-1">
                      <span>{formatTime(Math.floor(playbackTime))}</span>
                      <span>{formatTime(Math.floor(audioDuration))}</span>
                    </div>
                  </div>
                </div>

                <audio
                  ref={audioRef}
                  src={currentQuestion.audioUrl}
                  onTimeUpdate={(e) => setPlaybackTime(e.currentTarget.currentTime)}
                  onLoadedMetadata={(e) => setAudioDuration(e.currentTarget.duration)}
                  onEnded={() => setIsPlaying(false)}
                />
              </div>
            )}

            <Separator />

            {/* Answer section */}
            <div>
              <h3 className="font-medium mb-4 flex items-center gap-2">
                <Mic className="h-5 w-5" />
                作答區
              </h3>

              {/* Recording controls for speaking/reading questions */}
              {(currentQuestion.type === 'speaking' || currentQuestion.type === 'reading') && (
                <div className="space-y-4">
                  <div className="flex items-center justify-center gap-4">
                    {!isRecording && !currentAnswer?.audioUrl ? (
                      <Button
                        onClick={startRecording}
                        size="lg"
                        className="bg-red-600 hover:bg-red-700"
                      >
                        <Mic className="h-5 w-5 mr-2" />
                        開始錄音
                      </Button>
                    ) : isRecording ? (
                      <>
                        <Button
                          onClick={stopRecording}
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
                    ) : currentAnswer?.audioUrl ? (
                      <div className="w-full space-y-4">
                        <div className="bg-green-50 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-green-800 font-medium">
                              已完成錄音
                            </span>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={reRecord}
                            >
                              <RotateCcw className="h-4 w-4 mr-2" />
                              重新錄音
                            </Button>
                          </div>
                          <audio
                            controls
                            src={currentAnswer.audioUrl}
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
                        💡 提示：請清晰地朗讀或回答，完成後點擊停止錄音
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Text answer for listening questions */}
              {currentQuestion.type === 'listening' && (
                <div className="space-y-4">
                  <Textarea
                    placeholder="請輸入你的答案..."
                    className="min-h-[150px]"
                    value={currentAnswer?.textAnswer || ''}
                    onChange={(e) => {
                      const value = e.target.value;
                      setAnswers(prev => {
                        const newAnswers = new Map(prev);
                        const answer = newAnswers.get(currentQuestion.id) || {
                          questionId: currentQuestion.id,
                          status: 'not_started',
                          startTime: new Date()
                        };
                        answer.textAnswer = value;
                        answer.status = value ? 'completed' : 'in_progress';
                        newAnswers.set(currentQuestion.id, answer);
                        return newAnswers;
                      });
                    }}
                  />
                </div>
              )}
            </div>

            <Separator />

            {/* Navigation buttons */}
            <div className="flex items-center justify-between">
              <Button
                variant="outline"
                onClick={handlePreviousQuestion}
                disabled={currentQuestionIndex === 0}
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                上一題
              </Button>

              <span className="text-sm text-gray-600">
                {currentQuestionIndex + 1} / {questions.length}
              </span>

              {currentQuestionIndex < questions.length - 1 ? (
                <Button
                  onClick={handleNextQuestion}
                >
                  下一題
                  <ChevronRight className="h-4 w-4 ml-2" />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={submitting}
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      提交中...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      完成並提交
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Status summary */}
        <Card className="mt-6">
          <CardContent className="pt-6">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {Array.from(answers.values()).filter(a => a.status === 'completed').length}
                </div>
                <p className="text-sm text-gray-600">已完成</p>
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-600">
                  {Array.from(answers.values()).filter(a => a.status === 'in_progress').length}
                </div>
                <p className="text-sm text-gray-600">進行中</p>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-400">
                  {Array.from(answers.values()).filter(a => a.status === 'not_started').length}
                </div>
                <p className="text-sm text-gray-600">未開始</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
