import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useStudentAuthStore } from '@/stores/studentAuthStore';
import { toast } from 'sonner';
import ReadingAssessmentTemplate from '@/components/activities/ReadingAssessmentTemplate';
import ListeningClozeTemplate from '@/components/activities/ListeningClozeTemplate';
import SpeakingPracticeTemplate from '@/components/activities/SpeakingPracticeTemplate';
import GroupedQuestionsTemplate from '@/components/activities/GroupedQuestionsTemplate';
import {
  ChevronLeft,
  ChevronRight,
  Send,
  CheckCircle,
  Circle,
  Clock,
  Loader2,
  BookOpen
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Activity type from API
interface Activity {
  id: number;
  content_id: number;
  order: number;
  type: string;
  title: string;
  content: string;
  target_text: string;
  duration: number;
  points: number;
  status: string;
  score: number | null;
  audio_url?: string | null;
  completed_at: string | null;
  // For activities with multiple items (questions)
  items?: Array<{
    text?: string;
    translation?: string;
    audio_url?: string;
    [key: string]: any;
  }>;
  item_count?: number;
  recordings?: string[];
  answers?: string[];
  // Additional fields for different activity types
  blanks?: string[];
  prompts?: string[];
  example_audio_url?: string;
  // AI evaluation results
  ai_scores?: {
    accuracy_score?: number;
    fluency_score?: number;
    completeness_score?: number;
    pronunciation_score?: number;
    word_details?: Array<{
      word: string;
      accuracy_score: number;
      error_type: string;
    }>;
  };
}

interface ActivityResponse {
  assignment_id: number;
  title: string;
  total_activities: number;
  activities: Activity[];
}

interface Answer {
  progressId: number;
  audioBlob?: Blob;
  audioUrl?: string;
  textAnswer?: string;
  userAnswers?: string[]; // For listening cloze
  recordings?: string[]; // For grouped questions
  answers?: string[]; // For grouped questions answers
  startTime: Date;
  endTime?: Date;
  status: 'not_started' | 'in_progress' | 'completed';
}

export default function StudentActivityPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const navigate = useNavigate();
  const { token } = useStudentAuthStore();

  // State management
  const [activities, setActivities] = useState<Activity[]>([]);
  const [assignmentTitle, setAssignmentTitle] = useState('');
  const [currentActivityIndex, setCurrentActivityIndex] = useState(0);
  const [currentSubQuestionIndex, setCurrentSubQuestionIndex] = useState(0); // For activities with multiple items
  const [answers, setAnswers] = useState<Map<number, Answer>>(new Map());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const recordingInterval = useRef<NodeJS.Timeout | null>(null);

  // Load activities from API
  useEffect(() => {
    if (assignmentId && token) {
      loadActivities();
    }
  }, [assignmentId, token]);

  const loadActivities = async () => {
    try {
      setLoading(true);
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${apiUrl}/api/students/assignments/${assignmentId}/activities`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to load activities: ${response.status}`);
      }

      const data: ActivityResponse = await response.json();
      setActivities(data.activities);
      setAssignmentTitle(data.title);

      // Initialize answers for all activities
      const initialAnswers = new Map<number, Answer>();
      data.activities.forEach(activity => {
        initialAnswers.set(activity.id, {
          progressId: activity.id,
          status: activity.status === 'NOT_STARTED' ? 'not_started' :
                  activity.status === 'IN_PROGRESS' ? 'in_progress' : 'completed',
          startTime: new Date(),
          audioUrl: activity.audio_url || undefined,
          userAnswers: [] // For listening activities
        });
      });
      setAnswers(initialAnswers);
    } catch (error) {
      console.error('Failed to load activities:', error);
      toast.error('無法載入題目，請稍後再試');
      navigate(`/student/assignment/${assignmentId}`);
    } finally {
      setLoading(false);
    }
  };

  // Recording controls
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        const currentActivity = activities[currentActivityIndex];

        // Create local audio URL for playback
        const localAudioUrl = URL.createObjectURL(audioBlob);

        // Update local state immediately for playback
        setAnswers(prev => {
          const newAnswers = new Map(prev);
          const answer = newAnswers.get(currentActivity.id) || {
            progressId: currentActivity.id,
            status: 'not_started',
            startTime: new Date(),
            recordings: [],
            answers: []
          };

          // For grouped questions, store recordings per sub-question
          if (currentActivity.items && currentActivity.items.length > 0) {
            if (!answer.recordings) answer.recordings = [];
            answer.recordings[currentSubQuestionIndex] = localAudioUrl;
          } else {
            // For single questions, store directly
            answer.audioBlob = audioBlob;
            answer.audioUrl = localAudioUrl;
          }

          answer.status = 'in_progress';  // Keep as in_progress until uploaded
          answer.endTime = new Date();

          newAnswers.set(currentActivity.id, answer);
          return newAnswers;
        });

        // Update activity's recordings array for display
        if (currentActivity.items && currentActivity.items.length > 0) {
          currentActivity.recordings = currentActivity.recordings || [];
          currentActivity.recordings[currentSubQuestionIndex] = localAudioUrl;
        }

        // Upload to GCS
        const skipUpload = false; // 啟用 GCS 上傳
        if (!skipUpload) {
        try {
          const formData = new FormData();
          formData.append('assignment_id', assignmentId || '');
          formData.append('content_item_index', currentSubQuestionIndex.toString());
          formData.append('audio_file', audioBlob, 'recording.webm');

          const apiUrl = import.meta.env.VITE_API_URL || '';
          console.log('Uploading recording to:', `${apiUrl}/api/students/upload-recording`);

          const uploadResponse = await fetch(`${apiUrl}/api/students/upload-recording`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
            },
            body: formData
          });

          if (uploadResponse.ok) {
            const result = await uploadResponse.json();
            const { audio_url, storage_type, message } = result;
            console.log('Recording uploaded successfully:', {
              url: audio_url,
              storage: storage_type,
              message: message
            });

            // 根據儲存類型顯示不同訊息
            if (storage_type === 'local') {
              console.warn('Using local storage (GCS not available)');
              toast.info('錄音已儲存在本地伺服器');
            } else {
              toast.success('錄音已上傳到雲端');
            }

            // Update with the URL (whether local or GCS)
            setAnswers(prev => {
              const newAnswers = new Map(prev);
              const answer = newAnswers.get(currentActivity.id);
              if (answer) {
                if (currentActivity.items && currentActivity.items.length > 0) {
                  if (!answer.recordings) answer.recordings = [];
                  answer.recordings[currentSubQuestionIndex] = audio_url;
                } else {
                  answer.audioUrl = audio_url;
                }
                answer.status = 'completed';
              }
              newAnswers.set(currentActivity.id, answer!);
              return newAnswers;
            });

            // Save to server with the URL
            await autoSave(audio_url);
          } else {
            const errorText = await uploadResponse.text();
            console.error('Upload failed with status:', uploadResponse.status, errorText);
            throw new Error(`Upload failed: ${uploadResponse.status}`);
          }
        } catch (error) {
          console.error('Failed to upload recording:', error);

          // 如果是網絡錯誤，先保存在本地
          if (error instanceof TypeError && error.message === 'Failed to fetch') {
            console.log('Network error - saving locally for now');
            toast.warning('網絡問題，錄音已暫存本地');

            // 仍然保存本地 URL 讓用戶可以播放
            setAnswers(prev => {
              const newAnswers = new Map(prev);
              const answer = newAnswers.get(currentActivity.id);
              if (answer) {
                answer.status = 'completed';
              }
              newAnswers.set(currentActivity.id, answer!);
              return newAnswers;
            });
          } else {
            toast.error('錄音上傳失敗，請稍後再試');
          }
        }
        } else {
          // 暫時跳過上傳，只使用本地儲存
          console.log('Skipping GCS upload - using local storage');
          setAnswers(prev => {
            const newAnswers = new Map(prev);
            const answer = newAnswers.get(currentActivity.id);
            if (answer) {
              answer.status = 'completed';
            }
            newAnswers.set(currentActivity.id, answer!);
            return newAnswers;
          });

          // 仍然保存到 server（但使用本地 URL）
          await autoSave(localAudioUrl);
        }

        // Clean up
        stream.getTracks().forEach(track => track.stop());
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
    const currentActivity = activities[currentActivityIndex];
    setAnswers(prev => {
      const newAnswers = new Map(prev);
      const answer = newAnswers.get(currentActivity.id);
      if (answer) {
        answer.audioBlob = undefined;
        answer.audioUrl = undefined;
        answer.status = 'in_progress';
      }
      newAnswers.set(currentActivity.id, answer!);
      return newAnswers;
    });
    startRecording();
  };

  // Format time display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Navigation - handles both activities and sub-questions
  const handleNextActivity = async () => {
    await autoSave();
    const currentActivity = activities[currentActivityIndex];

    // If current activity has sub-questions and we're not at the last one
    if (currentActivity.items && currentActivity.items.length > 0) {
      if (currentSubQuestionIndex < currentActivity.items.length - 1) {
        // Move to next sub-question
        setCurrentSubQuestionIndex(currentSubQuestionIndex + 1);
        setRecordingTime(0);
        return;
      }
    }

    // Move to next activity if available
    if (currentActivityIndex < activities.length - 1) {
      setCurrentActivityIndex(currentActivityIndex + 1);
      setCurrentSubQuestionIndex(0);
      setRecordingTime(0);
    }
  };

  const handlePreviousActivity = async () => {
    await autoSave();
    const currentActivity = activities[currentActivityIndex];

    // If current activity has sub-questions and we're not at the first one
    if (currentActivity.items && currentActivity.items.length > 0) {
      if (currentSubQuestionIndex > 0) {
        // Move to previous sub-question
        setCurrentSubQuestionIndex(currentSubQuestionIndex - 1);
        setRecordingTime(0);
        return;
      }
    }

    // Move to previous activity if available
    if (currentActivityIndex > 0) {
      const prevActivityIndex = currentActivityIndex - 1;
      const prevActivity = activities[prevActivityIndex];
      setCurrentActivityIndex(prevActivityIndex);

      // If previous activity has sub-questions, go to the last one
      if (prevActivity.items && prevActivity.items.length > 0) {
        setCurrentSubQuestionIndex(prevActivity.items.length - 1);
      } else {
        setCurrentSubQuestionIndex(0);
      }
      setRecordingTime(0);
    }
  };

  const handleActivitySelect = async (index: number) => {
    await autoSave();
    setCurrentActivityIndex(index);
    setCurrentSubQuestionIndex(0); // Reset sub-question index
    setRecordingTime(0);
  };

  // Auto-save functionality
  const autoSave = async (audioUrl?: string) => {
    if (!token || !assignmentId) return;

    try {
      setSaving(true);
      const currentActivity = activities[currentActivityIndex];
      const answer = answers.get(currentActivity.id);

      if (!answer || !currentActivity.id) return;

      const apiUrl = import.meta.env.VITE_API_URL || '';
      await fetch(`${apiUrl}/api/students/assignments/${assignmentId}/activities/${currentActivity.id}/save`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          audio_url: audioUrl || answer.audioUrl,
          text_answer: answer.textAnswer,
          user_answers: answer.userAnswers, // For listening activities
          item_index: currentActivity.items ? currentSubQuestionIndex : undefined // Include sub-question index for grouped items
        })
      });

      console.log('Auto-saved activity progress');
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
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${apiUrl}/api/students/assignments/${assignmentId}/submit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to submit assignment');
      }

      toast.success('作業提交成功！');
      navigate(`/student/assignment/${assignmentId}`);
    } catch (error) {
      console.error('Failed to submit:', error);
      toast.error('提交失敗，請稍後再試');
    } finally {
      setSubmitting(false);
    }
  };

  // Get status display
  const getStatusIcon = (activity: Activity, answer?: Answer) => {
    const status = answer?.status || 'not_started';

    if (status === 'completed' || activity.status === 'SUBMITTED') {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    } else if (status === 'in_progress' || activity.status === 'IN_PROGRESS') {
      return <Clock className="h-4 w-4 text-yellow-500" />;
    } else {
      return <Circle className="h-4 w-4" />;
    }
  };

  // Get activity type badge
  const getActivityTypeBadge = (type: string) => {
    switch (type) {
      case 'reading_assessment':
        return <Badge variant="outline">朗讀錄音</Badge>;
      case 'listening_cloze':
        return <Badge variant="outline">聽力填空</Badge>;
      case 'speaking_practice':
        return <Badge variant="outline">口說練習</Badge>;
      case 'speaking_scenario':
        return <Badge variant="outline">情境對話</Badge>;
      case 'sentence_making':
        return <Badge variant="outline">造句練習</Badge>;
      case 'speaking_quiz':
        return <Badge variant="outline">口說測驗</Badge>;
      default:
        return <Badge variant="outline">學習活動</Badge>;
    }
  };

  // Render activity content based on type
  const renderActivityContent = (activity: Activity) => {
    const answer = answers.get(activity.id);

    // Check if activity has multiple items (grouped questions)
    if (activity.items && activity.items.length > 0) {
      return (
        <GroupedQuestionsTemplate
          items={activity.items}
          recordings={answer?.recordings || activity.recordings || []}
          answers={activity.answers}
          currentQuestionIndex={currentSubQuestionIndex}
          isRecording={isRecording}
          recordingTime={recordingTime}
          onStartRecording={startRecording}
          onStopRecording={stopRecording}
          formatTime={formatTime}
          progressId={activity.id}
          initialAssessmentResults={activity.ai_scores}
        />
      );
    }

    switch (activity.type) {
      case 'reading_assessment':
        return (
          <ReadingAssessmentTemplate
            content={activity.content}
            targetText={activity.target_text}
            audioUrl={answer?.audioUrl}
            isRecording={isRecording}
            recordingTime={recordingTime}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onReRecord={reRecord}
            formatTime={formatTime}
            exampleAudioUrl={activity.example_audio_url}
            progressId={activity.id}
          />
        );

      case 'listening_cloze':
        return (
          <ListeningClozeTemplate
            content={activity.content}
            audioUrl={activity.audio_url || ''}
            blanks={activity.blanks || []}
            userAnswers={answer?.userAnswers || []}
            onAnswerChange={(index, value) => {
              setAnswers(prev => {
                const newAnswers = new Map(prev);
                const ans = newAnswers.get(activity.id) || {
                  progressId: activity.id,
                  status: 'not_started',
                  startTime: new Date(),
                  userAnswers: []
                };
                if (!ans.userAnswers) ans.userAnswers = [];
                ans.userAnswers[index] = value;
                ans.status = 'in_progress';
                newAnswers.set(activity.id, ans);
                return newAnswers;
              });
            }}
            showAnswers={activity.status === 'SUBMITTED'}
          />
        );

      case 'speaking_practice':
      case 'speaking_scenario':
        return (
          <SpeakingPracticeTemplate
            topic={activity.title}
            prompts={activity.prompts || [activity.content]}
            suggestedDuration={activity.duration || 60}
            audioUrl={answer?.audioUrl}
            isRecording={isRecording}
            recordingTime={recordingTime}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onReRecord={reRecord}
            formatTime={formatTime}
          />
        );

      default:
        // Default to reading assessment template
        return (
          <ReadingAssessmentTemplate
            content={activity.content}
            targetText={activity.target_text || activity.content}
            audioUrl={answer?.audioUrl}
            isRecording={isRecording}
            recordingTime={recordingTime}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onReRecord={reRecord}
            formatTime={formatTime}
            progressId={activity.id}
          />
        );
    }
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

  if (activities.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">此作業尚無題目</p>
          <Button onClick={() => navigate(`/student/assignment/${assignmentId}`)}>
            返回作業詳情
          </Button>
        </div>
      </div>
    );
  }

  const currentActivity = activities[currentActivityIndex];
  const progress = ((currentActivityIndex + 1) / activities.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header with progress */}
      <div className="sticky top-0 bg-white border-b z-10">
        <div className="max-w-6xl mx-auto px-4 py-2">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate(`/student/assignment/${assignmentId}`)}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                返回作業
              </Button>
              <div className="h-6 w-px bg-gray-300" />
              <h1 className="text-base font-semibold">{assignmentTitle}</h1>
            </div>

            <div className="flex items-center gap-3">
              {saving && (
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  自動儲存中...
                </div>
              )}
              <Button
                onClick={handleSubmit}
                disabled={submitting}
                size="sm"
                variant="default"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    提交中...
                  </>
                ) : (
                  <>
                    <Send className="h-3 w-3 mr-1" />
                    提交作業
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Activity navigation - Grouped by content with sub-questions (horizontal layout) */}
          <div className="flex gap-4 overflow-x-auto pb-2">
            {activities.map((activity, activityIndex) => {
              const answer = answers.get(activity.id);
              const isActiveActivity = activityIndex === currentActivityIndex;

              // If activity has items, show them as sub-questions
              if (activity.items && activity.items.length > 0) {
                return (
                  <div key={activity.id} className="flex items-center gap-2 flex-shrink-0">
                    {/* Content title */}
                    <div className="flex items-center gap-1">
                      <span className="text-xs font-medium text-gray-600 whitespace-nowrap">{activity.title}</span>
                      <Badge variant="outline" className="text-xs px-1 py-0 h-5">{activity.items.length}題</Badge>
                    </div>

                    {/* Question buttons */}
                    <div className="flex gap-1">
                      {activity.items.map((_, itemIndex) => {
                        const isActiveItem = isActiveActivity && currentSubQuestionIndex === itemIndex;
                        const isCompleted = activity.recordings?.[itemIndex] || activity.answers?.[itemIndex];

                        return (
                          <button
                            key={itemIndex}
                            onClick={() => {
                              if (activityIndex !== currentActivityIndex) {
                                handleActivitySelect(activityIndex);
                              }
                              setCurrentSubQuestionIndex(itemIndex);
                            }}
                            className={cn(
                              "relative w-8 h-8 rounded-md border transition-all",
                              "flex items-center justify-center text-xs font-medium",
                              isActiveItem
                                ? "bg-blue-600 text-white border-blue-600"
                                : isCompleted
                                ? "bg-green-50 text-green-700 border-green-300"
                                : "bg-white text-gray-600 border-gray-300 hover:border-blue-400"
                            )}
                          >
                            {itemIndex + 1}
                            {isCompleted && !isActiveItem && (
                              <CheckCircle className="absolute -top-1 -right-1 w-3 h-3 text-green-600 bg-white rounded-full" />
                            )}
                          </button>
                        );
                      })}
                    </div>

                    {/* Separator between content groups */}
                    {activityIndex < activities.length - 1 && (
                      <div className="w-px h-8 bg-gray-300 ml-2" />
                    )}
                  </div>
                );
              }

              // For activities without items, show single button
              return (
                <Button
                  key={activity.id}
                  variant={isActiveActivity ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleActivitySelect(activityIndex)}
                  className="flex-shrink-0 h-8"
                >
                  <div className="flex items-center gap-2">
                    {getStatusIcon(activity, answer)}
                    <span className="text-xs">{activity.title}</span>
                  </div>
                </Button>
              );
            })}
          </div>

          {/* Overall progress */}
          <Progress value={progress} className="h-1 mt-1" />
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-4xl mx-auto p-4 mt-6">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-2xl mb-2">
                  第 {currentActivity.order} 題：{currentActivity.title}
                </CardTitle>
                {getActivityTypeBadge(currentActivity.type)}
              </div>
              <Badge className="bg-blue-100 text-blue-800">
                {currentActivity.points} 分
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Render activity-specific content */}
            {renderActivityContent(currentActivity)}

            {/* Navigation buttons */}
            <div className="flex items-center justify-between pt-6">
              <Button
                variant="outline"
                onClick={handlePreviousActivity}
                disabled={currentActivityIndex === 0 && currentSubQuestionIndex === 0}
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                上一題
              </Button>

              <span className="text-sm text-gray-600">
                {(() => {
                  // Calculate current question number across all activities
                  let currentQuestion = 0;
                  let totalQuestions = 0;

                  for (let i = 0; i < activities.length; i++) {
                    const activity = activities[i];
                    const questionCount = activity.items?.length || 1;

                    if (i < currentActivityIndex) {
                      currentQuestion += questionCount;
                    } else if (i === currentActivityIndex) {
                      currentQuestion += (activity.items ? currentSubQuestionIndex + 1 : 1);
                    }

                    totalQuestions += questionCount;
                  }

                  return `${currentQuestion} / ${totalQuestions}`;
                })()}
              </span>

              {(() => {
                const currentActivity = activities[currentActivityIndex];
                const isLastActivity = currentActivityIndex === activities.length - 1;
                const isLastSubQuestion = currentActivity.items
                  ? currentSubQuestionIndex === currentActivity.items.length - 1
                  : true;
                const isLastQuestion = isLastActivity && isLastSubQuestion;

                if (isLastQuestion) {
                  return (
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
                  );
                }

                return (
                  <Button
                    onClick={handleNextActivity}
                  >
                    下一題
                    <ChevronRight className="h-4 w-4 ml-2" />
                  </Button>
                );
              })()}
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
