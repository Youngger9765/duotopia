import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { format } from 'date-fns';
import { zhTW } from 'date-fns/locale';
import {
  Users,
  ChevronRight,
  ChevronDown,
  BookOpen,
  FileText,
  CheckCircle2,
  Circle,
  Package,
  Layers,
  ChevronLeft,
  ArrowRight,
  Check,
  Calendar as CalendarIconAlt,
  Clock,
  MessageSquare
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

interface Student {
  id: number;
  name: string;
  email: string;
}

interface Content {
  id: number;
  title: string;
  type: string;
  lesson_id: number;
  items_count?: number;
  level?: string;
}

interface Lesson {
  id: number;
  name: string;
  description?: string;
  order_index: number;
  contents?: Content[];
}

interface Program {
  id: number;
  name: string;
  description?: string;
  level?: string;
  lessons?: Lesson[];
}

interface AssignmentDialogProps {
  open: boolean;
  onClose: () => void;
  classroomId: number;
  students: Student[];
  onSuccess?: () => void;
}

// Content type labels in Chinese
const contentTypeLabels: Record<string, string> = {
  reading_assessment: '朗讀評測',
  READING_ASSESSMENT: '朗讀評測',
  speaking_practice: '口說練習',
  speaking_scenario: '情境對話',
  listening_cloze: '聽力填空',
  sentence_making: '造句練習',
  speaking_quiz: '口說測驗',
};

export function AssignmentDialog({
  open,
  onClose,
  classroomId,
  students,
  onSuccess
}: AssignmentDialogProps) {
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [expandedPrograms, setExpandedPrograms] = useState<Set<number>>(new Set());
  const [expandedLessons, setExpandedLessons] = useState<Set<number>>(new Set());
  const [selectedContents, setSelectedContents] = useState<Set<number>>(new Set());

  const [formData, setFormData] = useState({
    title: '',
    instructions: '',
    student_ids: [] as number[],
    assign_to_all: true,
    due_date: undefined as Date | undefined,
  });

  useEffect(() => {
    if (open) {
      loadPrograms();
      // Reset form when dialog opens
      setSelectedContents(new Set());
      setFormData({
        title: '',
        instructions: '',
        student_ids: students.map(s => s.id), // 預設全選所有學生
        assign_to_all: true,
        due_date: undefined,
      });
      setCurrentStep(1);
    }
  }, [open, classroomId, students]);

  const loadPrograms = async () => {
    try {
      // Load programs with their lessons and contents
      const response = await apiClient.get<Program[]>(`/api/teachers/programs`);

      // Load details for each program to get lessons and contents
      const programsWithDetails = await Promise.all(
        response.map(async (program) => {
          try {
            const detail = await apiClient.get<Program>(`/api/teachers/programs/${program.id}`);

            // For each lesson, try to load its contents
            if (detail.lessons) {
              const lessonsWithContents = await Promise.all(
                detail.lessons.map(async (lesson) => {
                  try {
                    const contents = await apiClient.get<Content[]>(`/api/teachers/lessons/${lesson.id}/contents`);
                    return { ...lesson, contents };
                  } catch {
                    return { ...lesson, contents: [] };
                  }
                })
              );
              return { ...detail, lessons: lessonsWithContents };
            }

            return detail;
          } catch {
            return { ...program, lessons: [] };
          }
        })
      );

      setPrograms(programsWithDetails);
    } catch (error) {
      console.error('Failed to load programs:', error);
      toast.error('無法載入課程資料');
      setPrograms([]);
    }
  };

  const toggleProgram = (programId: number) => {
    setExpandedPrograms(prev => {
      const newSet = new Set(prev);
      if (newSet.has(programId)) {
        newSet.delete(programId);
      } else {
        newSet.add(programId);
      }
      return newSet;
    });
  };

  const toggleLesson = (lessonId: number) => {
    setExpandedLessons(prev => {
      const newSet = new Set(prev);
      if (newSet.has(lessonId)) {
        newSet.delete(lessonId);
      } else {
        newSet.add(lessonId);
      }
      return newSet;
    });
  };

  const toggleContent = (contentId: number) => {
    setSelectedContents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(contentId)) {
        newSet.delete(contentId);
      } else {
        newSet.add(contentId);
      }
      return newSet;
    });
  };

  const toggleAllInLesson = (lesson: Lesson) => {
    if (!lesson.contents) return;

    const lessonContentIds = lesson.contents.map(c => c.id);
    const allSelected = lessonContentIds.every(id => selectedContents.has(id));

    setSelectedContents(prev => {
      const newSet = new Set(prev);
      if (allSelected) {
        lessonContentIds.forEach(id => newSet.delete(id));
      } else {
        lessonContentIds.forEach(id => newSet.add(id));
      }
      return newSet;
    });
  };

  const toggleStudent = (studentId: number) => {
    setFormData(prev => {
      const newIds = prev.student_ids.includes(studentId)
        ? prev.student_ids.filter(id => id !== studentId)
        : [...prev.student_ids, studentId];

      return {
        ...prev,
        student_ids: newIds,
        assign_to_all: newIds.length === students.length
      };
    });
  };

  const toggleAllStudents = () => {
    setFormData(prev => ({
      ...prev,
      assign_to_all: !prev.assign_to_all,
      student_ids: !prev.assign_to_all ? students.map(s => s.id) : []
    }));
  };

  const handleSubmit = async () => {
    // Validation
    if (selectedContents.size === 0) {
      toast.error('請至少選擇一個課程內容');
      return;
    }
    if (!formData.title.trim()) {
      toast.error('請輸入作業標題');
      return;
    }
    if (formData.student_ids.length === 0) {
      toast.error('請至少選擇一位學生');
      return;
    }

    setLoading(true);
    try {
      // Create assignments for each selected content
      const promises = Array.from(selectedContents).map(contentId => {
        const payload = {
          content_id: contentId,
          classroom_id: classroomId,
          title: formData.title,
          instructions: formData.instructions || undefined,
          student_ids: formData.assign_to_all ? [] : formData.student_ids,
          due_date: formData.due_date ? formData.due_date.toISOString() : undefined,
        };
        return apiClient.post('/api/assignments/create', payload);
      });

      const results = await Promise.all(promises);
      const totalCreated = results.reduce((sum, r: any) => sum + (r.count || 0), 0);

      toast.success(`成功創建 ${totalCreated} 份作業`);
      onSuccess?.();
      handleClose();
    } catch (error) {
      console.error('Failed to create assignments:', error);
      toast.error('創建作業失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      title: '',
      instructions: '',
      student_ids: [],
      assign_to_all: true,
      due_date: undefined,
    });
    setSelectedContents(new Set());
    setExpandedPrograms(new Set());
    setExpandedLessons(new Set());
    setCurrentStep(1);
    onClose();
  };

  // Get selected content details for summary
  const getSelectedContentsSummary = () => {
    const summary: { program: string; lesson: string; content: string; type: string }[] = [];

    programs.forEach(program => {
      program.lessons?.forEach(lesson => {
        lesson.contents?.forEach(content => {
          if (selectedContents.has(content.id)) {
            summary.push({
              program: program.name,
              lesson: lesson.name,
              content: content.title,
              type: content.type
            });
          }
        });
      });
    });

    return summary;
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return selectedContents.size > 0;
      case 2:
        return formData.student_ids.length > 0;
      case 3:
        return formData.title.trim().length > 0;
      default:
        return false;
    }
  };

  const steps = [
    { number: 1, title: '選擇內容', icon: BookOpen },
    { number: 2, title: '選擇學生', icon: Users },
    { number: 3, title: '作業詳情', icon: FileText },
  ];

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-5xl h-[92vh] flex flex-col p-0">
        {/* Compact Header with Clear Steps */}
        <div className="px-6 py-3 border-b bg-gray-50">
          <div className="flex items-center">
            <DialogTitle className="text-lg font-semibold">指派新作業</DialogTitle>

            {/* Centered Step Indicator with Icons */}
            <div className="flex-1 flex items-center justify-center">
              <div className="flex items-center gap-4">
                {steps.map((s, index) => {
                  const Icon = s.icon;
                  const isActive = s.number === currentStep;
                  const isCompleted = s.number < currentStep;

                  return (
                    <React.Fragment key={s.number}>
                      <div className="flex items-center gap-2">
                        <div className={cn(
                          "w-7 h-7 rounded-full flex items-center justify-center font-medium transition-all",
                          isActive && "bg-blue-600 text-white shadow-sm",
                          isCompleted && "bg-green-500 text-white",
                          !isActive && !isCompleted && "bg-gray-200 text-gray-500"
                        )}>
                          {isCompleted ? (
                            <CheckCircle2 className="h-4 w-4" />
                          ) : (
                            <span className="text-sm">{s.number}</span>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <Icon className={cn(
                            "h-4 w-4",
                            isActive && "text-blue-600",
                            isCompleted && "text-green-600",
                            !isActive && !isCompleted && "text-gray-400"
                          )} />
                          <span className={cn(
                            "text-sm",
                            isActive && "text-gray-900 font-semibold",
                            isCompleted && "text-green-700 font-medium",
                            !isActive && !isCompleted && "text-gray-500"
                          )}>
                            {s.title}
                          </span>
                        </div>
                      </div>
                      {index < steps.length - 1 && (
                        <ChevronRight className="h-4 w-4 text-gray-300" />
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Content Area - Maximized Height */}
        <div className="flex-1 overflow-hidden px-6 py-3">
          {/* Step 1: Select Contents */}
          {currentStep === 1 && (
            <div className="h-full flex flex-col">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  選擇要指派的課程內容（可多選）
                </p>
                {selectedContents.size > 0 && (
                  <Badge variant="secondary" className="bg-blue-50 text-blue-700">
                    已選擇 {selectedContents.size} 個
                  </Badge>
                )}
              </div>

              <ScrollArea className="flex-1 border rounded-lg p-3">
                <div className="space-y-2">
                  {programs.map(program => (
                    <Card key={program.id} className="overflow-hidden">
                      <button
                        onClick={() => toggleProgram(program.id)}
                        className="w-full p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          {expandedPrograms.has(program.id) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                          <Package className="h-4 w-4 text-blue-600" />
                          <span className="font-medium">{program.name}</span>
                          {program.level && (
                            <Badge variant="outline" className="ml-2">
                              {program.level}
                            </Badge>
                          )}
                        </div>
                        <span className="text-sm text-gray-500">
                          {program.lessons?.length || 0} 個單元
                        </span>
                      </button>

                      {expandedPrograms.has(program.id) && program.lessons && (
                        <div className="border-t bg-gray-50">
                          {program.lessons.map(lesson => (
                            <div key={lesson.id} className="ml-6">
                              <button
                                onClick={() => toggleLesson(lesson.id)}
                                className="w-full p-2 flex items-center justify-between hover:bg-gray-100 transition-colors"
                              >
                                <div className="flex items-center gap-2">
                                  {expandedLessons.has(lesson.id) ? (
                                    <ChevronDown className="h-4 w-4" />
                                  ) : (
                                    <ChevronRight className="h-4 w-4" />
                                  )}
                                  <Layers className="h-4 w-4 text-green-600" />
                                  <span className="text-sm">{lesson.name}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-xs text-gray-500">
                                    {lesson.contents?.length || 0} 個內容
                                  </span>
                                  {lesson.contents && lesson.contents.length > 0 && (
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-6 px-2 text-xs"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleAllInLesson(lesson);
                                      }}
                                    >
                                      {lesson.contents.every(c => selectedContents.has(c.id))
                                        ? '取消全選'
                                        : '全選'}
                                    </Button>
                                  )}
                                </div>
                              </button>

                              {expandedLessons.has(lesson.id) && lesson.contents && (
                                <div className="ml-6 space-y-1 pb-2 bg-white">
                                  {lesson.contents.map(content => (
                                    <button
                                      key={content.id}
                                      onClick={() => toggleContent(content.id)}
                                      className={cn(
                                        "w-full p-2 flex items-center gap-2 hover:bg-gray-50 rounded transition-colors text-left",
                                        selectedContents.has(content.id) && "bg-blue-50 hover:bg-blue-100"
                                      )}
                                    >
                                      {selectedContents.has(content.id) ? (
                                        <CheckCircle2 className="h-4 w-4 text-blue-600 flex-shrink-0" />
                                      ) : (
                                        <Circle className="h-4 w-4 text-gray-400 flex-shrink-0" />
                                      )}
                                      <div className="flex-1">
                                        <div className="text-sm font-medium">{content.title}</div>
                                        <div className="flex items-center gap-2 text-xs text-gray-500">
                                          <Badge variant="outline" className="px-1 py-0">
                                            {contentTypeLabels[content.type] || content.type}
                                          </Badge>
                                          {content.items_count && (
                                            <span>{content.items_count} 題</span>
                                          )}
                                        </div>
                                      </div>
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </ScrollArea>

              {/* Compact Selected Contents Summary */}
              {selectedContents.size > 0 && (
                <div className="mt-2 p-2 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex flex-wrap gap-1">
                    {getSelectedContentsSummary().slice(0, 8).map((item, idx) => (
                      <Badge key={idx} variant="secondary" className="bg-white text-xs py-0 h-5">
                        {item.content}
                      </Badge>
                    ))}
                    {selectedContents.size > 8 && (
                      <Badge variant="secondary" className="bg-white text-xs py-0 h-5">
                        +{selectedContents.size - 8}
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Select Students */}
          {currentStep === 2 && (
            <div className="h-full flex flex-col">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  選擇要接收作業的學生
                </p>
                <Badge variant="secondary" className="bg-blue-50 text-blue-700">
                  {formData.student_ids.length}/{students.length} 已選
                </Badge>
              </div>

              {/* Quick Select All */}
              <Card className="p-2 mb-2 bg-blue-50 border-blue-200">
                <button
                  onClick={toggleAllStudents}
                  className="flex items-center gap-3 w-full"
                >
                  <Checkbox
                    checked={formData.assign_to_all}
                    className="data-[state=checked]:bg-blue-600 h-5 w-5"
                  />
                  <div className="flex-1 text-left">
                    <p className="text-sm font-semibold text-blue-900">指派給全班所有學生</p>
                    <p className="text-xs text-blue-700">共 {students.length} 位學生</p>
                  </div>
                  {formData.assign_to_all && (
                    <Badge className="bg-blue-600 text-white">全選</Badge>
                  )}
                </button>
              </Card>

              {/* Student Grid - Maximum use of space */}
              <div className="flex-1 border rounded-lg bg-gray-50 p-2 overflow-hidden">
                <ScrollArea className="h-full">
                  <div className="grid grid-cols-3 gap-1.5 p-1">
                    {students.map(student => (
                      <button
                        key={student.id}
                        onClick={() => toggleStudent(student.id)}
                        className={cn(
                          "p-2 rounded-md border transition-all text-left relative",
                          formData.student_ids.includes(student.id)
                            ? "bg-blue-50 border-blue-300 shadow-sm"
                            : "bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm"
                        )}
                      >
                        <div className="flex items-start gap-2">
                          <Checkbox
                            checked={formData.student_ids.includes(student.id)}
                            className="data-[state=checked]:bg-blue-600 mt-0.5 h-4 w-4"
                          />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-xs truncate">{student.name}</p>
                            <p className="text-[10px] text-gray-500 truncate">{student.email}</p>
                          </div>
                        </div>
                        {formData.student_ids.includes(student.id) && (
                          <div className="absolute top-1 right-1">
                            <CheckCircle2 className="h-3 w-3 text-blue-600" />
                          </div>
                        )}
                      </button>
                    ))}
                  </div>

                </ScrollArea>
              </div>

              {/* Action Buttons for quick selection */}
              <div className="flex gap-2 mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFormData(prev => ({
                    ...prev,
                    student_ids: students.map(s => s.id),
                    assign_to_all: true
                  }))}
                  className="flex-1"
                >
                  <CheckCircle2 className="h-4 w-4 mr-1" />
                  全選
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFormData(prev => ({
                    ...prev,
                    student_ids: [],
                    assign_to_all: false
                  }))}
                  className="flex-1"
                >
                  <Circle className="h-4 w-4 mr-1" />
                  取消全選
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const currentIds = formData.student_ids;
                    const allIds = students.map(s => s.id);
                    const newIds = allIds.filter(id => !currentIds.includes(id));
                    setFormData(prev => ({
                      ...prev,
                      student_ids: newIds,
                      assign_to_all: false
                    }));
                  }}
                  className="flex-1"
                >
                  <ArrowRight className="h-4 w-4 mr-1" />
                  反選
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Assignment Details */}
          {currentStep === 3 && (
            <div className="h-full flex flex-col">
              <div className="mb-2">
                <p className="text-sm text-gray-600">
                  填寫作業標題和詳細資訊
                </p>
              </div>

              <ScrollArea className="flex-1">
                <div className="space-y-4 pr-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="title" className="flex items-center gap-1 text-sm">
                      <FileText className="h-3.5 w-3.5" />
                      作業標題 *
                    </Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="例：Unit 1-3 綜合練習"
                  />
                </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="instructions" className="flex items-center gap-1 text-sm">
                      <MessageSquare className="h-3.5 w-3.5" />
                      作業說明
                    </Label>
                  <Textarea
                    id="instructions"
                    value={formData.instructions}
                    onChange={(e) => setFormData(prev => ({ ...prev, instructions: e.target.value }))}
                    placeholder="請提供作業相關說明或要求..."
                    rows={2}
                  />
                </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label className="flex items-center gap-1 text-sm">
                        <CalendarIconAlt className="h-3.5 w-3.5" />
                        開始日期
                      </Label>
                      <Input
                        type="date"
                        defaultValue={new Date().toISOString().split('T')[0]}
                        className="text-sm"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="flex items-center gap-1 text-sm">
                        <Clock className="h-3.5 w-3.5" />
                        截止日期
                      </Label>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            variant="outline"
                            className={cn(
                              "w-full justify-start text-left font-normal text-sm h-9",
                              !formData.due_date && "text-muted-foreground"
                            )}
                          >
                            {formData.due_date ? (
                              format(formData.due_date, 'yyyy/MM/dd')
                            ) : (
                              <span>選擇日期</span>
                            )}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0">
                          <Calendar
                            mode="single"
                            selected={formData.due_date}
                            onSelect={(date) => setFormData(prev => ({ ...prev, due_date: date }))}
                            initialFocus
                          />
                        </PopoverContent>
                      </Popover>
                    </div>
                  </div>

                  {/* Assignment Summary */}
                  <Card className="p-3 bg-blue-50 border-blue-200">
                    <h4 className="text-xs font-medium mb-2 text-blue-900">作業摘要</h4>
                    <div className="space-y-1 text-xs">
                      <div className="flex items-center gap-2">
                        <BookOpen className="h-3 w-3 text-blue-600" />
                        <span className="text-gray-700">課程內容：</span>
                        <span className="font-medium text-blue-900">{selectedContents.size} 個</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Users className="h-3 w-3 text-blue-600" />
                        <span className="text-gray-700">指派對象：</span>
                        <span className="font-medium text-blue-900">
                          {formData.assign_to_all ? '全班學生' : `${formData.student_ids.length} 位學生`}
                        </span>
                      </div>
                      {formData.due_date && (
                        <div className="flex items-center gap-2">
                          <Clock className="h-3 w-3 text-blue-600" />
                          <span className="text-gray-700">截止日期：</span>
                          <span className="font-medium text-blue-900">
                            {format(formData.due_date, 'yyyy年MM月dd日', { locale: zhTW })}
                          </span>
                        </div>
                      )}
                    </div>
                  </Card>
                </div>
              </ScrollArea>
            </div>
          )}
        </div>

        {/* Footer with Navigation */}
        <DialogFooter className="px-6 py-3 border-t">
          <div className="flex items-center justify-between w-full">
            <Button
              variant="outline"
              onClick={currentStep === 1 ? handleClose : () => setCurrentStep(currentStep - 1)}
              disabled={loading}
            >
              {currentStep === 1 ? (
                <>取消</>
              ) : (
                <>
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  上一步
                </>
              )}
            </Button>

            <div className="flex items-center gap-2">
              {currentStep < 3 ? (
                <Button
                  onClick={() => setCurrentStep(currentStep + 1)}
                  disabled={!canProceed()}
                >
                  下一步
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={loading || !canProceed()}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {loading ? (
                    <>創建中...</>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-1" />
                      創建作業
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
