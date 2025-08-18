import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, RefreshCw, Volume2, Lightbulb, Play, Pause } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function ErrorPractice({ errors, session }) {
  const [playingAudio, setPlayingAudio] = useState(null);

  // **核心修正：調試用 - 打印所有數據**
  console.log('[ErrorPractice] 收到的 errors:', errors);
  console.log('[ErrorPractice] 收到的 session:', session);

  // **修正：從多個來源獲取錯誤數據**
  let allErrors = [];
  
  // 方法1：直接從 props 傳入的 errors
  if (errors && Array.isArray(errors) && errors.length > 0) {
    allErrors = [...errors];
  }
  
  // 方法2：從 session.errors 獲取
  if (session && session.errors && Array.isArray(session.errors) && session.errors.length > 0) {
    allErrors = [...allErrors, ...session.errors];
  }
  
  // 方法3：從 annotated_segments 中推導錯誤
  if (session && session.annotated_segments && Array.isArray(session.annotated_segments)) {
    const derivedErrors = [];
    session.annotated_segments.forEach((segment, index) => {
      if (segment.status === 'error') {
        derivedErrors.push({
          expected: segment.text,
          actual: segment.actual || '未偵測到',
          error_type: '讀錯',
          suggestion: `請仔細練習「${segment.text}」的發音`
        });
      } else if (segment.status === 'missing') {
        derivedErrors.push({
          expected: segment.text,
          actual: '',
          error_type: '遺漏',
          suggestion: `您遺漏了「${segment.text}」，請完整朗讀所有內容`
        });
      }
    });
    allErrors = [...allErrors, ...derivedErrors];
  }

  // 去重
  const uniqueErrors = allErrors.filter((error, index, self) => 
    index === self.findIndex(e => e.expected === error.expected && e.error_type === error.error_type)
  );

  console.log('[ErrorPractice] 最終錯誤列表:', uniqueErrors);

  if (!uniqueErrors || uniqueErrors.length === 0) {
    console.log('[ErrorPractice] 沒有錯誤，不顯示組件');
    return null;
  }

  // 分類錯誤類型
  const missingErrors = uniqueErrors.filter(error => error.error_type === '遺漏');
  const readingErrors = uniqueErrors.filter(error => error.error_type === '讀錯');

  // 使用 Web Speech API 進行標準發音
  const playStandardPronunciation = (text, errorId) => {
    if ('speechSynthesis' in window) {
      // 停止當前播放
      if (playingAudio) {
        speechSynthesis.cancel();
        setPlayingAudio(null);
      }

      if (playingAudio === errorId) {
        return; // 如果點擊的是同一個，則停止
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'zh-TW'; // 繁體中文
      utterance.rate = 0.7; // 較慢的語速便於學習
      utterance.pitch = 1.0;
      
      utterance.onstart = () => setPlayingAudio(errorId);
      utterance.onend = () => setPlayingAudio(null);
      utterance.onerror = () => setPlayingAudio(null);

      speechSynthesis.speak(utterance);
    } else {
      alert('您的瀏覽器不支援語音合成功能');
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
    <Card className="border-yellow-200 bg-gradient-to-r from-yellow-50 to-amber-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-yellow-800">
          <AlertTriangle className="w-5 h-5" />
          錯字詞練習
          <Badge variant="outline" className="bg-yellow-50 text-yellow-700">
            共 {uniqueErrors.length} 個錯誤
          </Badge>
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

        {/* 練習建議 */}
        <div className="mt-6 p-4 bg-teal-50 rounded-lg border border-teal-200">
          <div className="flex items-start gap-2 mb-3">
            <Lightbulb className="w-5 h-5 text-teal-600 mt-0.5 flex-shrink-0" />
            <h3 className="font-semibold text-teal-800">練習建議</h3>
          </div>
          <div className="space-y-2 text-sm text-teal-700">
            <div className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 bg-teal-500 rounded-full mt-2 flex-shrink-0"></span>
              <span>點擊 🔊 聽取正確發音</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 bg-teal-500 rounded-full mt-2 flex-shrink-0"></span>
              <span>反覆練習錯誤的詞語，注意發音細節</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 bg-teal-500 rounded-full mt-2 flex-shrink-0"></span>
              <span>放慢語速，確保每個詞都清楚發音</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 bg-teal-500 rounded-full mt-2 flex-shrink-0"></span>
              <span>多次練習後再次錄音，追蹤改進效果</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}