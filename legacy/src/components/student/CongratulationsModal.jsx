import React from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Award, Star, Target, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";

export default function CongratulationsModal({ 
    isOpen, 
    onClose, 
    achievement, 
    attempt, 
    standards,
    onNextLesson,
    onRetryLesson 
}) {
    if (!achievement || !attempt || !standards) return null;

    const isFirstTimeAchievement = attempt.attempt_number <= 4;
    
    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-md">
                <motion.div 
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="text-center py-6"
                >
                    {/* 慶祝動畫 */}
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                        className="w-20 h-20 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-6"
                    >
                        <Award className="w-10 h-10 text-white" />
                    </motion.div>
                    
                    {/* 主要標題 */}
                    <motion.h2 
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        className="text-2xl font-bold text-gray-900 mb-2"
                    >
                        🎉 恭喜達標！
                    </motion.h2>
                    
                    <motion.p 
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.4 }}
                        className="text-gray-600 mb-6"
                    >
                        您在第 {attempt.attempt_number} 次練習中成功達成目標！
                    </motion.p>
                    
                    {/* 成績展示 */}
                    <motion.div 
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        className="bg-gradient-to-r from-green-50 to-teal-50 rounded-lg p-4 mb-6"
                    >
                        <div className="grid grid-cols-2 gap-4">
                            <div className="text-center">
                                <div className="flex items-center justify-center gap-1 mb-1">
                                    <TrendingUp className="w-4 h-4 text-green-600" />
                                    <span className="text-sm text-gray-600">語速</span>
                                </div>
                                <div className="text-2xl font-bold text-green-600">
                                    {Math.round(attempt.words_per_minute)}
                                </div>
                                <div className="text-xs text-gray-500">
                                    目標: {standards.target_wpm} 字/分
                                </div>
                                <Badge className="bg-green-100 text-green-800 mt-1">
                                    ✓ 達標
                                </Badge>
                            </div>
                            
                            <div className="text-center">
                                <div className="flex items-center justify-center gap-1 mb-1">
                                    <Target className="w-4 h-4 text-blue-600" />
                                    <span className="text-sm text-gray-600">正確率</span>
                                </div>
                                <div className="text-2xl font-bold text-blue-600">
                                    {attempt.accuracy_percentage.toFixed(1)}%
                                </div>
                                <div className="text-xs text-gray-500">
                                    目標: {standards.target_accuracy}%
                                </div>
                                <Badge className="bg-blue-100 text-blue-800 mt-1">
                                    ✓ 達標
                                </Badge>
                            </div>
                        </div>
                    </motion.div>
                    
                    {/* 額外獎勵訊息 */}
                    {isFirstTimeAchievement && (
                        <motion.div 
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.6 }}
                            className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-6"
                        >
                            <div className="flex items-center justify-center gap-2 text-yellow-800">
                                <Star className="w-4 h-4" />
                                <span className="text-sm font-medium">
                                    {attempt.attempt_number === 1 ? "一次達標！太厲害了！" :
                                     attempt.attempt_number === 2 ? "第二次就達標！很棒！" :
                                     attempt.attempt_number === 3 ? "第三次達標！持續進步！" :
                                     "最後機會達標！永不放棄！"}
                                </span>
                            </div>
                        </motion.div>
                    )}
                    
                    {/* 操作按鈕 */}
                    <motion.div 
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.7 }}
                        className="space-y-3"
                    >
                        {onNextLesson && (
                            <Button 
                                onClick={onNextLesson}
                                className="w-full gradient-bg text-white"
                                size="lg"
                            >
                                挑戰下一課 🚀
                            </Button>
                        )}
                        
                        <div className="flex gap-3">
                            {onRetryLesson && (
                                <Button 
                                    onClick={onRetryLesson}
                                    variant="outline"
                                    className="flex-1"
                                >
                                    再練習一次
                                </Button>
                            )}
                            
                            <Button 
                                onClick={onClose}
                                variant="outline"
                                className="flex-1"
                            >
                                返回課程
                            </Button>
                        </div>
                    </motion.div>
                </motion.div>
            </DialogContent>
        </Dialog>
    );
}