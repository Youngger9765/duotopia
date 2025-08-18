
import React, { useState, useEffect } from 'react';
import { User } from '@/api/entities';
import { Class } from '@/api/entities';
import { Lesson } from '@/api/entities';
import { ClassStudent } from '@/api/entities';
import { StudentAssignment } from '@/api/entities';
import { ActivityResult } from '@/api/entities';
import { AssignmentSubmission } from '@/api/entities';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import {
    ListChecks, CheckCircle2, Sparkles, GraduationCap, MessageSquare, Star, Award,
    BookOpen, Mic, Edit2, Headphones, RefreshCw, Calendar, Clock, FileText, AlertTriangle
} from 'lucide-react';
import { motion } from 'framer-motion';
import { createPageUrl } from '@/utils';

export default function AssignmentsPage() {
    const [user, setUser] = useState(null); // Retaining original 'user' state
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [assignments, setAssignments] = useState([]);
    const [studentClass, setStudentClass] = useState(null);
    // Removed 'submissions' state as they are now fetched per assignment

    // **新增：評語對話框狀態**
    const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
    const [selectedFeedback, setSelectedFeedback] = useState(null);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            setError(null);
            try {
                // **核心修正：直接使用 User.me() 獲取當前用戶**
                const targetUser = await User.me();
                console.log('[Assignments] 當前登入用戶:', targetUser);
                setUser(targetUser); // Set the user state

                if (!targetUser?.email) {
                    setLoading(false);
                    // Optionally, redirect to login if no user email
                    console.warn('用戶未登入或無法獲取用戶資料，無法載入作業。');
                    return;
                }

                const studentEmail = targetUser.email;
                console.log('[Assignments] 開始載入作業，學生Email:', studentEmail);

                // Fetch student's class details for UI display (preserved from original logic)
                const allClassStudents = await ClassStudent.list();
                const studentClassLink = allClassStudents.find(cs => cs.email === targetUser.email);

                if (studentClassLink) {
                    const classDetails = await Class.get(studentClassLink.class_id);
                    setStudentClass(classDetails);
                } else {
                    setStudentClass(null); // No associated class found
                }

                // Fetch all student assignments
                const studentAssignments = await StudentAssignment.filter({
                    student_email: studentEmail
                }, '-assigned_date');
                console.log('[Assignments] 載入到的作業:', studentAssignments.length, '筆');

                // **核心修正：獲取相關的課文、提交狀態和活動結果**
                const assignmentsWithDetails = await Promise.all(
                    studentAssignments.map(async (assignment) => {
                        try {
                            const [lesson, submissions, activityResults] = await Promise.all([
                                Lesson.get(assignment.lesson_id),
                                AssignmentSubmission.filter({
                                    assignment_id: assignment.assignment_id,
                                    student_email: studentEmail
                                }),
                                ActivityResult.filter({
                                    assignment_id: assignment.assignment_id,
                                    student_email: studentEmail
                                })
                            ]);

                            // Calculate isCompleted and bestScore from activityResults
                            const isCompleted = activityResults.length > 0;
                            const bestScore = isCompleted ? Math.max(...activityResults.map(r => r.percentage_score || 0)) : 0;

                            return {
                                ...assignment,
                                lesson: lesson || { title: '課文已刪除', activity_type: 'unknown', is_active: false }, // Added is_active for robustness
                                submission: submissions && submissions.length > 0 ? submissions[0] : null,
                                isCompleted,
                                bestScore
                            };
                        } catch (error) {
                            console.error(`載入作業 ${assignment.assignment_id} 詳情失敗:`, error);
                            return {
                                ...assignment,
                                lesson: { title: '載入失敗', activity_type: 'unknown', is_active: false },
                                submission: null,
                                isCompleted: false,
                                bestScore: 0
                            };
                        }
                    })
                );

                // Filter out assignments where the lesson is not active, similar to original logic
                const finalProcessedAssignments = assignmentsWithDetails.filter(a => a.lesson && a.lesson.is_active);

                setAssignments(finalProcessedAssignments);
                console.log('[Assignments] 作業載入完成，總數:', finalProcessedAssignments.length);

            } catch (err) {
                console.error("Failed to load assignments:", err);
                setError("無法載入作業資料，請稍後再試。");
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    // **處理查看評語**
    const handleViewFeedback = (assignment) => {
        if (!assignment.submission) return;

        setSelectedFeedback({
            assignmentTitle: assignment.assignment_title,
            teacherGrade: assignment.submission.teacher_grade,
            teacherFeedback: assignment.submission.teacher_feedback,
            submissionStatus: assignment.submission.submission_status,
            gradedAt: assignment.submission.graded_at,
            revisionDescription: null, // Not applicable for regular feedback
            revisionRequestedAt: null, // Not applicable for regular feedback
            revisionRequirements: [] // Not applicable for regular feedback
        });
        setFeedbackModalOpen(true);
    };

    // **修正：處理查看訂正要求**
    const handleViewRevisionRequirements = (assignment) => {
        if (!assignment.submission) return;

        setSelectedFeedback({
            assignmentTitle: assignment.assignment_title,
            teacherGrade: assignment.submission.teacher_grade,
            teacherFeedback: assignment.submission.teacher_feedback || null,
            revisionDescription: assignment.submission.revision_description || null,
            revisionRequirements: assignment.submission.revision_requirements || [], // **核心修正：確保從正確欄位讀取**
            submissionStatus: assignment.submission.submission_status,
            gradedAt: assignment.submission.graded_at,
            revisionRequestedAt: assignment.submission.revision_requested_at || null
        });
        setFeedbackModalOpen(true);
    };

    const handleLessonClick = (lesson, assignmentId) => {
        // **新增：更嚴格的檢查**
        if (!lesson || !lesson.id) {
            console.error("無法開啟作業，因為關聯的課文資料不完整:", lesson);
            alert("無法開啟此作業，可能相關的課文已被移除。請聯繫老師。");
            return;
        }

        // 核心改動：將 assignment_id 加入 URL
        const baseUrl = (() => {
            switch (lesson.activity_type) {
                case 'listening_cloze':
                    return createPageUrl(`ListeningCloze?lesson_id=${lesson.id}`);
                case 'sentence_making':
                    return createPageUrl(`SentenceMaking?lesson_id=${lesson.id}`);
                case 'speaking_practice':
                    return createPageUrl(`SpeakingPractice?lesson_id=${lesson.id}`);
                case 'reading_assessment':
                default:
                    return createPageUrl(`StudentPractice?lesson_id=${lesson.id}`);
            }
        })();

        // 將 assignment_id 作為參數附加
        window.location.href = `${baseUrl}&assignment_id=${assignmentId}`;
    };

    const getActivityIcon = (activityType) => {
        switch (activityType) {
            case 'reading_assessment': return <FileText className="w-4 h-4" />;
            case 'listening_cloze': return <Headphones className="w-4 h-4" />;
            case 'sentence_making': return <Edit2 className="w-4 h-4" />;
            case 'speaking_practice': return <Mic className="w-4 h-4" />;
            default: return <BookOpen className="w-4 h-4" />;
        }
    };

    const getActivityLabel = (activityType) => {
        switch (activityType) {
            case 'reading_assessment': return '朗讀練習';
            case 'listening_cloze': return '聽力克漏字';
            case 'sentence_making': return '造句活動';
            case 'speaking_practice': return '錄音集';
            default: return '活動';
        }
    };


    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600 font-medium">載入作業中...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="text-center bg-white rounded-lg shadow-md p-8">
                    <p className="text-red-600 font-bold text-lg mb-2">錯誤！</p>
                    <p className="text-gray-700">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
            <div className="max-w-4xl mx-auto px-4 py-8">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-10"
                >
                    <div className="inline-flex items-center gap-4 bg-white/80 backdrop-blur-sm px-6 py-3 rounded-2xl shadow-lg border border-white/20 mb-6">
                        <GraduationCap className="w-8 h-8 text-violet-600" />
                        <div className="text-left">
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
                                {studentClass ? `${studentClass.class_name} - 我的作業` : '我的作業'}
                            </h1>
                            {user && <p className="text-sm text-gray-700 font-medium mt-1">學生: {user.full_name}</p>}
                        </div>
                        <Sparkles className="w-6 h-6 text-amber-500" />
                    </div>
                </motion.div>

                {assignments.length > 0 ? (
                    <div className="space-y-4">
                        {assignments.map((assignment, index) => (
                            <motion.div
                                key={`${assignment.assignment_id}-${assignment.id}`}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                                className="bg-white/90 backdrop-blur-md rounded-2xl shadow-lg border border-white/30 overflow-hidden"
                            >
                                <div className="p-6 flex flex-col gap-4">
                                    {/* Section 1: Header */}
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <div className="flex items-center gap-1.5 text-sm font-semibold text-violet-700">
                                                    {getActivityIcon(assignment.activity_type)}
                                                    <span>{getActivityLabel(assignment.activity_type)}</span>
                                                </div>
                                                <h4 className="font-bold text-gray-900 text-lg">
                                                    {assignment.assignment_title}
                                                </h4>
                                            </div>
                                            <p className="text-sm text-gray-600 ml-1">
                                                {assignment.assignment_description || assignment.lesson?.title}
                                            </p>
                                        </div>
                                        <div className="flex-shrink-0">
                                            {assignment.submission?.submission_status === 'needs_revision' ? (
                                                <Badge className="bg-orange-100 text-orange-800 border-orange-200">
                                                    <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />
                                                    需要訂正
                                                </Badge>
                                            ) : assignment.isCompleted ? (
                                                 <Badge className="bg-green-100 text-green-800 border-green-200">
                                                    <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                                                    已完成
                                                </Badge>
                                            ) : (
                                                <Badge variant="outline" className="bg-yellow-50 text-yellow-800 border-yellow-200">
                                                    待完成
                                                </Badge>
                                            )}
                                        </div>
                                    </div>

                                    {/* Section 2: Progress & Score */}
                                    <div className="bg-gray-50/70 rounded-lg p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {/* Progress Area */}
                                        <div className="flex flex-col gap-2">
                                            <div className="flex justify-between items-center text-sm">
                                                <span className="font-medium text-gray-700">完成進度</span>
                                                <span className="font-semibold text-blue-600">{assignment.bestScore.toFixed(0)}%</span>
                                            </div>
                                            <Progress value={assignment.bestScore} className="h-2" />
                                        </div>

                                        {/* Score & Feedback Area */}
                                        {assignment.submission && (assignment.submission.submission_status === 'graded' || assignment.submission.submission_status === 'needs_revision') && (
                                            <div className="flex flex-col gap-2">
                                                <div className="flex justify-between items-center text-sm">
                                                    <div className="flex items-center gap-1.5 font-medium text-gray-700">
                                                         {assignment.submission.submission_status === 'needs_revision'
                                                            ? <AlertTriangle className="w-4 h-4 text-orange-500" />
                                                            : <Award className="w-4 h-4 text-blue-500" />
                                                         }
                                                        <span>教師評分</span>
                                                    </div>
                                                    <span className={`font-semibold ${
                                                        assignment.submission.submission_status === 'needs_revision' ? 'text-orange-600' : 'text-blue-600'
                                                    }`}>
                                                        {assignment.submission.teacher_grade} 分
                                                    </span>
                                                </div>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => assignment.submission.submission_status === 'needs_revision'
                                                        ? handleViewRevisionRequirements(assignment)
                                                        : handleViewFeedback(assignment)
                                                    }
                                                    className={`w-full h-8 text-xs ${
                                                        assignment.submission.submission_status === 'needs_revision'
                                                        ? 'bg-orange-50 border-orange-200 text-orange-700 hover:bg-orange-100'
                                                        : 'bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100'
                                                    }`}
                                                >
                                                    <MessageSquare className="w-3 h-3 mr-1.5" />
                                                    {assignment.submission.submission_status === 'needs_revision' ? '查看訂正要求' : '查看老師評語'}
                                                </Button>
                                            </div>
                                        )}
                                    </div>

                                    {/* Section 3: Details & Action */}
                                    <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mt-2">
                                        <div className="flex items-center gap-4 text-xs text-gray-500">
                                            <div className="flex items-center gap-1.5">
                                                <Calendar className="w-3.5 h-3.5" />
                                                <span>指派: {new Date(assignment.assigned_date).toLocaleDateString()}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <Clock className="w-3.5 h-3.5" />
                                                <span className="text-red-600 font-medium">截止: {new Date(assignment.due_date).toLocaleDateString()}</span>
                                            </div>
                                            <Badge variant="outline" className="text-xs text-gray-400 bg-gray-50/50 border-gray-200 font-mono hover:bg-gray-100">
                                                ID: {assignment.assignment_id.slice(-8)}
                                            </Badge>
                                        </div>

                                        <Button
                                            onClick={() => handleLessonClick(assignment.lesson, assignment.assignment_id)}
                                            className="w-full sm:w-auto bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white font-semibold py-2 px-6 rounded-lg shadow-md hover:shadow-xl transition-all flex items-center gap-2"
                                        >
                                            <RefreshCw className="w-4 h-4" />
                                            {assignment.isCompleted ? '再次練習' : '開始作業'}
                                        </Button>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                ) : (
                     <div className="text-center py-20">
                        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-white/20 p-12 max-w-lg mx-auto">
                            <div className="w-24 h-24 bg-gradient-to-br from-green-100 to-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
                                <CheckCircle2 className="w-12 h-12 text-green-600" />
                            </div>
                            <h3 className="text-2xl font-bold text-gray-900 mb-4">
                                恭喜你！目前沒有作業
                            </h3>
                            <p className="text-gray-600 text-lg">
                                你可以前往「課堂練習」自主學習，或等待老師指派新作業。
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* **修改：教師評語/訂正要求對話框** */}
            <Dialog open={feedbackModalOpen} onOpenChange={setFeedbackModalOpen}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            {selectedFeedback?.submissionStatus === 'needs_revision' ? (
                                <>
                                    <AlertTriangle className="w-5 h-5 text-orange-600" />
                                    訂正要求
                                </>
                            ) : (
                                <>
                                    <MessageSquare className="w-5 h-5 text-blue-600" />
                                    老師評語
                                </>
                            )}
                        </DialogTitle>
                    </DialogHeader>
                    {selectedFeedback && (
                        <div className="space-y-4">
                            <div className={`${selectedFeedback.submissionStatus === 'needs_revision' ? 'bg-orange-50' : 'bg-blue-50'} rounded-lg p-4`}>
                                <h4 className={`font-medium ${selectedFeedback.submissionStatus === 'needs_revision' ? 'text-orange-900' : 'text-blue-900'} mb-2`}>
                                    作業：{selectedFeedback.assignmentTitle}
                                </h4>
                                <div className={`flex items-center gap-4 text-sm ${selectedFeedback.submissionStatus === 'needs_revision' ? 'text-orange-700' : 'text-blue-700'}`}>
                                    <span className="flex items-center gap-1">
                                        <Award className="w-4 h-4" />
                                        教師評分：<span className="font-bold text-lg">{selectedFeedback.teacherGrade}</span> 分
                                    </span>
                                    {selectedFeedback.gradedAt && (
                                        <span>
                                            批改時間：{new Date(selectedFeedback.gradedAt).toLocaleString()}
                                        </span>
                                    )}
                                </div>
                            </div>

                            {selectedFeedback.submissionStatus === 'needs_revision' ? (
                                <>
                                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                                        <div className="flex items-center gap-2 mb-3">
                                            <AlertTriangle className="w-5 h-5 text-orange-600" />
                                            <span className="font-medium text-orange-900 text-lg">老師要求訂正</span>
                                        </div>
                                        <p className="text-orange-800 text-sm mb-3">請仔細閱讀下方的訂正要求，完成改進後重新提交作業。</p>
                                        
                                        {selectedFeedback.revisionDescription && (
                                            <div className="bg-white rounded border-l-4 border-l-orange-500 p-3 mb-3">
                                                <h5 className="font-medium text-gray-900 mb-2">整體訂正說明</h5>
                                                <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                                                    {selectedFeedback.revisionDescription}
                                                </p>
                                            </div>
                                        )}
                                    </div>

                                    {/* **核心修正：正確顯示具體訂正項目** */}
                                    {selectedFeedback.revisionRequirements && selectedFeedback.revisionRequirements.length > 0 && (
                                        <div>
                                            <h5 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                                                <ListChecks className="w-4 h-4 text-orange-600" />
                                                具體訂正項目
                                            </h5>
                                            <div className="space-y-3">
                                                {selectedFeedback.revisionRequirements.map((req, index) => (
                                                    <div key={req.id || index} className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <h6 className="font-medium text-orange-900">
                                                                {req.title || `訂正項目 ${index + 1}`}
                                                            </h6>
                                                            <Badge 
                                                                className={`text-xs ${
                                                                    req.priority === 'high' ? 'bg-red-100 text-red-800 border-red-300' :
                                                                    req.priority === 'medium' ? 'bg-yellow-100 text-yellow-800 border-yellow-300' :
                                                                    'bg-blue-100 text-blue-800 border-blue-300'
                                                                }`}
                                                            >
                                                                {req.priority === 'high' ? '🔴 重要' : req.priority === 'medium' ? '🟡 普通' : '🔵 輕微'}
                                                            </Badge>
                                                        </div>
                                                        {req.description && (
                                                            <p className="text-orange-800 text-sm leading-relaxed">
                                                                {req.description}
                                                            </p>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* **新增：如果沒有具體項目，顯示提示** */}
                                    {(!selectedFeedback.revisionRequirements || selectedFeedback.revisionRequirements.length === 0) && (
                                        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                            <div className="flex items-center gap-2 text-gray-600">
                                                <MessageSquare className="w-4 h-4" />
                                                <span className="text-sm">老師沒有設定具體訂正項目，請參考上方的整體說明。</span>
                                            </div>
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div>
                                    <h5 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                                        <MessageSquare className="w-4 h-4 text-gray-600" />
                                        老師的話
                                    </h5>
                                    <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-l-blue-500">
                                        <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                                            {selectedFeedback.teacherFeedback || '老師暫時沒有留下評語。'}
                                        </p>
                                    </div>
                                </div>
                            )}

                            <div className="pt-4 border-t">
                                <Button
                                    onClick={() => setFeedbackModalOpen(false)}
                                    className={`w-full ${
                                        selectedFeedback.submissionStatus === 'needs_revision' 
                                        ? 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600'
                                        : 'bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600'
                                    }`}
                                >
                                    {selectedFeedback.submissionStatus === 'needs_revision' ? '我明白了，去訂正' : '我知道了'}
                                </Button>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
