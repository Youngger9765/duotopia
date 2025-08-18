import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, Target } from "lucide-react";

export default function ProgressChart({ attempts, standards }) {
    if (!attempts || attempts.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="w-5 h-5" />
                        練習進度圖表
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8 text-gray-500">
                        完成練習後，這裡會顯示您的進步曲線
                    </div>
                </CardContent>
            </Card>
        );
    }

    const chartData = attempts.map(attempt => ({
        attempt: `第${attempt.attempt_number}次`,
        speed: attempt.words_per_minute,
        accuracy: attempt.accuracy_percentage,
        achieved: standards && 
            attempt.words_per_minute >= standards.target_wpm &&
            attempt.accuracy_percentage >= standards.target_accuracy
    }));

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    您的練習進度
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="attempt" />
                            <YAxis yAxisId="left" />
                            <YAxis yAxisId="right" orientation="right" />
                            <Tooltip 
                                content={({ active, payload, label }) => {
                                    if (active && payload && payload.length) {
                                        const data = payload[0]?.payload;
                                        return (
                                            <div className="p-3 bg-white border rounded-md shadow-lg">
                                                <p className="font-bold">{label}</p>
                                                <p className="text-blue-600">語速: {payload[0]?.value} 字/分</p>
                                                <p className="text-green-600">正確率: {payload[1]?.value}%</p>
                                                {data?.achieved && (
                                                    <p className="text-yellow-600 text-sm">✓ 達標</p>
                                                )}
                                            </div>
                                        );
                                    }
                                    return null;
                                }}
                            />
                            <Line 
                                yAxisId="left" 
                                type="monotone" 
                                dataKey="speed" 
                                stroke="#0891b2" 
                                strokeWidth={2}
                                dot={{ fill: '#0891b2', strokeWidth: 2, r: 4 }}
                            />
                            <Line 
                                yAxisId="right" 
                                type="monotone" 
                                dataKey="accuracy" 
                                stroke="#059669" 
                                strokeWidth={2}
                                dot={{ fill: '#059669', strokeWidth: 2, r: 4 }}
                            />
                            
                            {/* 目標線 */}
                            {standards && (
                                <>
                                    <Line 
                                        yAxisId="left"
                                        type="monotone" 
                                        dataKey={() => standards.target_wpm}
                                        stroke="#ef4444" 
                                        strokeDasharray="5 5"
                                        dot={false}
                                        strokeWidth={1}
                                    />
                                    <Line 
                                        yAxisId="right"
                                        type="monotone" 
                                        dataKey={() => standards.target_accuracy}
                                        stroke="#f59e0b" 
                                        strokeDasharray="5 5"
                                        dot={false}
                                        strokeWidth={1}
                                    />
                                </>
                            )}
                        </LineChart>
                    </ResponsiveContainer>
                </div>
                
                {standards && (
                    <div className="mt-4 flex justify-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                            <div className="w-3 h-0.5 bg-red-400"></div>
                            <span className="text-gray-600">目標語速: {standards.target_wpm} 字/分</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <div className="w-3 h-0.5 bg-yellow-400"></div>
                            <span className="text-gray-600">目標正確率: {standards.target_accuracy}%</span>
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}