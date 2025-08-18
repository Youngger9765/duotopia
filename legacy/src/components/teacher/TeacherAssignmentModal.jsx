import React, { useState, useEffect } from "react";
import { ClassTeacher } from "@/api/entities";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, Plus, X, Save, Settings, Edit, Trash2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const availableRoles = ["導師", "協同教師", "助教", "實習教師"];
const availablePermissions = ["管理班級", "管理學生", "管理課文", "檢視報告"];

export default function TeacherAssignmentModal({ isOpen, onClose, classData, onSave, allSchools, allSchoolTeachers, classTeachers: initialClassTeachers }) {
    const [selectedSchoolId, setSelectedSchoolId] = useState("");
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const [activeTab, setActiveTab] = useState("add");
    const [editingAssignmentId, setEditingAssignmentId] = useState(null);
    const [editingData, setEditingData] = useState({});
    
    // Derived state
    const teachersForSelectedSchool = allSchoolTeachers.filter(t => t.school_id === selectedSchoolId && t.is_active);
    const classAssignments = initialClassTeachers.filter(ct => ct.class_id === classData?.id);
    const teachersInClass = classAssignments.map(assignment => {
        const teacherInfo = allSchoolTeachers.find(t => t.id === assignment.teacher_id);
        const schoolInfo = teacherInfo ? allSchools.find(s => s.id === teacherInfo.school_id) : null;
        return {
            ...assignment,
            teacher_name: teacherInfo?.teacher_name,
            email: teacherInfo?.email,
            school_name: schoolInfo?.school_name
        };
    });

    useEffect(() => {
        if (!isOpen) {
            setEditingAssignmentId(null);
            setEditingData({});
            setSearchTerm("");
            setSelectedSchoolId("");
            setActiveTab("add");
        }
    }, [isOpen]);

    const handleAddTeacher = async (teacherId) => {
        if (!classData) return;

        setLoading(true);
        try {
            await ClassTeacher.create({
                class_id: classData.id,
                teacher_id: teacherId,
                role: "協同教師",
                permissions: ["檢視報告"]
            });
            onSave(); // Refresh parent
        } catch (error) {
            console.error("新增教師失敗:", error);
            alert("新增教師失敗");
        } finally {
            setLoading(false);
        }
    };

    const handleRemoveTeacher = async (assignmentId) => {
        if (!window.confirm("確定要將此教師從班級中移除嗎？")) return;
        
        setLoading(true);
        try {
            await ClassTeacher.delete(assignmentId);
            onSave();
        } catch (error) {
            console.error("移除教師失敗:", error);
            alert("移除教師失敗");
        } finally {
            setLoading(false);
        }
    };
    
    const startEditing = (assignment) => {
        setEditingAssignmentId(assignment.id);
        setEditingData({
            role: assignment.role,
            permissions: new Set(assignment.permissions || [])
        });
    };

    const cancelEditing = () => {
        setEditingAssignmentId(null);
        setEditingData({});
    };

    const handleSavePermissions = async () => {
        if (!editingAssignmentId) return;

        setLoading(true);
        try {
            await ClassTeacher.update(editingAssignmentId, {
                role: editingData.role,
                permissions: Array.from(editingData.permissions)
            });
            cancelEditing();
            onSave();
        } catch (error) {
            console.error("儲存權限失敗:", error);
            alert("儲存失敗");
        } finally {
            setLoading(false);
        }
    };

    const handlePermissionChange = (permission) => {
        const newPermissions = new Set(editingData.permissions);
        if (newPermissions.has(permission)) {
            newPermissions.delete(permission);
        } else {
            newPermissions.add(permission);
        }
        setEditingData(prev => ({ ...prev, permissions: newPermissions }));
    };
    
    const filteredTeachers = teachersForSelectedSchool.filter(teacher =>
        teacher.teacher_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        teacher.email.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    if (!isOpen) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-3xl w-[95vw] h-[90vh] flex flex-col p-0">
                <DialogHeader className="p-6 border-b">
                    <DialogTitle>管理「{classData?.class_name}」的教師</DialogTitle>
                </DialogHeader>
                
                <div className="flex-1 overflow-y-auto p-6">
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                        <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="add">新增教師</TabsTrigger>
                            <TabsTrigger value="current">目前教師 ({teachersInClass.length})</TabsTrigger>
                        </TabsList>
                        <TabsContent value="add" className="mt-4">
                            <div className="space-y-4">
                                <div>
                                    <Label>選擇學校</Label>
                                    <Select onValueChange={setSelectedSchoolId} value={selectedSchoolId}>
                                        <SelectTrigger><SelectValue placeholder="請選擇學校" /></SelectTrigger>
                                        <SelectContent>
                                            {allSchools.map(school => (
                                                <SelectItem key={school.id} value={school.id}>{school.school_name}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                {selectedSchoolId && (
                                    <>
                                        <div className="relative">
                                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                                            <Input placeholder="搜尋教師..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-8" />
                                        </div>
                                        <div className="space-y-2 max-h-60 overflow-y-auto">
                                            {filteredTeachers.map(teacher => {
                                                const isAlreadyInClass = teachersInClass.some(t => t.teacher_id === teacher.id);
                                                return (
                                                    <div key={teacher.id} className="flex items-center justify-between p-3 border rounded-lg">
                                                        <div>
                                                            <p className="font-medium">{teacher.teacher_name}</p>
                                                            <p className="text-sm text-gray-500">{teacher.email}</p>
                                                        </div>
                                                        <Button size="sm" onClick={() => handleAddTeacher(teacher.id)} disabled={isAlreadyInClass || loading}>
                                                            {isAlreadyInClass ? "已加入" : <Plus className="w-4 h-4" />}
                                                        </Button>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </>
                                )}
                            </div>
                        </TabsContent>
                        <TabsContent value="current" className="mt-4">
                            <div className="space-y-3">
                                {teachersInClass.length > 0 ? (
                                    teachersInClass.map(teacher => (
                                        <Card key={teacher.id}>
                                            <CardContent className="p-4">
                                                {editingAssignmentId === teacher.id ? (
                                                    <div className="space-y-4">
                                                        <div>
                                                            <Label>角色</Label>
                                                            <Select value={editingData.role} onValueChange={(value) => setEditingData(prev => ({...prev, role: value}))}>
                                                                <SelectTrigger><SelectValue/></SelectTrigger>
                                                                <SelectContent>
                                                                    {availableRoles.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}
                                                                </SelectContent>
                                                            </Select>
                                                        </div>
                                                        <div>
                                                            <Label>權限</Label>
                                                            <div className="grid grid-cols-2 gap-2 mt-2">
                                                                {availablePermissions.map(p => (
                                                                    <div key={p} className="flex items-center gap-2">
                                                                        <Checkbox id={`perm-${p}`} checked={editingData.permissions.has(p)} onCheckedChange={() => handlePermissionChange(p)} />
                                                                        <Label htmlFor={`perm-${p}`}>{p}</Label>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                        <div className="flex justify-end gap-2">
                                                            <Button variant="ghost" onClick={cancelEditing}>取消</Button>
                                                            <Button onClick={handleSavePermissions} disabled={loading}><Save className="w-4 h-4 mr-2"/>儲存</Button>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div className="flex justify-between items-center">
                                                        <div>
                                                            <p className="font-bold">{teacher.teacher_name}</p>
                                                            <p className="text-sm text-gray-500">{teacher.email}</p>
                                                            <p className="text-xs text-blue-600 mt-1">{teacher.school_name}</p>
                                                            <div className="flex flex-wrap gap-1 mt-2">
                                                                <Badge variant="outline">{teacher.role}</Badge>
                                                                {(teacher.permissions || []).map(p => <Badge key={p} variant="secondary">{p}</Badge>)}
                                                            </div>
                                                        </div>
                                                        <div className="flex gap-1">
                                                            <Button variant="ghost" size="icon" onClick={() => startEditing(teacher)}><Edit className="w-4 h-4"/></Button>
                                                            <Button variant="ghost" size="icon" className="text-red-500" onClick={() => handleRemoveTeacher(teacher.id)} disabled={loading}><Trash2 className="w-4 h-4"/></Button>
                                                        </div>
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>
                                    ))
                                ) : (
                                    <p className="text-center text-gray-500 py-8">此班級尚無教師</p>
                                )}
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>
                
                <DialogFooter className="p-6 border-t">
                    <DialogClose asChild>
                        <Button variant="outline">關閉</Button>
                    </DialogClose>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}