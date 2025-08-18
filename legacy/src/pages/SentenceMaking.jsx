
import React, { useState, useEffect, useRef } from 'react';
import { Lesson } from '@/api/entities';
import { User } from '@/api/entities';
import { ActivityResult } from '@/api/entities';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, PenTool, CheckCircle2, XCircle, RefreshCw, Clock, Lightbulb, BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { InvokeLLM } from '@/api/integrations';
import ResultsDisplay from "../components/assessment/ResultsDisplay";
import HistoryTab from "../components/assessment/HistoryTab";
import SentenceMakingResults from "../components/assessment/SentenceMakingResults"; // 新增導入

export default function SentenceMakingPage() {
    const [lesson, setLesson] = useState(null);
    const [userSentences, setUserSentences] = useState({}); // 學生的造句答案
    const [currentKeywordIndex, setCurrentKeywordIndex] = useState(0);
    const [showResults, setShowResults] = useState(false); 
    const [currentStep, setCurrentStep] = useState('instruction'); // instruction, practice, results
    const [loading, setLoading] = useState(true);
    const [timeLeft, setTimeLeft] = useState(0);
    const [timerActive, setTimerActive] = useState(false);
    const [analyzing, setAnalyzing] = useState(false);
    // 修改 results 狀態，使其儲存完整的評分結果物件，包含 answers, total_score, detailed_feedback
    const [results, setResults] = useState(null); 
    // overallScore 和 overallFeedback 將從 results 物件中獲取，因此這些狀態可以移除或不再直接使用
    // const [overallScore, setOverallScore] = useState(0); 
    // const [overallFeedback, setOverallFeedback] = useState(''); 
    
    const timerRef = useRef(null);

    // New state variables for history functionality
    const [user, setUser] = useState(null);
    const [previousResults, setPreviousResults] = useState([]);
    const [selectedResult, setSelectedResult] = useState(null);
    const [activeTab, setActiveTab] = useState('practice'); // 'practice' 或 'history'

    useEffect(() => {
        loadUser(); // Load user and their previous results
        // lesson 載入依賴於 user 的載入，因為 loadPreviousResults 依賴於 currentUser
        // 因此將 loadLesson 移到 loadUser 內部或確保其在 currentUser 載入後調用
    }, []);

    useEffect(() => {
        // 在用戶載入後，如果 lesson 尚未載入，則載入課程
        if (user && !lesson) {
            loadLesson();
        }
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [user, lesson]); // 監聽 user 和 lesson 狀態，防止重複載入

    const loadUser = async () => {
        try {
            const currentUser = await User.me();
            setUser(currentUser);
            if (currentUser) {
                loadPreviousResults(currentUser);
            }
        } catch (error) {
            console.error('載入用戶資料失敗:', error);
        }
    };

    const loadPreviousResults = async (currentUser) => {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const lessonId = urlParams.get('lesson_id');
            
            if (!lessonId) return;
            
            // 載入該課程的歷史成績，按完成時間倒序排列
            const results = await ActivityResult.filter({
                lesson_id: lessonId,
                student_email: currentUser.email,
                activity_type: 'sentence_making'
            }, '-completed_at');
            
            console.log('載入的造句歷史記錄:', results);
            setPreviousResults(results);
        } catch (error) {
            console.error('載入歷史記錄失敗:', error);
        }
    };

    const loadLesson = async () => {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const lessonId = urlParams.get('lesson_id');
            
            console.log('URL參數:', window.location.search);
            console.log('獲取的lesson_id:', lessonId);
            
            if (!lessonId) {
                console.error('缺少 lesson_id 參數');
                setLoading(false);
                return;
            }

            const lessonData = await Lesson.get(lessonId);
            console.log('載入的課程資料:', lessonData);
            
            if (lessonData && lessonData.activity_type === 'sentence_making') {
                setLesson(lessonData);
                
                // 初始化用戶造句答案
                const initialSentences = {};
                lessonData.sentence_keywords?.forEach((_, index) => {
                    initialSentences[index] = '';
                });
                setUserSentences(initialSentences);
                
                // 設置計時器
                setTimeLeft((lessonData.time_limit_minutes || 10) * 60);
            } else {
                console.error('課程不存在或不是造句活動類型');
            }
        } catch (error) {
            console.error('載入課程失敗:', error);
        } finally {
            setLoading(false);
        }
    };

    const startTimer = () => {
        setTimerActive(true);
        timerRef.current = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1) {
                    handleSubmit(); // 時間到自動提交
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
    };

    const stopTimer = () => {
        setTimerActive(false);
        if (timerRef.current) {
            clearInterval(timerRef.current);
        }
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const startPractice = () => {
        setCurrentStep('practice');
        startTimer();
    };

    const handleSentenceChange = (keywordIndex, value) => {
        setUserSentences(prev => ({
            ...prev,
            [keywordIndex]: value
        }));
    };

    const nextKeyword = () => {
        if (currentKeywordIndex < lesson.sentence_keywords.length - 1) {
            setCurrentKeywordIndex(prev => prev + 1);
        }
    };

    const prevKeyword = () => {
        if (currentKeywordIndex > 0) {
            setCurrentKeywordIndex(prev => prev - 1);
        }
    };

    const handleSubmit = async () => {
        stopTimer();
        setAnalyzing(true);
        
        try {
            // 準備批改資料
            const sentences = lesson.sentence_keywords.map((_, index) => userSentences[index] || '');
            const keywords = lesson.sentence_keywords.map(kw => ({
                ...kw,
                language: kw.language || '繁體中文' // 確保有預設值
            }));
            
            console.log('開始批改造句...', { sentences, keywords });
            
            // 使用 InvokeLLM 進行批改
            const gradingPrompt = `你是一位專業的中文造句評分老師。請評分以下學生的造句練習：

評分標準：
1. 關鍵字使用 (30分)：是否正確使用指定的關鍵字
2. 語法正確性 (25分)：句子結構是否正確，語法是否通順
3. 語意完整性 (25分)：句子是否表達完整的意思
4. 創意表達 (20分)：用詞是否豐富，表達是否生動

造句題目：
${keywords.map((keyword, index) => `
第${index + 1}題：
關鍵字：${keyword.keyword}
關鍵字類型：${keyword.keyword_type || '單字'}
語言：${keyword.language || '繁體中文'}
範例句子：${keyword.example_sentence || '無'}
評分標準說明：${keyword.scoring_criteria || '請造出語法正確、語意完整的句子'}
學生造句：${sentences[index] || '未完成'}
`).join('\n')}

請為每個造句給出分數 (0-100) 和詳細評語，並計算總體平均分數。
請用${keywords[0]?.language || '繁體中文'}回應，語氣要鼓勵學生。`;

            const response = await InvokeLLM({
                prompt: gradingPrompt,
                response_json_schema: {
                    type: "object",
                    properties: {
                        results: {
                            type: "array",
                            items: {
                                type: "object",
                                properties: {
                                    keyword: { type: "string" },
                                    sentence: { type: "string" },
                                    score: { type: "number" },
                                    feedback: { type: "string" },
                                    suggestions: {
                                        type: "array",
                                        items: { type: "string" }
                                    },
                                    keyword_usage: { type: "string" },
                                    grammar_check: { type: "string" },
                                    creativity_score: { type: "number" }
                                }
                            }
                        },
                        overall_score: { type: "number" },
                        overall_feedback: { type: "string" }
                    }
                }
            });
            
            console.log('LLM 批改結果:', response);
            
            // 處理 LLM 回應，如果結構不完整則使用備用方案
            let gradingResponse;
            if (response && response.results) {
                gradingResponse = response;
            } else {
                // 備用的簡單評分邏輯
                console.log('LLM回應不完整，使用備用評分邏輯');
                gradingResponse = {
                    results: keywords.map((keyword, index) => {
                        const sentence = sentences[index] || '';
                        const hasKeyword = sentence.includes(keyword.keyword);
                        const hasContent = sentence.trim().length > 0;
                        
                        let score = 0;
                        if (!hasContent) {
                            score = 0;
                        } else if (hasKeyword) {
                            score = Math.floor(Math.random() * 20) + 75; // 75-95分
                        } else {
                            score = Math.floor(Math.random() * 20) + 40; // 40-60分
                        }
                        
                        return {
                            keyword: keyword.keyword,
                            sentence: sentence,
                            score: score,
                            feedback: !hasContent ? '請完成造句練習。' :
                                     hasKeyword ? `很好！您正確使用了關鍵字「${keyword.keyword}」，句子表達清楚。` :
                                     `請確保在句子中使用指定的關鍵字「${keyword.keyword}」。`,
                            suggestions: !hasContent ? ['請完成造句'] :
                                        hasKeyword ? ['可以嘗試更豐富的表達', '注意句子的流暢性'] :
                                        ['請在句子中包含關鍵字', '注意句子的完整性'],
                            keyword_usage: !hasContent ? 'poor' : hasKeyword ? 'good' : 'poor',
                            grammar_check: !hasContent ? 'poor' : 'fair',
                            creativity_score: !hasContent ? 0 : Math.floor(Math.random() * 10) + 10
                        };
                    }),
                    overall_score: 0,
                    overall_feedback: '請完成所有造句練習以獲得完整評分。'
                };
                
                // 計算平均分數
                const validScores = gradingResponse.results.filter(r => r.score > 0);
                if (validScores.length > 0) {
                    gradingResponse.overall_score = Math.round(validScores.reduce((sum, r) => sum + r.score, 0) / validScores.length);
                    
                    if (gradingResponse.overall_score >= 80) {
                        gradingResponse.overall_feedback = '造句表現優良！繼續保持這樣的水準。';
                    } else if (gradingResponse.overall_score >= 60) {
                        gradingResponse.overall_feedback = '造句表現不錯，建議多注意關鍵字的使用和句子的完整性。';
                    } else {
                        gradingResponse.overall_feedback = '造句需要多加練習，建議先完成所有題目。';
                    }
                }
            }
            
            // 轉換為 ActivityResult 格式
            const resultsForActivityResult = gradingResponse.results.map((result, index) => ({
                question_index: index,
                question_content: `請用「${result.keyword}」造句`, // Use LLM's keyword from the graded result
                student_answer: result.sentence,
                correct_answer: keywords[index]?.example_sentence || '', // Use the original lesson's example sentence
                is_correct: result.score >= 70, // Define 'correct' threshold
                score: result.score,
                feedback: result.feedback,
                additional_data: { // Store detailed feedback in additional_data
                    keyword_usage: result.keyword_usage || 'fair',
                    grammar_check: result.grammar_check || 'fair',
                    creativity_score: result.creativity_score || 0,
                    suggestions: result.suggestions || []
                }
            }));
            
            const timeSpent = (lesson.time_limit_minutes * 60) - timeLeft;
            
            // Calculate next attempt number
            const nextAttemptNumber = previousResults.length > 0 ? 
                Math.max(...previousResults.map(r => r.attempt_number || 1)) + 1 : 1;

            // 儲存結果到資料庫
            let activityResultData = null;
            try {
                if (!user) {
                    console.error("User not loaded, cannot save ActivityResult.");
                    throw new Error("User not loaded");
                }

                activityResultData = await ActivityResult.create({
                    student_id: user.id,
                    student_email: user.email,
                    lesson_id: lesson.id,
                    activity_type: 'sentence_making',
                    attempt_number: nextAttemptNumber,
                    total_score: gradingResponse.overall_score,
                    max_score: 100,
                    percentage_score: gradingResponse.overall_score,
                    time_spent_seconds: timeSpent,
                    answers: resultsForActivityResult,
                    detailed_feedback: gradingResponse.overall_feedback,
                    completed_at: new Date().toISOString(),
                    is_submitted: true // Mark as submitted
                });
                
                console.log('ActivityResult 儲存成功:', activityResultData);
                
                // Update historical results list
                setPreviousResults(prev => [activityResultData, ...prev]);

                // 同時儲存到 StudentProgress 以便在統計中顯示
                const { StudentProgress } = await import('@/api/entities'); // Lazy import for StudentProgress
                const progressResult = await StudentProgress.create({
                    student_id: user.id,
                    student_email: user.email,
                    lesson_id: lesson.id,
                    attempt_number: nextAttemptNumber,
                    words_per_minute: 0, // Sentence making activity does not calculate WPM
                    accuracy_percentage: gradingResponse.overall_score,
                    reading_time_seconds: timeSpent,
                    error_count: resultsForActivityResult.filter(r => !r.is_correct).length,
                    errors: resultsForActivityResult.filter(r => !r.is_correct).map(r => ({
                        expected: r.question_content,
                        actual: r.student_answer,
                        error_type: '造句待改進', // Custom error type for sentence making
                        suggestion: r.feedback
                    })),
                    detailed_analysis: gradingResponse.overall_feedback,
                    completed_at: new Date().toISOString(),
                    // Store complete grading results in annotated_segments (adapting for sentence making context)
                    annotated_segments: resultsForActivityResult.map(r => ({
                        text: r.question_content, // Storing the question content here as the 'actual' reference
                        status: r.is_correct ? 'correct' : 'error',
                        actual: r.student_answer // The actual sentence written by the student
                    })),
                    extra_words: [], // Not applicable for this activity type
                    comparative_feedback: gradingResponse.overall_feedback
                });

                console.log('StudentProgress 儲存成功:', progressResult);
                
            } catch (saveError) {
                console.warn('儲存結果時發生錯誤:', saveError);
                // 即使儲存失敗也繼續顯示結果
            }
            
            // 將完整的評分結果物件儲存到 results 狀態
            // 如果 activityResultData 成功儲存，則使用它，否則使用 LLM 的 gradingResponse 結構
            setResults(activityResultData || {
                answers: resultsForActivityResult,
                total_score: gradingResponse.overall_score,
                detailed_feedback: gradingResponse.overall_feedback
            });
            
            setCurrentStep('results');
            
        } catch (error) {
            console.error('提交造句失敗:', error);
            
            // 提供用戶友善的錯誤處理
            const errorMessage = error.message || '未知錯誤';
            if (errorMessage.includes('Network Error')) {
                alert('網路連線有問題，請檢查網路後重試。');
            } else {
                alert('批改系統暫時無法使用，請稍後再試。');
            }
        } finally {
            setAnalyzing(false);
        }
    };

    const handleSelectResult = (result) => {
        setSelectedResult(result);
        setActiveTab('history');
    };

    const startNewPractice = () => {
        // 重置所有狀態開始新練習
        setCurrentStep('instruction');
        setActiveTab('practice');
        setSelectedResult(null);
        setResults(null); // Reset results state
        
        setCurrentKeywordIndex(0);
        
        // Reset user sentences to be empty for a new practice
        const initialSentences = {};
        lesson?.sentence_keywords?.forEach((_, index) => {
            initialSentences[index] = '';
        });
        setUserSentences(initialSentences);

        setTimeLeft((lesson?.time_limit_minutes || 10) * 60);
        setTimerActive(false);
        
        if (timerRef.current) {
            clearInterval(timerRef.current);
        }
    };

    if (loading) {
        return (
            <div className="p-6 min-h-screen flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
        );
    }

    if (!lesson) {
        return (
            <div className="p-6 min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <p className="text-gray-600 mb-4">找不到指定的造句練習</p>
                    <Link to={createPageUrl("StudentDashboard")}>
                        <Button>返回課程列表</Button>
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 p-6">
            <div className="max-w-4xl mx-auto">
                {/* 頁面標題 */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <Link to={createPageUrl("StudentDashboard")}>
                            <Button variant="outline" size="sm">
                                <ArrowLeft className="w-4 h-4 mr-2" />
                                返回
                            </Button>
                        </Link>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">{lesson.title}</h1>
                            <div className="flex items-center gap-3 mt-2">
                                <Badge className="bg-indigo-100 text-indigo-800">造句活動</Badge>
                                <Badge variant="outline">{lesson.difficulty_level}</Badge>
                                <Badge variant="outline">
                                    <Clock className="w-3 h-3 mr-1" />
                                    {lesson.time_limit_minutes} 分鐘
                                </Badge>
                                {activeTab === 'practice' && currentStep === 'practice' && (
                                    <Badge variant="outline">
                                        第 {currentKeywordIndex + 1} / {lesson.sentence_keywords?.length || 0} 題
                                    </Badge>
                                )}
                            </div>
                        </div>
                    </div>
                    
                    {timerActive && activeTab === 'practice' && (
                        <div className="text-right">
                            <div className="text-sm text-gray-600">剩餘時間</div>
                            <div className={`text-2xl font-bold ${timeLeft <= 60 ? 'text-red-600' : 'text-gray-900'}`}>
                                {formatTime(timeLeft)}
                            </div>
                        </div>
                    )}
                </div>

                {/* 標籤頁 */}
                <div className="flex gap-2 mb-6">
                    <Button
                        variant={activeTab === 'practice' ? 'default' : 'outline'}
                        onClick={() => setActiveTab('practice')}
                        className="flex items-center gap-2"
                    >
                        <PenTool className="w-4 h-4" />
                        {currentStep === 'instruction' ? '開始造句' : currentStep === 'practice' ? '造句中' : '造句結果'}
                    </Button>
                    <Button
                        variant={activeTab === 'history' ? 'default' : 'outline'}
                        onClick={() => setActiveTab('history')}
                        className="flex items-center gap-2"
                    >
                        <BarChart3 className="w-4 h-4" />
                        歷史記錄 ({previousResults.length})
                    </Button>
                </div>

                <AnimatePresence mode="wait">
                    {activeTab === 'practice' && (
                        <motion.div
                            key="practice-tab"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                        >
                            {/* 說明階段 */}
                            {currentStep === 'instruction' && (
                                <motion.div
                                    key="instruction"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -20 }}
                                    className="space-y-6"
                                >
                                    <Card className="border-l-4 border-l-indigo-500">
                                        <CardHeader>
                                            <CardTitle className="flex items-center gap-2">
                                                <PenTool className="w-5 h-5 text-indigo-600" />
                                                造句練習說明
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="space-y-4">
                                            <div className="bg-indigo-50 p-4 rounded-lg">
                                                <h3 className="font-semibold text-indigo-900 mb-2">練習方式：</h3>
                                                <p className="text-indigo-800">根據老師提供的關鍵字、片語或句型，創作完整的句子。</p>
                                            </div>
                                            
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                <div className="text-center p-4 bg-gray-50 rounded-lg">
                                                    <div className="text-2xl font-bold text-indigo-600 mb-1">
                                                        {lesson.sentence_keywords?.length || 0}
                                                    </div>
                                                    <div className="text-sm text-gray-600">造句題目</div>
                                                </div>
                                                <div className="text-center p-4 bg-gray-50 rounded-lg">
                                                    <div className="text-2xl font-bold text-blue-600 mb-1">
                                                        {lesson.time_limit_minutes}
                                                    </div>
                                                    <div className="text-sm text-gray-600">分鐘</div>
                                                </div>
                                                <div className="text-center p-4 bg-gray-50 rounded-lg">
                                                    <div className="text-2xl font-bold text-purple-600 mb-1">
                                                        {lesson.difficulty_level}
                                                    </div>
                                                    <div className="text-sm text-gray-600">難易度</div>
                                                </div>
                                            </div>

                                            <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
                                                <h3 className="font-semibold text-amber-900 mb-2">注意事項：</h3>
                                                <ul className="text-amber-800 text-sm space-y-1">
                                                    <li>• 請在句子中正確使用指定的關鍵字</li>
                                                    <li>• 句子要完整並符合語法規則</li>
                                                    <li>• 可以使用上下頁切換不同題目</li>
                                                    <li>• AI會根據老師設定的標準進行評分</li>
                                                </ul>
                                            </div>

                                            <div className="flex gap-3">
                                                <Link to={createPageUrl("StudentDashboard")}>
                                                    <Button variant="outline">
                                                        返回選擇頁面
                                                    </Button>
                                                </Link>
                                            </div>
                                        </CardContent>
                                    </Card>

                                    {/* 開始按鈕 */}
                                    <div className="text-center">
                                        <Button onClick={startPractice} className="bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white px-8 py-3 text-lg">
                                            開始造句練習
                                        </Button>
                                    </div>
                                </motion.div>
                            )}

                            {/* 練習階段 */}
                            {currentStep === 'practice' && lesson.sentence_keywords && (
                                <motion.div
                                    key="practice-step"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -20 }}
                                    className="space-y-6"
                                >
                                    <Card className="shadow-lg">
                                        <CardHeader className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
                                            <CardTitle className="flex items-center justify-between">
                                                <span>造句練習 - 第 {currentKeywordIndex + 1} 題</span>
                                                <Badge variant="secondary" className="bg-white/20 text-white">
                                                    {lesson.sentence_keywords[currentKeywordIndex]?.keyword_type}
                                                </Badge>
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="p-6">
                                            <div className="space-y-6">
                                                {/* 關鍵字顯示 */}
                                                <div className="text-center">
                                                    <div className="text-sm text-gray-600 mb-2">請使用以下關鍵字造句：</div>
                                                    <div className="text-3xl font-bold text-indigo-600 mb-4">
                                                        {lesson.sentence_keywords[currentKeywordIndex]?.keyword}
                                                    </div>
                                                    
                                                    {/* 範例句子 */}
                                                    {lesson.sentence_keywords[currentKeywordIndex]?.example_sentence && (
                                                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                                                            <div className="flex items-center gap-2 mb-2">
                                                                <Lightbulb className="w-4 h-4 text-blue-600" />
                                                                <span className="text-sm font-semibold text-blue-900">參考範例：</span>
                                                            </div>
                                                            <p className="text-blue-800">
                                                                {lesson.sentence_keywords[currentKeywordIndex].example_sentence}
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* 造句輸入區 */}
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                                        您的造句：
                                                    </label>
                                                    <Textarea
                                                        value={userSentences[currentKeywordIndex] || ''}
                                                        onChange={(e) => handleSentenceChange(currentKeywordIndex, e.target.value)}
                                                        placeholder="請在這裡輸入您的句子..."
                                                        rows={4}
                                                        className="w-full text-lg"
                                                    />
                                                    <div className="text-sm text-gray-500 mt-2">
                                                        已輸入 {(userSentences[currentKeywordIndex] || '').length} 字
                                                    </div>
                                                </div>

                                                {/* 導航按鈕 */}
                                                <div className="flex justify-between items-center">
                                                    <Button
                                                        onClick={prevKeyword}
                                                        disabled={currentKeywordIndex === 0}
                                                        variant="outline"
                                                    >
                                                        上一題
                                                    </Button>
                                                    
                                                    <div className="flex gap-2">
                                                        {lesson.sentence_keywords.map((_, index) => (
                                                            <div
                                                                key={index}
                                                                className={`w-3 h-3 rounded-full ${
                                                                    index === currentKeywordIndex
                                                                        ? 'bg-indigo-500'
                                                                        : userSentences[index]
                                                                        ? 'bg-green-500'
                                                                        : 'bg-gray-300'
                                                                }`}
                                                            />
                                                        ))}
                                                    </div>

                                                    {currentKeywordIndex < lesson.sentence_keywords.length - 1 ? (
                                                        <Button
                                                            onClick={nextKeyword}
                                                            className="bg-indigo-500 hover:bg-indigo-600 text-white"
                                                        >
                                                            下一題
                                                        </Button>
                                                    ) : (
                                                        <Button
                                                            onClick={handleSubmit}
                                                            disabled={analyzing}
                                                            className="bg-green-500 hover:bg-green-600 text-white"
                                                        >
                                                            {analyzing ? '分析中...' : '完成造句'}
                                                        </Button>
                                                    )}
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                </motion.div>
                            )}

                            {/* 結果階段 */}
                            {currentStep === 'results' && results && (
                                <motion.div
                                    key="results"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    {/* 使用 SentenceMakingResults 組件顯示結果 */}
                                    <SentenceMakingResults results={results} />
                                    <div className="mt-6 text-center">
                                        <Button onClick={startNewPractice} className="bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white px-8 py-3 text-lg">
                                            再練習一次
                                        </Button>
                                    </div>
                                </motion.div>
                            )}
                        </motion.div>
                    )}

                    {activeTab === 'history' && (
                        <motion.div
                            key="history-tab"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                        >
                            {selectedResult ? (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <Button
                                            variant="outline"
                                            onClick={() => setSelectedResult(null)}
                                        >
                                            <ArrowLeft className="w-4 h-4 mr-2" />
                                            返回記錄列表
                                        </Button>
                                        <Button onClick={startNewPractice}>
                                            開始新的造句
                                        </Button>
                                    </div>
                                    {/* 使用 SentenceMakingResults 組件顯示歷史記錄詳情 */}
                                    <SentenceMakingResults results={selectedResult} />
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h2 className="text-xl font-semibold">造句練習記錄</h2>
                                        <Button onClick={startNewPractice}>
                                            開始新的造句
                                        </Button>
                                    </div>
                                    {previousResults.length === 0 ? (
                                        <Card>
                                            <CardContent className="text-center py-8">
                                                <PenTool className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                                                <p className="text-gray-500">尚無造句記錄</p>
                                                <p className="text-sm text-gray-400 mt-2">完成第一次造句練習後，記錄將會顯示在這裡</p>
                                            </CardContent>
                                        </Card>
                                    ) : (
                                        <HistoryTab 
                                            sessions={previousResults.map(result => ({
                                                ...result,
                                                created_date: result.completed_at,
                                                accuracy_percentage: result.percentage_score,
                                                words_per_minute: 0 // 造句沒有語速
                                            }))}
                                            onSelectSession={handleSelectResult}
                                            activeSessionId={selectedResult?.id}
                                        />
                                    )}
                                </div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
