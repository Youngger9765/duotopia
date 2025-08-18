
import React, { useState, useEffect, useRef } from 'react';
import { Lesson } from '@/api/entities';
import { User } from '@/api/entities';
import { ActivityResult } from '@/api/entities';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Play, Pause, Volume2, CheckCircle2, XCircle, RefreshCw, Clock, BarChart3, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';
import { motion, AnimatePresence } from 'framer-motion';
import ListeningClozeStartScreen from "../components/assessment/ListeningClozeStartScreen";
import ListeningClozeResults from "../components/assessment/ListeningClozeResults";

export default function ListeningClozePage() {
    const [lesson, setLesson] = useState(null);
    const [assignmentId, setAssignmentId] = useState(null); // 新增 state for assignment_id
    const [userAnswers, setUserAnswers] = useState({});
    // currentStep manages the overall flow: instruction (initial/history list), practice, results, history (detail view)
    const [currentStep, setCurrentStep] = useState('instruction');
    const [loading, setLoading] = useState(true);
    const [isPlaying, setIsPlaying] = useState(false);
    const [timeLeft, setTimeLeft] = useState(0);
    const [timerActive, setTimerActive] = useState(false);
    
    // States for result storage and display
    const [analyzing, setAnalyzing] = useState(false);
    const [results, setResults] = useState(null); // Stores the aggregated results object for display

    // States for history view
    const [user, setUser] = useState(null);
    const [previousResults, setPreviousResults] = useState([]);
    const [selectedResult, setSelectedResult] = useState(null);

    const audioRef = useRef(null);
    const timerRef = useRef(null);

    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const lessonId = urlParams.get('lesson_id');
        const assId = urlParams.get('assignment_id'); // 讀取 assignment_id
        
        if (assId) {
          setAssignmentId(assId);
        }

        if (lessonId) {
            loadLesson(lessonId);
            loadUser(lessonId, assId); // Load user and previous results, passing lessonId and assId
        } else {
            console.error('缺少 lesson_id 參數');
            setLoading(false);
        }
        
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
            // Stop TTS if it's playing
            if ('speechSynthesis' in window && speechSynthesis.speaking) {
                speechSynthesis.cancel();
            }
        };
    }, []);

    const loadUser = async (lessonId, assignmentId) => {
        try {
            const currentUser = await User.me();
            setUser(currentUser);
            if (currentUser) {
                loadPreviousResults(currentUser, lessonId, assignmentId);
            }
        } catch (error) {
            console.error('載入用戶資料失敗:', error);
        }
    };

    const loadPreviousResults = async (currentUser, lessonId, assignmentId) => {
        try {
            if (!lessonId) return;
            
            const filters = {
                lesson_id: lessonId,
                student_id: currentUser.id, // Filter by student_id instead of email for robustness
                activity_type: 'listening_cloze'
            };

            // Conditionally add assignment_id filter
            if (assignmentId) {
                filters.assignment_id = assignmentId;
            } else {
                // If no assignmentId is present in URL, explicitly filter for results without an assignment_id
                filters.assignment_id = null;
            }
            
            // 載入該課程的歷史成績，按 completed_at 降序排列
            const results = await ActivityResult.filter(filters, '-completed_at');
            
            console.log('載入的聽力歷史記錄:', results);
            setPreviousResults(results);
        } catch (error) {
            console.error('載入歷史記錄失敗:', error);
        }
    };

    const loadLesson = async (lessonId) => { // Accept lessonId as argument
        try {
            console.log('獲取的lesson_id:', lessonId);
            
            if (!lessonId) {
                console.error('缺少 lesson_id 參數');
                setLoading(false);
                return;
            }

            const lessonData = await Lesson.get(lessonId);
            console.log('載入的課程資料:', lessonData);
            
            if (lessonData && lessonData.activity_type === 'listening_cloze') {
                setLesson(lessonData);
                
                // Initialize user answers
                const initialAnswers = {};
                lessonData.cloze_questions?.forEach((_, index) => {
                    initialAnswers[index] = '';
                });
                setUserAnswers(initialAnswers);
                
                // Set timer
                setTimeLeft((lessonData.time_limit_minutes || 5) * 60);
            } else {
                console.error('課程不存在或不是聽力克漏字類型');
            }
        } catch (error) {
            console.error('載入課程失敗:', error);
        } finally {
            setLoading(false);
        }
    };

    const startTimer = () => {
        setTimerActive(true);
        timerRef.current = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1) {
                    handleSubmit(); // 時間到自動提交
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
    };

    const stopTimer = () => {
        setTimerActive(false);
        if (timerRef.current) {
            clearInterval(timerRef.current);
        }
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const playAudio = async () => {
        if (!lesson) return;

        try {
            if (lesson.audio_source_type === 'tts' && lesson.tts_text) {
                // Use TTS playback
                if ('speechSynthesis' in window) {
                    // Cancel any ongoing speech before starting a new one
                    if (speechSynthesis.speaking) {
                        speechSynthesis.cancel();
                    }

                    const utterance = new SpeechSynthesisUtterance(lesson.tts_text);
                    utterance.lang = 'zh-TW';
                    utterance.rate = lesson.tts_speed || 1.0;
                    
                    // Set voice type
                    const voices = speechSynthesis.getVoices();
                    const targetVoice = voices.find(voice => 
                        voice.lang.includes('zh') && 
                        (lesson.tts_voice?.includes('女') ? voice.name.includes('Female') : voice.name.includes('Male'))
                    );
                    if (targetVoice) utterance.voice = targetVoice;
                    
                    utterance.onstart = () => setIsPlaying(true);
                    utterance.onend = () => setIsPlaying(false);
                    utterance.onerror = (event) => {
                        console.error('TTS error:', event);
                        setIsPlaying(false);
                    };
                    
                    speechSynthesis.speak(utterance);
                }
            } else if (lesson.audio_url) {
                // Use uploaded audio file
                if (audioRef.current) {
                    if (isPlaying) {
                        audioRef.current.pause();
                        setIsPlaying(false);
                    } else {
                        await audioRef.current.play();
                        setIsPlaying(true);
                    }
                }
            }
        } catch (error) {
            console.error('播放音檔失敗:', error);
        }
    };

    const handleAnswerChange = (questionIndex, value) => {
        setUserAnswers(prev => ({
            ...prev,
            [questionIndex]: value
        }));
    };

    const startPractice = () => {
        setCurrentStep('practice');
        if (!timerActive) { // Prevent timer from restarting if already active
            startTimer();
        }
    };

    const handleSubmit = async () => {
        stopTimer();
        setAnalyzing(true);
        
        try {
            // Calculate results
            const resultsArray = lesson.cloze_questions.map((question, index) => {
                const userAnswer = userAnswers[index]?.trim() || '';
                const correctAnswer = question.correct_answer?.trim() || '';
                const isCorrect = userAnswer.toLowerCase() === correctAnswer.toLowerCase();
                
                return {
                    question_index: index,
                    question_content: question.question_text,
                    student_answer: userAnswer,
                    correct_answer: correctAnswer,
                    is_correct: isCorrect,
                    score: isCorrect ? 100 : 0,
                    feedback: isCorrect ? '答案正確！' : `正確答案是：${correctAnswer}`
                };
            });
            
            const totalQuestions = lesson.cloze_questions.length;
            const correctCount = resultsArray.filter(r => r.is_correct).length;
            const totalScorePercentage = totalQuestions > 0 ? Math.round((correctCount / totalQuestions) * 100) : 0;
            const timeSpent = ((lesson.time_limit_minutes || 0) * 60) - timeLeft;

            // Get next attempt number based on previously loaded results
            const nextAttemptNumber = previousResults.length > 0 ? 
                Math.max(...previousResults.map(r => r.attempt_number || 0)) + 1 : 1;
            
            // **核心修正：確保用戶已認證**
            if (!user) {
                throw new Error("User not authenticated.");
            }

            console.log('[ListeningCloze] 準備儲存結果:', {
                student_id: user.id,
                student_email: user.email,
                lesson_id: lesson.id,
                assignment_id: assignmentId,
                activity_type: 'listening_cloze',
                attempt_number: nextAttemptNumber,
                total_score: correctCount,
                max_score: totalQuestions,
                percentage_score: totalScorePercentage,
                time_spent_seconds: Math.max(0, timeSpent),
                answers: resultsArray
            });
            
            // **核心修正：加入錯誤處理和重試邏輯**
            let savedResult;
            let retryCount = 0;
            const maxRetries = 3;
            
            while (retryCount < maxRetries) {
                try {
                    savedResult = await ActivityResult.create({
                        student_id: user.id,
                        student_email: user.email,
                        lesson_id: lesson.id,
                        assignment_id: assignmentId,
                        activity_type: 'listening_cloze',
                        attempt_number: nextAttemptNumber,
                        total_score: correctCount,
                        max_score: totalQuestions,
                        percentage_score: totalScorePercentage,
                        time_spent_seconds: Math.max(0, timeSpent),
                        answers: resultsArray,
                        completed_at: new Date().toISOString(),
                        detailed_feedback: `聽力克漏字練習完成。總共 ${totalQuestions} 題，答對 ${correctCount} 題，正確率 ${totalScorePercentage}%。`,
                        is_submitted: true
                    });
                    
                    // 如果成功，跳出重試迴圈
                    break;
                } catch (apiError) {
                    retryCount++;
                    console.error(`[ListeningCloze] API 呼叫失敗 (第 ${retryCount} 次):`, apiError);
                    
                    if (retryCount >= maxRetries) {
                        // 達到最大重試次數，拋出錯誤
                        throw new Error(`提交失敗，已重試 ${maxRetries} 次。請檢查網路連線或稍後再試。`);
                    }
                    
                    // 等待一段時間後重試
                    await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
                }
            }
            
            console.log('[ListeningCloze] 聽力結果已成功儲存:', savedResult);
            
            // Update history list with the new result
            setPreviousResults(prev => [savedResult, ...prev]);

            const finalResults = {
                results: resultsArray,
                totalScore: totalScorePercentage,
                correctCount: correctCount,
                totalQuestions: totalQuestions,
                timeSpent: Math.max(0, timeSpent),
                savedResult: savedResult
            };

            setResults(finalResults);
            setCurrentStep('results');
            
        } catch (error) {
            console.error('[ListeningCloze] 提交答案失敗:', error);
            
            // **改善錯誤處理：給用戶更明確的錯誤訊息**
            let errorMessage = '提交失敗，請稍後再試';
            if (error.message.includes('網路')) {
                errorMessage = '網路連線有問題，請檢查網路後重試';
            } else if (error.message.includes('重試')) {
                errorMessage = error.message;
            } else if (error.message.includes('authenticated')) {
                errorMessage = '使用者驗證失敗，請重新登入';
            }
            
            alert(errorMessage);
        } finally {
            setAnalyzing(false);
        }
    };
    
    // Function to try the current lesson again (resets answers and timer)
    const handleTryAgain = () => {
        // Reset states to start a new practice for the same lesson
        setUserAnswers({}); // Clear user's answers
        setResults(null); // Clear previous results
        setCurrentStep('instruction'); // Go back to instruction/history page
        if (lesson) {
            setTimeLeft((lesson.time_limit_minutes || 5) * 60); // Reset timer
        }
        setTimerActive(false);
        if (timerRef.current) {
            clearInterval(timerRef.current); // Clear any running timer
        }
        // Stop TTS if it's playing
        if ('speechSynthesis' in window && speechSynthesis.speaking) {
            speechSynthesis.cancel();
        }
    };

    // Function to select a historical result and view its details
    const handleSelectResult = (result) => {
        setSelectedResult(result);
        setCurrentStep('history');
    };

    // Function to start a completely new practice, clearing any selected history
    const startNewPractice = () => {
        setCurrentStep('instruction'); // Go back to the instruction/history list page
        setSelectedResult(null); // Clear any selected historical result
        setTimeLeft((lesson?.time_limit_minutes || 5) * 60);
        setTimerActive(false);
        setResults(null); // Clear aggregated results
        setAnalyzing(false);
        
        // Reset answers
        const initialAnswers = {};
        lesson?.cloze_questions?.forEach((_, index) => {
            initialAnswers[index] = '';
        });
        setUserAnswers(initialAnswers);
        
        if (timerRef.current) {
            clearInterval(timerRef.current);
        }
        // Stop TTS if it's playing
        if ('speechSynthesis' in window && speechSynthesis.speaking) {
            speechSynthesis.cancel();
        }
    };

    if (loading) {
        return (
            <div className="p-6 min-h-screen flex items-center justify-center bg-gray-50">
                <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        );
    }

    if (!lesson) {
        return (
            <div className="p-6 min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <p className="text-gray-600 mb-4">找不到指定的聽力練習</p>
                    <Link to={createPageUrl("StudentDashboard")}>
                        <Button>返回課程列表</Button>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <Card className="w-full max-w-4xl mx-auto shadow-2xl border-0">
                <CardHeader className="bg-gradient-to-r from-teal-500 to-blue-500 text-white rounded-t-lg p-6">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-4">
                            <Link to={createPageUrl("StudentDashboard")} className="text-white hover:bg-white/20 p-2 rounded-full transition-colors">
                                <ArrowLeft className="w-5 h-5" />
                            </Link>
                            <div className="min-w-0">
                                <CardTitle className="text-2xl font-bold truncate">{lesson.title}</CardTitle>
                                <p className="text-sm text-white/90 truncate">聽力克漏字練習</p>
                            </div>
                        </div>
                        {currentStep === 'practice' && timerActive && (
                            <div className="flex items-center gap-2 text-lg font-semibold bg-white/20 px-4 py-2 rounded-lg">
                                <Clock className="w-5 h-5" />
                                <span>{formatTime(timeLeft)}</span>
                            </div>
                        )}
                    </div>
                </CardHeader>
                <CardContent className="p-6 md:p-8">
                    <AnimatePresence mode="wait">
                        {currentStep === 'instruction' && (
                            <motion.div
                                key="instruction-tab"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                            >
                                <ListeningClozeStartScreen 
                                    lesson={lesson}
                                    previousResults={previousResults}
                                    onStartPractice={startPractice} 
                                    onSelectResult={handleSelectResult}
                                />
                            </motion.div>
                        )}

                        {currentStep === 'practice' && (
                            <motion.div
                                key="practice-tab"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                className="animate-in fade-in duration-500"
                            >
                                {/* Timer and playback control */}
                                <Card className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                                    <CardContent className="p-6">
                                        <div className="flex justify-between items-center">
                                            <div className="flex items-center gap-4">
                                                <Button
                                                    onClick={playAudio}
                                                    variant="outline"
                                                    className="bg-white/20 border-white/30 text-white hover:bg-white/30"
                                                    disabled={analyzing}
                                                >
                                                    {isPlaying ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                                                    {isPlaying ? '暫停' : '播放音檔'}
                                                </Button>
                                                <span className="text-sm opacity-90">可重複播放</span>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-2xl font-bold">{formatTime(timeLeft)}</div>
                                                <div className="text-sm opacity-90">剩餘時間</div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>

                                {/* Question Area */}
                                <Card className="mt-6">
                                    <CardHeader>
                                        <CardTitle>聽力填空題</CardTitle>
                                        <p className="text-sm text-gray-600">
                                            請仔細聆聽音檔，在空格處填入正確的字詞
                                        </p>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        {lesson.cloze_questions?.map((question, index) => (
                                            <div key={index} className="p-4 bg-gray-50 rounded-lg">
                                                <div className="flex items-center gap-2 mb-3">
                                                    <Badge variant="outline">第 {index + 1} 題</Badge>
                                                </div>
                                                <div className="mb-3">
                                                    <p className="text-gray-800 leading-relaxed">
                                                        {question.question_text}
                                                    </p>
                                                </div>
                                                <Input
                                                    placeholder="請輸入答案"
                                                    value={userAnswers[index] || ''}
                                                    onChange={(e) => handleAnswerChange(index, e.target.value)}
                                                    className="text-lg"
                                                    disabled={analyzing}
                                                />
                                                {question.options && question.options.length > 0 && (
                                                    <div className="mt-3">
                                                        <p className="text-sm text-gray-600 mb-2">提示選項：</p>
                                                        <div className="flex gap-2 flex-wrap">
                                                            {question.options.map((option, optIndex) => (
                                                                <Badge
                                                                    key={optIndex}
                                                                    variant="outline"
                                                                    className="cursor-pointer hover:bg-blue-50"
                                                                    onClick={() => handleAnswerChange(index, option)}
                                                                >
                                                                    {option}
                                                                </Badge>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ))}

                                        <div className="text-center pt-4">
                                            <Button 
                                                onClick={handleSubmit} 
                                                size="lg" 
                                                className="gradient-bg text-white px-8"
                                                disabled={analyzing}
                                            >
                                                {analyzing ? (
                                                    <div className="flex items-center">
                                                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                                                        提交中...
                                                    </div>
                                                ) : '提交答案'}
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>

                                {/* Hidden audio element */}
                                {lesson.audio_url && (
                                    <audio
                                        ref={audioRef}
                                        src={lesson.audio_url}
                                        onEnded={() => setIsPlaying(false)}
                                        onPause={() => setIsPlaying(false)}
                                        className="hidden"
                                    />
                                )}
                            </motion.div>
                        )}

                        {currentStep === 'results' && results && (
                            <motion.div
                                key="results-tab"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                            >
                                <ListeningClozeResults 
                                    resultsData={results} 
                                    onTryAgain={handleTryAgain} 
                                    lessonTitle={lesson.title}
                                />
                            </motion.div>
                        )}
                        
                        {currentStep === 'history' && selectedResult && (
                            <motion.div
                                key="history-detail-tab"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="animate-in fade-in duration-500"
                            >
                                <div className="flex justify-between items-center mb-4">
                                    <Button variant="outline" onClick={() => { setCurrentStep('instruction'); setSelectedResult(null); }}>
                                        <ArrowLeft className="mr-2 h-4 w-4" /> 返回記錄列表
                                    </Button>
                                    <Button onClick={handleTryAgain}>
                                        <Plus className="mr-2 h-4 w-4" /> 開始新的練習
                                    </Button>
                                </div>
                                <ListeningClozeResults 
                                   resultsData={{ 
                                       results: selectedResult.answers,
                                       totalScore: selectedResult.percentage_score,
                                       correctCount: selectedResult.answers.filter(a => a.is_correct).length,
                                       totalQuestions: selectedResult.answers.length,
                                       timeSpent: selectedResult.time_spent_seconds,
                                   }}
                                   onTryAgain={handleTryAgain}
                                   lessonTitle={lesson.title}
                                   isHistoryView={true}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </CardContent>
            </Card>
        </div>
    );
}
