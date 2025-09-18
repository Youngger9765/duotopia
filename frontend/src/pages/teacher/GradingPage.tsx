import { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import AIScoreDisplay from "@/components/shared/AIScoreDisplay";
import AudioRecorder from "@/components/shared/AudioRecorder";
import {
  User,
  Clock,
  ChevronLeft,
  ChevronRight,
  Save,
  ArrowLeft,
  Volume2,
  CheckCircle,
  AlertCircle,
  Users,
  X,
} from "lucide-react";
import { Assignment } from "@/types";

interface AssignmentInfo extends Assignment {
  title: string;
}

interface StudentInfo {
  student_id: number;
  student_name: string;
  status: string;
}

interface StudentsResponse {
  students: StudentInfo[];
}

interface SubmissionItem {
  question_text: string;
  question_translation?: string;
  audio_url?: string;  // 學生的錄音
  question_audio_url?: string;  // 題目的參考錄音
  student_answer?: string;
  transcript?: string;
  duration?: number;
  content_title?: string;
  feedback?: string;
  passed?: boolean | null;
  ai_scores?: {
    accuracy_score: number;
    fluency_score: number;
    pronunciation_score: number;
    completeness_score: number;
    overall_score: number;
    word_details?: Array<{
      word: string;
      accuracy_score: number;
      error_type?: string;
    }>;
  };
}

interface StudentSubmission {
  student_number: number;
  student_name: string;
  student_email: string;
  status: string;
  submitted_at?: string;
  content_type: string;
  submissions: SubmissionItem[];
  content_groups?: Array<{
    content_id: number;
    content_title: string;
    content_type?: string;
    submissions: SubmissionItem[];
  }>;
  current_score?: number;
  current_feedback?: string;
  ai_scores?: {
    accuracy_score: number;
    fluency_score: number;
    pronunciation_score: number;
    completeness_score: number;
    overall_score: number;
    word_details?: Array<{
      word: string;
      accuracy_score: number;
      error_type?: string;
    }>;
  };
}

interface ItemFeedback {
  [key: number]: {
    feedback: string;
    passed: boolean | null; // true=通過, false=未通過, null=未評
  };
}

interface StudentListItem {
  student_id: number;
  student_name: string;
  status: string;
}

export default function GradingPage() {
  const { classroomId, assignmentId } = useParams<{ classroomId: string; assignmentId: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const studentId = searchParams.get("studentId");

  const [submission, setSubmission] = useState<StudentSubmission | null>(null);
  const [loading, setLoading] = useState(true);
  const [score, setScore] = useState(80);
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [selectedItemIndex, setSelectedItemIndex] = useState(0);
  const [itemFeedbacks, setItemFeedbacks] = useState<ItemFeedback>({});
  const [autoSaving, setAutoSaving] = useState(false);

  // 學生列表相關
  const [studentList, setStudentList] = useState<StudentListItem[]>([]);
  const [currentStudentIndex, setCurrentStudentIndex] = useState(0);
  const [assignmentTitle, setAssignmentTitle] = useState("");

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

  // 載入作業資訊和學生列表
  useEffect(() => {
    if (assignmentId) {
      loadAssignmentInfo();
      loadStudentList();
    }
  }, [assignmentId]);

  // 載入學生提交內容
  useEffect(() => {
    if (assignmentId && studentId) {
      loadSubmission();
      // 找到當前學生在列表中的位置
      const index = studentList.findIndex(
        (s) => s.student_id === parseInt(studentId),
      );
      if (index !== -1) {
        setCurrentStudentIndex(index);
      }
    } else if (assignmentId && studentList.length > 0 && !studentId) {
      // 如果沒有指定 studentId，預設選擇第一個學生（API 只回傳被指派的學生）
      const firstStudent = studentList[0];
      if (firstStudent && firstStudent.student_id) {
        setSearchParams({ studentId: firstStudent.student_id.toString() });
      }
    }
  }, [assignmentId, studentId, studentList]);

  const loadAssignmentInfo = async () => {
    try {
      const response = await apiClient.get(
        `/api/teachers/assignments/${assignmentId}`,
      ) as AssignmentInfo;
      setAssignmentTitle(response.title || `作業 #${assignmentId}`);
    } catch (error) {
      console.error("Failed to load assignment info:", error);
    }
  };

  const loadStudentList = async () => {
    try {
      // 載入此作業的所有學生
      const response = await apiClient.get(
        `/api/teachers/assignments/${assignmentId}/students`,
      ) as StudentsResponse;
      setStudentList(response.students || []);
    } catch (error) {
      console.error("Failed to load student list:", error);
      // 如果 API 還沒實作，使用模擬資料
      setStudentList([
        { student_id: 1, student_name: "王小明", status: "SUBMITTED" },
        { student_id: 2, student_name: "李小華", status: "GRADED" },
        { student_id: 3, student_name: "張大同", status: "SUBMITTED" },
      ]);
    }
  };

  const loadSubmission = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(
        `/api/teachers/assignments/${assignmentId}/submissions/${studentId}`,
      ) as StudentSubmission;

      setSubmission(response);

      // 如果已經有分數，預填
      if (
        response.current_score !== undefined &&
        response.current_score !== null
      ) {
        setScore(response.current_score);
        setFeedback(response.current_feedback || "");
      } else {
        setScore(80);
        setFeedback("");
      }

      // 載入個別題目的評語和通過狀態
      const loadedFeedbacks: ItemFeedback = {};
      if (response.submissions) {
        response.submissions.forEach((sub: {feedback?: string; passed?: boolean | null}, index: number) => {
          if (sub.feedback || sub.passed !== null) {
            loadedFeedbacks[index] = {
              feedback: sub.feedback || "",
              passed: sub.passed ?? null
            };
          }
        });
      }
      setItemFeedbacks(loadedFeedbacks);
      setSelectedItemIndex(0); // 重置選中的題目
    } catch (error) {
      console.error("Failed to load submission:", error);
      toast.error("無法載入學生作業");
    } finally {
      setLoading(false);
    }
  };

  // 自動儲存功能（不顯示提示）
  const handleAutoSave = async () => {
    if (!submission || submitting || autoSaving) return;

    setAutoSaving(true);
    try {
      // 準備個別題目的評分資料
      const itemResults: Array<{item_index: number; feedback: string; passed: boolean | null; score: number}> = [];
      Object.entries(itemFeedbacks).forEach(([index, fb]) => {
        itemResults.push({
          item_index: parseInt(index),
          feedback: fb.feedback || "",
          passed: fb.passed,
          score: fb.passed === true ? 100 : fb.passed === false ? 60 : 80
        });
      });

      // 合併個別題目評語到總評語
      const itemFeedbackTexts: string[] = [];
      Object.entries(itemFeedbacks).forEach(([index, fb]) => {
        if (fb.feedback && fb.feedback.trim()) {
          const passStatus =
            fb.passed === true ? "✅" : fb.passed === false ? "❌" : "";
          itemFeedbackTexts.push(
            `題目 ${parseInt(index) + 1} ${passStatus}: ${fb.feedback}`,
          );
        }
      });

      // 詳實記錄（各題評語）
      const detailedRecord = itemFeedbackTexts.length > 0
        ? itemFeedbackTexts.join("\n")
        : "";

      // 組合完整回饋：詳實記錄 + 總評
      const combinedFeedback = detailedRecord +
        (feedback ? `\n\n總評: ${feedback}` : "");

      await apiClient.post(`/api/teachers/assignments/${assignmentId}/grade`, {
        student_id: parseInt(studentId!),
        score: score,
        feedback: combinedFeedback,
        item_results: itemResults,
        update_status: false  // 自動儲存不更新狀態
      });

      // 自動儲存不顯示成功訊息，避免干擾
    } catch (error) {
      console.error("Auto-save failed:", error);
      // 自動儲存失敗也不顯示錯誤，避免頻繁提示
    } finally {
      setAutoSaving(false);
    }
  };

  const handleSaveGrade = async () => {
    if (!submission) return;

    try {
      setSubmitting(true);

      // 準備個別題目的評分資料
      const itemResults: Array<{item_index: number; feedback: string; passed: boolean | null; score: number}> = [];
      Object.entries(itemFeedbacks).forEach(([index, fb]) => {
        itemResults.push({
          item_index: parseInt(index),
          feedback: fb.feedback || "",
          passed: fb.passed,
          score: fb.passed === true ? 100 : fb.passed === false ? 60 : 80
        });
      });

      // 合併個別題目評語到總評語（用於顯示）
      const itemFeedbackTexts: string[] = [];
      Object.entries(itemFeedbacks).forEach(([index, fb]) => {
        if (fb.feedback && fb.feedback.trim()) {
          const passStatus =
            fb.passed === true ? "✅" : fb.passed === false ? "❌" : "";
          itemFeedbackTexts.push(
            `題目 ${parseInt(index) + 1} ${passStatus}: ${fb.feedback}`,
          );
        }
      });

      // 詳實記錄（各題評語）
      const detailedRecord = itemFeedbackTexts.length > 0
        ? itemFeedbackTexts.join("\n")
        : "";

      // 組合完整回饋：詳實記錄 + 總評
      const combinedFeedback = detailedRecord +
        (feedback ? `\n\n總評: ${feedback}` : "");

      await apiClient.post(`/api/teachers/assignments/${assignmentId}/grade`, {
        student_id: parseInt(studentId!),
        score: score,
        feedback: combinedFeedback,
        item_results: itemResults,
        update_status: false  // 儲存評分但不更新狀態
      });

      toast.success("評分已儲存");
    } catch (error) {
      console.error("Failed to save grade:", error);
      toast.error("儲存失敗，請稍後再試");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCompleteGrading = async () => {
    if (!submission) return;

    try {
      setSubmitting(true);

      // 準備個別題目的評分資料
      const itemResults: Array<{item_index: number; feedback: string; passed: boolean | null; score: number}> = [];
      Object.entries(itemFeedbacks).forEach(([index, fb]) => {
        itemResults.push({
          item_index: parseInt(index),
          feedback: fb.feedback || "",
          passed: fb.passed,
          score: fb.passed === true ? 100 : fb.passed === false ? 60 : 80
        });
      });

      // 合併個別題目評語到總評語（用於顯示）
      const itemFeedbackTexts: string[] = [];
      Object.entries(itemFeedbacks).forEach(([index, fb]) => {
        if (fb.feedback && fb.feedback.trim()) {
          const passStatus =
            fb.passed === true ? "✅" : fb.passed === false ? "❌" : "";
          itemFeedbackTexts.push(
            `題目 ${parseInt(index) + 1} ${passStatus}: ${fb.feedback}`,
          );
        }
      });

      // 詳實記錄（各題評語）
      const detailedRecord = itemFeedbackTexts.length > 0
        ? itemFeedbackTexts.join("\n")
        : "";

      // 組合完整回饋：詳實記錄 + 總評
      const combinedFeedback = detailedRecord +
        (feedback ? `\n\n總評: ${feedback}` : "");

      await apiClient.post(`/api/teachers/assignments/${assignmentId}/grade`, {
        student_id: parseInt(studentId!),
        score: score,
        feedback: combinedFeedback,
        item_results: itemResults,
        update_status: true  // 完成批改時更新狀態為 GRADED
      });

      toast.success("批改完成！");

      // 更新本地狀態
      if (submission) {
        submission.status = "GRADED";
      }

      // 更新學生列表中的狀態
      setStudentList(prev => prev.map(student =>
        student.student_id === parseInt(studentId!)
          ? { ...student, status: "GRADED" }
          : student
      ));

      // 切換到下一位學生
      if (currentStudentIndex < studentList.length - 1) {
        await handleNextStudent();
      }
    } catch (error) {
      console.error("Failed to complete grading:", error);
      toast.error("批改失敗，請稍後再試");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSetInProgress = async () => {
    if (!submission) return;

    try {
      setSubmitting(true);

      // 如果已經是批改中狀態，不需要做任何事
      if (submission.status === "SUBMITTED" || submission.status === "RESUBMITTED") {
        toast.info("已經是批改中狀態");
        return;
      }

      await apiClient.post(`/api/teachers/assignments/${assignmentId}/set-in-progress`, {
        student_id: parseInt(studentId!),
      });

      toast.success("已設為批改中");

      // 更新學生列表中的狀態
      setStudentList(prev => prev.map(student =>
        student.student_id === parseInt(studentId!)
          ? { ...student, status: "SUBMITTED" }
          : student
      ));

      // 重新載入提交資料
      await loadSubmission();
    } catch (error) {
      console.error("Failed to set in progress:", error);
      toast.error("設定批改中失敗，請稍後再試");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRequestRevision = async () => {
    if (!submission) return;

    try {
      setSubmitting(true);

      await apiClient.post(`/api/teachers/assignments/${assignmentId}/return-for-revision`, {
        student_id: parseInt(studentId!),
        message: "請依照評語修改後重新提交"
      });

      toast.success("已要求學生訂正");

      // 更新本地狀態
      if (submission) {
        submission.status = "RETURNED";
      }

      // 更新學生列表中的狀態
      setStudentList(prev => prev.map(student =>
        student.student_id === parseInt(studentId!)
          ? { ...student, status: "RETURNED" }
          : student
      ));

      // 重新載入提交資料
      await loadSubmission();
    } catch (error) {
      console.error("Failed to request revision:", error);
      toast.error("要求訂正失敗，請稍後再試");
    } finally {
      setSubmitting(false);
    }
  };

  const handlePreviousStudent = async () => {
    if (currentStudentIndex > 0) {
      // 切換前自動儲存
      await handleAutoSave();
      const prevStudent = studentList[currentStudentIndex - 1];
      setSearchParams({ studentId: (prevStudent.student_id || 0).toString() });
    }
  };

  const handleNextStudent = async () => {
    if (currentStudentIndex < studentList.length - 1) {
      // 切換前自動儲存
      await handleAutoSave();
      const nextStudent = studentList[currentStudentIndex + 1];
      setSearchParams({ studentId: (nextStudent.student_id || 0).toString() });
    }
  };

  const handleStudentSelect = async (student: StudentListItem) => {
    // 切換前自動儲存
    await handleAutoSave();
    setSearchParams({ studentId: (student.student_id || 0).toString() });
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { label: string; className: string }> = {
      NOT_STARTED: { label: "未開始", className: "bg-gray-100 text-gray-600" },
      IN_PROGRESS: { label: "進行中", className: "bg-blue-100 text-blue-600" },
      SUBMITTED: { label: "已提交", className: "bg-green-100 text-green-600" },
      GRADED: { label: "已批改", className: "bg-purple-100 text-purple-600" },
      RETURNED: { label: "已發還", className: "bg-yellow-100 text-yellow-600" },
      RESUBMITTED: {
        label: "重新提交",
        className: "bg-orange-100 text-orange-600",
      },
    };

    const config = statusMap[status] || {
      label: status,
      className: "bg-gray-100 text-gray-600",
    };
    return <Badge className={config.className}>{config.label}</Badge>;
  };

  const quickScoreButtons = [
    { label: "滿分", value: 100 },
    { label: "90分", value: 90 },
    { label: "80分", value: 80 },
    { label: "70分", value: 70 },
    { label: "60分", value: 60 },
  ];


  // 移除自動同步，總評現在是獨立的欄位
  // 不再自動將個別評語同步到總評

  // 鍵盤快捷鍵
  useEffect(() => {
    const handleKeyPress = async (e: KeyboardEvent) => {
      // Cmd/Ctrl + Enter: 完成批改
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        handleCompleteGrading();
      }
      // 左右箭頭切換題目
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        if (selectedItemIndex > 0) {
          // 切換前自動儲存
          await handleAutoSave();
          setSelectedItemIndex(selectedItemIndex - 1);
        }
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        const totalQuestions = getTotalQuestions();
        if (selectedItemIndex < totalQuestions - 1) {
          // 切換前自動儲存
          await handleAutoSave();
          setSelectedItemIndex(selectedItemIndex + 1);
        }
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [selectedItemIndex, submission, handleAutoSave]);

  // Get current item from either structure
  const getCurrentItem = () => {
    if (submission?.content_groups && submission.content_groups.length > 0) {
      let currentIndex = 0;
      for (const group of submission.content_groups) {
        if (selectedItemIndex < currentIndex + group.submissions.length) {
          return group.submissions[selectedItemIndex - currentIndex];
        }
        currentIndex += group.submissions.length;
      }
      return null;
    }
    return submission?.submissions?.[selectedItemIndex] || null;
  };

  const currentItem = getCurrentItem();

  // Get total questions count from either structure
  const getTotalQuestions = () => {
    if (submission?.content_groups && submission.content_groups.length > 0) {
      return submission.content_groups.reduce((sum, group) => sum + group.submissions.length, 0);
    }
    return submission?.submissions?.length || 0;
  };

  const totalQuestions = getTotalQuestions();

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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => navigate(`/teacher/classroom/${classroomId}/assignment/${assignmentId}`)}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                返回
              </Button>
              <div className="border-l h-8 mx-2"></div>
              <h1 className="text-xl font-semibold">
                批改作業: {assignmentTitle}
              </h1>
            </div>

            {/* 學生切換導航 */}
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                {currentStudentIndex + 1} / {studentList.length} 位學生
              </span>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handlePreviousStudent}
                  disabled={currentStudentIndex === 0}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleNextStudent}
                  disabled={currentStudentIndex === studentList.length - 1}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-12 gap-4">
          {/* 左側 - 學生列表 */}
          <div className="col-span-2">
            <Card className="p-3">
              <h3 className="text-sm font-medium mb-2 flex items-center gap-1 text-gray-600">
                <Users className="h-4 w-4" />
                學生
              </h3>
              <div className="space-y-1">
                {studentList.map((student) => (
                  <button
                    key={student.student_id}
                    onClick={() => handleStudentSelect(student)}
                    className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                      student.student_id === parseInt(studentId!)
                        ? "bg-blue-100 text-blue-700"
                        : "hover:bg-gray-100"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="truncate">{student.student_name}</span>
                      {/* 根據狀態顯示不同圖標 */}
                      {student.status === "GRADED" && (
                        <CheckCircle className="h-3 w-3 text-green-600 flex-shrink-0" />
                      )}
                      {student.status === "RETURNED" && (
                        <X className="h-3 w-3 text-orange-600 flex-shrink-0" />
                      )}
                      {(student.status === "SUBMITTED" || student.status === "IN_PROGRESS") && (
                        <div className="h-3 w-3" /> // 空白佔位
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </Card>
          </div>

          {/* 中間 - 學生作答內容 */}
          <div className="col-span-6">
            {submission ? (
              <div className="space-y-3">
                {/* 學生資訊卡片 - 更精簡 */}
                <Card className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <User className="h-4 w-4 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-sm">
                          {submission.student_name}
                        </h3>
                        <p className="text-xs text-gray-500">
                          {submission.student_email}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(submission.status)}
                      {submission.submitted_at && (
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <Clock className="h-3 w-3" />
                          {new Date(submission.submitted_at).toLocaleDateString(
                            "zh-TW",
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>

                {/* 題目內容 */}
                {submission.content_groups &&
                submission.content_groups.length > 0 ? (
                  <>
                    {/* 題目詳情與評語整合卡片 */}
                    {currentItem && (
                      <Card className="p-5">
                        <div className="space-y-4">
                          {/* 標題區 */}
                          <div className="border-b pb-2">
                            <div className="flex items-center justify-between">
                              <h5 className="text-sm font-semibold text-gray-700">
                                題目 {selectedItemIndex + 1}
                              </h5>
                              {currentItem && currentItem.content_title && (
                                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                  {currentItem.content_title}
                                </span>
                              )}
                            </div>
                          </div>

                          {/* 題目內容 */}
                          <div className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="font-medium text-xl text-gray-900 leading-relaxed">
                                  {currentItem.question_text}
                                </p>
                                {currentItem.question_translation && (
                                  <p className="text-sm text-gray-600 mt-2 italic">
                                    {currentItem.question_translation}
                                  </p>
                                )}
                              </div>
                              {/* 題目參考音檔播放按鈕 - 始終顯示 */}
                              <Button
                                variant="outline"
                                size="sm"
                                disabled={!currentItem.question_audio_url}
                                onClick={() => {
                                  if (currentItem.question_audio_url) {
                                    const audio = new Audio(currentItem.question_audio_url);
                                    audio.play().catch(err => {
                                      console.error("Failed to play audio:", err);
                                      toast.error("無法播放參考音檔");
                                    });
                                  }
                                }}
                                className={`ml-3 flex-shrink-0 ${!currentItem.question_audio_url ? 'opacity-50' : ''}`}
                              >
                                <Volume2 className="h-3 w-3 mr-1" />
                                {currentItem.question_audio_url ? '參考音檔' : '無參考音檔'}
                              </Button>
                            </div>
                          </div>

                          {/* 學生答案 - 只在有資料時顯示 */}
                          {currentItem.student_answer && (
                            <div className="p-4 rounded-lg border bg-blue-50 border-blue-200">
                              <p className="text-xs font-semibold mb-2 text-blue-700">
                                學生答案
                              </p>
                              <p className="text-base text-gray-900 leading-relaxed">
                                {currentItem.student_answer}
                              </p>
                            </div>
                          )}

                          {/* 語音辨識結果 - 只在有資料時顯示 */}
                          {currentItem.transcript && (
                            <div className="p-4 rounded-lg border bg-green-50 border-green-200">
                              <p className="text-xs font-semibold mb-2 text-green-700">
                                語音辨識結果
                              </p>
                              <p className="text-base text-gray-900 leading-relaxed">
                                {currentItem.transcript}
                              </p>
                            </div>
                          )}

                          {/* 學生回答區塊分隔 */}
                          <div className="border-t pt-4 mt-4">
                            <h5 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                              學生回答
                            </h5>
                          </div>

                          {/* 學生錄音播放器 - 使用 AudioRecorder 元件（唯讀模式） */}
                          <AudioRecorder
                            variant="compact"
                            title=""
                            existingAudioUrl={currentItem.audio_url || undefined}
                            readOnly={true}
                            disabled={false}
                            className="border-0 p-0 shadow-none"
                          />

                          {/* AI 評分結果 - 使用共用元件 */}
                          {currentItem.ai_scores && (
                            <AIScoreDisplay
                              scores={currentItem.ai_scores}
                              hasRecording={!!currentItem.audio_url}
                              title="AI 自動評分結果"
                            />
                          )}

                          {/* 教師批改區塊分隔線 */}
                          <div className="border-t-2 border-blue-200 pt-4 mt-6">
                            <div className="bg-blue-50 -mx-5 px-5 py-2 mb-4">
                              <h5 className="text-sm font-semibold text-blue-700 flex items-center gap-2">
                                <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                                教師批改區
                              </h5>
                            </div>
                            {/* 評語標題與通過按鈕 */}
                            <div className="flex items-center justify-between mb-3">
                              <label className="text-sm font-semibold">
                                題目 {selectedItemIndex + 1} 教師評語
                              </label>
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant={
                                    itemFeedbacks[selectedItemIndex]?.passed ===
                                    true
                                      ? "default"
                                      : "outline"
                                  }
                                  className={
                                    itemFeedbacks[selectedItemIndex]?.passed ===
                                    true
                                      ? "bg-green-600 hover:bg-green-700"
                                      : ""
                                  }
                                  onClick={() => {
                                    setItemFeedbacks({
                                      ...itemFeedbacks,
                                      [selectedItemIndex]: {
                                        ...itemFeedbacks[selectedItemIndex],
                                        feedback:
                                          itemFeedbacks[selectedItemIndex]
                                            ?.feedback || "",
                                        passed: true,
                                      },
                                    });
                                  }}
                                  disabled={submission?.status === "GRADED"}
                                >
                                  <CheckCircle className="h-4 w-4 mr-1" />
                                  通過
                                </Button>
                                <Button
                                  size="sm"
                                  variant={
                                    itemFeedbacks[selectedItemIndex]?.passed ===
                                    false
                                      ? "default"
                                      : "outline"
                                  }
                                  className={
                                    itemFeedbacks[selectedItemIndex]?.passed ===
                                    false
                                      ? "bg-red-600 hover:bg-red-700"
                                      : ""
                                  }
                                  onClick={() => {
                                    setItemFeedbacks({
                                      ...itemFeedbacks,
                                      [selectedItemIndex]: {
                                        ...itemFeedbacks[selectedItemIndex],
                                        feedback:
                                          itemFeedbacks[selectedItemIndex]
                                            ?.feedback || "",
                                        passed: false,
                                      },
                                    });
                                  }}
                                  disabled={submission?.status === "GRADED"}
                                >
                                  <X className="h-4 w-4 mr-1" />
                                  未通過
                                </Button>
                              </div>
                            </div>

                            {/* 評語輸入框 */}
                            <Textarea
                              value={
                                itemFeedbacks[selectedItemIndex]?.feedback || ""
                              }
                              onChange={(e) => {
                                setItemFeedbacks({
                                  ...itemFeedbacks,
                                  [selectedItemIndex]: {
                                    ...itemFeedbacks[selectedItemIndex],
                                    feedback: e.target.value,
                                    passed:
                                      itemFeedbacks[selectedItemIndex]
                                        ?.passed ?? null,
                                  },
                                });
                              }}
                              placeholder="針對此題的評語..."
                              className="min-h-[80px] resize-none bg-white mt-3"
                              readOnly={submission?.status === "GRADED"}
                              disabled={submission?.status === "GRADED"}
                            />


                            {/* 快速評語 */}
                            <div className="mt-2 flex flex-wrap gap-1">
                              {[
                                "很棒！",
                                "請多練習",
                                "發音清晰",
                                "表現優秀！",
                                "語調自然",
                                "很有進步",
                                "加油！",
                              ].map((text) => (
                                <Badge
                                  key={text}
                                  variant="secondary"
                                  className="cursor-pointer hover:bg-gray-200 text-xs"
                                  onClick={() => {
                                    const current =
                                      itemFeedbacks[selectedItemIndex]
                                        ?.feedback || "";
                                    setItemFeedbacks({
                                      ...itemFeedbacks,
                                      [selectedItemIndex]: {
                                        feedback: current
                                          ? `${current} ${text}`
                                          : text,
                                        passed:
                                          itemFeedbacks[selectedItemIndex]
                                            ?.passed ?? null,
                                      },
                                    });
                                  }}
                                >
                                  {text}
                                </Badge>
                              ))}
                            </div>

                            {/* 題目導航按鈕 */}
                            <div className="border-t pt-3 mt-3">
                              <div className="flex justify-between items-center">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={async () => {
                                    // 切換前自動儲存
                                    await handleAutoSave();
                                    // 計算上一題的索引
                                    if (selectedItemIndex > 0) {
                                      setSelectedItemIndex(
                                        selectedItemIndex - 1,
                                      );
                                    }
                                  }}
                                  disabled={selectedItemIndex === 0}
                                  className="text-xs"
                                >
                                  <ChevronLeft className="h-3 w-3 mr-1" />
                                  上一題
                                </Button>

                                <span className="text-xs text-gray-500">
                                  {selectedItemIndex + 1} /{" "}
                                  {totalQuestions}
                                </span>

                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={async () => {
                                    // 切換前自動儲存
                                    await handleAutoSave();
                                    // 計算下一題的索引
                                    const totalQuestions = getTotalQuestions();
                                    if (
                                      selectedItemIndex <
                                      totalQuestions - 1
                                    ) {
                                      setSelectedItemIndex(
                                        selectedItemIndex + 1,
                                      );
                                    }
                                  }}
                                  disabled={
                                    selectedItemIndex >=
                                    totalQuestions - 1
                                  }
                                  className="text-xs"
                                >
                                  下一題
                                  <ChevronRight className="h-3 w-3 ml-1" />
                                </Button>
                              </div>

                              {/* 鍵盤快捷鍵提示 */}
                              <div className="text-center mt-2">
                                <span className="text-xs text-gray-400">
                                  提示：使用 ← → 鍵快速切換題目
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </Card>
                    )}
                  </>
                ) : (
                  <Card className="p-6">
                    <div className="text-center text-gray-500">
                      <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                      <p>暫無作答內容</p>
                    </div>
                  </Card>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500">找不到學生作業</div>
            )}
          </div>

          {/* 右側 - 批改評分 */}
          <div className="col-span-4">
            <Card className="p-4 sticky top-24">
              <h4 className="font-medium text-sm mb-3">批改評分</h4>

              <div className="space-y-3">
                {/* 題號選擇區 */}
                {submission && submission.content_groups && (
                  <div className="space-y-2">
                    {submission.content_groups.map((group) => (
                      <div
                        key={group.content_id}
                        className="bg-gray-50 rounded-lg p-2"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <div className="flex-1">
                            <div className="text-xs text-gray-600">
                              {group.content_title}
                            </div>
                          </div>
                          <span className="text-xs text-gray-400">
                            {group.submissions.length}題
                          </span>
                        </div>

                        {/* 題號按鈕 */}
                        <div className="flex gap-1">
                          {group.submissions.map((_, index) => {
                            const globalIndex =
                              itemIndexMap.get(
                                `${group.content_id}-${index}`,
                              ) || 0;
                            const itemStatus = itemFeedbacks[globalIndex];
                            const isPassed = itemStatus?.passed;

                            // 根據通過狀態決定按鈕樣式
                            let buttonClass = "w-7 h-7 p-0 text-xs ";
                            let buttonVariant: "default" | "outline" | "ghost" =
                              "outline";

                            if (selectedItemIndex === globalIndex) {
                              // 當前選中的題目
                              if (isPassed === true) {
                                buttonClass +=
                                  "bg-green-600 hover:bg-green-700 text-white border-green-600";
                              } else if (isPassed === false) {
                                buttonClass +=
                                  "bg-red-600 hover:bg-red-700 text-white border-red-600";
                              } else {
                                buttonClass +=
                                  "bg-blue-600 hover:bg-blue-700 text-white border-blue-600";
                              }
                              buttonVariant = "default";
                            } else {
                              // 非選中的題目
                              if (isPassed === true) {
                                buttonClass +=
                                  "bg-green-500 hover:bg-green-600 text-white border-green-500";
                                buttonVariant = "default";
                              } else if (isPassed === false) {
                                buttonClass +=
                                  "bg-red-500 hover:bg-red-600 text-white border-red-500";
                                buttonVariant = "default";
                              } else {
                                buttonClass += "bg-white hover:bg-gray-50";
                              }
                            }

                            return (
                              <Button
                                key={index}
                                variant={buttonVariant}
                                size="sm"
                                className={buttonClass}
                                onClick={async () => {
                                  // 切換前自動儲存
                                  await handleAutoSave();
                                  setSelectedItemIndex(globalIndex);
                                }}
                              >
                                {index + 1}
                              </Button>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 分隔線 */}
                <div className="border-t pt-3"></div>

                {/* 分數評定 - 緊湊版 */}
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium">分數</label>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold text-blue-600">
                      {score} 分
                    </span>
                    <input
                      type="range"
                      value={score}
                      onChange={(e) => setScore(Number(e.target.value))}
                      min={0}
                      max={100}
                      step={1}
                      className="w-32 h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      style={{
                        background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${score}%, #e5e7eb ${score}%, #e5e7eb 100%)`,
                      }}
                    />
                  </div>
                  <div className="flex gap-1">
                    {quickScoreButtons.slice(0, 3).map((btn) => (
                      <Button
                        key={btn.value}
                        variant={score === btn.value ? "default" : "outline"}
                        size="sm"
                        onClick={() => setScore(btn.value)}
                        className="text-xs px-1.5 py-0.5 h-6"
                      >
                        {btn.label}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* 總評語回饋 - 分為兩個欄位 */}
                <div className="space-y-3">
                  <label className="text-xs font-medium mb-1 block">
                    總評語回饋
                  </label>

                  {/* 1. 詳實記錄（唯讀） */}
                  <div>
                    <label className="text-xs text-gray-600 mb-1 block">
                      1. 詳實記錄
                    </label>
                    <div className="p-3 bg-gray-100 rounded-lg border border-gray-300 max-h-32 overflow-y-auto">
                      <pre className="whitespace-pre-wrap text-xs text-gray-700 font-mono">
{Array.from({ length: totalQuestions }).map((_, index) => {
  const result = itemFeedbacks[index];
  return `題目 ${index + 1} ${result?.passed === true ? '✅' : result?.passed === false ? '❌' : '⬜'}: ${result?.feedback || '(尚無評語)'}
`;
}).join('') || '請先批改各題目...'}
                      </pre>
                    </div>
                  </div>

                  {/* 2. 總評（可編輯） */}
                  <div>
                    <label className="text-xs text-gray-600 mb-1 block">
                      2. 總評
                    </label>
                    <Textarea
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                      placeholder="給學生的總體鼓勵和建議..."
                      className="min-h-[60px] resize-none text-sm"
                    />
                  </div>
                </div>

                {/* 操作按鈕 */}
                <div className="space-y-4 pt-4 border-t">
                  {/* 儲存按鈕 - 獨立一行 */}
                  <Button
                    onClick={handleSaveGrade}
                    disabled={submitting || !submission}
                    className="w-full"
                    size="lg"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    儲存評分
                  </Button>

                  {/* 狀態流程提示 */}
                  <div className="text-center text-xs text-gray-500">
                    選擇批改狀態
                  </div>

                  {/* 狀態選擇按鈕 - 三個並列狀態 */}
                  <div className="flex gap-2">
                    {/* 批改中 */}
                    <Button
                      onClick={handleSetInProgress}
                      disabled={submitting || !submission ||
                        (submission?.status === "SUBMITTED" || submission?.status === "RESUBMITTED")}
                      variant={
                        submission?.status === "SUBMITTED" || submission?.status === "RESUBMITTED"
                          ? "default"
                          : "outline"
                      }
                      className={`flex-1 ${
                        submission?.status === "SUBMITTED" || submission?.status === "RESUBMITTED"
                          ? "bg-blue-600 hover:bg-blue-700 text-white"
                          : "border-blue-600 text-blue-600 hover:bg-blue-50"
                      }`}
                    >
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      批改中
                    </Button>

                    {/* 要求訂正 */}
                    <Button
                      onClick={handleRequestRevision}
                      disabled={submitting || !submission}
                      variant={submission?.status === "RETURNED" ? "default" : "outline"}
                      className={`flex-1 ${
                        submission?.status === "RETURNED"
                          ? "bg-orange-600 hover:bg-orange-700 text-white"
                          : "border-orange-600 text-orange-600 hover:bg-orange-50"
                      }`}
                    >
                      <X className="h-4 w-4 mr-2" />
                      要求訂正
                    </Button>

                    {/* 已完成 */}
                    <Button
                      onClick={handleCompleteGrading}
                      disabled={submitting || !submission}
                      variant={submission?.status === "GRADED" ? "default" : "outline"}
                      className={`flex-1 ${
                        submission?.status === "GRADED"
                          ? "bg-green-600 hover:bg-green-700 text-white"
                          : "border-green-600 text-green-600 hover:bg-green-50"
                      }`}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      已完成
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
