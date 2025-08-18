import React from 'react';
import ResultsDisplay from './ResultsDisplay';
import ListeningClozeResults from './ListeningClozeResults';
import SentenceMakingResults from './SentenceMakingResults';

export default function UnifiedResultsDisplay({ session, targets, activityType }) {
    // 根據活動類型選擇對應的結果顯示組件
    switch (activityType) {
        case 'listening_cloze':
            return (
                <ListeningClozeResults 
                    resultsData={{
                        results: session.answers || [],
                        totalScore: session.percentage_score || 0,
                        correctCount: (session.answers || []).filter(a => a.is_correct).length,
                        totalQuestions: (session.answers || []).length,
                        timeSpent: session.time_spent_seconds || 0,
                    }}
                    lessonTitle="課文練習"
                    isHistoryView={true}
                />
            );
            
        case 'sentence_making':
            return (
                <SentenceMakingResults 
                    resultsData={session}
                    lessonTitle="造句練習"
                    isHistoryView={true}
                />
            );
            
        case 'speaking_practice':
            return (
                <div className="p-6 bg-green-50 rounded-lg border border-green-200">
                    <h3 className="text-lg font-semibold text-green-800 mb-2">🎤 口說練習結果</h3>
                    <p className="text-green-700">分數：{Math.round(session.percentage_score || 0)} 分</p>
                    <p className="text-green-600 mt-2">練習時間：{Math.round(session.time_spent_seconds || 0)} 秒</p>
                    {/* **核心改動：修正 JSX 註解語法** */}
                    {session.detailed_feedback && (
                        <div className="mt-4 p-3 bg-white rounded border">
                            <p className="font-medium text-gray-700">AI 回饋：</p>
                            <p className="text-gray-600 mt-1">{session.detailed_feedback}</p>
                        </div>
                    )}
                </div>
            );
            
        case 'reading_assessment':
        default:
            // 朗讀評估使用原本的 ResultsDisplay
            return <ResultsDisplay session={session} targets={targets} />;
    }
}