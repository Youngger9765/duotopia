import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Play, CheckCircle2, Target, Award, User, Eye, History, PlusCircle } from "lucide-react";
import { ActivityResult } from "@/api/entities"; 
import { ClassStudent } from "@/api/entities";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";

export default function AttemptButtons({ lesson, studentId, onStartPractice, onViewResult, assignmentId }) {
    const [attempts, setAttempts] = useState([]);
    const [standards, setStandards] = useState(null);
    const [isTeacherSet, setIsTeacherSet] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (studentId) {
            loadData();
        }
    }, [lesson.id, studentId, assignmentId]);

    const loadData = async () => {
        setLoading(true);
        try {
            await Promise.all([loadAttempts(), loadStandards()]);
        } catch (error) {
            console.error("Failed to load attempt data:", error);
        } finally {
            setLoading(false);
        }
    };

    const loadAttempts = async () => {
        try {
            const filters = {
                student_email: studentId,
                lesson_id: lesson.id,
                activity_type: 'reading_assessment'
            };

            if (assignmentId) {
                filters.assignment_id = assignmentId;
            } else {
                filters.assignment_id = null;
            }
            
            const progressData = await ActivityResult.filter(filters, "attempt_number");
            
            setAttempts(Array.isArray(progressData) ? progressData : []);
            console.log(`[AttemptButtons] Loaded ${progressData.length} attempts for assignmentId: ${assignmentId || '自主練習'}`);
        } catch (error) {
            console.error("Failed to load attempts:", error);
            setAttempts([]);
        }
    };

    const loadStandards = async () => {
        try {
            const allClassStudents = await ClassStudent.list();
            const studentsList = Array.isArray(allClassStudents) ? allClassStudents : [];
            
            const studentData = studentsList.find(
                s => s.email && s.email.trim().toLowerCase() === studentId.trim().toLowerCase()
            );

            if (studentData && (studentData.target_wpm || studentData.target_accuracy)) {
                setStandards({
                    target_wpm: studentData.target_wpm || lesson.target_wpm || 230,
                    target_accuracy: studentData.target_accuracy || 85
                });
                setIsTeacherSet(true);
            } else {
                setStandards({
                    target_wpm: lesson.target_wpm || 230,
                    target_accuracy: 85
                });
                setIsTeacherSet(false);
            }
        } catch (error) {
            console.error("Failed to load personal standards:", error);
            setStandards({
                target_wpm: lesson.target_wpm || 230,
                target_accuracy: 85
            });
            setIsTeacherSet(false);
        }
    };

    const hasAchieved = () => {
        const attemptsArray = Array.isArray(attempts) ? attempts : [];
        if (!standards) return false;
        return attemptsArray.some(attempt => 
            attempt.words_per_minute >= standards.target_wpm &&
            attempt.percentage_score >= standards.target_accuracy
        );
    };

    if (loading) {
        return <div className="text-center py-4">載入中...</div>;
    }

    return (
        <div className="space-y-6">
            {/* 個人朗讀目標 */}
            {standards && (
                <Card className="bg-gradient-to-r from-teal-50 to-blue-50 border-teal-200">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-teal-800">
                            <Target className="w-5 h-5" />
                            您的個人朗讀目標
                            {isTeacherSet && (
                                <Badge variant="default" className="bg-blue-600 text-white ml-2">
                                    <User className="w-3 h-3 mr-1" />
                                    老師指定
                                </Badge>
                            )}
                        </CardTitle>
                        {isTeacherSet && (
                            <p className="text-sm text-teal-700 mt-1">
                                此目標由老師專門為您設定
                            </p>
                        )}
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="text-center p-3 bg-white rounded-lg">
                                <div className="text-2xl font-bold text-teal-600">{standards.target_wpm}</div>
                                <div className="text-sm text-gray-600">字/分鐘</div>
                            </div>
                            <div className="text-center p-3 bg-white rounded-lg">
                                <div className="text-2xl font-bold text-teal-600">{standards.target_accuracy}%</div>
                                <div className="text-sm text-gray-600">正確率</div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
            
            {/* 練習記錄與開始按鈕 */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <History className="w-5 h-5" />
                        朗讀練習記錄
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {/* 過去的練習列表 */}
                    <div className="space-y-3 mb-6">
                        {attempts.length > 0 ? (
                            attempts.map(attempt => {
                                const isAchieved = standards && 
                                    attempt.words_per_minute >= standards.target_wpm &&
                                    attempt.percentage_score >= standards.target_accuracy;
                                
                                return (
                                    <div 
                                        key={attempt.id}
                                        onClick={() => onViewResult(attempt)}
                                        className={`flex justify-between items-center p-3 rounded-lg cursor-pointer transition-all ${isAchieved ? 'bg-green-100 hover:bg-green-200 border-l-4 border-green-500' : 'bg-gray-50 hover:bg-gray-100 border-l-4 border-gray-300'}`}
                                    >
                                        <div className="flex items-center gap-3">
                                            {isAchieved ? <CheckCircle2 className="w-5 h-5 text-green-600" /> : <Eye className="w-5 h-5 text-gray-500" />}
                                            <div>
                                                <p className="font-semibold text-gray-800">第 {attempt.attempt_number} 次練習</p>
                                                <p className="text-xs text-gray-500">{format(new Date(attempt.completed_at), "yyyy-MM-dd HH:mm", { locale: zhCN })}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-medium text-sm text-gray-700">{Math.round(attempt.words_per_minute)} 字/分</p>
                                            <p className="font-medium text-sm text-gray-700">{attempt.percentage_score.toFixed(1)}% 正確率</p>
                                        </div>
                                    </div>
                                );
                            })
                        ) : (
                            <p className="text-center text-gray-500 py-4">尚無練習記錄，開始您的第一次練習吧！</p>
                        )}
                    </div>

                    {/* 開始新練習區塊 */}
                    <div className="mt-4 pt-4 border-t">
                        {hasAchieved() && (
                            <div className="p-4 bg-green-50 rounded-lg border border-green-200 text-center">
                                <div className="flex items-center justify-center gap-2 text-green-800">
                                    <Award className="w-5 h-5" />
                                    <span className="font-medium">恭喜您已達成朗讀目標！</span>
                                </div>
                                <p className="text-sm text-green-600 mt-1">您也可以繼續練習，挑戰更高分！</p>
                            </div>
                        )}

                        <Button 
                            onClick={() => onStartPractice(attempts.length + 1)}
                            className="w-full gradient-bg text-white mt-4"
                            size="lg"
                        >
                            <PlusCircle className="w-5 h-5 mr-2" />
                            開始第 {attempts.length + 1} 次練習
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}