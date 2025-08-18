import React, { useState, useEffect, useMemo } from 'react';
import { AssignmentSubmission } from '@/api/entities';
import { ClassStudent } from '@/api/entities';
import { StudentAssignment } from '@/api/entities';
import { StudentProgress } from '@/api/entities';
import { ActivityResult } from '@/api/entities';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { Play, Pause, Volume2, User, Clock, Target, MessageSquare, CheckCircle, XCircle, Edit, UserPlus, AlertCircle, CalendarIcon, Trash2, Save, Settings, BookOpen, Activity, Undo2, Send, Sparkles, Plus, CheckCircle2 } from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { aiGradingSuggestion } from '@/api/functions';

import UnifiedResultsDisplay from '../assessment/UnifiedResultsDisplay';

export default function GradingModal({ isOpen, onClose, assignment }) {
    const [allClassStudents, setAllClassStudents] = useState([]);
    const [assignedStudentEmails, setAssignedStudentEmails] = useState(new Set());
    const [submissions, setSubmissions] = useState([]);
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [studentProgress, setStudentProgress] = useState([]);
    const [loading, setLoading] = useState(false);
    const [assigningStudents, setAssigningStudents] = useState(new Set());
    
    // Grading states
    const [teacherGrade, setTeacherGrade] = useState('');
    const [teacherFeedback, setTeacherFeedback] = useState('');
    const [revisionItems, setRevisionItems] = useState([]);
    const [isSuggesting, setIsSuggesting] = useState(false);
    const [suggestionProgress, setSuggestionProgress] = useState('');
    
    // 提交和收回批改的載入狀態
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isRevoking, setIsRevoking] = useState(false);

    // **新增：訂正相關狀態**
    const [isRequestingRevision, setIsRequestingRevision] = useState(false);
    const [revisionDescription, setRevisionDescription] = useState('');
    const [revisionRequirements, setRevisionRequirements] = useState([]);

    // Assignment editing states
    const [isEditingAssignment, setIsEditingAssignment] = useState(false);
    const [editedAssignment, setEditedAssignment] = useState({
        title: '',
        description: '',
        due_date: null
    });
    const [savingAssignment, setSavingAssignment] = useState(false);

    const [isAssignmentInfoCollapsed, setIsAssignmentInfoCollapsed] = useState(false);
    const [currentSubmission, setCurrentSubmission] = useState(null);

    useEffect(() => {
        if (isOpen && assignment) {
            loadGradingData();
            setEditedAssignment({
                title: assignment.assignment_title || '',
                description: assignment.assignment_description || '',
                due_date: assignment.due_date ? new Date(assignment.due_date) : null
            });
            setIsAssignmentInfoCollapsed(false);
        }
    }, [isOpen, assignment]);

    const loadGradingData = async () => {
        setLoading(true);
        try {
            const [classStudents, assignmentRecords, assignmentSubmissions] = await Promise.all([
                ClassStudent.filter({ class_id: assignment.class_id }),
                StudentAssignment.filter({ assignment_id: assignment.assignment_id }),
                AssignmentSubmission.filter({ assignment_id: assignment.assignment_id })
            ]);
            
            setAllClassStudents(classStudents);
            const assignedEmails = new Set(assignmentRecords.map(record => record.student_email));
            setAssignedStudentEmails(assignedEmails);
            setSubmissions(assignmentSubmissions);
            
        } catch (err) {
            console.error("Failed to load grading data:", err);
        } finally {
            setLoading(false);
        }
    };
    
    const assignedAndEnrolledCount = useMemo(() => {
        if (!allClassStudents.length || !assignedStudentEmails.size) {
            return 0;
        }
        return allClassStudents.filter(student => assignedStudentEmails.has(student.email)).length;
    }, [allClassStudents, assignedStudentEmails]);

    const loadStudentProgress = async (studentEmail) => {
        try {
            const [activityResults, progressRecords] = await Promise.all([
                ActivityResult.filter({
                    lesson_id: assignment.lesson_id,
                    student_email: studentEmail,
                    assignment_id: assignment.assignment_id
                }, '-completed_at'),
                StudentProgress.filter({
                    lesson_id: assignment.lesson_id,
                    student_email: studentEmail,
                    assignment_id: assignment.assignment_id
                }, '-completed_at')
            ]);

            const combinedResults = activityResults.length > 0 ? activityResults : progressRecords;
            setStudentProgress(combinedResults);

        } catch (err) {
            console.error("Failed to load student progress:", err);
            setStudentProgress([]);
        }
    };

    const handleStudentSelect = async (student) => {
        if (!assignedStudentEmails.has(student.email)) return;
        
        setSelectedStudent(student);
        setIsAssignmentInfoCollapsed(true);
        await loadStudentProgress(student.email);
        
        const submission = submissions.find(s => s.student_email === student.email);
        setCurrentSubmission(submission || null);
        
        if (submission) {
            setTeacherGrade(submission.teacher_grade || '');
            setTeacherFeedback(submission.teacher_feedback || '');
            setRevisionItems(submission.revision_requests || []);
            
            if (submission.submission_status === 'needs_revision') {
                setIsRequestingRevision(true);
                setRevisionDescription(submission.revision_description || '');
                setRevisionRequirements(submission.revision_requirements || []);
            } else {
                setIsRequestingRevision(false);
                setRevisionDescription('');
                setRevisionRequirements([]);
            }
        } else {
            setTeacherGrade('');
            setTeacherFeedback('');
            setRevisionItems([]);
            setIsRequestingRevision(false);
            setRevisionDescription('');
            setRevisionRequirements([]);
        }
    };

    const handleAssignToStudent = async (student) => {
        setAssigningStudents(prev => new Set(prev).add(student.email));
        try {
            const assignmentData = {
                assignment_id: assignment.assignment_id,
                lesson_id: assignment.lesson_id,
                class_id: assignment.class_id,
                student_email: student.email,
                teacher_email: assignment.teacher_email,
                assignment_title: assignment.assignment_title,
                assignment_description: assignment.assignment_description || '',
                activity_type: assignment.activity_type,
                scheduled_dispatch_date: assignment.scheduled_dispatch_date || new Date().toISOString(),
                due_date: assignment.due_date,
                assigned_date: new Date().toISOString(),
                is_active: true,
            };
            await StudentAssignment.create(assignmentData);
            setAssignedStudentEmails(prev => new Set(prev).add(student.email));
        } catch (err) {
            console.error("Failed to assign homework to student:", err);
            alert(`補派作業失敗：${err.message}`);
        } finally {
            setAssigningStudents(prev => {
                const newSet = new Set(prev);
                newSet.delete(student.email);
                return newSet;
            });
        }
    };

    const handleUnassignStudent = async (student) => {
        if (!confirm(`確定要取消派發給 ${student.student_name} 的作業嗎？`)) return;
        
        try {
            const assignmentRecords = await StudentAssignment.filter({ 
                assignment_id: assignment.assignment_id,
                student_email: student.email
            });
            if (assignmentRecords.length > 0) {
                await StudentAssignment.delete(assignmentRecords[0].id);
                setAssignedStudentEmails(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(student.email);
                    return newSet;
                });
                if (selectedStudent?.email === student.email) {
                    setSelectedStudent(null);
                }
                alert(`已取消派發給 ${student.student_name} 的作業`);
            }
        } catch (err) {
            console.error("Failed to unassign homework:", err);
            alert(`取消派發失敗：${err.message}`);
        }
    };

    const handleSaveAssignment = async () => {
        setSavingAssignment(true);
        try {
            const assignmentRecords = await StudentAssignment.filter({ 
                assignment_id: assignment.assignment_id 
            });
            const updatePromises = assignmentRecords.map(record => 
                StudentAssignment.update(record.id, {
                    assignment_title: editedAssignment.title,
                    assignment_description: editedAssignment.description,
                    due_date: editedAssignment.due_date ? editedAssignment.due_date.toISOString() : assignment.due_date
                })
            );
            await Promise.all(updatePromises);
            assignment.assignment_title = editedAssignment.title;
            assignment.assignment_description = editedAssignment.description;
            assignment.due_date = editedAssignment.due_date ? editedAssignment.due_date.toISOString() : assignment.due_date;
            setIsEditingAssignment(false);
            alert('作業資訊已更新！');
        } catch (err) {
            console.error("Failed to update assignment:", err);
            alert(`更新失敗：${err.message}`);
        } finally {
            setSavingAssignment(false);
        }
    };

    const handleSubmitRevisionRequest = async () => {
        if (!selectedStudent || isSubmitting) return;
        setIsSubmitting(true);
        try {
            const submissionData = {
                assignment_id: assignment.assignment_id,
                student_id: selectedStudent.id,
                student_email: selectedStudent.email,
                student_name: selectedStudent.student_name,
                lesson_id: assignment.lesson_id,
                activity_type: assignment.activity_type,
                teacher_grade: parseFloat(teacherGrade) || 0,
                teacher_feedback: teacherFeedback,
                revision_requests: revisionItems,
                revision_description: revisionDescription,
                revision_requirements: revisionRequirements,
                submission_status: 'needs_revision',
                graded_at: new Date().toISOString(),
                graded_by: assignment.teacher_email,
                revision_requested_at: new Date().toISOString()
            };
            
            const updatedSubmission = currentSubmission 
                ? await AssignmentSubmission.update(currentSubmission.id, submissionData)
                : await AssignmentSubmission.create(submissionData);
            
            setCurrentSubmission(updatedSubmission);
            await loadGradingData();
            alert('訂正要求已提交給學生！');
        } catch (err) {
            console.error("Failed to submit revision request:", err);
            alert('提交訂正要求失敗，請重試。');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleGradeSubmit = async () => {
        if (!selectedStudent || isSubmitting) return;
        setIsSubmitting(true);
        try {
            const submissionData = {
                assignment_id: assignment.assignment_id,
                student_id: selectedStudent.id,
                student_email: selectedStudent.email,
                student_name: selectedStudent.student_name,
                lesson_id: assignment.lesson_id,
                activity_type: assignment.activity_type,
                teacher_grade: parseFloat(teacherGrade) || 0,
                teacher_feedback: teacherFeedback,
                revision_requests: revisionItems,
                submission_status: 'graded',
                graded_at: new Date().toISOString(),
                graded_by: assignment.teacher_email,
                revision_description: null,
                revision_requirements: [],
                revision_requested_at: null
            };
            
            const updatedSubmission = currentSubmission 
                ? await AssignmentSubmission.update(currentSubmission.id, submissionData)
                : await AssignmentSubmission.create(submissionData);

            setCurrentSubmission(updatedSubmission);
            await loadGradingData();
            alert('批改完成！');
        } catch (err) {
            console.error("Failed to submit grade:", err);
            alert('批改失敗，請重試。');
        } finally {
            setIsSubmitting(false);
        }
    };
    
    const handleRevokeGrading = async () => {
        if (!currentSubmission || isRevoking) return;
        if (!confirm('確定要收回這份作業的批改嗎？收回後可以重新編輯。')) return;
        setIsRevoking(true);
        try {
            const hasProgress = studentProgress.length > 0;
            const newStatus = hasProgress ? 'submitted' : 'in_progress';
            const updatedSubmission = await AssignmentSubmission.update(currentSubmission.id, {
                submission_status: newStatus,
                revision_description: null,
                revision_requirements: [],
                revision_requested_at: null,
                graded_at: null,
                graded_by: null
            });
            setCurrentSubmission(updatedSubmission);
            await loadGradingData();
            alert('批改已收回。您可以繼續編輯原有的評分和評語。');
        } catch (err) {
            console.error("Failed to revoke grading:", err);
            alert('收回批改失敗，請重試。');
        } finally {
            setIsRevoking(false);
        }
    };

    const addRevisionRequirement = () => {
        setRevisionRequirements([...revisionRequirements, { id: Date.now(), title: '', description: '', priority: 'medium' }]);
    };

    const removeRevisionRequirement = (id) => {
        setRevisionRequirements(revisionRequirements.filter(req => req.id !== id));
    };

    const updateRevisionRequirement = (id, field, value) => {
        setRevisionRequirements(revisionRequirements.map(req => req.id === id ? { ...req, [field]: value } : req));
    };

    const handleGetAISuggestion = async () => {
        if (!selectedStudent || studentProgress.length === 0) {
            alert("學生尚未提交任何練習，無法產生建議。");
            return;
        }
        setIsSuggesting(true);
        setSuggestionProgress('正在分析學生表現...');
        setTeacherGrade('');
        setTeacherFeedback('');
        setRevisionDescription('');
        try {
            setTimeout(() => setSuggestionProgress('正在生成評分建議...'), 1000);
            setTimeout(() => setSuggestionProgress('正在撰寫評語...'), 2000);
            const { data: suggestion } = await aiGradingSuggestion({
                assignment: {
                    assignment_title: assignment.assignment_title,
                    activity_type: assignment.activity_type,
                    assignment_description: assignment.assignment_description,
                    lesson_content: assignment.activity_type === 'reading_assessment' ? assignment.lesson?.content : undefined
                },
                studentProgress: studentProgress,
                studentName: selectedStudent.student_name,
                studentEmail: selectedStudent.email,
            });
            if (suggestion.suggested_grade !== undefined) {
                let currentGrade = 0;
                const targetGrade = Math.min(100, Math.max(0, Math.round(parseFloat(suggestion.suggested_grade))));
                const gradeInterval = setInterval(() => {
                    currentGrade += Math.ceil(targetGrade / 20);
                    if (currentGrade >= targetGrade) {
                        currentGrade = targetGrade;
                        clearInterval(gradeInterval);
                    }
                    setTeacherGrade(String(currentGrade));
                }, 100);
            }
            if (suggestion.suggested_feedback) {
                let currentText = '';
                const fullText = suggestion.suggested_feedback;
                let charIndex = 0;
                const typeInterval = setInterval(() => {
                    if (charIndex < fullText.length) {
                        currentText += fullText[charIndex];
                        if (isRequestingRevision) {
                            setRevisionDescription(currentText);
                        } else {
                            setTeacherFeedback(currentText);
                        }
                        charIndex++;
                    } else {
                        clearInterval(typeInterval);
                    }
                }, 30);
            }
            setSuggestionProgress('AI 建議生成完成！');
            setTimeout(() => setSuggestionProgress(''), 2000);
        } catch (err) {
            console.error("Failed to get AI grading suggestion:", err);
            alert("無法生成 AI 批改建議，請稍後再試。");
            setSuggestionProgress('');
        } finally {
            setIsSuggesting(false);
        }
    };

    const getSubmissionStatus = (studentEmail) => {
        if (!assignedStudentEmails.has(studentEmail)) {
            return { status: 'not_assigned', label: '未指派', color: 'bg-gray-100 text-gray-600 border-gray-300' };
        }
        const submission = submissions.find(s => s.student_email === studentEmail);
        const hasProgress = studentProgress.some(p => p.student_email === studentEmail && p.assignment_id === assignment.assignment_id);
        if (!submission && !hasProgress) return { status: 'not_started', label: '待完成', color: 'bg-yellow-100 text-yellow-700 border-yellow-300' };
        if (submission?.submission_status === 'needs_revision') return { status: 'needs_revision', label: '待訂正', color: 'bg-red-100 text-red-700 border-red-300' };
        if (submission?.submission_status === 'graded') return { status: 'graded', label: '已批改', color: 'bg-green-100 text-green-700 border-green-300' };
        if (!submission && hasProgress) return { status: 'submitted', label: '待批改', color: 'bg-blue-100 text-blue-700 border-blue-300' };
        if (submission && submission.submission_status === 'in_progress') return { status: 'submitted', label: '待批改', color: 'bg-blue-100 text-blue-700 border-blue-300' };
        return { status: 'submitted', label: '待批改', color: 'bg-blue-100 text-blue-700 border-blue-300' };
    };

    const hasStudentStarted = (studentEmail) => {
        const submission = submissions.find(s => s.student_email === studentEmail);
        const hasActivityResults = studentProgress.some(p => p.student_email === studentEmail && p.assignment_id === assignment.assignment_id);
        return !!submission || hasActivityResults;
    };

    const getActivityTypeLabel = (activityType) => {
        const types = {
            'reading_assessment': '朗讀練習',
            'speaking_practice': '錄音集',
            'speaking_scenario': '口說集',
            'listening_cloze': '聽力克漏字',
            'sentence_making': '造句活動'
        };
        return types[activityType] || '未知類型';
    };

    if (!isOpen) return null;

    const isGraded = currentSubmission?.submission_status === 'graded';
    const isRevisionRequested = currentSubmission?.submission_status === 'needs_revision';

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-7xl w-[95vw] h-[95vh] max-h-[95vh] flex flex-col p-0">
                <DialogHeader className="p-6 border-b bg-gradient-to-r from-blue-500 to-indigo-500 text-white">
                    <DialogTitle className="text-2xl font-bold mb-3">
                        批改作業：{assignment.assignment_title}
                    </DialogTitle>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm">
                        <Badge variant="secondary" className="bg-white/20 text-white border-white/30"><BookOpen className="w-3.5 h-3.5 mr-1.5" />課文: {assignment.lesson?.title || 'N/A'}</Badge>
                        <Badge variant="secondary" className="bg-white/20 text-white border-white/30"><Activity className="w-3.5 h-3.5 mr-1.5" />類型: {getActivityTypeLabel(assignment.activity_type)}</Badge>
                        <Badge variant="secondary" className="bg-white/20 text-white border-white/30"><CalendarIcon className="w-3.5 h-3.5 mr-1.5" />截止: {format(new Date(assignment.due_date), 'yyyy-MM-dd HH:mm', { locale: zhCN })}</Badge>
                        <Badge variant="secondary" className="bg-white/20 text-white border-white/30 font-mono text-xs">ID: {assignment.assignment_id.slice(-8)}</Badge>
                    </div>
                </DialogHeader>
                
                <div className="flex-1 flex overflow-hidden">
                    {/* Left side: Assignment Info Editor */}
                    {!isAssignmentInfoCollapsed && (
                        <div className="w-64 border-r bg-gray-50 overflow-y-auto flex-shrink-0">
                            <div className="p-4">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="font-semibold text-gray-900">作業資訊</h3>
                                    <div className="flex gap-1">
                                        <Button size="sm" variant="outline" onClick={() => setIsEditingAssignment(!isEditingAssignment)} className="h-7 px-2 text-xs"><Settings className="w-3 h-3 mr-1" />{isEditingAssignment ? '取消' : '編輯'}</Button>
                                        <Button size="sm" variant="ghost" onClick={() => setIsAssignmentInfoCollapsed(true)} className="h-7 px-2 text-xs" title="收起">✕</Button>
                                    </div>
                                </div>
                                {isEditingAssignment ? (
                                    <div className="space-y-3">
                                        <div>
                                            <label className="block text-xs font-medium text-gray-700 mb-1">作業標題</label>
                                            <Input value={editedAssignment.title} onChange={(e) => setEditedAssignment({ ...editedAssignment, title: e.target.value })} placeholder="請輸入作業標題" className="text-xs h-8" />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-700 mb-1">作業說明</label>
                                            <Textarea value={editedAssignment.description} onChange={(e) => setEditedAssignment({ ...editedAssignment, description: e.target.value })} placeholder="請輸入作業說明" rows={2} className="text-xs" />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-gray-700 mb-1">截止時間</label>
                                            <Popover>
                                                <PopoverTrigger asChild>
                                                    <Button variant="outline" className="w-full justify-start text-left font-normal text-xs h-8"><CalendarIcon className="mr-1 h-3 w-3" />{editedAssignment.due_date ? format(editedAssignment.due_date, "MM-dd HH:mm") : <span>選擇日期</span>}</Button>
                                                </PopoverTrigger>
                                                <PopoverContent className="w-auto p-0"><Calendar mode="single" selected={editedAssignment.due_date} onSelect={(date) => setEditedAssignment({ ...editedAssignment, due_date: date })} initialFocus /></PopoverContent>
                                            </Popover>
                                        </div>
                                        <Button onClick={handleSaveAssignment} disabled={savingAssignment} className="w-full bg-blue-600 hover:bg-blue-700 text-xs h-8"><Save className="w-3 h-3 mr-1" />{savingAssignment ? '儲存中...' : '儲存變更'}</Button>
                                    </div>
                                ) : (
                                    <div className="space-y-3 text-xs">
                                        <div><p className="text-gray-500 mb-1">標題</p><p className="font-medium text-sm">{assignment.assignment_title}</p></div>
                                        <div><p className="text-gray-500 mb-1">說明</p><p className="text-gray-700 text-sm">{assignment.assignment_description || '無說明'}</p></div>
                                        <div><p className="text-gray-500 mb-1">截止時間</p><p className="font-medium text-red-600 text-sm">{format(new Date(assignment.due_date), 'MM-dd HH:mm', { locale: zhCN })}</p></div>
                                        <div><p className="text-gray-500 mb-1">派發日期</p><p className="font-medium text-sm">{format(new Date(assignment.assigned_date), 'MM-dd HH:mm', { locale: zhCN })}</p></div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                    {isAssignmentInfoCollapsed && (
                        <div className="w-12 border-r bg-gray-50 flex flex-col items-center py-4">
                            <Button size="sm" variant="ghost" onClick={() => setIsAssignmentInfoCollapsed(false)} className="h-8 w-8 p-0 mb-2" title="展開作業資訊"><Settings className="w-4 h-4" /></Button>
                        </div>
                    )}
                    {/* Middle: Student List */}
                    <div className={`${isAssignmentInfoCollapsed ? 'w-80' : 'w-72'} border-r bg-gray-50 overflow-y-auto flex-shrink-0`}>
                        <div className="p-4">
                            <h3 className="font-semibold text-gray-900 mb-2">班級學生名單</h3>
                            <p className="text-xs text-gray-600 mb-4">共 {allClassStudents.length} 位學生 （已指派 {assignedAndEnrolledCount} 位）</p>
                            <div className="space-y-2">
                                {allClassStudents.map(student => {
                                    const isAssigned = assignedStudentEmails.has(student.email);
                                    const statusInfo = getSubmissionStatus(student.email);
                                    const isAssigning = assigningStudents.has(student.email);
                                    const studentStarted = hasStudentStarted(student.email);
                                    return (
                                        <Card key={student.id} className={`transition-all ${isAssigned && selectedStudent?.id === student.id ? 'ring-2 ring-blue-500 bg-blue-50' : 'bg-white'} ${isAssigned ? 'hover:shadow-md cursor-pointer' : 'opacity-75'}`} onClick={() => isAssigned && handleStudentSelect(student)}>
                                            <CardContent className="p-3">
                                                <div className="flex justify-between items-center">
                                                    <div className="flex-1 min-w-0"><p className="font-medium text-gray-900 text-sm truncate">{student.student_name}</p><p className="text-xs text-gray-500 truncate">{student.email}</p></div>
                                                    <div className="flex flex-col items-end gap-1 ml-2">
                                                        <Badge className={`text-xs border ${statusInfo.color} px-2 py-0.5`}>{statusInfo.label}</Badge>
                                                        <div className="flex gap-1">
                                                            {!isAssigned ? (<Button size="sm" variant="outline" className="text-xs h-6 px-2" onClick={(e) => { e.stopPropagation(); handleAssignToStudent(student); }} disabled={isAssigning}>{isAssigning ? <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin" /> : <><UserPlus className="w-3 h-3 mr-1" />補派</>}</Button>) : (!studentStarted && (<Button size="sm" variant="destructive" className="text-xs h-6 px-2" onClick={(e) => { e.stopPropagation(); handleUnassignStudent(student); }}><Trash2 className="w-3 h-3 mr-1" />取消</Button>))}
                                                        </div>
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                    {/* Right side: Grading Area */}
                    <div className="flex-1 overflow-y-auto">
                        {selectedStudent ? (
                            <div className="p-6">
                                <div className="mb-6">
                                    <h3 className="text-lg font-bold text-gray-900 mb-2">批改 {selectedStudent.student_name} 的作業</h3>
                                    <div className="bg-gray-50 rounded-lg p-4 mb-6">
                                        <div className="mb-4">
                                            <label className="block text-sm font-medium text-gray-700 mb-2">選擇批改方式</label>
                                            <div className="flex gap-4">
                                                <Button variant={!isRequestingRevision ? "default" : "outline"} onClick={() => setIsRequestingRevision(false)} disabled={isGraded || isSubmitting || isRevoking} className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4" />完成批改</Button>
                                                <Button variant={isRequestingRevision ? "default" : "outline"} onClick={() => setIsRequestingRevision(true)} disabled={isGraded || isSubmitting || isRevoking} className="flex items-center gap-2 bg-orange-600 hover:bg-orange-700 border-orange-600 text-white"><Edit className="w-4 h-4" />要求訂正</Button>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">教師評分 (0-100)</label>
                                                <div className="relative">
                                                    <Input type="number" min="0" max="100" value={teacherGrade} onChange={(e) => setTeacherGrade(e.target.value)} placeholder={isSuggesting ? "AI 正在計算分數..." : "請輸入分數"} disabled={isGraded || isSuggesting || isSubmitting || isRevoking} className={`${isSuggesting ? "bg-blue-50 border-blue-200" : ""} ${(isSubmitting || isRevoking || isGraded) ? "bg-gray-100 border-gray-300" : ""}`} />
                                                    {(isSuggesting || isSubmitting || isRevoking) && (<div className="absolute inset-y-0 right-0 pr-3 flex items-center"><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div></div>)}
                                                </div>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">批改狀態</label>
                                                <div className="p-2 bg-white border border-gray-200 rounded-md text-sm">{isRevisionRequested ? <span className="text-orange-600 font-medium">等待學生訂正</span> : isGraded ? <span className="text-green-600 font-medium">批改完成</span> : <span className="text-gray-600">進行中</span>}</div>
                                            </div>
                                        </div>
                                        <div className="mt-4">
                                            <label className="block text-sm font-medium text-gray-700 mb-1">{isRequestingRevision ? '訂正說明' : '教師評語'}{suggestionProgress && <span className="ml-2 text-xs text-blue-600 font-medium">{suggestionProgress}</span>}{(isSubmitting || isRevoking) && <span className="ml-2 text-xs text-gray-600 font-medium">{isSubmitting ? '正在提交批改...' : '正在收回批改...'}</span>}</label>
                                            <div className="relative">
                                                <Textarea value={isRequestingRevision ? revisionDescription : teacherFeedback} onChange={(e) => isRequestingRevision ? setRevisionDescription(e.target.value) : setTeacherFeedback(e.target.value)} placeholder={isGraded || isRevisionRequested ? "此作業已批改，如需修改請先收回。" : isRequestingRevision ? "請說明需要學生訂正的地方..." : isSuggesting ? "AI 正在撰寫評語..." : isSubmitting ? "正在提交批改..." : isRevoking ? "正在收回批改..." : "請輸入對學生的評語和建議..."} rows={4} disabled={isGraded || isRevisionRequested || isSuggesting || isSubmitting || isRevoking} className={`${isSuggesting ? "bg-blue-50 border-blue-200" : ""} ${(isSubmitting || isRevoking || isGraded || isRevisionRequested) ? "bg-gray-100 border-gray-300" : ""} ${isSuggesting && (teacherFeedback || revisionDescription) ? "animate-pulse" : ""}`} />
                                                {(isSuggesting || isSubmitting || isRevoking) && (<div className="absolute top-2 right-2">{isSuggesting ? <div className="flex items-center gap-1 text-blue-600"><div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div><div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div><div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div></div> : <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>}</div>)}
                                            </div>
                                        </div>
                                        {isRequestingRevision && !isGraded && (
                                            <div className="mt-4">
                                                <div className="flex justify-between items-center mb-2">
                                                    <label className="block text-sm font-medium text-gray-700">具體訂正項目</label>
                                                    <Button onClick={addRevisionRequirement} size="sm" variant="outline" className="text-orange-600 border-orange-600 hover:bg-orange-50" disabled={isSubmitting || isRevoking}><Plus className="w-4 h-4 mr-1" />添加項目</Button>
                                                </div>
                                                <div className="space-y-3">
                                                    {revisionRequirements.map((req) => (
                                                        <div key={req.id} className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                                                            <div className="flex justify-between items-start mb-2">
                                                                <Input placeholder="訂正項目標題" value={req.title} onChange={(e) => updateRevisionRequirement(req.id, 'title', e.target.value)} className="flex-1 mr-2" disabled={isSubmitting || isRevoking} />
                                                                <Select value={req.priority} onValueChange={(value) => updateRevisionRequirement(req.id, 'priority', value)} disabled={isSubmitting || isRevoking}>
                                                                    <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                                                                    <SelectContent><SelectItem value="high">重要</SelectItem><SelectItem value="medium">普通</SelectItem><SelectItem value="low">輕微</SelectItem></SelectContent>
                                                                </Select>
                                                                <Button onClick={() => removeRevisionRequirement(req.id)} size="sm" variant="ghost" className="ml-2 text-red-500 hover:text-red-700" disabled={isSubmitting || isRevoking}><Trash2 className="w-4 h-4" /></Button>
                                                            </div>
                                                            <Textarea placeholder="具體說明需要改進的地方..." value={req.description} onChange={(e) => updateRevisionRequirement(req.id, 'description', e.target.value)} rows={2} className="w-full" disabled={isSubmitting || isRevoking} />
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        <div className="flex justify-end mt-4 gap-2">
                                            <Button variant="outline" onClick={handleGetAISuggestion} disabled={isGraded || isRevisionRequested || isSuggesting || isSubmitting || isRevoking || !selectedStudent || studentProgress.length === 0} className={`transition-all duration-200 ${isSuggesting ? "bg-blue-50 border-blue-200" : ""}`}>{isSuggesting ? <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>生成建議中...</> : <><Sparkles className="w-4 h-4 mr-2" />AI 批改建議</>}</Button>
                                            {isGraded || isRevisionRequested ? <Button onClick={handleRevokeGrading} variant="destructive" disabled={isSuggesting || isSubmitting || isRevoking} className={`transition-all duration-200 ${isRevoking ? "opacity-75" : ""}`}>{isRevoking ? <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>收回中...</> : <><Undo2 className="w-4 h-4 mr-2" />收回批改</>}</Button> : <> {isRequestingRevision ? <Button onClick={handleSubmitRevisionRequest} className="bg-orange-600 hover:bg-orange-700 transition-all duration-200" disabled={isSuggesting || isSubmitting || isRevoking}>{isSubmitting ? <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>提交中...</> : <><Send className="w-4 h-4 mr-2" />要求學生訂正</>}</Button> : <Button onClick={handleGradeSubmit} className={`bg-blue-600 hover:bg-blue-700 transition-all duration-200 ${isSubmitting ? "opacity-75" : ""}`} disabled={isSuggesting || isSubmitting || isRevoking}>{isSubmitting ? <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>提交中...</> : <><Send className="w-4 h-4 mr-2" />完成批改</>}</Button>}</>}
                                        </div>
                                    </div>
                                    <div className="space-y-4">
                                        {studentProgress.length > 0 ? studentProgress.map((progress, index) => (<Card key={progress.id} className="border border-gray-200"><CardHeader><CardTitle className="text-base flex items-center justify-between"><div className="flex items-center gap-3"><span>第 {progress.attempt_number} 次練習</span><Badge variant="outline" className="bg-blue-50 text-blue-700">{format(new Date(progress.completed_at || progress.created_date), 'MM-dd HH:mm', { locale: zhCN })}</Badge>{progress.percentage_score !== undefined && <Badge className={progress.percentage_score >= 90 ? 'bg-green-100 text-green-800' : progress.percentage_score >= 70 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}>{progress.percentage_score.toFixed(1)}%</Badge>}</div><div className="flex items-center gap-2"><Checkbox id={`revision-${progress.id}`} checked={revisionItems.some(item => item.item_index === index)} onCheckedChange={(checked) => { if (checked) { setRevisionItems([...revisionItems, { item_index: index, reason: '', suggestion: '', is_resolved: false }]); } else { setRevisionItems(revisionItems.filter(item => item.item_index !== index)); } }} disabled={isGraded || isRevisionRequested || isSubmitting || isRevoking} /><label htmlFor={`revision-${progress.id}`} className="text-sm text-gray-600">打回訂正</label></div></CardTitle></CardHeader><CardContent><UnifiedResultsDisplay session={{...progress, audio_url: progress.audio_url, transcribed_text: progress.transcribed_text, punctuated_transcribed_text: progress.punctuated_transcribed_text, detailed_feedback: progress.detailed_feedback, annotated_segments: progress.annotated_segments, percentage_score: progress.percentage_score, words_per_minute: progress.words_per_minute, time_spent_seconds: progress.time_spent_seconds || progress.reading_time_seconds, answers: progress.answers, activity_type: assignment.activity_type }} targets={{ target_wpm: 230, target_accuracy: 85, set_by_teacher: true }} activityType={assignment.activity_type} />{assignment.activity_type === 'reading_assessment' && assignment.lesson?.content && (<Card className="mt-4 bg-blue-50 border-blue-200"><CardHeader><CardTitle className="text-sm flex items-center gap-2"><BookOpen className="w-4 h-4 text-blue-600" />原文對照</CardTitle></CardHeader><CardContent><div className="p-3 bg-white rounded border-l-4 border-l-blue-500"><p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{assignment.lesson.content}</p></div></CardContent></Card>)}</CardContent></Card>)) : (<div className="text-center py-8 text-gray-500"><User className="w-12 h-12 mx-auto mb-4 text-gray-300" /><p>此學生尚未完成作業</p></div>)}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-full text-gray-500">
                                <div className="text-center">
                                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4"><User className="w-8 h-8 text-gray-400" /></div>
                                    <h3 className="text-lg font-semibold text-gray-700 mb-2">選擇學生開始批改</h3>
                                    <p className="text-gray-500 mb-4">請從中間選擇一位已被指派作業的學生</p>
                                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
                                        <div className="flex items-center gap-2 text-blue-700 mb-2"><AlertCircle className="w-4 h-4" /><span className="font-medium">功能說明</span></div>
                                        <p className="text-sm text-blue-600">{isAssignmentInfoCollapsed ? '• 點擊左上角圖標可展開作業資訊\n• 選擇學生後開始批改作業' : '• 左側：編輯作業資訊\n• 中間：管理學生派發狀況\n• 右側：批改學生作業'}</p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}