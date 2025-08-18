import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, Target, TrendingUp, Clock } from "lucide-react";
import { StudentProgress } from "@/api/entities";

export default function ClassStatsSummary({ classId, students = [] }) {
    const [stats, setStats] = useState({
        totalStudents: 0,
        avgPracticeCount: 0,
        achievementRate: 0,
        avgAccuracy: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (classId && students.length > 0) {
            calculateStats();
        } else {
            setStats({
                totalStudents: students.length,
                avgPracticeCount: 0,
                achievementRate: 0,
                avgAccuracy: 0
            });
            setLoading(false);
        }
    }, [classId, students]);

    const calculateStats = async () => {
        try {
            const studentIds = students.map(s => s.student_id);
            if (studentIds.length === 0) {
                setLoading(false);
                return;
            }

            // 載入學生的練習記錄
            const progressRecords = await StudentProgress.filter({
                student_id: { $in: studentIds }
            });

            const totalStudents = students.length;
            const totalPractices = progressRecords.length;
            const avgPracticeCount = totalStudents > 0 ? totalPractices / totalStudents : 0;
            
            // 計算平均正確率
            const avgAccuracy = progressRecords.length > 0 
                ? progressRecords.reduce((sum, p) => sum + (p.accuracy_percentage || 0), 0) / progressRecords.length 
                : 0;

            // 簡單的達標率計算（正確率 >= 80%）
            const achievedCount = progressRecords.filter(p => (p.accuracy_percentage || 0) >= 80).length;
            const achievementRate = progressRecords.length > 0 ? (achievedCount / progressRecords.length) * 100 : 0;

            setStats({
                totalStudents,
                avgPracticeCount: Math.round(avgPracticeCount * 10) / 10,
                achievementRate: Math.round(achievementRate * 10) / 10,
                avgAccuracy: Math.round(avgAccuracy * 10) / 10
            });
        } catch (error) {
            console.error("計算班級統計失敗:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-4">
                <div className="w-4 h-4 border-2 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="ml-2 text-sm text-gray-600">載入統計中...</span>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="bg-blue-50 border-blue-200">
                <CardContent className="p-4 text-center">
                    <div className="flex items-center justify-center mb-2">
                        <Users className="w-5 h-5 text-blue-600" />
                    </div>
                    <div className="text-2xl font-bold text-blue-900">{stats.totalStudents}</div>
                    <div className="text-xs text-blue-700">總人數</div>
                </CardContent>
            </Card>

            <Card className="bg-green-50 border-green-200">
                <CardContent className="p-4 text-center">
                    <div className="flex items-center justify-center mb-2">
                        <Clock className="w-5 h-5 text-green-600" />
                    </div>
                    <div className="text-2xl font-bold text-green-900">{stats.avgPracticeCount}</div>
                    <div className="text-xs text-green-700">平均練習次數</div>
                </CardContent>
            </Card>

            <Card className="bg-purple-50 border-purple-200">
                <CardContent className="p-4 text-center">
                    <div className="flex items-center justify-center mb-2">
                        <Target className="w-5 h-5 text-purple-600" />
                    </div>
                    <div className="text-2xl font-bold text-purple-900">{stats.achievementRate}%</div>
                    <div className="text-xs text-purple-700">達標率</div>
                </CardContent>
            </Card>

            <Card className="bg-orange-50 border-orange-200">
                <CardContent className="p-4 text-center">
                    <div className="flex items-center justify-center mb-2">
                        <TrendingUp className="w-5 h-5 text-orange-600" />
                    </div>
                    <div className="text-2xl font-bold text-orange-900">{stats.avgAccuracy}%</div>
                    <div className="text-xs text-orange-700">平均正確率</div>
                </CardContent>
            </Card>
        </div>
    );
}