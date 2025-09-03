import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';
import {
  User,
  Clock,
  ChevronLeft,
  ChevronRight,
  Save,
  X,
  Volume2,
  AlertCircle
} from 'lucide-react';

interface GradingModalProps {
  isOpen: boolean;
  onClose: () => void;
  studentId: number;
  studentName: string;
  assignmentId: number;
  assignmentTitle: string;
  currentIndex?: number;
  totalStudents?: number;
  onSaveAndNext?: () => void;
  onPrevious?: () => void;
  onNext?: () => void;
}

interface StudentSubmission {
  student_id: number;
  student_name: string;
  student_email: string;
  status: string;
  submitted_at?: string;
  content_type: string;
  submissions: Array<{
    question_text: string;
    question_translation?: string;
    audio_url?: string;
    student_answer?: string;
    transcript?: string;
    duration?: number;
    content_title?: string;
  }>;
  content_groups?: Array<{
    content_id: number;
    content_title: string;
    content_type?: string;
    submissions: Array<{
      question_text: string;
      question_translation?: string;
      audio_url?: string;
      student_answer?: string;
      transcript?: string;
      duration?: number;
    }>;
  }>;
  current_score?: number;
  current_feedback?: string;
}

interface ItemFeedback {
  [key: number]: string;
}

export default function GradingModal({
  isOpen,
  onClose,
  studentId,
  studentName,
  assignmentId,
  assignmentTitle,
  currentIndex = 1,
  totalStudents = 1,
  onSaveAndNext,
  onPrevious,
  onNext,
}: GradingModalProps) {
  const [submission, setSubmission] = useState<StudentSubmission | null>(null);
  const [loading, setLoading] = useState(true);
  const [score, setScore] = useState(80);
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [selectedItemIndex, setSelectedItemIndex] = useState(0);
  const [itemFeedbacks, setItemFeedbacks] = useState<ItemFeedback>({});

  // 計算題目索引映射
  const getItemIndexMap = () => {
    const map = new Map<string, number>();
    if (!submission?.content_groups) return map;

    let globalIndex = 0;
    submission.content_groups.forEach((group) => {
      group.submissions.forEach((_, localIndex) => {
        map.set(`${group.content_id}-${localIndex}`, globalIndex);
        globalIndex++;
      });
    });
    return map;
  };

  const itemIndexMap = getItemIndexMap();

  useEffect(() => {
    if (isOpen && assignmentId && studentId) {
      loadSubmission();
    }
  }, [isOpen, assignmentId, studentId]);

  const loadSubmission = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<StudentSubmission>(
        `/api/teachers/assignments/${assignmentId}/submissions/${studentId}`
      );

      setSubmission(response);

      // 如果已經有分數，預填
      if (response && response.current_score !== undefined && response.current_score !== null) {
        setScore(response.current_score);
        setFeedback(response.current_feedback || '');
      } else {
        setScore(80); // 預設分數
        setFeedback(''); // 清空回饋
      }
    } catch (error) {
      console.error('Failed to load submission:', error);
      toast.error('無法載入學生作業');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitGrade = async () => {
    if (!submission) return;

    try {
      setSubmitting(true);

      // 合併個別題目評語到總評語
      const itemFeedbackTexts: string[] = [];
      Object.entries(itemFeedbacks).forEach(([index, fb]) => {
        if (fb.trim()) {
          itemFeedbackTexts.push(`題目 ${parseInt(index) + 1}: ${fb}`);
        }
      });

      const combinedFeedback = itemFeedbackTexts.length > 0
        ? itemFeedbackTexts.join('\n') + (feedback ? `\n\n總評: ${feedback}` : '')
        : feedback;

      await apiClient.post(
        `/api/teachers/assignments/${assignmentId}/grade`,
        {
          student_id: studentId,
          score: score,
          feedback: combinedFeedback
        }
      );

      toast.success('評分已儲存');

      // 如果有下一位功能，執行它
      if (onSaveAndNext) {
        onSaveAndNext();
      } else {
        onClose();
      }
    } catch (error) {
      console.error('Failed to submit grade:', error);
      toast.error('評分失敗，請稍後再試');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { label: string; className: string }> = {
      'NOT_STARTED': { label: '未開始', className: 'bg-gray-100 text-gray-600' },
      'IN_PROGRESS': { label: '進行中', className: 'bg-blue-100 text-blue-600' },
      'SUBMITTED': { label: '已提交', className: 'bg-green-100 text-green-600' },
      'GRADED': { label: '已批改', className: 'bg-purple-100 text-purple-600' },
      'RETURNED': { label: '已發還', className: 'bg-yellow-100 text-yellow-600' },
      'RESUBMITTED': { label: '重新提交', className: 'bg-orange-100 text-orange-600' },
    };

    const config = statusMap[status] || { label: status, className: 'bg-gray-100 text-gray-600' };
    return <Badge className={config.className}>{config.label}</Badge>;
  };

  const quickScoreButtons = [
    { label: '滿分', value: 100 },
    { label: '90分', value: 90 },
    { label: '80分', value: 80 },
    { label: '70分', value: 70 },
    { label: '60分', value: 60 },
  ];

  const commonFeedback = [
    '很棒！繼續保持！',
    '進步很多，加油！',
    '發音清晰，表現優秀！',
    '語調自然，很有進步！',
    '請多練習，加油！',
  ];

  // 鍵盤快捷鍵
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!isOpen) return;

      // Cmd/Ctrl + Enter: 儲存並下一位
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        handleSubmitGrade();
      }
      // ESC: 關閉
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
      // 左右箭頭切換學生
      if (e.key === 'ArrowLeft' && onPrevious) {
        e.preventDefault();
        onPrevious();
      }
      if (e.key === 'ArrowRight' && onNext) {
        e.preventDefault();
        onNext();
      }
      // 數字鍵切換題目
      if (e.key >= '1' && e.key <= '9' && submission?.submissions) {
        const index = parseInt(e.key) - 1;
        if (index < submission.submissions.length) {
          setSelectedItemIndex(index);
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isOpen, onClose, onPrevious, onNext, submission]);

  // 獲取當前選中的題目
  const currentItem = submission?.submissions?.[selectedItemIndex];

  // Debug 輸出
  useEffect(() => {
    console.log('Selected index:', selectedItemIndex);
    console.log('Current item:', currentItem);
    console.log('Total submissions:', submission?.submissions?.length);
  }, [selectedItemIndex, currentItem, submission]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-7xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <DialogHeader className="pb-4 border-b">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl">
              批改作業 - {assignmentTitle}
            </DialogTitle>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                學生：{studentName} ({currentIndex} / {totalStudents})
              </span>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onPrevious}
                  disabled={!onPrevious || currentIndex === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onNext}
                  disabled={!onNext || currentIndex === totalStudents}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </DialogHeader>

        {/* Body - 左右兩欄 */}
        <div className="flex-1 flex overflow-hidden">
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">載入中...</p>
              </div>
            </div>
          ) : submission ? (
            <>
              {/* 左側 - 學生資訊與作答內容 */}
              <div className="w-1/2 border-r overflow-y-auto p-6 bg-gray-50">
                {/* 學生資訊 */}
                <div className="mb-6">
                  <div className="flex items-center justify-between p-4 bg-white rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <User className="h-6 w-6 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-lg">{submission.student_name}</h3>
                        <p className="text-sm text-gray-500">{submission.student_email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {getStatusBadge(submission.status)}
                      {submission.submitted_at && (
                        <div className="flex items-center gap-1 text-sm text-gray-500">
                          <Clock className="h-4 w-4" />
                          {new Date(submission.submitted_at).toLocaleDateString('zh-TW')}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* 學生作答內容 - 按 Content 分組顯示 */}
                {submission.content_groups && submission.content_groups.length > 0 ? (
                  <div className="space-y-4">
                    <h4 className="font-medium">學生作答內容</h4>

                    {/* 題目選擇區 - 緊湊設計 */}
                    <div className="space-y-2">
                      {submission.content_groups.map((group, groupIndex) => (
                        <div key={group.content_id} className="bg-gray-50 rounded-lg p-3">
                          <div className="flex items-center gap-3">
                            <div className="flex-shrink-0">
                              <span className="text-xs font-medium text-gray-600">
                                {String.fromCharCode(65 + groupIndex)}
                              </span>
                            </div>
                            <div className="flex-1">
                              <div className="text-sm font-medium text-gray-700 mb-1">
                                {group.content_title}
                              </div>
                              <div className="flex gap-1">
                                {group.submissions.map((_, index) => {
                                  const globalIndex = itemIndexMap.get(`${group.content_id}-${index}`) || 0;

                                  return (
                                    <Button
                                      key={index}
                                      variant={selectedItemIndex === globalIndex ? "default" : "outline"}
                                      size="sm"
                                      className="w-6 h-6 p-0 text-xs"
                                      onClick={() => {
                                        console.log(`Clicking button ${index + 1} in group ${group.content_id}, globalIndex: ${globalIndex}`);
                                        setSelectedItemIndex(globalIndex);
                                      }}
                                    >
                                      {index + 1}
                                    </Button>
                                  );
                                })}
                              </div>
                            </div>
                            <div className="flex-shrink-0 text-xs text-gray-500">
                              {group.submissions.length} 題
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* 當前選中題目的詳細內容 */}
                    {currentItem && (
                      <Card className="p-5 bg-white border-2 border-blue-100">
                        <div className="space-y-4">
                          {/* 題目標題 */}
                          <div className="border-b pb-3">
                            <div className="flex items-center justify-between">
                              <h5 className="text-sm font-semibold text-gray-700">
                                題目 {selectedItemIndex + 1}
                              </h5>
                              {currentItem.content_title && (
                                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                  {currentItem.content_title}
                                </span>
                              )}
                            </div>
                          </div>

                          {/* 題目內容 */}
                          <div>
                            <p className="font-medium text-lg text-gray-900">
                              {currentItem.question_text}
                            </p>
                            {currentItem.question_translation && (
                              <p className="text-sm text-gray-500 mt-1">
                                {currentItem.question_translation}
                              </p>
                            )}
                          </div>

                          {/* 學生答案 */}
                          {currentItem.student_answer && (
                            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                              <p className="text-xs font-semibold text-blue-700 mb-1">學生答案</p>
                              <p className="text-sm text-gray-800">{currentItem.student_answer}</p>
                            </div>
                          )}

                          {/* 語音辨識結果 */}
                          {currentItem.transcript && (
                            <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                              <p className="text-xs font-semibold text-green-700 mb-1">語音辨識結果</p>
                              <p className="text-sm text-gray-800">{currentItem.transcript}</p>
                            </div>
                          )}

                          {/* 音頻播放 */}
                          {currentItem.audio_url && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full"
                              onClick={() => {
                                const audio = new Audio(currentItem.audio_url);
                                audio.play();
                              }}
                            >
                              <Volume2 className="h-3 w-3 mr-2" />
                              播放學生錄音
                            </Button>
                          )}

                          {/* 錄音時長 */}
                          {currentItem.duration && (
                            <div className="flex items-center gap-1 text-xs text-gray-500">
                              <Clock className="h-3 w-3" />
                              錄音時長：{Math.round(currentItem.duration)} 秒
                            </div>
                          )}

                          {/* 個別題目評語 */}
                          <div className="pt-3 mt-3 border-t">
                            <label className="text-xs font-medium text-gray-700 mb-1 block">
                              針對此題評語
                            </label>
                            <Textarea
                              value={itemFeedbacks[selectedItemIndex] || ''}
                              onChange={(e) => {
                                setItemFeedbacks({
                                  ...itemFeedbacks,
                                  [selectedItemIndex]: e.target.value
                                });
                              }}
                              placeholder="輸入針對此題的評語..."
                              className="min-h-[50px] resize-none bg-gray-50 text-sm"
                            />
                          </div>
                        </div>
                      </Card>
                    )}
                  </div>
                ) : (submission.submissions && submission.submissions.length > 0) ? (
                  <div>
                    <h4 className="font-medium mb-3 flex items-center justify-between">
                      <span>學生作答內容</span>
                      {submission.submissions.length > 1 && (
                        <div className="flex gap-1">
                          {submission.submissions.map((_, index) => (
                            <Button
                              key={index}
                              variant={selectedItemIndex === index ? "default" : "outline"}
                              size="sm"
                              className="w-8 h-8 p-0"
                              onClick={() => setSelectedItemIndex(index)}
                            >
                              {index + 1}
                            </Button>
                          ))}
                        </div>
                      )}
                    </h4>

                    {currentItem && (
                      <div className="space-y-4">
                        <Card className="p-6 bg-white">
                          <div className="space-y-4">
                            <div>
                              <h5 className="text-sm font-medium text-gray-500 mb-2">
                                題目 {selectedItemIndex + 1}
                                {currentItem.content_title && (
                                  <span className="ml-2 text-blue-600">
                                    ({currentItem.content_title})
                                  </span>
                                )}
                              </h5>
                              <p className="font-medium text-lg">{currentItem.question_text}</p>
                              {currentItem.question_translation && (
                                <p className="text-sm text-gray-500 mt-1">
                                  {currentItem.question_translation}
                                </p>
                              )}
                            </div>

                            {currentItem.student_answer && (
                              <div className="p-4 bg-blue-50 rounded-lg">
                                <p className="text-sm font-medium mb-1">學生答案</p>
                                <p className="text-base">{currentItem.student_answer}</p>
                              </div>
                            )}

                            {currentItem.transcript && (
                              <div className="p-4 bg-green-50 rounded-lg">
                                <p className="text-sm font-medium mb-1">語音辨識結果</p>
                                <p className="text-base">{currentItem.transcript}</p>
                              </div>
                            )}

                            {currentItem.audio_url && (
                              <Button
                                variant="outline"
                                className="w-full"
                                onClick={() => {
                                  // 播放音頻
                                  const audio = new Audio(currentItem.audio_url);
                                  audio.play();
                                }}
                              >
                                <Volume2 className="h-4 w-4 mr-2" />
                                播放學生錄音
                              </Button>
                            )}

                            {currentItem.duration && (
                              <div className="flex items-center gap-2 text-sm text-gray-500">
                                <Clock className="h-4 w-4" />
                                錄音時長：{Math.round(currentItem.duration)} 秒
                              </div>
                            )}
                          </div>
                        </Card>

                        {/* 個別題目評語 */}
                        <Card className="p-4 bg-yellow-50">
                          <label className="text-sm font-medium mb-2 block">
                            題目 {selectedItemIndex + 1} 評語
                          </label>
                          <Textarea
                            value={itemFeedbacks[selectedItemIndex] || ''}
                            onChange={(e) => {
                              setItemFeedbacks({
                                ...itemFeedbacks,
                                [selectedItemIndex]: e.target.value
                              });
                            }}
                            placeholder={`針對題目 ${selectedItemIndex + 1} 的表現給予評語...`}
                            className="min-h-[80px] resize-none bg-white"
                          />
                        </Card>
                      </div>
                    )}
                  </div>
                ) : (
                  <Card className="p-6 bg-white">
                    <div className="text-center text-gray-500">
                      <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                      <p>暫無作答內容</p>
                    </div>
                  </Card>
                )}
              </div>

              {/* 右側 - 批改區域 */}
              <div className="w-1/2 p-6 overflow-y-auto">
                <div className="space-y-6">
                  <Card className="p-6">
                    <h4 className="font-medium mb-4">批改評分</h4>

                    {/* 分數滑桿 */}
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium">分數評定</label>
                          <span className="text-2xl font-bold text-blue-600">{score} 分</span>
                        </div>
                        <input
                          type="range"
                          value={score}
                          onChange={(e) => setScore(Number(e.target.value))}
                          min={0}
                          max={100}
                          step={1}
                          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                          style={{
                            background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${score}%, #e5e7eb ${score}%, #e5e7eb 100%)`
                          }}
                        />

                        {/* 快速分數按鈕 */}
                        <div className="flex gap-2 mt-3">
                          {quickScoreButtons.map((btn) => (
                            <Button
                              key={btn.value}
                              variant={score === btn.value ? 'default' : 'outline'}
                              size="sm"
                              onClick={() => setScore(btn.value)}
                            >
                              {btn.label}
                            </Button>
                          ))}
                        </div>
                      </div>

                      {/* 評語 */}
                      <div>
                        <label className="text-sm font-medium mb-2 block">總評語回饋</label>

                        {/* 顯示已收集的個別評語 */}
                        {Object.keys(itemFeedbacks).length > 0 && (
                          <div className="mb-3 p-3 bg-gray-50 rounded-lg">
                            <p className="text-xs text-gray-600 mb-2">已收集的個別評語：</p>
                            <div className="space-y-1">
                              {Object.entries(itemFeedbacks).map(([index, fb]) =>
                                fb.trim() && (
                                  <div key={index} className="text-sm text-gray-700">
                                    <span className="font-medium">題目 {parseInt(index) + 1}:</span> {fb}
                                  </div>
                                )
                              )}
                            </div>
                          </div>
                        )}

                        <Textarea
                          value={feedback}
                          onChange={(e) => setFeedback(e.target.value)}
                          placeholder="請輸入總評語..."
                          className="min-h-[120px] resize-none"
                        />

                        {/* 快速評語 */}
                        <div className="flex flex-wrap gap-2 mt-2">
                          {commonFeedback.map((text) => (
                            <Badge
                              key={text}
                              variant="secondary"
                              className="cursor-pointer hover:bg-gray-200"
                              onClick={() => setFeedback(feedback ? `${feedback} ${text}` : text)}
                            >
                              {text}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </Card>

                  {/* 批改提示 */}
                  <Card className="p-4 bg-blue-50">
                    <h5 className="font-medium mb-2 text-blue-900">批改提示</h5>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>• 請根據學生的發音準確度給予評分</li>
                      <li>• 考慮語調、流暢度和表達的自然度</li>
                      <li>• 給予具體的改進建議</li>
                      <li>• 鼓勵學生的進步和努力</li>
                    </ul>
                  </Card>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              找不到學生作業
            </div>
          )}
        </div>

        {/* Footer */}
        <DialogFooter className="pt-4 border-t">
          <div className="flex items-center justify-between w-full">
            <div className="text-xs text-gray-500">
              提示：使用 ⌘+Enter 儲存並下一位，← → 切換學生，數字鍵 1-9 切換題目
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                <X className="h-4 w-4 mr-2" />
                取消
              </Button>
              <Button
                onClick={handleSubmitGrade}
                disabled={submitting || !submission}
              >
                <Save className="h-4 w-4 mr-2" />
                儲存評分
              </Button>
              {onSaveAndNext && (
                <Button
                  onClick={handleSubmitGrade}
                  disabled={submitting || !submission}
                  variant="default"
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  儲存並下一位
                  <ChevronRight className="h-4 w-4 ml-2" />
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
