
import React, { useState, useEffect, useMemo } from 'react';
import { User } from '@/api/entities';
import { Class } from '@/api/entities';
import { Course } from '@/api/entities';
import { Lesson } from '@/api/entities';
import { ClassCourseMapping } from '@/api/entities';
import { ClassStudent } from '@/api/entities';
import { StudentAssignment } from '@/api/entities';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { format } from "date-fns";
import { motion } from 'framer-motion';
import { ListChecks, BookOpen, Users, FileText, CalendarIcon, Search, Clock, Send, CheckCircle, AlertCircle, Trash2 } from 'lucide-react';

export default function AssignHomeworkPage() {
    const [user, setUser] = useState(null);
    const [allCourses, setAllCourses] = useState([]);
    const [allClasses, setAllClasses] = useState([]);
    const [allLessons, setAllLessons] = useState([]);
    const [mappings, setMappings] = useState([]);

    // Step 1: 選擇課程
    const [selectedCourseId, setSelectedCourseId] = useState('');
    const [courseSearch, setCourseSearch] = useState('');

    // Step 2: 選擇課文
    const [selectedLessonId, setSelectedLessonId] = useState('');
    const [lessonSearch, setLessonSearch] = useState('');

    // Step 3: 選擇班級
    const [selectedClassId, setSelectedClassId] = useState('');

    // Step 4: 選擇學生
    const [classStudents, setClassStudents] = useState([]);
    const [selectedStudents, setSelectedStudents] = useState(new Set());
    const [selectAllStudents, setSelectAllStudents] = useState(false);
    
    // Step 5: 作業詳情
    const [assignmentTitle, setAssignmentTitle] = useState('');
    const [assignmentDescription, setAssignmentDescription] = useState('');
    const [dispatchDate, setDispatchDate] = useState(new Date());
    const [dueDate, setDueDate] = useState(null);

    const [loading, setLoading] = useState(true);
    const [isAssigning, setIsAssigning] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');

    useEffect(() => {
        loadInitialData();
    }, []);

    // 當選擇班級時，載入班級學生
    useEffect(() => {
        if (selectedClassId) {
            loadClassStudents();
        } else {
            setClassStudents([]);
            setSelectedStudents(new Set());
        }
    }, [selectedClassId]);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            const currentUser = await User.me();
            setUser(currentUser);
            
            const [coursesData, classesData, lessonsData, mappingsData] = await Promise.all([
                Course.list(),
                Class.list(),
                Lesson.list(),
                ClassCourseMapping.list()
            ]);

            setAllCourses(Array.isArray(coursesData) ? coursesData : []);
            setAllClasses(Array.isArray(classesData) ? classesData : []);
            setAllLessons(Array.isArray(lessonsData) ? lessonsData : []);
            setMappings(Array.isArray(mappingsData) ? mappingsData : []);
            
        } catch (err) {
            console.error("Failed to load initial data:", err);
            setError("無法載入資料，請重新整理頁面。");
        } finally {
            setLoading(false);
        }
    };

    const loadClassStudents = async () => {
        if (!selectedClassId) return;
        
        try {
            const students = await ClassStudent.filter({ class_id: selectedClassId });
            setClassStudents(students);
            setSelectedStudents(new Set());
            setSelectAllStudents(false);
        } catch (err) {
            console.error("Failed to load class students:", err);
            setClassStudents([]);
        }
    };

    // 篩選課程
    const filteredCourses = useMemo(() => {
        if (!courseSearch) return allCourses;
        return allCourses.filter(course => 
            course.title.toLowerCase().includes(courseSearch.toLowerCase())
        );
    }, [courseSearch, allCourses]);

    // 根據選中的課程篩選課文
    const availableLessons = useMemo(() => {
        if (!selectedCourseId) return [];
        return allLessons.filter(lesson => 
            lesson.course_id === selectedCourseId && 
            lesson.is_active &&
            (lessonSearch === '' || lesson.title.toLowerCase().includes(lessonSearch.toLowerCase()))
        );
    }, [selectedCourseId, lessonSearch, allLessons]);

    // 根據選中的課程篩選可選班級
    const availableClasses = useMemo(() => {
        if (!selectedCourseId) return [];
        const linkedClassIds = mappings
            .filter(m => m.course_id === selectedCourseId)
            .map(m => m.class_id);
        return allClasses.filter(cls => linkedClassIds.includes(cls.id));
    }, [selectedCourseId, mappings, allClasses]);

    const handleStudentToggle = (studentId, checked) => {
        const newSelected = new Set(selectedStudents);
        if (checked) {
            newSelected.add(studentId);
        } else {
            newSelected.delete(studentId);
        }
        setSelectedStudents(newSelected);
        setSelectAllStudents(newSelected.size === classStudents.length && classStudents.length > 0);
    };

    const handleSelectAllToggle = (checked) => {
        if (checked) {
            setSelectedStudents(new Set(classStudents.map(s => s.id)));
        } else {
            setSelectedStudents(new Set());
        }
        setSelectAllStudents(checked);
    };

    const handleAssignHomework = async () => {
        if (!selectedCourseId || !selectedLessonId || !selectedClassId || 
            selectedStudents.size === 0 || !assignmentTitle || !dueDate) {
            setError('請完成所有步驟：選擇課程、課文、班級、至少一位學生、填寫作業標題和繳交期限。');
            return;
        }

        setError('');
        setSuccessMessage('');
        setIsAssigning(true);

        try {
            const selectedLesson = allLessons.find(l => l.id === selectedLessonId);
            if (!selectedLesson) {
                throw new Error("找不到選中的課文。");
            }

            // 生成一個唯一的作業ID，這個ID將用於所有被指派的學生
            const sharedAssignmentId = crypto.randomUUID();
            
            // 獲取選中的學生列表
            const selectedStudentsList = classStudents.filter(s => selectedStudents.has(s.id));
            
            console.log('[AssignHomework] 選中的學生:', selectedStudentsList.map(s => s.student_name));
            
            // 核心修正：為每個選中的學生單獨建立一筆 StudentAssignment 記錄
            const assignmentPromises = selectedStudentsList.map(student => {
                const assignmentData = {
                    assignment_id: sharedAssignmentId, // 所有學生共享同一個作業ID
                    lesson_id: selectedLessonId,
                    class_id: selectedClassId,
                    student_email: student.email, // 每個學生有自己的email
                    teacher_email: user.email,
                    assignment_title: assignmentTitle,
                    assignment_description: assignmentDescription,
                    activity_type: selectedLesson.activity_type,
                    scheduled_dispatch_date: dispatchDate.toISOString(),
                    due_date: dueDate.toISOString(),
                    assigned_date: new Date().toISOString(),
                    is_active: true,
                };
                
                console.log('[AssignHomework] 為學生建立作業記錄:', student.student_name, assignmentData);
                return StudentAssignment.create(assignmentData);
            });
            
            await Promise.all(assignmentPromises);

            setSuccessMessage(`作業「${assignmentTitle}」已成功指派給 ${selectedStudents.size} 位學生！`);
            
            // 重置表單
            setSelectedCourseId('');
            setSelectedLessonId('');
            setSelectedClassId('');
            setSelectedStudents(new Set());
            setSelectAllStudents(false);
            setAssignmentTitle('');
            setAssignmentDescription('');
            setDueDate(null);
            
        } catch (err) {
            console.error("Failed to assign homework:", err);
            setError(`作業指派失敗：${err.message}`);
        } finally {
            setIsAssigning(false);
        }
    };

    if (loading) return (
        <div className="p-6 bg-gray-50 min-h-screen flex items-center justify-center">
            <div className="text-center">
                <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-gray-600">載入作業派發中心...</p>
            </div>
        </div>
    );

    return (
        <div className="p-6 bg-gray-50 min-h-screen">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                    <ListChecks className="w-8 h-8 text-teal-600" />
                    作業派發中心
                </h1>
                <p className="text-gray-600 mt-2">請依序選擇課程、課文、班級和學生，然後設定作業詳情。</p>
            </header>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* 左欄：選擇步驟 */}
                <div className="space-y-6">
                    {/* Step 1: 選擇課程 */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <span className="bg-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">1</span>
                                選擇課程
                            </CardTitle>
                            <CardDescription>選擇要指派作業的課程</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Input 
                                placeholder="搜尋課程..." 
                                value={courseSearch} 
                                onChange={(e) => setCourseSearch(e.target.value)} 
                                className="mb-4"
                            />
                            <div className="max-h-48 overflow-y-auto border rounded-md p-2 space-y-2">
                                {filteredCourses.map(course => (
                                    <div 
                                        key={course.id}
                                        className={`p-3 rounded-md cursor-pointer transition-colors ${
                                            selectedCourseId === course.id 
                                                ? 'bg-teal-100 border border-teal-300' 
                                                : 'hover:bg-gray-100 border border-gray-200'
                                        }`}
                                        onClick={() => {
                                            setSelectedCourseId(course.id);
                                            setSelectedLessonId('');
                                            setSelectedClassId('');
                                        }}
                                    >
                                        <p className="font-semibold">{course.title}</p>
                                        {course.description && (
                                            <p className="text-sm text-gray-500 mt-1">{course.description}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Step 2: 選擇課文 */}
                    <Card className={selectedCourseId ? '' : 'opacity-50'}>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <span className="bg-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">2</span>
                                選擇課文 (作業內容)
                            </CardTitle>
                            <CardDescription>
                                {selectedCourseId ? '從課程中選擇要指派的課文' : '請先選擇課程'}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {selectedCourseId && (
                                <>
                                    <Input 
                                        placeholder="搜尋課文..." 
                                        value={lessonSearch} 
                                        onChange={(e) => setLessonSearch(e.target.value)} 
                                        className="mb-4"
                                    />
                                    <div className="max-h-60 overflow-y-auto border rounded-md p-2 space-y-2">
                                        {availableLessons.map(lesson => (
                                            <div 
                                                key={lesson.id}
                                                className={`p-3 rounded-md cursor-pointer transition-colors ${
                                                    selectedLessonId === lesson.id 
                                                        ? 'bg-teal-100 border border-teal-300' 
                                                        : 'hover:bg-gray-100 border border-gray-200'
                                                }`}
                                                onClick={() => {
                                                    setSelectedLessonId(lesson.id);
                                                    if (!assignmentTitle) setAssignmentTitle(lesson.title);
                                                }}
                                            >
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <p className="font-semibold">{lesson.title}</p>
                                                        <p className="text-sm text-gray-500">
                                                            {lesson.activity_type === 'speaking_practice' ? '錄音集' : 
                                                             lesson.activity_type === 'speaking_scenario' ? '口說集' : 
                                                             lesson.activity_type}
                                                        </p>
                                                    </div>
                                                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                                                        {lesson.difficulty_level}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </>
                            )}
                        </CardContent>
                    </Card>

                    {/* Step 3: 選擇班級 */}
                    <Card className={selectedLessonId ? '' : 'opacity-50'}>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <span className="bg-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">3</span>
                                選擇班級
                            </CardTitle>
                            <CardDescription>
                                {selectedLessonId ? '選擇要指派作業的班級' : '請先選擇課文'}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {selectedLessonId && (
                                <div className="space-y-2">
                                    {availableClasses.map(cls => (
                                        <div 
                                            key={cls.id}
                                            className={`p-3 rounded-md cursor-pointer transition-colors ${
                                                selectedClassId === cls.id 
                                                    ? 'bg-teal-100 border border-teal-300' 
                                                    : 'hover:bg-gray-100 border border-gray-200'
                                            }`}
                                            onClick={() => setSelectedClassId(cls.id)}
                                        >
                                            <div className="flex justify-between items-center">
                                                <div>
                                                    <p className="font-semibold">{cls.class_name}</p>
                                                    {cls.difficulty_level && (
                                                        <p className="text-sm text-gray-500">{cls.difficulty_level}</p>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* 右欄：學生選擇與作業詳情 */}
                <div className="space-y-6">
                    {/* Step 4: 選擇學生 */}
                    <Card className={selectedClassId ? '' : 'opacity-50'}>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <span className="bg-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">4</span>
                                選擇學生
                            </CardTitle>
                            <CardDescription>
                                {selectedClassId ? '選擇要指派作業的學生' : '請先選擇班級'}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {selectedClassId && classStudents.length > 0 && (
                                <>
                                    <div className="mb-4 p-3 bg-gray-50 rounded-md">
                                        <div className="flex items-center space-x-2">
                                            <Checkbox
                                                id="select-all"
                                                checked={selectAllStudents}
                                                onCheckedChange={handleSelectAllToggle}
                                            />
                                            <label htmlFor="select-all" className="font-medium">
                                                全選 ({classStudents.length} 位學生)
                                            </label>
                                        </div>
                                        <p className="text-sm text-gray-600 mt-1">
                                            已選擇 {selectedStudents.size} 位學生
                                        </p>
                                    </div>

                                    <div className="max-h-64 overflow-y-auto space-y-2">
                                        {classStudents.map(student => (
                                            <div key={student.id} className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded">
                                                <Checkbox
                                                    id={`student-${student.id}`}
                                                    checked={selectedStudents.has(student.id)}
                                                    onCheckedChange={(checked) => handleStudentToggle(student.id, checked)}
                                                />
                                                <label htmlFor={`student-${student.id}`} className="flex-1 cursor-pointer">
                                                    <p className="font-medium">{student.student_name}</p>
                                                    <p className="text-sm text-gray-500">{student.email}</p>
                                                </label>
                                            </div>
                                        ))}
                                    </div>
                                </>
                            )}
                        </CardContent>
                    </Card>

                    {/* Step 5: 作業詳情 */}
                    <Card className={selectedStudents.size > 0 ? '' : 'opacity-50'}>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <span className="bg-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">5</span>
                                設定作業詳情
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <Label htmlFor="assignment-title">作業標題</Label>
                                <Input 
                                    id="assignment-title" 
                                    value={assignmentTitle} 
                                    onChange={(e) => setAssignmentTitle(e.target.value)}
                                    disabled={selectedStudents.size === 0}
                                />
                            </div>
                            <div>
                                <Label htmlFor="assignment-desc">作業說明 (選填)</Label>
                                <Textarea 
                                    id="assignment-desc" 
                                    value={assignmentDescription} 
                                    onChange={(e) => setAssignmentDescription(e.target.value)}
                                    disabled={selectedStudents.size === 0}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <Label>預約派發時間</Label>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <Button variant="outline" className="w-full justify-start text-left font-normal" disabled={selectedStudents.size === 0}>
                                                <CalendarIcon className="mr-2 h-4 w-4" />
                                                {format(dispatchDate, "yyyy-MM-dd HH:mm")}
                                            </Button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-auto p-0">
                                            <Calendar 
                                                mode="single" 
                                                selected={dispatchDate} 
                                                onSelect={setDispatchDate} 
                                                initialFocus 
                                            />
                                        </PopoverContent>
                                    </Popover>
                                </div>
                                <div>
                                    <Label>繳交期限</Label>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <Button variant="outline" className="w-full justify-start text-left font-normal" disabled={selectedStudents.size === 0}>
                                                <CalendarIcon className="mr-2 h-4 w-4" />
                                                {dueDate ? format(dueDate, "yyyy-MM-dd HH:mm") : <span>選擇日期</span>}
                                            </Button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-auto p-0">
                                            <Calendar 
                                                mode="single" 
                                                selected={dueDate} 
                                                onSelect={setDueDate} 
                                                initialFocus 
                                            />
                                        </PopoverContent>
                                    </Popover>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* 派發按鈕與狀態 */}
                    <div>
                        {error && (
                            <div className="text-red-500 p-3 bg-red-100 rounded-md mb-4 flex items-center gap-2">
                                <AlertCircle className="w-4 h-4"/>
                                {error}
                            </div>
                        )}
                        {successMessage && (
                            <div className="text-green-600 p-3 bg-green-100 rounded-md mb-4 flex items-center gap-2">
                                <CheckCircle className="w-4 h-4"/>
                                {successMessage}
                            </div>
                        )}
                        
                        <Button 
                            onClick={handleAssignHomework} 
                            disabled={isAssigning || selectedStudents.size === 0} 
                            className="w-full text-lg py-6 bg-teal-600 hover:bg-teal-700"
                        >
                            <Send className="mr-2 h-5 w-5" />
                            {isAssigning ? '派發中...' : `確認派發作業給 ${selectedStudents.size} 位學生`}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
