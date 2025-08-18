
import React, { useState, useEffect, useCallback } from "react";
import { User } from "@/api/entities";
import { Course } from "@/api/entities";
import { Lesson } from "@/api/entities";
import { StudentProgress } from "@/api/entities";
import { TeacherNotification } from "@/api/entities";
import { Class } from "@/api/entities";
import { ClassCourseMapping } from "@/api/entities";
import { ClassStudent } from "@/api/entities";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Users, BookOpen, TrendingUp, Download, Plus, Settings, Eye, Pencil, Archive, ArchiveRestore, Bell, AlertTriangle, Edit, Trash2, Save, X, Search, Target, FileText, BarChart3, Clock, Mic, Headphones, Quote, MessageCircle, PenSquare } from "lucide-react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { createPageUrl } from "@/utils";
import { Label } from "@/components/ui/label";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";

import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogClose, DialogDescription } from "@/components/ui/dialog";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";


import ClassManagement from "../components/teacher/ClassManagement";
import ClassPerformanceOverview from "../components/teacher/ClassPerformanceOverview";
import ResultsDisplay from "../components/assessment/ResultsDisplay";

// 輔助函式，用於正確地從多個來源獲取目標值，並正確處理 0
const getTargetValue = (studentValue, lessonValue, courseValue, defaultValue) => {
    if (studentValue !== null && studentValue !== undefined) return studentValue;
    if (lessonValue !== null && lessonValue !== undefined) return lessonValue;
    if (courseValue !== null && courseValue !== undefined) return courseValue;
    return defaultValue;
};


export default function TeacherDashboard() {
  const [user, setUser] = useState(null);
  const [courses, setCourses] = useState([]);
  const [allClasses, setAllClasses] = useState([]);
  const [mappings, setMappings] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewLessonForm, setShowNewLessonForm] = useState(false);
  const [showNewCourseForm, setShowNewCourseForm] = useState(false);
  const [editingLesson, setEditingLesson] = useState(null);
  const [editingCourse, setEditingCourse] = useState(null);
  const [courseSearchTerm, setCourseSearchTerm] = useState("");
  const [showLinkerModal, setShowLinkerModal] = useState(false);
  const [linkingCourse, setLinkingCourse] = useState(null);
  const [showActivitySelector, setShowActivitySelector] = useState(false);
  
  // 新增狀態：用於通知詳情 Modal
  const [selectedNotification, setSelectedNotification] = useState(null);
  const [notificationDetail, setNotificationDetail] = useState(null); // Fixed syntax error here
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    loadBasicData();
  }, []);

  // 簡化的資料載入，只載入必要的基本資料
  const loadBasicData = async () => {
    setLoading(true);
    try {
      console.log("開始載入基本資料...");
      
      const userResult = await User.me().catch(e => { console.log("使用者未登入，使用 POC 模式"); return null; });
      setUser(userResult);

      if (!userResult) {
          setLoading(false);
          // If no user, ensure states are cleared or defaulted
          setUser(null);
          setCourses([]);
          setNotifications([]);
          setAllClasses([]);
          setMappings([]);
          console.log("使用者未登入，停止載入。");
          return;
      }

      console.log(`當前登入老師 email: ${userResult.email}`);

      // Use Promise.all to fetch all necessary data concurrently
      const [coursesData, classesData, mappingsData] = await Promise.all([
        Course.list().catch(e => { console.error("載入課程失敗:", e); return []; }),
        Class.list().catch(e => { console.error("載入班級失敗:", e); return []; }),
        ClassCourseMapping.list().catch(e => { console.error("載入關聯失敗:", e); return []; })
      ]);
      
      // 修正：使用 teacher_email 過濾通知
      console.log("開始載入通知資料...");
      const notificationsData = await TeacherNotification.filter({ teacher_email: userResult.email }, '-created_date').catch(e => { 
        console.error("載入通知失敗:", e); 
        return []; 
      });
      console.log(`找到 ${notificationsData.length} 筆通知記錄`);

      setCourses(Array.isArray(coursesData) ? coursesData : []);
      setAllClasses(Array.isArray(classesData) ? classesData : []);
      setNotifications(Array.isArray(notificationsData) ? notificationsData : []);
      setMappings(Array.isArray(mappingsData) ? mappingsData : []);
      
    } catch (error) {
      console.error("載入基本資料失敗:", error);
      // Ensure all states are cleared or set to default in case of a high-level error
      setUser(null);
      setCourses([]);
      setNotifications([]);
      setAllClasses([]);
      setMappings([]);
    } finally {
      setLoading(false);
      console.log("基本資料載入完成");
    }
  };

  // Function to refresh mappings from the backend
  const refreshMappings = async () => {
      try {
          const mappingsData = await ClassCourseMapping.list();
          setMappings(Array.isArray(mappingsData) ? mappingsData : []);
      } catch (e) {
          console.error("刷新關聯失敗:", e);
          setMappings([]);
      }
  };

  // 單獨載入課程相關資料
  const loadCourseData = async (courseId) => {
    if (!courseId) {
      setLessons([]);
      return;
    }
    
    try {
      console.log("載入課程資料:", courseId);
      const lessonsData = await Lesson.filter({ course_id: courseId }, "lesson_number");
      setLessons(Array.isArray(lessonsData) ? lessonsData : []);
      console.log("課文載入成功，數量:", Array.isArray(lessonsData) ? lessonsData.length : 0);
    } catch (error) {
      console.error("載入課文失敗:", error);
      setLessons([]);
    }
  };

  const handleStartNewLesson = (activityType) => {
    setEditingLesson(null); // Ensure not in edit mode
    setShowActivitySelector(false); // Close selector
    setShowNewLessonForm(true); // Open form
  
    // Pre-populate form data for a new lesson based on new LessonForm structure
    setEditingLesson({ 
      activity_type: activityType, 
      title: '',
      content: '', // For speaking_practice / listening_cloze
      description: '', // For speaking_practice / listening_cloze
      lesson_number: (lessons.length > 0 ? Math.max(...lessons.map(l => l.lesson_number || 0)) : 0) + 1, // Keep for sequencing
      difficulty_level: 'A1', // New default
      scenario_details: { time: '', place: '', context: '', ai_role: '' }, // New field for speaking_scenario
      // New fields for listening_cloze
      cloze_text: '',
      answer_options: [],
      // New fields for sentence_making
      prompt_text: '',
      example_sentences: [],
      target_word: '',
      image_url: '',
    });
  };

  const createNewCourse = async (courseData) => {
    try {
      console.log("建立新課程:", courseData);
      const newCourse = await Course.create({
        ...courseData,
        teacher_id: user ? user.id : 'poc_teacher'
      });
      setCourses(prev => [newCourse, ...prev]);
      setSelectedCourse(newCourse);
      setLessons([]);
      setShowNewCourseForm(false);
      console.log("新課程建立成功");
    } catch (error) {
      console.error("創建課程失敗:", error);
      alert("創建課程失敗，請重試");
    }
  };

  const handleUpdateCourse = async (courseId, courseData) => {
    try {
      const updatedCourse = await Course.update(courseId, courseData);
      setCourses(courses.map(c => c.id === courseId ? updatedCourse : c));
      if (selectedCourse?.id === courseId) {
        setSelectedCourse(updatedCourse);
      }
      setEditingCourse(null);
    } catch (error) {
      console.error("更新課程失敗:", error);
      alert("更新課程失敗，請重試");
    }
  };

  const handleDeleteCourse = async (courseId) => {
    if (window.confirm("您確定要刪除這個課程嗎？這將同時刪除課程內的所有課文與所有關聯班級，此操作無法復原。")) {
      try {
        const courseLessons = await Lesson.filter({ course_id: courseId });
        await Promise.all(courseLessons.map(lesson => Lesson.delete(lesson.id)));
        
        const courseMappings = mappings.filter(m => m.course_id === courseId);
        await Promise.all(courseMappings.map(mapping => ClassCourseMapping.delete(mapping.id)));
        await Course.delete(courseId);
        
        setCourses(courses.filter(c => c.id !== courseId));
        setMappings(prev => prev.filter(m => m.course_id !== courseId));
        if (selectedCourse?.id === courseId) {
          const remainingCourses = courses.filter(c => c.id !== courseId);
          setSelectedCourse(remainingCourses.length > 0 ? remainingCourses[0] : null);
          setLessons([]);
        }
      } catch (error) {
        console.error("刪除課程失敗:", error);
        alert("刪除課程失敗，請重試");
      }
    }
  };

  const createNewLesson = async (lessonData) => {
    if (!selectedCourse) {
      alert("請先選擇或創建一個課程");
      return;
    }

    try {
      const newLesson = await Lesson.create({
        ...lessonData,
        course_id: selectedCourse.id,
        is_active: true
      });
      setLessons(prev => [...prev, newLesson].sort((a,b) => (a.lesson_number || Infinity) - (b.lesson_number || Infinity)));
      setShowNewLessonForm(false);
      setEditingLesson(null);
    } catch (error) {
      console.error("創建課文失敗:", error);
      alert("創建課文失敗，請重試");
    }
  };

  const handleUpdateLesson = async (lessonId, lessonData) => {
    try {
        const updatedLesson = await Lesson.update(lessonId, lessonData);
        setLessons(lessons.map(l => l.id === lessonId ? updatedLesson : l));
        setEditingLesson(null);
    } catch(error) {
        console.error("更新課文失敗:", error);
        alert("更新失敗，請重試");
    }
  };

  const handleDeleteLesson = async (lessonId) => {
    if (window.confirm("您確定要刪除這篇課文嗎？此操作無法復原。")) {
      try {
        await Lesson.delete(lessonId);
        setLessons(lessons.filter(l => l.id !== lessonId));
      } catch (error) {
        console.error("刪除課文失敗:", error);
        alert("刪除課文失敗，請重試");
      }
    }
  };

  const toggleLessonStatus = async (lesson) => {
      try {
        await Lesson.update(lesson.id, { is_active: !lesson.is_active });
        setLessons(lessons.map(l => l.id === lesson.id ? {...l, is_active: !lesson.is_active} : l));
      } catch(error) {
          console.error("更新課文狀態失敗:", error);
          alert("更新失敗，請重試");
      }
  };

  const filteredCourses = courses.filter(c =>
    c.title.toLowerCase().includes(courseSearchTerm.toLowerCase())
  );

  // 新增功能：載入通知詳情
  const loadNotificationDetail = async (notification) => {
    if (!notification || !notification.student_progress_id) {
      console.warn("Attempted to load detail for notification without student_progress_id:", notification);
      return;
    }
    
    setLoadingDetail(true);
    setSelectedNotification(notification);
    
    try {
        console.log('[TeacherDashboard] 載入通知詳情，通知內容:', notification);
        console.log('[TeacherDashboard] 通知中的學生email:', notification.student_email);
        
        // 修正：同步獲取必要資料
        const [progress, lesson, studentClass] = await Promise.all([
            StudentProgress.get(notification.student_progress_id),
            Lesson.get(notification.lesson_id),
            Class.get(notification.class_id)
        ]);

        if (!progress || !lesson || !studentClass) {
            throw new Error("無法獲取完整的通知詳情資料。");
        }
        
        console.log('[TeacherDashboard] 載入的練習記錄:', progress);
        console.log('[TeacherDashboard] 練習記錄中的學生email:', progress.student_email);
        
        // 修正：使用通知中的 student_email，並從 ClassStudent 中查找學生資料
        const studentEmail = notification.student_email;
        console.log('[TeacherDashboard] 將使用的學生email:', studentEmail);
        
        const allClassStudents = await ClassStudent.list(); // 獲取所有班級學生資料
        const studentUser = allClassStudents.find(cs => cs.email === studentEmail); // 根據 email 查找學生資料
        
        console.log('[TeacherDashboard] 找到的學生資料:', studentUser);
        
        if (!studentUser) {
            throw new Error(`找不到 email 為 ${studentEmail} 的學生資料`);
        }

        const course = await Course.get(lesson.course_id);
        if (!course) {
            throw new Error("無法獲取課程資料");
        }

        // 修正：使用與後端相同的輔助函式來建立目標標準
        const target_wpm = getTargetValue(studentUser.target_wpm, lesson.target_wpm, course.default_target_wpm, 150);
        const target_accuracy = getTargetValue(studentUser.target_accuracy, lesson.target_accuracy, course.default_target_accuracy, 85);

        setNotificationDetail({
            progress,
            student: studentUser, // 確保使用正確的學生資料 (來自 ClassStudent)
            lesson,
            class: studentClass,
            targets: {
                target_wpm,
                target_accuracy,
                set_by_teacher: true
            }
        });
        
        // 將通知標為已讀
        if (!notification.is_read) {
            await TeacherNotification.update(notification.id, { is_read: true });
            // 更新前端狀態
            setNotifications(prev => prev.map(n => n.id === notification.id ? {...n, is_read: true} : n));
        }

    } catch (error) {
        console.error("載入通知詳情失敗:", error);
        alert("無法載入詳細資訊，請稍後再試。");
        setSelectedNotification(null);
        setNotificationDetail(null);
    } finally {
        setLoadingDetail(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">載入教師管理台...</p>
        </div>
      </div>
    );
  }

  const unreadNotifications = notifications.filter(n => !n.is_read);

  return (
    <div className="p-4 md:p-6 min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-6 md:mb-8 gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">教師管理台</h1>
            <p className="text-gray-600">管理課程內容與學生學習進度</p>
          </div>

          {unreadNotifications.length > 0 && (
            <div className="relative">
              <Button variant="outline" className="relative gap-2" onClick={() => { /* Trigger notification modal or navigate to tab */ }}>
                <Bell className="w-4 h-4" />
                通知
                <Badge variant="destructive" className="absolute -top-2 -right-2 w-5 h-5 rounded-full p-0 flex items-center justify-center text-xs">
                  {unreadNotifications.length}
                </Badge>
              </Button>
            </div>
          )}
        </div>

        <Tabs defaultValue="lessons" className="w-full">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-2 mb-6 md:mb-8">
            <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 bg-transparent gap-1 h-auto p-0">
              <TabsTrigger 
                value="lessons" 
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-teal-500 data-[state=active]:to-blue-500 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=active]:scale-[1.02] text-gray-600 hover:text-gray-900 hover:bg-gray-100/50 transition-all duration-200 rounded-xl py-3 px-4 text-sm md:text-base font-medium"
              >
                <div className="flex flex-col items-center gap-1">
                  <BookOpen className="w-4 h-4 md:w-5 md:h-5" />
                  <span>課程管理</span>
                </div>
              </TabsTrigger>
              <TabsTrigger 
                value="students" 
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-teal-500 data-[state=active]:to-blue-500 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=active]:scale-[1.02] text-gray-600 hover:text-gray-900 hover:bg-gray-100/50 transition-all duration-200 rounded-xl py-3 px-4 text-sm md:text-base font-medium"
              >
                <div className="flex flex-col items-center gap-1">
                  <Users className="w-4 h-4 md:w-5 md:h-5" />
                  <span>班師生</span>
                </div>
              </TabsTrigger>
              <TabsTrigger 
                value="performance" 
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-teal-500 data-[state=active]:to-blue-500 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=active]:scale-[1.02] text-gray-600 hover:text-gray-900 hover:bg-gray-100/50 transition-all duration-200 rounded-xl py-3 px-4 text-sm md:text-base font-medium"
              >
                <div className="flex flex-col items-center gap-1">
                  <BarChart3 className="w-4 h-4 md:w-5 md:h-5" />
                  <span>班級表現</span>
                </div>
              </TabsTrigger>
              <TabsTrigger 
                value="notifications" 
                className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-teal-500 data-[state=active]:to-blue-500 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=active]:scale-[1.02] text-gray-600 hover:text-gray-900 hover:bg-gray-100/50 transition-all duration-200 rounded-xl py-3 px-4 text-sm md:text-base font-medium relative"
              >
                <div className="flex flex-col items-center gap-1">
                  <div className="relative">
                    <Bell className="w-4 h-4 md:w-5 md:h-5" />
                    {unreadNotifications.length > 0 && (
                      <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></div>
                    )}
                  </div>
                  <span>通知中心</span>
                </div>
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="lessons" className="mt-0">
            <div className="md:hidden space-y-6">
              <Card className="glass-effect border-0 shadow-lg rounded-2xl overflow-hidden">
                <CardHeader className="pb-4 bg-gradient-to-r from-teal-50 to-blue-50">
                  <div className="flex flex-col gap-4">
                    <div className="flex justify-between items-center">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-r from-teal-500 to-blue-500 rounded-lg flex items-center justify-center">
                          <BookOpen className="w-4 h-4 text-white" />
                        </div>
                        課程列表
                      </CardTitle>
                      <Button onClick={() => setShowNewCourseForm(true)} size="sm" className="gradient-bg text-white shadow-lg hover:scale-105 transition-transform">
                        <Plus className="w-4 h-4 mr-1" />
                        新增
                      </Button>
                    </div>
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                      <Input 
                        placeholder="搜尋課程..." 
                        className="pl-10 h-10 border-0 bg-white/50 backdrop-blur-sm rounded-xl"
                        onChange={(e) => setCourseSearchTerm(e.target.value)}
                        value={courseSearchTerm}
                      />
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0 max-h-60 overflow-y-auto">
                  {filteredCourses.length === 0 && courseSearchTerm === '' ? (
                    <div className="p-6 text-center">
                      <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-500 text-sm mb-4">尚未建立任何課程</p>
                      <Button onClick={() => setShowNewCourseForm(true)} className="gradient-bg text-white" size="sm">
                        <Plus className="w-4 h-4 mr-2" />
                        建立第一個課程
                      </Button>
                    </div>
                  ) : filteredCourses.length === 0 && courseSearchTerm !== '' ? (
                    <div className="p-6 text-center text-gray-500">
                      <p>找不到符合「{courseSearchTerm}」的課程。</p>
                    </div>
                  ) : (
                    <div className="space-y-2 p-4">
                      {filteredCourses.map(course => (
                        <div
                          key={course.id}
                          className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                            selectedCourse?.id === course.id 
                              ? 'bg-teal-50 border-teal-200 ring-2 ring-teal-500' 
                              : 'bg-white border-gray-200 hover:bg-gray-50'
                          }`}
                          onClick={() => {
                            if (editingCourse?.id !== course.id) {
                                setSelectedCourse(course);
                                loadCourseData(course.id);
                                setShowNewLessonForm(false);
                                setEditingLesson(null);
                                setEditingCourse(null);
                            }
                          }}
                        >
                          {editingCourse?.id === course.id ? (
                            <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
                                <Input
                                    value={editingCourse.title}
                                    onChange={(e) => setEditingCourse({...editingCourse, title: e.target.value})}
                                    className="text-sm"
                                    autoFocus
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            handleUpdateCourse(editingCourse.id, { title: editingCourse.title });
                                        }
                                        if (e.key === 'Escape') {
                                            setEditingCourse(null);
                                        }
                                    }}
                                />
                                <div className="flex gap-1">
                                    <Button size="sm" onClick={(e) => {
                                        e.stopPropagation();
                                        handleUpdateCourse(editingCourse.id, { title: editingCourse.title });
                                    }} className="h-7 text-xs">
                                        <Save className="w-3 h-3 mr-1" /> 儲存
                                    </Button>
                                    <Button size="sm" variant="outline" onClick={(e) => {
                                        e.stopPropagation();
                                        setEditingCourse(null);
                                    }} className="h-7 text-xs">
                                        <X className="w-3 h-3 mr-1" /> 取消
                                    </Button>
                                </div>
                            </div>
                        ) : (
                            <div className="flex justify-between items-start">
                              <div className="flex-1 min-w-0">
                                <h3 className="font-semibold text-sm text-gray-900 truncate">{course.title}</h3>
                                <div className="flex flex-col gap-1 mt-1">
                                  <p className="text-xs text-gray-500">
                                    建立於 {format(new Date(course.created_date), "MM-dd")}
                                  </p>
                                  <Badge variant="secondary" className="w-fit text-xs">
                                    {mappings.filter(m => m.course_id === course.id).length} 個班級已關聯
                                  </Badge>
                                </div>
                              </div>
                              <div className="flex flex-col gap-1 ml-2">
                                <div className="flex gap-1">
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setEditingCourse(course);
                                    }}
                                    className="h-6 w-6 p-0 hover:bg-blue-100"
                                  >
                                    <Edit className="w-3 h-3" />
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDeleteCourse(course.id);
                                    }}
                                    className="h-6 w-6 p-0 hover:bg-red-100 text-red-600"
                                  >
                                    <Trash2 className="w-3 h-3" />
                                  </Button>
                                </div>
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setLinkingCourse(course);
                                    setShowLinkerModal(true);
                                  }} 
                                  className="h-6 text-xs px-2"
                                >
                                  管理班級
                                </Button>
                              </div>
                            </div>
                            )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="glass-effect border-0 shadow-lg rounded-2xl overflow-hidden">
                <CardHeader className="pb-4 bg-gradient-to-r from-blue-50 to-indigo-50">
                  <div className="flex justify-between items-center">
                        <div className="min-w-0 flex-1">
                          <CardTitle className="text-lg truncate flex items-center gap-2">
                            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-lg flex items-center justify-center">
                              <FileText className="w-4 h-4 text-white" />
                            </div>
                            {selectedCourse ? `${selectedCourse.title}` : '請選擇課程'}
                          </CardTitle>
                          {selectedCourse && (
                            <p className="text-sm text-gray-600 mt-1 ml-10">
                              共 {lessons.length} 篇活動
                            </p>
                          )}
                        </div>
                        {selectedCourse && (
                          <Button onClick={() => setShowActivitySelector(true)} className="gradient-bg text-white shadow-lg hover:scale-105 transition-transform" size="sm">
                            <Plus className="w-4 h-4 mr-1" />
                            新增
                          </Button>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="p-0 max-h-96 overflow-y-auto">
                      {!selectedCourse ? (
                        <div className="p-8 text-center">
                          <Target className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">選擇課程開始管理</h3>
                          <p className="text-gray-600 text-sm">從上方課程列表中選擇一個課程來查看和管理活動</p>
                        </div>
                      ) : (
                        <div className="p-4 space-y-4">
                          {showNewLessonForm && (
                            <div className="mb-6 p-4 border rounded-lg bg-teal-50/50">
                              <h3 className="text-lg font-semibold mb-4">新增活動</h3>
                              <LessonForm
                                initialData={editingLesson}
                                onSubmit={createNewLesson}
                                onCancel={() => { setShowNewLessonForm(false); setEditingLesson(null); }}
                                submitText="創建活動"
                              />
                            </div>
                          )}

                          {lessons.length === 0 && !showNewLessonForm ? (
                            <div className="text-center py-12">
                              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                              <h3 className="text-lg font-semibold text-gray-900 mb-2">此課程尚未有活動</h3>
                              <p className="text-gray-600 mb-6 text-sm">點擊「新增活動」創建第一個活動</p>
                              <Button onClick={() => setShowActivitySelector(true)} className="gradient-bg text-white">
                                <Plus className="w-4 h-4 mr-2" />
                                新增活動
                              </Button>
                            </div>
                          ) : (
                            lessons.map(lesson => (
                              <div key={lesson.id}>
                                {editingLesson?.id === lesson.id ? (
                                  <div className="p-4 border rounded-lg bg-teal-50/50">
                                    <h3 className="text-lg font-semibold mb-4">編輯活動</h3>
                                    <LessonForm
                                      initialData={editingLesson}
                                      onSubmit={(data) => handleUpdateLesson(lesson.id, data)}
                                      onCancel={() => setEditingLesson(null)}
                                      submitText="儲存變更"
                                    />
                                  </div>
                                ) : (
                                  <MobileLessonCard
                                    lesson={lesson}
                                    onEdit={() => setEditingLesson(lesson)}
                                    onDelete={() => handleDeleteLesson(lesson.id)}
                                    onToggleStatus={() => toggleLessonStatus(lesson)}
                                  />
                                )}
                              </div>
                            ))
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                <div className="hidden md:flex h-[calc(100vh-200px)] gap-6">
                  <div className="w-1/3 flex flex-col">
                    <Card className="glass-effect border-0 shadow-lg h-full flex flex-col">
                      <CardHeader className="pb-4">
                        <div className="flex justify-between items-center mb-2">
                          <CardTitle className="text-lg">課程列表</CardTitle>
                          <Button onClick={() => setShowNewCourseForm(true)} size="sm" className="gradient-bg text-white">
                            <Plus className="w-4 h-4 mr-1" />
                            新增課程
                          </Button>
                        </div>
                        <div className="relative">
                          <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                          <Input 
                            placeholder="搜尋課程..." 
                            className="pl-10 h-8"
                            onChange={(e) => setCourseSearchTerm(e.target.value)}
                            value={courseSearchTerm}
                          />
                        </div>
                      </CardHeader>
                      <CardContent className="flex-1 overflow-y-auto p-0">
                        {filteredCourses.length === 0 && courseSearchTerm === '' ? (
                          <div className="p-6 text-center">
                            <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                            <p className="text-gray-500 text-sm">尚未建立任何課程</p>
                            <Button onClick={() => setShowNewCourseForm(true)} className="mt-4 gradient-bg text-white" size="sm">
                              <Plus className="w-4 h-4 mr-2" />
                              建立第一個課程
                            </Button>
                          </div>
                        ) : filteredCourses.length === 0 && courseSearchTerm !== '' ? (
                          <div className="p-6 text-center text-gray-500">
                            <p>找不到符合「{courseSearchTerm}」的課程。</p>
                          </div>
                        ) : (
                          <div className="space-y-2 p-4">
                            {filteredCourses.map(course => (
                              <CourseListItem 
                                key={course.id} 
                                course={course}
                                isSelected={selectedCourse?.id === course.id}
                                onSelect={() => {
                                  setSelectedCourse(course);
                                  loadCourseData(course.id);
                                  setShowNewLessonForm(false);
                                  setEditingLesson(null);
                                }}
                                onEdit={handleUpdateCourse}
                                onDelete={handleDeleteCourse}
                                mappings={mappings}
                                onManageLinks={() => {
                                    setLinkingCourse(course);
                                    setShowLinkerModal(true);
                                }}
                              />
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>

                  <div className="w-2/3 flex flex-col">
                    <Card className="glass-effect border-0 shadow-lg h-full flex flex-col">
                      <CardHeader className="pb-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <CardTitle className="text-lg">
                              {selectedCourse ? `${selectedCourse.title} - 活動管理` : '請選擇課程'}
                            </CardTitle>
                            {selectedCourse && (
                              <p className="text-sm text-gray-600 mt-1">
                                共 {lessons.length} 篇活動
                              </p>
                            )}
                          </div>
                          {selectedCourse && (
                            <Button onClick={() => setShowActivitySelector(true)} className="gradient-bg text-white" size="sm">
                              <Plus className="w-4 h-4 mr-2" />
                              新增活動
                            </Button>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent className="flex-1 overflow-y-auto p-0">
                        {!selectedCourse ? (
                          <div className="p-8 text-center">
                            <Target className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">選擇課程開始管理</h3>
                            <p className="text-gray-600">從左側課程列表中選擇一個課程來查看和管理活動</p>
                          </div>
                        ) : (
                          <div className="p-4 space-y-4">
                            {showNewLessonForm && (
                              <div className="mb-6 p-4 border rounded-lg bg-teal-50/50">
                                <h3 className="text-lg font-semibold mb-4">新增活動</h3>
                                <LessonForm
                                  initialData={editingLesson}
                                  onSubmit={createNewLesson}
                                  onCancel={() => {setShowNewLessonForm(false); setEditingLesson(null);}}
                                  submitText="創建活動"
                                />
                              </div>
                            )}

                            {lessons.length === 0 && !showNewLessonForm ? (
                              <div className="text-center py-12">
                                <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">此課程尚未有活動</h3>
                                <p className="text-gray-600 mb-6">點擊「新增活動」創建第一個活動</p>
                                <Button onClick={() => setShowActivitySelector(true)} className="gradient-bg text-white">
                                  <Plus className="w-4 h-4 mr-2" />
                                  新增活動
                                </Button>
                              </div>
                            ) : (
                              lessons.map(lesson => (
                                <div key={lesson.id}>
                                  {editingLesson?.id === lesson.id ? (
                                    <div className="p-4 border rounded-lg bg-teal-50/50">
                                      <h3 className="text-lg font-semibold mb-4">編輯活動</h3>
                                      <LessonForm
                                        initialData={editingLesson}
                                        onSubmit={(data) => handleUpdateLesson(lesson.id, data)}
                                        onCancel={() => setEditingLesson(null)}
                                        submitText="儲存變更"
                                      />
                                    </div>
                                  ) : (
                                    <LessonCard
                                      lesson={lesson}
                                      onEdit={() => setEditingLesson(lesson)}
                                      onDelete={() => handleDeleteLesson(lesson.id)}
                                      onToggleStatus={() => toggleLessonStatus(lesson)}
                                    />
                                  )}
                                </div>
                              ))
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {showNewCourseForm && (
                  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <Card className="w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
                      <CardHeader className="bg-gradient-to-r from-teal-500 to-blue-500 text-white">
                        <div className="flex justify-between items-center">
                          <CardTitle className="flex items-center gap-2">
                            <Plus className="w-5 h-5" />
                            建立新課程
                          </CardTitle>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => setShowNewCourseForm(false)}
                            className="text-white hover:bg-white/20"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="p-6">
                        <NewCourseForm onSubmit={createNewCourse} onCancel={() => setShowNewCourseForm(false)} />
                      </CardContent>
                    </Card>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="students" className="mt-8">
                <div className="space-y-6">
                  <Card className="glass-effect border-0 shadow-lg">
                    <CardHeader>
                      <CardTitle>班師生管理</CardTitle>
                      <p className="text-sm text-gray-600">管理學生資料、個人標準設定與課程關聯</p>
                    </CardHeader>
                    <CardContent>
                      <ClassManagement 
                        allCourses={courses}
                        mappings={mappings}
                        onUpdateMappings={refreshMappings}
                      />
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="performance" className="mt-8">
                <Card className="glass-effect border-0 shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="w-5 h-5" />
                      班級表現總覽
                    </CardTitle>
                    <p className="text-sm text-gray-600">查看全班學生在各課文的朗讀表現狀況</p>
                  </CardHeader>
                  <CardContent>
                    <ClassPerformanceOverview 
                      allClasses={allClasses}
                      allCourses={courses}
                      mappings={mappings}
                    />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="notifications" className="mt-8">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Bell className="w-5 h-5" />
                      通知中心
                      {unreadNotifications.length > 0 && (
                        <Badge variant="destructive">{unreadNotifications.length} 未讀</Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {notifications.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        目前沒有任何通知
                      </div>
                    ) : (
                      <div className="space-y-3">
                          {notifications.map(notification => (
                            <div
                              key={notification.id}
                              className={`p-4 rounded-lg border ${
                                notification.is_read ? 'bg-gray-50/50 border-gray-200' : 'bg-yellow-50 border-yellow-300 shadow-sm'
                              }`}
                            >
                              <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-2">
                                    <AlertTriangle className={`w-4 h-4 ${
                                      notification.severity === 'high' ? 'text-red-500' : 'text-yellow-600'
                                    }`} />
                                    <Badge variant={notification.is_read ? 'outline' : 'destructive'}>
                                      {notification.notification_type === 'not_achieved' ? '未達標提醒' : '系統通知'}
                                    </Badge>
                                    <span className="text-xs text-gray-500">
                                      {format(new Date(notification.created_date), "yyyy-MM-dd HH:mm", { locale: zhCN })}
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-800">{notification.message}</p>
                                </div>
                                {notification.student_progress_id && (
                                  <Button 
                                    variant="outline" 
                                    size="sm" 
                                    onClick={() => loadNotificationDetail(notification)}
                                    disabled={loadingDetail && selectedNotification?.id === notification.id}
                                    className="w-full md:w-auto"
                                  >
                                    {loadingDetail && selectedNotification?.id === notification.id ? "載入中..." : "查看詳情"}
                                  </Button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
            
            {linkingCourse && (
                <CourseClassLinkerModal
                    isOpen={showLinkerModal}
                    onClose={() => { setShowLinkerModal(false); setLinkingCourse(null); }}
                    course={linkingCourse}
                    allClasses={allClasses}
                    existingMappings={mappings}
                    onUpdate={refreshMappings}
                />
            )}
          </div>

          <ActivityTypeSelectionModal
            isOpen={showActivitySelector}
            onClose={() => setShowActivitySelector(false)}
            onSelect={handleStartNewLesson}
          />

          {/* 新增：通知詳情 Modal */}
          <Dialog open={!!selectedNotification} onOpenChange={() => {setSelectedNotification(null); setNotificationDetail(null);}}>
              <DialogContent className="max-w-4xl w-[95vw] h-[95vh] max-h-[95vh] flex flex-col p-0 gap-0">
                  {loadingDetail ? (
                      <div className="flex items-center justify-center h-full">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                      </div>
                  ) : notificationDetail ? (
                      <>
                          <div className="flex-shrink-0 p-4 md:p-6 border-b bg-white">
                              <DialogTitle className="text-lg md:text-xl font-bold leading-tight">
                                  練習詳細報告
                              </DialogTitle>
                              <p className="text-sm text-gray-600 mt-1">
                                  {notificationDetail.student?.student_name || notificationDetail.student?.email} 於「{notificationDetail.lesson.title}」的練習結果
                              </p>
                          </div>
                          <div className="flex-1 overflow-auto p-4 md:p-6">
                              {/* 修正：傳入計算好的目標 */}
                              <ResultsDisplay 
                                  session={notificationDetail.progress} 
                                  targets={notificationDetail.targets} 
                              />
                          </div>
                      </>
                  ) : (
                      <div className="p-6 text-center">無法載入資料</div>
                  )}
              </DialogContent>
          </Dialog>
        </div>
      );
    }

    // 課程列表項目組件 (For desktop view)
    function CourseListItem({ course, isSelected, onSelect, onEdit, onDelete, mappings, onManageLinks }) {
      const [isEditing, setIsEditing] = useState(false);
      const [editData, setEditData] = useState(course);

      const handleSave = (e) => {
        e.stopPropagation();
        if (!editData.title.trim()) {
          alert("課程標題不能為空。");
          return;
        }
        onEdit(course.id, {title: editData.title});
        setIsEditing(false);
      };

      const handleCancel = (e) => {
        e.stopPropagation();
        setEditData(course);
        setIsEditing(false);
      };
      
      const linkedClassesCount = mappings.filter(m => m.course_id === course.id).length;

      return (
        <div 
          className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
            isSelected 
              ? 'bg-teal-50 border-teal-200 ring-2 ring-teal-500' 
              : 'bg-white border-gray-200 hover:bg-gray-50'
          }`}
          onClick={!isEditing ? onSelect : undefined}
        >
          {isEditing ? (
            <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
              <Input
                value={editData.title}
                onChange={(e) => setEditData({...editData, title: e.target.value})}
                className="text-sm"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSave(e);
                  if (e.key === 'Escape') handleCancel(e);
                }}
              />
              <div className="flex gap-1">
                <Button size="sm" onClick={handleSave} className="h-7 text-xs">
                  <Save className="w-3 h-3 mr-1" /> 儲存
                </Button>
                <Button size="sm" variant="outline" onClick={handleCancel} className="h-7 text-xs">
                  <X className="w-3 h-3 mr-1" /> 取消
                </Button>
              </div>
            </div>
          ) : (
            <>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-sm text-gray-900 truncate">{course.title}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-xs text-gray-500">
                        建立於 {format(new Date(course.created_date), "MM-dd")}
                    </p>
                    <Badge variant="secondary">{linkedClassesCount} 個班級已關聯</Badge>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1 ml-2" onClick={(e) => e.stopPropagation()}>
                   <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setIsEditing(true)}
                          className="h-7 w-7 p-0 hover:bg-blue-100"
                        >
                          <Edit className="w-3 h-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => onDelete(course.id)}
                          className="h-7 w-7 p-0 hover:bg-red-100 text-red-600"
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                    </div>
                    <Button size="sm" variant="outline" onClick={onManageLinks} className="h-7 text-xs">
                        管理班級
                    </Button>
                </div>
              </div>
            </>
          )}
        </div>
      );
    }

    // 課程關聯班級 Modal 組件
    function CourseClassLinkerModal({ isOpen, onClose, course, allClasses, existingMappings, onUpdate }) {
        const [selectedClassIds, setSelectedClassIds] = useState(new Set());
        const [isSaving, setIsSaving] = useState(false);

        useEffect(() => {
            if (course && isOpen) {
                const currentLinkedIds = existingMappings
                    .filter(m => m.course_id === course.id)
                    .map(m => m.class_id);
                setSelectedClassIds(new Set(currentLinkedIds));
            }
        }, [course, existingMappings, isOpen]);

        const handleToggleClass = (classId) => {
            const newSelection = new Set(selectedClassIds);
            if (newSelection.has(classId)) {
                newSelection.delete(classId);
            } else {
                newSelection.add(classId);
            }
            setSelectedClassIds(newSelection);
        };

        const handleSave = async () => {
            setIsSaving(true);
            try {
                const originalIds = new Set(existingMappings.filter(m => m.course_id === course.id).map(m => m.class_id));
                
                const idsToAdd = [...selectedClassIds].filter(id => !originalIds.has(id));
                const idsToRemove = [...originalIds].filter(id => !selectedClassIds.has(id));

                const creationPromises = idsToAdd.map(class_id => ClassCourseMapping.create({ course_id: course.id, class_id }));
                
                const deletionPromises = idsToRemove.map(class_id => {
                    const mappingToDelete = existingMappings.find(m => m.course_id === course.id && m.class_id === class_id);
                    return mappingToDelete ? ClassCourseMapping.delete(mappingToDelete.id) : Promise.resolve();
                });

                await Promise.all([...creationPromises, ...deletionPromises]);
                await onUpdate();
                onClose();

            } catch (error) {
                console.error("儲存班級關聯失敗:", error);
                alert("儲存失敗，請重試");
            } finally {
                setIsSaving(false);
            }
        };

        if (!isOpen || !course) return null;

        return (
            <Dialog open={isOpen} onOpenChange={onClose}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>管理「{course.title}」的班級關聯</DialogTitle>
                    </DialogHeader>
                    <div className="py-4 max-h-[60vh] overflow-y-auto">
                        <div className="space-y-2">
                            {allClasses.length === 0 ? (
                                <p className="text-gray-500 text-center">目前沒有可用的班級。</p>
                            ) : (
                                allClasses.map(cls => (
                                    <div key={cls.id} className="flex items-center space-x-3 p-2 rounded-md hover:bg-gray-100">
                                        <Checkbox
                                            id={`class-${cls.id}`}
                                            checked={selectedClassIds.has(cls.id)}
                                            onCheckedChange={() => handleToggleClass(cls.id)}
                                        />
                                        <label
                                            htmlFor={`class-${cls.id}`}
                                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex-grow cursor-pointer"
                                        >
                                            {cls.class_name}
                                        </label>
                                        {cls.difficulty_level && (
                                            <Badge variant="secondary" className="font-mono text-xs">{cls.difficulty_level}</Badge>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                    <DialogFooter>
                        <DialogClose asChild>
                            <Button type="button" variant="secondary">取消</Button>
                        </DialogClose>
                        <Button onClick={handleSave} disabled={isSaving}>
                            {isSaving ? "儲存中..." : "儲存變更"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        );
    }

    // 新課程表單組件
    function NewCourseForm({ onSubmit, onCancel }) {
      const [formData, setFormData] = useState({
        title: '',
        description: ''
      });

      const handleSubmit = (e) => {
        e.preventDefault();
        if (!formData.title.trim()) {
          alert("課程標題不能為空。");
          return;
        }
        onSubmit(formData);
      };

      return (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Label htmlFor="new-course-title">課程標題</Label>
          <Input
            id="new-course-title"
            placeholder="課程標題 (例如：英文打字初級班)"
            value={formData.title}
            onChange={(e) => setFormData({...formData, title: e.target.value})}
            required
          />
          <Label htmlFor="new-course-description">課程描述 (選填)</Label>
          <Textarea
            id="new-course-description"
            placeholder="課程描述 (選填)"
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            rows={3}
          />
          <div className="flex gap-2">
            <Button type="submit" className="gradient-bg text-white">創建課程</Button>
            <Button type="button" variant="outline" onClick={onCancel}>取消</Button>
          </div>
        </form>
      );
    }

    // Reusable Lesson Form Component
    function LessonForm({ onSubmit, onCancel, initialData, submitText }) {
      
      // Helper to create a complete and safe initial state
      const getInitialState = (data) => {
        const defaults = {
            title: '',
            content: '', // For reading_assessment / speaking_practice / listening_cloze
            description: '', // For reading_assessment / speaking_practice / listening_cloze
            lesson_number: 1, 
            difficulty_level: 'A1',
            activity_type: 'reading_assessment', // **修正：預設為朗讀練習**
            scenario_details: { time: '', place: '', context: '', ai_role: '' }, // For speaking_scenario
            cloze_text: '', // For listening_cloze
            answer_options: [], // For listening_cloze
            prompt_text: '', // For sentence_making
            example_sentences: [], // For sentence_making
            target_word: '', // For sentence_making
            image_url: '', // For sentence_making (if applicable)
            time_limit_minutes: 5, // Default for time-limited activities
            target_wpm: 150, // Default for reading assessment
            target_accuracy: 85, // Default for reading assessment
        };
        const mergedData = { ...defaults, ...data };
        if (!mergedData.scenario_details) {
            mergedData.scenario_details = defaults.scenario_details;
        }
        if (!mergedData.answer_options) { // Ensure answer_options is an array
            mergedData.answer_options = [];
        }
        if (!mergedData.example_sentences) { // Ensure example_sentences is an array
            mergedData.example_sentences = [];
        }
        return mergedData;
      };

      const [formData, setFormData] = useState(getInitialState(initialData));
      const classLevels = ["preA", "A1", "A2", "B1", "B2", "C1", "C2"];

      useEffect(() => {
        // When initialData changes (e.e., user selects a different lesson to edit),
        // reset the form state with the new data, ensuring it's complete.
        setFormData(getInitialState(initialData));
      }, [initialData]);

      const handleSubmit = (e) => {
        e.preventDefault();
        if (!formData.title.trim()) {
            alert("標題不能為空。");
            return;
        }

        const dataToSubmit = { ...formData };

        // Clean up fields based on activity_type
        switch (dataToSubmit.activity_type) {
            case 'speaking_practice':
            case 'reading_assessment': 
                delete dataToSubmit.scenario_details;
                delete dataToSubmit.cloze_text;
                delete dataToSubmit.answer_options;
                delete dataToSubmit.prompt_text;
                delete dataToSubmit.example_sentences;
                delete dataToSubmit.target_word;
                delete dataToSubmit.image_url;
                // target_wpm and target_accuracy should only exist for reading_assessment, 
                // so if speaking_practice, ensure they are removed.
                if (dataToSubmit.activity_type === 'speaking_practice') {
                    delete dataToSubmit.target_wpm;
                    delete dataToSubmit.target_accuracy;
                }
                break;
            case 'speaking_scenario':
                delete dataToSubmit.content;
                delete dataToSubmit.description;
                delete dataToSubmit.cloze_text;
                delete dataToSubmit.answer_options;
                delete dataToSubmit.prompt_text;
                delete dataToSubmit.example_sentences;
                delete dataToSubmit.target_word;
                delete dataToSubmit.image_url;
                delete dataToSubmit.target_wpm;
                delete dataToSubmit.target_accuracy;
                delete dataToSubmit.time_limit_minutes;
                break;
            case 'listening_cloze':
                delete dataToSubmit.content; // It has cloze_text instead
                delete dataToSubmit.description; // Not typically used for cloze
                delete dataToSubmit.scenario_details;
                delete dataToSubmit.prompt_text;
                delete dataToSubmit.example_sentences;
                delete dataToSubmit.target_word;
                delete dataToSubmit.image_url;
                delete dataToSubmit.target_wpm;
                delete dataToSubmit.target_accuracy;
                break;
            case 'sentence_making':
                delete dataToSubmit.content;
                delete dataToSubmit.description;
                delete dataToSubmit.scenario_details;
                delete dataToSubmit.cloze_text;
                delete dataToSubmit.answer_options;
                delete dataToSubmit.target_wpm;
                delete dataToSubmit.target_accuracy;
                delete dataToSubmit.time_limit_minutes;
                break;
            default:
                // For any other types, keep all fields or add specific cleanup
                break;
        }

        onSubmit(dataToSubmit);
      };
      
      return (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <Label>活動類型</Label>
            <Select value={formData.activity_type} onValueChange={value => setFormData({...formData, activity_type: value})}>
                <SelectTrigger><SelectValue/></SelectTrigger>
                <SelectContent>
                    <SelectItem value="reading_assessment">朗讀練習</SelectItem> 
                    <SelectItem value="speaking_practice">錄音集</SelectItem>
                    <SelectItem value="speaking_scenario">口說情境集</SelectItem>
                    <SelectItem value="listening_cloze">聽力克漏字</SelectItem>
                    <SelectItem value="sentence_making">造句集</SelectItem>
                </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
                <Label htmlFor="lesson-title">標題*</Label>
                <Input id="lesson-title" value={formData.title} onChange={(e) => setFormData({...formData, title: e.target.value})} required />
            </div>
            <div>
                <Label htmlFor="difficulty-level">級數*</Label>
                <Select value={formData.difficulty_level} onValueChange={value => setFormData({...formData, difficulty_level: value})}>
                    <SelectTrigger><SelectValue/></SelectTrigger>
                    <SelectContent>
                        {classLevels.map(level => <SelectItem key={level} value={level}>{level}</SelectItem>)}
                    </SelectContent>
                </Select>
            </div>
          </div>

          {(formData.activity_type === 'reading_assessment' || formData.activity_type === 'speaking_practice') && (
            <>
                <div>
                    <Label htmlFor="lesson-content">文本 (3-15句)*</Label>
                    <Textarea id="lesson-content" value={formData.content} onChange={(e) => setFormData({...formData, content: e.target.value})} rows={5} required />
                </div>
                <div>
                    <Label htmlFor="lesson-description">文本翻譯或說明</Label>
                    <Textarea id="lesson-description" value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} rows={3} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <Label htmlFor="time-limit-minutes">時間限制 (分鐘)</Label>
                        <Input id="time-limit-minutes" type="number" value={formData.time_limit_minutes} onChange={e => setFormData({...formData, time_limit_minutes: parseInt(e.target.value) || 0})} />
                    </div>
                    {formData.activity_type === 'reading_assessment' && (
                        <>
                            <div>
                                <Label htmlFor="target-wpm">目標字數/分鐘 (WPM)</Label>
                                <Input id="target-wpm" type="number" value={formData.target_wpm} onChange={e => setFormData({...formData, target_wpm: parseInt(e.target.value) || 0})} />
                            </div>
                            <div>
                                <Label htmlFor="target-accuracy">目標準確率 (%)</Label>
                                <Input id="target-accuracy" type="number" value={formData.target_accuracy} onChange={e => setFormData({...formData, target_accuracy: parseInt(e.target.value) || 0})} />
                            </div>
                        </>
                    )}
                </div>
            </>
          )}

          {formData.activity_type === 'speaking_scenario' && (
            <div className="space-y-4 p-4 border rounded-lg bg-indigo-50">
                <h4 className="font-semibold text-indigo-800">口說集情境設定</h4>
                <div className="grid grid-cols-2 gap-4">
                     <div>
                        <Label htmlFor="scenario-time">時間*</Label>
                        <Input id="scenario-time" value={formData.scenario_details.time} onChange={e => setFormData({...formData, scenario_details: {...formData.scenario_details, time: e.target.value}})} required />
                    </div>
                    <div>
                        <Label htmlFor="scenario-place">地點*</Label>
                        <Input id="scenario-place" value={formData.scenario_details.place} onChange={e => setFormData({...formData, scenario_details: {...formData.scenario_details, place: e.target.value}})} required />
                    </div>
                </div>
                 <div>
                    <Label htmlFor="scenario-context">情境*</Label>
                    <Textarea id="scenario-context" value={formData.scenario_details.context} onChange={e => setFormData({...formData, scenario_details: {...formData.scenario_details, context: e.target.value}})} rows={3} required />
                </div>
                 <div>
                    <Label htmlFor="scenario-ai-role">AI角色*</Label>
                    <Input id="scenario-ai-role" value={formData.scenario_details.ai_role} onChange={e => setFormData({...formData, scenario_details: {...formData.scenario_details, ai_role: e.target.value}})} required />
                </div>
            </div>
          )}

          {formData.activity_type === 'listening_cloze' && (
            <div className="space-y-4 p-4 border rounded-lg bg-amber-50">
                <h4 className="font-semibold text-amber-800">聽力克漏字設定</h4>
                <div>
                    <Label htmlFor="cloze-text">克漏字文本* (用 [___] 標記需要填空的單字)</Label>
                    <Textarea id="cloze-text" value={formData.cloze_text} onChange={e => setFormData({...formData, cloze_text: e.target.value})} rows={5} required />
                </div>
                {/* 動態新增答案選項 */}
                <div>
                    <Label>答案選項 (每個選項一行)</Label>
                    <Textarea
                        value={formData.answer_options.join('\n')}
                        onChange={e => setFormData({...formData, answer_options: e.target.value.split('\n')})}
                        rows={3}
                        placeholder="例如：&#10;apple&#10;banana&#10;orange"
                    />
                </div>
            </div>
          )}

          {formData.activity_type === 'sentence_making' && (
            <div className="space-y-4 p-4 border rounded-lg bg-indigo-50">
                <h4 className="font-semibold text-indigo-800">造句集設定</h4>
                <div>
                    <Label htmlFor="prompt-text">提示文字/圖片描述*</Label>
                    <Textarea id="prompt-text" value={formData.prompt_text} onChange={e => setFormData({...formData, prompt_text: e.target.value})} rows={3} required />
                </div>
                <div>
                    <Label htmlFor="target-word">目標單字 (選填)</Label>
                    <Input id="target-word" value={formData.target_word} onChange={e => setFormData({...formData, target_word: e.target.value})} />
                </div>
                <div>
                    <Label htmlFor="example-sentences">範例句子 (每個句子一行)</Label>
                    <Textarea
                        id="example-sentences"
                        value={formData.example_sentences.join('\n')}
                        onChange={e => setFormData({...formData, example_sentences: e.target.value.split('\n')})}
                        rows={3}
                        placeholder="例如：&#10;This is an example sentence.&#10;Another example here."
                    />
                </div>
                <div>
                    <Label htmlFor="image-url">圖片網址 (選填)</Label>
                    <Input id="image-url" value={formData.image_url} onChange={e => setFormData({...formData, image_url: e.target.value})} />
                </div>
            </div>
          )}
          
          <div className="flex gap-2">
            <Button type="submit" className="gradient-bg text-white">{submitText}</Button>
            <Button type="button" variant="outline" onClick={onCancel}>取消</Button>
          </div>
        </form>
      );
    }

    // 課文卡片組件 (For desktop view)
    function LessonCard({ lesson, onEdit, onDelete, onToggleStatus }) {
      const activityTypeMap = {
        reading_assessment: { label: '朗讀練習', color: 'bg-yellow-100 text-yellow-800' },
        speaking_practice: { label: '錄音集', color: 'bg-green-100 text-green-800' }, 
        listening_cloze: { label: '聽力克漏字', color: 'bg-blue-100 text-blue-800' },
        sentence_making: { label: '造句集', color: 'bg-indigo-100 text-indigo-800' },
        speaking_scenario: { label: '口說情境', color: 'bg-purple-100 text-purple-800' }, 
      };
      const currentActivity = activityTypeMap[lesson.activity_type] || activityTypeMap.reading_assessment; 

      return (
        <Card className={`transition-opacity ${!lesson.is_active ? 'opacity-60' : ''}`}>
          <CardContent className="p-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="font-bold text-lg">{lesson.title}</h3>
                  <Badge className={currentActivity.color}>{currentActivity.label}</Badge>
                  {!lesson.is_active && <Badge variant="destructive">已封存</Badge>}
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                  {lesson.time_limit_minutes > 0 && <span>時間限制: {lesson.time_limit_minutes} 分鐘</span>} 
                  {lesson.activity_type === 'reading_assessment' && (
                    <>
                      <span>目標: {lesson.target_wpm || 'N/A'} 字/分</span>
                      <span>字數: {lesson.content?.length || 0}</span>
                    </>
                  )}
                  <Badge>{lesson.difficulty_level}</Badge>
                </div>
                {lesson.activity_type === 'speaking_practice' && lesson.content && (
                  <p className="text-sm text-gray-700 line-clamp-2 mb-3">
                    {lesson.content.substring(0, 100)}...
                  </p>
                )}
                {lesson.activity_type === 'speaking_scenario' && lesson.scenario_details && (
                    <div className="text-sm text-gray-700 mb-3">
                        <p><strong>時間:</strong> {lesson.scenario_details.time}</p>
                        <p><strong>地點:</strong> {lesson.scenario_details.place}</p>
                        <p><strong>情境:</strong> {lesson.scenario_details.context}</p>
                        <p><strong>AI角色:</strong> {lesson.scenario_details.ai_role}</p>
                    </div>
                )}
                {lesson.activity_type === 'listening_cloze' && lesson.cloze_text && (
                    <p className="text-sm text-gray-700 line-clamp-2 mb-3">
                        {lesson.cloze_text.substring(0, 100)}...
                    </p>
                )}
                {lesson.activity_type === 'sentence_making' && lesson.prompt_text && (
                    <p className="text-sm text-gray-700 line-clamp-2 mb-3">
                        <strong>提示:</strong> {lesson.prompt_text.substring(0, 100)}...
                    </p>
                )}
              </div>
              <div className="flex items-center gap-2 ml-4">
                <Button variant="outline" size="sm" onClick={onEdit} className="gap-1">
                  <Pencil className="w-3 h-3" /> 編輯
                </Button>
                <Button
                  variant={lesson.is_active ? "secondary" : "default"}
                  size="sm"
                  onClick={onToggleStatus}
                  className={`gap-1 ${!lesson.is_active ? 'gradient-bg text-white' : ''}`}
                >
                  {lesson.is_active ? (
                    <><Archive className="w-3 h-3" /> 封存</>
                  ) : (
                    <><ArchiveRestore className="w-3 h-3" /> 取消封存</>
                  )}
                </Button>
                <Button variant="destructive" size="sm" onClick={onDelete} className="gap-1">
                  <Trash2 className="w-3 h-3" /> 刪除
                </Button>
                <Link to={createPageUrl(`StudentPractice?lesson_id=${lesson.id}`)}>
                  <Button variant="outline" size="sm" className="gap-1">
                    <Eye className="w-3 h-3" /> 試用
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    // 新增：手機版課文卡片組件
    function MobileLessonCard({ lesson, onEdit, onDelete, onToggleStatus }) {
      const activityTypeMap = {
        reading_assessment: { label: '朗讀練習', color: 'bg-yellow-100 text-yellow-800' },
        speaking_practice: { label: '錄音集', color: 'bg-green-100 text-green-800' }, 
        listening_cloze: { label: '聽力克漏字', color: 'bg-blue-100 text-blue-800' },
        sentence_making: { label: '造句集', color: 'bg-indigo-100 text-indigo-800' },
        speaking_scenario: { label: '口說情境', color: 'bg-purple-100 text-purple-800' }, 
      };
      const currentActivity = activityTypeMap[lesson.activity_type] || activityTypeMap.reading_assessment; 

      return (
        <Card className={`transition-opacity ${!lesson.is_active ? 'opacity-60' : ''}`}>
          <CardContent className="p-4">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="font-bold text-base truncate">{lesson.title}</h3>
                  <div className="flex flex-wrap gap-1 mt-1">
                    <Badge className={currentActivity.color}>{currentActivity.label}</Badge>
                    {!lesson.is_active && <Badge variant="destructive" className="mt-1">已封存</Badge>}
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-sm">
                {lesson.time_limit_minutes > 0 && (
                    <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-gray-500" />
                    <span className="text-gray-600">{lesson.time_limit_minutes}分鐘</span>
                    </div>
                )}
                {lesson.activity_type === 'reading_assessment' && (
                    <>
                    <div className="flex items-center gap-1">
                      <Target className="w-3 h-3 text-gray-500" />
                      <span className="text-gray-600">{lesson.target_wpm || 'N/A'}字/分</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <FileText className="w-3 h-3 text-gray-500" />
                      <span className="text-gray-600">{lesson.content?.length || 0}字</span>
                    </div>
                    </>
                )}
                <Badge className="w-fit">{lesson.difficulty_level}</Badge>
              </div>
              
              {lesson.activity_type === 'speaking_practice' && lesson.content && (
                <p className="text-sm text-gray-700 line-clamp-2">
                  {lesson.content.substring(0, 50)}...
                </p>
              )}
              {lesson.activity_type === 'speaking_scenario' && lesson.scenario_details && (
                    <div className="text-sm text-gray-700 line-clamp-2">
                        <p><strong>情境:</strong> {lesson.scenario_details.context}</p>
                    </div>
                )}
              {lesson.activity_type === 'listening_cloze' && lesson.cloze_text && (
                <p className="text-sm text-gray-700 line-clamp-2">
                  {lesson.cloze_text.substring(0, 50)}...
                </p>
              )}
              {lesson.activity_type === 'sentence_making' && lesson.prompt_text && (
                <p className="text-sm text-gray-700 line-clamp-2">
                  <strong>提示:</strong> {lesson.prompt_text.substring(0, 50)}...
                </p>
              )}
              
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm" onClick={onEdit} className="flex-1">
                  <Pencil className="w-3 h-3 mr-1" /> 編輯
                </Button>
                <Button
                  variant={lesson.is_active ? "secondary" : "default"}
                  size="sm"
                  onClick={onToggleStatus}
                  className={`flex-1 ${!lesson.is_active ? 'gradient-bg text-white' : ''}`}
                >
                  {lesson.is_active ? (
                    <><Archive className="w-3 h-3 mr-1" /> 封存</>
                  ) : (
                    <><ArchiveRestore className="w-3 h-3 mr-1" /> 取消封存</>
                  )}
                </Button>
              </div>
              
              <div className="flex gap-2">
                <Button variant="destructive" size="sm" onClick={onDelete} className="flex-1">
                  <Trash2 className="w-3 h-3 mr-1" /> 刪除
                </Button>
                <Link to={createPageUrl(`StudentPractice?lesson_id=${lesson.id}`)} className="flex-1">
                  <Button variant="outline" size="sm" className="w-full">
                    <Eye className="w-3 h-3 mr-1" /> 試用
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    // 新增：活動類型選擇 Modal
    function ActivityTypeSelectionModal({ isOpen, onClose, onSelect }) {
      const activityTypes = [
        { key: 'reading_assessment', title: '朗讀練習', description: '提供文本，學生進行朗讀練習，AI會針對發音準確度、流利度、語速進行評分與回饋。', icon: Mic, iconBg: 'bg-yellow-500' }, 
        { key: 'speaking_practice', title: '錄音集', description: '提供文本，學生可進行跟讀錄音，AI會針對文本發音、流利度、完整度給予評分與回饋。', icon: Mic, iconBg: 'bg-green-500' }, 
        { key: 'speaking_scenario', title: '口說情境', description: '建立互動情境，AI將扮演特定角色，與學生進行多輪對話練習，提升實戰口說能力。', icon: MessageCircle, iconBg: 'bg-blue-500' },
        { key: 'listening_cloze', title: '聽力克漏字', description: '學生聆聽句子後，填寫遺漏的單字或片語，訓練聽力與拼寫能力。', icon: Headphones, iconBg: 'bg-amber-500' },
        { key: 'sentence_making', title: '造句集', description: '提供關鍵字或圖片，讓學生發揮創意造句，並由 AI 評估語法正確性。', icon: PenSquare, iconBg: 'bg-indigo-500' }
      ];

      return (
        <Dialog open={isOpen} onOpenChange={onClose}>
          <DialogContent className="max-w-4xl p-0">
            <DialogHeader className="p-6 pb-4" style={{ background: 'linear-gradient(to right, #8A2BE2, #4B0082)', color: 'white', borderRadius: '8px 8px 0 0' }}>
              <DialogTitle className="text-2xl font-bold">新增活動</DialogTitle>
              <DialogDescription className="text-purple-200">請選擇您想為學生建立的活動類型</DialogDescription>
            </DialogHeader>
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              {activityTypes.map((type) => (
                <div
                  key={type.key}
                  onClick={() => onSelect(type.key)}
                  className="group p-6 border rounded-xl hover:shadow-xl hover:border-purple-300 hover:scale-[1.02] transition-all duration-250 cursor-pointer"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-white ${type.iconBg}`}>
                      <type.icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 group-hover:text-purple-700">{type.title}</h3>
                    </div>
                  </div>
                  <p className="text-gray-600 mt-3 text-sm">{type.description}</p>
                </div>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      );
    }
