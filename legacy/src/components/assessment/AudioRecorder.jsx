
import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Mic, Square, Play, Pause, Upload, AlertCircle, RefreshCw, FileAudio, CheckCircle2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { motion, AnimatePresence } from "framer-motion";
import { UploadFile } from "@/api/integrations";
import { improvedSpeechAnalysis } from "@/api/functions";
import { speakingQuizGrading } from "@/api/functions"; // 新增引用

// **核心修正：元件現在可以處理多種類型的回調**
export default function AudioRecorder({ onComplete, timeLimit, isProcessing: externalProcessing, originalText, quizData }) {
  const [mode, setMode] = useState('record'); // 'record' or 'upload'
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [hasPermission, setHasPermission] = useState(null);
  const [error, setError] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [fileName, setFileName] = useState('');
  
  const mediaRecorderRef = useRef(null);
  const audioRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    checkMicrophonePermission();
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const checkMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      setHasPermission(true);
    } catch (error) {
      console.error('Microphone permission denied:', error);
      setHasPermission(false);
      setError('需要麥克風權限才能進行錄音。請允許麥克風存取權限。');
    }
  };

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

        // **核心修正：如果是簡單錄音（非朗讀評估或錄音問答），則立即回傳結果**
        if (!originalText && !quizData && onComplete) {
            onComplete(audioBlob, url);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      // 開始計時器
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          if (timeLimit && newTime >= timeLimit * 60) {
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

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) { // 10MB 限制
        setError("檔案大小不能超過 10MB");
        return;
      }
      setError(null);
      setFileName(file.name);
      setAudioBlob(file);
      const url = URL.createObjectURL(file);
      setAudioUrl(url);
    }
  };

  const handleUpload = async () => {
    if (!audioBlob) {
      setError('請先錄音或選擇音檔');
      return;
    }

    // **核心修正：根據傳入的 props 決定使用哪個分析函數**
    if (originalText) {
        // 舊邏輯：朗讀評估
        if (!originalText.trim()) {
          setError('缺少原文內容，無法進行語音分析');
          return;
        }
        await processReadingAssessment(audioBlob, originalText);
    } else if (quizData) {
        // 新邏輯：錄音集批改
        await processSpeakingQuiz(audioBlob, quizData);
    } else {
        // **修正：處理沒有分析目標的情況，例如朗讀練習**
        // 在這種情況下，我們只回傳錄音檔資訊
        onComplete(audioBlob, URL.createObjectURL(audioBlob));
    }
  };

  const processReadingAssessment = async (blob, text) => {
    setIsProcessing(true);
    setError(null);
    try {
        const fileToUpload = blob instanceof File ? blob : new File([blob], 'recording.webm', { type: 'audio/webm' });
        const { file_url } = await UploadFile({ file: fileToUpload });

        if (!file_url) throw new Error("文件上傳失敗，未獲取到 URL。");

        console.log('[AudioRecorder] 準備進行語音分析:', {
          audio_url: file_url,
          original_text: text,
          recordingTime: recordingTime // **新增：記錄前端計時**
        });

        const response = await improvedSpeechAnalysis({
            audio_url: file_url,
            original_text: text
        });

        if (response.error || response.status >= 400 || !response.data) {
            const errorMessage = response.error?.message || response.data?.error || '語音分析失敗，請檢查後端日誌。';
            console.error("語音分析錯誤:", response);
            throw new Error(errorMessage);
        }

        // **核心修正：使用後端回傳的時間，若無則使用前端計時**
        const finalData = {
            ...response.data,
            audio_url: file_url,
            time_spent_seconds: response.data.time_spent_seconds || response.data.reading_time_seconds || recordingTime // **修正：多重備案**
        };

        console.log('[AudioRecorder] 最終資料:', {
            backend_time: response.data.time_spent_seconds,
            backend_reading_time: response.data.reading_time_seconds,
            frontend_time: recordingTime,
            final_time: finalData.time_spent_seconds
        });

        onComplete(finalData);
    } catch (error) {
        console.error('朗讀評估處理錯誤:', error);
        setError(`處理音檔時發生錯誤：${error.message}`);
    } finally {
        setIsProcessing(false);
    }
  };

  const processSpeakingQuiz = async (blob, data) => {
    setIsProcessing(true);
    setError(null);
    try {
        const fileToUpload = blob instanceof File ? blob : new File([blob], 'recording.webm', { type: 'audio/webm' });
        const { file_url } = await UploadFile({ file: fileToUpload });

        if (!file_url) throw new Error("文件上傳失敗，未獲取到 URL。");
        
        const currentRecordingDuration = recordingTime; // Use the current recording time for quiz grading

        const response = await speakingQuizGrading({
            audio_url: file_url,
            quiz_data: data,
            recording_duration: currentRecordingDuration
        });
        
        if (response.error || response.status >= 400 || !response.data) {
            const errorMessage = response.error?.message || response.data?.error || '錄音集批改失敗。';
            throw new Error(errorMessage);
        }

        onComplete({ ...response.data, audio_url: file_url });
    } catch (error) {
        console.error('錄音集處理錯誤:', error);
        setError(`處理音檔時發生錯誤：${error.message}`);
    } finally {
        setIsProcessing(false);
    }
  };

  const resetRecording = () => {
    setAudioBlob(null);
    setAudioUrl(null);
    setIsPlaying(false);
    setRecordingTime(0);
    setError(null);
    setFileName('');
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
  };

  const formatTime = (seconds) => `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`;
  const currentProcessing = externalProcessing || isProcessing;

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg space-y-6">
      <div className="flex justify-center bg-gray-100 p-1 rounded-lg">
        <Button onClick={() => setMode('record')} variant={mode === 'record' ? 'default' : 'ghost'} className="flex-1">
          <Mic className="w-4 h-4 mr-2" />即時錄音
        </Button>
        <Button onClick={() => setMode('upload')} variant={mode === 'upload' ? 'default' : 'ghost'} className="flex-1">
          <Upload className="w-4 h-4 mr-2" />上傳音檔
        </Button>
      </div>
      
      {/* 權限和錯誤提示 */}
      {hasPermission === false && (
        <Alert className="border-orange-200 bg-orange-50">
          <AlertCircle className="h-4 w-4 text-orange-600" />
          <AlertDescription className="text-orange-800">
            無法存取麥克風。請在瀏覽器設定中允許麥克風權限，然後重新整理頁面。
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}
      
      <AnimatePresence mode="wait">
        {mode === 'record' && (
          <motion.div key="record-panel" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
            {!isRecording && !audioBlob && (
              <div className="text-center space-y-4">
                <Button 
                  onClick={startRecording} 
                  disabled={hasPermission === false || currentProcessing}
                  className={`w-full py-4 text-lg font-semibold ${hasPermission === false ? 'opacity-50 cursor-not-allowed' : 'gradient-bg text-white hover:opacity-90'}`}
                >
                  <Mic className="w-6 h-6 mr-3" />
                  開始錄音
                </Button>
                {timeLimit && (
                  <p className="text-sm text-gray-500">時間限制：{timeLimit} 分鐘</p>
                )}
              </div>
            )}

            {isRecording && (
              <div className="text-center space-y-6">
                <div className="relative">
                  <div className="w-24 h-24 mx-auto bg-red-500 rounded-full flex items-center justify-center animate-pulse">
                    <Mic className="w-12 h-12 text-white" />
                  </div>
                  <div className="absolute inset-0 w-24 h-24 mx-auto border-4 border-red-300 rounded-full animate-ping"></div>
                </div>
                
                <div>
                  <p className="text-xl font-bold text-red-600">錄音中...</p>
                  <p className="text-2xl font-mono font-bold text-gray-800 mt-2">
                    {formatTime(recordingTime)}
                  </p>
                  {timeLimit && (
                    <p className="text-sm text-gray-500 mt-1">
                      剩餘時間：{formatTime((timeLimit * 60) - recordingTime)}
                    </p>
                  )}
                </div>

                <Button onClick={stopRecording} className="bg-red-600 hover:bg-red-700 text-white px-8 py-3">
                  <Square className="w-5 h-5 mr-2" />
                  停止錄音
                </Button>
              </div>
            )}

            {audioBlob && (
              <div className="text-center space-y-4">
                <p className="text-green-600 font-semibold">✓ 錄音完成</p>
                <p className="text-gray-600">錄音時長：{formatTime(recordingTime)}</p>
                
                <audio ref={audioRef} src={audioUrl} onEnded={() => setIsPlaying(false)} onPause={() => setIsPlaying(false)} className="hidden" />
                
                <div className="flex gap-2">
                  <Button onClick={togglePlayback} variant="outline" className="flex-1" disabled={currentProcessing}>
                    {isPlaying ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                    {isPlaying ? "暫停" : "播放"}
                  </Button>
                  <Button onClick={resetRecording} variant="outline" className="flex-1" disabled={currentProcessing}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    重新錄音
                  </Button>
                </div>
                
                {/* **核心修正：只在需要分析的模式下顯示按鈕，否則顯示提示訊息** */}
                {(originalText || quizData) ? (
                    <Button onClick={handleUpload} disabled={currentProcessing || !audioBlob} className="w-full gradient-bg text-white">
                      {currentProcessing ? "分析中..." : "上傳並分析"}
                    </Button>
                ) : (
                    <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                        <div className="flex items-center gap-2 justify-center">
                            <CheckCircle2 className="w-5 h-5 text-green-600" />
                            <span className="text-green-800 font-medium">錄音已儲存，請按「下一題」繼續</span>
                        </div>
                    </div>
                )}
              </div>
            )}
          </motion.div>
        )}

        {mode === 'upload' && (
          <motion.div key="upload-panel" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="text-center space-y-4">
            {!audioBlob && (
              <>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="audio/*"
                  className="hidden"
                />
                <Button onClick={() => fileInputRef.current.click()} className="w-full gradient-bg text-white">
                  <FileAudio className="w-5 h-5 mr-2" />
                  選擇音檔
                </Button>
                <p className="text-xs text-gray-500">支援 MP3, WAV, M4A, WEBM 等格式，上限 10MB</p>
              </>
            )}

            {audioBlob && (
              <div className="text-center space-y-4">
                <p className="text-gray-600 truncate">已選擇：{fileName}</p>
                <div className="text-xs text-gray-500">檔案大小: {Math.round(audioBlob.size / 1024)} KB</div>
                <audio ref={audioRef} src={audioUrl} onEnded={() => setIsPlaying(false)} onPause={() => setIsPlaying(false)} className="hidden" />
                <div className="flex gap-2">
                  <Button onClick={togglePlayback} variant="outline" className="flex-1" disabled={currentProcessing}>
                    {isPlaying ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                    {isPlaying ? "暫停" : "試聽"}
                  </Button>
                  <Button onClick={resetRecording} variant="outline" className="flex-1" disabled={currentProcessing}>
                    重新選擇
                  </Button>
                </div>
                
                {/* **核心修正：只在需要分析的模式下顯示按鈕** */}
                {(originalText || quizData) && (
                  <Button onClick={handleUpload} disabled={currentProcessing || !audioBlob} className="w-full gradient-bg text-white">
                    {currentProcessing ? "分析中..." : "上傳並分析"}
                  </Button>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
