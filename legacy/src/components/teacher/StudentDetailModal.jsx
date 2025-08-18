import React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Eye, Mail, Calendar, Target } from "lucide-react";
import { format } from "date-fns";
import { zhCN } from "date-fns/locale";

export default function StudentDetailModal({ student }) {
    return (
        <Dialog>
            <DialogTrigger asChild>
                <Button variant="ghost" size="sm">
                    <Eye className="w-4 h-4" />
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>學生詳細資料</DialogTitle>
                </DialogHeader>
                
                <div className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                基本資料
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm font-medium text-gray-500">姓名</label>
                                    <p className="text-lg font-semibold">{student.student_name}</p>
                                </div>
                                <div>
                                    <label className="text-sm font-medium text-gray-500">學號</label>
                                    <p className="text-lg">{student.student_id}</p>
                                </div>
                            </div>
                            
                            {student.email && (
                                <div className="flex items-center gap-2">
                                    <Mail className="w-4 h-4 text-gray-500" />
                                    <span>{student.email}</span>
                                </div>
                            )}
                            
                            {student.join_date && (
                                <div className="flex items-center gap-2">
                                    <Calendar className="w-4 h-4 text-gray-500" />
                                    <span>入班日期: {format(new Date(student.join_date), "yyyy年MM月dd日", { locale: zhCN })}</span>
                                </div>
                            )}
                            
                            <div className="flex items-center gap-2">
                                <Target className="w-4 h-4 text-gray-500" />
                                <span>目標語速: {student.target_wpm || 230} 字/分</span>
                            </div>
                        </CardContent>
                    </Card>

                    {(student.characteristics || student.learning_style || student.notes) && (
                        <Card>
                            <CardHeader>
                                <CardTitle>學習資料</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                {student.characteristics && (
                                    <div>
                                        <label className="text-sm font-medium text-gray-500">學生特質</label>
                                        <p className="text-gray-800">{student.characteristics}</p>
                                    </div>
                                )}
                                
                                {student.learning_style && (
                                    <div>
                                        <label className="text-sm font-medium text-gray-500">學習風格</label>
                                        <p className="text-gray-800">{student.learning_style}</p>
                                    </div>
                                )}
                                
                                {student.notes && (
                                    <div>
                                        <label className="text-sm font-medium text-gray-500">注意事項</label>
                                        <p className="text-gray-800">{student.notes}</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    )}

                    {student.tags && student.tags.length > 0 && (
                        <Card>
                            <CardHeader>
                                <CardTitle>學生標籤</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="flex flex-wrap gap-2">
                                    {student.tags.map((tag, index) => (
                                        <Badge key={index} variant="secondary">
                                            {tag}
                                        </Badge>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}