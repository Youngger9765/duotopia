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
import { apiClient } from '@/lib/api';
import { retryAudioUpload } from '@/utils/retryHelper';

interface ContentRow {
  id: string | number;
  text: string;
  definition: string;
  audioUrl?: string;
  audio_url?: string;
  translation?: string;
  selectedLanguage?: 'chinese' | 'english';  // 最後選擇的語言
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
  onConfirm: (audioUrl: string, settings: { accent?: string; gender?: string; speed?: string; source?: string; audioBlob?: Blob | null }) => void;
  contentId?: number;
  itemIndex?: number;
  isCreating?: boolean; // 是否為新增模式
}

const TTSModal = ({ open, onClose, row, onConfirm, contentId, itemIndex, isCreating = false }: TTSModalProps) => {
  const [text, setText] = useState(row.text);
  const [accent, setAccent] = useState(row.audioSettings?.accent || 'American English');
  const [gender, setGender] = useState(row.audioSettings?.gender || 'Male');
  const [speed, setSpeed] = useState(row.audioSettings?.speed || 'Normal x1');
  const [audioUrl, setAudioUrl] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState<string>('');
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [showAudioAnimation, setShowAudioAnimation] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedSource, setSelectedSource] = useState<'tts' | 'recording' | null>(null);
  const [activeTab, setActiveTab] = useState<string>('generate');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const audioBlobRef = useRef<Blob | null>(null);
  const recordingDurationRef = useRef<number>(0);

  const accents = ['American English', 'British English', 'Indian English', 'Australian English'];
  const genders = ['Male', 'Female'];
  const speeds = ['Slow x0.75', 'Normal x1', 'Fast x1.5'];

  // 當 modal 打開或 row.text 改變時，更新 text state
  useEffect(() => {
    if (open && row.text) {
      setText(row.text);
    }
  }, [open, row.text]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      // 根據選擇的口音和性別選擇適當的語音
      let voice = 'en-US-JennyNeural'; // 預設美國女聲

      if (accent === 'American English') {
        voice = gender === 'Male' ? 'en-US-ChristopherNeural' : 'en-US-JennyNeural';
      } else if (accent === 'British English') {
        voice = gender === 'Male' ? 'en-GB-RyanNeural' : 'en-GB-SoniaNeural';
      } else if (accent === 'Australian English') {
        voice = gender === 'Male' ? 'en-AU-WilliamNeural' : 'en-AU-NatashaNeural';
      }

      // 轉換速度設定
      let rate = '+0%';
      if (speed === 'Slow x0.75') rate = '-25%';
      else if (speed === 'Fast x1.5') rate = '+50%';

      const result = await apiClient.generateTTS(text, voice, rate, '+0%');

      if (result?.audio_url) {
        // 如果是相對路徑，加上 API base URL
        const fullUrl = result.audio_url.startsWith('http')
          ? result.audio_url
          : `${import.meta.env.VITE_API_URL}${result.audio_url}`;
        setAudioUrl(fullUrl);

        // 觸發動畫效果
        setShowAudioAnimation(true);
        setTimeout(() => setShowAudioAnimation(false), 3000);

        // 自動播放一次讓使用者知道音檔已生成
        const previewAudio = new Audio(fullUrl);
        previewAudio.volume = 0.5;
        previewAudio.play().catch(() => {
          // 如果自動播放失敗（瀏覽器限制），仍顯示成功訊息
        });

        toast.success('音檔生成成功！點擊播放按鈕試聽');
      }
    } catch (err) {
      console.error('TTS generation failed:', err);
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
      // 檢查支援的 MIME 類型 - 優先使用 opus 編碼
      let mimeType = 'audio/webm';
      const possibleTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/ogg',
        'audio/mp4'
      ];

      for (const type of possibleTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          mimeType = type;
          break;
        }
      }

      console.log('Using MIME type:', mimeType);
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000  // 設定位元率
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      setRecordingDuration(0);

      // 設定計時器
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration(prev => {
          const newDuration = prev + 1;
          // 30秒自動停止
          if (newDuration >= 30) {
            handleStopRecording();
            toast.info('已達到最長錄音時間 30 秒');
          }
          return newDuration;
        });
      }, 1000);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        // 清理計時器
        if (recordingTimerRef.current) {
          clearInterval(recordingTimerRef.current);
          recordingTimerRef.current = null;
        }

        // 使用基本的 MIME type，去掉 codec 信息
        const basicMimeType = mimeType.split(';')[0];
        const audioBlob = new Blob(audioChunksRef.current, { type: basicMimeType });

        // 使用 ref 來獲取當前的錄音時長
        const currentDuration = recordingDurationRef.current || recordingDuration;

        // 檢查檔案大小 (2MB 限制)
        if (audioBlob.size > 2 * 1024 * 1024) {
          toast.error('錄音檔案太大，請縮短錄音時間');
          stream.getTracks().forEach(track => track.stop());
          return;
        }

        // 確保有錄音資料
        if (audioBlob.size === 0) {
          toast.error('錄音失敗，請檢查麥克風權限');
          stream.getTracks().forEach(track => track.stop());
          return;
        }

        // 儲存 blob 以便之後上傳
        audioBlobRef.current = audioBlob;
        recordingDurationRef.current = currentDuration;

        // 創建本地 URL 供預覽播放
        const localUrl = URL.createObjectURL(audioBlob);
        setRecordedAudio(localUrl);
        toast.success('錄音完成！可以試聽或重新錄製');

        stream.getTracks().forEach(track => track.stop());
      };

      // 使用 timeslice 參數，每100ms收集一次數據
      mediaRecorder.start(100);
      setIsRecording(true);
      toast.success('開始錄音');
    } catch {
      toast.error('無法啟動錄音，請檢查麥克風權限');
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      // 先儲存當前的錄音時長到 ref
      recordingDurationRef.current = recordingDuration;

      mediaRecorderRef.current.stop();
      setIsRecording(false);

      // 清理計時器
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    }
  };

  const handleConfirm = async () => {
    // 如果兩種音源都有，需要用戶選擇
    if (audioUrl && recordedAudio) {
      if (!selectedSource) {
        toast.warning('請選擇要使用的音源（TTS 或錄音）');
        return;
      }

      // 新增模式：不上傳，只傳遞本地 URL
      if (isCreating) {
        const finalUrl = selectedSource === 'tts' ? audioUrl : recordedAudio;
        onConfirm(finalUrl, {
          accent,
          gender,
          speed,
          source: selectedSource,
          audioBlob: selectedSource === 'recording' ? audioBlobRef.current : null
        });
        onClose();
        return;
      }

      // 編輯模式：如果選擇錄音且還沒上傳（URL 是 blob:// 開頭），現在上傳
      if (selectedSource === 'recording' && recordedAudio.startsWith('blob:') && audioBlobRef.current) {
        setIsUploading(true);
        try {
          const result = await retryAudioUpload(
            () => apiClient.uploadAudio(
              audioBlobRef.current!,
              recordingDurationRef.current || 1,
              Number(contentId),
              Number(itemIndex)
            ),
            (attempt, error) => {
              toast.warning(`上傳失敗，正在重試... (第 ${attempt}/3 次)`);
              console.error(`Upload attempt ${attempt} failed:`, error);
            }
          );

          if (result && result.audio_url) {
            onConfirm(result.audio_url, { accent, gender, speed, source: 'recording' });
            onClose();
          } else {
            throw new Error('No audio URL returned');
          }
        } catch (err) {
          console.error('Upload failed after retries:', err);
          toast.error('上傳失敗，請檢查網路連線後重試');
        } finally {
          setIsUploading(false);
        }
        return;
      }

      const finalUrl = selectedSource === 'tts' ? audioUrl : recordedAudio;
      onConfirm(finalUrl, { accent, gender, speed, source: selectedSource });
    } else {
      // 只有一種音源
      const finalAudioUrl = recordedAudio || audioUrl;
      if (!finalAudioUrl) {
        toast.error('請先生成或錄製音檔');
        return;
      }

      // 新增模式：不上傳，只傳遞本地 URL
      if (isCreating) {
        const source = recordedAudio ? 'recording' : 'tts';
        onConfirm(finalAudioUrl, {
          accent,
          gender,
          speed,
          source,
          audioBlob: source === 'recording' ? audioBlobRef.current : null
        });
        onClose();
        return;
      }

      // 編輯模式：如果是錄音且還沒上傳，現在上傳
      if (recordedAudio && recordedAudio.startsWith('blob:') && audioBlobRef.current) {
        setIsUploading(true);
        try {
          const result = await retryAudioUpload(
            () => apiClient.uploadAudio(
              audioBlobRef.current!,
              recordingDurationRef.current || 1,
              Number(contentId),
              Number(itemIndex)
            ),
            (attempt, error) => {
              toast.warning(`上傳失敗，正在重試... (第 ${attempt}/3 次)`);
              console.error(`Upload attempt ${attempt} failed:`, error);
            }
          );

          if (result && result.audio_url) {
            onConfirm(result.audio_url, { accent, gender, speed, source: 'recording' });
            onClose();
          } else {
            throw new Error('No audio URL returned');
          }
        } catch (err) {
          console.error('Upload failed after retries:', err);
          toast.error('上傳失敗，請檢查網路連線後重試');
        } finally {
          setIsUploading(false);
        }
        return;
      }

      const source = recordedAudio ? 'recording' : 'tts';
      onConfirm(finalAudioUrl, { accent, gender, speed, source });
    }
    onClose();
  };


  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>音檔設定</DialogTitle>
        </DialogHeader>

        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="w-full"
        >
          <TabsList className="grid w-full grid-cols-2 bg-gray-100 p-1 rounded-lg">
            <TabsTrigger
              value="generate"
              className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md transition-all"
            >
              <Volume2 className="h-4 w-4 mr-1" />
              Generate
              {audioUrl && (
                <span className="ml-1 text-xs">✓</span>
              )}
            </TabsTrigger>
            <TabsTrigger
              value="record"
              className="data-[state=active]:bg-red-500 data-[state=active]:text-white rounded-md transition-all"
            >
              <Mic className="h-4 w-4 mr-1" />
              Record
              {recordedAudio && (
                <span className="ml-1 text-xs">✓</span>
              )}
            </TabsTrigger>
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
                title="使用免費的 Microsoft Edge TTS 生成語音"
              >
                {isGenerating ? 'Generating...' : 'Generate'}
              </Button>
              {audioUrl && (
                <Button
                  variant="outline"
                  onClick={handlePlayAudio}
                  size="icon"
                  className={`
                    border-2 transition-all duration-300
                    ${showAudioAnimation
                      ? 'border-green-500 bg-green-50 animate-bounce scale-110'
                      : 'border-gray-300 hover:border-green-500 hover:bg-green-50'
                    }
                  `}
                  title="播放生成的音檔"
                >
                  <Play className={`h-4 w-4 ${showAudioAnimation ? 'text-green-600' : 'text-gray-600'}`} />
                </Button>
              )}
            </div>

            {/* 音檔生成成功提示與管理 */}
            {audioUrl && (
              <div className={`mt-3 p-3 border rounded-lg transition-all duration-300 ${
                showAudioAnimation
                  ? 'bg-green-50 border-green-200 animate-pulse'
                  : 'bg-gray-50 border-gray-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-gray-700">
                    {showAudioAnimation && (
                      <div className="flex items-center gap-1">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                    )}
                    <Volume2 className="h-4 w-4 text-gray-600" />
                    <span className="text-sm font-medium">
                      {showAudioAnimation ? '音檔已生成！點擊播放按鈕試聽' : 'TTS 音檔已準備'}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setAudioUrl('');
                      setSelectedSource(null);
                      toast.info('已刪除 TTS 音檔');
                    }}
                    className="text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}

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

              {/* 顯示錄音時間 */}
              {isRecording && (
                <div className="mb-4 text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {Math.floor(recordingDuration / 60).toString().padStart(2, '0')}:
                    {(recordingDuration % 60).toString().padStart(2, '0')} / 00:30
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    最長錄音時間 30 秒
                  </div>
                </div>
              )}

              {/* 顯示上傳狀態 */}
              {isUploading && (
                <div className="mb-4 text-center">
                  <div className="text-sm text-blue-600">
                    正在上傳錄音檔案...
                  </div>
                </div>
              )}

              {!isRecording && !recordedAudio && !isUploading && (
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
                  {/* 使用自定義播放按鈕避免瀏覽器相容性問題 */}
                  <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => {
                            if (!recordedAudio) {
                              toast.error('沒有錄音可播放');
                              return;
                            }

                            const audio = new Audio(recordedAudio);
                            audio.play().catch(err => {
                              console.error('Play failed:', err);
                              toast.error('無法播放錄音');
                            });
                          }}
                        >
                          <Play className="h-4 w-4" />
                        </Button>
                        <div className="flex items-center gap-2">
                          <Mic className="h-4 w-4 text-red-600" />
                          <span className="text-sm text-gray-700 font-medium">
                            錄音檔案已準備 ({recordingDuration}秒)
                          </span>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setRecordedAudio('');
                          setSelectedSource(null);
                          audioBlobRef.current = null;
                          setRecordingDuration(0);
                          recordingDurationRef.current = 0;
                          toast.info('已刪除錄音檔案');
                        }}
                        className="text-red-600 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
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

        {/* 音源選擇（當兩種都有時） */}
        {audioUrl && recordedAudio && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm font-medium text-yellow-800 mb-3">
              🎵 您有兩種音源可選擇，請選擇要使用的音檔：
            </p>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setSelectedSource('tts')}
                className={`p-3 rounded-lg border-2 transition-all ${
                  selectedSource === 'tts'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 bg-white hover:border-gray-400'
                }`}
              >
                <Volume2 className={`h-5 w-5 mx-auto mb-1 ${
                  selectedSource === 'tts' ? 'text-blue-600' : 'text-gray-600'
                }`} />
                <div className="text-sm font-medium">TTS 語音</div>
                <div className="text-xs text-gray-500">AI 生成</div>
              </button>

              <button
                onClick={() => setSelectedSource('recording')}
                className={`p-3 rounded-lg border-2 transition-all ${
                  selectedSource === 'recording'
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-300 bg-white hover:border-gray-400'
                }`}
              >
                <Mic className={`h-5 w-5 mx-auto mb-1 ${
                  selectedSource === 'recording' ? 'text-red-600' : 'text-gray-600'
                }`} />
                <div className="text-sm font-medium">錄音檔案</div>
                <div className="text-xs text-gray-500">教師錄製</div>
              </button>
            </div>
          </div>
        )}

        <DialogFooter>
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

interface ReadingAssessmentPanelProps {
  content?: { id?: number; title?: string; items?: ContentRow[] };
  editingContent?: { id?: number; title?: string; items?: ContentRow[] };
  onUpdateContent?: (content: Record<string, unknown>) => void;
  onSave?: () => void | Promise<void>;
  // Alternative props for ClassroomDetail usage
  lessonId?: number;
  contentId?: number;
  onCancel?: () => void;
  isOpen?: boolean;
  isCreating?: boolean; // 是否為新增模式
}

export default function ReadingAssessmentPanel({
  content,
  editingContent,
  onUpdateContent,
  onSave,
  lessonId,
  onCancel,
  isCreating = false
}: ReadingAssessmentPanelProps) {
  const [title, setTitle] = useState('朗讀評測內容');
  const [rows, setRows] = useState<ContentRow[]>([
    { id: '1', text: '', definition: '', translation: '', selectedLanguage: 'chinese' },
    { id: '2', text: '', definition: '', translation: '', selectedLanguage: 'chinese' },
    { id: '3', text: '', definition: '', translation: '', selectedLanguage: 'chinese' }
  ]);
  const [level, setLevel] = useState('A1');
  const [tags, setTags] = useState<string[]>([]);
  const [isPublic, setIsPublic] = useState(false);  // 獨立的 isPublic 狀態
  const [tagInput, setTagInput] = useState('');
  const [selectedRow, setSelectedRow] = useState<ContentRow | null>(null);
  const [ttsModalOpen, setTtsModalOpen] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const levels = ['PreA', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

  // Load existing content data from database
  useEffect(() => {
    if (content?.id) {
      loadContentData();
    }
  }, [content?.id]);

  const loadContentData = async () => {
    if (!content?.id) return;

    setIsLoading(true);
    try {
      const data = await apiClient.getContentDetail(content.id) as {
        title?: string;
        items?: Array<{ text?: string; translation?: string; definition?: string; audio_url?: string }>;
        level?: string;
        tags?: string[];
        is_public?: boolean;
        audio_urls?: string[];
      };
      setTitle(data.title || '');

      // Convert items to rows format
      if (data.items && Array.isArray(data.items)) {
        const convertedRows = data.items.map((item: { text?: string; translation?: string; definition?: string; english_definition?: string; audio_url?: string; selectedLanguage?: 'chinese' | 'english' }, index: number) => ({
          id: (index + 1).toString(),
          text: item.text || '',
          definition: item.definition || '',  // 中文翻譯
          translation: item.english_definition || '',  // 英文釋義
          audioUrl: item.audio_url || '',
          selectedLanguage: item.selectedLanguage || 'chinese'  // 使用保存的語言選擇，預設中文
        }));
        setRows(convertedRows);
      }

      setLevel(data.level || 'A1');
      setTags(data.tags || []);
      setIsPublic(data.is_public || false);
    } catch (error) {
      console.error('Failed to load content:', error);
      toast.error('載入內容失敗');
    } finally {
      setIsLoading(false);
    }
  };

  // Update parent when data changes
  useEffect(() => {
    if (!onUpdateContent) return;

    const items = rows.map(row => ({
      text: row.text,
      definition: row.definition,  // 中文翻譯
      translation: row.translation, // 英文釋義
      audio_url: row.audioUrl,
      selectedLanguage: row.selectedLanguage // 記錄最後選擇的語言
    }));

    onUpdateContent({
      ...editingContent,
      title,
      items,
      level,
      tags,
      is_public: isPublic
    });
  }, [rows, title, level, tags, isPublic]);

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
    // 找出最大的 ID 數字，然後加 1
    const maxId = Math.max(...rows.map(r => parseInt(String(r.id)) || 0));
    const newRow: ContentRow = {
      id: (maxId + 1).toString(),
      text: '',
      definition: '',
      translation: '',
      selectedLanguage: 'chinese'
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
    // 找出最大的 ID 數字，然後加 1
    const maxId = Math.max(...rows.map(r => parseInt(String(r.id)) || 0));
    const newRow: ContentRow = {
      ...rowToCopy,
      id: (maxId + 1).toString()
    };
    const newRows = [...rows];
    newRows.splice(index + 1, 0, newRow);
    setRows(newRows);
  };

  const handleUpdateRow = (index: number, field: keyof ContentRow, value: string | 'chinese' | 'english') => {
    const newRows = [...rows];
    newRows[index] = { ...newRows[index], [field]: value };
    setRows(newRows);
  };

  const handleRemoveAudio = async (index: number) => {
    const newRows = [...rows];
    newRows[index] = { ...newRows[index], audioUrl: '' };
    setRows(newRows);

    // 如果是編輯模式，立即更新到後端
    if (!isCreating && editingContent?.id) {
      try {
        const items = newRows.map(row => ({
          text: row.text,
          definition: row.definition,
          translation: row.translation,
          audio_url: row.audioUrl || '',
          selectedLanguage: row.selectedLanguage
        }));

        await apiClient.updateContent(editingContent.id, {
          title: title || editingContent.title,
          items
        });

        toast.success('已移除音檔');
      } catch (error) {
        console.error('Failed to remove audio:', error);
        toast.error('移除音檔失敗');
        // 恢復原始狀態
        const originalRows = [...rows];
        setRows(originalRows);
      }
    } else {
      toast.info('已移除音檔');
    }
  };

  const handleOpenTTSModal = (row: ContentRow) => {
    setSelectedRow(row);
    setTtsModalOpen(true);
  };

  const handleTTSConfirm = async (audioUrl: string, settings: { accent?: string; gender?: string; speed?: string; source?: string; audioBlob?: Blob | null }) => {
    if (selectedRow) {
      const index = rows.findIndex(r => r.id === selectedRow.id);
      if (index !== -1) {
        const newRows = [...rows];
        // 一個 item 只能有一種音檔來源（TTS 或錄音）
        newRows[index] = {
          ...newRows[index],
          audioUrl, // 新的音檔會覆蓋舊的
          audioSettings: {
            accent: settings.accent || 'American English',
            gender: settings.gender || 'Male',
            speed: settings.speed || 'Normal x1'
          }
        };
        setRows(newRows);

        // 立即更新 content 並儲存到後端
        const items = newRows.map(row => ({
          text: row.text,
          definition: row.definition,  // 中文翻譯
          translation: row.translation, // 英文釋義
          audio_url: row.audioUrl || '',
          selectedLanguage: row.selectedLanguage // 記錄最後選擇的語言
        }));

        // 新增模式：只更新本地狀態
        if (isCreating) {
          // 更新本地狀態
          if (onUpdateContent) {
            onUpdateContent({
              ...editingContent,
              title,
              items,
              level,
              tags
            });
          }
          console.log('Audio URL saved locally (will upload on final save):', audioUrl);
        } else {
          // 編輯模式：直接呼叫 API 更新
          try {
            const updateData = {
              title: title || editingContent?.title,
              items,
              level,
              tags
            };

            console.log('Updating content with new audio:', audioUrl);
            await apiClient.updateContent(editingContent?.id ?? 0, updateData);

            // 更新成功後，重新從後端載入內容以確保同步
            const response = await apiClient.getContentDetail(editingContent?.id ?? 0);
            if (response && response.items) {
              const updatedRows = response.items.map((item: { text?: string; translation?: string; definition?: string; audio_url?: string }, index: number) => ({
                id: String(index + 1),
                text: item.text || '',
                definition: item.translation || '',
                audioUrl: item.audio_url || ''
              }));
              setRows(updatedRows);
              console.log('Updated rows with new audio URLs:', updatedRows);
            }

            // 更新本地狀態
            if (onUpdateContent) {
              onUpdateContent({
                ...editingContent,
                title,
                items,
                level,
                tags
              });
            }
          } catch (error) {
            console.error('Failed to update content:', error);
            toast.error('更新失敗，但音檔已生成');
          }
        }

        // 關閉 modal 但不要關閉 panel
        setTtsModalOpen(false);
        setSelectedRow(null);
      }
    }
  };

  const handleBatchGenerateTTS = async () => {
    try {
      // 收集需要生成 TTS 的文字
      const textsToGenerate = rows
        .filter(row => row.text && !row.audioUrl)
        .map(row => row.text);

      if (textsToGenerate.length === 0) {
        toast.info('所有項目都已有音檔');
        return;
      }

      toast.info(`正在生成 ${textsToGenerate.length} 個音檔...`);

      // 批次生成 TTS
      const result = await apiClient.batchGenerateTTS(
        textsToGenerate,
        'en-US-JennyNeural', // 預設使用美國女聲
        '+0%',
        '+0%'
      );

      if (result && typeof result === 'object' && 'audio_urls' in result && Array.isArray(result.audio_urls)) {
        // 更新 rows 的 audioUrl
        const newRows = [...rows];
        let audioIndex = 0;

        for (let i = 0; i < newRows.length; i++) {
          if (newRows[i].text && !newRows[i].audioUrl) {
            const audioUrl = (result as { audio_urls: string[] }).audio_urls[audioIndex];
            // 如果是相對路徑，加上 API base URL
            newRows[i].audioUrl = audioUrl.startsWith('http')
              ? audioUrl
              : `${import.meta.env.VITE_API_URL}${audioUrl}`;
            audioIndex++;
          }
        }

        setRows(newRows);

        // 立即更新 content 並儲存到後端（不要用 onSave 避免關閉 panel）
        const items = newRows.map(row => ({
          text: row.text,
          definition: row.definition,  // 中文翻譯
          translation: row.translation, // 英文釋義
          audio_url: row.audioUrl || '',
          selectedLanguage: row.selectedLanguage // 記錄最後選擇的語言
        }));

        // 新增模式：只更新本地狀態，不呼叫 API
        if (isCreating) {
          // 更新本地狀態
          if (onUpdateContent) {
            onUpdateContent({
              ...editingContent,
              title,
              items,
              level,
              tags
            });
          }

          toast.success(`成功生成 ${textsToGenerate.length} 個音檔！音檔將在儲存內容時一併上傳。`);
        } else {
          // 編輯模式：直接呼叫 API 更新
          try {
            const updateData = {
              title: title || editingContent?.title,
              items,
              level,
              tags
            };

            await apiClient.updateContent(editingContent?.id ?? 0, updateData);

            // 更新本地狀態
            if (onUpdateContent) {
              onUpdateContent({
                ...editingContent,
                title,
                items,
                level,
                tags
              });
            }

            toast.success(`成功生成並儲存 ${textsToGenerate.length} 個音檔！`);
          } catch (error) {
            console.error('Failed to save TTS:', error);
            toast.error('儲存失敗，但音檔已生成');
          }
        }
      }
    } catch (error) {
      console.error('Batch TTS generation failed:', error);
      toast.error('批次生成失敗，請重試');
    }
  };

  const handleGenerateSingleDefinition = async (index: number) => {
    const newRows = [...rows];
    const currentLang = newRows[index].selectedLanguage || 'chinese';
    return handleGenerateSingleDefinitionWithLang(index, currentLang);
  };

  const handleGenerateSingleDefinitionWithLang = async (index: number, targetLang: 'chinese' | 'english') => {
    const newRows = [...rows];
    if (!newRows[index].text) {
      toast.error('請先輸入文本');
      return;
    }

    toast.info(`生成翻譯中...`);
    try {
      const response = await apiClient.translateText(
        newRows[index].text,
        targetLang === 'chinese' ? 'zh-TW' : 'en'
      ) as { translation: string };

      // 根據目標語言寫入對應欄位，但不清空另一個欄位
      if (targetLang === 'chinese') {
        newRows[index].definition = response.translation;
      } else {
        newRows[index].translation = response.translation;
      }
      // 記錄最後選擇的語言
      newRows[index].selectedLanguage = targetLang;

      setRows(newRows);
      toast.success(`${targetLang === 'chinese' ? '中文翻譯' : '英文釋義'}生成完成`);
    } catch (error) {
      console.error('Translation error:', error);
      toast.error('翻譯失敗，請稍後再試');
    }
  };

  const handleBatchGenerateDefinitions = async () => {
    // 收集需要翻譯的項目（現在同時翻譯兩種語言）
    const itemsToTranslate: { index: number; text: string }[] = [];

    rows.forEach((row, index) => {
      if (row.text && (!row.definition || !row.translation)) {
        itemsToTranslate.push({ index, text: row.text });
      }
    });

    if (itemsToTranslate.length === 0) {
      toast.info('沒有需要翻譯的項目');
      return;
    }

    toast.info(`開始批次生成翻譯...`);
    const newRows = [...rows];

    try {
      // 收集需要中文翻譯的項目
      const needsChinese = itemsToTranslate.filter(item => !newRows[item.index].definition);
      // 收集需要英文翻譯的項目
      const needsEnglish = itemsToTranslate.filter(item => !newRows[item.index].translation);

      // 批次處理中文翻譯
      if (needsChinese.length > 0) {
        const chineseTexts = needsChinese.map(item => item.text);
        const chineseResponse = await apiClient.batchTranslate(chineseTexts, 'zh-TW');
        const chineseTranslations = (chineseResponse as { translations?: string[] }).translations || [];

        needsChinese.forEach((item, idx) => {
          newRows[item.index].definition = chineseTranslations[idx] || item.text;
          // 不清空英文欄位，保留兩種語言
        });
      }

      // 批次處理英文釋義
      if (needsEnglish.length > 0) {
        const englishTexts = needsEnglish.map(item => item.text);
        const englishResponse = await apiClient.batchTranslate(englishTexts, 'en');
        const englishTranslations = (englishResponse as { translations?: string[] }).translations || [];

        needsEnglish.forEach((item, idx) => {
          newRows[item.index].translation = englishTranslations[idx] || item.text;
          // 不清空中文欄位，保留兩種語言
        });
      }

      // 批次翻譯時預設使用中文
      itemsToTranslate.forEach(item => {
        if (!newRows[item.index].selectedLanguage) {
          newRows[item.index].selectedLanguage = 'chinese';
        }
      });

      setRows(newRows);
      toast.success(`批次翻譯完成！處理了 ${itemsToTranslate.length} 個項目`);
    } catch (error) {
      console.error('Batch translation error:', error);
      toast.error('批次翻譯失敗，請稍後再試');
    }
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">載入中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-200px)]">
      {/* Fixed Header Section */}
      <div className="flex-shrink-0 space-y-4 pb-4">
        {/* Title Input - Only show in create mode */}
        {isCreating && (
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              標題 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="請輸入內容標題"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        {/* Batch Actions - RWD adjusted */}
        <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleBatchGenerateTTS}
          className="bg-yellow-100 hover:bg-yellow-200 border-yellow-300"
          title="使用免費的 Microsoft Edge TTS 生成語音"
        >
          <Volume2 className="h-4 w-4 mr-1" />
          批次生成TTS
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleBatchGenerateDefinitions()}
          className="bg-green-100 hover:bg-green-200 border-green-300"
          title="批次生成翻譯（根據各行語言設定）"
        >
          <Globe className="h-4 w-4 mr-1" />
          批次生成翻譯
        </Button>
        </div>
      </div>

      {/* Scrollable Content Rows */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {rows.map((row, index) => (
          <div
            key={row.id}
            className="flex flex-col sm:flex-row items-start sm:items-center gap-2 p-3 bg-gray-50 rounded-lg"
            draggable
            onDragStart={() => handleDragStart(index)}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, index)}
          >
            <div className="flex items-center gap-1 w-full sm:w-auto">
              <GripVertical className="h-5 w-5 text-gray-400 cursor-move" />
              <span className="text-sm font-medium text-gray-600 w-6">
                {index + 1}
              </span>
            </div>

            <div className="flex-1 w-full space-y-2">
              <div className="relative">
                <input
                  type="text"
                  value={row.text}
                  onChange={(e) => handleUpdateRow(index, 'text', e.target.value)}
                  className="w-full px-3 py-2 pr-20 border rounded-md text-sm"
                  placeholder="輸入文本"
                  maxLength={200}
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-1">
                  {/* 如果有音檔，顯示播放按鈕 */}
                  {row.audioUrl && (
                    <button
                      onClick={() => {
                        if (!row.audioUrl) {
                          toast.error('沒有音檔可播放');
                          return;
                        }

                        console.log('Playing audio:', row.audioUrl);
                        const audio = new Audio(row.audioUrl);

                        audio.onerror = (e) => {
                          console.error('Audio playback error:', e);
                          toast.error('音檔播放失敗，請檢查音檔格式');
                        };

                        audio.play().catch(error => {
                          console.error('Play failed:', error);
                          toast.error('無法播放音檔');
                        });
                      }}
                      className="p-1 rounded text-green-600 hover:bg-green-100"
                      title="播放音檔"
                    >
                      <Play className="h-4 w-4" />
                    </button>
                  )}
                  {/* TTS/錄音按鈕 */}
                  <button
                    onClick={() => handleOpenTTSModal(row)}
                    className={`p-1 rounded ${
                      row.audioUrl ? 'text-blue-600 hover:bg-blue-100' : 'text-gray-600 bg-yellow-100 hover:bg-yellow-200'
                    }`}
                    title={row.audioUrl ? '重新錄製/生成' : '開啟 TTS/錄音'}
                  >
                    <Mic className="h-4 w-4" />
                  </button>
                  {/* 移除音檔按鈕 - 只在有音檔時顯示 */}
                  {row.audioUrl && (
                    <button
                      onClick={() => handleRemoveAudio(index)}
                      className="p-1 rounded text-red-600 hover:bg-red-100"
                      title="移除音檔"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                {/* 翻譯欄位 */}
                <div className="relative">
                  <textarea
                    value={(row.selectedLanguage || 'chinese') === 'chinese' ? (row.definition || '') : (row.translation || '')}
                    onChange={(e) => handleUpdateRow(index, (row.selectedLanguage || 'chinese') === 'chinese' ? 'definition' : 'translation', e.target.value)}
                    className="w-full px-3 py-2 pr-20 border rounded-md text-sm resize-none"
                    placeholder={(row.selectedLanguage || 'chinese') === 'chinese' ? '中文翻譯' : '英文釋義'}
                    rows={1}
                  />
                  {/* 右側對齊的選單和按鈕 */}
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    <select
                      value={row.selectedLanguage || 'chinese'}
                      onChange={async (e) => {
                        const newLang = e.target.value as 'chinese' | 'english';
                        handleUpdateRow(index, 'selectedLanguage', newLang);
                        // 只有在目標欄位為空時才自動翻譯，避免覆蓋用戶手動輸入的內容
                        if (row.text) {
                          const targetFieldEmpty = newLang === 'chinese' ? !row.definition : !row.translation;
                          if (targetFieldEmpty) {
                            setTimeout(() => {
                              handleGenerateSingleDefinitionWithLang(index, newLang);
                            }, 100);
                          }
                        }
                      }}
                      className="px-1 py-0.5 border rounded text-xs bg-white"
                    >
                      <option value="chinese">中文翻譯</option>
                      <option value="english">英文釋義</option>
                    </select>
                    <button
                      onClick={() => handleGenerateSingleDefinition(index)}
                      className="p-1 rounded hover:bg-gray-200 text-gray-600 flex items-center gap-0.5"
                      title={`生成${(row.selectedLanguage || 'chinese') === 'chinese' ? '中文翻譯' : '英文釋義'}`}
                    >
                      <Globe className="h-4 w-4" />
                      <span className="text-xs">{(row.selectedLanguage || 'chinese') === 'chinese' ? '中' : 'EN'}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1 w-full sm:w-auto justify-end">
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

        {/* Add Row Button */}
        <button
          onClick={handleAddRow}
          className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 flex items-center justify-center gap-2 text-gray-600 hover:text-blue-600"
          disabled={rows.length >= 15}
        >
          <Plus className="h-5 w-5" />
          新增項目
        </button>
      </div>

      {/* Fixed Footer Section */}
      <div className="flex-shrink-0 space-y-4 pt-3 border-t mt-4">
        <div className="flex flex-col sm:flex-row gap-4">
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

          <div className="flex items-center gap-2 flex-1">
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
              className="px-3 py-1 border rounded-md flex-1"
              placeholder="按 Enter 新增標籤"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isPublicEdit"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
              className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
            <label htmlFor="isPublicEdit" className="text-sm font-medium text-gray-700 whitespace-nowrap">
              公開內容
            </label>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
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

      {/* TTS Modal */}
      {selectedRow && (
        <TTSModal
          open={ttsModalOpen}
          onClose={() => setTtsModalOpen(false)}
          row={selectedRow}
          onConfirm={handleTTSConfirm}
          contentId={editingContent?.id}
          itemIndex={rows.findIndex(r => r.id === selectedRow.id)}
          isCreating={isCreating}
        />
      )}

      {/* 底部按鈕（新增模式時顯示） */}
      {isCreating && (
        <div className="flex justify-end gap-2 mt-6 pt-6 border-t">
          <Button
            variant="outline"
            onClick={onCancel}
          >
            取消
          </Button>
          <Button
            onClick={async () => {
              // 檢查必填欄位
              if (!title) {
                toast.error('請輸入標題');
                return;
              }

              // 過濾掉空白的項目，只保留有文字的
              const validRows = rows.filter(r => r.text && r.text.trim());

              if (validRows.length === 0) {
                toast.error('請至少填寫一個項目的文字');
                return;
              }

              // 收集有效的資料
              /*const items = validRows.map(row => ({
                text: row.text.trim(),
                translation: row.definition.trim(),
                audio_url: row.audioUrl || ''
              }));*/

              // Prepare content data for callback
            /*const contentData = {
                title,
                items,
                level,
                tags,
                target_wpm: 60,
                target_accuracy: 0.8,
                time_limit_seconds: 180,
                is_public: isPublic
              };*/

              // 準備要儲存的資料
              const saveData = {
                title: title,
                items: validRows.map(row => ({
                  text: row.text.trim(),
                  definition: row.definition || '',  // 中文翻譯
                  english_definition: row.translation || '',  // 英文釋義
                  translation: row.definition || '',  // 主要翻譯欄位（保持向後兼容）
                  selectedLanguage: row.selectedLanguage || 'chinese',  // 記錄選擇的語言
                  audio_url: row.audioUrl || row.audio_url || ''
                })),
                target_wpm: 60,
                target_accuracy: 0.8,
                time_limit_seconds: 180
              };

              console.log('Saving data:', saveData);

              // 如果是創建模式，需要呼叫 API 創建內容
              if (isCreating && lessonId) {
                try {
                  await apiClient.createContent(lessonId, {
                    type: 'reading_assessment',
                    ...saveData
                  });
                  toast.success('內容已成功創建');
                  // 呼叫 onSave 關閉對話框
                  if (onSave) {
                    await (onSave as () => void | Promise<void>)();
                  }
                } catch (error) {
                  console.error('Failed to create content:', error);
                  toast.error('創建內容失敗');
                }
              } else if (onSave) {
                // 編輯模式，呼叫 onSave
                try {
                  await (onSave as () => void | Promise<void>)();
                  toast.success('儲存成功');
                } catch (error) {
                  console.error('Save error:', error);
                  toast.error('儲存失敗');
                }
              }
            }}
          >
            儲存
          </Button>
        </div>
      )}
    </div>
  );
}
