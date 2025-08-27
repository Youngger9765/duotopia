import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import TeacherLayout from '@/components/TeacherLayout';
import StudentTable, { Student } from '@/components/StudentTable';
import { ArrowLeft, Users, BookOpen, Plus, Settings, Edit, Clock, FileText, ListOrdered, X, Save, Mic } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Program {
  id: number;
  name: string;
  description?: string;
  level?: string;
  estimated_hours?: number;
  created_at?: string;
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
      setPrograms(classroomPrograms);
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
        <div className={`transition-all duration-300 ${isPanelOpen ? 'mr-96' : ''}`}>
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
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  新增學生
                </Button>
              </div>
              
              <StudentTable
                students={classroom.students}
                showClassroom={false}
                onAddStudent={() => console.log('Add student')}
                onEditStudent={(student) => console.log('Edit student:', student)}
                onEmailStudent={(student) => console.log('Email student:', student)}
                emptyMessage="此班級尚無學生"
              />
            </TabsContent>

            {/* Programs Tab */}
            <TabsContent value="programs" className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">班級課程</h3>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  建立課程
                </Button>
              </div>
              
              {programs.length > 0 ? (
                <Accordion type="single" collapsible className="w-full">
                  {programs.map((program) => (
                    <AccordionItem key={program.id} value={`program-${program.id}`}>
                      <AccordionTrigger className="hover:no-underline">
                        <div className="flex items-center justify-between w-full pr-4">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                              <BookOpen className="h-5 w-5 text-blue-600" />
                            </div>
                            <div className="text-left">
                              <h4 className="font-semibold">{program.name}</h4>
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
                          </div>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="pl-14 pr-4">
                          {/* Mock Lessons - 實際應從 API 獲取 */}
                          <Accordion type="single" collapsible className="w-full">
                            {[1, 2, 3].map((lessonNum) => (
                              <AccordionItem key={lessonNum} value={`lesson-${program.id}-${lessonNum}`} className="border-l-2 border-gray-200 ml-2">
                                <AccordionTrigger className="hover:no-underline pl-4">
                                  <div className="flex items-center justify-between w-full pr-4">
                                    <div className="flex items-center space-x-3">
                                      <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                                        <ListOrdered className="h-4 w-4 text-green-600" />
                                      </div>
                                      <div className="text-left">
                                        <h5 className="font-medium">第 {lessonNum} 課：基礎對話練習</h5>
                                        <p className="text-sm text-gray-500">Greetings and Introductions</p>
                                      </div>
                                    </div>
                                    <div className="text-sm text-gray-500">
                                      30 分鐘
                                    </div>
                                  </div>
                                </AccordionTrigger>
                                <AccordionContent>
                                  <div className="pl-12 pr-4 space-y-3">
                                    {/* Mock Contents - 實際應從 API 獲取 */}
                                    {[
                                      { id: 1, type: '朗讀錄音', items: 5, time: '10 分鐘' },
                                      { id: 2, type: '口說練習', items: 3, time: '10 分鐘' },
                                      { id: 3, type: '情境對話', items: 2, time: '10 分鐘' },
                                    ].map((content) => (
                                      <div key={content.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                                        <div className="flex items-center space-x-3">
                                          <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                                            <FileText className="h-4 w-4 text-purple-600" />
                                          </div>
                                          <div>
                                            <p className="font-medium text-sm">{content.type}</p>
                                            <p className="text-xs text-gray-500">{content.items} 個項目</p>
                                          </div>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                          <span className="text-sm text-gray-500">{content.time}</span>
                                          <Button 
                                            size="sm" 
                                            variant="outline"
                                            onClick={() => handleContentClick({
                                              ...content,
                                              lessonName: `第 ${lessonNum} 課：基礎對話練習`,
                                              programName: program.name
                                            })}
                                          >
                                            檢視
                                          </Button>
                                        </div>
                                      </div>
                                    ))}
                                    
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
                            ))}
                            
                            {/* Add Lesson Button */}
                            <div className="pl-6 pt-2">
                              <Button size="sm" variant="outline" className="w-full">
                                <Plus className="h-4 w-4 mr-2" />
                                新增單元
                              </Button>
                            </div>
                          </Accordion>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              ) : (
                <div className="text-center py-12">
                  <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">尚未建立課程</p>
                  <p className="text-sm text-gray-400 mt-2">為班級建立課程內容，開始教學</p>
                  <Button className="mt-4" size="sm">
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
        <div className={`fixed right-0 top-0 h-full w-96 bg-white shadow-xl border-l transform transition-transform duration-300 z-50 ${
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

                  {/* Mock Content Items */}
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
    </TeacherLayout>
  );
}