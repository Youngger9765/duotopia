import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Check, X, ArrowLeft, Plus } from 'lucide-react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

export default function ListeningClozeResults({ resultsData, onTryAgain, lessonTitle, isHistoryView = false }) {
    if (!resultsData || !resultsData.results) {
        return (
            <div className="text-center p-8">
                <p className="text-gray-600">無法載入結果，請稍後再試。</p>
                <Button onClick={onTryAgain} className="mt-4">返回</Button>
            </div>
        );
    }
    
    const { results, totalScore, correctCount, totalQuestions, timeSpent } = resultsData;

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <Card className="bg-gray-50 border-gray-200">
                <CardHeader>
                    <CardTitle className="text-xl text-center">練習總結 - {lessonTitle}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                        <div>
                            <p className="text-sm text-gray-500">總分數</p>
                            <p className="text-2xl font-bold text-teal-600">{Math.round(totalScore)}</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500">答對題數</p>
                            <p className="text-2xl font-bold">{correctCount} / {totalQuestions}</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500">正確率</p>
                            <p className="text-2xl font-bold">{totalQuestions > 0 ? Math.round((correctCount / totalQuestions) * 100) : 0}%</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500">花費時間</p>
                            <p className="text-2xl font-bold">{timeSpent} 秒</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <div>
                <h3 className="text-lg font-semibold mb-4">作答詳情</h3>
                <ScrollArea className="h-[400px] border rounded-lg p-4 bg-white">
                    <div className="space-y-4">
                        {results.map((item, index) => (
                            <div key={index} className={`p-4 rounded-lg ${item.is_correct ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                                <div className="flex items-start gap-4">
                                    <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${item.is_correct ? 'bg-green-500' : 'bg-red-500'}`}>
                                        {item.is_correct ? <Check className="w-4 h-4 text-white" /> : <X className="w-4 h-4 text-white" />}
                                    </div>
                                    <div className="flex-1">
                                        <p className="font-semibold text-gray-800 mb-2">第 {index + 1} 題：<span className="text-gray-600 font-normal">{item.question_content.replace('___', ` [ ${item.correct_answer} ] `)}</span></p>
                                        <div className="space-y-1 text-sm">
                                            <p><Badge variant="secondary">你的答案</Badge> <span className={`font-mono ${item.is_correct ? 'text-green-800' : 'text-red-800 line-through'}`}>{item.student_answer || '未作答'}</span></p>
                                            {!item.is_correct && <p><Badge variant="secondary" className="bg-green-200 text-green-900">正確答案</Badge> <span className="font-mono text-green-800">{item.correct_answer}</span></p>}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </ScrollArea>
            </div>
            
            {!isHistoryView && (
                 <div className="text-center mt-6">
                    <Button onClick={onTryAgain}>
                        <Plus className="mr-2 h-4 w-4" /> 再試一次
                    </Button>
                </div>
            )}
        </div>
    );
}