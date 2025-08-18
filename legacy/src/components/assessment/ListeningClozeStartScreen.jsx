import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Play, History, CheckCircle2 } from 'lucide-react';
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";

export default function ListeningClozeStartScreen({ lesson, previousResults, onStartPractice, onSelectResult }) {
    const hasHistory = previousResults && previousResults.length > 0;

    return (
        <div className="space-y-6">
            <Card className="text-center bg-white/90 backdrop-blur-sm shadow-lg border-0">
                <CardHeader>
                    <CardTitle className="text-2xl font-bold">{lesson.title}</CardTitle>
                    <CardDescription className="text-gray-600 mt-2">{lesson.content || '請準備好聆聽音檔並完成填空。'}</CardDescription>
                </CardHeader>
                <CardContent>
                    <Button onClick={onStartPractice} size="lg" className="bg-gradient-to-r from-teal-500 to-blue-500 text-white shadow-lg hover:scale-105 transition-transform duration-300">
                        <Play className="w-5 h-5 mr-2" />
                        開始練習
                    </Button>
                </CardContent>
            </Card>

            {hasHistory && (
                <div>
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-800">
                        <History className="w-5 h-5 text-gray-500" />
                        過去的練習記錄
                    </h3>
                    <div className="space-y-3">
                        {previousResults.map(result => {
                            const isAchieved = result.percentage_score >= 80;
                            return (
                                <div
                                    key={result.id}
                                    onClick={() => onSelectResult(result)}
                                    className="p-4 rounded-xl cursor-pointer transition-all duration-200 bg-white hover:bg-teal-50 border flex justify-between items-center shadow-sm"
                                >
                                    <div>
                                        <p className="font-semibold text-gray-800">
                                            第 {result.attempt_number} 次練習
                                        </p>
                                        <p className="text-sm text-gray-500 mt-1">
                                            {format(new Date(result.completed_at), "yyyy年MM月dd日 HH:mm", { locale: zhCN })}
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <Badge variant={isAchieved ? "default" : "secondary"} className={isAchieved ? "bg-green-100 text-green-800 border-green-200" : "bg-gray-100 text-gray-800"}>
                                            {isAchieved && <CheckCircle2 className="w-4 h-4 mr-1" />}
                                            正確率: {result.percentage_score ? result.percentage_score.toFixed(1) : '0.0'}%
                                        </Badge>
                                        <p className="text-sm text-gray-600 mt-1">
                                            耗時: {result.time_spent_seconds || 0} 秒
                                        </p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}