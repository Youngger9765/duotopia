import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Mic,
  Volume2,
  GripVertical,
  Copy,
  Trash2,
  Plus,
  Globe,
  Play,
  Square,
  RefreshCw,
  Clipboard,
} from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api";
import { retryAudioUpload } from "@/utils/retryHelper";
// dnd-kit imports
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

// 詞性列表
// value 用全名存資料庫，label 用縮寫顯示
const PARTS_OF_SPEECH = [
  { value: "noun", label: "n.", fullName: "noun" },
  { value: "verb", label: "v.", fullName: "verb" },
  { value: "adjective", label: "adj.", fullName: "adjective" },
  { value: "adverb", label: "adv.", fullName: "adverb" },
  { value: "pronoun", label: "pron.", fullName: "pronoun" },
  { value: "preposition", label: "prep.", fullName: "preposition" },
  { value: "conjunction", label: "conj.", fullName: "conjunction" },
  { value: "interjection", label: "interj.", fullName: "interjection" },
  { value: "determiner", label: "det.", fullName: "determiner" },
  { value: "auxiliary", label: "aux.", fullName: "auxiliary" },
] as const;

// 單字翻譯語言選項（含英文）
type WordTranslationLanguage = "chinese" | "english" | "japanese" | "korean";

const WORD_TRANSLATION_LANGUAGES = [
  { value: "chinese" as const, label: "中文", code: "zh-TW" },
  { value: "english" as const, label: "英文", code: "en" },
  { value: "japanese" as const, label: "日文", code: "ja" },
  { value: "korean" as const, label: "韓文", code: "ko" },
];

// 例句翻譯語言選項（不含英文）
type SentenceTranslationLanguage = "chinese" | "japanese" | "korean";

const SENTENCE_TRANSLATION_LANGUAGES = [
  { value: "chinese" as const, label: "中文", code: "zh-TW" },
  { value: "japanese" as const, label: "日文", code: "ja" },
  { value: "korean" as const, label: "韓文", code: "ko" },
];

interface ContentRow {
  id: string | number;
  text: string;
  definition: string; // 中文翻譯
  audioUrl?: string;
  audio_url?: string;
  translation?: string; // 英文釋義
  japanese_translation?: string; // 日文翻譯
  korean_translation?: string; // 韓文翻譯
  selectedWordLanguage?: WordTranslationLanguage; // 單字翻譯語言
  selectedSentenceLanguage?: SentenceTranslationLanguage; // 例句翻譯語言
  partsOfSpeech?: string[]; // 詞性陣列（可複選）
  audioSettings?: {
    accent: string;
    gender: string;
    speed: string;
  };
  // Example sentence fields
  example_sentence?: string;
  example_sentence_translation?: string; // 例句中文翻譯
  example_sentence_japanese?: string; // 例句日文翻譯
  example_sentence_korean?: string; // 例句韓文翻譯
}

interface TTSModalProps {
  open: boolean;
  onClose: () => void;
  row: ContentRow;
  onConfirm: (
    audioUrl: string,
    settings: {
      accent?: string;
      gender?: string;
      speed?: string;
      source?: string;
      audioBlob?: Blob | null;
    },
  ) => void;
  contentId?: number;
  itemIndex?: number;
  isCreating?: boolean; // 是否為新增模式
}

const TTSModal = ({
  open,
  onClose,
  row,
  onConfirm,
  contentId,
  itemIndex,
  isCreating = false,
}: TTSModalProps) => {
  const [text, setText] = useState(row.text);
  const [accent, setAccent] = useState(
    row.audioSettings?.accent || "American English",
  );
  const [gender, setGender] = useState(row.audioSettings?.gender || "Male");
  const [speed, setSpeed] = useState(row.audioSettings?.speed || "Normal x1");
  const [audioUrl, setAudioUrl] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState<string>("");
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [showAudioAnimation, setShowAudioAnimation] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedSource, setSelectedSource] = useState<
    "tts" | "recording" | null
  >(null);
  const [activeTab, setActiveTab] = useState<string>("generate");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const audioBlobRef = useRef<Blob | null>(null);
  const recordingDurationRef = useRef<number>(0);

  const accents = [
    "American English",
    "British English",
    "Indian English",
    "Australian English",
  ];
  const genders = ["Male", "Female"];
  const speeds = ["Slow x0.75", "Normal x1", "Fast x1.5"];

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
      let voice = "en-US-JennyNeural"; // 預設美國女聲

      if (accent === "American English") {
        voice =
          gender === "Male" ? "en-US-ChristopherNeural" : "en-US-JennyNeural";
      } else if (accent === "British English") {
        voice = gender === "Male" ? "en-GB-RyanNeural" : "en-GB-SoniaNeural";
      } else if (accent === "Australian English") {
        voice =
          gender === "Male" ? "en-AU-WilliamNeural" : "en-AU-NatashaNeural";
      }

      // 轉換速度設定
      let rate = "+0%";
      if (speed === "Slow x0.75") rate = "-25%";
      else if (speed === "Fast x1.5") rate = "+50%";

      const result = await apiClient.generateTTS(text, voice, rate, "+0%");

      if (result?.audio_url) {
        // 如果是相對路徑，加上 API base URL
        const fullUrl = result.audio_url.startsWith("http")
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

        toast.success("音檔生成成功！點擊播放按鈕試聽");
      }
    } catch (err) {
      console.error("TTS generation failed:", err);
      toast.error("生成失敗，請重試");
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
      let mimeType = "audio/webm";
      const possibleTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/ogg",
        "audio/mp4",
      ];

      for (const type of possibleTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          mimeType = type;
          break;
        }
      }

      console.log("Using MIME type:", mimeType);
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000, // 設定位元率
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      setRecordingDuration(0);

      // 設定計時器
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration((prev) => {
          const newDuration = prev + 1;
          // 30秒自動停止
          if (newDuration >= 30) {
            handleStopRecording();
            toast.info("已達到最長錄音時間 30 秒");
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
        const basicMimeType = mimeType.split(";")[0];
        const audioBlob = new Blob(audioChunksRef.current, {
          type: basicMimeType,
        });

        // 使用 ref 來獲取當前的錄音時長
        const currentDuration =
          recordingDurationRef.current || recordingDuration;

        // 檢查檔案大小 (2MB 限制)
        if (audioBlob.size > 2 * 1024 * 1024) {
          toast.error("錄音檔案太大，請縮短錄音時間");
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        // 確保有錄音資料
        if (audioBlob.size === 0) {
          toast.error("錄音失敗，請檢查麥克風權限");
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        // 儲存 blob 以便之後上傳
        audioBlobRef.current = audioBlob;
        recordingDurationRef.current = currentDuration;

        // 創建本地 URL 供預覽播放
        const localUrl = URL.createObjectURL(audioBlob);
        setRecordedAudio(localUrl);
        toast.success("錄音完成！可以試聽或重新錄製");

        stream.getTracks().forEach((track) => track.stop());
      };

      // 使用 timeslice 參數，每100ms收集一次數據
      mediaRecorder.start(100);
      setIsRecording(true);
      toast.success("開始錄音");
    } catch {
      toast.error("無法啟動錄音，請檢查麥克風權限");
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
        toast.warning("請選擇要使用的音源（TTS 或錄音）");
        return;
      }

      // 新增模式：不上傳，只傳遞本地 URL
      if (isCreating) {
        const finalUrl = selectedSource === "tts" ? audioUrl : recordedAudio;
        onConfirm(finalUrl, {
          accent,
          gender,
          speed,
          source: selectedSource,
          audioBlob:
            selectedSource === "recording" ? audioBlobRef.current : null,
        });
        onClose();
        return;
      }

      // 編輯模式：如果選擇錄音且還沒上傳（URL 是 blob:// 開頭），現在上傳
      if (
        selectedSource === "recording" &&
        recordedAudio.startsWith("blob:") &&
        audioBlobRef.current
      ) {
        setIsUploading(true);
        try {
          const result = await retryAudioUpload(
            () =>
              apiClient.uploadAudio(
                audioBlobRef.current!,
                recordingDurationRef.current || 1,
                Number(contentId),
                Number(itemIndex),
              ),
            (attempt, error) => {
              toast.warning(`上傳失敗，正在重試... (第 ${attempt}/3 次)`);
              console.error(`Upload attempt ${attempt} failed:`, error);
            },
          );

          if (result && result.audio_url) {
            onConfirm(result.audio_url, {
              accent,
              gender,
              speed,
              source: "recording",
            });
            onClose();
          } else {
            throw new Error("No audio URL returned");
          }
        } catch (err) {
          console.error("Upload failed after retries:", err);
          toast.error("上傳失敗，請檢查網路連線後重試");
        } finally {
          setIsUploading(false);
        }
        return;
      }

      const finalUrl = selectedSource === "tts" ? audioUrl : recordedAudio;
      onConfirm(finalUrl, { accent, gender, speed, source: selectedSource });
    } else {
      // 只有一種音源
      const finalAudioUrl = recordedAudio || audioUrl;
      if (!finalAudioUrl) {
        toast.error("請先生成或錄製音檔");
        return;
      }

      // 新增模式：不上傳，只傳遞本地 URL
      if (isCreating) {
        const source = recordedAudio ? "recording" : "tts";
        onConfirm(finalAudioUrl, {
          accent,
          gender,
          speed,
          source,
          audioBlob: source === "recording" ? audioBlobRef.current : null,
        });
        onClose();
        return;
      }

      // 編輯模式：如果是錄音且還沒上傳，現在上傳
      if (
        recordedAudio &&
        recordedAudio.startsWith("blob:") &&
        audioBlobRef.current
      ) {
        setIsUploading(true);
        try {
          const result = await retryAudioUpload(
            () =>
              apiClient.uploadAudio(
                audioBlobRef.current!,
                recordingDurationRef.current || 1,
                Number(contentId),
                Number(itemIndex),
              ),
            (attempt, error) => {
              toast.warning(`上傳失敗，正在重試... (第 ${attempt}/3 次)`);
              console.error(`Upload attempt ${attempt} failed:`, error);
            },
          );

          if (result && result.audio_url) {
            onConfirm(result.audio_url, {
              accent,
              gender,
              speed,
              source: "recording",
            });
            onClose();
          } else {
            throw new Error("No audio URL returned");
          }
        } catch (err) {
          console.error("Upload failed after retries:", err);
          toast.error("上傳失敗，請檢查網路連線後重試");
        } finally {
          setIsUploading(false);
        }
        return;
      }

      const source = recordedAudio ? "recording" : "tts";
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

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-gray-100 p-1 rounded-lg">
            <TabsTrigger
              value="generate"
              className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md transition-all"
            >
              <Volume2 className="h-4 w-4 mr-1" />
              Generate
              {audioUrl && <span className="ml-1 text-xs">✓</span>}
            </TabsTrigger>
            <TabsTrigger
              value="record"
              className="data-[state=active]:bg-red-500 data-[state=active]:text-white rounded-md transition-all"
            >
              <Mic className="h-4 w-4 mr-1" />
              Record
              {recordedAudio && <span className="ml-1 text-xs">✓</span>}
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
                {accents.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
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
                  {genders.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
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
                  {speeds.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="flex-1 bg-yellow-500 hover:bg-yellow-600 dark:bg-yellow-400 dark:hover:bg-yellow-500 text-black"
                title="使用免費的 Microsoft Edge TTS 生成語音"
              >
                {isGenerating ? "Generating..." : "Generate"}
              </Button>
              {audioUrl && (
                <Button
                  variant="outline"
                  onClick={handlePlayAudio}
                  size="icon"
                  className={`
                    border-2 transition-all duration-300
                    ${
                      showAudioAnimation
                        ? "border-green-500 bg-green-50 animate-bounce scale-110"
                        : "border-gray-300 hover:border-green-500 hover:bg-green-50"
                    }
                  `}
                  title="播放生成的音檔"
                >
                  <Play
                    className={`h-4 w-4 ${showAudioAnimation ? "text-green-600" : "text-gray-600"}`}
                  />
                </Button>
              )}
            </div>

            {/* 音檔生成成功提示與管理 */}
            {audioUrl && (
              <div
                className={`mt-3 p-3 border rounded-lg transition-all duration-300 ${
                  showAudioAnimation
                    ? "bg-green-50 border-green-200 animate-pulse"
                    : "bg-gray-50 border-gray-200"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-gray-700">
                    {showAudioAnimation && (
                      <div className="flex items-center gap-1">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <div
                          className="w-2 h-2 bg-green-500 rounded-full animate-pulse"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-green-500 rounded-full animate-pulse"
                          style={{ animationDelay: "0.4s" }}
                        ></div>
                      </div>
                    )}
                    <Volume2 className="h-4 w-4 text-gray-600" />
                    <span className="text-sm font-medium">
                      {showAudioAnimation
                        ? "音檔已生成！點擊播放按鈕試聽"
                        : "TTS 音檔已準備"}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setAudioUrl("");
                      setSelectedSource(null);
                      toast.info("已刪除 TTS 音檔");
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
                <div
                  className={`w-24 h-24 rounded-full flex items-center justify-center ${
                    isRecording ? "bg-red-100 animate-pulse" : "bg-gray-100"
                  }`}
                >
                  <Mic
                    className={`h-12 w-12 ${isRecording ? "text-red-600" : "text-gray-600"}`}
                  />
                </div>
              </div>

              {/* 顯示錄音時間 */}
              {isRecording && (
                <div className="mb-4 text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {Math.floor(recordingDuration / 60)
                      .toString()
                      .padStart(2, "0")}
                    :{(recordingDuration % 60).toString().padStart(2, "0")} /
                    00:30
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
                <Button
                  onClick={handleStopRecording}
                  variant="destructive"
                  size="lg"
                >
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
                              toast.error("沒有錄音可播放");
                              return;
                            }

                            const audio = new Audio(recordedAudio);
                            audio.play().catch((err) => {
                              console.error("Play failed:", err);
                              toast.error("無法播放錄音");
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
                          setRecordedAudio("");
                          setSelectedSource(null);
                          audioBlobRef.current = null;
                          setRecordingDuration(0);
                          recordingDurationRef.current = 0;
                          toast.info("已刪除錄音檔案");
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
                onClick={() => setSelectedSource("tts")}
                className={`p-3 rounded-lg border-2 transition-all ${
                  selectedSource === "tts"
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-300 bg-white hover:border-gray-400"
                }`}
              >
                <Volume2
                  className={`h-5 w-5 mx-auto mb-1 ${
                    selectedSource === "tts" ? "text-blue-600" : "text-gray-600"
                  }`}
                />
                <div className="text-sm font-medium">TTS 語音</div>
                <div className="text-xs text-gray-500">AI 生成</div>
              </button>

              <button
                onClick={() => setSelectedSource("recording")}
                className={`p-3 rounded-lg border-2 transition-all ${
                  selectedSource === "recording"
                    ? "border-red-500 bg-red-50"
                    : "border-gray-300 bg-white hover:border-gray-400"
                }`}
              >
                <Mic
                  className={`h-5 w-5 mx-auto mb-1 ${
                    selectedSource === "recording"
                      ? "text-red-600"
                      : "text-gray-600"
                  }`}
                />
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
          <Button onClick={handleConfirm}>Confirm</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// SortableRowInner component with complete functionality
interface SortableRowInnerProps {
  row: ContentRow;
  index: number;
  handleUpdateRow: (
    index: number,
    field: keyof ContentRow,
    value: string | string[],
  ) => void;
  handleRemoveRow: (index: number) => void;
  handleDuplicateRow: (index: number) => void;
  handleOpenTTSModal: (row: ContentRow) => void;
  handleRemoveAudio: (index: number) => void;
  handleGenerateSingleDefinition: (index: number) => Promise<void>;
  handleGenerateSingleDefinitionWithLang: (
    index: number,
    lang: WordTranslationLanguage,
  ) => Promise<void>;
  handleGenerateExampleTranslation: (index: number) => Promise<void>;
  handleGenerateExampleTranslationWithLang: (
    index: number,
    lang: SentenceTranslationLanguage,
  ) => Promise<void>;
  handleOpenAIGenerateModal: (index: number) => void;
  rowsLength: number;
}

function SortableRowInner({
  row,
  index,
  handleUpdateRow,
  handleRemoveRow,
  handleDuplicateRow,
  handleOpenTTSModal,
  handleRemoveAudio,
  handleGenerateSingleDefinition,
  handleGenerateSingleDefinitionWithLang,
  handleGenerateExampleTranslation,
  handleGenerateExampleTranslationWithLang,
  handleOpenAIGenerateModal,
  rowsLength,
}: SortableRowInnerProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: row.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  // 處理詞性切換
  const handleTogglePartOfSpeech = (pos: string) => {
    const currentPOS = row.partsOfSpeech || [];
    const newPOS = currentPOS.includes(pos)
      ? currentPOS.filter((p) => p !== pos)
      : [...currentPOS, pos];
    handleUpdateRow(index, "partsOfSpeech", newPOS);
  };

  return (
    <div ref={setNodeRef} style={style} className="p-4 bg-gray-50 rounded-lg">
      {/* 頂部：拖曳手把 + 序號 + 動作按鈕 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {/* Drag handle */}
          <div
            {...attributes}
            {...listeners}
            className="cursor-grab active:cursor-grabbing touch-none"
            title="拖曳以重新排序"
          >
            <GripVertical className="h-5 w-5 text-gray-400 hover:text-gray-700 transition-colors" />
          </div>
          <span className="text-sm font-medium text-gray-600">{index + 1}</span>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1">
          {/* Audio controls */}
          {row.audioUrl && (
            <button
              onClick={() => {
                if (!row.audioUrl) {
                  toast.error("沒有音檔可播放");
                  return;
                }
                const audio = new Audio(row.audioUrl);
                audio.onerror = (e) => {
                  console.error("Audio playback error:", e);
                  toast.error("音檔播放失敗，請檢查音檔格式");
                };
                audio.play().catch((error) => {
                  console.error("Play failed:", error);
                  toast.error("無法播放音檔");
                });
              }}
              className="p-1.5 rounded text-green-600 hover:bg-green-100"
              title="播放音檔"
            >
              <Play className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={() => handleOpenTTSModal(row)}
            className={`p-1.5 rounded ${
              row.audioUrl
                ? "text-blue-600 hover:bg-blue-100"
                : "text-gray-600 bg-yellow-100 hover:bg-yellow-200"
            }`}
            title={row.audioUrl ? "重新錄製/生成" : "開啟 TTS/錄音"}
          >
            <Mic className="h-4 w-4" />
          </button>
          {row.audioUrl && (
            <button
              onClick={() => handleRemoveAudio(index)}
              className="p-1.5 rounded text-red-600 hover:bg-red-100"
              title="移除音檔"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
          <div className="w-px h-4 bg-gray-300 mx-1" />
          <button
            onClick={() => handleDuplicateRow(index)}
            className="p-1.5 rounded hover:bg-gray-200"
            title="複製"
          >
            <Copy className="h-4 w-4 text-gray-600" />
          </button>
          <button
            onClick={() => handleRemoveRow(index)}
            className="p-1.5 rounded hover:bg-gray-200"
            title="刪除"
            disabled={rowsLength <= 1}
          >
            <Trash2
              className={`h-4 w-4 ${rowsLength <= 1 ? "text-gray-300" : "text-gray-600"}`}
            />
          </button>
        </div>
      </div>

      {/* 第一列：英文單字 + 翻譯（同一列，flex-wrap） */}
      <div className="flex flex-wrap gap-2 mb-3">
        {/* 英文單字 input - 限制 50 字元 */}
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            value={row.text}
            onChange={(e) => handleUpdateRow(index, "text", e.target.value)}
            className="w-full px-3 py-2 border rounded-md text-sm"
            placeholder="輸入英文單字"
            maxLength={50}
          />
        </div>

        {/* 翻譯 input */}
        <div className="flex-1 min-w-[200px] relative">
          <input
            type="text"
            value={(() => {
              const lang = row.selectedWordLanguage || "chinese";
              if (lang === "chinese") return row.definition || "";
              if (lang === "english") return row.translation || "";
              if (lang === "japanese") return row.japanese_translation || "";
              if (lang === "korean") return row.korean_translation || "";
              return row.definition || "";
            })()}
            onChange={(e) => {
              const lang = row.selectedWordLanguage || "chinese";
              let field: keyof ContentRow = "definition";
              if (lang === "english") field = "translation";
              else if (lang === "japanese") field = "japanese_translation";
              else if (lang === "korean") field = "korean_translation";
              handleUpdateRow(index, field, e.target.value);
            }}
            className="w-full px-3 py-2 pr-24 border rounded-md text-sm"
            placeholder={`${WORD_TRANSLATION_LANGUAGES.find((l) => l.value === (row.selectedWordLanguage || "chinese"))?.label || "中文"}翻譯(非必填)`}
            maxLength={200}
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-1">
            <select
              value={row.selectedWordLanguage || "chinese"}
              onChange={(e) => {
                const newLang = e.target.value as WordTranslationLanguage;
                handleUpdateRow(index, "selectedWordLanguage", newLang);
                // Auto-generate when switching language if text exists
                if (row.text && row.text.trim()) {
                  setTimeout(() => {
                    handleGenerateSingleDefinitionWithLang(index, newLang);
                  }, 100);
                }
              }}
              className="px-1 py-0.5 border rounded text-xs bg-white"
            >
              {WORD_TRANSLATION_LANGUAGES.map((lang) => (
                <option key={lang.value} value={lang.value}>
                  {lang.label}
                </option>
              ))}
            </select>
            <button
              onClick={() => handleGenerateSingleDefinition(index)}
              className="p-1 rounded hover:bg-gray-200 text-gray-600"
              title={`AI 生成${WORD_TRANSLATION_LANGUAGES.find((l) => l.value === (row.selectedWordLanguage || "chinese"))?.label || "中文"}翻譯`}
            >
              <Globe className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 第二列：詞性選擇 Chips */}
      <div className="flex flex-wrap gap-2 mb-3">
        {PARTS_OF_SPEECH.map((pos) => {
          const isSelected = (row.partsOfSpeech || []).includes(pos.value);
          return (
            <button
              key={pos.value}
              onClick={() => handleTogglePartOfSpeech(pos.value)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                isSelected
                  ? "bg-gradient-to-r from-cyan-400 to-teal-400 text-white shadow-sm"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
              title={pos.fullName}
            >
              {pos.label}
            </button>
          );
        })}
      </div>

      {/* 第三列：例句輸入（帶 AI 按鈕） */}
      <div className="relative mb-2">
        <input
          type="text"
          value={row.example_sentence || ""}
          onChange={(e) =>
            handleUpdateRow(index, "example_sentence", e.target.value)
          }
          className="w-full px-3 py-2 pr-12 border rounded-md text-sm"
          placeholder="輸入英文例句"
          maxLength={500}
        />
        <button
          onClick={() => handleOpenAIGenerateModal(index)}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-blue-100 text-blue-600 border border-blue-300"
          title="AI 生成例句"
        >
          <span className="text-xs font-medium">AI</span>
        </button>
      </div>

      {/* 第四列：例句翻譯 */}
      <div className="relative">
        <input
          type="text"
          value={(() => {
            const lang = row.selectedSentenceLanguage || "chinese";
            if (lang === "chinese")
              return row.example_sentence_translation || "";
            if (lang === "japanese") return row.example_sentence_japanese || "";
            if (lang === "korean") return row.example_sentence_korean || "";
            return row.example_sentence_translation || "";
          })()}
          onChange={(e) => {
            const lang = row.selectedSentenceLanguage || "chinese";
            let field: keyof ContentRow = "example_sentence_translation";
            if (lang === "japanese") field = "example_sentence_japanese";
            else if (lang === "korean") field = "example_sentence_korean";
            handleUpdateRow(index, field, e.target.value);
          }}
          className="w-full px-3 py-2 pr-24 border rounded-md text-sm"
          placeholder={`${SENTENCE_TRANSLATION_LANGUAGES.find((l) => l.value === (row.selectedSentenceLanguage || "chinese"))?.label || "中文"}翻譯(非必須)`}
          maxLength={500}
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-1">
          <select
            value={row.selectedSentenceLanguage || "chinese"}
            onChange={(e) => {
              const newLang = e.target.value as SentenceTranslationLanguage;
              handleUpdateRow(index, "selectedSentenceLanguage", newLang);
              // Auto-generate when switching language if example sentence exists
              if (row.example_sentence && row.example_sentence.trim()) {
                setTimeout(() => {
                  handleGenerateExampleTranslationWithLang(index, newLang);
                }, 100);
              }
            }}
            className="px-1 py-0.5 border rounded text-xs bg-white"
          >
            {SENTENCE_TRANSLATION_LANGUAGES.map((lang) => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
          {row.example_sentence && row.example_sentence.trim() && (
            <button
              onClick={() => handleGenerateExampleTranslation(index)}
              className="p-1 rounded hover:bg-gray-200 text-gray-600"
              title={`AI 生成${SENTENCE_TRANSLATION_LANGUAGES.find((l) => l.value === (row.selectedSentenceLanguage || "chinese"))?.label || "中文"}例句翻譯`}
            >
              <Globe className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface SentenceMakingPanelProps {
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

export default function SentenceMakingPanel({
  content,
  editingContent,
  onUpdateContent,
  onSave,
  lessonId,
  isCreating = false,
}: SentenceMakingPanelProps) {
  const [title, setTitle] = useState("句子模組內容");
  const [rows, setRows] = useState<ContentRow[]>([
    {
      id: "1",
      text: "",
      definition: "",
      translation: "",
      selectedWordLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
    },
    {
      id: "2",
      text: "",
      definition: "",
      translation: "",
      selectedWordLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
    },
    {
      id: "3",
      text: "",
      definition: "",
      translation: "",
      selectedWordLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
    },
  ]);
  const [selectedRow, setSelectedRow] = useState<ContentRow | null>(null);
  const [ttsModalOpen, setTtsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [batchPasteDialogOpen, setBatchPasteDialogOpen] = useState(false);
  const [batchPasteText, setBatchPasteText] = useState("");
  const [batchPasteAutoTTS, setBatchPasteAutoTTS] = useState(false);
  const [batchPasteAutoTranslate, setBatchPasteAutoTranslate] = useState(false);

  // AI 生成例句對話框狀態
  const [aiGenerateModalOpen, setAiGenerateModalOpen] = useState(false);
  const [aiGenerateTargetIndex, setAiGenerateTargetIndex] = useState<
    number | null
  >(null); // null 表示批次生成
  const [aiGenerateLevel, setAiGenerateLevel] = useState<string>("A1");
  const [aiGeneratePrompt, setAiGeneratePrompt] = useState("");
  const [aiGenerateTranslate, setAiGenerateTranslate] = useState(true);
  const [aiGenerateTranslateLang, setAiGenerateTranslateLang] =
    useState<string>("中文");
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);

  // dnd-kit sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement required to start drag
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

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
      const data = (await apiClient.getContentDetail(content.id)) as {
        title?: string;
        items?: Array<{
          text?: string;
          translation?: string;
          definition?: string;
          audio_url?: string;
        }>;
        level?: string;
        tags?: string[];
        is_public?: boolean;
        audio_urls?: string[];
      };
      setTitle(data.title || "");

      // Convert items to rows format
      if (data.items && Array.isArray(data.items)) {
        const convertedRows = data.items.map(
          (
            item: {
              text?: string;
              translation?: string;
              definition?: string;
              english_definition?: string;
              japanese_translation?: string;
              korean_translation?: string;
              audio_url?: string;
              selectedWordLanguage?: WordTranslationLanguage;
              selectedSentenceLanguage?: SentenceTranslationLanguage;
              example_sentence?: string;
              example_sentence_translation?: string;
              example_sentence_japanese?: string;
              example_sentence_korean?: string;
              parts_of_speech?: string[];
            },
            index: number,
          ) => ({
            id: (index + 1).toString(),
            text: item.text || "",
            definition: item.definition || "", // 中文翻譯
            translation: item.english_definition || "", // 英文釋義
            japanese_translation: item.japanese_translation || "",
            korean_translation: item.korean_translation || "",
            audioUrl: item.audio_url || "",
            selectedWordLanguage: item.selectedWordLanguage || "chinese",
            selectedSentenceLanguage:
              item.selectedSentenceLanguage || "chinese",
            example_sentence: item.example_sentence || "",
            example_sentence_translation:
              item.example_sentence_translation || "",
            example_sentence_japanese: item.example_sentence_japanese || "",
            example_sentence_korean: item.example_sentence_korean || "",
            partsOfSpeech: item.parts_of_speech || [],
          }),
        );
        setRows(convertedRows);
      }
    } catch (error) {
      console.error("Failed to load content:", error);
      toast.error("載入內容失敗");
    } finally {
      setIsLoading(false);
    }
  };

  // Update parent when data changes
  useEffect(() => {
    if (!onUpdateContent) return;

    const items = rows.map((row) => ({
      text: row.text,
      definition: row.definition, // 中文翻譯
      translation: row.translation, // 英文釋義
      audio_url: row.audioUrl,
      selectedWordLanguage: row.selectedWordLanguage, // 記錄最後選擇的語言
      example_sentence: row.example_sentence,
      example_sentence_translation: row.example_sentence_translation,
      parts_of_speech: row.partsOfSpeech || [],
    }));

    onUpdateContent({
      ...editingContent,
      title,
      items,
    });
  }, [rows, title]);

  // dnd-kit drag end handler
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setRows((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const handleAddRow = () => {
    if (rows.length >= 15) {
      toast.error("最多只能新增 15 列");
      return;
    }
    // 找出最大的 ID 數字，然後加 1
    const maxId = Math.max(...rows.map((r) => parseInt(String(r.id)) || 0));
    const newRow: ContentRow = {
      id: (maxId + 1).toString(),
      text: "",
      definition: "",
      translation: "",
      selectedWordLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
    };
    setRows([...rows, newRow]);
  };

  const handleDeleteRow = (index: number) => {
    if (rows.length <= 1) {
      toast.error("至少需要保留 1 列");
      return;
    }
    const newRows = rows.filter((_, i) => i !== index);
    setRows(newRows);
  };

  const handleCopyRow = (index: number) => {
    if (rows.length >= 15) {
      toast.error("最多只能新增 15 列");
      return;
    }
    const rowToCopy = rows[index];
    // 找出最大的 ID 數字，然後加 1
    const maxId = Math.max(...rows.map((r) => parseInt(String(r.id)) || 0));
    const newRow: ContentRow = {
      ...rowToCopy,
      id: (maxId + 1).toString(),
    };
    const newRows = [...rows];
    newRows.splice(index + 1, 0, newRow);
    setRows(newRows);
  };

  const handleUpdateRow = (
    index: number,
    field: keyof ContentRow,
    value: string | string[],
  ) => {
    const newRows = [...rows];
    newRows[index] = { ...newRows[index], [field]: value };
    setRows(newRows);
  };

  const handleRemoveAudio = async (index: number) => {
    const newRows = [...rows];
    newRows[index] = { ...newRows[index], audioUrl: "" };
    setRows(newRows);

    // 如果是編輯模式，立即更新到後端
    if (!isCreating && editingContent?.id) {
      try {
        const items = newRows.map((row) => ({
          text: row.text,
          definition: row.definition,
          translation: row.translation,
          audio_url: row.audioUrl || "",
          selectedWordLanguage: row.selectedWordLanguage,
        }));

        await apiClient.updateContent(editingContent.id, {
          title: title || editingContent.title,
          items,
        });

        toast.success("已移除音檔");
      } catch (error) {
        console.error("Failed to remove audio:", error);
        toast.error("移除音檔失敗");
        // 恢復原始狀態
        const originalRows = [...rows];
        setRows(originalRows);
      }
    } else {
      toast.info("已移除音檔");
    }
  };

  const handleOpenTTSModal = (row: ContentRow) => {
    setSelectedRow(row);
    setTtsModalOpen(true);
  };

  const handleTTSConfirm = async (
    audioUrl: string,
    settings: {
      accent?: string;
      gender?: string;
      speed?: string;
      source?: string;
      audioBlob?: Blob | null;
    },
  ) => {
    if (selectedRow) {
      const index = rows.findIndex((r) => r.id === selectedRow.id);
      if (index !== -1) {
        const newRows = [...rows];
        // 一個 item 只能有一種音檔來源（TTS 或錄音）
        newRows[index] = {
          ...newRows[index],
          audioUrl, // 新的音檔會覆蓋舊的
          audioSettings: {
            accent: settings.accent || "American English",
            gender: settings.gender || "Male",
            speed: settings.speed || "Normal x1",
          },
        };
        setRows(newRows);

        // 立即更新 content 並儲存到後端
        const items = newRows.map((row) => ({
          text: row.text,
          definition: row.definition, // 中文翻譯
          translation: row.translation, // 英文釋義
          audio_url: row.audioUrl || "",
          selectedWordLanguage: row.selectedWordLanguage, // 記錄最後選擇的語言
        }));

        // 新增模式：只更新本地狀態
        if (isCreating) {
          // 更新本地狀態
          if (onUpdateContent) {
            onUpdateContent({
              ...editingContent,
              title,
              items,
            });
          }
          console.log(
            "Audio URL saved locally (will upload on final save):",
            audioUrl,
          );
        } else if (editingContent?.id) {
          // 編輯模式：直接呼叫 API 更新
          try {
            const updateData = {
              title: title || editingContent?.title,
              items,
            };

            console.log("Updating content with new audio:", audioUrl);
            await apiClient.updateContent(editingContent.id, updateData);

            // 更新成功後，重新從後端載入內容以確保同步
            const response = await apiClient.getContentDetail(
              editingContent.id,
            );
            if (response && response.items) {
              const updatedRows = response.items.map(
                (
                  item: {
                    text?: string;
                    translation?: string;
                    definition?: string;
                    audio_url?: string;
                  },
                  index: number,
                ) => ({
                  id: String(index + 1),
                  text: item.text || "",
                  definition: item.translation || "",
                  audioUrl: item.audio_url || "",
                }),
              );
              setRows(updatedRows);
              console.log("Updated rows with new audio URLs:", updatedRows);
            }

            // 更新本地狀態
            if (onUpdateContent) {
              onUpdateContent({
                ...editingContent,
                title,
                items,
              });
            }
          } catch (error) {
            console.error("Failed to update content:", error);
            toast.error("更新失敗，但音檔已生成");
          }
        } else {
          // 沒有 content ID，音檔將在儲存時上傳
          console.log(
            "Audio URL saved locally (will upload on final save):",
            audioUrl,
          );
        }

        // 關閉 modal 但不要關閉 panel
        setTtsModalOpen(false);
        setSelectedRow(null);
      }
    }
  };

  const handleBatchGenerateTTS = async () => {
    try {
      // 收集需要生成 TTS 的例句（而非單字）
      const textsToGenerate = rows
        .filter((row) => row.example_sentence && !row.audioUrl)
        .map((row) => row.example_sentence || "");

      if (textsToGenerate.length === 0) {
        toast.info("所有項目都已有音檔，或例句為空");
        return;
      }

      toast.info(`正在生成 ${textsToGenerate.length} 個例句音檔...`);

      // 批次生成 TTS
      const result = await apiClient.batchGenerateTTS(
        textsToGenerate,
        "en-US-JennyNeural", // 預設使用美國女聲
        "+0%",
        "+0%",
      );

      if (
        result &&
        typeof result === "object" &&
        "audio_urls" in result &&
        Array.isArray(result.audio_urls)
      ) {
        // 更新 rows 的 audioUrl（例句音檔）
        const newRows = [...rows];
        let audioIndex = 0;

        for (let i = 0; i < newRows.length; i++) {
          if (newRows[i].example_sentence && !newRows[i].audioUrl) {
            const audioUrl = (result as { audio_urls: string[] }).audio_urls[
              audioIndex
            ];
            // 如果是相對路徑，加上 API base URL
            newRows[i].audioUrl = audioUrl.startsWith("http")
              ? audioUrl
              : `${import.meta.env.VITE_API_URL}${audioUrl}`;
            audioIndex++;
          }
        }

        setRows(newRows);

        // 立即更新 content 並儲存到後端（不要用 onSave 避免關閉 panel）
        const items = newRows.map((row) => ({
          text: row.text,
          definition: row.definition, // 中文翻譯
          translation: row.translation, // 英文釋義
          audio_url: row.audioUrl || "",
          selectedWordLanguage: row.selectedWordLanguage, // 記錄最後選擇的語言
        }));

        // 新增模式：只更新本地狀態，不呼叫 API
        if (isCreating) {
          // 更新本地狀態
          if (onUpdateContent) {
            onUpdateContent({
              ...editingContent,
              title,
              items,
            });
          }

          toast.success(
            `成功生成 ${textsToGenerate.length} 個音檔！音檔將在儲存內容時一併上傳。`,
          );
        } else if (editingContent?.id) {
          // 編輯模式：直接呼叫 API 更新
          try {
            const updateData = {
              title: title || editingContent?.title,
              items,
            };

            await apiClient.updateContent(editingContent.id, updateData);

            // 更新本地狀態
            if (onUpdateContent) {
              onUpdateContent({
                ...editingContent,
                title,
                items,
              });
            }

            toast.success(`成功生成並儲存 ${textsToGenerate.length} 個音檔！`);
          } catch (error) {
            console.error("Failed to save TTS:", error);
            toast.error("儲存失敗，但音檔已生成");
          }
        } else {
          // 沒有 content ID，只是本地更新
          toast.success(
            `成功生成 ${textsToGenerate.length} 個音檔！音檔將在儲存內容時一併上傳。`,
          );
        }
      }
    } catch (error) {
      console.error("Batch TTS generation failed:", error);
      toast.error("批次生成失敗，請重試");
    }
  };

  const handleGenerateSingleDefinition = async (index: number) => {
    const currentLang = rows[index].selectedWordLanguage || "chinese";
    return handleGenerateSingleDefinitionWithLang(index, currentLang);
  };

  const handleGenerateSingleDefinitionWithLang = async (
    index: number,
    targetLang: WordTranslationLanguage,
  ) => {
    const newRows = [...rows];
    if (!newRows[index].text) {
      toast.error("請先輸入文本");
      return;
    }

    // 檢查是否需要自動辨識詞性（詞性陣列為空且翻譯成中文）
    const needAutoDetectPOS =
      targetLang === "chinese" &&
      (!newRows[index].partsOfSpeech ||
        newRows[index].partsOfSpeech.length === 0);

    const langConfig = WORD_TRANSLATION_LANGUAGES.find(
      (l) => l.value === targetLang,
    );
    toast.info(`生成${langConfig?.label || ""}翻譯中...`);

    try {
      if (needAutoDetectPOS) {
        // 使用新的 API 同時翻譯和辨識詞性（僅中文）
        const response = await apiClient.translateWithPos(
          newRows[index].text,
          langConfig?.code || "zh-TW",
        );

        newRows[index].definition = response.translation;
        // 自動填入詞性
        if (response.parts_of_speech && response.parts_of_speech.length > 0) {
          newRows[index].partsOfSpeech = response.parts_of_speech;
        }
      } else {
        // 已有詞性或非中文，只翻譯不改變詞性
        const response = (await apiClient.translateText(
          newRows[index].text,
          langConfig?.code || "zh-TW",
        )) as { translation: string };

        // 根據目標語言寫入對應欄位
        if (targetLang === "chinese") {
          newRows[index].definition = response.translation;
        } else if (targetLang === "english") {
          newRows[index].translation = response.translation;
        } else if (targetLang === "japanese") {
          newRows[index].japanese_translation = response.translation;
        } else if (targetLang === "korean") {
          newRows[index].korean_translation = response.translation;
        }
      }

      // 記錄最後選擇的語言
      newRows[index].selectedWordLanguage = targetLang;
      setRows(newRows);
      toast.success(
        needAutoDetectPOS
          ? "翻譯及詞性辨識完成"
          : `${langConfig?.label || ""}翻譯生成完成`,
      );
    } catch (error) {
      console.error("Translation error:", error);
      toast.error("翻譯失敗，請稍後再試");
    }
  };

  const handleBatchGenerateDefinitions = async () => {
    // 收集需要翻譯的項目
    const itemsToTranslate: { index: number; text: string }[] = [];

    rows.forEach((row, index) => {
      if (row.text && !row.definition) {
        itemsToTranslate.push({ index, text: row.text });
      }
    });

    if (itemsToTranslate.length === 0) {
      toast.info("沒有需要翻譯的項目");
      return;
    }

    toast.info(`開始批次生成翻譯...`);
    const newRows = [...rows];

    try {
      // 分類：需要辨識詞性的項目 vs 已有詞性的項目
      const needsPOS = itemsToTranslate.filter(
        (item) =>
          !newRows[item.index].partsOfSpeech ||
          newRows[item.index].partsOfSpeech!.length === 0,
      );
      const hasPOS = itemsToTranslate.filter(
        (item) =>
          newRows[item.index].partsOfSpeech &&
          newRows[item.index].partsOfSpeech!.length > 0,
      );

      // 對需要辨識詞性的項目使用新 API
      if (needsPOS.length > 0) {
        const textsForPOS = needsPOS.map((item) => item.text);
        const posResponse = await apiClient.batchTranslateWithPos(
          textsForPOS,
          "zh-TW",
        );
        const results = posResponse.results || [];

        needsPOS.forEach((item, idx) => {
          if (results[idx]) {
            newRows[item.index].definition = results[idx].translation;
            // 自動填入詞性
            if (
              results[idx].parts_of_speech &&
              results[idx].parts_of_speech.length > 0
            ) {
              newRows[item.index].partsOfSpeech = results[idx].parts_of_speech;
            }
          }
        });
      }

      // 對已有詞性的項目只翻譯
      if (hasPOS.length > 0) {
        const textsNoPOS = hasPOS.map((item) => item.text);
        const translateResponse = await apiClient.batchTranslate(
          textsNoPOS,
          "zh-TW",
        );
        const translations =
          (translateResponse as { translations?: string[] }).translations || [];

        hasPOS.forEach((item, idx) => {
          newRows[item.index].definition = translations[idx] || item.text;
        });
      }

      setRows(newRows);
      const posCount = needsPOS.length;
      toast.success(
        `批次翻譯完成！處理了 ${itemsToTranslate.length} 個項目` +
          (posCount > 0 ? `，其中 ${posCount} 個自動辨識了詞性` : ""),
      );
    } catch (error) {
      console.error("Batch translation error:", error);
      toast.error("批次翻譯失敗，請稍後再試");
    }
  };

  // Example sentence translation functions
  const handleGenerateExampleTranslation = async (index: number) => {
    const currentLang = rows[index].selectedSentenceLanguage || "chinese";
    return handleGenerateExampleTranslationWithLang(index, currentLang);
  };

  const handleGenerateExampleTranslationWithLang = async (
    index: number,
    targetLang: SentenceTranslationLanguage,
  ) => {
    const newRows = [...rows];
    if (!newRows[index].example_sentence) {
      toast.error("請先輸入例句");
      return;
    }

    const langConfig = SENTENCE_TRANSLATION_LANGUAGES.find(
      (l) => l.value === targetLang,
    );
    toast.info(`生成例句${langConfig?.label || ""}翻譯中...`);

    try {
      const response = (await apiClient.translateText(
        newRows[index].example_sentence!,
        langConfig?.code || "zh-TW",
      )) as { translation: string };

      // 根據目標語言寫入對應欄位
      if (targetLang === "chinese") {
        newRows[index].example_sentence_translation = response.translation;
      } else if (targetLang === "japanese") {
        newRows[index].example_sentence_japanese = response.translation;
      } else if (targetLang === "korean") {
        newRows[index].example_sentence_korean = response.translation;
      }

      // 記錄最後選擇的語言
      newRows[index].selectedSentenceLanguage = targetLang;
      setRows(newRows);
      toast.success(`例句${langConfig?.label || ""}翻譯生成完成`);
    } catch (error) {
      console.error("Example sentence translation error:", error);
      toast.error("例句翻譯失敗，請稍後再試");
    }
  };

  // 打開 AI 生成例句對話框
  const handleOpenAIGenerateModal = (index: number | null) => {
    setAiGenerateTargetIndex(index);
    setAiGenerateModalOpen(true);
  };

  // AI 生成例句
  const handleAIGenerateSentences = async () => {
    setIsGeneratingAI(true);

    try {
      // 確定要生成的目標
      const targetIndices: number[] = [];
      if (aiGenerateTargetIndex !== null) {
        // 單個生成：只處理該項目
        targetIndices.push(aiGenerateTargetIndex);
      } else {
        // 批次生成：所有有單字的項目（不管有沒有例句，全部重新生成）
        rows.forEach((row, index) => {
          if (row.text && row.text.trim()) {
            targetIndices.push(index);
          }
        });
      }

      if (targetIndices.length === 0) {
        toast.info("沒有可生成例句的項目（請先輸入單字）");
        setIsGeneratingAI(false);
        return;
      }

      // 收集需要生成的單字和詞性
      const wordsToGenerate = targetIndices.map((idx) => ({
        word: rows[idx].text,
        partsOfSpeech: rows[idx].partsOfSpeech || [],
      }));

      // 根據翻譯語言決定 target_language
      let targetLanguage = "";
      if (aiGenerateTranslate) {
        switch (aiGenerateTranslateLang) {
          case "中文":
            targetLanguage = "zh-TW";
            break;
          case "日文":
            targetLanguage = "ja";
            break;
          case "韓文":
            targetLanguage = "ko";
            break;
        }
      }

      toast.info(`正在生成 ${wordsToGenerate.length} 個例句...`);

      // 呼叫 API 生成例句
      const response = await apiClient.generateSentences({
        words: wordsToGenerate.map((w) => w.word),
        level: aiGenerateLevel,
        prompt: aiGeneratePrompt || undefined,
        translate_to: targetLanguage || undefined,
        parts_of_speech: wordsToGenerate.map((w) => w.partsOfSpeech),
      });

      // 更新 rows
      const newRows = [...rows];
      const results =
        (
          response as {
            sentences: Array<{ sentence: string; translation?: string }>;
          }
        ).sentences || [];

      targetIndices.forEach((idx, i) => {
        // 先清空現有的例句和翻譯
        newRows[idx].example_sentence = "";
        newRows[idx].example_sentence_translation = "";

        // 填入新生成的例句
        if (results[i]) {
          newRows[idx].example_sentence = results[i].sentence;
          // 只有勾選翻譯且 API 有返回翻譯時才填入
          if (aiGenerateTranslate && results[i].translation) {
            newRows[idx].example_sentence_translation = results[i].translation;
          }
          // 如果未勾選翻譯，翻譯欄位保持空（已在上面清空）
        }
      });

      setRows(newRows);
      toast.success(`成功生成 ${results.length} 個例句！`);
      setAiGenerateModalOpen(false);
    } catch (error) {
      console.error("AI generate sentences error:", error);
      toast.error("AI 生成例句失敗，請稍後再試");
    } finally {
      setIsGeneratingAI(false);
    }
  };

  const handleBatchPaste = async (autoTTS: boolean, autoTranslate: boolean) => {
    // 分割文字，每行一個項目
    const lines = batchPasteText
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    if (lines.length === 0) {
      toast.error("請輸入內容");
      return;
    }

    toast.info(`正在處理 ${lines.length} 個項目...`);

    // 清除空白 items
    const nonEmptyRows = rows.filter((row) => row.text && row.text.trim());

    // 建立新 items
    let newItems: ContentRow[] = lines.map((text, index) => ({
      id: `batch-${Date.now()}-${index}`,
      text,
      definition: "",
      translation: "",
      selectedWordLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
    }));

    // 批次處理 TTS 和翻譯
    if (autoTTS || autoTranslate) {
      try {
        if (autoTTS) {
          const ttsResult = await apiClient.batchGenerateTTS(
            lines,
            "en-US-JennyNeural",
            "+0%",
            "+0%",
          );
          if (
            ttsResult &&
            typeof ttsResult === "object" &&
            "audio_urls" in ttsResult
          ) {
            const audioUrls = (ttsResult as { audio_urls: string[] })
              .audio_urls;
            newItems = newItems.map((item, i) => ({
              ...item,
              audioUrl: audioUrls[i]?.startsWith("http")
                ? audioUrls[i]
                : `${import.meta.env.VITE_API_URL}${audioUrls[i]}`,
              audio_url: audioUrls[i]?.startsWith("http")
                ? audioUrls[i]
                : `${import.meta.env.VITE_API_URL}${audioUrls[i]}`,
            }));
          }
        }

        if (autoTranslate) {
          const result = await apiClient.batchTranslate(lines, "zh-TW");
          const translations =
            (result as { translations?: string[] }).translations || result;
          if (Array.isArray(translations)) {
            newItems = newItems.map((item, i) => ({
              ...item,
              definition: translations[i] || "",
            }));
          }
        }
      } catch (error) {
        console.error("Batch processing error:", error);
        toast.error("批次處理失敗");
        return;
      }
    }

    // 合併新舊項目
    const updatedRows = [...nonEmptyRows, ...newItems];

    // 更新前端狀態
    setRows(updatedRows);

    // 🔥 重點：直接儲存到資料庫
    try {
      const saveData = {
        title: title || "句子模組內容",
        items: updatedRows.map((row) => ({
          text: row.text.trim(),
          definition: row.definition || "",
          english_definition: row.translation || "",
          translation: row.definition || "",
          selectedWordLanguage: row.selectedWordLanguage || "chinese",
          audio_url: row.audioUrl || row.audio_url || "",
        })),
        target_wpm: 60,
        target_accuracy: 0.8,
        time_limit_seconds: 180,
      };

      const existingContentId = editingContent?.id || content?.id;

      if (existingContentId) {
        // 編輯模式：更新現有內容
        await apiClient.updateContent(existingContentId, saveData);
        toast.success(
          `已新增 ${lines.length} 個項目並儲存（共 ${updatedRows.length} 個）`,
        );
      } else if (isCreating && lessonId) {
        // 創建模式：新增內容
        await apiClient.createContent(lessonId, {
          type: "SENTENCE_MAKING",
          ...saveData,
        });
        toast.success(`已新增 ${lines.length} 個項目並創建內容`);
        // 🔥 不要呼叫 onSave 避免重新載入，直接顯示結果
      } else {
        // 沒有 contentId 也沒有 lessonId，只更新前端
        toast.success(
          `已新增 ${lines.length} 個項目（共 ${updatedRows.length} 個）`,
        );
      }
    } catch (error) {
      console.error("Failed to save batch paste:", error);
      toast.error("儲存失敗，請稍後再試");
      return;
    }

    setBatchPasteDialogOpen(false);
    setBatchPasteText("");
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
        {/* Title Input - Show in both create and edit mode */}
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

        {/* Batch Actions - RWD adjusted */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setBatchPasteDialogOpen(true)}
            className="bg-blue-100 hover:bg-blue-200 border-blue-300"
            title="批次貼上素材，每行一個項目"
          >
            <Clipboard className="h-4 w-4 mr-1" />
            批次貼上
          </Button>
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
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleOpenAIGenerateModal(null)}
            className="bg-purple-100 hover:bg-purple-200 border-purple-300"
            title="批次 AI 生成例句"
          >
            <Globe className="h-4 w-4 mr-1" />
            批次AI生成例句
          </Button>
        </div>
      </div>

      {/* Scrollable Content Rows with dnd-kit */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={rows.map((row) => row.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="flex-1 overflow-y-auto space-y-3 pr-2">
            {rows.map((row, index) => {
              // useSortable must be called inside the component that's in SortableContext
              // so we'll use a nested component
              return (
                <SortableRowInner
                  key={row.id}
                  row={row}
                  index={index}
                  handleUpdateRow={handleUpdateRow}
                  handleRemoveRow={handleDeleteRow}
                  handleDuplicateRow={handleCopyRow}
                  handleOpenTTSModal={handleOpenTTSModal}
                  handleRemoveAudio={handleRemoveAudio}
                  handleGenerateSingleDefinition={
                    handleGenerateSingleDefinition
                  }
                  handleGenerateSingleDefinitionWithLang={
                    handleGenerateSingleDefinitionWithLang
                  }
                  handleGenerateExampleTranslation={
                    handleGenerateExampleTranslation
                  }
                  handleGenerateExampleTranslationWithLang={
                    handleGenerateExampleTranslationWithLang
                  }
                  handleOpenAIGenerateModal={handleOpenAIGenerateModal}
                  rowsLength={rows.length}
                />
              );
            })}

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
        </SortableContext>
      </DndContext>

      {/* TTS Modal */}
      {selectedRow && (
        <TTSModal
          open={ttsModalOpen}
          onClose={() => setTtsModalOpen(false)}
          row={selectedRow}
          onConfirm={handleTTSConfirm}
          contentId={editingContent?.id}
          itemIndex={rows.findIndex((r) => r.id === selectedRow.id)}
          isCreating={isCreating}
        />
      )}

      {/* Batch Paste Dialog */}
      <Dialog
        open={batchPasteDialogOpen}
        onOpenChange={setBatchPasteDialogOpen}
      >
        <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
          <DialogHeader className="pb-4 flex-shrink-0">
            <DialogTitle className="text-2xl font-bold text-gray-900">
              批次貼上素材
            </DialogTitle>
            <p className="text-sm text-gray-500 mt-2">
              每行一個項目，支援自動生成 TTS 與翻譯
            </p>
          </DialogHeader>
          <div className="space-y-6 overflow-y-auto flex-1 min-h-0">
            <div>
              <label className="text-base font-semibold text-gray-800 mb-3 block">
                請貼上內容：
              </label>
              <textarea
                value={batchPasteText}
                onChange={(e) => setBatchPasteText(e.target.value)}
                placeholder="put&#10;Put it away.&#10;It's time to put everything away. Right now."
                className="w-full min-h-80 max-h-[60vh] px-4 py-3 border-2 border-gray-300 rounded-lg font-mono text-base focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all resize-y overflow-y-auto"
              />
              <div className="text-xs text-gray-500 mt-2">
                {batchPasteText.split("\n").filter((line) => line.trim())
                  .length || 0}{" "}
                個項目
              </div>
            </div>
            <div className="flex gap-6 p-4 bg-gray-50 rounded-lg">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={batchPasteAutoTTS}
                  onChange={(e) => setBatchPasteAutoTTS(e.target.checked)}
                  className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-base font-medium text-gray-700">
                  自動生成 TTS
                </span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={batchPasteAutoTranslate}
                  onChange={(e) => setBatchPasteAutoTranslate(e.target.checked)}
                  className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-base font-medium text-gray-700">
                  自動翻譯
                </span>
              </label>
            </div>
          </div>
          <DialogFooter className="pt-6 flex-shrink-0 border-t border-gray-200 mt-4">
            <Button
              variant="outline"
              onClick={() => setBatchPasteDialogOpen(false)}
              className="px-6 py-2 text-base"
            >
              取消
            </Button>
            <Button
              onClick={() =>
                handleBatchPaste(batchPasteAutoTTS, batchPasteAutoTranslate)
              }
              className="px-6 py-2 text-base bg-blue-600 hover:bg-blue-700"
            >
              確認貼上
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI 生成例句對話框 */}
      <Dialog open={aiGenerateModalOpen} onOpenChange={setAiGenerateModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold">AI 生成例句</DialogTitle>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* 難度等級選擇 */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                難度等級
              </label>
              <div className="flex flex-wrap gap-2">
                {["A1", "A2", "B1", "B2", "C1", "C2"].map((level) => (
                  <button
                    key={level}
                    onClick={() => setAiGenerateLevel(level)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      aiGenerateLevel === level
                        ? "bg-gradient-to-r from-cyan-400 to-teal-400 text-white shadow-sm"
                        : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                    }`}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </div>

            {/* AI Prompt 輸入 */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                給 AI 的提示 (選填)
              </label>
              <textarea
                value={aiGeneratePrompt}
                onChange={(e) => setAiGeneratePrompt(e.target.value)}
                placeholder="例如：請生成與日常生活相關的例句"
                className="w-full px-3 py-2 border rounded-lg text-sm resize-none"
                rows={3}
              />
            </div>

            {/* 翻譯選項 */}
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={aiGenerateTranslate}
                  onChange={(e) => setAiGenerateTranslate(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  翻譯成
                </span>
              </label>
              <select
                value={aiGenerateTranslateLang}
                onChange={(e) => setAiGenerateTranslateLang(e.target.value)}
                disabled={!aiGenerateTranslate}
                className={`px-3 py-1.5 border rounded-md text-sm ${
                  !aiGenerateTranslate ? "bg-gray-100 text-gray-400" : ""
                }`}
              >
                <option value="中文">中文</option>
                <option value="日文">日文</option>
                <option value="韓文">韓文</option>
              </select>
            </div>

            {/* 生成目標提示 */}
            <div className="text-sm bg-amber-50 border border-amber-200 p-3 rounded-lg">
              {aiGenerateTargetIndex !== null ? (
                <div>
                  <span className="text-amber-700">
                    將為「
                    <strong>{rows[aiGenerateTargetIndex]?.text || ""}</strong>
                    」重新生成例句
                  </span>
                  {rows[aiGenerateTargetIndex]?.example_sentence && (
                    <div className="text-amber-600 text-xs mt-1">
                      現有例句將被覆蓋
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <span className="text-amber-700">
                    將為{" "}
                    <strong>
                      {rows.filter((r) => r.text && r.text.trim()).length}
                    </strong>{" "}
                    個單字重新生成例句
                  </span>
                  <div className="text-amber-600 text-xs mt-1">
                    所有現有例句{aiGenerateTranslate ? "及翻譯" : ""}將被覆蓋
                    {!aiGenerateTranslate && "，翻譯欄位將被清空"}
                  </div>
                </div>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setAiGenerateModalOpen(false)}
            >
              取消
            </Button>
            <Button
              onClick={handleAIGenerateSentences}
              disabled={isGeneratingAI}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isGeneratingAI ? "生成中..." : "生成"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Save Button */}
      {onSave && (
        <div className="fixed bottom-6 right-6 z-50">
          <Button
            size="lg"
            className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg"
            onClick={async () => {
              // 過濾掉空白項目
              const validRows = rows.filter(
                (row) => row.text && row.text.trim(),
              );

              if (validRows.length === 0) {
                toast.error("請至少新增一個內容項目");
                return;
              }

              if (!title || title.trim() === "") {
                toast.error("請輸入標題");
                return;
              }

              // 準備要儲存的資料
              const saveData = {
                title: title,
                items: validRows.map((row) => ({
                  text: row.text.trim(),
                  definition: row.definition || "",
                  english_definition: row.translation || "",
                  translation: row.definition || "",
                  selectedWordLanguage: row.selectedWordLanguage || "chinese",
                  audio_url: row.audioUrl || row.audio_url || "",
                  example_sentence: row.example_sentence || "",
                  example_sentence_translation:
                    row.example_sentence_translation || "",
                  parts_of_speech: row.partsOfSpeech || [],
                })),
                target_wpm: 60,
                target_accuracy: 0.8,
                time_limit_seconds: 180,
              };

              console.log("Saving data:", saveData);

              const existingContentId = editingContent?.id || content?.id;

              if (existingContentId) {
                // 編輯模式：更新現有內容
                try {
                  await apiClient.updateContent(existingContentId, saveData);
                  toast.success("儲存成功");
                  if (onSave) {
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    await (onSave as (content?: any) => void | Promise<void>)({
                      id: existingContentId,
                      title: saveData.title,
                      items: saveData.items,
                    });
                  }
                } catch (error) {
                  console.error("Failed to update content:", error);
                  toast.error("儲存失敗");
                }
              } else if (isCreating && lessonId) {
                // 創建模式：新增內容
                try {
                  const newContent = await apiClient.createContent(lessonId, {
                    type: "SENTENCE_MAKING",
                    ...saveData,
                  });
                  toast.success("內容已成功創建");
                  if (onSave) {
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    await (onSave as (content?: any) => void | Promise<void>)(
                      newContent,
                    );
                  }
                } catch (error) {
                  console.error("Failed to create content:", error);
                  toast.error("創建內容失敗");
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
