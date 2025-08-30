import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { 
  Mic, 
  Globe,
  GripVertical, 
  Copy, 
  Trash2, 
  Plus,
  Volume2
} from 'lucide-react';
import { toast } from 'sonner';

interface ContentRow {
  id: string;
  text: string;
  definition: string;
  audioUrl?: string;
}

interface ReadingAssessmentPanelProps {
  content: any;
  editingContent: any;
  onUpdateContent: (content: any) => void;
  onSave: () => void;
}

export default function ReadingAssessmentPanel({
  content,
  editingContent,
  onUpdateContent,
  onSave
}: ReadingAssessmentPanelProps) {
  const [rows, setRows] = useState<ContentRow[]>([]);
  const [title, setTitle] = useState('');
  const [level, setLevel] = useState('A1');
  const [tags, setTags] = useState<string[]>(['public']);
  const [tagInput, setTagInput] = useState('');

  useEffect(() => {
    // Initialize from editingContent
    if (editingContent) {
      setTitle(editingContent.title || content?.title || '');
      
      // Convert items to rows format
      if (editingContent.items && Array.isArray(editingContent.items)) {
        const convertedRows = editingContent.items.map((item: any, index: number) => ({
          id: (index + 1).toString(),
          text: item.text || '',
          definition: item.translation || item.definition || '',
          audioUrl: item.audio_url || ''
        }));
        setRows(convertedRows.length > 0 ? convertedRows : [
          { id: '1', text: '', definition: '' },
          { id: '2', text: '', definition: '' },
          { id: '3', text: '', definition: '' }
        ]);
      } else {
        setRows([
          { id: '1', text: '', definition: '' },
          { id: '2', text: '', definition: '' },
          { id: '3', text: '', definition: '' }
        ]);
      }
      
      setLevel(editingContent.level || content?.level || 'A1');
      setTags(editingContent.tags || content?.tags || ['public']);
    }
  }, [editingContent, content]);

  // Update parent when rows change
  useEffect(() => {
    const items = rows.map(row => ({
      text: row.text,
      translation: row.definition,
      audio_url: row.audioUrl
    }));
    
    onUpdateContent({
      ...editingContent,
      title,
      items,
      level,
      tags
    });
  }, [rows, title, level, tags]);

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

  const handleGenerateSingleDefinition = async (index: number) => {
    toast.info(`生成翻譯中...`);
    const newRows = [...rows];
    if (newRows[index].text) {
      // MOCK: Generate definition
      newRows[index].definition = `${newRows[index].text} 的中文翻譯 (MOCK)`;
      await new Promise(resolve => setTimeout(resolve, 500));
      setRows(newRows);
      toast.success('翻譯生成完成 (MOCK)');
    } else {
      toast.error('請先輸入文本');
    }
  };

  const handleBatchGenerateTTS = async () => {
    toast.info('開始批次生成語音...');
    const newRows = [...rows];
    for (let i = 0; i < newRows.length; i++) {
      if (newRows[i].text && !newRows[i].audioUrl) {
        newRows[i].audioUrl = 'mock-audio-url';
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    setRows(newRows);
    toast.success('批次生成完成 (MOCK)');
  };

  const handleBatchGenerateDefinitions = async () => {
    toast.info(`開始批次生成翻譯...`);
    const newRows = [...rows];
    for (let i = 0; i < newRows.length; i++) {
      if (newRows[i].text && !newRows[i].definition) {
        newRows[i].definition = `${newRows[i].text} 的中文翻譯 (MOCK)`;
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    }
    setRows(newRows);
    toast.success('批次翻譯生成完成 (MOCK)');
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  const handleAddTag = () => {
    if (tagInput && !tags.includes(tagInput)) {
      setTags([...tags, tagInput]);
      setTagInput('');
    }
  };

  const levels = ['PreA', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

  return (
    <div className="space-y-4">
      {/* MOCK Warning */}
      <div className="bg-yellow-100 border border-yellow-400 text-yellow-800 px-3 py-2 rounded text-sm">
        <span className="font-bold">⚠️ 開發模式：</span>
        TTS 生成、語音錄製、翻譯功能目前為 MOCK 實作
      </div>

      {/* Title */}
      <div>
        <h3 className="text-lg font-semibold mb-2">
          {content?.isNew ? '新增' : '編輯'}朗讀錄音內容
        </h3>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full px-3 py-2 border rounded-md"
          placeholder="輸入標題"
        />
      </div>

      {/* Batch Actions */}
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleBatchGenerateTTS}
          className="bg-yellow-100 hover:bg-yellow-200 border-yellow-300"
        >
          <Volume2 className="h-4 w-4 mr-1" />
          批次生成TTS (MOCK)
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleBatchGenerateDefinitions}
          className="bg-yellow-100 hover:bg-yellow-200 border-yellow-300"
        >
          <Globe className="h-4 w-4 mr-1" />
          批次生成翻譯 (MOCK)
        </Button>
      </div>

      {/* Content Rows */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {rows.map((row, index) => (
          <div
            key={row.id}
            className="flex items-start gap-2 p-2 bg-gray-50 rounded"
          >
            <div className="flex flex-col items-center gap-1 mt-2">
              <GripVertical className="h-4 w-4 text-gray-400 cursor-move" />
              <span className="text-xs font-medium text-gray-600">
                {index + 1}
              </span>
            </div>

            <div className="flex-1 space-y-2">
              <div className="relative">
                <input
                  type="text"
                  value={row.text}
                  onChange={(e) => handleUpdateRow(index, 'text', e.target.value)}
                  className="w-full px-3 py-1.5 pr-10 border rounded text-sm"
                  placeholder="輸入文本"
                />
                <button
                  onClick={() => toast.info('開啟 TTS Modal (TODO)')}
                  className={`absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded ${
                    row.audioUrl ? 'text-blue-600 hover:bg-blue-100' : 'text-gray-600 bg-yellow-100 hover:bg-yellow-200'
                  }`}
                  title="錄音/TTS"
                >
                  <Mic className="h-3 w-3" />
                </button>
              </div>

              <div className="relative">
                <input
                  type="text"
                  value={row.definition}
                  onChange={(e) => handleUpdateRow(index, 'definition', e.target.value)}
                  className="w-full px-3 py-1.5 pr-10 border rounded text-sm"
                  placeholder="輸入定義"
                />
                <button
                  onClick={() => handleGenerateSingleDefinition(index)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-yellow-200 bg-yellow-100 text-gray-600"
                  title="生成翻譯"
                >
                  <Globe className="h-3 w-3" />
                </button>
              </div>
            </div>

            <div className="flex flex-col gap-1 mt-2">
              <button
                onClick={() => handleCopyRow(index)}
                className="p-1 rounded hover:bg-gray-200"
                title="複製"
              >
                <Copy className="h-3 w-3 text-gray-600" />
              </button>
              <button
                onClick={() => handleDeleteRow(index)}
                className="p-1 rounded hover:bg-gray-200"
                title="刪除"
                disabled={rows.length <= 3}
              >
                <Trash2 className={`h-3 w-3 ${rows.length <= 3 ? 'text-gray-300' : 'text-gray-600'}`} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add Row Button */}
      <button
        onClick={handleAddRow}
        className="w-full py-1.5 border-2 border-dashed border-gray-300 rounded hover:border-blue-400 flex items-center justify-center gap-2 text-gray-600 hover:text-blue-600 text-sm"
        disabled={rows.length >= 15}
      >
        <Plus className="h-4 w-4" />
        新增項目
      </button>

      {/* Level and Tags */}
      <div className="space-y-3 pt-3 border-t">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">LEVEL：</label>
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
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
            className="flex-1 px-2 py-1 border rounded text-sm"
            placeholder="搜尋標籤或按 Enter 新增"
          />
        </div>

        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {tags.map(tag => (
              <span
                key={tag}
                className="px-2 py-0.5 bg-gray-100 rounded-full text-xs flex items-center gap-1"
              >
                {tag}
                <button
                  onClick={() => handleRemoveTag(tag)}
                  className="hover:text-red-600"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}