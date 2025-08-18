import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { User } from '@/api/entities';
import { Lesson } from '@/api/entities';
import { SpeakingQuiz } from '@/api/entities';
import { SpeakingSession } from '@/api/entities';
import { SpeakingQuizResult } from '@/api/entities';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, ArrowRight, Mic, Play, Pause, Volume2, Clock, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';
import { motion, AnimatePresence } from 'framer-motion';

import SpeakingQuizRecorder from '../components/speaking/SpeakingQuizRecorder';
import SpeakingQuizResults from '../components/speaking/SpeakingQuizResults';

export default function SpeakingQuizzesPage() {
    const location = useLocation();
    const urlParams = new URLSearchParams(location.search);
    const lessonId = urlParams.get('lesson_id');
    
    const [user, setUser] = useState(null);
    const [lesson, setLesson] = useState(null);
    const [quizzes, setQuizzes] = useState([]);
    const [currentQuizIndex, setCurrentQuizIndex] = useState(0);
    const [session, setSession] = useState(null);
    const [quizResults, setQuizResults] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentStep, setCurrentStep] = useState('quiz'); // 'quiz' | 'results'
    const [isPlayingDemo, setIsPlayingDemo] = useState(false);

    useEffect(() => {
        loadInitialData();
    }, [lessonId]);

    const loadInitialData = async () => {
        try {
            setLoading(true);
            const currentUser = await User.me();
            setUser(currentUser);

            if (!lessonId) {
                setError('缺少錄音集ID');
                return;
            }

            // 載入錄音集資料
            const lessonData = await Lesson.get(lessonId);
            setLesson(lessonData);

            // 載入題目清單
            const quizList = await SpeakingQuiz.filter({ lesson_id: lessonId }, "quiz_number");
            setQuizzes(quizList);

            // 檢查是否已有進行中的測驗
            const existingSessions = await SpeakingSession.filter({
                student_email: currentUser.email,
                lesson_id: lessonId,
                status: 'in_progress'
            });

            if (existingSessions.length > 0) {
                // 恢復進行中的測驗
                const currentSession = existingSessions[0];
                setSession(currentSession);
                setCurrentQuizIndex(currentSession.completed_quizzes);
                
                // 載入已完成的題目結果
                const existingResults = await SpeakingQuizResult.filter({
                    session_id: currentSession.session_id
                });
                const resultsMap = {};
                existingResults.forEach(result => {
                    resultsMap[result.quiz_number] = result;
                });
                setQuizResults(resultsMap);
            } else {
                // 建立新的測驗場次
                const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                const newSession = await SpeakingSession.create({
                    student_id: currentUser.id,
                    student_email: currentUser.email,
                    lesson_id: lessonId,
                    session_id: sessionId,
                    total_quizzes: quizList.length,
                    max_total_score: quizList.reduce((sum, quiz) => sum + (quiz.points || 10), 0),
                    started_at: new Date().toISOString()
                });
                setSession(newSession);
            }

        } catch (error) {
            console.error('載入資料失敗:', error);
            setError('載入資料失敗：' + error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleQuizComplete = async (quizResult) => {
        try {
            const currentQuiz = quizzes[currentQuizIndex];
            
            // 儲存本題結果
            const result = await SpeakingQuizResult.create({
                student_id: user.id,
                student_email: user.email,
                lesson_id: lessonId,
                quiz_id: currentQuiz.id,
                session_id: session.session_id,
                quiz_number: currentQuiz.quiz_number,
                ...quizResult
            });

            // 更新本地結果
            setQuizResults(prev => ({
                ...prev,
                [currentQuiz.quiz_number]: result
            }));

            // 更新測驗場次
            const updatedSession = await SpeakingSession.update(session.id, {
                completed_quizzes: session.completed_quizzes + 1,
                total_score: session.total_score + (quizResult.score || 0),
                time_spent_seconds: session.time_spent_seconds + (quizResult.recording_duration || 0)
            });
            setSession(updatedSession);

            // 檢查是否完成所有題目
            if (currentQuizIndex + 1 >= quizzes.length) {
                // 完成整個測驗
                await completeSession();
            } else {
                // 進入下一題
                setCurrentQuizIndex(prev => prev + 1);
            }

        } catch (error) {
            console.error('儲存結果失敗:', error);
            setError('儲存結果失敗：' + error.message);
        }
    };

    const completeSession = async () => {
        try {
            const finalScore = Object.values(quizResults).reduce((sum, result) => sum + (result.score || 0), 0);
            const percentageScore = session.max_total_score > 0 ? (finalScore / session.max_total_score) * 100 : 0;

            await SpeakingSession.update(session.id, {
                status: 'completed',
                total_score: finalScore,
                percentage_score: percentageScore,
                completed_at: new Date().toISOString()
            });

            setCurrentStep('results');
        } catch (error) {
            console.error('完成測驗失敗:', error);
            setError('完成測驗失敗：' + error.message);
        }
    };

    const playDemoAudio = () => {
        const currentQuiz = quizzes[currentQuizIndex];
        if (currentQuiz?.demo_audio_url) {
            const audio = new Audio(currentQuiz.demo_audio_url);
            audio.onplay = () => setIsPlayingDemo(true);
            audio.onended = () => setIsPlayingDemo(false);
            audio.onerror = () => setIsPlayingDemo(false);
            audio.play();
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600 font-medium">載入錄音集...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
                <div className="text-center bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-white/20 p-12 max-w-lg mx-auto">
                    <p className="text-red-600 font-bold text-xl mb-4">發生錯誤</p>
                    <p className="text-gray-700 text-lg mb-6">{error}</p>
                    <Link to={createPageUrl("StudentDashboard")}>
                        <Button className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white font-semibold py-3 rounded-xl">
                            返回課程列表
                        </Button>
                    </Link>
                </div>
            </div>
        );
    }

    if (currentStep === 'results') {
        return (
            <SpeakingQuizResults 
                session={session}
                lesson={lesson}
                quizResults={Object.values(quizResults)}
                quizzes={quizzes}
            />
        );
    }

    const currentQuiz = quizzes[currentQuizIndex];
    const progress = session ? ((currentQuizIndex / quizzes.length) * 100) : 0;

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
            <div className="max-w-4xl mx-auto px-4 py-6">
                {/* 頁面標題和進度 */}
                <div className="flex items-center gap-4 mb-8">
                    <Link to={createPageUrl("StudentDashboard")} className="text-teal-600 hover:text-teal-700 transition-colors">
                        <ArrowLeft className="w-6 h-6" />
                    </Link>
                    <div className="flex-1">
                        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{lesson?.title}</h1>
                        <div className="flex items-center gap-4 mt-2">
                            <Badge className="bg-green-100 text-green-800">🎤 錄音集</Badge>
                            <span className="text-sm text-gray-600">
                                第 {currentQuizIndex + 1} 題，共 {quizzes.length} 題
                            </span>
                        </div>
                        <div className="mt-3">
                            <Progress value={progress} className="h-2" />
                            <p className="text-xs text-gray-500 mt-1">完成進度：{Math.round(progress)}%</p>
                        </div>
                    </div>
                </div>

                {/* 題目內容 */}
                {currentQuiz && (
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={currentQuizIndex}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-6"
                        >
                            {/* 題目卡片 */}
                            <Card className="bg-white/90 backdrop-blur-sm shadow-lg">
                                <CardHeader>
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <CardTitle className="text-xl">{currentQuiz.quiz_title}</CardTitle>
                                            <div className="flex items-center gap-2 mt-2">
                                                <Badge variant="outline">{currentQuiz.difficulty_level}</Badge>
                                                <Badge variant="outline">{currentQuiz.points} 分</Badge>
                                                <Badge variant="outline">
                                                    <Clock className="w-3 h-3 mr-1" />
                                                    {currentQuiz.time_limit_seconds} 秒
                                                </Badge>
                                            </div>
                                        </div>
                                        {currentQuiz.demo_audio_url && (
                                            <Button 
                                                variant="outline" 
                                                size="sm"
                                                onClick={playDemoAudio}
                                                disabled={isPlayingDemo}
                                            >
                                                {isPlayingDemo ? (
                                                    <><Pause className="w-4 h-4 mr-2" />播放中</>
                                                ) : (
                                                    <><Volume2 className="w-4 h-4 mr-2" />示範</>
                                                )}
                                            </Button>
                                        )}
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    {/* 題目圖片 */}
                                    {currentQuiz.image_url && (
                                        <div className="mb-4">
                                            <img 
                                                src={currentQuiz.image_url} 
                                                alt="題目配圖"
                                                className="w-full max-w-md mx-auto rounded-lg shadow-md"
                                            />
                                        </div>
                                    )}
                                    
                                    {/* 題目內容 */}
                                    <div className="prose max-w-none">
                                        <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                                            {currentQuiz.content}
                                        </p>
                                    </div>

                                    {/* 目標句型 */}
                                    {currentQuiz.target_sentence_pattern && (
                                        <div className="mt-4 p-3 bg-blue-50 rounded-lg border-l-4 border-l-blue-500">
                                            <p className="text-sm font-medium text-blue-800">目標句型：</p>
                                            <p className="text-blue-700">{currentQuiz.target_sentence_pattern}</p>
                                        </div>
                                    )}

                                    {/* 範例句子 */}
                                    {currentQuiz.example_sentences && currentQuiz.example_sentences.length > 0 && (
                                        <div className="mt-4 p-3 bg-green-50 rounded-lg border-l-4 border-l-green-500">
                                            <p className="text-sm font-medium text-green-800">參考範例：</p>
                                            <ul className="text-green-700 mt-1 space-y-1">
                                                {currentQuiz.example_sentences.map((example, index) => (
                                                    <li key={index}>• {example}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {/* 期望關鍵字 */}
                                    {currentQuiz.expected_keywords && currentQuiz.expected_keywords.length > 0 && (
                                        <div className="mt-4 p-3 bg-purple-50 rounded-lg border-l-4 border-l-purple-500">
                                            <p className="text-sm font-medium text-purple-800">建議使用的關鍵字：</p>
                                            <div className="flex flex-wrap gap-2 mt-2">
                                                {currentQuiz.expected_keywords.map((keyword, index) => (
                                                    <Badge key={index} className="bg-purple-100 text-purple-800">
                                                        {keyword}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            {/* 錄音區域 */}
                            <SpeakingQuizRecorder
                                quiz={currentQuiz}
                                onComplete={handleQuizComplete}
                                timeLimit={currentQuiz.time_limit_seconds}
                            />
                        </motion.div>
                    </AnimatePresence>
                )}
            </div>
        </div>
    );
}