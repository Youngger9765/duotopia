
import React, { useState, useEffect } from 'react';
import { User } from '@/api/entities';
import { Class } from '@/api/entities';
import { Course } from '@/api/entities';
import { Lesson } from '@/api/entities';
import { StudentAssignment } from '@/api/entities';
import { AssignmentSubmission } from '@/api/entities';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { GraduationCap, FileText, Users, Clock, CheckCircle, AlertTriangle, Search, Filter, SortAsc } from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { motion } from 'framer-motion';

import GradingModal from '../components/teacher/GradingModal';

export default function GradingDashboard() {
    const [user, setUser] = useState(null);
    const [allClasses, setAllClasses] = useState([]);
    const [selectedClassId, setSelectedClassId] = useState('');
    const [classAssignments, setClassAssignments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    
    // 篩選和排序狀態
    const [filterCourse, setFilterCourse] = useState('all');
    const [filterLesson, setFilterLesson] = useState('all');
    // **修改：將排序改為陣列，支援複選**
    const [sortCriteria, setSortCriteria] = useState(['date']); // 預設按派發日期排序
    const [searchQuery, setSearchQuery] = useState('');
    
    // Modal states
    const [selectedAssignment, setSelectedAssignment] = useState(null);
    const [gradingModalOpen, setGradingModalOpen] = useState(false);

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        if (selectedClassId) {
            loadClassAssignments();
        }
    }, [selectedClassId]);

    const loadInitialData = async () => {
        setLoading(true);
        try {
            const currentUser = await User.me();
            setUser(currentUser);
            
            const classes = await Class.list();
            setAllClasses(classes);
            
        } catch (err) {
            console.error("Failed to load initial data:", err);
            setError("無法載入資料，請重新整理頁面。");
        } finally {
            setLoading(false);
        }
    };

    const loadClassAssignments = async () => {
        if (!selectedClassId) return;
        
        setLoading(true);
        try {
            const studentAssignmentRecords = await StudentAssignment.filter({ 
                class_id: selectedClassId 
            }, '-assigned_date');
            
            const assignmentGroups = {};
            studentAssignmentRecords.forEach(record => {
                if (!assignmentGroups[record.assignment_id]) {
                    assignmentGroups[record.assignment_id] = {
                        assignment_id: record.assignment_id,
                        lesson_id: record.lesson_id,
                        assignment_title: record.assignment_title,
                        activity_type: record.activity_type,
                        assigned_date: record.assigned_date,
                        due_date: record.due_date,
                        class_id: record.class_id,
                        teacher_email: record.teacher_email,
                        assignment_description: record.assignment_description,
                        scheduled_dispatch_date: record.scheduled_dispatch_date,
                        assignedStudents: new Set(),
                    };
                }
                assignmentGroups[record.assignment_id].assignedStudents.add(record.student_email);
            });
            
            const uniqueAssignments = Object.values(assignmentGroups).map(group => ({
                ...group,
                assignedStudents: Array.from(group.assignedStudents)
            }));
            
            // **核心新增：載入課程和課文資訊**
            const assignmentsWithStats = await Promise.all(
                uniqueAssignments.map(async (assignment) => {
                    const assignedStudentCount = assignment.assignedStudents.length;
                    
                    const [submissions, lesson] = await Promise.all([
                        AssignmentSubmission.filter({ assignment_id: assignment.assignment_id }),
                        Lesson.get(assignment.lesson_id)
                    ]);
                    
                    // 載入課程資訊
                    const course = lesson?.course_id ? await Course.get(lesson.course_id) : null;
                    
                    const submittedCount = submissions.filter(s => 
                        ['submitted', 'graded', 'needs_revision'].includes(s.submission_status)
                    ).length;
                    
                    const gradedCount = submissions.filter(s => s.submission_status === 'graded').length;
                    const needsRevisionCount = submissions.filter(s => s.submission_status === 'needs_revision').length;
                    
                    return {
                        ...assignment,
                        lesson,
                        course, // **新增課程資訊**
                        stats: {
                            totalStudents: assignedStudentCount,
                            submittedCount,
                            gradedCount,
                            needsRevisionCount,
                            notStartedCount: assignedStudentCount - submittedCount
                        }
                    };
                })
            );
            
            setClassAssignments(assignmentsWithStats);
            
        } catch (err) {
            console.error("Failed to load class assignments:", err);
            setError("無法載入班級作業資料。");
        } finally {
            setLoading(false);
        }
    };

    const handleAssignmentClick = (assignment) => {
        setSelectedAssignment(assignment);
        setGradingModalOpen(true);
    };

    const getActivityTypeInfo = (activityType) => {
        const types = {
            'reading_assessment': { label: '朗讀評估', emoji: '💬' },
            'speaking_practice': { label: '錄音集', emoji: '🎤' },
            'speaking_scenario': { label: '口說集', emoji: '🗣️' },
            'listening_cloze': { label: '聽力克漏字', emoji: '🎧' },
            'sentence_making': { label: '造句練習', emoji: '✍️' }
        };
        return types[activityType] || { label: activityType, emoji: '📝' };
    };

    const getStatusColor = (submitted, total, graded) => {
        if (graded === total) return 'text-green-600 bg-green-50 border-green-200';
        if (submitted > graded) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
        return 'text-gray-600 bg-gray-50 border-gray-200';
    };

    // **新增：處理排序按鈕點擊**
    const handleSortToggle = (sortKey) => {
        setSortCriteria(prev => {
            if (prev.includes(sortKey)) {
                // 如果已選中，則移除
                return prev.filter(key => key !== sortKey);
            } else {
                // 如果未選中，則加入
                return [...prev, sortKey];
            }
        });
    };

    // **修改：篩選和排序邏輯，支援多重排序**
    const filteredAndSortedAssignments = React.useMemo(() => {
        let filtered = [...classAssignments];
        
        // 根據課程篩選
        if (filterCourse !== 'all') {
            filtered = filtered.filter(assignment => assignment.course?.id === filterCourse);
        }
        
        // 根據課文篩選
        if (filterLesson !== 'all') {
            filtered = filtered.filter(assignment => assignment.lesson_id === filterLesson);
        }
        
        // 根據搜尋關鍵字篩選
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(assignment => 
                assignment.assignment_title.toLowerCase().includes(query) ||
                assignment.lesson?.title.toLowerCase().includes(query) ||
                assignment.course?.title.toLowerCase().includes(query)
            );
        }
        
        // **修改：多重排序邏輯**
        if (sortCriteria.length > 0) {
            filtered.sort((a, b) => {
                for (const sortKey of sortCriteria) {
                    let comparison = 0;
                    
                    switch (sortKey) {
                        case 'course':
                            comparison = (a.course?.title || '').localeCompare(b.course?.title || '');
                            break;
                        case 'lesson':
                            comparison = (a.lesson?.title || '').localeCompare(b.lesson?.title || '');
                            break;
                        case 'title':
                            comparison = a.assignment_title.localeCompare(b.assignment_title);
                            break;
                        case 'due_date':
                            // Older dates come first (ascending)
                            comparison = new Date(a.due_date) - new Date(b.due_date);
                            break;
                        case 'date':
                        default:
                            // Newer dates come first (descending)
                            comparison = new Date(b.assigned_date) - new Date(a.assigned_date);
                            break;
                    }
                    
                    if (comparison !== 0) {
                        return comparison;
                    }
                }
                return 0; // If all criteria are equal
            });
        }
        
        return filtered;
    }, [classAssignments, filterCourse, filterLesson, searchQuery, sortCriteria]);

    // **新增：取得可用的課程和課文選項**
    const availableCourses = React.useMemo(() => {
        const courses = new Map();
        classAssignments.forEach(assignment => {
            if (assignment.course) {
                courses.set(assignment.course.id, assignment.course);
            }
        });
        return Array.from(courses.values());
    }, [classAssignments]);

    const availableLessons = React.useMemo(() => {
        const lessons = new Map();
        let filtered = classAssignments;
        if (filterCourse !== 'all') {
            filtered = filtered.filter(assignment => assignment.course?.id === filterCourse);
        }
        filtered.forEach(assignment => {
            if (assignment.lesson) {
                lessons.set(assignment.lesson.id, assignment.lesson);
            }
        });
        return Array.from(lessons.values());
    }, [classAssignments, filterCourse]);

    if (loading && !selectedClassId) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600 font-medium">載入批改系統中...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* 頁面標題 */}
                <motion.div 
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-8"
                >
                    <div className="inline-flex items-center gap-4 bg-white/80 backdrop-blur-sm px-6 py-3 rounded-2xl shadow-lg border border-white/20 mb-6">
                        <GraduationCap className="w-8 h-8 text-blue-600" />
                        <div className="text-left">
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                                作業批改系統
                            </h1>
                            <p className="text-sm text-gray-700 font-medium mt-1">管理與批改學生作業</p>
                        </div>
                        <FileText className="w-6 h-6 text-indigo-500" />
                    </div>
                </motion.div>

                {/* 班級選擇器 */}
                <Card className="mb-8 bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Users className="w-5 h-5 text-blue-600" />
                            選擇批改班級
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-4">
                            <div className="flex-1">
                                <Select onValueChange={setSelectedClassId} value={selectedClassId}>
                                    <SelectTrigger className="w-full">
                                        <SelectValue placeholder="請選擇要批改作業的班級..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {allClasses.map(cls => (
                                            <SelectItem key={cls.id} value={cls.id}>
                                                {cls.class_name}
                                                {cls.difficulty_level && ` (${cls.difficulty_level})`}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            {selectedClassId && (
                                <Button 
                                    onClick={loadClassAssignments} 
                                    disabled={loading}
                                    className="bg-blue-600 hover:bg-blue-700 text-white"
                                >
                                    {loading ? "載入中..." : "重新載入"}
                                </Button>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* **修改：篩選和排序控制** */}
                {selectedClassId && classAssignments.length > 0 && (
                    <Card className="mb-6 bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                        <CardContent className="p-4 space-y-4">
                            {/* 第一行：搜尋和篩選 */}
                            <div className="flex flex-wrap items-center gap-4">
                                <div className="flex items-center gap-2">
                                    <Search className="w-4 h-4 text-gray-500" />
                                    <Input
                                        placeholder="搜尋作業標題、課文或課程..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="w-64"
                                    />
                                </div>
                                
                                <div className="flex items-center gap-2">
                                    <Filter className="w-4 h-4 text-gray-500" />
                                    <Select value={filterCourse} onValueChange={setFilterCourse}>
                                        <SelectTrigger className="w-40">
                                            <SelectValue placeholder="課程" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">所有課程</SelectItem>
                                            {availableCourses.map(course => (
                                                <SelectItem key={course.id} value={course.id}>
                                                    {course.title}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="flex items-center gap-2">
                                    <Select value={filterLesson} onValueChange={setFilterLesson}>
                                        <SelectTrigger className="w-40">
                                            <SelectValue placeholder="課文" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">所有課文</SelectItem>
                                            {availableLessons.map(lesson => (
                                                <SelectItem key={lesson.id} value={lesson.id}>
                                                    {lesson.title}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            {/* **新增：第二行排序按鈕** */}
                            <div className="flex items-center gap-3 pt-2 border-t border-gray-100">
                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                    <SortAsc className="w-4 h-4" />
                                    <span className="font-medium">排序方式：</span>
                                </div>
                                
                                <div className="flex flex-wrap gap-2">
                                    {[
                                        { key: 'date', label: '派發日期' },
                                        { key: 'due_date', label: '截止日期' },
                                        { key: 'course', label: '課程' },
                                        { key: 'lesson', label: '課文' },
                                        { key: 'title', label: '作業標題' }
                                    ].map(({ key, label }) => (
                                        <Button
                                            key={key}
                                            variant={sortCriteria.includes(key) ? "default" : "outline"}
                                            size="sm"
                                            onClick={() => handleSortToggle(key)}
                                            className={`transition-all ${
                                                sortCriteria.includes(key) 
                                                    ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-md' 
                                                    : 'hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700'
                                            }`}
                                        >
                                            {label}
                                            {sortCriteria.includes(key) && (
                                                <span className="ml-1 text-xs bg-white/20 rounded-full px-1.5 py-0.5">
                                                    {sortCriteria.indexOf(key) + 1}
                                                </span>
                                            )}
                                        </Button>
                                    ))}
                                </div>
                                
                                {/* 清除排序按鈕 */}
                                {sortCriteria.length > 0 && (
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setSortCriteria([])}
                                        className="text-gray-500 hover:text-red-600 ml-2"
                                    >
                                        清除排序
                                    </Button>
                                )}
                            </div>
                            
                            {/* **新增：顯示當前排序狀態** */}
                            {sortCriteria.length > 0 && (
                                <div className="text-xs text-gray-500 bg-gray-50 rounded px-3 py-2">
                                    <span className="font-medium">目前排序：</span>
                                    {sortCriteria.map((key, index) => {
                                        const sortLabels = {
                                            'date': '派發日期',
                                            'due_date': '截止日期',
                                            'course': '課程',
                                            'lesson': '課文',
                                            'title': '作業標題'
                                        };
                                        return (
                                            <span key={key}>
                                                {index > 0 && ' → '}
                                                <span className="font-medium text-blue-600">
                                                    {index + 1}. {sortLabels[key]}
                                                </span>
                                            </span>
                                        );
                                    })}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* 作業列表 */}
                {selectedClassId && (
                    <div className="space-y-4">
                        {filteredAndSortedAssignments.length === 0 && !loading ? (
                            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                                <CardContent className="text-center py-12">
                                    <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                        {classAssignments.length === 0 ? '此班級尚無作業' : '找不到符合條件的作業'}
                                    </h3>
                                    <p className="text-gray-600">
                                        {classAssignments.length === 0 
                                            ? '請先到「指派作業」頁面為學生建立作業。'
                                            : '請調整篩選條件或搜尋關鍵字。'
                                        }
                                    </p>
                                </CardContent>
                            </Card>
                        ) : (
                            filteredAndSortedAssignments.map((assignment, index) => {
                                const activityInfo = getActivityTypeInfo(assignment.activity_type);
                                return (
                                <motion.div
                                    key={assignment.assignment_id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                >
                                    <Card 
                                        className="bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer"
                                        onClick={() => handleAssignmentClick(assignment)}
                                    >
                                        <CardContent className="p-6">
                                            <div className="flex justify-between items-start">
                                                <div className="flex-1">
                                                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                                                        {assignment.assignment_title}
                                                    </h3>
                                                    <div className="flex items-center gap-2 mb-4 flex-wrap">
                                                        <Badge 
                                                            variant="outline" 
                                                            className="bg-blue-50 text-blue-700 border-blue-200 flex items-center"
                                                        >
                                                            <span className="mr-1.5">{activityInfo.emoji}</span>
                                                            {activityInfo.label}
                                                        </Badge>
                                                        
                                                        {/* **新增：課程資訊** */}
                                                        {assignment.course && (
                                                            <Badge 
                                                                variant="outline" 
                                                                className="bg-purple-50 text-purple-700 border-purple-200"
                                                            >
                                                                課程: {assignment.course.title}
                                                            </Badge>
                                                        )}
                                                        
                                                        <Badge 
                                                            variant="outline" 
                                                            className="bg-gray-100 text-gray-700 border-gray-200"
                                                        >
                                                            課文: {assignment.lesson?.title}
                                                        </Badge>
                                                        <Badge 
                                                            variant="outline" 
                                                            className="bg-gray-50 text-gray-600 border-gray-200"
                                                        >
                                                            ID: {assignment.assignment_id.slice(-8)}
                                                        </Badge>
                                                    </div>
                                                    
                                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                                        <div>
                                                            <p className="text-gray-500">派發日期</p>
                                                            <p className="font-medium">
                                                                {format(new Date(assignment.assigned_date), 'MM/dd', { locale: zhCN })}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-gray-500">截止日期</p>
                                                            <p className="font-medium text-red-600">
                                                                {format(new Date(assignment.due_date), 'MM/dd', { locale: zhCN })}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-gray-500">繳交情況</p>
                                                            <p className="font-medium">
                                                                {assignment.stats.submittedCount}/{assignment.stats.totalStudents}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-gray-500">批改進度</p>
                                                            <p className="font-medium">
                                                                {assignment.stats.gradedCount}/{assignment.stats.totalStudents}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <div className="flex flex-col items-end gap-2">
                                                    <div className={`px-3 py-1 rounded-full text-sm font-medium border ${
                                                        getStatusColor(
                                                            assignment.stats.submittedCount, 
                                                            assignment.stats.totalStudents,
                                                            assignment.stats.gradedCount
                                                        )
                                                    }`}>
                                                        {assignment.stats.gradedCount === assignment.stats.totalStudents 
                                                            ? '批改完成' 
                                                            : assignment.stats.submittedCount > assignment.stats.gradedCount
                                                            ? '待批改'
                                                            : '待繳交'
                                                        }
                                                    </div>
                                                    
                                                    {assignment.stats.needsRevisionCount > 0 && (
                                                        <Badge variant="destructive" className="text-xs">
                                                            {assignment.stats.needsRevisionCount} 份需訂正
                                                        </Badge>
                                                    )}
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                </motion.div>
                            )})
                        )}
                    </div>
                )}

                {/* 批改Modal */}
                {selectedAssignment && (
                    <GradingModal
                        isOpen={gradingModalOpen}
                        onClose={() => {
                            setGradingModalOpen(false);
                            setSelectedAssignment(null);
                            loadClassAssignments(); // 重新載入資料
                        }}
                        assignment={selectedAssignment}
                    />
                )}
            </div>
        </div>
    );
}
