
import React, { useState, useEffect } from 'react';
import { Course } from '@/api/entities';
import { Lesson } from '@/api/entities';
import { Class } from '@/api/entities';
import { ClassStudent } from '@/api/entities';
import { ClassCourseMapping } from '@/api/entities';
import { User } from '@/api/entities';
import { ActivityResult } from '@/api/entities';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BookText, ArrowRight, Clock, Target, BookOpen, Sparkles, GraduationCap } from 'lucide-react';
import { motion } from 'framer-motion';

export default function StudentDashboard() {
    const [courses, setCourses] = useState([]);
    const [lessonsByCourse, setLessonsByCourse] = useState({});
    const [loading, setLoading] = useState(true);
    const [studentClass, setStudentClass] = useState(null); // This holds the Class object
    const [user, setUser] = useState(null);
    const [progress, setProgress] = useState({});
    const [error, setError] = useState(null);
    const [currentStudent, setCurrentStudent] = useState(null); // Added this state to hold the ClassStudent object
    const [isTeacherPreview, setIsTeacherPreview] = useState(false); // **新增**：用於識別教師預覽模式

    useEffect(() => {
        loadStudentData();
    }, []);

    const loadStudentData = async () => {
        setLoading(true);
        setError(null);
        try {
            // **核心修正：直接使用 User.me() 獲取當前用戶**
            const targetUser = await User.me();
            console.log('[StudentDashboard] 當前登入用戶:', targetUser);
            
            if (!targetUser?.email) {
                console.log('[StudentDashboard] 用戶 email 不可用，停止載入');
                throw new Error('無法獲取用戶資料'); // Throw error to be caught below
            }
            setUser(targetUser);
            console.log('[StudentDashboard] 設定用戶成功，email:', targetUser.email);

            if (targetUser.role !== 'student') {
                // --- 教師預覽模式 ---
                setIsTeacherPreview(true);
                console.log('[StudentDashboard] Teacher preview mode activated for:', targetUser.email);
                
                // 獲取老師創建的所有班級
                console.log(`[StudentDashboard] 載入教師的班級，由 ${targetUser.email} 創建...`);
                const teacherClasses = await Class.filter({ created_by: targetUser.email });
                
                if (!teacherClasses || teacherClasses.length === 0) {
                    console.log('[StudentDashboard] 老師沒有建立任何班級。');
                    setCourses([]);
                    setLessonsByCourse({});
                    setProgress({}); // 預覽模式沒有進度
                    setLoading(false);
                    return; // 老師沒有建立任何班級
                }
                const teacherClassIds = teacherClasses.map(c => c.id);
                console.log('[StudentDashboard] 老師的班級 ID:', teacherClassIds);

                // 獲取這些班級關聯的所有課程映射
                console.log('[StudentDashboard] 載入課程映射...');
                const courseMappings = await ClassCourseMapping.filter({ class_id: { $in: teacherClassIds } });
                const courseIds = [...new Set(courseMappings.map(m => m.course_id))]; // 去重
                console.log('[StudentDashboard] 提取的課程 ID 列表 (教師預覽):', courseIds);

                if (courseIds.length === 0) {
                    console.log('[StudentDashboard] 老師的班級沒有關聯任何課程。');
                    setCourses([]);
                    setLessonsByCourse({});
                    setProgress({});
                    setLoading(false);
                    return; // 班級沒有關聯任何課程
                }

                // 載入所有相關課程和課文
                console.log('[StudentDashboard] 載入課程和課文 (教師預覽)...');
                const [allCourses, allLessons] = await Promise.all([
                    Course.filter({ id: { $in: courseIds }, is_active: true }),
                    Lesson.filter({ course_id: { $in: courseIds }, is_active: true }, "lesson_number"),
                ]);
                
                console.log('[StudentDashboard] 載入的課程數量 (教師預覽):', allCourses.length);
                console.log('[StudentDashboard] 載入的課文數量 (教師預覽):', allLessons.length);

                setCourses(allCourses);
                const lessonsMap = allLessons.reduce((acc, lesson) => {
                    if (!acc[lesson.course_id]) acc[lesson.course_id] = [];
                    acc[lesson.course_id].push(lesson);
                    return acc;
                }, {});
                setLessonsByCourse(lessonsMap);
                setProgress({}); // 預覽模式沒有進度
                console.log('[StudentDashboard] 教師預覽模式資料載入完成。');

            } else {
                // --- 學生模式 ---
                setIsTeacherPreview(false);
                console.log('[StudentDashboard] Student mode activated for:', targetUser.email);
                
                let studentClassEntity = null; // This will hold the ClassStudent entity for the current user

                // **核心修正：根據用戶角色載入資料**
                console.log('[StudentDashboard] 步驟1: 載入學生班級關聯...');
                if (targetUser.role === 'student' && targetUser.student_id) {
                    console.log(`[StudentDashboard] 用戶是學生，嘗試透過 student_id: ${targetUser.student_id} 獲取班級學生資料`);
                    studentClassEntity = await ClassStudent.get(targetUser.student_id);
                } else {
                    // 為了向後兼容，嘗試通過 email 查找
                    console.log(`[StudentDashboard] 用戶不是學生或無 student_id，嘗試透過 email: ${targetUser.email} 獲取班級學生資料`);
                    const students = await ClassStudent.filter({ email: targetUser.email });
                    if (students && students.length > 0) {
                        studentClassEntity = students[0];
                    }
                }
                
                setCurrentStudent(studentClassEntity); // Set the new `currentStudent` state

                if (!studentClassEntity) {
                    console.log('[StudentDashboard] 學生未加入任何班級或找不到記錄，清空狀態');
                    setStudentClass(null);
                    setCourses([]);
                    setLessonsByCourse({});
                    setProgress({});
                    setLoading(false);
                    return;
                }

                console.log('[StudentDashboard] 找到學生的班級學生實體:', studentClassEntity);
                const classId = studentClassEntity.class_id;
                console.log('[StudentDashboard] 找到班級 ID:', classId);
                
                const classDetails = await Class.get(classId);
                console.log('[StudentDashboard] 班級詳細資料:', classDetails);
                setStudentClass(classDetails);

                console.log('[StudentDashboard] 步驟2: 用班級 ID 查找課程關聯 -', classId);
                const courseMappings = await ClassCourseMapping.filter({ class_id: classId });
                console.log('[StudentDashboard] ClassCourseMapping 查詢結果:', courseMappings);
                
                const courseIds = courseMappings.map(m => m.course_id);
                console.log('[StudentDashboard] 提取的課程 ID 列表:', courseIds);

                if (courseIds.length === 0) {
                    console.log('[StudentDashboard] 班級沒有關聯任何課程，清空狀態');
                    setCourses([]);
                    setLessonsByCourse({});
                    setProgress({});
                    setLoading(false);
                    return;
                }

                console.log('[StudentDashboard] 步驟3: 載入課程、課文和作業資料...');
                const [allCourses, allLessons] = await Promise.all([
                    Course.filter({ id: { $in: courseIds }, is_active: true }),
                    Lesson.filter({ course_id: { $in: courseIds }, is_active: true }, "lesson_number"),
                ]);
                console.log('[StudentDashboard] 載入的課程數量:', allCourses.length);
                console.log('[StudentDashboard] 課程詳細資料:', allCourses);
                console.log('[StudentDashboard] 載入的課文數量:', allLessons.length);
                console.log('[StudentDashboard] 課文詳細資料:', allLessons);

                setCourses(allCourses);

                const lessonsMap = allLessons.reduce((acc, lesson) => {
                    if (!acc[lesson.course_id]) {
                        acc[lesson.course_id] = [];
                    }
                    acc[lesson.course_id].push(lesson);
                    return acc;
                }, {});
                console.log('[StudentDashboard] 課文按課程分組結果:', lessonsMap);
                setLessonsByCourse(lessonsMap);

                const lessonIds = allLessons.map(l => l.id);
                console.log('[StudentDashboard] 步驟4: 載入練習記錄，課文 ID 列表:', lessonIds);
                
                if (lessonIds.length > 0) {
                    console.log('[StudentDashboard] 開始查詢練習記錄...');
                    const allProgressRecords = await ActivityResult.filter({ 
                        lesson_id: { $in: lessonIds }, 
                        student_email: targetUser.email 
                    });
                    
                    console.log('[StudentDashboard] 載入的練習記錄總數:', allProgressRecords.length);
                    console.log('[StudentDashboard] 載入的練習記錄:', allProgressRecords);

                    const progressByLesson = allProgressRecords.reduce((acc, p) => {
                    if (!acc[p.lesson_id]) {
                        acc[p.lesson_id] = [];
                    }
                    acc[p.lesson_id].push(p);
                    return acc;
                    }, {});

                    console.log('[StudentDashboard] 練習記錄按課文分組結果:', progressByLesson);
                    setProgress(progressByLesson);
                } else {
                    console.log('[StudentDashboard] 沒有課文，清空練習記錄');
                    setProgress({});
                }

                console.log('[StudentDashboard] 學生模式資料載入完成');
            }
        } catch (error) {
            console.error("[StudentDashboard] 載入學生資料失敗:", error);
            console.error("[StudentDashboard] 錯誤詳細資訊:", error.message);
            console.error("[StudentDashboard] 錯誤堆疊:", error.stack);
            setError("載入資料失敗，請重新整理頁面或聯繫老師。"); // Updated error message
            setCourses([]);
            setLessonsByCourse({});
            setStudentClass(null);
            setUser(null);
            setProgress({});
            setCurrentStudent(null); // Clear this new state too
            setIsTeacherPreview(false); // Reset teacher preview flag on error
        } finally {
            setLoading(false);
            console.log('[StudentDashboard] 載入狀態設為 false，載入完畢');
        }
    };

    const handleLessonClick = (lesson) => {
        if (!lesson || !lesson.id) {
            console.error("無法開啟練習，因為課文資料不完整:", lesson);
            alert("無法開啟此練習，可能相關的課文已被移除。請聯繫老師。");
            return;
        }

        // For teacher preview, lessons are not meant to be practiced.
        // However, the original outline implies they can still click to see the lesson content.
        // If the intention is to disable interaction for teachers, this part needs modification.
        // For now, assuming teachers can also click to "preview" the activity type link.
        switch (lesson.activity_type) {
            case 'listening_cloze':
                window.location.href = createPageUrl(`ListeningCloze?lesson_id=${lesson.id}`);
                break;
            case 'sentence_making':
                window.location.href = createPageUrl(`SentenceMaking?lesson_id=${lesson.id}`);
                break;
            case 'speaking_practice':
                window.location.href = createPageUrl(`SpeakingPractice?lesson_id=${lesson.id}`);
                break;
            case 'reading_assessment':
            default:
                window.location.href = createPageUrl(`StudentPractice?lesson_id=${lesson.id}`);
                break;
        }
    };

    const getDifficultyColor = (level) => {
        switch (level) {
            case '初級': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
            case '中級': return 'bg-amber-100 text-amber-800 border-amber-200';
            case '高級': return 'bg-rose-100 text-rose-800 border-rose-200';
            default: return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const getDifficultyIcon = (level) => {
        switch (level) {
            case '初級': return '🌱';
            case '中級': return '🌳';
            case '高級': return '🏔️';
            default: return '📚';
        }
    };

    const getActivityIcon = (activityType) => {
        switch (activityType) {
            case 'reading_assessment': return '💬';
            case 'listening_cloze': return '🎧';
            case 'sentence_making': return '✍️';
            case 'speaking_practice': return '🎤';
            default: return '📚';
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
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600 font-medium">載入課程資料中...</p>
                </div>
            </div>
        );
    }
    
    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
                <div className="text-center bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-white/20 p-12 max-w-lg mx-auto">
                    <p className="text-red-600 font-bold text-xl mb-4">錯誤！</p>
                    <p className="text-gray-700 text-lg">{error}</p>
                    <Button onClick={loadStudentData} className="mt-6 bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white font-semibold py-3 rounded-xl transition-all duration-300">
                        重新載入
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
            <div className="max-w-7xl mx-auto px-6 py-8">
                <motion.div 
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-12"
                >
                    <div className="inline-flex items-center gap-4 bg-white/80 backdrop-blur-sm px-6 py-3 rounded-2xl shadow-lg border border-white/20 mb-6">
                        <BookOpen className="w-8 h-8 text-teal-600" />
                        <div className="text-left">
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent">
                                課堂練習
                            </h1>
                            {user && (
                                <p className="text-sm text-gray-700 font-medium mt-1">
                                    {isTeacherPreview ? `教師預覽模式: ${user.full_name}` : `學生: ${user.full_name}`}
                                </p>
                            )}
                        </div>
                        <Sparkles className="w-6 h-6 text-amber-500" />
                    </div>
                    <p className="text-gray-600 text-lg max-w-2xl mx-auto leading-relaxed">
                        在這裡自由探索與練習所有課程內容，為學習增添更多樂趣！🚀
                    </p>
                </motion.div>

                {courses.length === 0 && !loading ? (
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="text-center py-20"
                    >
                        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-white/20 p-12 max-w-lg mx-auto">
                            <div className="w-24 h-24 bg-gradient-to-br from-teal-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                                <BookText className="w-12 h-12 text-teal-600" />
                            </div>
                            <h3 className="text-2xl font-bold text-gray-900 mb-4">
                                {isTeacherPreview 
                                    ? '無可用練習' 
                                    : (studentClass ? '本班級尚無課程' : '您尚未加入任何班級')}
                            </h3>
                            <p className="text-gray-600 text-lg">
                                {isTeacherPreview
                                    ? '請先至教師管理台建立課程並將課程關聯至班級'
                                    : (studentClass ? '請等候老師為您的班級加入課程' : '請聯繫您的老師將您加入班級')}
                            </p>
                        </div>
                    </motion.div>
                ) : (
                    <div className="space-y-12">
                        {courses.length > 0 && (
                            <div className="text-center">
                                 <h2 className="text-2xl font-bold text-gray-800">自主練習區</h2>
                                 <p className="text-gray-500">除了老師指定的作業外，你也可以在這裡自由練習</p>
                            </div>
                        )}
                        
                        {courses.map((course, courseIndex) => {
                            const courseLessons = lessonsByCourse[course.id] || [];
                            if (courseLessons.length === 0) return null;

                            return (
                                <motion.div 
                                    key={course.id}
                                    initial={{ opacity: 0, y: 50 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: courseIndex * 0.1 }}
                                >
                                    <Card className="bg-white/90 backdrop-blur-sm shadow-2xl border-0 rounded-3xl overflow-hidden">
                                        <CardHeader className="bg-gradient-to-r from-teal-500 via-blue-500 to-indigo-500 text-white p-8">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center">
                                                        <BookOpen className="w-8 h-8 text-white" />
                                                    </div>
                                                    <div>
                                                        <CardTitle className="text-3xl font-bold mb-2">{course.title}</CardTitle>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-white/90 text-sm mb-1">共有課文</div>
                                                    <div className="text-3xl font-bold">{courseLessons.length}</div>
                                                    <div className="text-white/80 text-sm">篇</div>
                                                </div>
                                            </div>
                                        </CardHeader>

                                        <CardContent className="p-8">
                                            {/* 手機版：垂直卡片佈局 */}
                                            <div className="grid gap-6 md:hidden">
                                                {courseLessons.map((lesson, lessonIndex) => {
                                                    const lessonProgress = progress[lesson.id] || [];
                                                    const hasProgress = lessonProgress.length > 0;

                                                    return (
                                                        <motion.div
                                                            key={lesson.id}
                                                            initial={{ opacity: 0, y: 20 }}
                                                            animate={{ opacity: 1, y: 0 }}
                                                            transition={{ delay: (courseIndex * 0.1) + (lessonIndex * 0.05) }}
                                                            whileHover={{ y: -5, transition: { duration: 0.2 } }}
                                                        >
                                                            <Card className="group hover:shadow-2xl transition-all duration-300 border border-gray-100 hover:border-teal-200 bg-gradient-to-br from-white to-gray-50/50 rounded-2xl overflow-hidden">
                                                                <CardContent className="p-6">
                                                                    <div className="flex items-start gap-3 mb-4">
                                                                        <div className="w-12 h-12 bg-gradient-to-br from-teal-100 to-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                                                                            <span className="text-2xl">{getActivityIcon(lesson.activity_type)}</span>
                                                                        </div>
                                                                        <div className="flex-1 min-w-0">
                                                                            <h3 className="font-bold text-lg text-gray-900 mb-1 line-clamp-2 group-hover:text-teal-600 transition-colors">
                                                                                {lesson.title}
                                                                            </h3>
                                                                            <div className="text-sm text-gray-500 mb-2">
                                                                                {getActivityLabel(lesson.activity_type)} • 第 {lesson.lesson_number} 課
                                                                            </div>
                                                                        </div>
                                                                        {hasProgress && !isTeacherPreview && (
                                                                            <Badge className="bg-green-100 text-green-800 border-green-200 font-medium px-2 py-1 flex-shrink-0">
                                                                                已練習
                                                                            </Badge>
                                                                        )}
                                                                    </div>

                                                                    <div className="space-y-3 mb-6">
                                                                        <div className="flex items-center justify-between">
                                                                            <Badge className={`${getDifficultyColor(lesson.difficulty_level)} font-medium px-3 py-1`}>
                                                                                {lesson.difficulty_level}
                                                                            </Badge>
                                                                            <div className="flex items-center gap-1 text-sm text-gray-600">
                                                                                <BookText className="w-4 h-4" />
                                                                                <span>{lesson.content?.length || 0} 字</span>
                                                                            </div>
                                                                        </div>
                                                                        
                                                                        <div className="grid grid-cols-2 gap-3 text-sm">
                                                                            <div className="flex items-center gap-2 bg-blue-50 rounded-lg p-2">
                                                                                <Clock className="w-4 h-4 text-blue-600" />
                                                                                <span className="text-blue-800 font-medium">{lesson.time_limit_minutes} 分鐘</span>
                                                                            </div>
                                                                            {lesson.activity_type === 'reading_assessment' && (
                                                                                <div className="flex items-center gap-2 bg-emerald-50 rounded-lg p-2">
                                                                                    <Target className="w-4 h-4 text-emerald-600" />
                                                                                    <span className="text-emerald-800 font-medium">{lesson.target_wpm} 字/分</span>
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                    </div>

                                                                    <Button 
                                                                        onClick={() => handleLessonClick(lesson)}
                                                                        className="w-full bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white font-semibold py-3 rounded-xl transition-all duration-300 transform group-hover:scale-105 shadow-lg hover:shadow-xl"
                                                                    >
                                                                        <span>開始練習</span>
                                                                        <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                                                                    </Button>
                                                                </CardContent>
                                                            </Card>
                                                        </motion.div>
                                                    );
                                                })}
                                            </div>

                                            {/* 桌面版：橫式卡片佈局 */}
                                            <div className="hidden md:block space-y-4">
                                                {courseLessons.map((lesson, lessonIndex) => {
                                                    const lessonProgress = progress[lesson.id] || [];
                                                    const hasProgress = lessonProgress.length > 0;

                                                    return (
                                                        <motion.div
                                                            key={lesson.id}
                                                            initial={{ opacity: 0, x: -20 }}
                                                            animate={{ opacity: 1, x: 0 }}
                                                            transition={{ delay: (courseIndex * 0.1) + (lessonIndex * 0.05) }}
                                                            whileHover={{ x: 5, transition: { duration: 0.2 } }}
                                                        >
                                                            <Card className="group hover:shadow-xl transition-all duration-300 border border-gray-100 hover:border-teal-200 bg-gradient-to-r from-white to-gray-50/30 rounded-2xl overflow-hidden">
                                                                <CardContent className="p-0">
                                                                    <div className="flex items-center">
                                                                        {/* 左側圖標區域 */}
                                                                        <div className="flex-shrink-0 w-24 h-24 bg-gradient-to-br from-teal-100 to-blue-100 flex items-center justify-center">
                                                                            <span className="text-3xl">{getActivityIcon(lesson.activity_type)}</span>
                                                                        </div>
                                                                        
                                                                        {/* 中間內容區域 */}
                                                                        <div className="flex-1 p-6">
                                                                            <div className="flex items-start justify-between mb-3">
                                                                                <div className="flex-1">
                                                                                    <h3 className="font-bold text-xl text-gray-900 mb-1 group-hover:text-teal-600 transition-colors">
                                                                                        {lesson.title}
                                                                                    </h3>
                                                                                    <div className="flex items-center gap-3 text-sm text-gray-500 mb-3">
                                                                                        <span>{getActivityLabel(lesson.activity_type)}</span>
                                                                                        <span>•</span>
                                                                                        <span>第 {lesson.lesson_number} 課</span>
                                                                                    </div>
                                                                                </div>
                                                                                {hasProgress && !isTeacherPreview && (
                                                                                    <Badge className="bg-green-100 text-green-800 border-green-200 font-medium px-3 py-1">
                                                                                        已練習
                                                                                    </Badge>
                                                                                )}
                                                                            </div>
                                                                            
                                                                            <div className="flex items-center gap-6 text-sm">
                                                                                <Badge className={`${getDifficultyColor(lesson.difficulty_level)} font-medium px-3 py-1`}>
                                                                                    {lesson.difficulty_level}
                                                                                </Badge>
                                                                                
                                                                                <div className="flex items-center gap-2 text-gray-600">
                                                                                    <BookText className="w-4 h-4" />
                                                                                    <span>{lesson.content?.length || 0} 字</span>
                                                                                </div>
                                                                                
                                                                                <div className="flex items-center gap-2 text-blue-600">
                                                                                    <Clock className="w-4 h-4" />
                                                                                    <span>{lesson.time_limit_minutes} 分鐘</span>
                                                                                </div>
                                                                                
                                                                                {lesson.activity_type === 'reading_assessment' && (
                                                                                    <div className="flex items-center gap-2 text-emerald-600">
                                                                                        <Target className="w-4 h-4" />
                                                                                        <span>{lesson.target_wpm} 字/分</span>
                                                                                    </div>
                                                                                )}
                                                                            </div>
                                                                        </div>
                                                                        
                                                                        {/* 右側按鈕區域 */}
                                                                        <div className="flex-shrink-0 p-6">
                                                                            <Button 
                                                                                onClick={() => handleLessonClick(lesson)}
                                                                                className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-300 transform group-hover:scale-105 shadow-lg hover:shadow-xl flex items-center gap-2"
                                                                            >
                                                                                <span>開始練習</span>
                                                                                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                                                            </Button>
                                                                        </div>
                                                                    </div>
                                                                </CardContent>
                                                            </Card>
                                                        </motion.div>
                                                    );
                                                })}
                                            </div>
                                        </CardContent>
                                    </Card>
                                </motion.div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
