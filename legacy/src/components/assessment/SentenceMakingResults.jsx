import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Check, X, Lightbulb, PenTool } from 'lucide-react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

export default function SentenceMakingResults({ resultsData, lessonTitle, isHistoryView = false }) {
    if (!resultsData || !resultsData.answers) {
        return (
            <div className="text-center p-8">
                <p className="text-gray-600">無法載入造句結果，請稍後再試。</p>
            </div>
        );
    }
    
    const { answers, percentage_score, time_spent_seconds } = resultsData;
    const totalQuestions = answers.length;
    const averageScore = percentage_score || 0;

    const getScoreColor = (score) => {
        if (score >= 90) return 'text-green-600';
        if (score >= 70) return 'text-yellow-600';
        return 'text-red-600';
    };

    const getScoreBadge = (score) => {
        if (score >= 90) return { text: '優秀', class: 'bg-green-100 text-green-800' };
        if (score >= 70) return { text: '良好', class: 'bg-yellow-100 text-yellow-800' };
        if (score >= 50) return { text: '及格', class: 'bg-blue-100 text-blue-800' };
        return { text: '需加強', class: 'bg-red-100 text-red-800' };
    };

    const overallBadge = getScoreBadge(averageScore);

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
                <CardHeader>
                    <CardTitle className="text-xl text-center flex items-center justify-center gap-2">
                        <PenTool className="w-6 h-6 text-purple-600" />
                        造句練習結果 - {lessonTitle}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                        <div>
                            <p className="text-sm text-gray-500">平均分數</p>
                            <p className={`text-3xl font-bold ${getScoreColor(averageScore)}`}>{Math.round(averageScore)}</p>
                            <Badge className={overallBadge.class}>{overallBadge.text}</Badge>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500">造句題數</p>
                            <p className="text-3xl font-bold text-gray-700">{totalQuestions}</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500">花費時間</p>
                            <p className="text-3xl font-bold text-gray-700">{Math.round(time_spent_seconds || 0)} 秒</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <div>
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-amber-500" />
                    逐題造句分析
                </h3>
                <ScrollArea className="h-[500px] border rounded-lg p-4 bg-white">
                    <div className="space-y-6">
                        {answers.map((item, index) => {
                            const scoreBadge = getScoreBadge(item.score || 0);
                            
                            return (
                                <div key={index} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <span className="font-semibold text-gray-800">第 {index + 1} 題</span>
                                            <Badge className={scoreBadge.class}>{scoreBadge.text}</Badge>
                                            <span className={`font-bold ${getScoreColor(item.score || 0)}`}>
                                                {Math.round(item.score || 0)} 分
                                            </span>
                                        </div>
                                    </div>
                                    
                                    <div className="space-y-3">
                                        <div>
                                            <p className="text-sm font-medium text-gray-600">📝 關鍵字：</p>
                                            <p className="font-mono bg-blue-50 p-2 rounded border-l-4 border-blue-400">
                                                {item.question_content || '未知關鍵字'}
                                            </p>
                                        </div>
                                        
                                        <div>
                                            <p className="text-sm font-medium text-gray-600">✍️ 你的造句：</p>
                                            <p className="bg-white p-3 rounded border-l-4 border-purple-400 leading-relaxed">
                                                {item.student_answer || '未完成造句'}
                                            </p>
                                        </div>
                                        
                                        {item.feedback && (
                                            <div>
                                                <p className="text-sm font-medium text-gray-600 flex items-center gap-1">
                                                    <Lightbulb className="w-4 h-4 text-amber-500" />
                                                    AI 老師評語：
                                                </p>
                                                <p className="bg-amber-50 border border-amber-200 p-3 rounded text-amber-800 leading-relaxed">
                                                    {item.feedback}
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </ScrollArea>
            </div>
        </div>
    );
}