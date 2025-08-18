
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { StudentProgress } from '@/api/entities';
import { Lesson } from '@/api/entities';
import { User } from '@/api/entities';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowLeft, Trash2, TrendingUp } from 'lucide-react';
import ResultsDisplay from '../components/assessment/ResultsDisplay';
import { createPageUrl } from '@/utils';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export default function PracticeDetail() {
    const navigate = useNavigate();
    const [viewingAttempt, setViewingAttempt] = useState(null);
    const [allAttempts, setAllAttempts] = useState([]);
    const [lesson, setLesson] = useState(null);
    const [student, setStudent] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const id = urlParams.get('id');
        if (id) {
            loadData(id);
        } else {
            navigate(createPageUrl("TeacherDashboard"));
        }
    }, [navigate]);

    const loadData = async (id) => {
        setLoading(true);
        try {
            const progressData = await StudentProgress.filter({ id });
            if (progressData.length > 0) {
                const currentProgress = progressData[0];
                setViewingAttempt(currentProgress);
                
                const [lessonData, studentData, allAttemptsData] = await Promise.all([
                    Lesson.filter({ id: currentProgress.lesson_id }),
                    User.filter({ id: currentProgress.student_id }),
                    StudentProgress.filter({ 
                        lesson_id: currentProgress.lesson_id, 
                        student_id: currentProgress.student_id 
                    }, "-attempt_number")
                ]);

                if (lessonData.length > 0) setLesson(lessonData[0]);
                if (studentData.length > 0) {
                    setStudent(studentData[0]);
                } else {
                    setStudent({ full_name: `學生 (ID: ${currentProgress.student_id.substring(0,6)}...)` });
                }
                setAllAttempts(allAttemptsData);

            } else {
                navigate(createPageUrl("TeacherDashboard"));
            }
        } catch (error) {
            console.error("載入練習詳情失敗:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!viewingAttempt) return;
        try {
            await StudentProgress.delete(viewingAttempt.id);
            alert("刪除成功！");
            navigate(createPageUrl("TeacherDashboard"));
        } catch (error) {
            console.error("刪除失敗:", error);
            alert("刪除失敗，請重試");
        }
    };
    
    const getProgressChartData = () => {
        return allAttempts.map(attempt => ({
          attempt: `第${attempt.attempt_number}次`,
          wpm: attempt.words_per_minute,
          accuracy: attempt.accuracy_percentage
        })).reverse(); // Reverse to show from first to last attempt
    };

    if (loading) {
        return (
          <div className="p-6 min-h-screen flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        );
    }

    if (!viewingAttempt || !lesson || !student) {
        return <div className="p-6 text-center">找不到練習記錄</div>;
    }

    return (
        <div className="p-6 min-h-screen">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-4">
                        <Button variant="outline" size="icon" className="rounded-full" onClick={() => navigate(createPageUrl("TeacherDashboard"))}>
                            <ArrowLeft className="w-5 h-5" />
                        </Button>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">{lesson.title} - 練習詳情</h1>
                            <p className="text-gray-600">學生: {student.full_name}</p>
                        </div>
                    </div>
                    <AlertDialog>
                        <AlertDialogTrigger asChild>
                           <Button variant="destructive" className="gap-2"><Trash2 className="w-4 h-4"/> 刪除此筆記錄</Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                            <AlertDialogHeader>
                                <AlertDialogTitle>確定要刪除第 {viewingAttempt.attempt_number} 次的練習記錄嗎？</AlertDialogTitle>
                                <AlertDialogDescription>此操作無法復原。這將永久刪除此學生的練習記錄。</AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                                <AlertDialogCancel>取消</AlertDialogCancel>
                                <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">確定刪除</AlertDialogAction>
                            </AlertDialogFooter>
                        </AlertDialogContent>
                    </AlertDialog>
                </div>
                
                <div className="grid lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-6">
                        <ResultsDisplay session={viewingAttempt} targets={lesson} />
                        
                        <Card className="glass-effect border-0 shadow-lg">
                            <CardHeader>
                                <CardTitle>所有練習記錄 (共 {allAttempts.length} 次)</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-4">
                                {allAttempts.map((attempt) => (
                                  <div 
                                    key={attempt.id} 
                                    className={`p-4 rounded-lg cursor-pointer hover:bg-teal-50 hover:shadow-md transition-all duration-200 ${viewingAttempt.id === attempt.id ? 'bg-teal-100 border-2 border-teal-300' : 'bg-gray-50'}`}
                                    onClick={() => setViewingAttempt(attempt)}
                                  >
                                    <div className="flex justify-between items-center">
                                      <h4 className="font-semibold">第 {attempt.attempt_number} 次</h4>
                                      <div className="flex gap-4 text-sm">
                                        <span>正確率: {attempt.accuracy_percentage.toFixed(1)}%</span>
                                        <span>語速: {attempt.words_per_minute} 字/分</span>
                                        <span>錯誤: {attempt.error_count} 字</span>
                                      </div>
                                    </div>
                                    <Progress value={attempt.accuracy_percentage} className="mt-2" />
                                  </div>
                                ))}
                              </div>
                            </CardContent>
                        </Card>
                    </div>
                    
                    <div className="space-y-6">
                         <Card className="glass-effect border-0 shadow-lg">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <TrendingUp className="w-5 h-5" />
                                    進步趨勢
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="h-48">
                                <ResponsiveContainer width="100%" height="100%">
                                  <LineChart data={getProgressChartData()}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="attempt" />
                                    <YAxis yAxisId="left" domain={[0, 'dataMax + 20']} />
                                    <YAxis yAxisId="right" orientation="right" domain={[0, 100]} />
                                    <Tooltip content={({ active, payload, label }) => {
                                      if (active && payload && payload.length) {
                                        // Find wpm and accuracy data from the payload
                                        const wpmData = payload.find(p => p.dataKey === 'wpm');
                                        const accuracyData = payload.find(p => p.dataKey === 'accuracy');
                                        return (
                                          <div className="p-2 bg-white border rounded-md shadow-lg">
                                            <p className="font-bold">{label}</p>
                                            <p className="text-blue-600">{`速度: ${wpmData?.value || 0} 字/分`}</p>
                                            <p className="text-green-600">{`正確率: ${accuracyData?.value || 0}%`}</p>
                                          </div>
                                        );
                                      }
                                      return null;
                                    }} />
                                    <Line yAxisId="left" type="monotone" dataKey="wpm" stroke="#0891b2" strokeWidth={2} name="速度 (字/分)"/>
                                    <Line yAxisId="right" type="monotone" dataKey="accuracy" stroke="#059669" strokeWidth={2} name="正確率 (%)"/>
                                  </LineChart>
                                </ResponsiveContainer>
                              </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
}
