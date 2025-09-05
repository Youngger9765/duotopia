import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BookOpen, Copy, Plus, Archive, Search, CheckCircle } from 'lucide-react';
import { TagInputWithSuggestions, TagSuggestion } from '@/components/ui/tag-input';
import { apiClient } from '@/lib/api';
import { toast } from 'sonner';

interface Program {
  id: number;
  name: string;
  description?: string;
  is_template?: boolean;
  classroom_id?: number;
  classroom_name?: string;
  level?: string;
  estimated_hours?: number;
  lesson_count?: number;
  tags?: string[];
}


interface CreateProgramDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  classroomId: number;
  classroomName: string;
}

export default function CreateProgramDialog({
  open,
  onClose,
  onSuccess,
  classroomId,
  classroomName
}: CreateProgramDialogProps) {
  const [activeTab, setActiveTab] = useState('template');
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  // 公版模板
  const [templates, setTemplates] = useState<Program[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<Program | null>(null);
  const [templateName, setTemplateName] = useState('');

  // 其他班級課程
  const [copyablePrograms, setCopyablePrograms] = useState<Program[]>([]);
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const [copyName, setCopyName] = useState('');

  // 自建課程
  const [customForm, setCustomForm] = useState({
    name: '',
    description: '',
    level: 'A1',
    estimated_hours: '',
    tags: [] as string[],
  });

  const [searchTerm, setSearchTerm] = useState('');

  // 預設的標籤建議
  const tagSuggestions: TagSuggestion[] = [
    // 程度相關
    { value: 'beginner', label: '初級', category: 'level' },
    { value: 'intermediate', label: '中級', category: 'level' },
    { value: 'advanced', label: '進階', category: 'level' },

    // 技能相關
    { value: 'speaking', label: '口說', category: 'skill' },
    { value: 'listening', label: '聽力', category: 'skill' },
    { value: 'reading', label: '閱讀', category: 'skill' },
    { value: 'writing', label: '寫作', category: 'skill' },
    { value: 'grammar', label: '文法', category: 'skill' },
    { value: 'vocabulary', label: '詞彙', category: 'skill' },
    { value: 'pronunciation', label: '發音', category: 'skill' },

    // 主題相關
    { value: 'daily', label: '日常生活', category: 'topic' },
    { value: 'business', label: '商務', category: 'topic' },
    { value: 'travel', label: '旅遊', category: 'topic' },
    { value: 'academic', label: '學術', category: 'topic' },
    { value: 'conversation', label: '會話', category: 'topic' },
    { value: 'exam', label: '考試準備', category: 'topic' },

    // 其他
    { value: 'phonics', label: '自然發音', category: 'other' },
    { value: 'interactive', label: '互動式', category: 'other' },
    { value: 'game-based', label: '遊戲化', category: 'other' },
  ];

  useEffect(() => {
    if (open) {
      fetchData();
      resetForms();
    }
  }, [open]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [templatesData, copyableData] = await Promise.all([
        apiClient.getTemplatePrograms() as Promise<Program[]>,
        apiClient.getCopyablePrograms() as Promise<Program[]>
      ]);

      setTemplates(templatesData);
      // 過濾掉當前班級的課程
      const otherPrograms = copyableData.filter(p => p.classroom_id !== classroomId);
      setCopyablePrograms(otherPrograms);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('載入課程資料失敗');
    } finally {
      setLoading(false);
    }
  };

  const resetForms = () => {
    setSelectedTemplate(null);
    setTemplateName('');
    setSelectedProgram(null);
    setCopyName('');
    setCustomForm({
      name: '',
      description: '',
      level: 'A1',
      estimated_hours: '',
      tags: [],
    });
    setSearchTerm('');
    setActiveTab('template');
  };

  const handleCreateFromTemplate = async () => {
    if (!selectedTemplate) return;

    setCreating(true);
    try {
      await apiClient.copyFromTemplate({
        template_id: selectedTemplate.id,
        classroom_id: classroomId,
        name: templateName || undefined,
      });
      toast.success('成功從公版模板建立課程！');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Failed to create from template:', error);
      toast.error('建立失敗，請稍後再試');
    } finally {
      setCreating(false);
    }
  };

  const handleCopyFromClassroom = async () => {
    if (!selectedProgram) return;

    setCreating(true);
    try {
      await apiClient.copyFromClassroom({
        source_program_id: selectedProgram.id,
        target_classroom_id: classroomId,
        name: copyName || undefined,
      });
      toast.success('成功複製課程！');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Failed to copy from classroom:', error);
      toast.error('複製失敗，請稍後再試');
    } finally {
      setCreating(false);
    }
  };

  const handleCreateCustom = async () => {
    if (!customForm.name) return;

    setCreating(true);
    try {
      await apiClient.createCustomProgram(classroomId, {
        name: customForm.name,
        description: customForm.description,
        level: customForm.level,
        estimated_hours: customForm.estimated_hours ? Number(customForm.estimated_hours) : undefined,
        tags: customForm.tags,
      });
      toast.success('成功建立自訂課程！');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Failed to create custom program:', error);
      toast.error('建立失敗，請稍後再試');
    } finally {
      setCreating(false);
    }
  };

  const filteredTemplates = templates.filter(t =>
    t.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredPrograms = copyablePrograms.filter(p =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getLevelBadge = (level?: string) => {
    if (!level) return null;
    const levelColors: Record<string, string> = {
      'A1': 'bg-green-100 text-green-800',
      'A2': 'bg-green-100 text-green-800',
      'B1': 'bg-blue-100 text-blue-800',
      'B2': 'bg-blue-100 text-blue-800',
      'C1': 'bg-purple-100 text-purple-800',
      'C2': 'bg-purple-100 text-purple-800',
    };
    const color = levelColors[level.toUpperCase()] || 'bg-gray-100 text-gray-800';
    return <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>{level}</span>;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>建立課程到「{classroomName}」</DialogTitle>
          <DialogDescription>
            選擇建立課程的方式
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 overflow-hidden">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="template" className="flex items-center gap-2">
              <Archive className="h-4 w-4" />
              從公版複製
            </TabsTrigger>
            <TabsTrigger value="classroom" className="flex items-center gap-2">
              <Copy className="h-4 w-4" />
              從其他班級複製
            </TabsTrigger>
            <TabsTrigger value="custom" className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              自建課程
            </TabsTrigger>
          </TabsList>

          {/* 從公版模板複製 */}
          <TabsContent value="template" className="flex-1 overflow-hidden flex flex-col">
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="搜尋公版課程模板..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 mb-4">
              {loading ? (
                <div className="text-center py-8 text-gray-500">載入中...</div>
              ) : filteredTemplates.length === 0 ? (
                <div className="text-center py-8 text-gray-500">沒有可用的公版課程模板</div>
              ) : (
                filteredTemplates.map((template) => (
                  <div
                    key={template.id}
                    onClick={() => {
                      setSelectedTemplate(template);
                      setTemplateName(template.name);
                    }}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedTemplate?.id === template.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <BookOpen className="h-4 w-4 text-gray-400" />
                          <h4 className="font-medium">{template.name}</h4>
                          {selectedTemplate?.id === template.id && (
                            <CheckCircle className="h-4 w-4 text-blue-500" />
                          )}
                        </div>
                        {template.description && (
                          <p className="text-sm text-gray-500 mt-1">{template.description}</p>
                        )}
                        <div className="flex items-center gap-4 mt-2">
                          {template.level && getLevelBadge(template.level)}
                          {template.estimated_hours && (
                            <span className="text-xs text-gray-500">{template.estimated_hours} 小時</span>
                          )}
                          {template.lesson_count && (
                            <span className="text-xs text-gray-500">{template.lesson_count} 個課程</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {selectedTemplate && (
              <div className="border-t pt-4">
                <Label htmlFor="template-name">新課程名稱（選填，留空使用原名）</Label>
                <Input
                  id="template-name"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder={selectedTemplate.name}
                  className="mt-1"
                />
              </div>
            )}
          </TabsContent>

          {/* 從其他班級複製 */}
          <TabsContent value="classroom" className="flex-1 overflow-hidden flex flex-col">
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="搜尋其他班級的課程..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 mb-4">
              {loading ? (
                <div className="text-center py-8 text-gray-500">載入中...</div>
              ) : filteredPrograms.length === 0 ? (
                <div className="text-center py-8 text-gray-500">沒有其他班級的課程</div>
              ) : (
                filteredPrograms.map((program) => (
                  <div
                    key={program.id}
                    onClick={() => {
                      setSelectedProgram(program);
                      setCopyName(program.name);
                    }}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedProgram?.id === program.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <BookOpen className="h-4 w-4 text-gray-400" />
                          <h4 className="font-medium">{program.name}</h4>
                          {selectedProgram?.id === program.id && (
                            <CheckCircle className="h-4 w-4 text-blue-500" />
                          )}
                        </div>
                        {program.classroom_name && (
                          <p className="text-sm text-gray-500 mt-1">來自：{program.classroom_name}</p>
                        )}
                        {program.description && (
                          <p className="text-sm text-gray-500 mt-1">{program.description}</p>
                        )}
                        <div className="flex items-center gap-4 mt-2">
                          {program.level && getLevelBadge(program.level)}
                          {program.estimated_hours && (
                            <span className="text-xs text-gray-500">{program.estimated_hours} 小時</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {selectedProgram && (
              <div className="border-t pt-4">
                <Label htmlFor="copy-name">新課程名稱（選填，留空使用原名）</Label>
                <Input
                  id="copy-name"
                  value={copyName}
                  onChange={(e) => setCopyName(e.target.value)}
                  placeholder={selectedProgram.name}
                  className="mt-1"
                />
              </div>
            )}
          </TabsContent>

          {/* 自建課程 */}
          <TabsContent value="custom" className="space-y-4">
            <div>
              <Label htmlFor="custom-name">課程名稱 *</Label>
              <Input
                id="custom-name"
                value={customForm.name}
                onChange={(e) => setCustomForm({ ...customForm, name: e.target.value })}
                placeholder="例如：進階英語會話"
              />
            </div>

            <div>
              <Label htmlFor="custom-description">課程描述</Label>
              <Textarea
                id="custom-description"
                value={customForm.description}
                onChange={(e) => setCustomForm({ ...customForm, description: e.target.value })}
                placeholder="描述這個課程的內容和目標"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="custom-level">等級</Label>
                <Select
                  value={customForm.level}
                  onValueChange={(value) => setCustomForm({ ...customForm, level: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="A1">A1 - 入門</SelectItem>
                    <SelectItem value="A2">A2 - 基礎</SelectItem>
                    <SelectItem value="B1">B1 - 中級</SelectItem>
                    <SelectItem value="B2">B2 - 中高級</SelectItem>
                    <SelectItem value="C1">C1 - 高級</SelectItem>
                    <SelectItem value="C2">C2 - 精通</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="custom-hours">預計時數</Label>
                <Input
                  id="custom-hours"
                  type="number"
                  value={customForm.estimated_hours}
                  onChange={(e) => setCustomForm({ ...customForm, estimated_hours: e.target.value })}
                  placeholder="20"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>標籤</Label>
              <TagInputWithSuggestions
                value={customForm.tags}
                onChange={(tags) => setCustomForm({ ...customForm, tags })}
                placeholder="輸入標籤後按 Enter 新增"
                maxTags={10}
                suggestions={tagSuggestions}
                showSuggestions={true}
              />
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={creating}>
            取消
          </Button>
          {activeTab === 'template' && (
            <Button
              onClick={handleCreateFromTemplate}
              disabled={!selectedTemplate || creating}
            >
              {creating ? '建立中...' : '從模板建立'}
            </Button>
          )}
          {activeTab === 'classroom' && (
            <Button
              onClick={handleCopyFromClassroom}
              disabled={!selectedProgram || creating}
            >
              {creating ? '複製中...' : '複製課程'}
            </Button>
          )}
          {activeTab === 'custom' && (
            <Button
              onClick={handleCreateCustom}
              disabled={!customForm.name || creating}
            >
              {creating ? '建立中...' : '建立自訂課程'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
