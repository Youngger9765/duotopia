import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Mic, 
  Volume2, 
  GripVertical, 
  Copy, 
  Trash2, 
  Plus, 
  Globe,
  X,
  Play,
  Square,
  RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';

interface ContentRow {
  id: string;
  text: string;
  definition: string;
  audioUrl?: string;
  audioSettings?: {
    accent: string;
    gender: string;
    speed: string;
  };
}

interface TTSModalProps {
  open: boolean;
  onClose: () => void;
  row: ContentRow;
  onConfirm: (audioUrl: string, settings: any) => void;
}

const TTSModal = ({ open, onClose, row, onConfirm }: TTSModalProps) => {
  const [text, setText] = useState(row.text);
  const [accent, setAccent] = useState(row.audioSettings?.accent || 'American English');
  const [gender, setGender] = useState(row.audioSettings?.gender || 'Male');
  const [speed, setSpeed] = useState(row.audioSettings?.speed || 'Normal x1');
  const [audioUrl, setAudioUrl] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState<string>('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const accents = ['American English', 'British English', 'Indian English', 'Australian English'];
  const genders = ['Male', 'Female'];
  const speeds = ['Slow x0.75', 'Normal x1', 'Fast x1.5'];

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      // TODO: Call actual TTS API
      // For now, mock the generation
      await new Promise(resolve => setTimeout(resolve, 1000));
      setAudioUrl('mock-audio-url');
      toast.success('音檔生成成功 (MOCK)');
    } catch (error) {
      toast.error('生成失敗，請重試');
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePlayAudio = () => {
    if (audioUrl && audioRef.current) {
      audioRef.current.play();
    }
  };

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const url = URL.createObjectURL(audioBlob);
        setRecordedAudio(url);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      toast.error('無法啟動錄音，請檢查麥克風權限');
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleConfirm = () => {
    const finalAudioUrl = recordedAudio || audioUrl;
    if (!finalAudioUrl) {
      toast.error('請先生成或錄製音檔');
      return;
    }
    onConfirm(finalAudioUrl, { accent, gender, speed });
    onClose();
  };

  const handleRemove = () => {
    setAudioUrl('');
    setRecordedAudio('');
    toast.info('已移除音檔');
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>音檔設定</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="generate" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="generate">Generate</TabsTrigger>
            <TabsTrigger value="record">Record</TabsTrigger>
          </TabsList>

          <TabsContent value="generate" className="space-y-4">
            <div>
              <label className="text-sm font-medium">Text</label>
              <input
                type="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                placeholder="Enter text to generate speech"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Accent</label>
              <select
                value={accent}
                onChange={(e) => setAccent(e.target.value)}
                className="w-full mt-1 px-3 py-2 border rounded-md"
              >
                {accents.map(a => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Gender</label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                >
                  {genders.map(g => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm font-medium">Speed</label>
                <select
                  value={speed}
                  onChange={(e) => setSpeed(e.target.value)}
                  className="w-full mt-1 px-3 py-2 border rounded-md"
                >
                  {speeds.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-2">
              <Button 
                onClick={handleGenerate} 
                disabled={isGenerating}
                className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-black"
                title="MOCK: 此功能尚未連接實際 TTS API"
              >
                {isGenerating ? 'Generating...' : 'Generate (MOCK)'}
              </Button>
              {audioUrl && (
                <Button
                  variant="outline"
                  onClick={handlePlayAudio}
                  size="icon"
                >
                  <Play className="h-4 w-4" />
                </Button>
              )}
            </div>

            {audioUrl && (
              <audio ref={audioRef} src={audioUrl} className="hidden" />
            )}
          </TabsContent>

          <TabsContent value="record" className="space-y-4">
            <div className="flex flex-col items-center justify-center py-8">
              <div className="mb-4">
                <div className={`w-24 h-24 rounded-full flex items-center justify-center ${
                  isRecording ? 'bg-red-100 animate-pulse' : 'bg-gray-100'
                }`}>
                  <Mic className={`h-12 w-12 ${isRecording ? 'text-red-600' : 'text-gray-600'}`} />
                </div>
              </div>

              {!isRecording && !recordedAudio && (
                <Button onClick={handleStartRecording} size="lg">
                  <Mic className="h-5 w-5 mr-2" />
                  開始錄音
                </Button>
              )}

              {isRecording && (
                <Button onClick={handleStopRecording} variant="destructive" size="lg">
                  <Square className="h-5 w-5 mr-2" />
                  停止錄音
                </Button>
              )}

              {recordedAudio && !isRecording && (
                <div className="space-y-4">
                  <audio controls src={recordedAudio} className="w-full" />
                  <div className="flex gap-2">
                    <Button onClick={handleStartRecording} variant="outline">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      重新錄製
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={handleRemove}>
            Remove
          </Button>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          <Button onClick={handleConfirm}>
            Confirm
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

interface ReadingAssessmentEditorProps {
  lessonId: number;
  contentId?: number;
  initialData?: any;
  onSave: (data: any) => void;
  onCancel: () => void;
}

export default function ReadingAssessmentEditor({
  lessonId,
  contentId,
  initialData,
  onSave,
  onCancel
}: ReadingAssessmentEditorProps) {
  const [title, setTitle] = useState(initialData?.title || '');
  const [rows, setRows] = useState<ContentRow[]>(
    initialData?.rows || [
      { id: '1', text: '', definition: '' },
      { id: '2', text: '', definition: '' },
      { id: '3', text: '', definition: '' }
    ]
  );
  const [level, setLevel] = useState(initialData?.level || 'A1');
  const [tags, setTags] = useState<string[]>(initialData?.tags || ['public']);
  const [tagInput, setTagInput] = useState('');
  const [selectedRow, setSelectedRow] = useState<ContentRow | null>(null);
  const [ttsModalOpen, setTtsModalOpen] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Load existing content data if editing
  useEffect(() => {
    if (contentId) {
      loadContentData();
    }
  }, [contentId]);

  const loadContentData = async () => {
    if (!contentId) return;
    
    setIsLoading(true);
    try {
      // TODO: Call API to load content data
      // For now, use mock data
      const mockData = {
        title: '朗讀錄音練習 ' + contentId,
        items: [
          { text: 'Hello, how are you?', translation: '你好，你好嗎？' },
          { text: 'I am fine, thank you.', translation: '我很好，謝謝。' },
          { text: 'What is your name?', translation: '你叫什麼名字？' }
        ],
        level: 'A1',
        tags: ['greeting', 'basic']
      };
      
      setTitle(mockData.title);
      setRows(mockData.items.map((item, index) => ({
        id: (index + 1).toString(),
        text: item.text,
        definition: item.translation
      })));
      setLevel(mockData.level);
      setTags(mockData.tags);
    } catch (error) {
      toast.error('載入內容失敗');
    } finally {
      setIsLoading(false);
    }
  };

  const levels = ['PreA', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    if (draggedIndex === null) return;

    const draggedRow = rows[draggedIndex];
    const newRows = [...rows];
    newRows.splice(draggedIndex, 1);
    newRows.splice(dropIndex, 0, draggedRow);
    setRows(newRows);
    setDraggedIndex(null);
  };

  const handleAddRow = () => {
    if (rows.length >= 15) {
      toast.error('最多只能新增 15 列');
      return;
    }
    const newRow: ContentRow = {
      id: Date.now().toString(),
      text: '',
      definition: ''
    };
    setRows([...rows, newRow]);
  };

  const handleDeleteRow = (index: number) => {
    if (rows.length <= 3) {
      toast.error('至少需要保留 3 列');
      return;
    }
    const newRows = rows.filter((_, i) => i !== index);
    setRows(newRows);
  };

  const handleCopyRow = (index: number) => {
    if (rows.length >= 15) {
      toast.error('最多只能新增 15 列');
      return;
    }
    const rowToCopy = rows[index];
    const newRow: ContentRow = {
      ...rowToCopy,
      id: Date.now().toString()
    };
    const newRows = [...rows];
    newRows.splice(index + 1, 0, newRow);
    setRows(newRows);
  };

  const handleUpdateRow = (index: number, field: keyof ContentRow, value: string) => {
    const newRows = [...rows];
    newRows[index] = { ...newRows[index], [field]: value };
    setRows(newRows);
  };

  const handleOpenTTSModal = (row: ContentRow) => {
    setSelectedRow(row);
    setTtsModalOpen(true);
  };

  const handleTTSConfirm = (audioUrl: string, settings: any) => {
    if (selectedRow) {
      const index = rows.findIndex(r => r.id === selectedRow.id);
      if (index !== -1) {
        const newRows = [...rows];
        newRows[index] = {
          ...newRows[index],
          audioUrl,
          audioSettings: settings
        };
        setRows(newRows);
      }
    }
  };

  const handleBatchGenerateTTS = async () => {
    toast.info('開始批次生成語音...');
    // TODO: Implement batch TTS generation
    const newRows = [...rows];
    for (let i = 0; i < newRows.length; i++) {
      if (newRows[i].text && !newRows[i].audioUrl) {
        // MOCK: Generate TTS for this row
        newRows[i].audioUrl = 'mock-audio-url';
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    setRows(newRows);
    toast.success('批次生成完成 (MOCK)');
  };

  const handleGenerateSingleDefinition = async (index: number, translationType: 'chinese' | 'english' = 'chinese') => {
    toast.info(`生成翻譯中...`);
    // TODO: Implement definition generation with Google Translate API
    const newRows = [...rows];
    if (newRows[index].text) {
      // MOCK: Generate definition for this specific row
      newRows[index].definition = translationType === 'chinese' 
        ? `${newRows[index].text} 的中文翻譯 (MOCK)`
        : `Definition of ${newRows[index].text} (MOCK)`;
      await new Promise(resolve => setTimeout(resolve, 500));
      setRows(newRows);
      toast.success('翻譯生成完成 (MOCK)');
    } else {
      toast.error('請先輸入文本');
    }
  };

  const handleBatchGenerateDefinitions = async (translationType: 'chinese' | 'english') => {
    toast.info(`開始批次生成${translationType === 'chinese' ? '中文' : '英文'}翻譯...`);
    // TODO: Implement batch definition generation
    const newRows = [...rows];
    for (let i = 0; i < newRows.length; i++) {
      if (newRows[i].text && !newRows[i].definition) {
        // MOCK: Generate definition for this row
        newRows[i].definition = translationType === 'chinese' 
          ? `${newRows[i].text} 的中文翻譯 (MOCK)`
          : `Definition of ${newRows[i].text} (MOCK)`;
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    }
    setRows(newRows);
    toast.success('批次翻譯生成完成 (MOCK)');
  };

  const handleAddTag = () => {
    if (tagInput && !tags.includes(tagInput)) {
      setTags([...tags, tagInput]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  const handleSave = () => {
    if (!title) {
      toast.error('請輸入標題');
      return;
    }

    const validRows = rows.filter(r => r.text.trim());
    if (validRows.length < 3) {
      toast.error('至少需要 3 個有效的文本項目');
      return;
    }

    const data = {
      title,
      type: 'reading_assessment',
      lessonId,
      contentId,
      rows: validRows,
      level,
      tags
    };

    onSave(data);
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">載入中...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* MOCK Warning Banner */}
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-3 rounded mb-6">
          <div className="flex items-center">
            <span className="font-bold mr-2">⚠️ 開發模式：</span>
            <span>TTS 生成、語音錄製、翻譯功能目前為 MOCK 實作，尚未連接實際 API</span>
          </div>
        </div>

        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-4">{contentId ? '編輯' : '新增'}朗讀錄音內容</h2>
          
          <div className="mb-4">
            <label className="text-sm font-medium">標題：</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="ml-2 px-3 py-1 border rounded-md"
              placeholder="輸入標題"
            />
          </div>

          {/* Audio Controls */}
          <div className="flex items-center gap-2 mb-4">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBatchGenerateTTS}
              className="bg-yellow-100 hover:bg-yellow-200 border-yellow-300"
              title="MOCK: 此功能尚未連接實際 TTS API"
            >
              <Volume2 className="h-4 w-4 mr-1" />
              批次生成TTS (MOCK)
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBatchGenerateDefinitions('chinese')}
              className="bg-yellow-100 hover:bg-yellow-200 border-yellow-300"
              title="MOCK: 此功能尚未連接 Google Translate API"
            >
              <Globe className="h-4 w-4 mr-1" />
              批次生成翻譯 (MOCK)
            </Button>
          </div>
        </div>

        {/* Content Rows */}
        <div className="space-y-3 mb-6">
          {rows.map((row, index) => (
            <div
              key={row.id}
              className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg"
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, index)}
            >
              <div className="flex items-center gap-1">
                <GripVertical className="h-5 w-5 text-gray-400 cursor-move" />
                <span className="text-sm font-medium text-gray-600 w-6">
                  {index + 1}
                </span>
              </div>

              <div className="flex-1 grid grid-cols-2 gap-2">
                <div className="relative">
                  <input
                    type="text"
                    value={row.text}
                    onChange={(e) => handleUpdateRow(index, 'text', e.target.value)}
                    className="w-full px-3 py-2 pr-10 border rounded-md"
                    placeholder="輸入文本"
                    maxLength={200}
                  />
                  <button
                    onClick={() => handleOpenTTSModal(row)}
                    className={`absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded ${
                      row.audioUrl ? 'text-blue-600 hover:bg-blue-100' : 'text-gray-600 bg-yellow-100 hover:bg-yellow-200'
                    }`}
                    title={row.audioUrl ? '已有音檔' : 'MOCK: 開啟 TTS/錄音 Modal (尚未連接實際 API)'}
                  >
                    <Mic className="h-4 w-4" />
                  </button>
                </div>

                <div className="relative">
                  <input
                    type="text"
                    value={row.definition}
                    onChange={(e) => handleUpdateRow(index, 'definition', e.target.value)}
                    className="w-full px-3 py-2 pr-10 border rounded-md"
                    placeholder="輸入定義"
                  />
                  <button
                    onClick={() => handleGenerateSingleDefinition(index, 'chinese')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-yellow-200 bg-yellow-100 text-gray-600"
                    title="MOCK: 生成此項翻譯 (尚未連接 Google Translate API)"
                  >
                    <Globe className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => handleCopyRow(index)}
                  className="p-1 rounded hover:bg-gray-200"
                  title="複製"
                >
                  <Copy className="h-4 w-4 text-gray-600" />
                </button>
                <button
                  onClick={() => handleDeleteRow(index)}
                  className="p-1 rounded hover:bg-gray-200"
                  title="刪除"
                  disabled={rows.length <= 3}
                >
                  <Trash2 className={`h-4 w-4 ${rows.length <= 3 ? 'text-gray-300' : 'text-gray-600'}`} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Add Row Button */}
        <button
          onClick={handleAddRow}
          className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 flex items-center justify-center gap-2 text-gray-600 hover:text-blue-600"
          disabled={rows.length >= 15}
        >
          <Plus className="h-5 w-5" />
          新增項目
        </button>

        {/* Level and Tags */}
        <div className="mt-6 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">LEVEL：</label>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className="px-3 py-1 border rounded-md"
            >
              {levels.map(l => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">標籤：</label>
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddTag();
                }
              }}
              className="px-3 py-1 border rounded-md"
              placeholder="搜尋標籤或按 Enter 新增"
            />
          </div>

          <div className="flex gap-2">
            {tags.map(tag => (
              <span
                key={tag}
                className="px-3 py-1 bg-gray-100 rounded-full text-sm flex items-center gap-1"
              >
                {tag}
                <button
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-1 hover:text-red-600"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex justify-end gap-3">
          <Button variant="outline" onClick={onCancel}>
            取消
          </Button>
          <Button onClick={handleSave}>
            儲存
          </Button>
        </div>
      </div>

      {/* TTS Modal */}
      {selectedRow && (
        <TTSModal
          open={ttsModalOpen}
          onClose={() => setTtsModalOpen(false)}
          row={selectedRow}
          onConfirm={handleTTSConfirm}
        />
      )}
    </div>
  );
}