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
    [key: string]: unknown;
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
  status?: string;  // 加入作業狀態
  total_activities: number;
  activities: Activity[];
}

interface Answer {
  progressId: number;
  progressIds?: number[]; // For grouped questions with multiple progress records
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
  const [assignmentStatus, setAssignmentStatus] = useState<string>('');  // 作業狀態
  const [isReadOnly, setIsReadOnly] = useState(false);  // 唯讀模式
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
      console.log('Loaded activities from API:', data.activities);

      // Log AI assessment data from items
      data.activities.forEach((activity, idx) => {
        if (activity.items && activity.items.length > 0) {
          console.log(`Activity ${idx} items with AI assessment:`,
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            activity.items.map((item: any) => ({
              id: item.id,
              text: item.text?.substring(0, 20),
              has_ai: !!item.ai_assessment,
              scores: item.ai_assessment ? {
                accuracy: item.ai_assessment.accuracy_score,
                fluency: item.ai_assessment.fluency_score,
                pronunciation: item.ai_assessment.pronunciation_score
              } : null
            }))
          );
        }
      });

      setActivities(data.activities);
      setAssignmentTitle(data.title);

      // 設置作業狀態和唯讀模式
      if (data.status) {
        setAssignmentStatus(data.status);
        // 如果作業已提交或已評分，設為唯讀模式
        const readOnlyStatuses = ['SUBMITTED', 'GRADED'];
        setIsReadOnly(readOnlyStatuses.includes(data.status));

        if (readOnlyStatuses.includes(data.status)) {
          console.log('🔒 Assignment is in read-only mode:', data.status);
        }
      }

      // Initialize answers for all activities
      const initialAnswers = new Map<number, Answer>();
      data.activities.forEach(activity => {
        initialAnswers.set(activity.id, {
          progressId: activity.id,
          status: activity.status === 'NOT_STARTED' ? 'not_started' :
                  activity.status === 'IN_PROGRESS' ? 'in_progress' : 'completed',
          startTime: new Date(),
          audioUrl: activity.audio_url || undefined,
          recordings: activity.recordings || [], // Load existing recordings
          answers: activity.answers || [], // Load existing answers
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
    // 唯讀模式下不允許錄音
    if (isReadOnly) {
      toast.warning('檢視模式下無法錄音');
      return;
    }

    try {
      // Clear old recordings and AI scores when starting new recording
      const currentActivity = activities[currentActivityIndex];

      // Clear previous recording and AI scores for grouped questions
      if (currentActivity.items && currentActivity.items.length > 0) {
        setActivities(prevActivities => {
          const newActivities = [...prevActivities];
          const activityIndex = newActivities.findIndex(a => a.id === currentActivity.id);
          if (activityIndex !== -1) {
            const recordings = [...(newActivities[activityIndex].recordings || [])];
            // Ensure array is long enough
            while (recordings.length <= currentSubQuestionIndex) {
              recordings.push('');
            }
            recordings[currentSubQuestionIndex] = ''; // Clear current recording
            newActivities[activityIndex] = {
              ...newActivities[activityIndex],
              recordings: recordings,
              ai_scores: undefined // Clear AI scores
            };
          }
          return newActivities;
        });

        // Also clear from answers
        setAnswers(prev => {
          const newAnswers = new Map(prev);
          const answer = newAnswers.get(currentActivity.id);
          if (answer) {
            if (!answer.recordings) answer.recordings = [];
            // Ensure array is long enough
            while (answer.recordings.length <= currentSubQuestionIndex) {
              answer.recordings.push('');
            }
            answer.recordings[currentSubQuestionIndex] = '';
            newAnswers.set(currentActivity.id, answer);
          }
          return newAnswers;
        });
      }

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
            // Ensure array is long enough
            while (answer.recordings.length <= currentSubQuestionIndex) {
              answer.recordings.push('');
            }
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
          // Update activities state to trigger re-render
          setActivities(prevActivities => {
            const newActivities = [...prevActivities];
            const activityIndex = newActivities.findIndex(a => a.id === currentActivity.id);
            if (activityIndex !== -1) {
              const recordings = [...(newActivities[activityIndex].recordings || [])];
              // Ensure array is long enough
              while (recordings.length <= currentSubQuestionIndex) {
                recordings.push('');
              }
              recordings[currentSubQuestionIndex] = localAudioUrl;
              newActivities[activityIndex] = {
                ...newActivities[activityIndex],
                recordings: recordings
              };
            }
            return newActivities;
          });
        }

        // Upload to GCS
        const skipUpload = false; // 啟用 GCS 上傳
        if (!skipUpload) {
        try {
          // 獲取當前 item 的 ID
          const currentItem = currentActivity.items?.[currentSubQuestionIndex];
          if (!currentItem?.id) {
            throw new Error('Content item ID not found');
          }

          const formData = new FormData();
          formData.append('assignment_id', assignmentId || '');
          formData.append('content_item_id', currentItem.id.toString());  // 使用 ContentItem 的 ID！
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
            const { audio_url, message, progress_id } = result;
            console.log('Recording uploaded successfully:', {
              url: audio_url,
              message: message,
              progress_id: progress_id
            });

            // 錄音成功上傳到雲端
            toast.success('錄音已上傳到雲端');

            // Update with the GCS URL and progress_id
            setAnswers(prev => {
              const newAnswers = new Map(prev);
              const answer = newAnswers.get(currentActivity.id);
              if (answer) {
                if (currentActivity.items && currentActivity.items.length > 0) {
                  if (!answer.recordings) answer.recordings = [];
                  if (!answer.progressIds) answer.progressIds = [];

                  // Ensure arrays are long enough
                  while (answer.recordings.length <= currentSubQuestionIndex) {
                    answer.recordings.push('');
                  }
                  while (answer.progressIds.length <= currentSubQuestionIndex) {
                    answer.progressIds.push(0);
                  }

                  answer.recordings[currentSubQuestionIndex] = audio_url;
                  // 🔥 關鍵修復：存儲 progress_id 到對應的子問題索引
                  if (progress_id) {
                    answer.progressIds[currentSubQuestionIndex] = progress_id;
                  }
                } else {
                  answer.audioUrl = audio_url;
                  if (progress_id) {
                    answer.progressId = progress_id;
                  }
                }
                answer.status = 'completed';
              }
              newAnswers.set(currentActivity.id, answer!);
              return newAnswers;
            });

            // Also update activities state with GCS URL
            if (currentActivity.items && currentActivity.items.length > 0) {
              setActivities(prevActivities => {
                const newActivities = [...prevActivities];
                const activityIndex = newActivities.findIndex(a => a.id === currentActivity.id);
                if (activityIndex !== -1) {
                  const recordings = [...(newActivities[activityIndex].recordings || [])];
                  // Ensure array is long enough
                  while (recordings.length <= currentSubQuestionIndex) {
                    recordings.push('');
                  }
                  recordings[currentSubQuestionIndex] = audio_url;
                  newActivities[activityIndex] = {
                    ...newActivities[activityIndex],
                    recordings: recordings
                  };
                }
                return newActivities;
              });
            }

            // Save to server with the URL - autoSave will handle the updated recordings array
            await autoSave();
          } else {
            const errorText = await uploadResponse.text();
            console.error('Upload failed with status:', uploadResponse.status, errorText);
            throw new Error(`Upload failed: ${uploadResponse.status}`);
          }
        } catch (error) {
          console.error('Failed to upload recording:', error);

          // 處理錯誤
          if (error instanceof TypeError && error.message === 'Failed to fetch') {
            console.error('Network error - cannot upload recording');
            toast.error('網絡連接失敗，無法上傳錄音');
          } else {
            toast.error('錄音上傳失敗，請稍後再試');
          }
        }
        } // End of if (!skipUpload)
      }; // End of recorder.onstop

      // Start recording
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

  const handleActivitySelect = async (index: number, subQuestionIndex: number = 0) => {
    await autoSave();
    setCurrentActivityIndex(index);
    setCurrentSubQuestionIndex(subQuestionIndex); // Set to specific sub-question
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

      // Prepare save data based on activity type
      const saveData: Record<string, unknown> = {
        text_answer: answer.textAnswer,
        user_answers: answer.userAnswers, // For listening activities
      };

      // For activities with multiple items (grouped questions)
      if (currentActivity.items && currentActivity.items.length > 0) {
        // Save recordings array and answers array
        saveData.recordings = answer.recordings || [];
        saveData.answers = answer.answers || [];
        saveData.item_index = currentSubQuestionIndex;
      } else {
        // For single activities, save single audio_url
        saveData.audio_url = audioUrl || answer.audioUrl;
      }

      await fetch(`${apiUrl}/api/students/assignments/${assignmentId}/activities/${currentActivity.id}/save`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(saveData)
      });

      console.log('Auto-saved activity progress');
    } catch (error) {
      console.error('Failed to auto-save:', error);
    } finally {
      setSaving(false);
    }
  };

  // Final submission
  const handleSubmit = async (e?: React.MouseEvent) => {
    console.log('🔥 [DEBUG] handleSubmit called in StudentActivityPage!');
    console.log('🔥 [DEBUG] Event:', e);

    // 防止預設行為和事件冒泡
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    const unanswered = Array.from(answers.values()).filter(
      a => a.status === 'not_started'
    );

    if (unanswered.length > 0) {
      const confirm = window.confirm(
        `還有 ${unanswered.length} 題未作答，確定要提交嗎？`
      );
      if (!confirm) {
        console.log('🔥 [DEBUG] User cancelled submission');
        return;
      }
    }

    try {
      console.log('🔥 [DEBUG] Starting submission...');
      setSubmitting(true);
      const apiUrl = import.meta.env.VITE_API_URL || '';
      console.log('🔥 [DEBUG] Calling API:', `${apiUrl}/api/students/assignments/${assignmentId}/submit`);

      const response = await fetch(`${apiUrl}/api/students/assignments/${assignmentId}/submit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('🔥 [DEBUG] API Response status:', response.status);

      if (!response.ok) {
        throw new Error('Failed to submit assignment');
      }

      toast.success('作業提交成功！');
      console.log('🔥 [DEBUG] Submission successful, redirecting to detail page...');

      // 使用 window.location.href 確保完全重新載入並跳轉到正確的 detail 頁面
      setTimeout(() => {
        const detailUrl = `/student/assignment/${assignmentId}/detail`;
        console.log('🔥 [DEBUG] Redirecting to:', detailUrl);
        window.location.href = detailUrl;
      }, 500);
    } catch (error) {
      console.error('🔥 [DEBUG] Failed to submit:', error);
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
      // Extract AI assessments from items and format for GroupedQuestionsTemplate
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const aiAssessments: Record<number, any> = {};
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      activity.items.forEach((item: any, index: number) => {
        if (item.ai_assessment) {
          aiAssessments[index] = {
            accuracy_score: item.ai_assessment.accuracy_score,
            fluency_score: item.ai_assessment.fluency_score,
            pronunciation_score: item.ai_assessment.pronunciation_score,
            completeness_score: item.ai_assessment.completeness_score || 0,
            word_details: []
          };
        }
      });

      // Use the extracted AI assessments if available, otherwise fallback to activity.ai_scores
      const assessmentResults = Object.keys(aiAssessments).length > 0
        ? { items: aiAssessments }
        : activity.ai_scores;

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
          progressIds={answer?.progressIds} // 🔥 傳遞 progress_id 數組
          initialAssessmentResults={assessmentResults}
          readOnly={isReadOnly}  // 傳遞唯讀狀態
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
            readOnly={isReadOnly}
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
            readOnly={isReadOnly}
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
            readOnly={isReadOnly}
          />
        );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <div className="text-center">
          <div className="relative">
            {/* Outer ring */}
            <div className="absolute inset-0 animate-ping">
              <div className="h-16 w-16 rounded-full border-4 border-blue-200 opacity-75"></div>
            </div>
            {/* Inner spinning circle */}
            <Loader2 className="h-16 w-16 animate-spin text-blue-600 mx-auto relative" />
          </div>
          <p className="mt-6 text-lg font-medium text-gray-700">載入作業中...</p>
          <p className="mt-2 text-sm text-gray-500">請稍候，正在準備您的學習內容</p>
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
          <Button onClick={() => navigate(`/student/assignment/${assignmentId}/detail`)}>
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
      {/* 唯讀模式提示 */}
      {isReadOnly && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-2">
          <div className="max-w-6xl mx-auto flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-blue-600" />
            <span className="text-blue-700">
              {assignmentStatus === 'SUBMITTED' ? '作業已提交，目前為檢視模式' :
               assignmentStatus === 'GRADED' ? '作業已評分，目前為檢視模式' : '檢視模式'}
            </span>
          </div>
        </div>
      )}

      {/* Header with progress */}
      <div className="sticky top-0 bg-white border-b z-10">
        <div className="max-w-6xl mx-auto px-4 py-2">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate(`/student/assignment/${assignmentId}/detail`)}
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
              {!isReadOnly && (
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
              )}
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
                                handleActivitySelect(activityIndex, itemIndex);
                              } else {
                                setCurrentSubQuestionIndex(itemIndex);
                              }
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
                      disabled={submitting || isReadOnly}
                      style={{ display: isReadOnly ? 'none' : 'inline-flex' }}
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
