
import React, { useState, useEffect } from "react";
import { format } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Plus, Edit, Trash2, Users, BookOpen } from "lucide-react";
import { Badge } from "@/components/ui/badge"; // Added for CourseLinkerModal

import { Class } from "@/api/entities";
import { ClassStudent } from "@/api/entities";
// Import ClassCourseMapping as it will be used directly in this file
import { ClassCourseMapping } from "@/api/entities";

import StudentTable from "./StudentTable";

// Reusable modal component for Add/Edit student
function StudentModal({ isOpen, onClose, onSubmit, studentData, classId }) {
    const [formData, setFormData] = useState({
        student_name: '',
        student_id: '',
        email: '',
        birth_date: '',
        class_id: classId
    });

    useEffect(() => {
        if (studentData) {
            setFormData({
                student_name: studentData.student_name || '',
                student_id: studentData.student_id || '',
                email: studentData.email || '',
                birth_date: studentData.birth_date ? format(new Date(studentData.birth_date), 'yyyy-MM-dd') : '',
                class_id: studentData.class_id || classId
            });
        } else {
            setFormData({ student_name: '', student_id: '', email: '', birth_date: '', class_id: classId });
        }
    }, [studentData, isOpen, classId]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        await onSubmit(formData);
    };

    if (!isOpen) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>{studentData ? '編輯學生' : '新增學生'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4 py-4">
                    <div>
                        <Label htmlFor="student-name">學生姓名*</Label>
                        <Input id="student-name" value={formData.student_name} onChange={e => setFormData({...formData, student_name: e.target.value})} required />
                    </div>
                     <div>
                        <Label htmlFor="student-id">學號</Label>
                        <Input id="student-id" value={formData.student_id} onChange={e => setFormData({...formData, student_id: e.target.value})} />
                    </div>
                    <div>
                        <Label htmlFor="email">Email*</Label>
                        <Input id="email" type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} required />
                    </div>
                    <div>
                        <Label htmlFor="birth-date">生日* (作為預設密碼)</Label>
                        <Input id="birth-date" type="date" value={formData.birth_date} onChange={e => setFormData({...formData, birth_date: e.target.value})} required />
                    </div>
                    <DialogFooter>
                        <Button type="button" variant="secondary" onClick={onClose}>取消</Button>
                        <Button type="submit">儲存</Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

export default function ClassManagement({ allCourses, mappings, onUpdateMappings }) {
    const [classes, setClasses] = useState([]);
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedClass, setSelectedClass] = useState(null);
    const [isClassModalOpen, setIsClassModalOpen] = useState(false);
    const [isStudentModalOpen, setIsStudentModalOpen] = useState(false);
    const [editingClass, setEditingClass] = useState(null);
    const [editingStudent, setEditingStudent] = useState(null);
    const [studentsForClass, setStudentsForClass] = useState(new Set());
    const [classSearch, setClassSearch] = useState("");

    const [showCourseLinkerModal, setShowCourseLinkerModal] = useState(false);
    const [selectedClassForCourse, setSelectedClassForCourse] = useState(null);

    const classLevels = ["preA", "A1", "A2", "B1", "B2", "C1", "C2"];

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [classesData, studentsData] = await Promise.all([
                Class.list('-created_date'),
                ClassStudent.list()
            ]);
            setClasses(Array.isArray(classesData) ? classesData : []);
            setStudents(Array.isArray(studentsData) ? studentsData : []);
        } catch (error) {
            console.error("Failed to load class management data:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleOpenClassModal = (cls = null) => {
        setEditingClass(cls);
        if (cls) {
            const studentIdsInClass = students.filter(s => s.class_id === cls.id).map(s => s.id);
            setStudentsForClass(new Set(studentIdsInClass));
        } else {
            setStudentsForClass(new Set());
        }
        setIsClassModalOpen(true);
    };

    const handleClassSubmit = async (formData) => {
        try {
            let classResult;
            const classPayload = {
                class_name: formData.class_name,
                difficulty_level: formData.difficulty_level,
                description: formData.description
            };

            if (editingClass) {
                classResult = await Class.update(editingClass.id, classPayload);
            } else {
                classResult = await Class.create(classPayload);
            }

            const originalStudentIdsInThisClass = new Set(students.filter(s => s.class_id === (editingClass ? editingClass.id : classResult.id)).map(s => s.id));
            const allInvolvedStudentIds = new Set([...originalStudentIdsInThisClass, ...studentsForClass]);

            for (const studentId of allInvolvedStudentIds) {
                const isNowInClass = studentsForClass.has(studentId);
                const wasInClass = originalStudentIdsInThisClass.has(studentId);

                if (isNowInClass && !wasInClass) {
                    await ClassStudent.update(studentId, { class_id: classResult.id });
                } else if (!isNowInClass && wasInClass) {
                    await ClassStudent.update(studentId, { class_id: null }); 
                }
            }
            
            await loadData();
            setIsClassModalOpen(false);
            setEditingClass(null);
            if (selectedClass?.id === classResult.id) {
                setSelectedClass(classResult);
            }
        } catch (error) {
            console.error("Failed to save class:", error);
            alert("儲存班級失敗，請重試。");
        }
    };

    const handleStudentSubmit = async (formData) => {
        try {
            const studentPayload = { ...formData, class_id: selectedClass?.id };
            if (editingStudent) {
                await ClassStudent.update(editingStudent.id, studentPayload);
            } else {
                await ClassStudent.create(studentPayload);
            }
            await loadData();
            setIsStudentModalOpen(false);
            setEditingStudent(null);
        } catch (error) {
            console.error("Failed to save student:", error);
            alert("儲存學生失敗，請重試。");
        }
    };
    
    const handleDeleteClass = async (classId) => {
        if (window.confirm("確定要刪除這個班級嗎？班級內的學生將會被標示為未分班。此操作無法復原。")) {
            try {
                const studentsInClass = students.filter(s => s.class_id === classId);
                await Promise.all(studentsInClass.map(s => ClassStudent.update(s.id, { class_id: null })));
                
                // Also delete associated course mappings
                const mappingsToDelete = mappings.filter(m => m.class_id === classId);
                await Promise.all(mappingsToDelete.map(m => ClassCourseMapping.delete(m.id)));

                await Class.delete(classId);
                await loadData();
                await onUpdateMappings(); // Refresh mappings after class deletion
                if (selectedClass?.id === classId) {
                    setSelectedClass(null);
                }
            } catch (error) {
                console.error("刪除班級失敗:", error);
                alert("刪除班級失敗，請重試。");
            }
        }
    };
    
    const handleDeleteStudent = async (studentId) => {
        if (window.confirm("確定要刪除這位學生嗎？此操作無法復原。")) {
            try {
                await ClassStudent.delete(studentId);
                await loadData();
            } catch (error) {
                console.error("刪除學生失敗:", error);
                alert("刪除學生失敗，請重試。");
            }
        }
    };

    const toggleStudentInClass = (studentId) => {
        const newSet = new Set(studentsForClass);
        if (newSet.has(studentId)) {
            newSet.delete(studentId);
        } else {
            newSet.add(studentId);
        }
        setStudentsForClass(newSet);
    };

    const handleManageClassCourses = (classData) => {
        setSelectedClassForCourse(classData);
        setShowCourseLinkerModal(true);
    };

    const filteredClasses = classes.filter(c => c.class_name.toLowerCase().includes(classSearch.toLowerCase()));

    if (loading) {
        return (
            <div className="text-center py-8">
                <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-gray-600">載入資料中...</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-1">
                <Card>
                    <CardHeader>
                        <CardTitle>班級列表</CardTitle>
                        <Button onClick={() => handleOpenClassModal()} className="mt-2">
                            <Plus className="w-4 h-4 mr-2" /> 新增班級
                        </Button>
                        <Input placeholder="搜尋班級..." value={classSearch} onChange={e => setClassSearch(e.target.value)} className="mt-2" />
                    </CardHeader>
                    <CardContent className="max-h-96 overflow-y-auto">
                        {filteredClasses.length === 0 ? (
                            <p className="text-center text-gray-500">{classSearch === "" ? "尚無班級，點擊「新增班級」建立。" : "找不到符合條件的班級。"}</p>
                        ) : (
                            filteredClasses.map(cls => (
                                <div 
                                    key={cls.id} 
                                    className={`p-3 rounded-md cursor-pointer flex justify-between items-center ${selectedClass?.id === cls.id ? 'bg-teal-100' : 'hover:bg-gray-100'}`}
                                    onClick={() => setSelectedClass(cls)}
                                >
                                    <div>
                                        <p className="font-semibold">{cls.class_name}</p>
                                        <p className="text-sm text-gray-500">{cls.difficulty_level || '未設定程度'}</p>
                                        <p className="text-xs text-teal-600">
                                            {mappings.filter(m => m.class_id === cls.id).length} 個課程已關聯
                                        </p>
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); handleOpenClassModal(cls); }} title="編輯班級">
                                            <Edit className="w-4 h-4" />
                                        </Button>
                                        <Button 
                                            size="sm" 
                                            variant="outline" 
                                            onClick={(e) => { 
                                                e.stopPropagation(); 
                                                handleManageClassCourses(cls); 
                                            }} 
                                            title="管理課程"
                                            className="text-xs px-2 h-6"
                                        >
                                            <BookOpen className="w-3 h-3 mr-1" />
                                            課程
                                        </Button>
                                        <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); handleDeleteClass(cls.id); }} title="刪除班級">
                                            <Trash2 className="w-4 h-4 text-red-500" />
                                        </Button>
                                    </div>
                                </div>
                            ))
                        )}
                    </CardContent>
                </Card>
            </div>

            <div className="md:col-span-2">
                <Card>
                    <CardHeader>
                        <CardTitle>
                            {selectedClass ? `${selectedClass.class_name} - 學生列表` : '請選擇一個班級'}
                        </CardTitle>
                        {selectedClass && (
                            <Button onClick={() => { setEditingStudent(null); setIsStudentModalOpen(true); }} className="mt-2">
                                <Plus className="w-4 h-4 mr-2" /> 新增學生至本班
                            </Button>
                        )}
                    </CardHeader>
                    <CardContent>
                        {selectedClass ? (
                            students.filter(s => s.class_id === selectedClass.id).length > 0 ? (
                                <StudentTable
                                    students={students.filter(s => s.class_id === selectedClass.id)}
                                    onEdit={(student) => { setEditingStudent(student); setIsStudentModalOpen(true); }}
                                    onDelete={handleDeleteStudent}
                                />
                            ) : (
                                <div className="text-center py-8">
                                    <p className="text-gray-500 mb-2">此班級尚無學生。</p>
                                </div>
                            )
                        ) : (
                            <div className="text-center py-8 text-gray-500">
                                <p>從左側選擇班級以查看或管理學生。</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            <StudentModal 
                isOpen={isStudentModalOpen}
                onClose={() => setIsStudentModalOpen(false)}
                onSubmit={handleStudentSubmit}
                studentData={editingStudent}
                classId={selectedClass?.id}
            />

            {isClassModalOpen && (
                 <Dialog open={isClassModalOpen} onOpenChange={setIsClassModalOpen}>
                    <DialogContent className="max-w-2xl">
                        <DialogHeader>
                            <DialogTitle>{editingClass ? '編輯班級' : '新增班級'}</DialogTitle>
                        </DialogHeader>
                        <ClassModalForm 
                            onSubmit={handleClassSubmit} 
                            onClose={() => setIsClassModalOpen(false)}
                            classData={editingClass}
                            classLevels={classLevels}
                            allStudents={students}
                            studentsForClass={studentsForClass}
                            onToggleStudent={toggleStudentInClass}
                        />
                    </DialogContent>
                </Dialog>
            )}

            {/* 新增：課程關聯 Modal */}
            <CourseLinkerModal
                isOpen={showCourseLinkerModal}
                onClose={() => {
                    setShowCourseLinkerModal(false);
                    setSelectedClassForCourse(null);
                }}
                classData={selectedClassForCourse}
                allCourses={allCourses}
                existingMappings={mappings}
                onUpdate={onUpdateMappings}
            />
        </div>
    );
}

function ClassModalForm({ onSubmit, onClose, classData, classLevels, allStudents, studentsForClass, onToggleStudent }) {
    const [formData, setFormData] = useState({
        class_name: classData?.class_name || '',
        difficulty_level: classData?.difficulty_level || classLevels[0],
        description: classData?.description || ''
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        await onSubmit(formData);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4 py-4">
            <div>
                <Label htmlFor="class-name">班級名稱*</Label>
                <Input id="class-name" value={formData.class_name} onChange={e => setFormData({...formData, class_name: e.target.value})} required />
            </div>
            <div>
                <Label htmlFor="difficulty-level">班級程度*</Label>
                <Select value={formData.difficulty_level} onValueChange={value => setFormData({...formData, difficulty_level: value})}>
                    <SelectTrigger className="w-full">
                        <SelectValue placeholder="選擇班級程度"/>
                    </SelectTrigger>
                    <SelectContent>
                        {classLevels.map(level => <SelectItem key={level} value={level}>{level}</SelectItem>)}
                    </SelectContent>
                </Select>
            </div>
             <div>
                <Label htmlFor="description">班級描述</Label>
                <Textarea id="description" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
            </div>
            <div>
                <Label className="text-sm font-semibold">將學生加入此班級</Label>
                <div className="max-h-48 overflow-y-auto border rounded-md p-2 space-y-1">
                    {allStudents.length === 0 ? (
                        <p className="text-gray-500 text-sm">尚無學生可供選擇。</p>
                    ) : (
                        allStudents.map(student => (
                            <div key={student.id} className="flex items-center gap-2 p-1 rounded hover:bg-gray-100">
                                <Checkbox 
                                    id={`student-${student.id}`} 
                                    checked={studentsForClass.has(student.id)}
                                    onCheckedChange={() => onToggleStudent(student.id)}
                                />
                                <label htmlFor={`student-${student.id}`} className="text-sm cursor-pointer">{student.student_name} ({student.email})</label>
                            </div>
                        ))
                    )}
                </div>
            </div>
            <DialogFooter>
                <Button type="button" variant="secondary" onClick={onClose}>取消</Button>
                <Button type="submit">儲存</Button>
            </DialogFooter>
        </form>
    );
}

// 新增：課程關聯 Modal 組件
function CourseLinkerModal({ isOpen, onClose, classData, allCourses, existingMappings, onUpdate }) {
    const [selectedCourseIds, setSelectedCourseIds] = useState(new Set());
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (classData && isOpen) {
            const currentLinkedIds = existingMappings
                .filter(m => m.class_id === classData.id)
                .map(m => m.course_id);
            setSelectedCourseIds(new Set(currentLinkedIds));
        }
    }, [classData, existingMappings, isOpen]);

    const handleToggleCourse = (courseId) => {
        const newSelection = new Set(selectedCourseIds);
        if (newSelection.has(courseId)) {
            newSelection.delete(courseId);
        } else {
            newSelection.add(courseId);
        }
        setSelectedCourseIds(newSelection);
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            // ClassCourseMapping is already imported at the top, no need for dynamic import here.
            
            const originalIds = new Set(existingMappings.filter(m => m.class_id === classData.id).map(m => m.course_id));
            
            const idsToAdd = [...selectedCourseIds].filter(id => !originalIds.has(id));
            const idsToRemove = [...originalIds].filter(id => !selectedCourseIds.has(id));

            const creationPromises = idsToAdd.map(course_id => 
                ClassCourseMapping.create({ class_id: classData.id, course_id })
            );
            
            const deletionPromises = idsToRemove.map(course_id => {
                const mappingToDelete = existingMappings.find(m => m.class_id === classData.id && m.course_id === course_id);
                // Ensure mappingToDelete exists before attempting to delete by ID
                return mappingToDelete ? ClassCourseMapping.delete(mappingToDelete.id) : Promise.resolve();
            });

            await Promise.all([...creationPromises, ...deletionPromises]);
            await onUpdate(); // Call the parent's update function to refresh mappings
            onClose();

        } catch (error) {
            console.error("儲存課程關聯失敗:", error);
            alert("儲存失敗，請重試");
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen || !classData) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <BookOpen className="w-5 h-5" />
                        管理「{classData.class_name}」的課程
                    </DialogTitle>
                </DialogHeader>
                <div className="py-4 max-h-[60vh] overflow-y-auto">
                    <div className="space-y-2">
                        {allCourses.length === 0 ? (
                            <p className="text-gray-500 text-center">目前沒有可用的課程。</p>
                        ) : (
                            allCourses.map(course => (
                                <div key={course.id} className="flex items-center space-x-3 p-2 rounded-md hover:bg-gray-100">
                                    <Checkbox
                                        id={`course-${course.id}`}
                                        checked={selectedCourseIds.has(course.id)}
                                        onCheckedChange={() => handleToggleCourse(course.id)}
                                    />
                                    <label
                                        htmlFor={`course-${course.id}`}
                                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex-grow cursor-pointer"
                                    >
                                        {course.title}
                                    </label>
                                    <Badge variant="outline" className="text-xs">
                                        {course.created_date ? new Date(course.created_date).toLocaleDateString() : ''}
                                    </Badge>
                                </div>
                            ))
                        )}
                    </div>
                </div>
                <DialogFooter>
                    <Button type="button" variant="secondary" onClick={onClose}>取消</Button>
                    <Button onClick={handleSave} disabled={isSaving}>
                        {isSaving ? "儲存中..." : "儲存變更"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
