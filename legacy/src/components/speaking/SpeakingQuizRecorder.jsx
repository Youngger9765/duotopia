import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Mic, Square, Play, Pause, RefreshCw, Send } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadFile } from "@/api/integrations";
import { speakingQuizGrading } from "@/api/functions";

export default function SpeakingQuizRecorder({ quiz, onComplete, timeLimit }) {
    const [isRecording, setIsRecording] = useState(false);
    const [audioBlob, setAudioBlob] = useState(null);
    const [audioUrl, setAudioUrl] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);
    
    const mediaRecorderRef = useRef(null);
    const audioRef = useRef(null);
    const chunksRef = useRef([]);
    const timerRef = useRef(null);

    useEffect(() => {
        return () => {
            if (timerRef.current) {
                clearInterval(timerRef.current);
            }
        };
    }, []);

    const startRecording = async () => {
        try {
            setError(null);
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            mediaRecorderRef.current = new MediaRecorder(stream);
            chunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            mediaRecorderRef.current.onstop = () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
                setAudioBlob(audioBlob);
                const url = URL.createObjectURL(audioBlob);
                setAudioUrl(url);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
            setRecordingTime(0);
            
            // 開始計時器
            timerRef.current = setInterval(() => {
                setRecordingTime(prev => {
                    const newTime = prev + 1;
                    if (newTime >= timeLimit) {
                        stopRecording();
                        return newTime;
                    }
                    return newTime;
                });
            }, 1000);

        } catch (error) {
            console.error('Error starting recording:', error);
            setError('無法開始錄音，請檢查麥克風設定');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            if (timerRef.current) {
                clearInterval(timerRef.current);
            }
        }
    };

    const togglePlayback = () => {
        if (audioRef.current) {
            if (isPlaying) {
                audioRef.current.pause();
            } else {
                audioRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    const resetRecording = () => {
        setAudioBlob(null);
        setAudioUrl(null);
        setIsPlaying(false);
        setRecordingTime(0);
        setError(null);
        if (timerRef.current) {
            clearInterval(timerRef.current);
        }
    };

    const submitRecording = async () => {
        if (!audioBlob) {
            setError('請先錄音');
            return;
        }

        setIsProcessing(true);
        setError(null);

        try {
            // 上傳音檔
            const fileToUpload = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
            const { file_url } = await UploadFile({ file: fileToUpload });

            if (!file_url) {
                throw new Error("文件上傳失敗");
            }

            // 進行AI批改
            const response = await speakingQuizGrading({
                audio_url: file_url,
                quiz_data: quiz,
                recording_duration: recordingTime
            });

            if (response.error || response.status >= 400) {
                throw new Error(response.error?.message || 'AI批改失敗');
            }

            const gradingResult = response.data;

            // 回傳結果給父組件
            onComplete({
                audio_url: file_url,
                transcribed_text: gradingResult.transcribed_text,
                score: gradingResult.score,
                max_score: quiz.points || 10,
                ai_feedback: gradingResult.feedback,
                grammar_score: gradingResult.grammar_score,
                fluency_score: gradingResult.fluency_score,
                pronunciation_score: gradingResult.pronunciation_score,
                content_score: gradingResult.content_score,
                keyword_usage: gradingResult.keyword_usage,
                recording_duration: recordingTime,
                completed_at: new Date().toISOString()
            });

        } catch (error) {
            console.error('提交錄音失敗:', error);
            setError(`處理錄音時發生錯誤：${error.message}`);
        } finally {
            setIsProcessing(false);
        }
    };

    const formatTime = (seconds) => `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`;
    const progressPercentage = (recordingTime / timeLimit) * 100;

    return (
        <Card className="bg-white/90 backdrop-blur-sm shadow-lg">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Mic className="w-5 h-5 text-orange-600" />
                    錄音作答
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                {error && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-red-800 text-sm">{error}</p>
                    </div>
                )}

                <AnimatePresence mode="wait">
                    {!isRecording && !audioBlob && (
                        <motion.div
                            key="start"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="text-center space-y-4"
                        >
                            <div className="text-gray-600">
                                <p>準備好了嗎？點擊開始錄音</p>
                                <p className="text-sm">時間限制：{timeLimit} 秒</p>
                            </div>
                            <Button 
                                onClick={startRecording} 
                                className="bg-red-500 hover:bg-red-600 text-white px-8 py-3"
                                disabled={isProcessing}
                            >
                                <Mic className="w-5 h-5 mr-2" />
                                開始錄音
                            </Button>
                        </motion.div>
                    )}

                    {isRecording && (
                        <motion.div
                            key="recording"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="text-center space-y-6"
                        >
                            <div className="relative">
                                <div className="w-24 h-24 mx-auto bg-red-500 rounded-full flex items-center justify-center animate-pulse">
                                    <Mic className="w-12 h-12 text-white" />
                                </div>
                                <div className="absolute inset-0 w-24 h-24 mx-auto border-4 border-red-300 rounded-full animate-ping"></div>
                            </div>
                            
                            <div>
                                <p className="text-xl font-bold text-red-600">錄音中...</p>
                                <p className="text-3xl font-mono font-bold text-gray-800 mt-2">
                                    {formatTime(recordingTime)}
                                </p>
                                <Progress value={progressPercentage} className="mt-3 h-2" />
                                <p className="text-sm text-gray-500 mt-1">
                                    剩餘時間：{formatTime(timeLimit - recordingTime)}
                                </p>
                            </div>

                            <Button 
                                onClick={stopRecording} 
                                className="bg-gray-600 hover:bg-gray-700 text-white px-8 py-3"
                            >
                                <Square className="w-5 h-5 mr-2" />
                                停止錄音
                            </Button>
                        </motion.div>
                    )}

                    {audioBlob && !isProcessing && (
                        <motion.div
                            key="review"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="space-y-4"
                        >
                            <div className="text-center">
                                <p className="text-green-600 font-semibold mb-2">✓ 錄音完成</p>
                                <p className="text-gray-600">錄音時長：{formatTime(recordingTime)}</p>
                            </div>
                            
                            <audio 
                                ref={audioRef} 
                                src={audioUrl} 
                                onEnded={() => setIsPlaying(false)} 
                                onPause={() => setIsPlaying(false)} 
                                className="hidden" 
                            />
                            
                            <div className="flex gap-3 justify-center">
                                <Button onClick={togglePlayback} variant="outline">
                                    {isPlaying ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                                    {isPlaying ? "暫停" : "試聽"}
                                </Button>
                                <Button onClick={resetRecording} variant="outline">
                                    <RefreshCw className="w-4 h-4 mr-2" />
                                    重新錄音
                                </Button>
                                <Button onClick={submitRecording} className="bg-green-600 hover:bg-green-700 text-white">
                                    <Send className="w-4 h-4 mr-2" />
                                    提交答案
                                </Button>
                            </div>
                        </motion.div>
                    )}

                    {isProcessing && (
                        <motion.div
                            key="processing"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-center space-y-4"
                        >
                            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                            <p className="text-blue-600 font-medium">AI 正在批改中...</p>
                            <p className="text-sm text-gray-500">請稍候，系統正在分析您的錄音</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </CardContent>
        </Card>
    );
}