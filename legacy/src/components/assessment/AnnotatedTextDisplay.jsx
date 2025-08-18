import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BookOpen, CheckCircle2, XCircle, AlertCircle, Eye, EyeOff } from "lucide-react";

export default function AnnotatedTextDisplay({ segments, extraWords }) {
  const [showDetails, setShowDetails] = useState(true);

  if (!segments || segments.length === 0) {
    return (
      <Card className="border-gray-200">
        <CardContent className="p-6 text-center">
          <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">暫無朗讀分析數據</p>
        </CardContent>
      </Card>
    );
  }

  // 統計數據
  const stats = segments.reduce((acc, segment) => {
    acc[segment.status] = (acc[segment.status] || 0) + 1;
    return acc;
  }, {});

  const correctCount = stats.correct || 0;
  const errorCount = stats.error || 0;
  const missingCount = stats.missing || 0;
  const totalSegments = segments.length;

  return (
    <div className="space-y-6">
      {/* 分析統計概覽 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-green-50 border-green-200">
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <span className="font-semibold text-green-800">正確</span>
            </div>
            <div className="text-2xl font-bold text-green-700">{correctCount}</div>
            <div className="text-xs text-green-600">片段</div>
          </CardContent>
        </Card>

        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <XCircle className="w-5 h-5 text-red-600" />
              <span className="font-semibold text-red-800">讀錯</span>
            </div>
            <div className="text-2xl font-bold text-red-700">{errorCount}</div>
            <div className="text-xs text-red-600">片段</div>
          </CardContent>
        </Card>

        <Card className="bg-orange-50 border-orange-200">
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <AlertCircle className="w-5 h-5 text-orange-600" />
              <span className="font-semibold text-orange-800">遺漏</span>
            </div>
            <div className="text-2xl font-bold text-orange-700">{missingCount}</div>
            <div className="text-xs text-orange-600">片段</div>
          </CardContent>
        </Card>

        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <BookOpen className="w-5 h-5 text-blue-600" />
              <span className="font-semibold text-blue-800">總計</span>
            </div>
            <div className="text-2xl font-bold text-blue-700">{totalSegments}</div>
            <div className="text-xs text-blue-600">片段</div>
          </CardContent>
        </Card>
      </div>

      {/* 詳細分析切換 */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">逐句分析對比</h3>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowDetails(!showDetails)}
          className="gap-2"
        >
          {showDetails ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          {showDetails ? '隱藏詳情' : '顯示詳情'}
        </Button>
      </div>

      {showDetails && (
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              {segments.map((segment, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border-l-4 ${
                    segment.status === 'correct'
                      ? 'bg-green-50 border-l-green-500'
                      : segment.status === 'error'
                      ? 'bg-red-50 border-l-red-500'
                      : 'bg-orange-50 border-l-orange-500'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-1">
                      {segment.status === 'correct' && (
                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                      )}
                      {segment.status === 'error' && (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                      {segment.status === 'missing' && (
                        <AlertCircle className="w-5 h-5 text-orange-600" />
                      )}
                    </div>
                    
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            segment.status === 'correct'
                              ? 'default'
                              : segment.status === 'error'
                              ? 'destructive'
                              : 'secondary'
                          }
                          className="text-xs"
                        >
                          {segment.status === 'correct' ? '正確' : 
                           segment.status === 'error' ? '讀錯' : '遺漏'}
                        </Badge>
                        <span className="text-sm text-gray-500">第 {index + 1} 個片段</span>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-700">原文：</span>
                          <span className="text-sm text-gray-900 bg-gray-100 px-2 py-1 rounded">
                            {segment.text}
                          </span>
                        </div>
                        
                        {segment.status !== 'missing' && segment.actual && (
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-700">實讀：</span>
                            <span className={`text-sm px-2 py-1 rounded ${
                              segment.status === 'correct'
                                ? 'text-green-800 bg-green-100'
                                : 'text-red-800 bg-red-100'
                            }`}>
                              {segment.actual}
                            </span>
                          </div>
                        )}
                        
                        {segment.status === 'missing' && (
                          <div className="text-sm text-orange-700 bg-orange-100 px-2 py-1 rounded">
                            未朗讀此片段
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 多餘內容 */}
      {extraWords && extraWords.length > 0 && (
        <Card className="bg-purple-50 border-purple-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-purple-800">
              <AlertCircle className="w-5 h-5" />
              多餘朗讀內容
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {extraWords.map((word, index) => (
                <Badge key={index} variant="outline" className="bg-purple-100 text-purple-800 border-purple-300">
                  {word}
                </Badge>
              ))}
            </div>
            <p className="text-sm text-purple-700 mt-3">
              建議：避免加入原文以外的內容，專注於準確朗讀課文。
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}