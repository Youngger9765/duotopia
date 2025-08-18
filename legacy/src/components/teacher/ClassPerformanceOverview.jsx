
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Class } from "@/api/entities";
import { ClassStudent } from "@/api/entities";
import { StudentProgress } from "@/api/entities";
import { Lesson } from "@/api/entities";
import { User } from "@/api/entities";
import { CheckCircle2, XCircle, Users, BookOpen, AlertCircle, X, Clock, Target, Calendar, BarChart3, Eye } from "lucide-react";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

import ResultsDisplay from "../assessment/ResultsDisplay";

export default function ClassPerformanceOverview({ allClasses, allCourses, mappings }) {
    const [selectedClass, setSelectedClass] = useState(null);
    const [students, setStudents] = useState([]);
    const [lessons, setLessons] = useState([]);
    const [progressData, setProgressData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [displayedLessons, setDisplayedLessons] = useState(5);
    
    // 新增：側欄狀態
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [selectedStudentData, setSelectedStudentData] = useState(null);
    const [selectedLessonData, setSelectedLessonData] = useState(null);
    const [studentProgressList, setStudentProgressList] = useState([]);
    const [selectedProgressDetail, setSelectedProgressDetail] = useState(null);

    useEffect(() => {
        if (selectedClass) {
            loadClassData();
        }
    }, [selectedClass, mappings]);

    const loadClassData = async () => {
        setLoading(true);
        try {
            console.log("開始載入班級數據，班級ID:", selectedClass.id);
            
            // 1. 載入班級學生
            const classStudents = await ClassStudent.filter({ class_id: selectedClass.id });
            const studentsArray = Array.isArray(classStudents) ? classStudents : [];
            console.log("載入班級學生:", studentsArray.length, "位");
            setStudents(studentsArray);

            // 2. 找到班級關聯的課程
            const classCourseIds = mappings
                .filter(m => m.class_id === selectedClass.id)
                .map(m => m.course_id);
            
            console.log("班級關聯課程ID:", classCourseIds);

            if (classCourseIds.length === 0) {
                console.log("此班級沒有關聯任何課程");
                setLessons([]);
                setProgressData([]);
                return;
            }

            // 3. 載入課程的所有課文
            let allLessons = [];
            try {
                if (classCourseIds.length === 1) {
                    allLessons = await Lesson.filter({ 
                        course_id: classCourseIds[0],
                        is_active: true 
                    }, "-created_date");
                } else {
                    const lessonPromises = classCourseIds.map(courseId => 
                        Lesson.filter({ course_id: courseId, is_active: true }, "-created_date")
                    );
                    const lessonArrays = await Promise.all(lessonPromises);
                    allLessons = lessonArrays.flat().sort((a, b) => new Date(b.created_date) - new Date(a.created_date));
                }
            } catch (error) {
                console.error("載入課文失敗:", error);
                allLessons = [];
            }
            
            console.log("載入課文數量:", allLessons.length);
            setLessons(Array.isArray(allLessons) ? allLessons : []);

            // 4. 載入所有學生的練習進度 - 使用 email 比對
            if (allLessons.length > 0 && studentsArray.length > 0) {
                console.log("開始載入練習進度...");
                
                try {
                    // 收集所有學生的 email
                    const studentEmails = studentsArray.map(s => s.email).filter(Boolean);
                    console.log("學生 emails:", studentEmails);
                    
                    if (studentEmails.length === 0) {
                        console.log("沒有找到學生 email，無法載入進度");
                        setProgressData([]);
                        return;
                    }
                    
                    // 載入所有相關的練習進度
                    const allProgress = await StudentProgress.filter({
                        lesson_id: { $in: allLessons.map(l => l.id) }
                    }, "-completed_at");
                    
                    console.log("載入的所有練習進度:", allProgress.length);
                    
                    // 在前端過濾出屬於當前班級學生的進度
                    const classProgress = allProgress.filter(p => {
                        const studentEmail = p.student_email || p.created_by || p.student_id;
                        const isClassStudent = studentEmails.includes(studentEmail);
                        
                        if (isClassStudent) {
                            console.log(`匹配到學生 ${studentEmail} 的練習記錄`);
                        }
                        
                        return isClassStudent;
                    });
                    
                    console.log("班級學生的練習進度:", classProgress.length);
                    setProgressData(Array.isArray(classProgress) ? classProgress : []);
                } catch (error) {
                    console.error("載入學生進度失敗:", error);
                    setProgressData([]);
                }
            } else {
                console.log("沒有課文或學生，跳過載入進度");
                setProgressData([]);
            }

        } catch (error) {
            console.error("載入班級數據失敗:", error);
            setStudents([]);
            setLessons([]);
            setProgressData([]);
        } finally {
            setLoading(false);
            console.log("班級數據載入完成");
        }
    };

    // 獲取學生在特定課文的最佳表現
    const getStudentLessonPerformance = (studentEmail, lessonId, lesson) => {
        const studentProgress = progressData.filter(p => {
            if (p.lesson_id !== lessonId) return false;
            
            const recordEmail = p.student_email || p.created_by || p.student_id;
            return recordEmail === studentEmail;
        });

        if (studentProgress.length === 0) {
            return { hasData: false };
        }

        const bestProgress = studentProgress.reduce((best, current) => {
            const currentScore = (Number(current.accuracy_percentage) / 100) * Number(current.words_per_minute);
            const bestScore = (Number(best.accuracy_percentage) / 100) * Number(best.words_per_minute);
            return currentScore > bestScore ? current : best;
        });

        const student = students.find(s => s.email === studentEmail);
        const targetWpm = student?.target_wpm || lesson?.target_wpm || 230;
        const targetAccuracy = student?.target_accuracy || 85;

        const actualWpm = Number(bestProgress.words_per_minute) || 0;
        const actualAccuracy = Number(bestProgress.accuracy_percentage) || 0;
        
        const isAchieved = actualWpm >= targetWpm && actualAccuracy >= targetAccuracy;

        return {
            hasData: true,
            isAchieved,
            wpm: Math.round(actualWpm),
            accuracy: Math.round(actualAccuracy),
            attempts: studentProgress.length,
            bestProgress,
            allProgress: studentProgress
        };
    };

    // 處理點擊學生表現數據
    const handleCellClick = (student, lesson) => {
        const performance = getStudentLessonPerformance(student.email, lesson.id, lesson);
        
        if (!performance.hasData) {
            return;
        }

        setSelectedStudentData(student);
        setSelectedLessonData(lesson);
        setStudentProgressList(performance.allProgress.sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at)));
        setSidebarOpen(true);
    };

    // 關閉側欄
    const closeSidebar = () => {
        setSidebarOpen(false);
        setSelectedStudentData(null);
        setSelectedLessonData(null);
        setStudentProgressList([]);
        setSelectedProgressDetail(null);
    };

    // 打開練習詳情
    const openProgressDetail = (progress) => {
        setSelectedProgressDetail(progress);
    };

    const displayLessons = lessons.slice(0, displayedLessons);
    const canLoadMore = displayedLessons < lessons.length;

    const handleLoadMore = () => {
        setDisplayedLessons(prev => Math.min(prev + 5, lessons.length));
    };

    return (
        <div className="space-y-6 relative">
            {/* 班級選擇器 */}
            <div className="flex items-center gap-4">
                <div className="flex-1">
                    <label className="text-sm font-medium text-gray-700 mb-2 block">選擇班級</label>
                    <Select onValueChange={(classId) => {
                        const selectedClassData = allClasses.find(c => c.id === classId);
                        console.log("選擇班級:", selectedClassData);
                        setSelectedClass(selectedClassData);
                        setDisplayedLessons(5);
                    }}>
                        <SelectTrigger className="w-full">
                            <SelectValue placeholder="請選擇要查看表現的班級..." />
                        </SelectTrigger>
                        <SelectContent>
                            {allClasses.map(cls => (
                                <SelectItem key={cls.id} value={cls.id}>
                                    {cls.class_name}
                                    {cls.difficulty_level && ` (${cls.difficulty_level})`}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
                
                {selectedClass && (
                    <div className="flex gap-4 text-sm">
                        <div className="flex items-center gap-2">
                            <Users className="w-4 h-4 text-blue-600" />
                            <span className="text-gray-700">{students.length} 位學生</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <BookOpen className="w-4 h-4 text-green-600" />
                            <span className="text-gray-700">{lessons.length} 篇課文</span>
                        </div>
                    </div>
                )}
            </div>

            {/* 表現表格 */}
            {selectedClass && (
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                            <span>{selectedClass.class_name} - 全班朗讀表現</span>
                            {loading && (
                                <div className="w-5 h-5 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
                            )}
                        </CardTitle>
                        <div className="text-sm text-gray-600">
                            <p>✔ 表示達到個人或課文目標標準 / ✖ 表示尚未達標 / — 表示尚未練習</p>
                            <p>顯示最近 {displayedLessons} 篇課文，點擊有數據的格子可查看詳細練習記錄</p>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {students.length === 0 && !loading ? (
                            <div className="text-center py-8">
                                <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                                <p className="text-gray-500">此班級尚無學生資料</p>
                            </div>
                        ) : displayLessons.length === 0 && !loading ? (
                            <div className="text-center py-8">
                                <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                                <p className="text-gray-500">此班級尚無關聯的課文</p>
                            </div>
                        ) : (
                            <div className="relative">
                                <div className="overflow-x-auto border rounded-lg">
                                    <table className="w-full min-w-max">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="sticky left-0 bg-gray-50 px-4 py-3 text-left text-sm font-semibold text-gray-700 border-r border-gray-200 min-w-[120px] z-10">
                                                    學生姓名
                                                </th>
                                                {displayLessons.map(lesson => (
                                                    <th key={lesson.id} className="px-3 py-3 text-center text-sm font-semibold text-gray-700 border-r border-gray-200 min-w-[140px]">
                                                        <div className="space-y-1">
                                                            <div className="font-medium">{lesson.title}</div>
                                                            <div className="text-xs text-gray-500">
                                                                目標: {lesson.target_wpm || 230}字/分
                                                            </div>
                                                        </div>
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white">
                                            {students.map((student, index) => (
                                                <tr key={student.id} className={index % 2 === 0 ? "bg-white" : "bg-gray-50/50"}>
                                                    <td className="sticky left-0 bg-inherit px-4 py-3 border-r border-gray-200 z-10">
                                                        <div className="font-medium text-gray-900">{student.student_name}</div>
                                                        <div className="text-xs text-gray-500">{student.email}</div>
                                                    </td>
                                                    {displayLessons.map(lesson => {
                                                        const performance = getStudentLessonPerformance(student.email, lesson.id, lesson);
                                                        
                                                        return (
                                                            <td 
                                                                key={`${student.id}-${lesson.id}`} 
                                                                className={`px-3 py-3 text-center border-r border-gray-200 ${
                                                                    performance.hasData ? 'cursor-pointer hover:bg-blue-50 transition-colors' : ''
                                                                }`}
                                                                onClick={() => performance.hasData && handleCellClick(student, lesson)}
                                                            >
                                                                {!performance.hasData ? (
                                                                    <span className="text-gray-400 text-lg">—</span>
                                                                ) : (
                                                                    <div className="space-y-1">
                                                                        <div className="flex items-center justify-center gap-1">
                                                                            {performance.isAchieved ? (
                                                                                <CheckCircle2 className="w-4 h-4 text-green-600" />
                                                                            ) : (
                                                                                <XCircle className="w-4 h-4 text-red-600" />
                                                                            )}
                                                                            <span className={`text-xs font-medium ${
                                                                                performance.isAchieved ? 'text-green-600' : 'text-red-600'
                                                                            }`}>
                                                                                {performance.isAchieved ? '達標' : '未達標'}
                                                                            </span>
                                                                        </div>
                                                                        <div className="text-sm text-gray-700">
                                                                            <div>{performance.wpm} 字/分</div>
                                                                            <div>{performance.accuracy}% 正確率</div>
                                                                        </div>
                                                                        <Badge variant="outline" className="text-xs">
                                                                            {performance.attempts} 次練習
                                                                        </Badge>
                                                                    </div>
                                                                )}
                                                            </td>
                                                        );
                                                    })}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                {canLoadMore && (
                                    <div className="mt-6 text-center">
                                        <Button 
                                            variant="outline" 
                                            onClick={handleLoadMore}
                                            className="hover:bg-teal-50 hover:border-teal-300"
                                        >
                                            <BookOpen className="w-4 h-4 mr-2" />
                                            載入更多課文 (還有 {lessons.length - displayedLessons} 篇)
                                        </Button>
                                    </div>
                                )}
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* 側欄 */}
            {sidebarOpen && (
                <div className="fixed inset-0 z-50 flex">
                    <div 
                        className="fixed inset-0 bg-black/50 transition-opacity"
                        onClick={closeSidebar}
                    />
                    
                    <div className="ml-auto relative bg-white w-full max-w-md shadow-xl">
                        <div className="h-full flex flex-col">
                            <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-teal-500 to-blue-500 text-white">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-lg font-semibold">{selectedStudentData?.student_name}</h3>
                                        <p className="text-sm text-white/90">{selectedLessonData?.title}</p>
                                    </div>
                                    <Button 
                                        variant="ghost" 
                                        size="sm" 
                                        onClick={closeSidebar}
                                        className="text-white hover:bg-white/20"
                                    >
                                        <X className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>

                            <div className="flex-1 overflow-y-auto p-4">
                                <div className="space-y-4">
                                    <div className="text-sm text-gray-600 mb-4">
                                        共 {studentProgressList.length} 次練習記錄
                                    </div>
                                    
                                    {studentProgressList.map((progress, index) => (
                                        <Card 
                                            key={progress.id} 
                                            className="cursor-pointer hover:shadow-md transition-shadow border border-gray-200"
                                            onClick={() => openProgressDetail(progress)}
                                        >
                                            <CardContent className="p-4">
                                                <div className="flex justify-between items-start mb-3">
                                                    <div>
                                                        <Badge variant="outline" className="mb-2">
                                                            第 {progress.attempt_number} 次練習
                                                        </Badge>
                                                        <div className="text-xs text-gray-500">
                                                            {progress.completed_at ? format(new Date(progress.completed_at), "yyyy-MM-dd HH:mm", { locale: zhCN }) : 'N/A'}
                                                        </div>
                                                    </div>
                                                    <Eye className="w-4 h-4 text-gray-400" />
                                                </div>
                                                
                                                <div className="grid grid-cols-2 gap-3 text-sm">
                                                    <div className="flex items-center gap-2">
                                                        <Target className="w-4 h-4 text-green-600" />
                                                        <span className="text-gray-700">{Math.round(progress.accuracy_percentage)}%</span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <BarChart3 className="w-4 h-4 text-blue-600" />
                                                        <span className="text-gray-700">{Math.round(progress.words_per_minute)} 字/分</span>
                                                    </div>
                                                </div>
                                                
                                                <div className="mt-3">
                                                    <div className={`text-xs font-medium ${
                                                        Number(progress.words_per_minute) >= (selectedStudentData?.target_wpm || selectedLessonData?.target_wpm || 230) && 
                                                        Number(progress.accuracy_percentage) >= (selectedStudentData?.target_accuracy || 85)
                                                            ? 'text-green-600' : 'text-red-600'
                                                    }`}>
                                                        {Number(progress.words_per_minute) >= (selectedStudentData?.target_wpm || selectedLessonData?.target_wpm || 230) && 
                                                         Number(progress.accuracy_percentage) >= (selectedStudentData?.target_accuracy || 85) ? '✔ 達標' : '✖ 未達標'}
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 練習詳情 Modal */}
            {selectedProgressDetail && (
                <Dialog open={!!selectedProgressDetail} onOpenChange={() => setSelectedProgressDetail(null)}>
                    <DialogContent className="max-w-4xl w-[95vw] h-[95vh] max-h-[95vh] flex flex-col p-0 gap-0">
                        <div className="flex-shrink-0 p-4 md:p-6 border-b bg-white">
                            <div className="flex items-start justify-between gap-4">
                                <div className="min-w-0 flex-1">
                                    <DialogTitle className="text-lg md:text-xl font-bold leading-tight">
                                        {selectedStudentData?.student_name} - {selectedLessonData?.title}
                                    </DialogTitle>
                                    <p className="text-sm text-gray-600 mt-1">
                                        第{selectedProgressDetail.attempt_number}次練習
                                    </p>
                                </div>
                                <Button 
                                    variant="ghost" 
                                    size="sm" 
                                    onClick={() => setSelectedProgressDetail(null)}
                                    className="flex-shrink-0 w-8 h-8 p-0 hover:bg-gray-100 rounded-full"
                                >
                                    <X className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>
                        
                        <div className="flex-1 overflow-auto p-4 md:p-6">
                            <ResultsDisplay 
                                session={selectedProgressDetail} 
                                targets={{
                                    target_wpm: selectedStudentData?.target_wpm || selectedLessonData?.target_wpm || 230,
                                    target_accuracy: selectedStudentData?.target_accuracy || 85,
                                    set_by_teacher: true
                                }} 
                            />
                        </div>
                    </DialogContent>
                </Dialog>
            )}
        </div>
    );
}
