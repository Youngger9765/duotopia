import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';
import {
  ArrowLeft,
  ArrowRight,
  Save,
  Play,
  Pause,
  CheckCircle,
  Clock,
  User
} from 'lucide-react';

interface StudentSubmission {
  student_number: number;
  student_name: string;
  student_email: string;
  status: string;
  submitted_at?: string;
  content_type: string;
  submissions: Array<{
    question_text: string;
    question_translation?: string;
    question_audio_url?: string;  // 題目參考音檔
    student_audio_url?: string;  // 學生錄音檔案
    student_answer?: string;
    transcript?: string;
    duration?: number;
    feedback?: string;
    passed?: boolean;
    ai_scores?: {
      accuracy_score: number;
      fluency_score: number;
      completeness_score: number;
      pronunciation_score: number;
      word_details: Array<{
        word: string;
        accuracy_score: number;
        error_type?: string | null;
      }>;
    };
  }>;
  current_score?: number;
  current_feedback?: string;
  item_results?: Array<{
    item_index: number;
    feedback: string;
    passed: boolean;
  }>;
}

export default function StudentGradingPage() {
  const { classroomId, assignmentId, studentId } = useParams();
  const navigate = useNavigate();

  console.log('=== StudentGradingPage Mounted ===');
  console.log('URL params:', { classroomId, assignmentId, studentId });
  console.log('Type of params:', {
    classroomId: typeof classroomId,
    assignmentId: typeof assignmentId,
    studentId: typeof studentId
  });

  const [submission, setSubmission] = useState<StudentSubmission | null>(null);
  const [loading, setLoading] = useState(true);
  const [score, setScore] = useState(0);
  const [overallComment, setOverallComment] = useState(''); // 可編輯的總評
  const [itemResults, setItemResults] = useState<Array<{
    item_index: number;
    feedback: string;
    passed: boolean;
  }>>([]); // 每題的評語和通過狀態
  const [submitting, setSubmitting] = useState(false);
  const [currentAudioIndex, setCurrentAudioIndex] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0); // 當前題目索引

  const audioRef = useState<HTMLAudioElement>(new Audio())[0];

  useEffect(() => {
    console.log('StudentGradingPage params:', { classroomId, assignmentId, studentId });
    if (assignmentId && studentId) {
      loadSubmission();
    } else {
      console.error('Missing params:', { assignmentId, studentId });
      toast.error('參數錯誤：找不到作業或學生 ID');
      setLoading(false);
    }
  }, [assignmentId, studentId]);

  const loadSubmission = async () => {
    try {
      setLoading(true);
      const url = `/api/teachers/teachers/assignments/${assignmentId}/submissions/${studentId}`;
      console.log('Fetching submission from:', url);

      const response = await apiClient.get<StudentSubmission>(url);
      console.log('API Response:', response);

      // apiClient 直接返回資料，不是 { data: ... } 格式
      if (!response) {
        console.error('No response from API');
        toast.error('無法載入學生作業：無回應');
        return;
      }

      setSubmission(response as StudentSubmission);

      // 如果已經有分數，預填
      if (response.current_score !== undefined && response.current_score !== null) {
        setScore(response.current_score);
        setOverallComment(response.current_feedback || '');
      } else {
        setScore(80); // 預設分數
        setOverallComment(''); // 清空回饋
      }

      // 初始化每題的評語結果
      if (response.item_results) {
        setItemResults(response.item_results);
      } else {
        // 初始化空的評語結果
        const initialResults = response.submissions?.map((_, index: number) => ({
          item_index: index,
          feedback: '',
          passed: false
        }));
        setItemResults(initialResults);
      }
    } catch (error) {
      console.error('Failed to load submission:', error);
      toast.error('無法載入學生作業');
    } finally {
      setLoading(false);
    }
  };

  const playAudio = (audioUrl: string, index: number) => {
    if (currentAudioIndex === index && isPlaying) {
      audioRef.pause();
      setIsPlaying(false);
    } else {
      // 確保音頻 URL 是完整的
      const fullUrl = audioUrl.startsWith('http')
        ? audioUrl
        : `${import.meta.env.VITE_API_URL}${audioUrl}`;

      audioRef.src = fullUrl;
      audioRef.play();
      setCurrentAudioIndex(index);
      setIsPlaying(true);

      audioRef.onended = () => {
        setIsPlaying(false);
        setCurrentAudioIndex(null);
      };
    }
  };

  const addQuickFeedback = (text: string) => {
    // 添加快速回饋到當前題目
    setItemResults(prev => {
      const newResults = [...prev];
      if (newResults[currentQuestionIndex]) {
        const currentFeedback = newResults[currentQuestionIndex].feedback;
        newResults[currentQuestionIndex].feedback = currentFeedback
          ? `${currentFeedback}\n${text}`
          : text;
      }
      return newResults;
    });
  };

  const toggleItemPassed = (index: number) => {
    setItemResults(prev => {
      const newResults = [...prev];
      if (newResults[index]) {
        newResults[index].passed = !newResults[index].passed;
      }
      return newResults;
    });
  };

  const updateItemFeedback = (index: number, feedback: string) => {
    setItemResults(prev => {
      const newResults = [...prev];
      if (newResults[index]) {
        newResults[index].feedback = feedback;
      }
      return newResults;
    });
  };

  // 生成詳實記錄（唯讀）
  const generateDetailedRecord = () => {
    if (!submission) return '';

    let record = '【批改詳細記錄】\n\n';
    submission.submissions.forEach((item, index) => {
      const result = itemResults[index];
      record += `第 ${index + 1} 題：${item.question_text}\n`;
      record += `狀態：${result?.passed ? '✅ 通過' : '❌ 未通過'}\n`;
      if (result?.feedback) {
        record += `評語：${result.feedback}\n`;
      }
      record += '\n';
    });

    return record;
  };

  const handleSubmitGrade = async () => {
    if (!submission) return;

    try {
      setSubmitting(true);

      // 組合詳實記錄和總評作為完整回饋
      const detailedRecord = generateDetailedRecord();
      const fullFeedback = `${detailedRecord}\n【總評】\n${overallComment.trim()}`;

      await apiClient.post(`/api/teachers/teachers/assignments/${assignmentId}/grade`, {
        student_number: submission.student_number,
        score: score,
        feedback: fullFeedback,
        item_results: itemResults,
        update_status: true // 完成批改
      });

      toast.success('評分已儲存');

      // 返回作業詳情頁
      navigate(`/teacher/classroom/${classroomId}/assignment/${assignmentId}`);

    } catch (error) {
      console.error('Failed to submit grade:', error);
      toast.error('評分失敗，請稍後再試');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveAndNext = async () => {
    await handleSubmitGrade();
    // TODO: 導航到下一個學生
    toast.info('已儲存，請手動選擇下一位學生');
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

  if (!submission) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="p-6">
          <p className="text-gray-600">找不到學生作業</p>
          <Button
            onClick={() => navigate(`/teacher/classroom/${classroomId}/assignment/${assignmentId}`)}
            className="mt-4"
          >
            返回作業列表
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => navigate(`/teacher/classroom/${classroomId}/assignment/${assignmentId}`)}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回作業列表
          </Button>

          <div className="flex items-center gap-4">
            <Badge variant="outline" className="text-lg px-4 py-2">
              <User className="h-4 w-4 mr-2" />
              {submission.student_name}
            </Badge>
            {submission.submitted_at && (
              <Badge variant="secondary" className="text-sm">
                <Clock className="h-3 w-3 mr-1" />
                提交時間：{new Date(submission.submitted_at).toLocaleString('zh-TW')}
              </Badge>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左側：學生作答內容 */}
          <Card>
            <CardHeader>
              <CardTitle>學生作答內容</CardTitle>
            </CardHeader>
            <CardContent>
              {/* 題目導航 */}
              <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-lg">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1))}
                  disabled={currentQuestionIndex === 0}
                >
                  <ArrowLeft className="h-4 w-4 mr-1" />
                  上一題
                </Button>
                <span className="font-medium">
                  第 {currentQuestionIndex + 1} / {submission.submissions.length} 題
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentQuestionIndex(Math.min(submission.submissions.length - 1, currentQuestionIndex + 1))}
                  disabled={currentQuestionIndex === submission.submissions.length - 1}
                >
                  下一題
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </div>

              {/* 當前題目內容 */}
              {submission.submissions[currentQuestionIndex] && (
                <div className="p-4 border rounded-lg bg-white">
                  <div className="mb-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-lg">
                        第 {currentQuestionIndex + 1} 題
                      </h4>
                      {/* 通過/未通過標記 */}
                      <Button
                        variant={itemResults[currentQuestionIndex]?.passed ? "default" : "outline"}
                        size="sm"
                        onClick={() => toggleItemPassed(currentQuestionIndex)}
                        className={itemResults[currentQuestionIndex]?.passed ? "bg-green-600 hover:bg-green-700" : ""}
                      >
                        <CheckCircle className="h-4 w-4 mr-1" />
                        {itemResults[currentQuestionIndex]?.passed ? "通過" : "未通過"}
                      </Button>
                    </div>
                    <p className="text-gray-700 mt-2">{submission.submissions[currentQuestionIndex].question_text}</p>
                    {submission.submissions[currentQuestionIndex].question_translation && (
                      <p className="text-gray-500 text-sm mt-1">
                        {submission.submissions[currentQuestionIndex].question_translation}
                      </p>
                    )}
                  </div>

                  {/* 音頻播放 - 只使用 student_audio_url */}
                  {submission.submissions[currentQuestionIndex].student_audio_url && (
                    <div className="space-y-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => playAudio(
                          submission.submissions[currentQuestionIndex].student_audio_url!,
                          currentQuestionIndex
                        )}
                        className="w-full"
                      >
                        {currentAudioIndex === currentQuestionIndex && isPlaying ? (
                          <>
                            <Pause className="h-4 w-4 mr-2" />
                            暫停播放
                          </>
                        ) : (
                          <>
                            <Play className="h-4 w-4 mr-2" />
                            播放學生錄音
                          </>
                        )}
                      </Button>

                      {submission.submissions[currentQuestionIndex].duration && (
                        <p className="text-sm text-gray-500">
                          錄音長度：{submission.submissions[currentQuestionIndex].duration} 秒
                        </p>
                      )}

                      {submission.submissions[currentQuestionIndex].transcript && (
                        <div className="p-2 bg-gray-50 rounded text-sm">
                          <p className="text-gray-600">學生朗讀內容：</p>
                          <p className="mt-1">{submission.submissions[currentQuestionIndex].transcript}</p>
                        </div>
                      )}

                      {/* AI 評分結果顯示（唯讀） */}
                      {submission.submissions[currentQuestionIndex].ai_scores && (
                        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                          <h4 className="text-sm font-semibold text-blue-800 mb-2">🤖 AI 語音評估結果</h4>
                          
                          {/* 綜合分數 */}
                          <div className="grid grid-cols-2 gap-3 mb-3">
                            <div className="text-center">
                              <div className="text-lg font-bold text-blue-700">
                                {submission.submissions[currentQuestionIndex].ai_scores!.accuracy_score.toFixed(1)}
                              </div>
                              <div className="text-xs text-blue-600">準確度</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-blue-700">
                                {submission.submissions[currentQuestionIndex].ai_scores!.fluency_score.toFixed(1)}
                              </div>
                              <div className="text-xs text-blue-600">流暢度</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-blue-700">
                                {submission.submissions[currentQuestionIndex].ai_scores!.completeness_score.toFixed(1)}
                              </div>
                              <div className="text-xs text-blue-600">完整度</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-blue-700">
                                {submission.submissions[currentQuestionIndex].ai_scores!.pronunciation_score.toFixed(1)}
                              </div>
                              <div className="text-xs text-blue-600">發音分數</div>
                            </div>
                          </div>

                          {/* 單字詳細評分 */}
                          {submission.submissions[currentQuestionIndex].ai_scores!.word_details.length > 0 && (
                            <div>
                              <p className="text-sm text-blue-700 font-medium mb-2">單字分析：</p>
                              <div className="flex flex-wrap gap-1">
                                {submission.submissions[currentQuestionIndex].ai_scores!.word_details.map((word, idx) => (
                                  <span
                                    key={idx}
                                    className={`px-2 py-1 rounded text-xs font-medium ${
                                      word.accuracy_score >= 90
                                        ? 'bg-green-100 text-green-800'
                                        : word.accuracy_score >= 80
                                        ? 'bg-yellow-100 text-yellow-800'
                                        : 'bg-red-100 text-red-800'
                                    }`}
                                    title={`${word.word}: ${word.accuracy_score.toFixed(1)}分${word.error_type ? ' (' + word.error_type + ')' : ''}`}
                                  >
                                    {word.word} ({word.accuracy_score.toFixed(1)})
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          <p className="text-xs text-blue-500 mt-2">※ 此為 AI 自動評估結果，僅供參考</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* 單題評語 - 移除此部分，評語應該在右側編輯 */}
                </div>
              )}

              {/* 題目狀態總覽 */}
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium mb-2">批改進度</p>
                <div className="flex gap-1">
                  {submission.submissions.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentQuestionIndex(index)}
                      className={`w-8 h-8 rounded text-sm font-medium transition-colors ${
                        index === currentQuestionIndex
                          ? 'bg-blue-600 text-white'
                          : itemResults[index]?.passed
                            ? 'bg-green-100 text-green-700 hover:bg-green-200'
                            : itemResults[index]?.feedback
                              ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                              : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                      }`}
                    >
                      {index + 1}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 右側：批改評分 */}
          <Card>
            <CardHeader>
              <CardTitle>批改評分</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* 分數滑桿 */}
              <div>
                <Label className="text-base font-semibold">分數評定</Label>
                <div className="mt-4 space-y-4">
                  <Input
                    type="range"
                    value={score}
                    onChange={(e) => setScore(Number(e.target.value))}
                    min={0}
                    max={100}
                    step={1}
                    className="w-full"
                  />
                  <div className="text-center">
                    <span className="text-4xl font-bold text-blue-600">
                      {score}
                    </span>
                    <span className="text-2xl text-gray-600 ml-2">分</span>
                  </div>
                </div>

                {/* 快速分數按鈕 */}
                <div className="flex gap-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setScore(100)}
                  >
                    滿分
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setScore(90)}
                  >
                    90分
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setScore(80)}
                  >
                    80分
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setScore(70)}
                  >
                    70分
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setScore(60)}
                  >
                    60分
                  </Button>
                </div>
              </div>

              {/* 當前題目評語編輯 */}
              <div>
                <Label className="text-base font-semibold">題目 {currentQuestionIndex + 1} 評語</Label>
                <Textarea
                  placeholder={`針對第 ${currentQuestionIndex + 1} 題的評語...`}
                  value={itemResults[currentQuestionIndex]?.feedback || ''}
                  onChange={(e) => updateItemFeedback(currentQuestionIndex, e.target.value)}
                  rows={3}
                  className="mt-2"
                />

                {/* 快速回饋選項 */}
                <div className="mt-3">
                  <p className="text-sm text-gray-600 mb-2">快速回饋：</p>
                  <div className="flex flex-wrap gap-2">
                    <Badge
                      variant="secondary"
                      className="cursor-pointer hover:bg-blue-100"
                      onClick={() => addQuickFeedback('很棒！繼續保持！')}
                    >
                      很棒！繼續保持！
                    </Badge>
                    <Badge
                      variant="secondary"
                      className="cursor-pointer hover:bg-blue-100"
                      onClick={() => addQuickFeedback('發音很準確，表現優秀！')}
                    >
                      發音準確
                    </Badge>
                    <Badge
                      variant="secondary"
                      className="cursor-pointer hover:bg-blue-100"
                      onClick={() => addQuickFeedback('語調自然，很有進步！')}
                    >
                      語調自然
                    </Badge>
                    <Badge
                      variant="secondary"
                      className="cursor-pointer hover:bg-blue-100"
                      onClick={() => addQuickFeedback('可以試著放慢速度，讓發音更清楚。')}
                    >
                      放慢速度
                    </Badge>
                    <Badge
                      variant="secondary"
                      className="cursor-pointer hover:bg-blue-100"
                      onClick={() => addQuickFeedback('注意語調起伏，會更生動。')}
                    >
                      注意語調
                    </Badge>
                    <Badge
                      variant="secondary"
                      className="cursor-pointer hover:bg-blue-100"
                      onClick={() => addQuickFeedback('多練習幾次會更流暢喔！')}
                    >
                      多加練習
                    </Badge>
                  </div>
                </div>
              </div>

              {/* 詳實記錄（唯讀） */}
              <div className="border-t pt-4">
                <Label className="text-base font-semibold">總評語回饋</Label>

                {/* 1. 詳實記錄 */}
                <div className="mt-3">
                  <Label className="text-sm text-gray-600">1. 詳實記錄</Label>
                  <div className="mt-1 p-3 bg-gray-100 rounded-lg border border-gray-300 max-h-48 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-xs text-gray-700 font-mono">
{itemResults.map((result, index) => {
  const item = submission?.submissions[index];
  if (!item) return '';
  return `題目 ${index + 1} ${result.passed ? '✅' : '❌'}: ${item.question_text.substring(0, 20)}...${result.passed ? ' 很棒！繼續保持！' : ' 需要加強！'}
${result.feedback ? `評語: ${result.feedback}` : ''}
`;
}).join('')}
                    </pre>
                  </div>
                </div>

                {/* 2. 總評（可編輯） */}
                <div className="mt-3">
                  <Label className="text-sm text-gray-600">2. 總評</Label>
                  <Textarea
                    placeholder="給學生的總體鼓勵和建議..."
                    value={overallComment}
                    onChange={(e) => setOverallComment(e.target.value)}
                    rows={3}
                    className="mt-1"
                  />
                </div>
              </div>

              {/* 提交按鈕 */}
              <div className="flex gap-3 pt-4">
                <Button
                  onClick={handleSubmitGrade}
                  disabled={submitting}
                  className="flex-1"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {submitting ? '儲存中...' : '儲存評分'}
                </Button>
                <Button
                  onClick={handleSaveAndNext}
                  disabled={submitting}
                  variant="outline"
                  className="flex-1"
                >
                  <ArrowRight className="h-4 w-4 mr-2" />
                  儲存並下一位
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
