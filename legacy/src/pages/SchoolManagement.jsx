import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { School, Building2, Users, GraduationCap, Calendar, Plus, Edit, Trash2, Save, X, ChevronDown, Search, BookOpen } from "lucide-react";
import { School as SchoolEntity } from "@/api/entities";
import { SchoolTeacher } from "@/api/entities";
import { SchoolStudent } from "@/api/entities";
import { Semester } from "@/api/entities";
import { motion, AnimatePresence } from "framer-motion";

export default function SchoolManagement() {
    const [schools, setSchools] = useState([]);
    const [selectedSchool, setSelectedSchool] = useState(null);
    const [teachers, setTeachers] = useState([]);
    const [students, setStudents] = useState([]);
    const [semesters, setSemesters] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // Modal states
    const [showSchoolModal, setShowSchoolModal] = useState(false);
    const [showTeacherModal, setShowTeacherModal] = useState(false);
    const [showStudentModal, setShowStudentModal] = useState(false);
    const [showSemesterModal, setShowSemesterModal] = useState(false);
    
    // Edit states
    const [editingSchool, setEditingSchool] = useState(null);
    const [editingTeacher, setEditingTeacher] = useState(null);
    const [editingStudent, setEditingStudent] = useState(null);
    const [editingSemester, setEditingSemester] = useState(null);
    
    // Search states
    const [teacherSearch, setTeacherSearch] = useState("");
    const [studentSearch, setStudentSearch] = useState("");
    
    // Expanded states
    const [expandedSchools, setExpandedSchools] = useState(new Set());

    useEffect(() => {
        loadSchools();
    }, []);

    useEffect(() => {
        if (selectedSchool) {
            loadSchoolData(selectedSchool.id);
        }
    }, [selectedSchool]);

    const loadSchools = async () => {
        setLoading(true);
        try {
            const schoolsData = await SchoolEntity.list();
            setSchools(schoolsData);
        } catch (error) {
            console.error("載入學校失敗:", error);
        } finally {
            setLoading(false);
        }
    };

    const loadSchoolData = async (schoolId) => {
        try {
            const [teachersData, studentsData, semestersData] = await Promise.all([
                SchoolTeacher.filter({ school_id: schoolId }),
                SchoolStudent.filter({ school_id: schoolId }),
                Semester.filter({ school_id: schoolId })
            ]);
            
            setTeachers(teachersData);
            setStudents(studentsData);
            setSemesters(semestersData);
        } catch (error) {
            console.error("載入學校資料失敗:", error);
        }
    };

    const handleCreateSchool = async (schoolData) => {
        try {
            await SchoolEntity.create(schoolData);
            loadSchools();
            setShowSchoolModal(false);
            setEditingSchool(null);
        } catch (error) {
            console.error("建立學校失敗:", error);
            alert('建立學校失敗，請重試');
        }
    };

    const handleCreateTeacher = async (teacherData) => {
        try {
            await SchoolTeacher.create({ ...teacherData, school_id: selectedSchool.id });
            loadSchoolData(selectedSchool.id);
            setShowTeacherModal(false);
            setEditingTeacher(null);
        } catch (error) {
            console.error("建立教師失敗:", error);
            alert('建立教師失敗，請重試');
        }
    };

    const handleCreateStudent = async (studentData) => {
        try {
            await SchoolStudent.create({ ...studentData, school_id: selectedSchool.id });
            loadSchoolData(selectedSchool.id);
            setShowStudentModal(false);
            setEditingStudent(null);
        } catch (error) {
            console.error("建立學生失敗:", error);
            alert('建立學生失敗，請重試');
        }
    };

    const handleCreateSemester = async (semesterData) => {
        try {
            await Semester.create({ ...semesterData, school_id: selectedSchool.id });
            loadSchoolData(selectedSchool.id);
            setShowSemesterModal(false);
            setEditingSemester(null);
        } catch (error) {
            console.error("建立學期失敗:", error);
            alert('建立學期失敗，請重試');
        }
    };

    const toggleSchoolExpanded = (schoolId) => {
        const newExpanded = new Set(expandedSchools);
        if (newExpanded.has(schoolId)) {
            newExpanded.delete(schoolId);
        } else {
            newExpanded.add(schoolId);
        }
        setExpandedSchools(newExpanded);
    };

    const filteredTeachers = teachers.filter(teacher => 
        teacher.teacher_name.toLowerCase().includes(teacherSearch.toLowerCase()) ||
        teacher.email.toLowerCase().includes(teacherSearch.toLowerCase())
    );

    const filteredStudents = students.filter(student => 
        student.student_name.toLowerCase().includes(studentSearch.toLowerCase()) ||
        student.email.toLowerCase().includes(studentSearch.toLowerCase()) ||
        student.class_name?.toLowerCase().includes(studentSearch.toLowerCase())
    );

    if (loading) {
        return (
            <div className="p-6 min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600">載入學校管理系統...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
            <div className="max-w-7xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">學校管理系統</h1>
                        <p className="text-gray-600">管理學校、教師名冊、學生名單與學期資料</p>
                    </div>
                    <Button 
                        onClick={() => {
                            setEditingSchool(null);
                            setShowSchoolModal(true);
                        }}
                        className="gradient-bg text-white shadow-lg hover:shadow-xl transition-shadow"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        新增學校
                    </Button>
                </div>

                {schools.length === 0 ? (
                    <Card className="text-center py-12">
                        <CardContent>
                            <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                            <h3 className="text-xl font-semibold text-gray-900 mb-2">尚未建立任何學校</h3>
                            <p className="text-gray-600 mb-6">建立您的第一個學校開始管理</p>
                            <Button 
                                onClick={() => {
                                    setEditingSchool(null);
                                    setShowSchoolModal(true);
                                }}
                                className="gradient-bg text-white shadow-lg hover:shadow-xl transition-shadow"
                                size="lg"
                            >
                                <Plus className="w-5 h-5 mr-2" />
                                建立第一個學校
                            </Button>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="space-y-6">
                        {schools.map(school => (
                            <Card key={school.id} className="shadow-lg hover:shadow-xl transition-all duration-300 border-l-4 border-l-blue-500">
                                <Collapsible
                                    open={expandedSchools.has(school.id)}
                                    onOpenChange={() => toggleSchoolExpanded(school.id)}
                                >
                                    <CollapsibleTrigger asChild>
                                        <div className="cursor-pointer hover:bg-gray-50/50 transition-colors">
                                            <CardHeader>
                                                <div className="flex justify-between items-center">
                                                    <div className="flex items-center gap-4">
                                                        <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center">
                                                            <Building2 className="w-6 h-6 text-white" />
                                                        </div>
                                                        <div>
                                                            <CardTitle className="text-xl font-bold text-gray-900">{school.school_name}</CardTitle>
                                                            <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                                                                <Badge variant="outline">{school.school_type}</Badge>
                                                                <span>代碼: {school.school_code}</span>
                                                                {school.established_year && <span>創校: {school.established_year}</span>}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <Button
                                                            size="sm"
                                                            variant="ghost"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                setEditingSchool(school);
                                                                setShowSchoolModal(true);
                                                            }}
                                                        >
                                                            <Edit className="w-4 h-4" />
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            variant="ghost"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                setSelectedSchool(school);
                                                            }}
                                                        >
                                                            <BookOpen className="w-4 h-4" />
                                                        </Button>
                                                        <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${expandedSchools.has(school.id) ? 'rotate-180' : ''}`} />
                                                    </div>
                                                </div>
                                            </CardHeader>
                                        </div>
                                    </CollapsibleTrigger>
                                    
                                    <CollapsibleContent>
                                        <div className="px-6 pb-6 border-t bg-gradient-to-br from-gray-50 to-blue-50/30">
                                            <div className="mt-6">
                                                <Button
                                                    onClick={() => setSelectedSchool(school)}
                                                    className="gradient-bg text-white"
                                                >
                                                    管理此學校
                                                </Button>
                                            </div>
                                        </div>
                                    </CollapsibleContent>
                                </Collapsible>
                            </Card>
                        ))}
                    </div>
                )}

                {/* 學校詳細管理 */}
                {selectedSchool && (
                    <Card className="mt-8 shadow-xl">
                        <CardHeader className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white">
                            <div className="flex justify-between items-center">
                                <CardTitle className="text-xl">{selectedSchool.school_name} - 管理面板</CardTitle>
                                <Button variant="ghost" size="sm" onClick={() => setSelectedSchool(null)} className="text-white hover:bg-white/20">
                                    <X className="w-4 h-4" />
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent className="p-0">
                            <Tabs defaultValue="teachers" className="w-full">
                                <TabsList className="grid w-full grid-cols-3 bg-gray-100 m-6 mb-0">
                                    <TabsTrigger value="teachers" className="flex items-center gap-2">
                                        <Users className="w-4 h-4" />
                                        教師名冊
                                    </TabsTrigger>
                                    <TabsTrigger value="students" className="flex items-center gap-2">
                                        <GraduationCap className="w-4 h-4" />
                                        學生名單
                                    </TabsTrigger>
                                    <TabsTrigger value="semesters" className="flex items-center gap-2">
                                        <Calendar className="w-4 h-4" />
                                        學期管理
                                    </TabsTrigger>
                                </TabsList>

                                <TabsContent value="teachers" className="p-6">
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <div className="flex items-center gap-4">
                                                <div className="relative">
                                                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                                    <Input
                                                        placeholder="搜尋教師..."
                                                        value={teacherSearch}
                                                        onChange={(e) => setTeacherSearch(e.target.value)}
                                                        className="pl-10 w-64"
                                                    />
                                                </div>
                                                <Badge variant="secondary">{filteredTeachers.length} 位教師</Badge>
                                            </div>
                                            <Button
                                                onClick={() => {
                                                    setEditingTeacher(null);
                                                    setShowTeacherModal(true);
                                                }}
                                                className="gradient-bg text-white"
                                            >
                                                <Plus className="w-4 h-4 mr-2" />
                                                新增教師
                                            </Button>
                                        </div>

                                        <div className="grid gap-4">
                                            {filteredTeachers.map(teacher => (
                                                <TeacherCard
                                                    key={teacher.id}
                                                    teacher={teacher}
                                                    onEdit={() => {
                                                        setEditingTeacher(teacher);
                                                        setShowTeacherModal(true);
                                                    }}
                                                    onDelete={async () => {
                                                        if (confirm('確定要刪除此教師嗎？')) {
                                                            await SchoolTeacher.delete(teacher.id);
                                                            loadSchoolData(selectedSchool.id);
                                                        }
                                                    }}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                </TabsContent>

                                <TabsContent value="students" className="p-6">
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <div className="flex items-center gap-4">
                                                <div className="relative">
                                                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                                                    <Input
                                                        placeholder="搜尋學生..."
                                                        value={studentSearch}
                                                        onChange={(e) => setStudentSearch(e.target.value)}
                                                        className="pl-10 w-64"
                                                    />
                                                </div>
                                                <Badge variant="secondary">{filteredStudents.length} 位學生</Badge>
                                            </div>
                                            <Button
                                                onClick={() => {
                                                    setEditingStudent(null);
                                                    setShowStudentModal(true);
                                                }}
                                                className="gradient-bg text-white"
                                            >
                                                <Plus className="w-4 h-4 mr-2" />
                                                新增學生
                                            </Button>
                                        </div>

                                        <div className="grid gap-4">
                                            {filteredStudents.map(student => (
                                                <StudentCard
                                                    key={student.id}
                                                    student={student}
                                                    onEdit={() => {
                                                        setEditingStudent(student);
                                                        setShowStudentModal(true);
                                                    }}
                                                    onDelete={async () => {
                                                        if (confirm('確定要刪除此學生嗎？')) {
                                                            await SchoolStudent.delete(student.id);
                                                            loadSchoolData(selectedSchool.id);
                                                        }
                                                    }}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                </TabsContent>

                                <TabsContent value="semesters" className="p-6">
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <Badge variant="secondary">{semesters.length} 個學期</Badge>
                                            <Button
                                                onClick={() => {
                                                    setEditingSemester(null);
                                                    setShowSemesterModal(true);
                                                }}
                                                className="gradient-bg text-white"
                                            >
                                                <Plus className="w-4 h-4 mr-2" />
                                                新增學期
                                            </Button>
                                        </div>

                                        <div className="grid gap-4">
                                            {semesters.map(semester => (
                                                <SemesterCard
                                                    key={semester.id}
                                                    semester={semester}
                                                    onEdit={() => {
                                                        setEditingSemester(semester);
                                                        setShowSemesterModal(true);
                                                    }}
                                                    onDelete={async () => {
                                                        if (confirm('確定要刪除此學期嗎？')) {
                                                            await Semester.delete(semester.id);
                                                            loadSchoolData(selectedSchool.id);
                                                        }
                                                    }}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                </TabsContent>
                            </Tabs>
                        </CardContent>
                    </Card>
                )}

                {/* 各種 Modal */}
                <SchoolModal
                    isOpen={showSchoolModal}
                    onClose={() => {
                        setShowSchoolModal(false);
                        setEditingSchool(null);
                    }}
                    onSave={handleCreateSchool}
                    school={editingSchool}
                />

                <TeacherModal
                    isOpen={showTeacherModal}
                    onClose={() => {
                        setShowTeacherModal(false);
                        setEditingTeacher(null);
                    }}
                    onSave={handleCreateTeacher}
                    teacher={editingTeacher}
                />

                <StudentModal
                    isOpen={showStudentModal}
                    onClose={() => {
                        setShowStudentModal(false);
                        setEditingStudent(null);
                    }}
                    onSave={handleCreateStudent}
                    student={editingStudent}
                    semesters={semesters}
                />

                <SemesterModal
                    isOpen={showSemesterModal}
                    onClose={() => {
                        setShowSemesterModal(false);
                        setEditingSemester(null);
                    }}
                    onSave={handleCreateSemester}
                    semester={editingSemester}
                />
            </div>
        </div>
    );
}

// Teacher Card Component
function TeacherCard({ teacher, onEdit, onDelete }) {
    return (
        <Card className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
                <div className="flex justify-between items-start">
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
                                <Users className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-gray-900">{teacher.teacher_name}</h3>
                                <p className="text-sm text-gray-600">{teacher.email}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                            <Badge variant="outline">{teacher.position}</Badge>
                            {teacher.department && <span>{teacher.department}</span>}
                            {teacher.employee_id && <span>職員編號: {teacher.employee_id}</span>}
                        </div>
                        {teacher.subjects && teacher.subjects.length > 0 && (
                            <div className="mt-2">
                                <span className="text-xs text-gray-500">任教科目: </span>
                                {teacher.subjects.map(subject => (
                                    <Badge key={subject} variant="secondary" className="mr-1 text-xs">
                                        {subject}
                                    </Badge>
                                ))}
                            </div>
                        )}
                    </div>
                    <div className="flex gap-2">
                        <Button variant="ghost" size="sm" onClick={onEdit}>
                            <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={onDelete} className="text-red-600 hover:text-red-700">
                            <Trash2 className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

// Student Card Component
function StudentCard({ student, onEdit, onDelete }) {
    return (
        <Card className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
                <div className="flex justify-between items-start">
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full flex items-center justify-center">
                                <GraduationCap className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-gray-900">{student.student_name}</h3>
                                <p className="text-sm text-gray-600">{student.email}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                            <Badge variant="outline">{student.grade_level}</Badge>
                            {student.class_name && <span>{student.class_name}</span>}
                            <span>學號: {student.student_id}</span>
                        </div>
                        {student.semester && (
                            <div className="mt-2">
                                <Badge variant="secondary" className="text-xs">{student.semester}</Badge>
                            </div>
                        )}
                    </div>
                    <div className="flex gap-2">
                        <Button variant="ghost" size="sm" onClick={onEdit}>
                            <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={onDelete} className="text-red-600 hover:text-red-700">
                            <Trash2 className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

// Semester Card Component
function SemesterCard({ semester, onEdit, onDelete }) {
    return (
        <Card className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
                <div className="flex justify-between items-start">
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                                <Calendar className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-gray-900">{semester.semester_name}</h3>
                                <p className="text-sm text-gray-600">{semester.academic_year}學年度 {semester.semester_type}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                            {semester.start_date && <span>開始: {semester.start_date}</span>}
                            {semester.end_date && <span>結束: {semester.end_date}</span>}
                            {semester.is_active && <Badge variant="default">當前學期</Badge>}
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="ghost" size="sm" onClick={onEdit}>
                            <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={onDelete} className="text-red-600 hover:text-red-700">
                            <Trash2 className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

// School Modal Component
function SchoolModal({ isOpen, onClose, onSave, school }) {
    const [formData, setFormData] = useState({
        school_name: '',
        school_code: '',
        address: '',
        phone: '',
        principal_name: '',
        established_year: new Date().getFullYear(),
        school_type: '國小'
    });

    useEffect(() => {
        if (school) {
            setFormData(school);
        } else {
            setFormData({
                school_name: '',
                school_code: '',
                address: '',
                phone: '',
                principal_name: '',
                established_year: new Date().getFullYear(),
                school_type: '國小'
            });
        }
    }, [school, isOpen]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (school) {
            SchoolEntity.update(school.id, formData).then(() => {
                onSave();
            });
        } else {
            onSave(formData);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>{school ? '編輯學校' : '新增學校'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>學校名稱 *</Label>
                            <Input
                                value={formData.school_name}
                                onChange={(e) => setFormData({...formData, school_name: e.target.value})}
                                required
                            />
                        </div>
                        <div>
                            <Label>學校代碼 *</Label>
                            <Input
                                value={formData.school_code}
                                onChange={(e) => setFormData({...formData, school_code: e.target.value})}
                                required
                            />
                        </div>
                    </div>
                    
                    <div>
                        <Label>學校類型</Label>
                        <Select value={formData.school_type} onValueChange={(value) => setFormData({...formData, school_type: value})}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="國小">國小</SelectItem>
                                <SelectItem value="國中">國中</SelectItem>
                                <SelectItem value="高中">高中</SelectItem>
                                <SelectItem value="高職">高職</SelectItem>
                                <SelectItem value="大學">大學</SelectItem>
                                <SelectItem value="其他">其他</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div>
                        <Label>學校地址</Label>
                        <Input
                            value={formData.address}
                            onChange={(e) => setFormData({...formData, address: e.target.value})}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>聯絡電話</Label>
                            <Input
                                value={formData.phone}
                                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                            />
                        </div>
                        <div>
                            <Label>創校年份</Label>
                            <Input
                                type="number"
                                value={formData.established_year}
                                onChange={(e) => setFormData({...formData, established_year: parseInt(e.target.value)})}
                            />
                        </div>
                    </div>

                    <div>
                        <Label>校長姓名</Label>
                        <Input
                            value={formData.principal_name}
                            onChange={(e) => setFormData({...formData, principal_name: e.target.value})}
                        />
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={onClose}>取消</Button>
                        <Button type="submit" className="gradient-bg text-white">
                            {school ? '更新' : '建立'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

// Teacher Modal Component
function TeacherModal({ isOpen, onClose, onSave, teacher }) {
    const [formData, setFormData] = useState({
        teacher_name: '',
        email: '',
        employee_id: '',
        phone: '',
        department: '',
        position: '教師',
        subjects: [],
        hire_date: '',
        notes: ''
    });

    const [newSubject, setNewSubject] = useState('');

    useEffect(() => {
        if (teacher) {
            setFormData(teacher);
        } else {
            setFormData({
                teacher_name: '',
                email: '',
                employee_id: '',
                phone: '',
                department: '',
                position: '教師',
                subjects: [],
                hire_date: '',
                notes: ''
            });
        }
    }, [teacher, isOpen]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (teacher) {
            SchoolTeacher.update(teacher.id, formData).then(() => {
                onSave();
            });
        } else {
            onSave(formData);
        }
    };

    const addSubject = () => {
        if (newSubject.trim() && !formData.subjects.includes(newSubject.trim())) {
            setFormData({
                ...formData,
                subjects: [...formData.subjects, newSubject.trim()]
            });
            setNewSubject('');
        }
    };

    const removeSubject = (subject) => {
        setFormData({
            ...formData,
            subjects: formData.subjects.filter(s => s !== subject)
        });
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>{teacher ? '編輯教師' : '新增教師'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>教師姓名 *</Label>
                            <Input
                                value={formData.teacher_name}
                                onChange={(e) => setFormData({...formData, teacher_name: e.target.value})}
                                required
                            />
                        </div>
                        <div>
                            <Label>電子郵件 *</Label>
                            <Input
                                type="email"
                                value={formData.email}
                                onChange={(e) => setFormData({...formData, email: e.target.value})}
                                required
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>職員編號</Label>
                            <Input
                                value={formData.employee_id}
                                onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
                            />
                        </div>
                        <div>
                            <Label>聯絡電話</Label>
                            <Input
                                value={formData.phone}
                                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>職務</Label>
                            <Select value={formData.position} onValueChange={(value) => setFormData({...formData, position: value})}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="教師">教師</SelectItem>
                                    <SelectItem value="主任">主任</SelectItem>
                                    <SelectItem value="組長">組長</SelectItem>
                                    <SelectItem value="校長">校長</SelectItem>
                                    <SelectItem value="副校長">副校長</SelectItem>
                                    <SelectItem value="代課教師">代課教師</SelectItem>
                                    <SelectItem value="實習教師">實習教師</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <Label>任教科系/部門</Label>
                            <Input
                                value={formData.department}
                                onChange={(e) => setFormData({...formData, department: e.target.value})}
                            />
                        </div>
                    </div>

                    <div>
                        <Label>任教科目</Label>
                        <div className="flex gap-2 mb-2">
                            <Input
                                value={newSubject}
                                onChange={(e) => setNewSubject(e.target.value)}
                                placeholder="新增科目"
                                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSubject())}
                            />
                            <Button type="button" onClick={addSubject} variant="outline">
                                <Plus className="w-4 h-4" />
                            </Button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {formData.subjects.map(subject => (
                                <Badge key={subject} variant="secondary" className="cursor-pointer" onClick={() => removeSubject(subject)}>
                                    {subject} <X className="w-3 h-3 ml-1" />
                                </Badge>
                            ))}
                        </div>
                    </div>

                    <div>
                        <Label>到職日期</Label>
                        <Input
                            type="date"
                            value={formData.hire_date}
                            onChange={(e) => setFormData({...formData, hire_date: e.target.value})}
                        />
                    </div>

                    <div>
                        <Label>備註</Label>
                        <Textarea
                            value={formData.notes}
                            onChange={(e) => setFormData({...formData, notes: e.target.value})}
                            rows={3}
                        />
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={onClose}>取消</Button>
                        <Button type="submit" className="gradient-bg text-white">
                            {teacher ? '更新' : '建立'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

// Student Modal Component
function StudentModal({ isOpen, onClose, onSave, student, semesters }) {
    const [formData, setFormData] = useState({
        student_name: '',
        email: '',
        student_id: '',
        grade_level: '',
        class_name: '',
        semester: semesters.length > 0 ? semesters[0].semester_name : '113學年度上學期',
        parent_name: '',
        parent_phone: '',
        birth_date: '',
        enroll_date: '',
        notes: ''
    });

    useEffect(() => {
        if (student) {
            setFormData(student);
        } else {
            setFormData({
                student_name: '',
                email: '',
                student_id: '',
                grade_level: '',
                class_name: '',
                semester: semesters.length > 0 ? semesters[0].semester_name : '113學年度上學期',
                parent_name: '',
                parent_phone: '',
                birth_date: '',
                enroll_date: '',
                notes: ''
            });
        }
    }, [student, isOpen, semesters]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (student) {
            SchoolStudent.update(student.id, formData).then(() => {
                onSave();
            });
        } else {
            onSave(formData);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>{student ? '編輯學生' : '新增學生'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>學生姓名 *</Label>
                            <Input
                                value={formData.student_name}
                                onChange={(e) => setFormData({...formData, student_name: e.target.value})}
                                required
                            />
                        </div>
                        <div>
                            <Label>電子郵件 *</Label>
                            <Input
                                type="email"
                                value={formData.email}
                                onChange={(e) => setFormData({...formData, email: e.target.value})}
                                required
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>學號 *</Label>
                            <Input
                                value={formData.student_id}
                                onChange={(e) => setFormData({...formData, student_id: e.target.value})}
                                required
                            />
                        </div>
                        <div>
                            <Label>年級</Label>
                            <Input
                                value={formData.grade_level}
                                onChange={(e) => setFormData({...formData, grade_level: e.target.value})}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>班級</Label>
                            <Input
                                value={formData.class_name}
                                onChange={(e) => setFormData({...formData, class_name: e.target.value})}
                            />
                        </div>
                        <div>
                            <Label>學期</Label>
                            <Select value={formData.semester} onValueChange={(value) => setFormData({...formData, semester: value})}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {semesters.map(semester => (
                                        <SelectItem key={semester.id} value={semester.semester_name}>
                                            {semester.semester_name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>家長姓名</Label>
                            <Input
                                value={formData.parent_name}
                                onChange={(e) => setFormData({...formData, parent_name: e.target.value})}
                            />
                        </div>
                        <div>
                            <Label>家長電話</Label>
                            <Input
                                value={formData.parent_phone}
                                onChange={(e) => setFormData({...formData, parent_phone: e.target.value})}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>出生日期</Label>
                            <Input
                                type="date"
                                value={formData.birth_date}
                                onChange={(e) => setFormData({...formData, birth_date: e.target.value})}
                            />
                        </div>
                        <div>
                            <Label>入學日期</Label>
                            <Input
                                type="date"
                                value={formData.enroll_date}
                                onChange={(e) => setFormData({...formData, enroll_date: e.target.value})}
                            />
                        </div>
                    </div>

                    <div>
                        <Label>備註</Label>
                        <Textarea
                            value={formData.notes}
                            onChange={(e) => setFormData({...formData, notes: e.target.value})}
                            rows={3}
                        />
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={onClose}>取消</Button>
                        <Button type="submit" className="gradient-bg text-white">
                            {student ? '更新' : '建立'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

// Semester Modal Component
function SemesterModal({ isOpen, onClose, onSave, semester }) {
    const [formData, setFormData] = useState({
        semester_name: '',
        academic_year: '',
        semester_type: '上學期',
        start_date: '',
        end_date: '',
        is_active: false
    });

    useEffect(() => {
        if (semester) {
            setFormData(semester);
        } else {
            const currentYear = new Date().getFullYear() - 1911; // 民國年
            setFormData({
                semester_name: `${currentYear}學年度上學期`,
                academic_year: currentYear.toString(),
                semester_type: '上學期',
                start_date: '',
                end_date: '',
                is_active: false
            });
        }
    }, [semester, isOpen]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (semester) {
            Semester.update(semester.id, formData).then(() => {
                onSave();
            });
        } else {
            onSave(formData);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle>{semester ? '編輯學期' : '新增學期'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <Label>學期名稱 *</Label>
                        <Input
                            value={formData.semester_name}
                            onChange={(e) => setFormData({...formData, semester_name: e.target.value})}
                            required
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>學年度 *</Label>
                            <Input
                                value={formData.academic_year}
                                onChange={(e) => setFormData({...formData, academic_year: e.target.value})}
                                required
                            />
                        </div>
                        <div>
                            <Label>學期類型</Label>
                            <Select value={formData.semester_type} onValueChange={(value) => setFormData({...formData, semester_type: value})}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="上學期">上學期</SelectItem>
                                    <SelectItem value="下學期">下學期</SelectItem>
                                    <SelectItem value="暑期">暑期</SelectItem>
                                    <SelectItem value="寒假">寒假</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>開學日期</Label>
                            <Input
                                type="date"
                                value={formData.start_date}
                                onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                            />
                        </div>
                        <div>
                            <Label>結束日期</Label>
                            <Input
                                type="date"
                                value={formData.end_date}
                                onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                            />
                        </div>
                    </div>

                    <div className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            id="is_active"
                            checked={formData.is_active}
                            onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                            className="rounded"
                        />
                        <Label htmlFor="is_active">設為當前學期</Label>
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={onClose}>取消</Button>
                        <Button type="submit" className="gradient-bg text-white">
                            {semester ? '更新' : '建立'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}