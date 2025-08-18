
import React, { useState, useEffect, useCallback } from "react";
import { Lesson } from "@/api/entities";
import { User } from "@/api/entities";
import { ClassStudent } from "@/api/entities";
import { ActivityResult } from "@/api/entities";
import { Course } from "@/api/entities";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TrendingUp, TrendingDown, Target, Clock, BarChart3, Eye, CheckCircle, XCircle, X } from "lucide-react";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

import UnifiedResultsDisplay from "../components/assessment/UnifiedResultsDisplay";

function PerformanceChart({ data, dataKey, yAxisLabel, targetStandard, unit, color }) {
  const [hoveredData, setHoveredData] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div className="h-80 flex flex-col items-center justify-center text-center text-gray-500">
        <BarChart3 className="w-12 h-12 text-gray-300 mb-4" />
        <p className="font-semibold">暫無練習數據</p>
      </div>
    );
  }

  const width = 800;
  const height = 350;
  const padding = { top: 60, right: 60, bottom: 40, left: 60 };

  const values = data.map(d => d[dataKey]);
  const maxValue = Math.max(1, ...values, targetStandard || 0);

  const yDomainMax = dataKey === 'accuracy_percentage' ? 100 : Math.ceil((maxValue + 10) / 10) * 10;
  
  const xScale = (index) => data.length === 1 
    ? padding.left + (width - padding.left - padding.right) / 2 
    : padding.left + (index * (width - padding.left - padding.right)) / (data.length - 1);
  
  const yScale = (value) => height - padding.bottom - Math.max(0, (value / yDomainMax)) * (height - padding.top - padding.bottom);
  
  const linePath = data.map((d, i) => 
    `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d[dataKey])}`
  ).join(' ');
  
  const standardY = targetStandard != null ? yScale(targetStandard) : null;

  return (
    <div className="relative w-full h-80">
      <div className="absolute -top-4 right-0 p-3 bg-white/80 backdrop-blur-sm border rounded-lg shadow-lg text-sm z-10 pointer-events-none min-w-[200px] transition-opacity duration-200" style={{ opacity: hoveredData ? 1 : 0, transform: hoveredData ? 'translateY(0)' : 'translateY(-10px)' }}>
        {hoveredData && (
          <>
            <p className="font-bold text-gray-900">{hoveredData.lessonTitle} - {hoveredData.title}</p>
            <p className="text-sm font-medium" style={{ color }}>{yAxisLabel}: {hoveredData[dataKey].toFixed(1)}{unit}</p>
            {hoveredData.activityType === 'reading_assessment' && (
              <>
                {dataKey !== 'words_per_minute' && <p className="text-xs text-gray-500">語速: {hoveredData.words_per_minute.toFixed(0)} 字/分</p>}
                {dataKey !== 'accuracy_percentage' && <p className="text-xs text-gray-500">正確率: {hoveredData.accuracy_percentage.toFixed(1)}%</p>}
                {dataKey !== 'correct_wpm' && <p className="text-xs text-gray-500">正確字數/分: {hoveredData.correct_wpm.toFixed(0)} 字/分</p>}
              </>
            )}
            <p className="text-xs text-gray-500">日期: {format(new Date(hoveredData.date), "yyyy-MM-dd", { locale: zhCN })}</p>
          </>
        )}
      </div>

      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="border rounded-lg bg-white" onMouseLeave={() => setHoveredData(null)}>
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e5e7eb" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        
        {[0, 0.25, 0.5, 0.75, 1].map(tick => {
          const val = Math.round(yDomainMax * tick);
          return (
            <g key={`y-label-${tick}`}>
              <text x={padding.left - 8} y={yScale(val) + 4} fontSize="10" fill="#6b7280" textAnchor="end">{val}</text>
              <line x1={padding.left} y1={yScale(val)} x2={width-padding.right} y2={yScale(val)} stroke="#e5e7eb" strokeDasharray="2,2"/>
            </g>
          );
        })}
        <text 
          x={padding.left - 30} 
          y={height / 2} 
          fontSize="12" 
          fill="#6b7280" 
          fontWeight="bold" 
          textAnchor="middle" 
          transform={`rotate(-90, ${padding.left-30}, ${height/2})`}
        >
          {yAxisLabel}
        </text>
        
        {data.map((d, i) => {
          if (data.length <= 10 || i % Math.ceil(data.length / 8) === 0) {
            return (
              <text key={i} x={xScale(i)} y={height - padding.bottom + 15} fontSize="10" fill="#6b7280" textAnchor="middle">
                {d.name}
              </text>
            );
          }
          return null;
        })}
        
        {standardY != null && (
          <>
            <line 
              x1={padding.left} 
              y1={standardY} 
              x2={width - padding.right} 
              y2={standardY} 
              stroke="#ef4444" 
              strokeWidth="2" 
              strokeDasharray="5,5"
            />
            <text 
              x={width - padding.right} 
              y={standardY - 5} 
              fontSize="11" 
              fill="#ef4444" 
              fontWeight="bold" 
              textAnchor="end"
            >
              目標: {targetStandard}{unit}
            </text>
          </>
        )}
        
        <path d={linePath} fill="none" stroke={color} strokeWidth="3"/>
        
        {data.map((d, i) => (
          <circle 
            key={`point-${i}`} 
            cx={xScale(i)} 
            cy={yScale(d[dataKey])} 
            r="5" 
            fill={targetStandard != null && d[dataKey] >= targetStandard ? "#22c55e" : color}
            stroke="white"
            strokeWidth="2"
            onMouseOver={() => setHoveredData(d)}
            onMouseMove={(e) => { /* Optional: update tooltip position if needed */ }}
          />
        ))}
        
      </svg>
    </div>
  );
}

export default function StatisticsPage() {
  const [chartData, setChartData] = useState({ chart: [], table: [] });
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [overallStats, setOverallStats] = useState({
    totalAssessments: 0,
    avgAccuracy: 0,
    avgSpeed: 0,
    avgCorrectWPM: 0,
    improvement: 0
  });
  const [activeView, setActiveView] = useState('correct_wpm');

  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  const fetchWithRetry = async (fetchFn, maxRetries = 3, delayMs = 1000) => {
      for (let i = 0; i < maxRetries; i++) {
          try {
              return await fetchFn();
          } catch (error) {
              if (error.response?.status === 429 && i < maxRetries - 1) {
                  console.warn(`API 請求被限制，${delayMs * (i + 1)}ms 後重試... (${i + 1}/${maxRetries})`);
                  await delay(delayMs * (i + 1));
                  continue;
              }
              throw error;
          }
      }
  };

  const urlParams = new URLSearchParams(window.location.search);
  const viewMode = urlParams.get('view_mode');
  const targetStudentEmail = urlParams.get('student_email');
  const isTeacherView = viewMode === 'teacher';

  useEffect(() => {
    loadData();
  }, [isTeacherView, targetStudentEmail]);

  const calculateOverallStats = (allPracticesData) => {
    const readingAssessments = allPracticesData.filter(p => p.activityType === 'reading_assessment');

    const totalAssessments = allPracticesData.length;
    if (totalAssessments === 0) {
      setOverallStats({ totalAssessments: 0, avgAccuracy: 0, avgSpeed: 0, avgCorrectWPM: 0, improvement: 0 });
      return;
    }

    const avgAccuracy = allPracticesData.reduce((sum, item) => sum + (Number(item.accuracy_percentage) || 0), 0) / totalAssessments;
    
    const avgSpeed = readingAssessments.length > 0 ? readingAssessments.reduce((sum, item) => sum + (Number(item.words_per_minute) || 0), 0) / readingAssessments.length : 0;
    const avgCorrectWPM = readingAssessments.length > 0 ? readingAssessments.reduce((sum, item) => {
      const correctWPM = (Number(item.accuracy_percentage) / 100) * (Number(item.words_per_minute) || 0);
      return sum + correctWPM;
    }, 0) / readingAssessments.length : 0;

    let improvement = 0;
    if (readingAssessments.length >= 6) {
      const sortedByDateAsc = [...readingAssessments].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      const recent = sortedByDateAsc.slice(-3);
      const previous = sortedByDateAsc.slice(-6, -3);

      if (recent.length === 3 && previous.length === 3) {
        const recentAvgCorrectWPM = recent.reduce((sum, p) => {
          const correctWPM = (Number(p.accuracy_percentage) / 100) * (Number(p.words_per_minute) || 0);
          return sum + correctWPM;
        }, 0) / recent.length;
        
        const previousAvgCorrectWPM = previous.reduce((sum, p) => {
          const correctWPM = (Number(p.accuracy_percentage) / 100) * (Number(p.words_per_minute) || 0);
          return sum + correctWPM;
        }, 0) / previous.length;
        
        if (previousAvgCorrectWPM === 0) {
          improvement = recentAvgCorrectWPM > 0 ? 10000 : 0;
        } else {
          improvement = ((recentAvgCorrectWPM - previousAvgCorrectWPM) / previousAvgCorrectWPM) * 100;
        }
      }
    }
    
    setOverallStats({ 
      totalAssessments, 
      avgAccuracy, 
      avgCorrectWPM,
      avgSpeed, 
      improvement 
    });
  };

  const processGroupedData = useCallback((allPractices) => {
    const groupedByCourse = allPractices.reduce((courseGroups, practice) => {
        const courseId = practice.courseId;
        const lessonId = practice.lesson_id;
        
        if (!courseGroups[courseId]) {
            courseGroups[courseId] = {
                courseId: courseId,
                courseTitle: practice.courseTitle,
                lessons: {},
                totalPractices: 0,
                latestDate: null,
                bestOverallAccuracy: 0,
                bestOverallSpeed: 0,
                bestOverallCorrectWPM: 0
            };
        }
        
        if (!courseGroups[courseId].lessons[lessonId]) {
            courseGroups[courseId].lessons[lessonId] = {
                lessonId,
                lessonTitle: practice.lessonTitle,
                activityType: practice.activityType,
                attempts: [],
                bestAccuracy: 0,
                bestSpeed: 0,
                bestCorrectWPM: 0,
                latestDate: null,
                totalAttempts: 0
            };
        }
        
        const lessonGroup = courseGroups[courseId].lessons[lessonId];
        lessonGroup.attempts.push(practice);
        lessonGroup.totalAttempts++;
        lessonGroup.bestAccuracy = Math.max(lessonGroup.bestAccuracy, practice.accuracy_percentage);
        
        if (practice.activityType === 'reading_assessment') {
            lessonGroup.bestSpeed = Math.max(lessonGroup.bestSpeed, practice.words_per_minute);
            lessonGroup.bestCorrectWPM = Math.max(lessonGroup.bestCorrectWPM, practice.correct_wpm);
            
            courseGroups[courseId].bestOverallSpeed = Math.max(courseGroups[courseId].bestOverallSpeed, practice.words_per_minute);
            courseGroups[courseId].bestOverallCorrectWPM = Math.max(courseGroups[courseId].bestOverallCorrectWPM, practice.correct_wpm);
        }
        
        courseGroups[courseId].totalPractices++;
        courseGroups[courseId].bestOverallAccuracy = Math.max(courseGroups[courseId].bestOverallAccuracy, practice.accuracy_percentage);
        
        const practiceDate = new Date(practice.date);
        if (!lessonGroup.latestDate || practiceDate > lessonGroup.latestDate) {
            lessonGroup.latestDate = practiceDate;
        }
        if (!courseGroups[courseId].latestDate || practiceDate > courseGroups[courseId].latestDate) {
            courseGroups[courseId].latestDate = practiceDate;
        }
        
        return courseGroups;
    }, {});

    const structuredData = Object.values(groupedByCourse)
        .map(courseGroup => ({
            ...courseGroup,
            lessons: Object.values(courseGroup.lessons)
                .map(lessonGroup => ({
                    ...lessonGroup,
                    attempts: lessonGroup.attempts.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()),
                }))
                .sort((a, b) => new Date(b.latestDate).getTime() - new Date(a.latestDate).getTime())
        }))
        .sort((a, b) => new Date(b.latestDate).getTime() - new Date(a.latestDate).getTime());

    const chartSourceData = allPractices
        .filter(p => activeView === 'accuracy_percentage' || p.activityType === 'reading_assessment')
        .slice(-20)
        .map((practice, index) => ({
            ...practice,
            name: `第${index + 1}次`,
        }));
    
    setChartData({ chart: chartSourceData, table: structuredData });
    calculateOverallStats(allPractices);
  }, [activeView]);

  const prepareAndSetAllData = async (allActivityResults, allLessons) => {
        const lessonMap = new Map(allLessons.map(l => [l.id, l]));

        let allPractices = allActivityResults.map(a => {
            const lesson = lessonMap.get(a.lesson_id);
            let title = `第${a.attempt_number}次練習`;
            let wordsPerMinute = 0;
            let accuracyPercentage = 0;
            let correctWpm = 0;

            if (a.activity_type === 'reading_assessment') {
                title = `第${a.attempt_number}次朗讀練習`; 
                wordsPerMinute = Number(a.words_per_minute) || 0; 
                accuracyPercentage = Number(a.percentage_score) || 0;
                correctWpm = Math.round((accuracyPercentage / 100) * wordsPerMinute);
            } else if (a.activity_type === 'sentence_making') {
                title = `第${a.attempt_number}次造句`;
                accuracyPercentage = Number(a.percentage_score) || 0;
            } else if (a.activity_type === 'listening_cloze') {
                title = `第${a.attempt_number}次聽力`;
                accuracyPercentage = Number(a.percentage_score) || 0;
            } else if (a.activity_type === 'speaking_practice') {
                title = `第${a.attempt_number}次錄音`;
                accuracyPercentage = Number(a.percentage_score) || 0;
            } else {
                accuracyPercentage = Number(a.percentage_score) || 0;
            }

            return {
                ...a,
                date: a.completed_at,
                title: title,
                lessonTitle: lesson?.title || '未知課文',
                activityType: a.activity_type,
                courseId: lesson?.course_id || 'unknown_course',
                courseTitle: lesson?.course?.title || '未知課程',
                words_per_minute: wordsPerMinute,
                accuracy_percentage: accuracyPercentage,
                correct_wpm: correctWpm,
            };
        })
        .filter(p => p.date && !isNaN(new Date(p.date).getTime()))
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        const uniqueCourseIds = [...new Set(allPractices.map(p => p.courseId))].filter(id => id && id !== 'unknown_course');
        const courseTitlesPromises = uniqueCourseIds.map(async (courseId) => {
            try {
                const course = await fetchWithRetry(() => Course.get(courseId));
                return { courseId, courseTitle: course?.title || '未知課程' };
            } catch (error) {
                console.error(`載入課程 ${courseId} 失敗:`, error);
                return { courseId, courseTitle: '未知課程' };
            }
        });

        const fetchedCourseTitles = await Promise.all(courseTitlesPromises);
        const courseTitleMap = new Map(fetchedCourseTitles.map(c => [c.courseId, c.courseTitle]));
        
        const practicesWithCourseTitles = allPractices.map(practice => ({
            ...practice,
            courseTitle: courseTitleMap.get(practice.courseId) || practice.courseTitle
        }));

        processGroupedData(practicesWithCourseTitles);
    };

  const loadData = async () => {
    setLoading(true);
    try {
        let allActivityResults = [];
        let allLessons = [];
        
        const fetchAndFilterData = async (userEmail, userId) => {
            console.log(`正在為使用者 ${userEmail} 載入數據...`);
            
            const [activityResults, lessons] = await Promise.all([
                fetchWithRetry(() => ActivityResult.list("-completed_at", 1000)),
                fetchWithRetry(() => Lesson.list())
            ]);

            const filteredActivities = activityResults.filter(a => a.student_email === userEmail || a.student_id === userId);
            
            return {
                activityData: filteredActivities,
                allLessons: lessons
            };
        };
        
        // 核心修正：優先使用 sessionStorage 的學生視角
        const studentViewData = sessionStorage.getItem('studentView');
        const studentInView = studentViewData ? JSON.parse(studentViewData) : null;

        if (studentInView) {
            console.log("學生視角模式 - 學生 email:", studentInView.email);
            
            // 根據學生 email 查找對應的 User 資料
            let targetUser;
            try {
                const studentUsers = await User.filter({ email: studentInView.email });
                if (studentUsers.length > 0) {
                    targetUser = studentUsers[0];
                    console.log("找到學生 User 資料:", targetUser);
                } else {
                    // 如果找不到對應的 User，使用 sessionStorage 中的基本資訊
                    console.log("未找到學生 User，使用 sessionStorage 資料");
                    targetUser = { 
                        email: studentInView.email, 
                        id: studentInView.id, 
                        full_name: studentInView.name 
                    };
                }
            } catch (error) {
                console.error("查找學生 User 失敗:", error);
                targetUser = { 
                    email: studentInView.email, 
                    id: studentInView.id, 
                    full_name: studentInView.name 
                };
            }
            
            const { activityData, allLessons: lessons } = await fetchAndFilterData(targetUser.email, targetUser.id);
            allActivityResults = activityData;
            allLessons = lessons;
        } else if (isTeacherView && targetStudentEmail) {
            console.log("教師檢視模式 - 學生 email:", targetStudentEmail);
            const studentUser = await User.filter({ email: targetStudentEmail });
            const studentId = studentUser.length > 0 ? studentUser[0].id : null;

            const { activityData, allLessons: lessons } = await fetchAndFilterData(targetStudentEmail, studentId);
            allActivityResults = activityData;
            allLessons = lessons;

        } else {
            const currentUser = await User.me();
            console.log("學生檢視模式 - 當前用戶 email:", currentUser.email);
            if (!currentUser?.email) {
                console.log("用戶 email 不可用，停止載入");
                setLoading(false);
                return;
            }
            const { activityData, allLessons: lessons } = await fetchAndFilterData(currentUser.email, currentUser.id);
            allActivityResults = activityData;
            allLessons = lessons;
        }

        await prepareAndSetAllData(allActivityResults, allLessons);
    } catch (error) {
        console.error("載入數據失敗:", error);
        if (error.response?.status === 429) {
            alert("系統目前負載較高，請稍候再試。");
        }
    } finally {
        setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="p-6 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">載入統計數據...</p>
        </div>
      </div>
    );
  }

  const chartConfig = {
    correct_wpm: { dataKey: 'correct_wpm', label: '正確字數/分', target: 150, unit: '字/分', color: '#0891b2' },
    accuracy_percentage: { dataKey: 'accuracy_percentage', label: '正確率/分數', target: 95, unit: '%', color: '#059669' },
    words_per_minute: { dataKey: 'words_per_minute', label: '語速', target: 180, unit: '字/分', color: '#7c3aed' }
  };
  const currentConfig = chartConfig[activeView];


  return (
    <Dialog>
      <div className="p-4 md:p-6 min-h-screen">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
              {isTeacherView ? '學生統計報告' : '統計報告'}
            </h1>
            <p className="text-gray-600">
              {isTeacherView ? '查看學生的朗讀表現和進步趨勢' : '分析您的朗讀表現和進度趨勢'}
            </p>
            {isTeacherView && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  <strong>教師檢視模式</strong> - 您正在查看學生: {targetStudentEmail} 的統計報告
                </p>
                {!targetStudentEmail && (
                  <p className="text-sm text-red-600 mt-1">
                    URL中缺少 'student_email' 參數，請確認網址是否正確。
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-8">
            <Card className="glass-effect border-0 shadow-lg">
              <CardContent className="p-4 md:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">總練習的次數</p>
                    <p className="text-2xl font-bold text-gray-900">{overallStats.totalAssessments}</p>
                  </div>
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 md:w-6 md:h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass-effect border-0 shadow-lg">
              <CardContent className="p-4 md:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">平均正確字數</p>
                    <p className="text-2xl font-bold text-gray-900">{Math.round(overallStats.avgCorrectWPM || 0)}</p>
                    <p className="text-xs text-gray-500">字/分鐘</p>
                  </div>
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-green-100 rounded-xl flex items-center justify-center">
                    <Target className="w-5 h-5 md:w-6 md:h-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass-effect border-0 shadow-lg">
              <CardContent className="p-4 md:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">平均語速</p>
                    <p className="text-2xl font-bold text-gray-900">{overallStats.avgSpeed.toFixed(0)}</p>
                    <p className="text-xs text-gray-500">字/分鐘</p>
                  </div>
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                    <Clock className="w-5 h-5 md:w-6 md:h-6 text-purple-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass-effect border-0 shadow-lg">
              <CardContent className="p-4 md:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">最近改進</p>
                    <p className={`text-2xl font-bold ${overallStats.improvement >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {overallStats.improvement > 0 ? '+' : ''}{overallStats.improvement.toFixed(1)}%
                    </p>
                  </div>
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                    {overallStats.improvement >= 0 ? 
                      <TrendingUp className="w-5 h-5 md:w-6 md:h-6 text-orange-600" /> : 
                      <TrendingDown className="w-5 h-5 md:w-6 md:h-6 text-orange-600" />
                    }
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="glass-effect border-0 shadow-lg mb-8">
            <CardHeader>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="w-full sm:w-auto">
                  <CardTitle>
                    {isTeacherView ? '學生學習進度' : '我的學習進度'}
                  </CardTitle>
                  <p className="text-sm text-gray-600 mt-1">紅色虛線為{isTeacherView ? '設定的' : '老師設定的'}目標標準，將滑鼠懸停在數據點上可查看詳細資訊。</p>
                </div>
                <Tabs defaultValue="correct_wpm" onValueChange={setActiveView} className="w-full sm:w-auto">
                  <TabsList className="grid grid-cols-3 w-full sm:w-auto">
                    <TabsTrigger value="correct_wpm">正確字/分</TabsTrigger>
                    <TabsTrigger value="accuracy_percentage">正確率</TabsTrigger>
                    <TabsTrigger value="words_per_minute">語速</TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <div className="min-w-[700px] h-[350px]">
                {chartData.chart && chartData.chart.length >= 1 ? (
                  <PerformanceChart
                    data={chartData.chart}
                    dataKey={currentConfig.dataKey}
                    yAxisLabel={currentConfig.label}
                    targetStandard={currentConfig.target}
                    unit={currentConfig.unit}
                    color={currentConfig.color}
                  />
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center text-gray-500">
                    <BarChart3 className="w-12 h-12 text-gray-300 mb-4" />
                    <p className="font-semibold">暫無練習數據</p>
                    <p className="text-sm">完成練習後，這裡將會顯示{isTeacherView ? '學生的' : '您的'}進度趨勢。</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
          
          <Card className="glass-effect border-0 shadow-lg">
            <CardHeader>
              <CardTitle>練習記錄</CardTitle>
              <p className="text-sm text-gray-600">
                {isTeacherView ? '學生的練習記錄列表（按課程和課文分組）' : '您的練習記錄（按課程和課文分組），點擊「查看詳情」可查看分析結果'}
              </p>
            </CardHeader>
            <CardContent>
              {chartData.table?.length === 0 ? 
                <div className="text-center py-8">
                  <p className="text-gray-500">暫無練習記錄</p>
                </div> :
                <div>
                  <div className="md:hidden space-y-8">
                    {chartData.table?.map((courseGroup) => (
                      <div key={courseGroup.courseId} className="space-y-4">
                        <Card className="bg-gradient-to-r from-indigo-50 to-blue-50 border-l-4 border-l-indigo-500">
                          <CardHeader className="pb-3">
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <h2 className="text-xl font-bold text-indigo-900 mb-1">{courseGroup.courseTitle}</h2>
                                <p className="text-sm text-indigo-600">共 {courseGroup.totalPractices} 次練習 • {courseGroup.lessons.length} 篇課文</p>
                              </div>
                              <Badge variant="outline" className="ml-2 border-indigo-300 text-indigo-700">
                                {format(new Date(courseGroup.latestDate), "MM-dd", { locale: zhCN })}
                              </Badge>
                            </div>
                            
                            <div className="grid grid-cols-3 gap-2 mt-3 p-3 bg-white/50 rounded-lg">
                              <div className="text-center">
                                <p className="text-xs text-gray-600">最佳正確率</p>
                                <p className="font-bold text-indigo-700">{courseGroup.bestOverallAccuracy.toFixed(1)}%</p>
                              </div>
                              {courseGroup.bestOverallSpeed > 0 && (
                                <>
                                  <div className="text-center">
                                    <p className="text-xs text-gray-600">最佳語速</p>
                                    <p className="font-bold text-indigo-700">{Math.round(courseGroup.bestOverallSpeed)}</p>
                                  </div>
                                  <div className="text-center">
                                    <p className="text-xs text-gray-600">最佳正確字/分</p>
                                    <p className="font-bold text-indigo-700">{Math.round(courseGroup.bestOverallCorrectWPM)}</p>
                                  </div>
                                </>
                              )}
                            </div>
                          </CardHeader>
                        </Card>

                        <div className="pl-4 space-y-4">
                          {courseGroup.lessons.map((lessonGroup) => (
                            <Card key={lessonGroup.lessonId} className="bg-white/90 backdrop-blur-sm border-l-4 border-l-teal-500">
                              <CardHeader className="pb-3">
                                <div className="flex justify-between items-start">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                      <h3 className="font-bold text-lg text-gray-900">{lessonGroup.lessonTitle}</h3>
                                      <Badge className={
                                        lessonGroup.activityType === 'reading_assessment' ? 'bg-yellow-100 text-yellow-800' :
                                        lessonGroup.activityType === 'listening_cloze' ? 'bg-blue-100 text-blue-800' :
                                        lessonGroup.activityType === 'sentence_making' ? 'bg-purple-100 text-purple-800' :
                                        lessonGroup.activityType === 'speaking_practice' ? 'bg-green-100 text-green-800' :
                                        'bg-gray-100 text-gray-800'
                                      }>
                                        {lessonGroup.activityType === 'reading_assessment' ? '口說' :
                                         lessonGroup.activityType === 'listening_cloze' ? '聽力克漏字' :
                                         lessonGroup.activityType === 'sentence_making' ? '造句' :
                                         lessonGroup.activityType === 'speaking_practice' ? '錄音' :
                                         '練習'}
                                      </Badge>
                                    </div>
                                    <p className="text-sm text-gray-600">共 {lessonGroup.totalAttempts} 次練習</p>
                                  </div>
                                  <Badge variant="outline" className="ml-2">
                                    {format(new Date(lessonGroup.latestDate), "MM-dd", { locale: zhCN })}
                                  </Badge>
                                </div>
                              </CardHeader>
                              <CardContent className="pt-0">
                                <div className="grid grid-cols-3 gap-2 mb-4 p-3 bg-teal-50 rounded-lg">
                                  <div className="text-center">
                                    <p className="text-xs text-gray-600">最佳正確率</p>
                                    <p className="font-bold text-teal-700">{lessonGroup.bestAccuracy.toFixed(1)}%</p>
                                  </div>
                                  {lessonGroup.activityType === 'reading_assessment' && (
                                    <>
                                      <div className="text-center">
                                        <p className="text-xs text-gray-600">最佳語速</p>
                                        <p className="font-bold text-teal-700">{Math.round(lessonGroup.bestSpeed)}</p>
                                      </div>
                                      <div className="text-center">
                                        <p className="text-xs text-gray-600">最佳正確字/分</p>
                                        <p className="font-bold text-teal-700">{Math.round(lessonGroup.bestCorrectWPM)}</p>
                                      </div>
                                    </>
                                  )}
                                </div>
                                
                                <div className="space-y-2">
                                  {lessonGroup.attempts.map((attempt) => (
                                    <DialogTrigger asChild key={attempt.id}>
                                      <div 
                                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 active:scale-95 transition-all"
                                        onClick={() => setSelectedRecord(attempt)}
                                      >
                                        <div className="flex items-center gap-3">
                                          <Badge variant="secondary">第{attempt.attempt_number}次</Badge>
                                          <div className="text-sm">
                                            <span className={`font-semibold ${
                                              attempt.accuracy_percentage >= 90 ? 'text-green-600' : 
                                              attempt.accuracy_percentage >= 70 ? 'text-yellow-600' : 'text-red-600'
                                            }`}>
                                              {attempt.accuracy_percentage.toFixed(1)}%
                                            </span>
                                            {lessonGroup.activityType === 'reading_assessment' && (
                                              <span className="text-gray-500 ml-2">
                                                {Math.round(attempt.words_per_minute)}字/分
                                              </span>
                                            )}
                                          </div>
                                        </div>
                                        <div className="text-xs text-gray-500">
                                          {format(new Date(attempt.date), "MM-dd HH:mm", { locale: zhCN })}
                                        </div>
                                      </div>
                                    </DialogTrigger>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="hidden md:block space-y-8">
                    {chartData.table?.map((courseGroup) => (
                      <div key={courseGroup.courseId} className="space-y-6">
                        <Card className="bg-gradient-to-r from-indigo-50 to-blue-50 border-l-4 border-l-indigo-500">
                          <CardHeader>
                            <div className="flex justify-between items-center">
                              <div>
                                <h2 className="text-2xl font-bold text-indigo-900 mb-2">{courseGroup.courseTitle}</h2>
                                <p className="text-sm text-indigo-600">
                                  共 {courseGroup.totalPractices} 次練習 • {courseGroup.lessons.length} 篇課文 • 
                                  最後練習：{format(new Date(courseGroup.latestDate), "yyyy-MM-dd", { locale: zhCN })}
                                </p>
                              </div>
                              <div className="flex gap-6 text-sm">
                                <div className="text-center">
                                  <p className="text-indigo-600">課程最佳正確率</p>
                                  <p className="font-bold text-indigo-800 text-lg">{courseGroup.bestOverallAccuracy.toFixed(1)}%</p>
                                </div>
                                {courseGroup.bestOverallSpeed > 0 && (
                                  <>
                                    <div className="text-center">
                                      <p className="text-indigo-600">課程最佳語速</p>
                                      <p className="font-bold text-indigo-800 text-lg">{Math.round(courseGroup.bestOverallSpeed)} 字/分</p>
                                    </div>
                                    <div className="text-center">
                                      <p className="text-indigo-600">課程最佳正確字/分</p>
                                      <p className="font-bold text-indigo-800 text-lg">{Math.round(courseGroup.bestOverallCorrectWPM)}</p>
                                    </div>
                                  </>
                                )}
                              </div>
                            </div>
                          </CardHeader>
                        </Card>

                        <div className="pl-6 space-y-6">
                          {courseGroup.lessons.map((lessonGroup) => (
                            <Card key={lessonGroup.lessonId} className="bg-white/90 backdrop-blur-sm">
                              <CardHeader className="pb-4">
                                <div className="flex justify-between items-center">
                                  <div>
                                    <div className="flex items-center gap-2 mb-2">
                                      <h3 className="text-xl font-bold text-gray-900">{lessonGroup.lessonTitle}</h3>
                                      <Badge className={
                                        lessonGroup.activityType === 'reading_assessment' ? 'bg-yellow-100 text-yellow-800' :
                                        lessonGroup.activityType === 'listening_cloze' ? 'bg-blue-100 text-blue-800' :
                                        lessonGroup.activityType === 'sentence_making' ? 'bg-purple-100 text-purple-800' :
                                        lessonGroup.activityType === 'speaking_practice' ? 'bg-green-100 text-green-800' :
                                        'bg-gray-100 text-gray-800'
                                      }>
                                        {lessonGroup.activityType === 'reading_assessment' ? '口說' :
                                         lessonGroup.activityType === 'listening_cloze' ? '聽力克漏字' :
                                         lessonGroup.activityType === 'sentence_making' ? '造句' :
                                         lessonGroup.activityType === 'speaking_practice' ? '錄音' :
                                         '練習'}
                                      </Badge>
                                    </div>
                                    <p className="text-sm text-gray-600">共 {lessonGroup.totalAttempts} 次練習 • 最後練習：{format(new Date(lessonGroup.latestDate), "yyyy-MM-dd", { locale: zhCN })}</p>
                                  </div>
                                  <div className="flex gap-4 text-sm">
                                    <div className="text-center">
                                      <p className="text-gray-600">最佳正確率</p>
                                      <p className="font-bold text-green-600">{lessonGroup.bestAccuracy.toFixed(1)}%</p>
                                    </div>
                                    {lessonGroup.activityType === 'reading_assessment' && (
                                      <>
                                        <div className="text-center">
                                          <p className="text-gray-600">最佳語速</p>
                                          <p className="font-bold text-purple-600">{Math.round(lessonGroup.bestSpeed)} 字/分</p>
                                        </div>
                                        <div className="text-center">
                                          <p className="text-gray-600">最佳正確字/分</p>
                                          <p className="font-bold text-teal-600">{Math.round(lessonGroup.bestCorrectWPM)}</p>
                                        </div>
                                      </>
                                    )}
                                  </div>
                                </div>
                              </CardHeader>
                              <CardContent>
                                <div className="overflow-x-auto">
                                  <table className="w-full">
                                    <thead>
                                      <tr className="border-b border-gray-200">
                                        <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">練習次數</th>
                                        <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">日期時間</th>
                                        <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">正確率/分數</th>
                                        {lessonGroup.activityType === 'reading_assessment' && (
                                          <>
                                            <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">語速</th>
                                            <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">正確字/分</th>
                                          </>
                                        )}
                                        <th className="text-left py-2 px-3 text-sm font-semibold text-gray-700">操作</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {lessonGroup.attempts.map((attempt, index) => (
                                        <tr key={attempt.id} className={`${index % 2 === 0 ? "bg-gray-50/50" : "bg-white"} hover:bg-teal-50/50 transition-colors`}>
                                          <td className="py-3 px-3">
                                            <Badge variant="outline">第 {attempt.attempt_number} 次</Badge>
                                          </td>
                                          <td className="py-3 px-3 text-sm text-gray-600">
                                            {format(new Date(attempt.date), "MM-dd HH:mm", { locale: zhCN })}
                                          </td>
                                          <td className="py-3 px-3">
                                            <span className={`font-semibold ${
                                              attempt.accuracy_percentage >= 90 ? 'text-green-600' : 
                                              attempt.accuracy_percentage >= 70 ? 'text-yellow-600' : 'text-red-600'
                                            }`}>
                                              {attempt.accuracy_percentage.toFixed(1)}%
                                            </span>
                                          </td>
                                          {lessonGroup.activityType === 'reading_assessment' && (
                                            <>
                                              <td className="py-3 px-3 text-gray-700 font-medium">
                                                {Math.round(attempt.words_per_minute)} 字/分
                                              </td>
                                              <td className="py-3 px-3 text-teal-700 font-medium">
                                                {Math.round(attempt.correct_wpm)}
                                              </td>
                                            </>
                                          )}
                                          <td className="py-3 px-3">
                                            <DialogTrigger asChild>
                                              <Button variant="outline" size="sm" onClick={() => setSelectedRecord(attempt)}>
                                                <Eye className="w-4 h-4 mr-2" />
                                                查看詳情
                                              </Button>
                                            </DialogTrigger>
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              }
            </CardContent>
          </Card>
        </div>
      </div>
      
      <DialogContent className="max-w-4xl w-[95vw] h-[95vh] max-h-[95vh] flex flex-col p-0 gap-0">
        {selectedRecord && (
          <>
            <div className="flex-shrink-0 p-4 md:p-6 border-b bg-white">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <DialogTitle className="text-lg md:text-xl font-bold leading-tight">
                    {selectedRecord.lessonTitle} - {selectedRecord.title}
                  </DialogTitle>
                  {isTeacherView && (
                    <p className="text-sm text-gray-600 mt-1">
                      學生: {targetStudentEmail}
                    </p>
                  )}
                  <div className="flex items-center gap-2 mt-2">
                      <Badge className={
                          selectedRecord.activityType === 'reading_assessment' ? 'bg-yellow-100 text-yellow-800' :
                          selectedRecord.activityType === 'listening_cloze' ? 'bg-blue-100 text-blue-800' :
                          selectedRecord.activityType === 'sentence_making' ? 'bg-purple-100 text-purple-800' :
                          selectedRecord.activityType === 'speaking_practice' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                      }>
                          {selectedRecord.activityType === 'speaking_practice' ? '🎤 錄音練習' :
                            selectedRecord.activityType === 'listening_cloze' ? '🎧 聽力克漏字' :
                            selectedRecord.activityType === 'sentence_making' ? '✍️ 造句練習' :
                            selectedRecord.activityType === 'reading_assessment' ? '💬 朗讀練習' :
                            '📚 練習'}
                      </Badge>
                  </div>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => setSelectedRecord(null)}
                  className="flex-shrink-0 w-8 h-8 p-0 hover:bg-gray-100 rounded-full"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
            
            <div className="flex-1 overflow-auto p-4 md:p-6">
              <UnifiedResultsDisplay 
                  session={selectedRecord} 
                  targets={{
                      target_wpm: selectedRecord.target_wpm || 230,
                      target_accuracy: selectedRecord.target_accuracy || 85,
                      set_by_teacher: true
                  }}
                  activityType={selectedRecord.activityType}
              />
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
