import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Class } from "@/api/entities";
import { ClassStudent } from "@/api/entities";
import { StudentProgress } from "@/api/entities";
import { Lesson } from "@/api/entities";
import { Users, ChevronDown, ChevronRight, BarChart3, CheckCircle, XCircle } from "lucide-react";

export default function ClassAnalytics() {
    const [classes, setClasses] = useState([]);
    const [selectedClassId, setSelectedClassId] = useState('');
    const [studentAnalytics, setStudentAnalytics] = useState([]);
    const [expandedStudents, setExpandedStudents] = useState(new Set());
    const [sortBy, setSortBy] = useState('name');
    const [loadingClasses, setLoadingClasses] = useState(true);
    const [loadingAnalytics, setLoadingAnalytics] = useState(false);

    // 載入班級列表
    useEffect(() => {
        const loadClasses = async () => {
            setLoadingClasses(true);
            try {
                const classesData = await Class.filter({ is_active: true }, "-created_date");
                setClasses(classesData);
                if (classesData.length > 0) {
                    setSelectedClassId(classesData[0].id);
                }
            } catch (error) {
                console.error("載入班級失敗:", error);
            } finally {
                setLoadingClasses(false);
            }
        };
        loadClasses();
    }, []);

    // 當選擇班級改變時載入數據
    useEffect(() => {
        if (selectedClassId) {
            loadClassAnalytics(selectedClassId);
        }
    }, [selectedClassId]);

    const loadClassAnalytics = useCallback(async (classId) => {
        setLoadingAnalytics(true);
        try {
            // 先載入班級學生
            const classStudents = await ClassStudent.filter({ class_id: classId });
            
            if (classStudents.length === 0) {
                setStudentAnalytics([]);
                setLoadingAnalytics(false);
                return;
            }

            // 立即顯示學生列表，數據預設為0
            const initialStudents = classStudents.map(student => ({
                ...student,
                totalAttempts: 0,
                avgWPM: 0,
                avgAccuracy: 0,
                achievementProgress: 0,
                lessonDetails: []
            }));
            setStudentAnalytics(initialStudents);

            // 然後載入練習記錄
            const studentIds = classStudents.map(s => s.student_id);
            const progressRecords = await StudentProgress.filter({ student_id: { $in: studentIds } });
            
            if (progressRecords.length === 0) {
                setLoadingAnalytics(false);
                return;
            }

            // 計算每個學生的統計數據
            const updatedStudents = initialStudents.map(student => {
                const studentRecords = progressRecords.filter(p => p.student_id === student.student_id);
                
                if (studentRecords.length === 0) {
                    return student; // 保持預設值
                }

                const totalAttempts = studentRecords.length;
                const avgWPM = Math.round(studentRecords.reduce((sum, r) => sum + (r.words_per_minute || 0), 0) / totalAttempts);
                const avgAccuracy = parseFloat((studentRecords.reduce((sum, r) => sum + (r.accuracy_percentage || 0), 0) / totalAttempts).toFixed(1));

                return {
                    ...student,
                    totalAttempts,
                    avgWPM,
                    avgAccuracy,
                    achievementProgress: 0 // 簡化版本先不計算達標進度
                };
            });

            setStudentAnalytics(updatedStudents);

        } catch (error) {
            console.error("載入班級分析失敗:", error);
        } finally {
            setLoadingAnalytics(false);
        }
    }, []);

    const sortedStudents = [...studentAnalytics].sort((a, b) => {
        switch (sortBy) {
            case 'attempts': return b.totalAttempts - a.totalAttempts;
            case 'wpm': return b.avgWPM - a.avgWPM;
            case 'accuracy': return b.avgAccuracy - a.avgAccuracy;
            default: return a.student_name.localeCompare(b.student_name);
        }
    });

    if (loadingClasses) {
        return <div className="text-center py-8">載入班級列表...</div>;
    }

    return (
        <div className="space-y-6">
            {/* 班級選擇和排序 */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="w-5 h-5" />
                        班級學生表現分析
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm font-medium text-gray-700 mb-2 block">選擇班級</label>
                            <Select value={selectedClassId} onValueChange={setSelectedClassId}>
                                <SelectTrigger>
                                    <SelectValue placeholder="請選擇班級" />
                                </SelectTrigger>
                                <SelectContent>
                                    {classes.map(cls => (
                                        <SelectItem key={cls.id} value={cls.id}>
                                            {cls.class_name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-700 mb-2 block">排序方式</label>
                            <Select value={sortBy} onValueChange={setSortBy}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="name">依姓名排序</SelectItem>
                                    <SelectItem value="attempts">依朗讀次數排序</SelectItem>
                                    <SelectItem value="wpm">依平均語速排序</SelectItem>
                                    <SelectItem value="accuracy">依平均正確率排序</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* 學生分析表格 */}
            {loadingAnalytics ? (
                <div className="text-center py-12">
                    <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600">載入學生數據...</p>
                </div>
            ) : sortedStudents.length === 0 ? (
                <Card>
                    <CardContent className="text-center py-12">
                        <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-500">此班級暫無學生資料</p>
                    </CardContent>
                </Card>
            ) : (
                <Card>
                    <CardContent className="p-0">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b">
                                    <tr>
                                        <th className="text-left py-3 px-4 font-medium text-gray-900">學生姓名</th>
                                        <th className="text-center py-3 px-4 font-medium text-gray-900">總朗讀次數</th>
                                        <th className="text-center py-3 px-4 font-medium text-gray-900">平均語速 (WPM)</th>
                                        <th className="text-center py-3 px-4 font-medium text-gray-900">平均正確率 (%)</th>
                                        <th className="text-center py-3 px-4 font-medium text-gray-900">達標進度</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sortedStudents.map((student, index) => (
                                        <tr key={student.student_id} className={`${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-teal-50 transition-colors border-b`}>
                                            <td className="py-3 px-4">
                                                <div className="font-medium text-gray-900">{student.student_name}</div>
                                                <div className="text-sm text-gray-500">{student.student_id}</div>
                                            </td>
                                            <td className="text-center py-3 px-4">
                                                <Badge variant="outline">{student.totalAttempts} 次</Badge>
                                            </td>
                                            <td className="text-center py-3 px-4 font-medium">{student.avgWPM}</td>
                                            <td className="text-center py-3 px-4 font-medium">{student.avgAccuracy}%</td>
                                            <td className="text-center py-3 px-4">
                                                <Progress value={student.achievementProgress} className="h-2" />
                                                <span className="text-xs text-gray-500">{Math.round(student.achievementProgress)}%</span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}