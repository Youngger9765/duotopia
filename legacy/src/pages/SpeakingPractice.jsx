
import React, { useState, useEffect, useRef } from 'react';
import { Lesson } from '@/api/entities';
import { ActivityResult } from '@/api/entities';
import { User } from '@/api/entities';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Mic, MessageCircle, CheckCircle2, RefreshCw, Ear, Play, History, List } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadFile } from '@/api/integrations';
import { speakingPracticeAnalysis } from '@/api/functions';
import { format } from "date-fns";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import AudioRecorder from '../components/assessment/AudioRecorder';

export default function SpeakingPracticePage() {
    const [lesson, setLesson] = useState(null);
    const [currentTopicIndex, setCurrentTopicIndex] = useState(0);
    const [recordings, setRecordings] = useState({});
    const [currentStep, setCurrentStep] = useState('instruction');
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);
    const [analysisProgress, setAnalysisProgress] = useState(0);
    const [hasExistingResults, setHasExistingResults] = useState(false);
    const [historicalRecords, setHistoricalRecords] = useState([]);
    const [selectedRecord, setSelectedRecord] = useState(null);

    useEffect(() => {
        loadLesson();
    }, []);

    const loadLesson = async () => {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const lessonId = urlParams.get('lesson_id');
            const assignmentId = urlParams.get('assignment_id');
            
            if (!lessonId) {
                setError('缺少必要的課文ID，無法載入此練習。');
                setLoading(false);
                return;
            }
            
            const lessonData = await Lesson.get(lessonId);
            if (lessonData && lessonData.activity_type === 'speaking_practice') {
                setLesson(lessonData);
                await loadExistingResults(lessonId, assignmentId);
            } else {
                setError('找不到指定的錄音練習或課程類型不符。');
            }
        } catch (err) {
            console.error('載入課程失敗:', err);
            setError('載入課程資料時發生錯誤，請稍後再試。');
        } finally {
            setLoading(false);
        }
    };

    const loadExistingResults = async (lessonId, assignmentId) => {
        try {
            const currentUser = await User.me();
            let filters = {
                student_email: currentUser.email,
                lesson_id: lessonId,
                activity_type: 'speaking_practice'
            };
            
            if (assignmentId) {
                filters.assignment_id = assignmentId;
            }
            
            const existingRecords = await ActivityResult.filter(filters, '-created_date');
            
            if (existingRecords.length > 0) {
                console.log('[SpeakingPractice] 找到現存記錄:', existingRecords);
                setHasExistingResults(true);
                setHistoricalRecords(existingRecords);
            }
        } catch (error) {
            console.error('載入現存記錄失敗:', error);
        }
    };

    const getBackUrl = () => {
        const urlParams = new URLSearchParams(window.location.search);
        const assignmentId = urlParams.get('assignment_id');
        
        if (assignmentId) {
            return createPageUrl("Assignments");
        } else {
            return createPageUrl("StudentDashboard");
        }
    };

    const handleRecordingComplete = (topicIndex, audioBlob, audioUrl) => {
        setRecordings(prev => ({
            ...prev,
            [topicIndex]: { audioBlob, audioUrl }
        }));
    };

    const nextTopic = () => {
        if (lesson && lesson.speaking_topics && currentTopicIndex < lesson.speaking_topics.length - 1) {
            setCurrentTopicIndex(prev => prev + 1);
        }
    };

    const prevTopic = () => {
        if (currentTopicIndex > 0) {
            setCurrentTopicIndex(prev => prev - 1);
        }
    };

    const handleSubmit = async () => {
        setAnalyzing(true);
        setAnalysisProgress(0);

        try {
            if (!lesson || !lesson.speaking_topics || Object.keys(recordings).length === 0) {
                throw new Error("您尚未完成任何錄音，無法提交。");
            }

            const analysisResults = [];
            const totalTopicsToAnalyze = Object.keys(recordings).length;
            let analyzedCount = 0;

            for (const [indexStr, recordingData] of Object.entries(recordings)) {
                const index = parseInt(indexStr, 10);
                const topicData = lesson.speaking_topics[index];
                
                const { file_url } = await UploadFile({ file: new File([recordingData.audioBlob], 'recording.webm') });
                
                const { data: analysis } = await speakingPracticeAnalysis({
                    audio_url: file_url,
                    topic: topicData.topic,
                    description: topicData.description
                });
                
                analysisResults.push({
                    question_index: index,
                    question_content: topicData.topic,
                    student_answer: analysis.transcribed_text,
                    student_audio_url: file_url,
                    is_correct: true,
                    score: analysis.score,
                    feedback: analysis.feedback,
                });

                analyzedCount++;
                setAnalysisProgress((analyzedCount / totalTopicsToAnalyze) * 100);
            }

            const currentUser = await User.me();
            const urlParams = new URLSearchParams(window.location.search);
            const assignmentId = urlParams.get('assignment_id');
            const averageScore = analysisResults.reduce((sum, r) => sum + r.score, 0) / analysisResults.length;

            await ActivityResult.create({
                student_id: currentUser.id,
                student_email: currentUser.email,
                lesson_id: lesson.id,
                assignment_id: assignmentId,
                activity_type: 'speaking_practice',
                attempt_number: 1,
                total_score: averageScore,
                max_score: 100,
                percentage_score: averageScore,
                answers: analysisResults,
                completed_at: new Date().toISOString(),
                detailed_feedback: `練習完成，平均分數 ${averageScore.toFixed(1)}。`
            });
            
            setResults(analysisResults);
            setCurrentStep('results');

        } catch (err) {
            console.error('提交或分析失敗:', err);
            setError(`提交失敗：${err.message}`);
        } finally {
            setAnalyzing(false);
        }
    };

    const renderResultsContent = (record) => {
        if (!record || !record.answers) return <p>沒有可顯示的結果。</p>;
        return record.answers.map((result, index) => (
            <Card key={index} className="border">
                <CardHeader>
                    <div className="flex justify-between items-start">
                        <CardTitle className="text-lg">主題：{result.question_content}</CardTitle>
                        <Badge className="bg-blue-100 text-blue-800">得分: {result.score}</Badge>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <h4 className="font-semibold text-gray-700 flex items-center gap-2 mb-2">
                            <Ear className="w-4 h-4 text-gray-600" />你的回答 (語音辨識)
                        </h4>
                        <div className="p-3 bg-gray-50 rounded-md border">
                            <p className="text-gray-800">{result.student_answer}</p>
                            {result.student_audio_url && (
                                <audio controls src={result.student_audio_url} className="w-full mt-2">
                                    Your browser does not support the audio element.
                                </audio>
                            )}
                        </div>
                    </div>
                    <div>
                        <h4 className="font-semibold text-gray-700 flex items-center gap-2 mb-2">
                            <MessageCircle className="w-4 h-4 text-teal-600" />AI 智能回饋
                        </h4>
                        <div className="p-3 bg-teal-50 rounded-md border border-teal-100">
                            <p className="text-teal-900 whitespace-pre-wrap">{result.feedback}</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        ));
    };

    if (error) {
        return (
            <div className="p-6 min-h-screen flex items-center justify-center">
                <Card className="text-center p-8 shadow-lg">
                    <h2 className="text-2xl font-bold text-red-600 mb-4">發生錯誤</h2>
                    <p className="text-gray-700 text-lg">{error}</p>
                    <Link to={createPageUrl("StudentDashboard")} className="mt-6 inline-block">
                        <Button>返回課程列表</Button>
                    </Link>
                </Card>
            </div>
        );
    }
    
    if (loading) return <div className="p-6 min-h-screen flex items-center justify-center"><div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div></div>;
    if (!lesson) return <div className="p-6 min-h-screen flex items-center justify-center"><p>找不到指定的練習</p></div>;

    if (analyzing) {
        return (
            <div className="p-6 min-h-screen flex items-center justify-center">
                <Card className="text-center p-8 shadow-lg w-full max-w-md">
                    <h2 className="text-2xl font-bold text-teal-600 mb-4">AI 智能分析中...</h2>
                    <p className="text-gray-600 mb-6">請稍候，AI 正在仔細聆聽您的錄音並產生回饋。</p>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div className="bg-teal-500 h-2.5 rounded-full" style={{ width: `${analysisProgress}%`, transition: 'width 0.5s ease-in-out' }}></div>
                    </div>
                    <p className="mt-2 text-sm text-teal-700">{Math.round(analysisProgress)}%</p>
                </Card>
            </div>
        );
    }

    return (
        <Dialog>
            <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
                <div className="max-w-4xl mx-auto px-6 py-8">
                    <div className="flex items-center justify-between mb-8">
                        <div className="flex items-center gap-4">
                            <Link to={getBackUrl()}>
                                <Button variant="outline" size="sm">
                                    <ArrowLeft className="w-4 h-4 mr-2" />返回
                                </Button>
                            </Link>
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">{lesson.title}</h1>
                                <div className="flex items-center gap-3 mt-2">
                                    <Badge className="bg-green-100 text-green-800">錄音練習</Badge>
                                    <Badge variant="outline">{lesson.difficulty_level}</Badge>
                                </div>
                            </div>
                        </div>
                    </div>

                    <AnimatePresence mode="wait">
                        {currentStep === 'instruction' && (
                            <motion.div key="instruction" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-8">
                               <Card className="border-l-4 border-l-green-500 p-6">
                                   <CardTitle className="flex items-center gap-2 text-green-700 mb-4">
                                       <MessageCircle /> 錄音練習說明
                                   </CardTitle>
                                   <CardContent>
                                       <p className="mb-4">根據老師提供的主題和引導問題，進行錄音表達練習。</p>
                                       <Button 
                                           onClick={() => {
                                                setRecordings({}); 
                                                setResults(null); 
                                                setCurrentTopicIndex(0); 
                                                setCurrentStep('practice'); 
                                           }} 
                                           className="bg-gradient-to-r from-green-500 to-teal-500 text-white px-8"
                                       >
                                           {hasExistingResults ? "重新練習" : "開始練習"}
                                       </Button>
                                   </CardContent>
                               </Card>
                               
                                {hasExistingResults && (
                                    <Card>
                                        <CardHeader>
                                            <CardTitle className="flex items-center gap-2 text-gray-700">
                                                <History className="w-5 h-5"/>
                                                練習歷史記錄
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="space-y-3">
                                            {historicalRecords.map(record => (
                                                <DialogTrigger asChild key={record.id}>
                                                    <div 
                                                        className="flex justify-between items-center p-4 rounded-lg hover:bg-gray-100 cursor-pointer border transition-colors"
                                                        onClick={() => setSelectedRecord(record)}
                                                    >
                                                        <div className="flex items-center gap-3">
                                                            <div className="text-sm text-gray-600">
                                                                {format(new Date(record.completed_at), "yyyy-MM-dd HH:mm")}
                                                            </div>
                                                        </div>
                                                        <div className="flex items-center gap-4">
                                                          <Badge variant="outline" className="text-base">
                                                              分數: {record.percentage_score.toFixed(0)}%
                                                          </Badge>
                                                          <Button variant="ghost" size="sm">查看詳情</Button>
                                                        </div>
                                                    </div>
                                                </DialogTrigger>
                                            ))}
                                        </CardContent>
                                    </Card>
                                )}
                            </motion.div>
                        )}

                        {currentStep === 'practice' && lesson.speaking_topics && (
                            <motion.div key="practice" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-6">
                                <Card className="shadow-lg">
                                    <CardHeader className="bg-gradient-to-r from-green-500 to-teal-500 text-white">
                                        <CardTitle>口說主題 - 第 {currentTopicIndex + 1} 題</CardTitle>
                                    </CardHeader>
                                    <CardContent className="p-6">
                                        <div className="space-y-6">
                                            <div className="text-center"><h2 className="text-2xl font-bold">{lesson.speaking_topics[currentTopicIndex]?.topic}</h2></div>
                                            {lesson.speaking_topics[currentTopicIndex]?.description && <div className="bg-blue-50 p-4 rounded-lg"><p className="text-blue-800">{lesson.speaking_topics[currentTopicIndex].description}</p></div>}
                                            <div className="bg-white border rounded-lg p-6">
                                                <AudioRecorder key={currentTopicIndex} onComplete={(audioBlob, audioUrl) => handleRecordingComplete(currentTopicIndex, audioBlob, audioUrl)} maxDuration={(lesson.speaking_topics[currentTopicIndex]?.duration_minutes || 2) * 60} />
                                                {recordings[currentTopicIndex] && <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200 flex items-center gap-2"><CheckCircle2 className="w-5 h-5 text-green-600" /><span className="text-green-800">此題錄音已完成</span></div>}
                                            </div>
                                            <div className="flex justify-between items-center">
                                                <Button onClick={prevTopic} disabled={currentTopicIndex === 0} variant="outline">上一題</Button>
                                                <div className="flex gap-2">{lesson.speaking_topics.map((_, index) => <div key={index} className={`w-3 h-3 rounded-full ${index === currentTopicIndex ? 'bg-green-500' : recordings[index] ? 'bg-teal-500' : 'bg-gray-300'}`} />)}</div>
                                                {currentTopicIndex < lesson.speaking_topics.length - 1 ? (
                                                    <Button onClick={nextTopic} className="bg-green-500 hover:bg-green-600 text-white">下一題</Button>
                                                ) : (
                                                    <Button onClick={handleSubmit} disabled={analyzing} className="bg-teal-500 hover:bg-teal-600 text-white">完成練習</Button>
                                                )}
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        )}

                        {currentStep === 'results' && results && (
                            <motion.div key="results" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                                <Card className="shadow-lg">
                                    <CardHeader className="bg-gradient-to-r from-green-500 to-teal-500 text-white">
                                        <CardTitle className="flex items-center gap-2">
                                            <CheckCircle2 />本次練習結果
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="p-6 space-y-6">
                                        {renderResultsContent({ answers: results })}
                                        <div className="flex gap-3 justify-center">
                                            <Button 
                                                onClick={() => setCurrentStep('instruction')} 
                                                variant="outline"
                                            >
                                                <List className="w-4 h-4 mr-2" />返回練習首頁
                                            </Button>
                                            <Link to={getBackUrl()}>
                                                <Button className="bg-gradient-to-r from-green-500 to-teal-500 text-white">
                                                    完成並返回
                                                </Button>
                                            </Link>
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
            
            <DialogContent className="max-w-4xl w-[95vw] h-[90vh] flex flex-col p-0 gap-0">
                {selectedRecord && (
                    <>
                        <DialogHeader className="p-6 border-b">
                            <DialogTitle>
                                歷史紀錄 - {format(new Date(selectedRecord.completed_at), "yyyy年MM月dd日 HH:mm")}
                            </DialogTitle>
                        </DialogHeader>
                        <div className="flex-grow overflow-y-auto p-6 space-y-6">
                           {renderResultsContent(selectedRecord)}
                        </div>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
}
