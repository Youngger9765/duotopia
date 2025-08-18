
import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Target, Clock, BarChart3, MessageSquare, Play, Pause, Volume2, CheckCircle2, XCircle, User, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import ErrorPractice from "./ErrorPractice";
import IntelligentAnalysisDisplay from './IntelligentAnalysisDisplay';

import { improvedSpeechAnalysis } from "@/api/functions";

export default function ResultsDisplay({ session, targets, originalText, onDebugNotification, onSessionUpdate }) {
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [analysisMessage, setAnalysisMessage] = React.useState('');
  const audioRef = React.useRef(null);

  const accuracy = session.percentage_score || 0;
  const readingTime = session.time_spent_seconds || 0;
  const wordsPerMinute = session.words_per_minute || 0;
  
  const aiAnalysis = session.detailed_analysis && session.detailed_analysis.trim() 
    ? session.detailed_analysis 
    : session.detailed_feedback;
    
  const hasErrors = (session.errors && session.errors.length > 0) || 
                   (session.annotated_segments && session.annotated_segments.some(s => s.status === 'error' || s.status === 'missing'));

  const handleRerunAnalysis = async () => {
    setIsAnalyzing(true);
    setAnalysisMessage('正在重新評估...');
    
    try {
      console.log('[ResultsDisplay] 開始重新評估，Session ID:', session.id);
      
      if (!session.audio_url || !originalText) {
        throw new Error('缺少必要資料：音檔 URL 或原文');
      }

      setAnalysisMessage('調用 AI 分析函式...');
      const response = await improvedSpeechAnalysis({
        audio_url: session.audio_url,
        original_text: originalText
      });

      console.log('[ResultsDisplay] AI 分析回應:', response);

      if (response.error || response.status >= 400 || !response.data) {
        throw new Error(response.error?.message || response.data?.error || 'AI 分析失敗');
      }

      if (response.data) {
        setAnalysisMessage('更新資料庫記錄...');
        
        const { ActivityResult } = await import('@/api/entities');
        
        const updatedData = {
          transcribed_text: response.data.transcribed_text,
          punctuated_transcribed_text: response.data.punctuated_transcribed_text,
          time_spent_seconds: response.data.time_spent_seconds,
          words_per_minute: response.data.words_per_minute,
          annotated_segments: response.data.annotated_segments,
          detailed_feedback: response.data.detailed_analysis,
          percentage_score: response.data.accuracy_percentage,
          total_score: response.data.accuracy_percentage,
        };
        
        console.log('[ResultsDisplay] 準備更新資料庫，ID:', session.id, '資料:', updatedData);
        
        const updatedRecord = await ActivityResult.update(session.id, updatedData);
        console.log('[ResultsDisplay] 資料庫更新成功:', updatedRecord);
        
        setAnalysisMessage('評估完成！頁面資料已更新');
        
        if (onSessionUpdate) {
          const updatedSession = { ...session, ...updatedData };
          console.log('[ResultsDisplay] 通知父組件更新 session:', updatedSession);
          onSessionUpdate(updatedSession);
        }
        
      } else {
        throw new Error('AI 分析函式沒有回傳任何資料');
      }
      
    } catch (error) {
      console.error('[ResultsDisplay] 重新評估失敗:', error);
      setAnalysisMessage(`重新評估失敗: ${error.message}`);
      
      setTimeout(() => {
        setAnalysisMessage('');
      }, 5000);
    } finally {
      setIsAnalyzing(false);
      setTimeout(() => {
        if (!analysisMessage.includes('失敗')) {
          setAnalysisMessage('');
        }
      }, 3000);
    }
  };

  const getAccuracyColor = (percentage) => {
    if (percentage >= 90) return "text-green-600";
    if (percentage >= 70) return "text-yellow-600";
    return "text-red-600";
  };

  const speedInfo = ((wpm) => {
    if (wpm >= 200) return { level: '流暢', color: 'text-green-600', description: '朗讀速度非常理想' };
    if (wpm >= 120) return { level: '良好', color: 'text-blue-600', description: '朗讀速度適中' };
    if (wpm >= 60) return { level: '緩慢', color: 'text-yellow-600', description: '朗讀速度稍慢，可以加快一些' };
    return { level: '很慢', color: 'text-red-600', description: '朗讀速度較慢，需要多加練習' };
  })(wordsPerMinute);

  const togglePlayback = () => {
    const audio = audioRef.current;
    if (audio) {
      if (isPlaying) {
        audio.pause();
      } else {
        audio.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const hasTargets = targets && (targets.target_wpm || targets.target_accuracy);
  const wpmMet = hasTargets && targets.target_wpm ? wordsPerMinute >= targets.target_wpm : false;
  const accuracyMet = hasTargets && targets.target_accuracy ? accuracy >= targets.target_accuracy : false;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* 音檔播放器 */}
      {session.audio_url && (
        <audio ref={audioRef} onEnded={() => setIsPlaying(false)} preload="metadata">
          <source src={session.audio_url} type="audio/webm" />
          <source src={session.audio_url} type="audio/mp3" />
          <source src={session.audio_url} type="audio/wav" />
          您的瀏覽器不支援音檔播放。
        </audio>
      )}

      {/* 成績總覽卡片 */}
      <Card className="bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200">
        <CardHeader>
          <CardTitle className="text-xl text-center flex items-center justify-center gap-2">
            <Target className="w-6 h-6 text-emerald-600" />
            朗讀成績總覽
            {hasTargets && targets.set_by_teacher && (
                <Badge variant="default" className="bg-blue-600 text-white ml-2">
                    <User className="w-3 h-3 mr-1" />
                    老師指定目標
                </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-sm text-gray-500">正確率</p>
               <div className="flex items-baseline justify-center gap-1">
                 <p className={`text-3xl font-bold ${getAccuracyColor(accuracy)}`}>{accuracy.toFixed(1)}%</p>
                 {hasTargets && <p className="text-lg text-gray-500">/ {targets.target_accuracy}%</p>}
              </div>
              {hasTargets && (
                <div className="flex items-center justify-center gap-1 mt-1">
                  {accuracyMet ? (
                    <><CheckCircle2 className="w-4 h-4 text-green-500" /><span className="text-green-600 text-xs">達標</span></>
                  ) : (
                    <><XCircle className="w-4 h-4 text-red-500" /><span className="text-red-600 text-xs">未達標</span></>
                  )}
                </div>
              )}
            </div>
            <div>
              <p className="text-sm text-gray-500">流暢度 (字/分鐘)</p>
              <div className="flex items-baseline justify-center gap-1">
                <p className={`text-3xl font-bold ${speedInfo.color}`}>{Math.round(wordsPerMinute)}</p>
                 {hasTargets && <p className="text-lg text-gray-500">/ {targets.target_wpm}</p>}
              </div>
              {hasTargets && (
                <div className="flex items-center justify-center gap-1 mt-1">
                  {wpmMet ? (
                    <><CheckCircle2 className="w-4 h-4 text-green-500" /><span className="text-green-600 text-xs">達標</span></>
                  ) : (
                    <><XCircle className="w-4 h-4 text-red-500" /><span className="text-red-600 text-xs">未達標</span></>
                  )}
                </div>
              )}
            </div>
            <div>
              <p className="text-sm text-gray-500">朗讀時間</p>
              <p className="text-3xl font-bold text-blue-600">{readingTime}</p>
              <p className="text-xs text-gray-500">秒</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 錄音內容與 STT 結果 */}
      <Card className="border-orange-200 bg-gradient-to-r from-orange-50 to-amber-50">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2">
              <Volume2 className="w-5 h-5 text-orange-600" />
              錄音內容
            </CardTitle>
            {session.audio_url && (
              <Button onClick={togglePlayback} variant="outline" size="sm" className="gap-2">
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                {isPlaying ? "暫停播放" : "播放錄音"}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-700 mb-2">原文</h4>
            <div className="p-4 bg-white rounded-lg border-l-4 border-l-gray-400">
              <p className="text-gray-800 leading-relaxed">
                {originalText || "無原文內容"}
              </p>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-700 mb-2">加標點後結果</h4>
            <div className="p-4 bg-white rounded-lg border-l-4 border-l-blue-400">
              <p className="text-gray-800 leading-relaxed">
                {session.punctuated_transcribed_text || session.transcribed_text || "無法取得語音辨識結果"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI 智能回饋區塊 */}
      <Card className="border-purple-200 bg-gradient-to-r from-purple-50 to-pink-50">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-purple-600" />
              AI 智能回饋
            </CardTitle>
            <Button 
                onClick={handleRerunAnalysis}
                disabled={isAnalyzing || !session.audio_url || !originalText}
                variant="outline" 
                size="sm" 
                className="gap-2"
              >
                {isAnalyzing ? (
                  <div className="w-4 h-4 animate-spin rounded-full border-2 border-purple-600 border-t-transparent" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                {isAnalyzing ? "評估中..." : "重新評估"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <AnimatePresence>
            {analysisMessage && (
                <motion.div
                    initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                    animate={{ opacity: 1, height: 'auto', marginBottom: '1rem' }}
                    exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                    className={`p-3 rounded-lg border-l-4 text-sm font-medium overflow-hidden ${
                        analysisMessage.includes('失敗') || analysisMessage.includes('錯誤') 
                        ? 'bg-red-50 border-l-red-500 text-red-800' 
                        : analysisMessage.includes('完成')
                        ? 'bg-green-50 border-l-green-500 text-green-800'
                        : 'bg-blue-50 border-l-blue-500 text-blue-800'
                    }`}
                >
                    <div className="flex items-center gap-3">
                        {isAnalyzing && (
                        <div className="w-5 h-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                        )}
                        <p>{analysisMessage}</p>
                    </div>
                </motion.div>
            )}
          </AnimatePresence>

          {aiAnalysis ? (
            <div className="p-4 bg-white rounded-lg border-l-4 border-l-purple-500">
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {aiAnalysis}
              </p>
            </div>
          ) : (
            <div className="p-4 bg-yellow-50 rounded-lg border-l-4 border-l-yellow-500">
              <p className="text-yellow-800 font-medium mb-2">AI 回饋暫時無法提供</p>
              <p className="text-yellow-700 text-sm">
                系統可能仍在分析您的朗讀，或您可以點擊上方「重新評估」按鈕。
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 智能分析組件 */}
      {session.annotated_segments && session.annotated_segments.length > 0 ? (
        <IntelligentAnalysisDisplay 
          session={session} 
          originalText={originalText}
        />
      ) : (
        <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-800">
              <BarChart3 className="w-5 h-5" />
              AI 智能朗讀分析
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-6">
              <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="font-semibold text-gray-600">智能分析處理中</p>
              <p className="text-sm text-gray-500 mt-2">系統正在分析您的朗讀表現，請稍候...</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 核心修正：強化錯字練習區塊的顯示邏輯 */}
      <ErrorPractice 
        errors={session.errors || []}
        session={session}
        onDebugNotification={onDebugNotification}
      />
    </div>
  );
}
