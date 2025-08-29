import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import TeacherLayout from '@/components/TeacherLayout';
import StudentTable, { Student } from '@/components/StudentTable';
import { StudentDialogs } from '@/components/StudentDialogs';
import { ProgramDialog } from '@/components/ProgramDialog';
import { LessonDialog } from '@/components/LessonDialog';
import { ArrowLeft, Users, BookOpen, Plus, Settings, Edit, Clock, FileText, ListOrdered, X, Save, Mic, Trash2, GripVertical } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Content {
  id: number;
  type?: string;
  title: string;
  items_count: number;
  estimated_time?: string;
}

interface Lesson {
  id: number;
  name: string;
  description?: string;
  order_index: number;
  estimated_minutes?: number;
  program_id: number;
  contents?: Content[];
}

interface Program {
  id: number;
  name: string;
  description?: string;
  level?: string;
  estimated_hours?: number;
  created_at?: string;
  order_index?: number;
  lessons?: Lesson[];
}

interface ClassroomInfo {
  id: number;
  name: string;
  description?: string;
  level?: string;
  student_count: number;
  students: Student[];
  program_count?: number;
}

export default function ClassroomDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [classroom, setClassroom] = useState<ClassroomInfo | null>(null);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('students');
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [selectedContent, setSelectedContent] = useState<any>(null);
  
  // Student dialog states
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [dialogType, setDialogType] = useState<'view' | 'create' | 'edit' | 'delete' | null>(null);
  
  // Program dialog states
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const [programDialogType, setProgramDialogType] = useState<'create' | 'edit' | 'delete' | null>(null);
  
  // Lesson dialog states
  const [selectedLesson, setSelectedLesson] = useState<any>(null);
  const [lessonDialogType, setLessonDialogType] = useState<'create' | 'edit' | 'delete' | null>(null);
  const [lessonProgramId, setLessonProgramId] = useState<number | undefined>(undefined);
  
  // Drag states
  const [draggedProgram, setDraggedProgram] = useState<number | null>(null);
  const [draggedLesson, setDraggedLesson] = useState<{programId: number, lessonIndex: number} | null>(null);
  const [dropIndicatorProgram, setDropIndicatorProgram] = useState<number | null>(null);
  const [dropIndicatorLesson, setDropIndicatorLesson] = useState<{programId: number, lessonIndex: number} | null>(null);

  useEffect(() => {
    if (id) {
      fetchClassroomDetail();
      fetchPrograms();
    }
  }, [id]);

  const fetchClassroomDetail = async () => {
    try {
      setLoading(true);
      const classrooms = await apiClient.getTeacherClassrooms() as ClassroomInfo[];
      const currentClassroom = classrooms.find(c => c.id === Number(id));
      
      if (currentClassroom) {
        setClassroom(currentClassroom);
      } else {
        console.error('Classroom not found');
        navigate('/teacher/classrooms');
      }
    } catch (err) {
      console.error('Fetch classroom error:', err);
      navigate('/teacher/classrooms');
    } finally {
      setLoading(false);
    }
  };

  const fetchPrograms = async () => {
    try {
      const allPrograms = await apiClient.getTeacherPrograms() as any[];
      // Filter programs for this classroom
      const classroomPrograms = allPrograms.filter(p => p.classroom_id === Number(id));
      
      // Fetch detailed info including lessons for each program
      const programsWithLessons = await Promise.all(
        classroomPrograms.map(async (program) => {
          try {
            const detail = await apiClient.getProgramDetail(program.id) as any;
            return { 
              ...program, 
              lessons: detail.lessons ? detail.lessons.sort((a: Lesson, b: Lesson) => a.order_index - b.order_index) : [] 
            };
          } catch (err) {
            console.error(`Failed to fetch lessons for program ${program.id}:`, err);
            return { ...program, lessons: [] };
          }
        })
      );
      
      // Sort programs by order_index
      programsWithLessons.sort((a, b) => (a.order_index || 0) - (b.order_index || 0));
      setPrograms(programsWithLessons);
    } catch (err) {
      console.error('Fetch programs error:', err);
    }
  };


  const handleContentClick = (content: any) => {
    setSelectedContent(content);
    setIsPanelOpen(true);
  };

  const closePanel = () => {
    setIsPanelOpen(false);
    setTimeout(() => setSelectedContent(null), 300);
  };

  // Student CRUD handlers
  const handleCreateStudent = () => {
    setSelectedStudent(null);
    setDialogType('create');
  };

  const handleViewStudent = (student: Student) => {
    setSelectedStudent(student);
    setDialogType('view');
  };

  const handleEditStudent = (student: Student) => {
    setSelectedStudent(student);
    setDialogType('edit');
  };

  const handleEmailStudent = (student: Student) => {
    // TODO: Implement email functionality
    console.log('Email student:', student);
  };

  const handleResetPassword = async (student: Student) => {
    if (!confirm(`確定要將 ${student.name} 的密碼重設為預設密碼嗎？`)) {
      return;
    }
    
    try {
      await apiClient.resetStudentPassword(student.id);
      // Refresh data
      fetchClassroomDetail();
    } catch (error) {
      console.error('Failed to reset password:', error);
      alert('重設密碼失敗，請稍後再試');
    }
  };

  const handleSaveStudent = () => {
    // Refresh data after save
    fetchClassroomDetail();
  };

  const handleDeleteStudent = () => {
    // Refresh data after delete
    fetchClassroomDetail();
  };

  const handleCloseDialog = () => {
    setSelectedStudent(null);
    setDialogType(null);
  };

  const handleSwitchToEdit = () => {
    // Switch from view to edit mode
    setDialogType('edit');
  };

  const handleCreateProgram = () => {
    setSelectedProgram(null);
    setProgramDialogType('create');
  };

  const handleAddLesson = (programId: number) => {
    setSelectedLesson(null);
    setLessonProgramId(programId);
    setLessonDialogType('create');
  };

  const handleEditProgram = (programId: number) => {
    const program = programs.find(p => p.id === programId);
    if (program) {
      setSelectedProgram(program);
      setProgramDialogType('edit');
    }
  };

  const handleEditLesson = (programId: number, lessonId: number) => {
    const program = programs.find(p => p.id === programId);
    const lesson = program?.lessons?.find((l: Lesson) => l.id === lessonId);
    if (lesson) {
      setSelectedLesson(lesson);
      setLessonProgramId(programId);
      setLessonDialogType('edit');
    }
  };

  const handleDeleteProgram = (programId: number) => {
    const program = programs.find(p => p.id === programId);
    if (program) {
      setSelectedProgram(program);
      setProgramDialogType('delete');
    }
  };

  const handleDeleteLesson = (programId: number, lessonId: number) => {
    const program = programs.find(p => p.id === programId);
    const lesson = program?.lessons?.find((l: Lesson) => l.id === lessonId);
    if (lesson) {
      setSelectedLesson(lesson);
      setLessonProgramId(programId);
      setLessonDialogType('delete');
    }
  };

  const handleSaveProgram = (program: Program) => {
    if (programDialogType === 'create') {
      setPrograms([...programs, program]);
    } else if (programDialogType === 'edit') {
      setPrograms(programs.map(p => p.id === program.id ? program : p));
    }
    fetchPrograms(); // Refresh data
  };

  const handleDeleteProgramConfirm = (programId: number) => {
    setPrograms(programs.filter(p => p.id !== programId));
    fetchPrograms(); // Refresh data
  };

  const handleSaveLesson = (lesson: any) => {
    const programIndex = programs.findIndex(p => p.id === lesson.program_id);
    if (programIndex !== -1) {
      const updatedPrograms = [...programs];
      if (!updatedPrograms[programIndex].lessons) {
        updatedPrograms[programIndex].lessons = [];
      }
      
      if (lessonDialogType === 'create') {
        updatedPrograms[programIndex].lessons!.push(lesson);
      } else if (lessonDialogType === 'edit') {
        const lessonIndex = updatedPrograms[programIndex].lessons!.findIndex(l => l.id === lesson.id);
        if (lessonIndex !== -1) {
          updatedPrograms[programIndex].lessons![lessonIndex] = lesson;
        }
      }
      
      setPrograms(updatedPrograms);
    }
    // TODO: Call API to save lesson
    console.log('Lesson saved:', lesson);
  };

  const handleDeleteLessonConfirm = (lessonId: number) => {
    const updatedPrograms = programs.map(program => {
      if (program.lessons) {
        return {
          ...program,
          lessons: program.lessons.filter(l => l.id !== lessonId)
        };
      }
      return program;
    });
    setPrograms(updatedPrograms);
    // TODO: Call API to delete lesson
    console.log('Lesson deleted:', lessonId);
  };

  const handleReorderPrograms = async (dragIndex: number, dropIndex: number) => {
    const newPrograms = [...programs];
    const [draggedItem] = newPrograms.splice(dragIndex, 1);
    newPrograms.splice(dropIndex, 0, draggedItem);
    
    // Update order_index for each program
    const updatedPrograms = newPrograms.map((program, index) => ({
      ...program,
      order_index: index + 1
    }));
    
    setPrograms(updatedPrograms);
    
    // Save new order to backend
    try {
      const orderData = updatedPrograms.map((program, index) => ({
        id: program.id,
        order_index: index + 1
      }));
      await apiClient.reorderPrograms(orderData);
      console.log('Programs reordered and saved');
    } catch (error) {
      console.error('Failed to save program order:', error);
      // 可選：恢復原始順序
      fetchPrograms();
    }
  };

  const handleReorderLessons = async (programId: number, dragIndex: number, dropIndex: number) => {
    const programIndex = programs.findIndex(p => p.id === programId);
    if (programIndex !== -1 && programs[programIndex].lessons) {
      const updatedPrograms = [...programs];
      const lessons = [...updatedPrograms[programIndex].lessons!];
      
      // Reorder lessons
      const [draggedItem] = lessons.splice(dragIndex, 1);
      lessons.splice(dropIndex, 0, draggedItem);
      
      // Update order_index for each lesson
      const reorderedLessons = lessons.map((lesson, index) => ({
        ...lesson,
        order_index: index + 1
      }));
      
      updatedPrograms[programIndex].lessons = reorderedLessons;
      setPrograms(updatedPrograms);
      
      // Save new order to backend
      try {
        const orderData = reorderedLessons.map((lesson, index) => ({
          id: lesson.id,
          order_index: index + 1
        }));
        await apiClient.reorderLessons(programId, orderData);
        console.log(`Lessons reordered and saved for program ${programId}`);
      } catch (error) {
        console.error('Failed to save lesson order:', error);
        // 可選：恢復原始順序
        fetchPrograms();
      }
    }
  };

  const getLevelBadge = (level?: string) => {
    const levelColors: Record<string, string> = {
      'PREA': 'bg-gray-100 text-gray-800',
      'A1': 'bg-green-100 text-green-800',
      'A2': 'bg-blue-100 text-blue-800',
      'B1': 'bg-purple-100 text-purple-800',
      'B2': 'bg-indigo-100 text-indigo-800',
      'C1': 'bg-red-100 text-red-800',
      'C2': 'bg-orange-100 text-orange-800',
    };
    const color = levelColors[level?.toUpperCase() || 'A1'] || 'bg-gray-100 text-gray-800';
    return <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>{level || 'A1'}</span>;
  };

  if (loading) {
    return (
      <TeacherLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">載入中...</p>
          </div>
        </div>
      </TeacherLayout>
    );
  }

  if (!classroom) {
    return (
      <TeacherLayout>
        <div className="text-center py-12">
          <p className="text-gray-500">找不到班級資料</p>
          <Button 
            className="mt-4"
            onClick={() => navigate('/teacher/classrooms')}
          >
            返回班級列表
          </Button>
        </div>
      </TeacherLayout>
    );
  }

  return (
    <TeacherLayout>
      <div className="relative">
        <div className={`transition-all duration-300 ${isPanelOpen ? 'mr-[50%]' : ''}`}>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/teacher/classrooms')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回
            </Button>
            <div>
              <h2 className="text-3xl font-bold text-gray-900">{classroom.name}</h2>
              {classroom.description && (
                <p className="text-gray-600 mt-1">{classroom.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              班級設定
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">學生數</p>
                <p className="text-2xl font-bold">{classroom.student_count}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">課程數</p>
                <p className="text-2xl font-bold">{programs.length}</p>
              </div>
              <BookOpen className="h-8 w-8 text-green-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">等級</p>
                <p className="text-2xl font-bold">{classroom.level || 'A1'}</p>
              </div>
              <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-purple-600 font-bold">L</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm border">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <div className="border-b bg-gray-50 px-6 py-3">
              <TabsList className="grid w-full max-w-[500px] grid-cols-2 h-12 bg-white border">
                <TabsTrigger 
                  value="students" 
                  className="data-[state=active]:bg-blue-500 data-[state=active]:text-white text-base font-medium"
                >
                  <Users className="h-5 w-5 mr-2" />
                  學生列表
                </TabsTrigger>
                <TabsTrigger 
                  value="programs"
                  className="data-[state=active]:bg-blue-500 data-[state=active]:text-white text-base font-medium"
                >
                  <BookOpen className="h-5 w-5 mr-2" />
                  課程列表
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Students Tab */}
            <TabsContent value="students" className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">班級學生</h3>
                <Button size="sm" onClick={handleCreateStudent}>
                  <Plus className="h-4 w-4 mr-2" />
                  新增學生
                </Button>
              </div>
              
              <StudentTable
                students={classroom.students}
                showClassroom={false}
                onAddStudent={handleCreateStudent}
                onViewStudent={handleViewStudent}
                onEditStudent={handleEditStudent}
                onEmailStudent={handleEmailStudent}
                onResetPassword={handleResetPassword}
                emptyMessage="此班級尚無學生"
              />
            </TabsContent>

            {/* Programs Tab */}
            <TabsContent value="programs" className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">班級課程</h3>
                <Button size="sm" onClick={handleCreateProgram}>
                  <Plus className="h-4 w-4 mr-2" />
                  建立課程
                </Button>
              </div>
              
              {programs.length > 0 ? (
                <Accordion type="single" collapsible className="w-full">
                  {programs.map((program, programIndex) => (
                    <div key={program.id} className="relative">
                      {/* 插入指示器 - 顯示在項目上方 */}
                      {dropIndicatorProgram === programIndex && (
                        <div className="h-1 bg-blue-500 rounded-full mx-2 my-1 animate-pulse" />
                      )}
                      <AccordionItem 
                        value={`program-${program.id}`}
                        className={`
                          transition-opacity duration-200
                          ${draggedProgram === programIndex ? 'opacity-30' : ''}
                        `}
                        onDragOver={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          if (draggedProgram === null) return;
                          
                          const rect = e.currentTarget.getBoundingClientRect();
                          const y = e.clientY - rect.top;
                          const height = rect.height;
                          
                          // 判斷是在上半部還是下半部
                          if (y < height / 2) {
                            // 在上半部，顯示在當前項目上方
                            setDropIndicatorProgram(programIndex);
                          } else {
                            // 在下半部，顯示在下一個項目上方
                            setDropIndicatorProgram(programIndex + 1);
                          }
                        }}
                        onDragLeave={(e) => {
                          e.preventDefault();
                          // 只有當離開整個項目時才清除指示器
                          if (!e.currentTarget.contains(e.relatedTarget as Node)) {
                            setDropIndicatorProgram(null);
                          }
                        }}
                        onDrop={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          if (draggedProgram !== null && dropIndicatorProgram !== null) {
                            let targetIndex = dropIndicatorProgram;
                            // 如果拖曳的項目原本在目標位置之前，需要調整目標索引
                            if (draggedProgram < targetIndex) {
                              targetIndex--;
                            }
                            if (draggedProgram !== targetIndex) {
                              handleReorderPrograms(draggedProgram, targetIndex);
                            }
                          }
                          setDraggedProgram(null);
                          setDropIndicatorProgram(null);
                        }}>
                      <AccordionTrigger className="hover:no-underline group">
                        <div className="flex items-center justify-between w-full pr-4">
                          <div className="flex items-center space-x-3">
                            <div 
                              className="cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity select-none"
                              title="拖曳以重新排序"
                              draggable
                              onDragStart={(e) => {
                                e.stopPropagation();
                                e.dataTransfer.effectAllowed = 'move';
                                // 創建自定義拖曳預覽
                                const preview = document.createElement('div');
                                preview.style.position = 'absolute';
                                preview.style.top = '-1000px';
                                preview.style.backgroundColor = '#3B82F6';
                                preview.style.color = 'white';
                                preview.style.padding = '4px 8px';
                                preview.style.borderRadius = '4px';
                                preview.style.fontSize = '12px';
                                preview.textContent = `移動: ${program.name}`;
                                document.body.appendChild(preview);
                                e.dataTransfer.setDragImage(preview, 0, 0);
                                setTimeout(() => document.body.removeChild(preview), 0);
                                setDraggedProgram(programIndex);
                              }}
                              onDragEnd={(e) => {
                                e.stopPropagation();
                                setDraggedProgram(null);
                                setDropIndicatorProgram(null);
                              }}
                            >
                              <GripVertical className="h-5 w-5 text-gray-400" />
                            </div>
                            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                              <BookOpen className="h-5 w-5 text-blue-600" />
                            </div>
                            <div className="text-left">
                              <div className="flex items-center space-x-2">
                                <h4 className="font-semibold">{program.name}</h4>
                                <Button 
                                  size="sm" 
                                  variant="ghost" 
                                  className="h-6 w-6 p-0"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleEditProgram(program.id);
                                  }}
                                >
                                  <Edit className="h-3 w-3" />
                                </Button>
                              </div>
                              <p className="text-sm text-gray-500">{program.description || '暫無描述'}</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-4">
                            {getLevelBadge(program.level)}
                            {program.estimated_hours && (
                              <div className="flex items-center text-sm text-gray-500">
                                <Clock className="h-4 w-4 mr-1" />
                                <span>{program.estimated_hours} 小時</span>
                              </div>
                            )}
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              className="h-8 w-8 p-0"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteProgram(program.id);
                              }}
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="pl-14 pr-4">
                          <Accordion type="single" collapsible className="w-full">
                            {(program.lessons || []).map((lesson, lessonIndex) => (
                              <div key={lesson.id} className="relative">
                                {/* 插入指示器 - 顯示在單元上方 */}
                                {dropIndicatorLesson && 
                                 dropIndicatorLesson.programId === program.id && 
                                 dropIndicatorLesson.lessonIndex === lessonIndex && (
                                  <div className="h-0.5 bg-green-500 rounded-full mx-2 my-0.5 animate-pulse" />
                                )}
                                <AccordionItem 
                                  value={`lesson-${program.id}-${lesson.id}`} 
                                  className={`
                                    border-l-2 border-gray-200 ml-2 transition-opacity duration-200
                                    ${draggedLesson && draggedLesson.programId === program.id && draggedLesson.lessonIndex === lessonIndex ? 'opacity-30' : ''}
                                  `}
                                  onDragOver={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    if (!draggedLesson || draggedLesson.programId !== program.id) return;
                                    
                                    const rect = e.currentTarget.getBoundingClientRect();
                                    const y = e.clientY - rect.top;
                                    const height = rect.height;
                                    
                                    // 判斷是在上半部還是下半部
                                    if (y < height / 2) {
                                      setDropIndicatorLesson({ programId: program.id, lessonIndex });
                                    } else {
                                      setDropIndicatorLesson({ programId: program.id, lessonIndex: lessonIndex + 1 });
                                    }
                                  }}
                                  onDragLeave={(e) => {
                                    e.preventDefault();
                                    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
                                      setDropIndicatorLesson(null);
                                    }
                                  }}
                                  onDrop={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    if (draggedLesson && dropIndicatorLesson && 
                                        draggedLesson.programId === program.id &&
                                        dropIndicatorLesson.programId === program.id) {
                                      let targetIndex = dropIndicatorLesson.lessonIndex;
                                      if (draggedLesson.lessonIndex < targetIndex) {
                                        targetIndex--;
                                      }
                                      if (draggedLesson.lessonIndex !== targetIndex) {
                                        handleReorderLessons(program.id, draggedLesson.lessonIndex, targetIndex);
                                      }
                                    }
                                    setDraggedLesson(null);
                                    setDropIndicatorLesson(null);
                                  }}>
                                <AccordionTrigger className="hover:no-underline pl-4 group">
                                  <div className="flex items-center justify-between w-full pr-4">
                                    <div className="flex items-center space-x-3">
                                      <div 
                                        className="cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity select-none"
                                        title="拖曳以重新排序"
                                        draggable
                                        onDragStart={(e) => {
                                          e.stopPropagation();
                                          e.dataTransfer.effectAllowed = 'move';
                                          // 創建自定義拖曳預覽
                                          const preview = document.createElement('div');
                                          preview.style.position = 'absolute';
                                          preview.style.top = '-1000px';
                                          preview.style.backgroundColor = '#3B82F6';
                                          preview.style.color = 'white';
                                          preview.style.padding = '4px 8px';
                                          preview.style.borderRadius = '4px';
                                          preview.style.fontSize = '12px';
                                          preview.textContent = `移動: ${lesson.name}`;
                                          document.body.appendChild(preview);
                                          e.dataTransfer.setDragImage(preview, 0, 0);
                                          setTimeout(() => document.body.removeChild(preview), 0);
                                          setDraggedLesson({ programId: program.id, lessonIndex });
                                        }}
                                        onDragEnd={(e) => {
                                          e.stopPropagation();
                                          setDraggedLesson(null);
                                          setDropIndicatorLesson(null);
                                        }}
                                      >
                                        <GripVertical className="h-4 w-4 text-gray-400" />
                                      </div>
                                      <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                                        <ListOrdered className="h-4 w-4 text-green-600" />
                                      </div>
                                      <div className="text-left">
                                        <div className="flex items-center space-x-2">
                                          <h5 className="font-medium">{lesson.name}</h5>
                                          <Button 
                                            size="sm" 
                                            variant="ghost" 
                                            className="h-5 w-5 p-0"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleEditLesson(program.id, lesson.id);
                                            }}
                                          >
                                            <Edit className="h-3 w-3" />
                                          </Button>
                                        </div>
                                        <p className="text-sm text-gray-500">{lesson.description || '暫無描述'}</p>
                                      </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                      <span className="text-sm text-gray-500">{lesson.estimated_minutes || 30} 分鐘</span>
                                      <Button 
                                        size="sm" 
                                        variant="ghost" 
                                        className="h-6 w-6 p-0"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleDeleteLesson(program.id, lesson.id);
                                        }}
                                      >
                                        <Trash2 className="h-3 w-3 text-red-500" />
                                      </Button>
                                    </div>
                                  </div>
                                </AccordionTrigger>
                                <AccordionContent>
                                  <div className="pl-12 pr-4 space-y-3">
                                    {/* 實際 Content 資料 */}
                                    {(lesson.contents && lesson.contents.length > 0) ? (
                                      lesson.contents.map((content: any) => (
                                      <div 
                                        key={content.id} 
                                        className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 cursor-pointer transition-colors duration-200 group"
                                        onClick={() => handleContentClick({
                                          ...content,
                                          lessonName: lesson.name,
                                          programName: program.name
                                        })}>
                                        <div className="flex items-center space-x-3">
                                          <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                                            <FileText className="h-4 w-4 text-purple-600" />
                                          </div>
                                          <div>
                                            <p className="font-medium text-sm">{content.title || '未命名內容'}</p>
                                            <p className="text-xs text-gray-500">{content.items_count || 0} 個項目</p>
                                          </div>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                          <span className="text-sm text-gray-500">{content.estimated_time || '10 分鐘'}</span>
                                          <span className="text-xs text-gray-400 group-hover:text-gray-600">
                                            點擊編輯 →
                                          </span>
                                        </div>
                                      </div>
                                    ))
                                    ) : (
                                      <div className="p-4 text-center text-gray-500 text-sm">
                                        尚無內容，請新增內容
                                      </div>
                                    )}
                                    
                                    <div className="flex justify-end space-x-2 pt-2">
                                      <Button size="sm" variant="outline">
                                        <Edit className="h-4 w-4 mr-2" />
                                        編輯課程
                                      </Button>
                                      <Button size="sm" variant="outline">
                                        <Plus className="h-4 w-4 mr-2" />
                                        新增內容
                                      </Button>
                                    </div>
                                  </div>
                                </AccordionContent>
                              </AccordionItem>
                              </div>
                            ))}
                            {/* 最後位置的插入指示器（單元） */}
                            {dropIndicatorLesson && 
                             dropIndicatorLesson.programId === program.id && 
                             dropIndicatorLesson.lessonIndex === (program.lessons?.length || 0) && (
                              <div className="h-0.5 bg-green-500 rounded-full mx-2 my-0.5 animate-pulse" />
                            )}
                            
                            {/* Add Lesson Button */}
                            <div className="pl-6 pt-2">
                              <Button size="sm" variant="outline" className="w-full" onClick={() => handleAddLesson(program.id)}>
                                <Plus className="h-4 w-4 mr-2" />
                                新增單元
                              </Button>
                            </div>
                          </Accordion>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                    </div>
                  ))}
                  {/* 最後位置的插入指示器 */}
                  {dropIndicatorProgram === programs.length && (
                    <div className="h-1 bg-blue-500 rounded-full mx-2 my-1 animate-pulse" />
                  )}
                </Accordion>
              ) : (
                <div className="text-center py-12">
                  <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">尚未建立課程</p>
                  <p className="text-sm text-gray-400 mt-2">為班級建立課程內容，開始教學</p>
                  <Button className="mt-4" size="sm" onClick={handleCreateProgram}>
                    <Plus className="h-4 w-4 mr-2" />
                    建立第一個課程
                  </Button>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
        </div>

        {/* Right Sliding Panel */}
        <div className={`fixed right-0 top-0 h-full w-1/2 bg-white shadow-xl border-l transform transition-transform duration-300 z-50 ${
          isPanelOpen ? 'translate-x-0' : 'translate-x-full'
        }`}>
          {selectedContent && (
            <div className="h-full flex flex-col">
              {/* Panel Header */}
              <div className="flex items-center justify-between p-4 border-b bg-gray-50">
                <div>
                  <h3 className="font-semibold text-lg">內容編輯器</h3>
                  <p className="text-sm text-gray-500 mt-1">{selectedContent.type}</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={closePanel}
                  className="hover:bg-gray-200"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>

              {/* Panel Content */}
              <div className="flex-1 overflow-y-auto p-4">
                <div className="space-y-4">
                  {/* Content Info */}
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <p className="text-sm font-medium text-blue-900">{selectedContent.programName}</p>
                    <p className="text-xs text-blue-700 mt-1">{selectedContent.lessonName}</p>
                  </div>

                  {/* Content Type Badge */}
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                      <FileText className="h-4 w-4 text-purple-600" />
                    </div>
                    <div>
                      <p className="font-medium">{selectedContent.type}</p>
                      <p className="text-sm text-gray-500">{selectedContent.items} 個項目 • {selectedContent.time}</p>
                    </div>
                  </div>

                  {/* Content Items - 真實內容編輯介面 */}
                  <div className="space-y-3">
                    <h4 className="font-medium text-sm">內容項目</h4>
                    {[1, 2, 3].map((item) => (
                      <div key={item} className="border rounded-lg p-3 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">項目 {item}</span>
                          <Button size="sm" variant="ghost">
                            <Edit className="h-3 w-3" />
                          </Button>
                        </div>
                        <input
                          type="text"
                          className="w-full px-3 py-2 border rounded-md text-sm"
                          placeholder="英文內容"
                          defaultValue={`Hello, how are you? (Example ${item})`}
                        />
                        <input
                          type="text"
                          className="w-full px-3 py-2 border rounded-md text-sm"
                          placeholder="中文翻譯"
                          defaultValue={`你好，你好嗎？（範例 ${item}）`}
                        />
                        <div className="flex items-center space-x-2">
                          <Button size="sm" variant="outline" className="flex-1">
                            <Mic className="h-4 w-4 mr-1" />
                            錄音
                          </Button>
                          <Button size="sm" variant="outline" className="text-red-600">
                            刪除
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Add Item Button */}
                  <Button variant="outline" className="w-full">
                    <Plus className="h-4 w-4 mr-2" />
                    新增項目
                  </Button>

                  {/* Settings */}
                  <div className="space-y-3 pt-4 border-t">
                    <h4 className="font-medium text-sm">設定</h4>
                    <div>
                      <label className="text-sm text-gray-600">目標 WPM (每分鐘字數)</label>
                      <input
                        type="number"
                        className="w-full px-3 py-2 border rounded-md mt-1"
                        placeholder="120"
                        defaultValue="120"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">目標準確率 (%)</label>
                      <input
                        type="number"
                        className="w-full px-3 py-2 border rounded-md mt-1"
                        placeholder="80"
                        defaultValue="80"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">時間限制 (秒)</label>
                      <input
                        type="number"
                        className="w-full px-3 py-2 border rounded-md mt-1"
                        placeholder="600"
                        defaultValue="600"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Panel Footer */}
              <div className="p-4 border-t bg-gray-50">
                <div className="flex space-x-2">
                  <Button variant="outline" className="flex-1" onClick={closePanel}>
                    取消
                  </Button>
                  <Button className="flex-1">
                    <Save className="h-4 w-4 mr-2" />
                    儲存變更
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Student Dialogs */}
      <StudentDialogs
        student={selectedStudent}
        dialogType={dialogType}
        onClose={handleCloseDialog}
        onSave={handleSaveStudent}
        onDelete={handleDeleteStudent}
        onSwitchToEdit={handleSwitchToEdit}
        classrooms={classroom ? [classroom] : []}
      />
      
      {/* Program Dialog */}
      <ProgramDialog
        program={selectedProgram}
        dialogType={programDialogType}
        classroomId={Number(id)}
        onClose={() => {
          setSelectedProgram(null);
          setProgramDialogType(null);
        }}
        onSave={handleSaveProgram}
        onDelete={handleDeleteProgramConfirm}
      />
      
      {/* Lesson Dialog */}
      <LessonDialog
        lesson={selectedLesson}
        dialogType={lessonDialogType}
        programId={lessonProgramId}
        onClose={() => {
          setSelectedLesson(null);
          setLessonDialogType(null);
          setLessonProgramId(undefined);
        }}
        onSave={handleSaveLesson}
        onDelete={handleDeleteLessonConfirm}
      />
    </TeacherLayout>
  );
}