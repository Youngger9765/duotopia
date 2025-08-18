
import React, { useState, useEffect, useCallback } from 'react';
import { Lesson } from '@/api/entities';
import { User } from '@/api/entities';
import { ActivityResult } from '@/api/entities';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Play, Clock, Target, BookOpen, History, Mic, ListChecks } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { ClassStudent } from '@/api/entities';

// 導入組件
import TextDisplay from '../components/assessment/TextDisplay';
import AudioRecorder from '../components/assessment/AudioRecorder';
import ResultsDisplay from '../components/assessment/ResultsDisplay';
import AttemptButtons from '../components/student/AttemptButtons';
import CongratulationsModal from '../components/student/CongratulationsModal';

export default function StudentPractice() { // Renamed from StudentPracticePage
    const [assessment, setAssessment] = useState(null); // Renamed lesson to assessment
    const [standards, setStandards] = useState(null); // Retained standards state
    const [currentSession, setCurrentSession] = useState(null); // Renamed session to currentSession
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(''); // Initialize error as empty string
    const [currentStep, setCurrentStep] = useState('selection'); // Retained currentStep for internal flow
    const [isProcessing, setIsProcessing] = useState(false);
    const [showConfetti, setShowConfetti] = useState(false); // Retained showConfetti
    const [practiceHistory, setPracticeHistory] = useState([]);
    const [user, setUser] = useState(null);
    const [assignmentId, setAssignmentId] = useState(null);
    const [lessonId, setLessonId] = useState(null); // New state for lessonId from URL

    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const lessonIdParam = urlParams.get('lesson_id');
        const attemptNumber = urlParams.get('attempt');
        const assignmentIdParam = urlParams.get('assignment_id');

        if (!lessonIdParam) {
            setError('找不到練習，缺少課文 ID。請返回並重新選擇。');
            setLoading(false);
            return; // Stop execution if lesson_id is missing
        }

        setLessonId(lessonIdParam);
        if (assignmentIdParam) {
            setAssignmentId(assignmentIdParam);
        }

        const initializePage = async () => {
            try {
                const currentUser = await User.me();
                setUser(currentUser);
                if (!currentUser) {
                    setError('無法載入用戶資訊，請重新登入');
                    setLoading(false);
                    return;
                }
                await loadAssessment(lessonIdParam, attemptNumber, currentUser, assignmentIdParam); // Renamed loadData to loadAssessment
            } catch (err) {
                console.error("初始化頁面失敗:", err);
                setError("初始化頁面失敗：" + err.message);
                setLoading(false);
            }
        };

        initializePage();
    }, []); // Empty dependency array means this runs once on mount

    const loadPracticeHistory = useCallback(async (lessonIdToLoad, currentUser) => {
        if (!lessonIdToLoad || !currentUser?.email) return;
        try {
            const filters = {
                lesson_id: lessonIdToLoad,
                student_email: currentUser.email,
                activity_type: 'reading_assessment',
            };
            
            // 核心修正：根據是否有 assignment_id 來決定篩選條件
            if (assignmentId) {
                // 作業模式：只查詢該特定作業的記錄
                filters.assignment_id = assignmentId;
                console.log('[StudentPractice] 作業模式，篩選條件:', filters);
            } else {
                // 自主練習模式：只查詢沒有 assignment_id 的記錄
                filters.assignment_id = null;
                console.log('[StudentPractice] 自主練習模式，篩選條件:', filters);
            }

            const records = await ActivityResult.filter(filters, "-completed_at");
            console.log('[StudentPractice] 載入的練習記錄數量:', records.length);
            setPracticeHistory(records);
        } catch (error) {
            console.error('載入歷史記錄失敗:', error);
            setError('載入歷史記錄失敗：' + error.message);
        }
    }, [assignmentId]); // 修正：將 assignmentId 加入依賴陣列

    const loadAssessment = async (lessonIdToLoad, attemptNumber = null, currentUser = null, assignmentIdFromURL = null) => { // Renamed loadData to loadAssessment
        setLoading(true);
        setError('');
        
        try {
            const currentLesson = await Lesson.get(lessonIdToLoad);
            if (!currentLesson) {
                setError('找不到指定的課文');
                setLoading(false);
                return;
            }
            
            setAssessment(currentLesson); // Set assessment
            
            // 核心修正：集中處理標準設定
            let finalStandards = {
                target_wpm: currentLesson.target_wpm || 230,
                target_accuracy: currentLesson.target_accuracy || 85,
                set_by_teacher: false
            };

            if (currentUser?.email) {
                try {
                    const studentDataRecords = await ClassStudent.filter({ email: currentUser.email.trim().toLowerCase() });
                    if (studentDataRecords && studentDataRecords.length > 0) {
                        const studentData = studentDataRecords[0];
                        if (studentData.target_wpm || studentData.target_accuracy) {
                            finalStandards = {
                                target_wpm: studentData.target_wpm || currentLesson.target_wpm || 230,
                                target_accuracy: studentData.target_accuracy || currentLesson.target_accuracy || 85,
                                set_by_teacher: true
                            };
                        }
                    }
                } catch (e) {
                    console.error("載入學生個人標準失敗:", e);
                    // 繼續使用課程預設值
                }
            }
            setStandards(finalStandards);
            
            if (currentUser) {
                // **核心修正：在查詢特定練習前，先載入完整歷史記錄**
                await loadPracticeHistory(currentLesson.id, currentUser);
            }

            if (attemptNumber && currentUser) {
                const filters = {
                    student_email: currentUser.email,
                    lesson_id: lessonIdToLoad,
                    attempt_number: parseInt(attemptNumber),
                    activity_type: 'reading_assessment'
                };
                
                // 核心修正：查詢特定練習記錄時也要考慮 assignment_id
                if (assignmentIdFromURL) {
                    filters.assignment_id = assignmentIdFromURL;
                } else {
                    filters.assignment_id = null;
                }

                const progressRecords = await ActivityResult.filter(filters);
                console.log('[StudentPractice] 查詢特定練習記錄:', filters, '結果:', progressRecords.length);

                if (progressRecords.length > 0) {
                    setCurrentSession(progressRecords[0]); // Set currentSession
                    setCurrentStep('results');
                } else {
                    setCurrentStep('selection'); // Fallback to selection if attempt not found
                }
            } else {
                setCurrentStep('selection');
            }
        } catch (error) {
            console.error('載入課文失敗:', error);
            setError('載入課文失敗：' + error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAnalysisComplete = async (analysisResult) => {
        setIsProcessing(true);
        try {
            if (!user?.email) {
                setError('用戶資訊不完整，請重新登入');
                return;
            }

            // 核心修正：計算嘗試次數時也要按 assignment_id 分組
            const filters = {
                lesson_id: assessment.id,
                student_email: user.email,
                activity_type: 'reading_assessment'
            };
            
            if (assignmentId) {
                filters.assignment_id = assignmentId;
            } else {
                filters.assignment_id = null;
            }
            
            const existingAttempts = await ActivityResult.filter(filters);
            console.log('[StudentPractice] 現有嘗試記錄:', existingAttempts.length, '筆');
            
            const maxAttempt = existingAttempts.reduce((max, record) => Math.max(max, record.attempt_number || 0), 0);
            const actualAttemptNumber = maxAttempt + 1;
            console.log('[StudentPractice] 新的嘗試次數:', actualAttemptNumber);

            const newSessionData = {
                student_id: user.id,
                student_email: user.email,
                lesson_id: assessment.id, // Use assessment.id
                assignment_id: assignmentId, // 修正：正確傳遞 assignment_id
                activity_type: 'reading_assessment',
                percentage_score: Number(analysisResult.accuracy_percentage) || 0,
                words_per_minute: Number(analysisResult.words_per_minute) || 0,
                time_spent_seconds: analysisResult.reading_time_seconds || 0,
                audio_url: analysisResult.audio_url,
                transcribed_text: analysisResult.transcribed_text || '',
                punctuated_transcribed_text: analysisResult.punctuated_transcribed_text || '',
                detailed_feedback: analysisResult.detailed_analysis || '',
                annotated_segments: analysisResult.annotated_segments || [],
                completed_at: new Date().toISOString(),
                attempt_number: actualAttemptNumber,
            };

            console.log('[StudentPractice] 準備儲存 ActivityResult 數據:', newSessionData);
            const savedSession = await ActivityResult.create(newSessionData);
            console.log('[StudentPractice] ActivityResult 已儲存, ID:', savedSession.id);
            
            setCurrentSession(savedSession); // Set currentSession
            setCurrentStep('results');
            
            await loadPracticeHistory(assessment.id, user); // Use assessment.id

            const isAchieved = (Number(analysisResult.words_per_minute) || 0) >= standards.target_wpm && 
                              (Number(analysisResult.accuracy_percentage) || 0) >= standards.target_accuracy;
            
            if (isAchieved) {
                setShowConfetti(true);
            }

        } catch (error) {
            console.error('處理錄音失敗:', error);
            setError('處理錄音時發生錯誤，請重試');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleStartPractice = (attemptNum = null) => {
        setCurrentSession(null); // Clear currentSession
        setCurrentStep('practice');
    };

    const handleViewResult = (result) => {
        setCurrentSession(result); // Set currentSession
        setCurrentStep('results');
    };
    
    const handleDebugNotification = () => {
        alert("手動觸發除錯通知（開發者功能）。詳細日誌請查看瀏覽器主控台。");
        console.log("手動觸發通知，當前練習結果:", currentSession); // Use currentSession
    };

    // 核心修正：處理來自子組件的 session 更新
    const handleSessionUpdate = (updatedSession) => {
        console.log('[StudentPractice] 收到 session 更新:', updatedSession);
        setCurrentSession(updatedSession);
        
        // 重要：同時更新歷史記錄中的對應項目
        setPracticeHistory(prevHistory => 
            prevHistory.map(record => 
                record.id === updatedSession.id ? updatedSession : record
            )
        );
        
        // 移除錯誤的 save() 調用 - updatedSession 只是普通物件，不是實體
        // 資料庫更新已經在 ResultsDisplay 組件中完成，這裡不需要再次保存
    };

    // 新增：根據是否為作業模式決定返回頁面
    const getBackUrl = () => {
        return assignmentId ? createPageUrl("Assignments") : createPageUrl("StudentDashboard");
    };

    const getBackLabel = () => {
        return assignmentId ? "返回作業列表" : "返回課程列表";
    };

    // 核心修正：改善錯誤顯示
    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
                <Card className="text-center p-8 shadow-lg">
                    <h2 className="text-2xl font-bold text-red-600 mb-4">發生錯誤</h2>
                    <p className="text-gray-700 text-lg">{error}</p>
                    <Link to={getBackUrl()} className="mt-6 inline-block">
                        <Button className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white font-semibold py-3 rounded-xl">
                            {getBackLabel()}
                        </Button>
                    </Link>
                </Card>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600 font-medium">載入課文資料中...</p>
                </div>
            </div>
        );
    }

    // This block is now mostly redundant because `error` handles missing lesson.
    // However, if `assessment` is null *after* loading without an error (e.g., deleted), this catches it.
    if (!assessment) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
                <div className="text-center bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-white/20 p-12 max-w-lg mx-auto">
                    <p className="text-gray-700 text-xl">找不到指定的課文</p>
                    <Link to={getBackUrl()} className="inline-block mt-6">
                        <Button className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white font-semibold py-3 rounded-xl">
                            {getBackLabel()}
                        </Button>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
            <div className="max-w-6xl mx-auto px-4 py-6">
                {/* 修正：頁面標題中的返回按鈕 */}
                <div className="flex items-center gap-4 mb-8">
                    <Link to={getBackUrl()} className="text-teal-600 hover:text-teal-700 transition-colors" title={getBackLabel()}>
                        <ArrowLeft className="w-6 h-6" />
                    </Link>
                    <div>
                        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{assessment.title}</h1> {/* Use assessment.title */}
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                            <span className="flex items-center gap-1">
                                <Clock className="w-4 h-4" />
                                {assessment.time_limit_minutes} 分鐘 {/* Use assessment.time_limit_minutes */}
                            </span>
                            <span className="flex items-center gap-1">
                                <Target className="w-4 h-4" />
                                {standards?.target_wpm} 字/分 
                                {standards?.set_by_teacher && (
                                    <span className="ml-1 text-xs text-blue-500">(老師設定)</span>
                                )}
                            </span>
                            <span className="flex items-center gap-1">
                                <BookOpen className="w-4 h-4" />
                                {assessment.content?.length || 0} 字 {/* Use assessment.content */}
                            </span>
                            {assignmentId && (
                                <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-300">
                                    <ListChecks className="w-3 h-3 mr-1" />
                                    作業模式
                                </Badge>
                            )}
                        </div>
                    </div>
                </div>

                {/* 核心修正：移除 Tabs 結構，直接顯示練習內容 */}
                <div className="space-y-6">
                    <AnimatePresence mode="wait">
                        {currentStep === 'selection' && (
                            <motion.div
                                key="selection"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="space-y-6"
                            >
                                <TextDisplay text={assessment.content} /> {/* Use assessment.content */}
                                <AttemptButtons 
                                    lesson={assessment} // Pass assessment
                                    studentId={user?.email}
                                    onStartPractice={handleStartPractice}
                                    onViewResult={handleViewResult}
                                    assignmentId={assignmentId} // 核心修正：將 assignmentId 傳遞下去
                                />
                            </motion.div>
                        )}

                        {currentStep === 'practice' && (
                            <motion.div
                                key="practice"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="space-y-6"
                            >
                                <TextDisplay text={assessment.content} /> {/* Use assessment.content */}
                                <AudioRecorder
                                    originalText={assessment.content} // Use assessment.content
                                    onComplete={handleAnalysisComplete}
                                    timeLimit={assessment.time_limit_minutes} // Use assessment.time_limit_minutes
                                    isProcessing={isProcessing}
                                />
                            </motion.div>
                        )}

                        {currentStep === 'results' && currentSession && ( // Use currentSession
                            <motion.div
                                key="results"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                            >
                                <ResultsDisplay 
                                    session={currentSession} // Pass currentSession
                                    targets={standards}
                                    originalText={assessment?.content} // Use assessment.content
                                    onDebugNotification={handleDebugNotification}
                                    onSessionUpdate={handleSessionUpdate} // 核心修正：傳遞更新函式
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            <CongratulationsModal 
                isOpen={showConfetti}
                onClose={() => setShowConfetti(false)}
                achievement={currentSession && standards && // Use currentSession
                    (currentSession.words_per_minute >= standards.target_wpm && 
                     currentSession.percentage_score >= standards.target_accuracy)}
                attempt={currentSession} // Pass currentSession
                standards={standards}
            />
        </div>
    );
}
