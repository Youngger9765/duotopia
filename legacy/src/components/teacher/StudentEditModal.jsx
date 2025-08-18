
import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { X, User, AtSign, ListChecks, Tag, Edit } from 'lucide-react';

export default function StudentEditModal({ isOpen, student, onClose, onSave }) {
    const [editData, setEditData] = useState({});
    const [newTag, setNewTag] = useState('');

    useEffect(() => {
        if (student) {
            setEditData({
                ...student,
                tags: student.tags || []
            });
        }
    }, [student]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        
        // 允許清空數字欄位
        if (name === 'target_wpm' || name === 'target_accuracy') {
            setEditData(prev => ({ ...prev, [name]: value }));
        } else {
            setEditData(prev => ({ ...prev, [name]: value }));
        }
    };
    
    const handleNumberInputBlur = (e) => {
        const { name, value } = e.target;
        // 如果使用者離開欄位且欄位為空，則將其設為 null 或保持為空字串，以待後續處理
        // 這裡我們讓它保持為空字串，在儲存時再決定如何處理
        if (value === '') {
            setEditData(prev => ({ ...prev, [name]: '' }));
        } else {
            setEditData(prev => ({ ...prev, [name]: parseInt(value, 10) || 0 }));
        }
    };

    const handleSave = () => {
        const dataToSave = {
            ...editData,
            target_wpm: editData.target_wpm === '' ? null : parseInt(editData.target_wpm, 10),
            target_accuracy: editData.target_accuracy === '' ? null : parseInt(editData.target_accuracy, 10),
        };
        onSave(dataToSave);
    };

    const handleAddTag = () => {
        if (newTag && !editData.tags.includes(newTag)) {
            setEditData(prev => ({ ...prev, tags: [...prev.tags, newTag.trim()] }));
            setNewTag('');
        }
    };

    const handleRemoveTag = (tagToRemove) => {
        setEditData(prev => ({ ...prev, tags: prev.tags.filter(tag => tag !== tagToRemove) }));
    };

    if (!student) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-2xl bg-gradient-to-br from-gray-50 to-blue-50/30 p-0 rounded-2xl shadow-2xl border-0">
                <DialogHeader className="bg-gradient-to-r from-teal-500 to-blue-500 text-white p-6 rounded-t-2xl">
                    <div className="flex justify-between items-center">
                        <DialogTitle className="text-2xl font-bold flex items-center gap-3">
                            <Edit className="w-6 h-6" />
                            編輯學生資料 - {student.student_name}
                        </DialogTitle>
                        <Button variant="ghost" size="icon" onClick={onClose} className="text-white hover:bg-white/20 rounded-full">
                            <X className="w-5 h-5" />
                        </Button>
                    </div>
                </DialogHeader>

                <div className="p-8 space-y-6 max-h-[70vh] overflow-y-auto">
                    {/* 基本資料 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <Label htmlFor="student_name" className="text-gray-700 font-semibold flex items-center gap-2"><User className="w-4 h-4"/>學生姓名</Label>
                            <Input id="student_name" name="student_name" value={editData.student_name || ''} onChange={handleInputChange} className="border-2"/>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="student_id" className="text-gray-700 font-semibold flex items-center gap-2"><ListChecks className="w-4 h-4"/>學號</Label>
                            <Input id="student_id" name="student_id" value={editData.student_id || ''} onChange={handleInputChange} className="border-2"/>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="email" className="text-gray-700 font-semibold flex items-center gap-2"><AtSign className="w-4 h-4"/>電子郵件</Label>
                        <Input id="email" name="email" value={editData.email || ''} onChange={handleInputChange} className="border-2"/>
                    </div>

                    {/* 個人標準設定 */}
                    <div className="p-6 bg-white/80 rounded-xl border border-gray-200">
                        <h4 className="font-bold text-gray-800 mb-2">個人標準設定</h4>
                        <p className="text-sm text-gray-600 mb-4">設定此學生的個人目標標準。如不設定，系統將使用課程的預設標準。</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <Label htmlFor="target_wpm">目標語速 (字/分鐘)</Label>
                                <Input
                                    id="target_wpm"
                                    name="target_wpm"
                                    type="number"
                                    value={editData.target_wpm || ''}
                                    onChange={handleInputChange}
                                    onBlur={handleNumberInputBlur}
                                    placeholder="預設值"
                                    className="border-2"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="target_accuracy">目標正確率 (%)</Label>
                                <Input
                                    id="target_accuracy"
                                    name="target_accuracy"
                                    type="number"
                                    value={editData.target_accuracy || ''}
                                    onChange={handleInputChange}
                                    onBlur={handleNumberInputBlur}
                                    placeholder="預設值"
                                    max="100"
                                    min="0"
                                    className="border-2"
                                />
                            </div>
                        </div>
                    </div>

                    {/* 學生標籤 */}
                    <div className="space-y-2">
                        <Label htmlFor="tags" className="text-gray-700 font-semibold flex items-center gap-2"><Tag className="w-4 h-4"/>學生標籤</Label>
                        <div className="flex gap-2">
                            <Input
                                id="tags"
                                value={newTag}
                                onChange={(e) => setNewTag(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
                                placeholder="輸入標籤後按 Enter"
                                className="border-2"
                            />
                            <Button onClick={handleAddTag} variant="outline">新增</Button>
                        </div>
                        <div className="flex flex-wrap gap-2 mt-2">
                            {editData.tags?.map(tag => (
                                <Badge key={tag} variant="secondary" className="text-sm py-1 px-3">
                                    {tag}
                                    <button onClick={() => handleRemoveTag(tag)} className="ml-2 text-red-500 hover:text-red-700">
                                        <X className="w-3 h-3" />
                                    </button>
                                </Badge>
                            ))}
                        </div>
                    </div>

                    {/* 筆記 */}
                    <div className="space-y-2">
                        <Label htmlFor="notes" className="text-gray-700 font-semibold">筆記</Label>
                        <Textarea id="notes" name="notes" value={editData.notes || ''} onChange={handleInputChange} placeholder="關於此學生的筆記..." className="border-2" rows={4}/>
                    </div>
                </div>

                <DialogFooter className="p-6 bg-white/80 rounded-b-2xl border-t">
                    <Button variant="outline" onClick={onClose}>取消</Button>
                    <Button onClick={handleSave} className="gradient-bg text-white shadow-lg hover:shadow-xl transition-shadow">儲存變更</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
