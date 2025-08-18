import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle2, XCircle, AlertTriangle, BookOpen, Volume2, Lightbulb, RefreshCw, Eye, EyeOff, Pause } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function IntelligentAnalysisDisplay({ session, originalText }) {
  const [showDetails, setShowDetails] = useState(true);
  const [playingAudio, setPlayingAudio] = useState(null);

  if (!session.annotated_segments || session.annotated_segments.length === 0) {
    return (
      <Card className="border-gray-200 bg-gray-50">
        <CardContent className="p-6 text-center">
          <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="font-semibold text-gray-600">AI 智能分析暫時無法提供</p>
          <p className="text-sm text-gray-500 mt-2">系統正在處理您的朗讀資料，請稍後重新整理頁面。</p>
        </CardContent>
      </Card>
    );
  }

  // 統計數據
  const correctSegments = session.annotated_segments.filter(s => s.status === 'correct');
  const errorSegments = session.annotated_segments.filter(s => s.status === 'error');
  const missingSegments = session.annotated_segments.filter(s => s.status === 'missing');
  const totalSegments = session.annotated_segments.length;

  // 核心修正：同時處理讀錯與遺漏錯誤
  const errors = session.errors || [];
  const readingErrors = errors.filter(e => e.error_type === '讀錯');
  const missingErrors = errors.filter(e => e.error_type === '遺漏');

  const playStandardPronunciation = (text, errorId) => {
    if ('speechSynthesis' in window) {
      if (playingAudio) {
        window.speechSynthesis.cancel();
        setPlayingAudio(null);
      }
      if (playingAudio === errorId) return;

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'zh-TW';
      utterance.rate = 0.7;
      utterance.onstart = () => setPlayingAudio(errorId);
      utterance.onend = () => setPlayingAudio(null);
      utterance.onerror = () => setPlayingAudio(null);
      window.speechSynthesis.speak(utterance);
    } else {
      alert('您的瀏覽器不支援語音合成功能');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'correct': return 'border-l-4 border-l-green-500 bg-green-50';
      case 'error': return 'border-l-4 border-l-red-500 bg-red-50';
      case 'missing': return 'border-l-4 border-l-orange-500 bg-orange-50';
      default: return 'border-l-4 border-l-gray-500 bg-gray-50';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'correct': return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      case 'error': return <XCircle className="w-5 h-5 text-red-600" />;
      case 'missing': return <AlertTriangle className="w-5 h-5 text-orange-600" />;
      default: return <BookOpen className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'correct': return <Badge className="bg-green-500 text-white px-3 py-1 rounded-full">正確</Badge>;
      case 'error': return <Badge className="bg-red-500 text-white px-3 py-1 rounded-full">讀錯</Badge>;
      case 'missing': return <Badge className="bg-orange-500 text-white px-3 py-1 rounded-full">遺漏</Badge>;
      default: return <Badge className="bg-gray-500 text-white px-3 py-1 rounded-full">未知</Badge>;
    }
  };

  const ErrorCard = ({ error, index, type }) => (
    <motion.div
      key={`${type}-${index}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="p-4 bg-white rounded-lg border border-red-200 shadow-sm"
    >
      <div className="flex items-start justify-between mb-3">
        <Badge className={type === '遺漏' ? 'bg-orange-100 text-orange-800' : 'bg-red-100 text-red-800'}>
          {type}
        </Badge>
        <Button 
          variant="ghost" 
          size="sm" 
          className="gap-1 hover:bg-gray-100"
          onClick={() => playStandardPronunciation(error.expected, `${type}-${index}`)}
        >
          {playingAudio === `${type}-${index}` ? (
            <Pause className="w-4 h-4 text-gray-500" />
          ) : (
            <Volume2 className="w-4 h-4 text-gray-500" />
          )}
        </Button>
      </div>
      
      <div className="space-y-3">
        <div className="flex items-start gap-2">
          <span className="text-sm font-medium text-gray-600 min-w-[50px]">正確：</span>
          <span className="text-green-700 bg-green-50 px-2 py-1 rounded font-medium">
            {error.expected}
          </span>
        </div>
        
        {type === '讀錯' && (
          <div className="flex items-start gap-2">
            <span className="text-sm font-medium text-gray-600 min-w-[50px]">您讀：</span>
            <span className="text-red-700 bg-red-50 px-2 py-1 rounded font-medium">
              {error.actual || '未偵測到'}
            </span>
          </div>
        )}
        
        {error.suggestion && (
          <div className="p-3 bg-blue-50 rounded border-l-4 border-l-blue-400">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <span className="text-sm text-blue-800">{error.suggestion}</span>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* AI 智能朗讀分析標題與統計 */}
      <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-800 text-xl">
            <BookOpen className="w-6 h-6" />
            AI 智能朗讀分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-green-100 rounded-lg">
              <CheckCircle2 className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-green-700">{correctSegments.length}</div>
              <div className="text-sm text-green-600">片段</div>
              <div className="text-xs text-green-500 mt-1">正確</div>
            </div>
            
            <div className="text-center p-4 bg-red-100 rounded-lg">
              <XCircle className="w-8 h-8 text-red-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-red-700">{errorSegments.length}</div>
              <div className="text-sm text-red-600">片段</div>
              <div className="text-xs text-red-500 mt-1">讀錯</div>
            </div>
            
            <div className="text-center p-4 bg-orange-100 rounded-lg">
              <AlertTriangle className="w-8 h-8 text-orange-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-orange-700">{missingSegments.length}</div>
              <div className="text-sm text-orange-600">片段</div>
              <div className="text-xs text-orange-500 mt-1">遺漏</div>
            </div>
            
            <div className="text-center p-4 bg-blue-100 rounded-lg">
              <BookOpen className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-blue-700">{totalSegments}</div>
              <div className="text-sm text-blue-600">片段</div>
              <div className="text-xs text-blue-500 mt-1">總計</div>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">逐句分析對比</h3>
            <Button
              onClick={() => setShowDetails(!showDetails)}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              {showDetails ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              {showDetails ? '隱藏詳情' : '顯示詳情'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 逐句分析對比 */}
      <AnimatePresence>
        {showDetails && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            {session.annotated_segments.map((segment, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`p-4 rounded-lg ${getStatusColor(segment.status)}`}
              >
                <div className="flex items-center gap-3 mb-3">
                  {getStatusIcon(segment.status)}
                  {getStatusBadge(segment.status)}
                  <span className="text-sm font-medium text-gray-700">第 {index + 1} 個片段</span>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <span className="text-sm font-medium text-gray-600 min-w-[50px]">原文：</span>
                    <span className="text-gray-900 font-medium">{segment.text}</span>
                  </div>
                  
                  {segment.status === 'correct' && segment.actual && (
                    <div className="flex items-start gap-2">
                      <span className="text-sm font-medium text-gray-600 min-w-[50px]">實讀：</span>
                      <span className="text-gray-900">{segment.actual}</span>
                    </div>
                  )}
                  
                  {segment.status === 'error' && segment.actual && (
                    <div className="flex items-start gap-2">
                      <span className="text-sm font-medium text-gray-600 min-w-[50px]">實讀：</span>
                      <span className="text-red-600 font-medium">{segment.actual}</span>
                    </div>
                  )}
                  
                  {segment.status === 'missing' && (
                    <div className="bg-orange-100 px-3 py-2 rounded text-orange-700 font-medium text-sm">
                      未明讀此片段
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 核心修正：恢復完整的錯字詞練習區塊 */}
      {(readingErrors.length > 0 || missingErrors.length > 0) && (
        <Card className="border-yellow-200 bg-gradient-to-r from-yellow-50 to-amber-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <AlertTriangle className="w-5 h-5" />
              錯字詞練習
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* 遺漏錯誤 */}
            {missingErrors.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <AlertTriangle className="w-4 h-4 text-orange-600" />
                  <h3 className="font-semibold text-orange-800">遺漏錯誤</h3>
                  <Badge variant="outline" className="bg-orange-50 text-orange-700">
                    {missingErrors.length} 個
                  </Badge>
                </div>
                <div className="space-y-4">
                  {missingErrors.map((error, index) => (
                    <ErrorCard key={`missing-${index}`} error={error} index={index} type="遺漏" />
                  ))}
                </div>
              </div>
            )}

            {/* 讀錯錯誤 */}
            {readingErrors.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <RefreshCw className="w-4 h-4 text-red-600" />
                  <h3 className="font-semibold text-red-800">讀錯錯誤</h3>
                  <Badge variant="outline" className="bg-red-50 text-red-700">
                    {readingErrors.length} 個
                  </Badge>
                </div>
                <div className="space-y-4">
                  {readingErrors.map((error, index) => (
                    <ErrorCard key={`reading-${index}`} error={error} index={index} type="讀錯" />
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* AI 詳細分析與建議 */}
      {session.detailed_analysis && (
        <Card className="border-teal-200 bg-gradient-to-r from-teal-50 to-cyan-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-teal-800">
              <Lightbulb className="w-5 h-5" />
              AI 詳細分析與建議
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-4 bg-white rounded-lg border border-teal-200">
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {session.detailed_analysis}
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}