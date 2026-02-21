import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
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
  Image as ImageIcon,
  X,
  Loader2,
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

/**
 * 將縮寫詞性轉換為完整名稱
 * 例如："n." -> "noun", "v." -> "verb"
 */
const convertAbbreviatedPOS = (abbreviatedList: string[]): string[] => {
  return abbreviatedList
    .map((abbr) => {
      // 先嘗試找縮寫對應的完整名稱
      const found = PARTS_OF_SPEECH.find(
        (pos) => pos.label === abbr || pos.label === abbr + ".",
      );
      if (found) return found.value;
      // 如果已經是完整名稱就直接返回
      const isFullName = PARTS_OF_SPEECH.find((pos) => pos.value === abbr);
      if (isFullName) return abbr;
      return null;
    })
    .filter((v): v is string => v !== null);
};

/**
 * 解析 AI 回傳的多個定義
 * 支援格式：
 *   - 編號換行：  "1. (n.) ...\n2. (n.) ..."
 *   - 編號同行：  "1. (v.) 探す  2. (v.) 求める"
 *   - POS 換行：  "(v.) 수행하다\n(v.) 공연하다\n(v.) 연기하다"
 *   - POS 同行：  "(v.) 수행하다  (v.) 공연하다"
 * 回傳各定義字串陣列；若只有 1 個定義則回傳空陣列（不需選擇）
 */
const parseMultipleDefinitions = (text: string): string[] => {
  const numbered = /^\d+\.\s/;
  const posStart = /^\(\w+\.\)\s/;

  // 1) 換行分割 → 編號格式
  let parts = text
    .split(/\n/)
    .map((s) => s.trim())
    .filter((s) => numbered.test(s));
  if (parts.length > 1) return parts;

  // 2) 同行分割 → 編號格式
  parts = text
    .split(/(?=\d+\.\s)/)
    .map((s) => s.trim())
    .filter((s) => numbered.test(s));
  if (parts.length > 1) return parts;

  // 3) 換行分割 → POS 開頭格式 (無編號)
  parts = text
    .split(/\n/)
    .map((s) => s.trim())
    .filter((s) => posStart.test(s));
  if (parts.length > 1) return parts;

  // 4) 同行分割 → POS 開頭格式 (無編號)
  parts = text
    .split(/(?=\(\w+\.\)\s)/)
    .map((s) => s.trim())
    .filter((s) => posStart.test(s));
  if (parts.length > 1) return parts;

  return [];
};

/**
 * 從翻譯結果中提取 POS 並清理文字
 * 輸入: "1. (v.) to recognize..." 或 "(n.) 蘋果" 或 "蘋果"
 * 回傳: { text: "to recognize...", pos: "v." } 或 { text: "蘋果", pos: null }
 */
const extractPosFromTranslation = (
  raw: string,
): { text: string; pos: string | null } => {
  // 先去掉編號 "1. "
  let text = raw.replace(/^\d+\.\s*/, "");
  // 提取詞性 (v.) (n.) (adj.) 等
  const posMatch = text.match(/^\((\w+\.)\)\s*/);
  if (posMatch) {
    text = text.replace(/^\(\w+\.\)\s*/, "");
    return { text, pos: posMatch[1] };
  }
  return { text, pos: null };
};

/**
 * 批次翻譯用：若有多義，只取第一個定義並提取 POS
 */
const extractFirstDefinition = (
  raw: string,
): { text: string; pos: string | null } => {
  const multiDefs = parseMultipleDefinitions(raw);
  const first = multiDefs.length > 0 ? multiDefs[0] : raw;
  return extractPosFromTranslation(first);
};

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
  imageUrl?: string; // 單字圖片 URL
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
  const { t } = useTranslation();
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

        toast.success(t("contentEditor.messages.audioGeneratedSuccess"));
      }
    } catch (err) {
      console.error("TTS generation failed:", err);
      toast.error(t("contentEditor.messages.generationFailed"));
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
            toast.info(t("contentEditor.messages.maxRecordingTimeReached"));
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
          toast.error(t("contentEditor.messages.recordingFileTooLarge"));
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        // 確保有錄音資料
        if (audioBlob.size === 0) {
          toast.error(t("contentEditor.messages.recordingFailed"));
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        // 儲存 blob 以便之後上傳
        audioBlobRef.current = audioBlob;
        recordingDurationRef.current = currentDuration;

        // 創建本地 URL 供預覽播放
        const localUrl = URL.createObjectURL(audioBlob);
        setRecordedAudio(localUrl);
        toast.success(t("contentEditor.messages.recordingComplete"));

        stream.getTracks().forEach((track) => track.stop());
      };

      // 使用 timeslice 參數，每100ms收集一次數據
      mediaRecorder.start(100);
      setIsRecording(true);
      toast.success(t("contentEditor.messages.recordingStarted"));
    } catch {
      toast.error(t("contentEditor.messages.cannotStartRecording"));
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
        toast.warning(t("contentEditor.messages.selectAudioSource"));
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
              toast.warning(t("contentEditor.messages.uploadRetrying"));
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
          toast.error(t("contentEditor.messages.uploadFailed"));
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
        toast.error(t("contentEditor.messages.generateOrRecordFirst"));
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
              toast.warning(t("contentEditor.messages.uploadRetrying"));
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
          toast.error(t("contentEditor.messages.uploadFailed"));
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
          <DialogTitle>{t("contentEditor.modals.audioSettings")}</DialogTitle>
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
                title={t("contentEditor.tooltips.ttsMicrosoftEdge")}
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
                  title={t("contentEditor.tooltips.playGeneratedAudio")}
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
                        ? t("contentEditor.messages.audioGenerated")
                        : t("contentEditor.messages.ttsAudioReady")}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setAudioUrl("");
                      setSelectedSource(null);
                      toast.info(t("contentEditor.messages.ttsAudioDeleted"));
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
                    {t("contentEditor.messages.maxRecordingTime")}
                  </div>
                </div>
              )}

              {/* 顯示上傳狀態 */}
              {isUploading && (
                <div className="mb-4 text-center">
                  <div className="text-sm text-blue-600">
                    {t("contentEditor.messages.uploadingRecording")}
                  </div>
                </div>
              )}

              {!isRecording && !recordedAudio && !isUploading && (
                <Button onClick={handleStartRecording} size="lg">
                  <Mic className="h-5 w-5 mr-2" />
                  {t("contentEditor.buttons.startRecording")}
                </Button>
              )}

              {isRecording && (
                <Button
                  onClick={handleStopRecording}
                  variant="destructive"
                  size="lg"
                >
                  <Square className="h-5 w-5 mr-2" />
                  {t("contentEditor.buttons.stopRecording")}
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
                              toast.error(
                                t("contentEditor.messages.noRecordingToPlay"),
                              );
                              return;
                            }

                            const audio = new Audio(recordedAudio);
                            audio.play().catch((err) => {
                              console.error("Play failed:", err);
                              toast.error(
                                t("contentEditor.messages.cannotPlayRecording"),
                              );
                            });
                          }}
                        >
                          <Play className="h-4 w-4" />
                        </Button>
                        <div className="flex items-center gap-2">
                          <Mic className="h-4 w-4 text-red-600" />
                          <span className="text-sm text-gray-700 font-medium">
                            {t("contentEditor.messages.recordingFileReady", {
                              duration: recordingDuration,
                            })}
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
                          toast.info(
                            t("contentEditor.messages.recordingDeleted"),
                          );
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
                      {t("contentEditor.buttons.rerecord")}
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
              🎵 {t("contentEditor.messages.selectAudioSourceToUse")}
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
                <div className="text-sm font-medium">
                  {t("contentEditor.audioSources.tts")}
                </div>
                <div className="text-xs text-gray-500">
                  {t("contentEditor.audioSources.aiGenerated")}
                </div>
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
                <div className="text-sm font-medium">
                  {t("contentEditor.audioSources.recording")}
                </div>
                <div className="text-xs text-gray-500">
                  {t("contentEditor.audioSources.teacherRecorded")}
                </div>
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
  handleImageUpload: (index: number, file: File) => Promise<void>;
  handleRemoveImage: (index: number) => void;
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
  imageUploading?: boolean;
  // 剪貼簿貼上圖片功能
  isActive?: boolean;
  onRowFocus?: () => void;
  onWordLanguageChange?: (lang: WordTranslationLanguage) => void;
}

function SortableRowInner({
  row,
  index,
  handleUpdateRow,
  handleRemoveRow,
  handleDuplicateRow,
  handleOpenTTSModal,
  handleRemoveAudio,
  handleImageUpload,
  handleRemoveImage,
  handleGenerateSingleDefinition,
  handleGenerateSingleDefinitionWithLang,
  handleGenerateExampleTranslation,
  handleGenerateExampleTranslationWithLang,
  handleOpenAIGenerateModal,
  rowsLength,
  imageUploading,
  isActive = false,
  onRowFocus,
  onWordLanguageChange,
}: SortableRowInnerProps) {
  const { t } = useTranslation();
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

  // 偵測作業系統，用於顯示對應的截圖提示
  const getScreenshotHint = (): string => {
    // 手機版不顯示提示（sm breakpoint = 640px）
    if (typeof window !== "undefined" && window.innerWidth < 640) {
      return "";
    }
    // 偵測作業系統
    if (typeof navigator !== "undefined") {
      const platform = navigator.platform?.toLowerCase() || "";
      const userAgent = navigator.userAgent?.toLowerCase() || "";
      if (platform.includes("mac") || userAgent.includes("mac")) {
        return t("vocabularySet.image.macScreenshotHint");
      }
      if (platform.includes("win") || userAgent.includes("win")) {
        return t("vocabularySet.image.windowsScreenshotHint");
      }
    }
    return "";
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
    <div
      ref={setNodeRef}
      style={style}
      className={`p-4 rounded-lg transition-all cursor-pointer ${
        isActive ? "bg-blue-50 border-l-4 border-l-blue-500" : "bg-gray-50"
      }`}
      onClick={onRowFocus}
    >
      {/* 頂部：拖曳手把 + 序號 + 動作按鈕 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {/* Drag handle */}
          <div
            {...attributes}
            {...listeners}
            className="cursor-grab active:cursor-grabbing touch-none"
            title={t("contentEditor.tooltips.dragToReorder")}
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
                  toast.error(t("contentEditor.messages.noRecordingToPlay"));
                  return;
                }
                const audio = new Audio(row.audioUrl);
                audio.onerror = (e) => {
                  console.error("Audio playback error:", e);
                  toast.error(
                    t("contentEditor.messages.audioGeneratedSuccess"),
                  );
                };
                audio.play().catch((error) => {
                  console.error("Play failed:", error);
                  toast.error(t("contentEditor.messages.cannotPlayRecording"));
                });
              }}
              className="p-1.5 rounded text-green-600 hover:bg-green-100"
              title={t("contentEditor.tooltips.playAudio")}
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
            title={
              row.audioUrl
                ? t("contentEditor.tooltips.rerecordOrGenerate")
                : t("contentEditor.tooltips.openTTSRecording")
            }
          >
            <Mic className="h-4 w-4" />
          </button>
          {row.audioUrl && (
            <button
              onClick={() => handleRemoveAudio(index)}
              className="p-1.5 rounded text-red-600 hover:bg-red-100"
              title={t("contentEditor.tooltips.removeAudio")}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
          <div className="w-px h-4 bg-gray-300 mx-1" />
          <button
            onClick={() => handleDuplicateRow(index)}
            className="p-1.5 rounded hover:bg-gray-200"
            title={t("contentEditor.tooltips.duplicate")}
          >
            <Copy className="h-4 w-4 text-gray-600" />
          </button>
          <button
            onClick={() => handleRemoveRow(index)}
            className="p-1.5 rounded hover:bg-gray-200"
            title={t("contentEditor.tooltips.delete")}
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
            placeholder={t("vocabularySet.placeholders.enterEnglishWord")}
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
            placeholder={t("vocabularySet.placeholders.translation", {
              lang: t(
                `contentEditor.translationLanguages.${WORD_TRANSLATION_LANGUAGES.find((l) => l.value === (row.selectedWordLanguage || "chinese"))?.value || "chinese"}`,
              ),
            })}
            maxLength={200}
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-1">
            <select
              value={row.selectedWordLanguage || "chinese"}
              onChange={(e) => {
                const newLang = e.target.value as WordTranslationLanguage;
                handleUpdateRow(index, "selectedWordLanguage", newLang);
                onWordLanguageChange?.(newLang);
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
              title={t("vocabularySet.tooltips.generateTranslation", {
                lang: t(
                  `contentEditor.translationLanguages.${WORD_TRANSLATION_LANGUAGES.find((l) => l.value === (row.selectedWordLanguage || "chinese"))?.value || "chinese"}`,
                ),
              })}
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

      {/* 圖片上傳區域 */}
      <div className="mb-3">
        {row.imageUrl ? (
          <div className="relative inline-block">
            <img
              src={row.imageUrl}
              alt={row.text || "word image"}
              className="h-20 w-20 object-cover rounded-lg border border-gray-300"
            />
            <button
              onClick={() => handleRemoveImage(index)}
              className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
              title={t("vocabularySet.image.remove")}
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ) : (
          <label
            className={`inline-flex items-center gap-2 px-3 py-2 border-2 border-dashed rounded-lg cursor-pointer transition-all ${
              imageUploading
                ? "opacity-50 cursor-not-allowed border-gray-300"
                : isActive
                  ? "border-blue-400 bg-blue-50 hover:bg-blue-100"
                  : "border-gray-300 hover:border-blue-400 hover:bg-blue-50"
            }`}
            title={isActive ? getScreenshotHint() : ""}
          >
            <input
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              className="hidden"
              disabled={imageUploading}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  handleImageUpload(index, file);
                }
                // Reset input so same file can be selected again
                e.target.value = "";
              }}
            />
            {imageUploading ? (
              <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
            ) : (
              <ImageIcon
                className={`h-4 w-4 ${isActive ? "text-blue-500" : "text-gray-500"}`}
              />
            )}
            <span
              className={`text-sm ${isActive ? "text-blue-600" : "text-gray-600"}`}
            >
              {imageUploading ? (
                t("vocabularySet.image.uploading")
              ) : isActive ? (
                <>
                  <span className="hidden sm:inline">
                    {t("vocabularySet.image.pasteShortcut")}
                  </span>
                  {t("vocabularySet.image.clickToUpload")}
                </>
              ) : (
                t("vocabularySet.image.upload")
              )}
            </span>
          </label>
        )}
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
          placeholder={t("vocabularySet.placeholders.enterEnglishSentence")}
          maxLength={500}
        />
        <button
          onClick={() => handleOpenAIGenerateModal(index)}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-blue-100 text-blue-600 border border-blue-300"
          title={t("vocabularySet.tooltips.generateExampleSentence")}
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
          placeholder={t("vocabularySet.placeholders.exampleTranslation", {
            lang: t(
              `contentEditor.translationLanguages.${SENTENCE_TRANSLATION_LANGUAGES.find((l) => l.value === (row.selectedSentenceLanguage || "chinese"))?.value || "chinese"}`,
            ),
          })}
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
              title={t("vocabularySet.tooltips.generateExampleTranslation", {
                lang: t(
                  `contentEditor.translationLanguages.${SENTENCE_TRANSLATION_LANGUAGES.find((l) => l.value === (row.selectedSentenceLanguage || "chinese"))?.value || "chinese"}`,
                ),
              })}
            >
              <Globe className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface VocabularySetPanelProps {
  content?: { id?: number; title?: string; items?: ContentRow[] };
  editingContent?: { id?: number; title?: string; items?: ContentRow[] };
  onUpdateContent?: (content: Record<string, unknown>) => void;
  onSave?: () => void | Promise<void>;
  // Alternative props for ClassroomDetail usage
  lessonId?: number;
  programLevel?: string; // Program difficulty level for AI generation
  onCancel?: () => void;
  isOpen?: boolean;
  isCreating?: boolean; // 是否為新增模式
}

export default function VocabularySetPanel({
  content,
  editingContent,
  onUpdateContent,
  onSave,
  lessonId,
  programLevel,
  isCreating = false,
}: VocabularySetPanelProps) {
  const { t } = useTranslation();

  const [title, setTitle] = useState(t("vocabularySet.defaultTitle"));
  // 記住用戶最後選擇的翻譯語言，批次翻譯時使用
  const [lastSelectedWordLang, setLastSelectedWordLang] =
    useState<WordTranslationLanguage>("chinese");
  const [rows, setRows] = useState<ContentRow[]>([
    {
      id: "1",
      text: "",
      definition: "",
      translation: "",
      imageUrl: "",
      selectedWordLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
    },
    {
      id: "2",
      text: "",
      definition: "",
      translation: "",
      imageUrl: "",
      selectedWordLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
    },
    {
      id: "3",
      text: "",
      definition: "",
      translation: "",
      imageUrl: "",
      selectedWordLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
    },
  ]);
  const [selectedRow, setSelectedRow] = useState<ContentRow | null>(null);
  const [ttsModalOpen, setTtsModalOpen] = useState(false);
  // 追蹤當前編輯的行索引（用於剪貼簿貼上圖片）
  const [activeRowIndex, setActiveRowIndex] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [batchPasteDialogOpen, setBatchPasteDialogOpen] = useState(false);
  const [batchPasteText, setBatchPasteText] = useState("");
  const [batchPasteAutoTTS, setBatchPasteAutoTTS] = useState(true);
  const [batchPasteAutoTranslate, setBatchPasteAutoTranslate] = useState(true);

  // TTS settings for batch paste (Issue #121)
  const [batchTTSAccent, setBatchTTSAccent] = useState("American English");
  const [batchTTSGender, setBatchTTSGender] = useState("Male");
  const [batchTTSSpeed, setBatchTTSSpeed] = useState("Normal x1");

  // 多義 Picker 狀態（英英釋義 / 中文翻譯皆可）
  const [definitionPicker, setDefinitionPicker] = useState<{
    rowIndex: number;
    word: string;
    options: string[];
    targetLang: WordTranslationLanguage;
  } | null>(null);

  // AI 生成例句對話框狀態
  const [aiGenerateModalOpen, setAiGenerateModalOpen] = useState(false);
  const [aiGenerateTargetIndex, setAiGenerateTargetIndex] = useState<
    number | null
  >(null); // null 表示批次生成
  const [aiGenerateLevel, setAiGenerateLevel] = useState<string>(
    programLevel || "A1",
  ); // 🔥 階段2：預設使用 Program level
  const [aiGeneratePrompt, setAiGeneratePrompt] = useState("");
  const [aiGenerateTranslate, setAiGenerateTranslate] = useState(true);
  const [aiGenerateTranslateLang, setAiGenerateTranslateLang] =
    useState<string>(() => {
      const lang = navigator.language || "zh-TW";
      if (lang.startsWith("ja")) return "日文";
      if (lang.startsWith("ko")) return "韓文";
      return "中文"; // 預設中文（含 zh、en 及其他語言）
    });
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

  // TTS options for batch paste (Issue #121)
  const batchTTSAccents = [
    "American English",
    "British English",
    "Indian English",
    "Australian English",
  ];
  const batchTTSGenders = ["Male", "Female"];
  const batchTTSSpeeds = ["Slow x0.75", "Normal x1", "Fast x1.5"];

  // Load saved TTS settings from localStorage (Issue #121)
  useEffect(() => {
    const saved = localStorage.getItem("duotopia_batch_tts_settings");
    if (saved) {
      try {
        const settings = JSON.parse(saved);
        if (settings.accent) setBatchTTSAccent(settings.accent);
        if (settings.gender) setBatchTTSGender(settings.gender);
        if (settings.speed) setBatchTTSSpeed(settings.speed);
      } catch {
        // Ignore parse errors
      }
    }
  }, []);

  // Helper function to get voice and rate from TTS settings (Issue #121)
  const getVoiceAndRate = (accent: string, gender: string, speed: string) => {
    let voice = "en-US-JennyNeural"; // default

    if (accent === "American English") {
      voice =
        gender === "Male" ? "en-US-ChristopherNeural" : "en-US-JennyNeural";
    } else if (accent === "British English") {
      voice = gender === "Male" ? "en-GB-RyanNeural" : "en-GB-SoniaNeural";
    } else if (accent === "Indian English") {
      voice = gender === "Male" ? "en-IN-PrabhatNeural" : "en-IN-NeerjaNeural";
    } else if (accent === "Australian English") {
      voice = gender === "Male" ? "en-AU-WilliamNeural" : "en-AU-NatashaNeural";
    }

    let rate = "+0%";
    if (speed === "Slow x0.75") rate = "-25%";
    else if (speed === "Fast x1.5") rate = "+50%";

    return { voice, rate };
  };

  // Save TTS settings to localStorage (Issue #121)
  const saveBatchTTSSettings = () => {
    localStorage.setItem(
      "duotopia_batch_tts_settings",
      JSON.stringify({
        accent: batchTTSAccent,
        gender: batchTTSGender,
        speed: batchTTSSpeed,
      }),
    );
  };

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

      // 預設使用課程難度
      if (data.level) {
        setAiGenerateLevel(data.level);
      }

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
              image_url?: string;
              selectedWordLanguage?: WordTranslationLanguage;
              selectedSentenceLanguage?: SentenceTranslationLanguage;
              example_sentence?: string;
              example_sentence_translation?: string;
              example_sentence_japanese?: string;
              example_sentence_korean?: string;
              parts_of_speech?: string[];
              // 新的統一欄位
              vocabulary_translation?: string;
              vocabulary_translation_lang?: WordTranslationLanguage;
              example_sentence_translation_lang?: SentenceTranslationLanguage;
            },
            index: number,
          ) => {
            // 處理單字翻譯：優先使用新的統一欄位
            let definition = "";
            let translation = "";
            let japanese_translation = "";
            let korean_translation = "";
            let selectedWordLanguage: WordTranslationLanguage = "chinese";

            if (
              item.vocabulary_translation_lang &&
              item.vocabulary_translation
            ) {
              // 使用新的統一欄位格式
              selectedWordLanguage = item.vocabulary_translation_lang;
              if (item.vocabulary_translation_lang === "chinese") {
                definition = item.vocabulary_translation;
              } else if (item.vocabulary_translation_lang === "english") {
                translation = item.vocabulary_translation;
              } else if (item.vocabulary_translation_lang === "japanese") {
                japanese_translation = item.vocabulary_translation;
              } else if (item.vocabulary_translation_lang === "korean") {
                korean_translation = item.vocabulary_translation;
              }
            } else {
              // 向後相容：使用舊的欄位格式
              definition = item.definition || "";
              translation = item.english_definition || "";
              japanese_translation = item.japanese_translation || "";
              korean_translation = item.korean_translation || "";
              selectedWordLanguage = item.selectedWordLanguage || "chinese";
            }

            // 處理例句翻譯：優先使用新的統一欄位
            let example_sentence_translation = "";
            let example_sentence_japanese = "";
            let example_sentence_korean = "";
            let selectedSentenceLanguage: SentenceTranslationLanguage =
              "chinese";

            if (
              item.example_sentence_translation_lang &&
              item.example_sentence_translation
            ) {
              // 使用新的統一欄位格式
              selectedSentenceLanguage = item.example_sentence_translation_lang;
              if (item.example_sentence_translation_lang === "chinese") {
                example_sentence_translation =
                  item.example_sentence_translation;
              } else if (
                item.example_sentence_translation_lang === "japanese"
              ) {
                example_sentence_japanese = item.example_sentence_translation;
              } else if (item.example_sentence_translation_lang === "korean") {
                example_sentence_korean = item.example_sentence_translation;
              }
            } else {
              // 向後相容：使用舊的欄位格式
              example_sentence_translation =
                item.example_sentence_translation || "";
              example_sentence_japanese = item.example_sentence_japanese || "";
              example_sentence_korean = item.example_sentence_korean || "";
              selectedSentenceLanguage =
                item.selectedSentenceLanguage || "chinese";
            }

            return {
              id: (index + 1).toString(),
              text: item.text || "",
              definition,
              translation,
              japanese_translation,
              korean_translation,
              audioUrl: item.audio_url || "",
              imageUrl: item.image_url || "",
              selectedWordLanguage,
              selectedSentenceLanguage,
              example_sentence: item.example_sentence || "",
              example_sentence_translation,
              example_sentence_japanese,
              example_sentence_korean,
              partsOfSpeech: item.parts_of_speech || [],
            };
          },
        );
        setRows(convertedRows);
      }
    } catch (error) {
      console.error("Failed to load content:", error);
      toast.error(t("contentEditor.messages.loadingContentFailed"));
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
      image_url: row.imageUrl || "", // 圖片 URL
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
      toast.error(t("contentEditor.messages.maxRowsReached"));
      return;
    }
    // 找出最大的 ID 數字，然後加 1
    const maxId = Math.max(...rows.map((r) => parseInt(String(r.id)) || 0));
    const newRow: ContentRow = {
      id: (maxId + 1).toString(),
      text: "",
      definition: "",
      translation: "",
      imageUrl: "",
      selectedWordLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
    };
    setRows([...rows, newRow]);
  };

  const handleDeleteRow = (index: number) => {
    if (rows.length <= 1) {
      toast.error(t("contentEditor.messages.minRowsRequired"));
      return;
    }
    const newRows = rows.filter((_, i) => i !== index);
    setRows(newRows);
  };

  const handleCopyRow = (index: number) => {
    if (rows.length >= 15) {
      toast.error(t("contentEditor.messages.maxRowsReached"));
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

        toast.success(t("contentEditor.messages.audioRemoved"));
      } catch (error) {
        console.error("Failed to remove audio:", error);
        toast.error(t("contentEditor.messages.removeAudioFailed"));
        // 恢復原始狀態
        const originalRows = [...rows];
        setRows(originalRows);
      }
    } else {
      toast.info(t("contentEditor.messages.audioRemoved"));
    }
  };

  // 圖片上傳狀態
  const [imageUploading, setImageUploading] = useState(false);

  // 圖片上傳處理
  const handleImageUpload = async (index: number, file: File) => {
    // 檢查檔案大小 (2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error(t("vocabularySet.image.tooLarge"));
      return;
    }

    // 檢查檔案類型
    const validTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
    if (!validTypes.includes(file.type)) {
      toast.error(t("vocabularySet.image.invalidType"));
      return;
    }

    setImageUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (editingContent?.id) {
        formData.append("content_id", editingContent.id.toString());
        formData.append("item_index", index.toString());
      }

      const response = await apiClient.uploadImage(formData);
      const imageUrl = response.image_url;

      // 更新本地狀態
      const newRows = [...rows];
      newRows[index] = { ...newRows[index], imageUrl };
      setRows(newRows);

      toast.success(t("vocabularySet.image.uploadSuccess"));
    } catch (error) {
      console.error("Image upload failed:", error);
      toast.error(t("vocabularySet.image.uploadFailed"));
    } finally {
      setImageUploading(false);
    }
  };

  // 移除圖片
  const handleRemoveImage = (index: number) => {
    const newRows = [...rows];
    newRows[index] = { ...newRows[index], imageUrl: "" };
    setRows(newRows);
    toast.info(t("vocabularySet.image.removed"));
  };

  // 剪貼簿貼上圖片功能
  useEffect(() => {
    const handlePaste = async (e: ClipboardEvent) => {
      // 從剪貼簿獲取圖片
      const items = e.clipboardData?.items;
      const files = e.clipboardData?.files;

      let imageBlob: Blob | null = null;

      // 方法 1: 從 DataTransferItemList 獲取（適用於複製圖檔）
      if (items) {
        for (let i = 0; i < items.length; i++) {
          if (items[i].kind === "file" && items[i].type.startsWith("image/")) {
            imageBlob = items[i].getAsFile();
            break;
          }
        }
      }

      // 方法 2: 從 FileList 獲取（適用於 macOS 截圖）
      if (!imageBlob && files && files.length > 0) {
        for (let i = 0; i < files.length; i++) {
          if (files[i].type.startsWith("image/")) {
            imageBlob = files[i];
            break;
          }
        }
      }

      // 如果沒有圖片，讓預設行為處理（文字貼上）
      if (!imageBlob) return;

      // 檢查是否有選中的行
      if (activeRowIndex === null) {
        toast.info(t("vocabularySet.image.pasteSelectRow"));
        return;
      }

      // 檢查該行是否已有圖片
      if (rows[activeRowIndex].imageUrl) {
        toast.info(t("vocabularySet.image.pasteHasImage"));
        return;
      }

      // 阻止預設行為
      e.preventDefault();

      // 轉換為 File 並上傳
      const ext = imageBlob.type.split("/")[1] || "png";
      const file = new File([imageBlob], `pasted-image.${ext}`, {
        type: imageBlob.type,
      });
      await handleImageUpload(activeRowIndex, file);
    };

    document.addEventListener("paste", handlePaste);
    return () => document.removeEventListener("paste", handlePaste);
  }, [activeRowIndex, rows, t]);

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
        } else if (editingContent?.id) {
          // 編輯模式：直接呼叫 API 更新
          try {
            const updateData = {
              title: title || editingContent?.title,
              items,
            };

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
            toast.error(
              t("contentEditor.messages.updateFailedButAudioGenerated"),
            );
          }
        }

        // 關閉 modal 但不要關閉 panel
        setTtsModalOpen(false);
        setSelectedRow(null);
      }
    }
  };

  // ========== 靜默自動生成函數（用於儲存時自動補齊）==========

  /**
   * 靜默批次生成翻譯（成功不跳 toast，失敗才跳）
   * @returns 是否成功
   */
  const autoGenerateTranslationsSilently = async (
    currentRows: ContentRow[],
  ): Promise<{ success: boolean; updatedRows: ContentRow[] }> => {
    const batchLang = lastSelectedWordLang;
    const langConfig = WORD_TRANSLATION_LANGUAGES.find(
      (l) => l.value === batchLang,
    );
    const langCode = langConfig?.code || "zh-TW";

    // 收集需要翻譯的項目（依語言檢查對應欄位）
    const itemsToTranslate: { index: number; text: string }[] = [];

    currentRows.forEach((row, index) => {
      if (row.text && row.text.trim()) {
        let hasTranslation = false;
        if (batchLang === "chinese" && row.definition) hasTranslation = true;
        else if (batchLang === "english" && row.translation)
          hasTranslation = true;
        else if (batchLang === "japanese" && row.japanese_translation)
          hasTranslation = true;
        else if (batchLang === "korean" && row.korean_translation)
          hasTranslation = true;

        if (!hasTranslation) {
          itemsToTranslate.push({ index, text: row.text });
        }
      }
    });

    if (itemsToTranslate.length === 0) {
      return { success: true, updatedRows: currentRows };
    }

    const newRows = [...currentRows];

    try {
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

      // 需要辨識詞性：中文用 batchTranslateWithPos，其他用 batchTranslate
      if (needsPOS.length > 0) {
        const texts = needsPOS.map((item) => item.text);
        if (batchLang === "chinese") {
          const posResponse = await apiClient.batchTranslateWithPos(
            texts,
            langCode,
          );
          const results = posResponse.results || [];
          needsPOS.forEach((item, idx) => {
            if (results[idx]) {
              const parsed = extractFirstDefinition(
                results[idx].translation,
              );
              newRows[item.index].definition = parsed.text;
              if (
                results[idx].parts_of_speech &&
                results[idx].parts_of_speech.length > 0
              ) {
                newRows[item.index].partsOfSpeech = convertAbbreviatedPOS(
                  results[idx].parts_of_speech,
                );
              } else if (parsed.pos) {
                newRows[item.index].partsOfSpeech = convertAbbreviatedPOS([
                  parsed.pos,
                ]);
              }
              newRows[item.index].selectedWordLanguage = batchLang;
            }
          });
        } else {
          const translateResponse = await apiClient.batchTranslate(
            texts,
            langCode,
          );
          const translations =
            (translateResponse as { translations?: string[] }).translations ||
            [];
          needsPOS.forEach((item, idx) => {
            const raw = translations[idx] || item.text;
            const parsed = extractFirstDefinition(raw);
            if (batchLang === "english") {
              newRows[item.index].translation = parsed.text;
            } else if (batchLang === "japanese") {
              newRows[item.index].japanese_translation = parsed.text;
            } else if (batchLang === "korean") {
              newRows[item.index].korean_translation = parsed.text;
            }
            if (parsed.pos) {
              newRows[item.index].partsOfSpeech = convertAbbreviatedPOS([
                parsed.pos,
              ]);
            }
            newRows[item.index].selectedWordLanguage = batchLang;
          });
        }
      }

      // 已有詞性的項目只翻譯
      if (hasPOS.length > 0) {
        const texts = hasPOS.map((item) => item.text);
        const translateResponse = await apiClient.batchTranslate(
          texts,
          langCode,
        );
        const translations =
          (translateResponse as { translations?: string[] }).translations || [];

        hasPOS.forEach((item, idx) => {
          const raw = translations[idx] || item.text;
          const parsed = extractFirstDefinition(raw);
          if (batchLang === "chinese") {
            newRows[item.index].definition = parsed.text;
          } else if (batchLang === "english") {
            newRows[item.index].translation = parsed.text;
          } else if (batchLang === "japanese") {
            newRows[item.index].japanese_translation = parsed.text;
          } else if (batchLang === "korean") {
            newRows[item.index].korean_translation = parsed.text;
          }
          if (parsed.pos) {
            newRows[item.index].partsOfSpeech = convertAbbreviatedPOS([
              parsed.pos,
            ]);
          }
          newRows[item.index].selectedWordLanguage = batchLang;
        });
      }

      return { success: true, updatedRows: newRows };
    } catch (error) {
      console.error("Auto translation error:", error);
      toast.error(t("contentEditor.messages.batchTranslationFailed"));
      return { success: false, updatedRows: currentRows };
    }
  };

  /**
   * 靜默批次生成音檔（成功不跳 toast，失敗才跳）
   * 為每個有 text 但沒有 audioUrl 的單字生成音檔
   * @returns 是否成功
   */
  const autoGenerateAudioSilently = async (
    currentRows: ContentRow[],
  ): Promise<{ success: boolean; updatedRows: ContentRow[] }> => {
    // 收集需要生成 TTS 的單字（有 text 但沒有 audioUrl）
    const textsToGenerate = currentRows
      .filter((row) => row.text && row.text.trim() && !row.audioUrl)
      .map((row) => row.text.trim());

    if (textsToGenerate.length === 0) {
      return { success: true, updatedRows: currentRows };
    }

    try {
      // 批次生成 TTS（使用預設美國女聲）
      const result = await apiClient.batchGenerateTTS(
        textsToGenerate,
        "en-US-JennyNeural",
        "+0%",
        "+0%",
      );

      if (
        result &&
        typeof result === "object" &&
        "audio_urls" in result &&
        Array.isArray(result.audio_urls)
      ) {
        const newRows = [...currentRows];
        let audioIndex = 0;

        for (let i = 0; i < newRows.length; i++) {
          if (
            newRows[i].text &&
            newRows[i].text.trim() &&
            !newRows[i].audioUrl
          ) {
            const audioUrl = (result as { audio_urls: string[] }).audio_urls[
              audioIndex
            ];
            newRows[i].audioUrl = audioUrl.startsWith("http")
              ? audioUrl
              : `${import.meta.env.VITE_API_URL}${audioUrl}`;
            audioIndex++;
          }
        }

        return { success: true, updatedRows: newRows };
      }

      return { success: true, updatedRows: currentRows };
    } catch (error) {
      console.error("Auto TTS generation failed:", error);
      toast.error(t("contentEditor.messages.batchGenerationFailed"));
      return { success: false, updatedRows: currentRows };
    }
  };

  // ========== 原有函數 ==========

  const handleBatchGenerateTTS = async () => {
    try {
      // 收集需要生成 TTS 的單字（不是例句）
      const textsToGenerate = rows
        .filter((row) => row.text && row.text.trim() && !row.audioUrl)
        .map((row) => row.text.trim());

      if (textsToGenerate.length === 0) {
        toast.info(t("vocabularySet.messages.allItemsHaveAudioOrEmpty"));
        return;
      }

      toast.info(
        t("vocabularySet.messages.generatingWordAudio", {
          count: textsToGenerate.length,
        }),
      );

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
        // 更新 rows 的 audioUrl（單字音檔）
        const newRows = [...rows];
        let audioIndex = 0;

        for (let i = 0; i < newRows.length; i++) {
          if (
            newRows[i].text &&
            newRows[i].text.trim() &&
            !newRows[i].audioUrl
          ) {
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
            t("contentEditor.messages.audioGeneratedSuccessfully", {
              count: textsToGenerate.length,
            }),
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

            toast.success(
              t("contentEditor.messages.audioGeneratedAndSaved", {
                count: textsToGenerate.length,
              }),
            );
          } catch (error) {
            console.error("Failed to save TTS:", error);
            toast.error(
              t("contentEditor.messages.savingFailedButAudioGenerated"),
            );
          }
        } else {
          // 沒有 content ID，只是本地更新
          toast.success(
            t("contentEditor.messages.audioGeneratedSuccessfully", {
              count: textsToGenerate.length,
            }),
          );
        }
      }
    } catch (error) {
      console.error("Batch TTS generation failed:", error);
      toast.error(t("contentEditor.messages.batchGenerationFailed"));
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
      toast.error(t("contentEditor.messages.enterTextFirst"));
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
    toast.info(t("contentEditor.messages.generatingTranslation"));

    try {
      if (needAutoDetectPOS) {
        // 使用新的 API 同時翻譯和辨識詞性（僅中文）
        const response = await apiClient.translateWithPos(
          newRows[index].text,
          langConfig?.code || "zh-TW",
        );

        // 自動填入詞性（轉換縮寫為完整名稱）
        if (response.parts_of_speech && response.parts_of_speech.length > 0) {
          newRows[index].partsOfSpeech = convertAbbreviatedPOS(
            response.parts_of_speech,
          );
        }

        // 中文多義檢查
        const multiDefs = parseMultipleDefinitions(response.translation);
        if (multiDefs.length > 1) {
          setDefinitionPicker({
            rowIndex: index,
            word: newRows[index].text,
            options: multiDefs,
            targetLang: "chinese",
          });
          newRows[index].selectedWordLanguage = targetLang;
          setRows(newRows);
          return;
        }

        // 單個定義：去掉編號前綴，提取詞性
        const parsed = extractPosFromTranslation(response.translation);
        if (parsed.pos) {
          newRows[index].partsOfSpeech = convertAbbreviatedPOS([
            parsed.pos,
          ]);
        }
        newRows[index].definition = parsed.text;
      } else {
        // 已有詞性或非中文，只翻譯不改變詞性
        const response = (await apiClient.translateText(
          newRows[index].text,
          langConfig?.code || "zh-TW",
        )) as { translation: string };

        // 多義檢查：所有語言，若有多個定義則彈出選擇器
        {
          const multiDefs = parseMultipleDefinitions(response.translation);
          if (multiDefs.length > 1) {
            setDefinitionPicker({
              rowIndex: index,
              word: newRows[index].text,
              options: multiDefs,
              targetLang,
            });
            newRows[index].selectedWordLanguage = targetLang;
            setRows(newRows);
            return;
          }
        }

        // 根據目標語言寫入對應欄位
        {
          const parsed = extractPosFromTranslation(
            response.translation,
          );
          if (parsed.pos) {
            newRows[index].partsOfSpeech = convertAbbreviatedPOS([
              parsed.pos,
            ]);
          }
          if (targetLang === "chinese") {
            newRows[index].definition = parsed.text;
          } else if (targetLang === "english") {
            newRows[index].translation = parsed.text;
          } else if (targetLang === "japanese") {
            newRows[index].japanese_translation = parsed.text;
          } else if (targetLang === "korean") {
            newRows[index].korean_translation = parsed.text;
          }
        }
      }

      // 記錄最後選擇的語言
      newRows[index].selectedWordLanguage = targetLang;
      setRows(newRows);
      toast.success(
        needAutoDetectPOS
          ? t("vocabularySet.messages.translationAndPOSComplete")
          : t("contentEditor.messages.translationComplete"),
      );
    } catch (error) {
      console.error("Translation error:", error);
      toast.error(t("contentEditor.messages.translationFailed"));
    }
  };

  const handleBatchGenerateDefinitions = async () => {
    const batchLang = lastSelectedWordLang;
    const langConfig = WORD_TRANSLATION_LANGUAGES.find(
      (l) => l.value === batchLang,
    );
    const langCode = langConfig?.code || "zh-TW";

    // 依語言判斷哪些項目缺少翻譯
    const getTranslationField = (row: ContentRow) => {
      if (batchLang === "chinese") return row.definition;
      if (batchLang === "english") return row.translation;
      if (batchLang === "japanese") return row.japanese_translation;
      if (batchLang === "korean") return row.korean_translation;
      return row.definition;
    };

    const itemsToTranslate: { index: number; text: string }[] = [];
    rows.forEach((row, index) => {
      if (row.text && !getTranslationField(row)) {
        itemsToTranslate.push({ index, text: row.text });
      }
    });

    if (itemsToTranslate.length === 0) {
      toast.info(t("contentEditor.messages.noItemsNeedTranslation"));
      return;
    }

    toast.info(t("contentEditor.messages.startingBatchTranslation"));
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

      // 對需要辨識詞性的項目：中文用 batchTranslateWithPos，其他用 batchTranslate
      if (needsPOS.length > 0) {
        const texts = needsPOS.map((item) => item.text);
        if (batchLang === "chinese") {
          const posResponse = await apiClient.batchTranslateWithPos(
            texts,
            langCode,
          );
          const results = posResponse.results || [];
          needsPOS.forEach((item, idx) => {
            if (results[idx]) {
              const parsed = extractFirstDefinition(
                results[idx].translation,
              );
              newRows[item.index].definition = parsed.text;
              if (
                results[idx].parts_of_speech &&
                results[idx].parts_of_speech.length > 0
              ) {
                newRows[item.index].partsOfSpeech = convertAbbreviatedPOS(
                  results[idx].parts_of_speech,
                );
              } else if (parsed.pos) {
                newRows[item.index].partsOfSpeech = convertAbbreviatedPOS([
                  parsed.pos,
                ]);
              }
            }
            newRows[item.index].selectedWordLanguage = batchLang;
          });
        } else {
          const translateResponse = await apiClient.batchTranslate(
            texts,
            langCode,
          );
          const translations =
            (translateResponse as { translations?: string[] }).translations ||
            [];
          needsPOS.forEach((item, idx) => {
            const raw = translations[idx] || item.text;
            const parsed = extractFirstDefinition(raw);
            if (batchLang === "english") {
              newRows[item.index].translation = parsed.text;
            } else if (batchLang === "japanese") {
              newRows[item.index].japanese_translation = parsed.text;
            } else if (batchLang === "korean") {
              newRows[item.index].korean_translation = parsed.text;
            }
            if (parsed.pos) {
              newRows[item.index].partsOfSpeech = convertAbbreviatedPOS([
                parsed.pos,
              ]);
            }
            newRows[item.index].selectedWordLanguage = batchLang;
          });
        }
      }

      // 對已有詞性的項目只翻譯
      if (hasPOS.length > 0) {
        const texts = hasPOS.map((item) => item.text);
        const translateResponse = await apiClient.batchTranslate(
          texts,
          langCode,
        );
        const translations =
          (translateResponse as { translations?: string[] }).translations || [];

        hasPOS.forEach((item, idx) => {
          const raw = translations[idx] || item.text;
          const parsed = extractFirstDefinition(raw);
          if (batchLang === "chinese") {
            newRows[item.index].definition = parsed.text;
          } else if (batchLang === "english") {
            newRows[item.index].translation = parsed.text;
          } else if (batchLang === "japanese") {
            newRows[item.index].japanese_translation = parsed.text;
          } else if (batchLang === "korean") {
            newRows[item.index].korean_translation = parsed.text;
          }
          if (parsed.pos) {
            newRows[item.index].partsOfSpeech = convertAbbreviatedPOS([
              parsed.pos,
            ]);
          }
          newRows[item.index].selectedWordLanguage = batchLang;
        });
      }

      setRows(newRows);
      toast.success(
        t("vocabularySet.messages.batchTranslationSuccess", {
          total: itemsToTranslate.length,
          posCount: needsPOS.length > 0 ? needsPOS.length : 0,
        }),
      );
    } catch (error) {
      console.error("Batch translation error:", error);
      toast.error(t("contentEditor.messages.batchTranslationFailed"));
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
      toast.error(t("vocabularySet.messages.enterExampleFirst"));
      return;
    }

    const langConfig = SENTENCE_TRANSLATION_LANGUAGES.find(
      (l) => l.value === targetLang,
    );
    toast.info(t("vocabularySet.messages.generatingExampleTranslation"));

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
      toast.success(t("vocabularySet.messages.exampleTranslationComplete"));
    } catch (error) {
      console.error("Example sentence translation error:", error);
      toast.error(t("vocabularySet.messages.exampleTranslationFailed"));
    }
  };

  // 打開 AI 生成例句對話框
  const handleOpenAIGenerateModal = (index: number | null) => {
    setAiGenerateTargetIndex(index);
    // 🔥 階段2：每次打開 modal 都重設為 Program level
    setAiGenerateLevel(programLevel || "A1");
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
        toast.info(t("vocabularySet.messages.noItemsForExampleGeneration"));
        setIsGeneratingAI(false);
        return;
      }

      // 收集需要生成的單字、翻譯和詞性
      const wordsToGenerate = targetIndices.map((idx) => ({
        word: rows[idx].text,
        definition: rows[idx].definition || "",
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

      toast.info(
        t("vocabularySet.messages.generatingExamples", {
          count: wordsToGenerate.length,
        }),
      );

      // 呼叫 API 生成例句
      const response = await apiClient.generateSentences({
        words: wordsToGenerate.map((w) => w.word),
        definitions: wordsToGenerate.map((w) => w.definition),
        lesson_id: lessonId,
        level: aiGenerateLevel,
        prompt: aiGeneratePrompt || undefined,
        translate_to: targetLanguage || undefined,
        parts_of_speech: wordsToGenerate.map((w) => w.partsOfSpeech),
      });

      // 更新 rows
      const newRows = [...rows];
      const sentencesData = (
        response as {
          sentences?: Array<{
            sentence: string;
            translation?: string;
            word: string;
          }>;
        }
      ).sentences;

      if (!sentencesData || !Array.isArray(sentencesData)) {
        toast.error(
          t("vocabularySet.messages.exampleGenerationFailed") ||
            "例句生成失敗，請稍後再試",
        );
        return;
      }
      const results = sentencesData;

      // 驗證陣列長度是否匹配，防止錯位
      if (results.length !== targetIndices.length) {
        console.error(
          `Array mismatch: expected ${targetIndices.length} sentences, got ${results.length}`,
        );
        toast.warning(
          t("vocabularySet.messages.exampleGenerationPartialFailure") ||
            "部分單字造句可能失敗，請檢查結果",
        );
        // 繼續處理，但已警告用戶部分可能失敗
      }

      // 使用 Map 優化查找效率，防止 O(n²) 複雜度
      const resultMap = new Map(results.map((r) => [r.word, r]));

      // 使用 word 欄位進行匹配，而非依賴索引，以防止錯位
      targetIndices.forEach((idx) => {
        const targetWord = newRows[idx].text;

        // 先清空現有的例句和翻譯
        newRows[idx].example_sentence = "";
        newRows[idx].example_sentence_translation = "";

        // 使用 Map 查找對應的句子（O(1) 複雜度）
        const matchedResult = resultMap.get(targetWord);

        if (matchedResult) {
          newRows[idx].example_sentence = matchedResult.sentence;
          // 只有勾選翻譯且 API 有返回翻譯時才填入
          if (aiGenerateTranslate && matchedResult.translation) {
            newRows[idx].example_sentence_translation =
              matchedResult.translation;
          }
        } else {
          console.warn(
            `No sentence found for word: ${targetWord} at index ${idx}`,
          );
        }
      });

      setRows(newRows);
      toast.success(
        t("vocabularySet.messages.examplesGeneratedSuccess", {
          count: results.length,
        }),
      );
      setAiGenerateModalOpen(false);
    } catch (error) {
      console.error("AI generate sentences error:", error);
      toast.error(t("vocabularySet.messages.exampleGenerationFailed"));
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
      toast.error(t("contentEditor.messages.enterContent"));
      return;
    }

    toast.info(
      t("contentEditor.messages.processingItems", { count: lines.length }),
    );

    // 清除空白 items
    const nonEmptyRows = rows.filter((row) => row.text && row.text.trim());

    // 建立新 items
    let newItems: ContentRow[] = lines.map((text, index) => ({
      id: `batch-${Date.now()}-${index}`,
      text,
      definition: "",
      translation: "",
      selectedWordLanguage: lastSelectedWordLang,
      example_sentence: "",
      example_sentence_translation: "",
    }));

    const batchLang = lastSelectedWordLang;
    const batchLangCode =
      WORD_TRANSLATION_LANGUAGES.find((l) => l.value === batchLang)?.code ||
      "zh-TW";

    // 批次處理 TTS 和翻譯
    if (autoTTS || autoTranslate) {
      try {
        if (autoTTS) {
          // Get voice and rate from selected TTS settings (Issue #121)
          const { voice, rate } = getVoiceAndRate(
            batchTTSAccent,
            batchTTSGender,
            batchTTSSpeed,
          );
          // Save settings for next time
          saveBatchTTSSettings();

          const ttsResult = await apiClient.batchGenerateTTS(
            lines,
            voice,
            rate,
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
          if (batchLang === "chinese") {
            // 中文：使用 batchTranslateWithPos 同時取得翻譯和詞性
            const posResponse = await apiClient.batchTranslateWithPos(
              lines,
              batchLangCode,
            );
            const results = posResponse.results || [];
            newItems = newItems.map((item, i) => {
              const parsed = extractFirstDefinition(
                results[i]?.translation || "",
              );
              return {
                ...item,
                definition: parsed.text,
                partsOfSpeech:
                  results[i]?.parts_of_speech?.length > 0
                    ? convertAbbreviatedPOS(results[i].parts_of_speech)
                    : parsed.pos
                      ? convertAbbreviatedPOS([parsed.pos])
                      : [],
              };
            });
          } else {
            // 英/日/韓：使用 batchTranslate
            const translateResponse = await apiClient.batchTranslate(
              lines,
              batchLangCode,
            );
            const translations =
              (translateResponse as { translations?: string[] })
                .translations || [];
            newItems = newItems.map((item, i) => {
              const parsed = extractFirstDefinition(
                translations[i] || "",
              );
              const updated: Partial<ContentRow> = {
                partsOfSpeech: parsed.pos
                  ? convertAbbreviatedPOS([parsed.pos])
                  : item.partsOfSpeech,
              };
              if (batchLang === "english")
                updated.translation = parsed.text;
              else if (batchLang === "japanese")
                updated.japanese_translation = parsed.text;
              else if (batchLang === "korean")
                updated.korean_translation = parsed.text;
              return { ...item, ...updated };
            });
          }
        }
      } catch (error) {
        console.error("Batch processing error:", error);
        toast.error(t("contentEditor.messages.batchProcessingFailed"));
        return;
      }
    }

    // 合併新舊項目
    const updatedRows = [...nonEmptyRows, ...newItems];

    // 只更新前端狀態，不直接儲存到資料庫
    // 使用者需要按最終的「儲存」按鈕才會執行 POST/PUT
    setRows(updatedRows);

    toast.success(
      t("vocabularySet.messages.itemsAdded", {
        added: lines.length,
        total: updatedRows.length,
      }),
    );

    setBatchPasteDialogOpen(false);
    setBatchPasteText("");
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">
            {t("contentEditor.messages.loading")}
          </p>
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
            {t("contentEditor.labels.title")}{" "}
            <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={t("contentEditor.placeholders.enterContentTitle")}
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
            title={t("readingAssessmentPanel.batchActions.batchPasteTooltip")}
          >
            <Clipboard className="h-4 w-4 mr-1" />
            {t("readingAssessmentPanel.batchActions.batchPaste")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleBatchGenerateTTS}
            className="bg-yellow-100 hover:bg-yellow-200 border-yellow-300"
            title={t(
              "readingAssessmentPanel.batchActions.batchGenerateTTSTooltip",
            )}
          >
            <Volume2 className="h-4 w-4 mr-1" />
            {t("readingAssessmentPanel.batchActions.batchGenerateTTS")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleBatchGenerateDefinitions()}
            className="bg-green-100 hover:bg-green-200 border-green-300"
            title={t(
              "readingAssessmentPanel.batchActions.batchGenerateTranslationTooltip",
            )}
          >
            <Globe className="h-4 w-4 mr-1" />
            {t("readingAssessmentPanel.batchActions.batchGenerateTranslation")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleOpenAIGenerateModal(null)}
            className="bg-purple-100 hover:bg-purple-200 border-purple-300"
            title={t("vocabularySet.tooltips.batchAIGenerateExamples")}
          >
            <Globe className="h-4 w-4 mr-1" />
            {t("vocabularySet.buttons.batchAIGenerateExamples")}
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
                  handleImageUpload={handleImageUpload}
                  handleRemoveImage={handleRemoveImage}
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
                  imageUploading={imageUploading}
                  isActive={activeRowIndex === index}
                  onRowFocus={() => setActiveRowIndex(index)}
                  onWordLanguageChange={setLastSelectedWordLang}
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
              {t("contentEditor.buttons.addItem")}
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

      {/* 多義 Picker Dialog（英英釋義 / 中文翻譯） */}
      <Dialog
        open={definitionPicker !== null}
        onOpenChange={(open) => {
          if (!open) setDefinitionPicker(null);
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {(() => {
                const lang = definitionPicker?.targetLang;
                const word = definitionPicker?.word;
                if (lang === "chinese") return `選擇「${word}」的中文翻譯`;
                if (lang === "japanese") return `選擇「${word}」的日文翻譯`;
                if (lang === "korean") return `選擇「${word}」的韓文翻譯`;
                return `選擇「${word}」的英英釋義`;
              })()}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-2 py-2">
            {definitionPicker?.options.map((def, i) => (
              <button
                key={i}
                onClick={() => {
                  const parsed = extractPosFromTranslation(def);
                  const newRows = [...rows];
                  const ri = definitionPicker.rowIndex;
                  if (parsed.pos) {
                    newRows[ri].partsOfSpeech =
                      convertAbbreviatedPOS([parsed.pos]);
                  }
                  const tLang = definitionPicker.targetLang;
                  if (tLang === "chinese") {
                    newRows[ri].definition = parsed.text;
                  } else if (tLang === "english") {
                    newRows[ri].translation = parsed.text;
                  } else if (tLang === "japanese") {
                    newRows[ri].japanese_translation = parsed.text;
                  } else if (tLang === "korean") {
                    newRows[ri].korean_translation = parsed.text;
                  }
                  setRows(newRows);
                  setDefinitionPicker(null);
                  toast.success(
                    t("contentEditor.messages.translationComplete"),
                  );
                }}
                className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-all text-sm"
              >
                {def}
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Batch Paste Dialog */}
      <Dialog
        open={batchPasteDialogOpen}
        onOpenChange={setBatchPasteDialogOpen}
      >
        <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
          <DialogHeader className="pb-4 flex-shrink-0">
            <DialogTitle className="text-2xl font-bold text-gray-900">
              {t("contentEditor.modals.batchPasteTitle")}
            </DialogTitle>
            <p className="text-sm text-gray-500 mt-2">
              {t("contentEditor.modals.batchPasteSubtitle")}
            </p>
          </DialogHeader>
          <div className="space-y-6 overflow-y-auto flex-1 min-h-0">
            <div>
              <label className="text-base font-semibold text-gray-800 mb-3 block">
                {t("contentEditor.labels.pasteContent")}
              </label>
              <textarea
                value={batchPasteText}
                onChange={(e) => setBatchPasteText(e.target.value)}
                placeholder="apple&#10;banana&#10;orange"
                className="w-full min-h-80 max-h-[60vh] px-4 py-3 border-2 border-gray-300 rounded-lg font-mono text-base focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all resize-y overflow-y-auto"
              />
              <div className="text-xs text-gray-500 mt-2">
                {batchPasteText.split("\n").filter((line) => line.trim())
                  .length || 0}{" "}
                {t("contentEditor.messages.items")}
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
                  {t("contentEditor.checkboxes.autoGenerateTTS")}
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
                  {t("contentEditor.checkboxes.autoTranslate")}
                </span>
              </label>
            </div>

            {/* TTS Settings Section (Issue #121) */}
            {batchPasteAutoTTS && (
              <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <label className="text-sm font-semibold text-gray-800 mb-3 block">
                  {t("contentEditor.ttsSettings.title")}
                </label>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs font-medium text-gray-600 mb-1 block">
                      {t("contentEditor.ttsSettings.accent")}
                    </label>
                    <select
                      value={batchTTSAccent}
                      onChange={(e) => setBatchTTSAccent(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    >
                      {batchTTSAccents.map((accent) => (
                        <option key={accent} value={accent}>
                          {accent}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600 mb-1 block">
                      {t("contentEditor.ttsSettings.gender")}
                    </label>
                    <select
                      value={batchTTSGender}
                      onChange={(e) => setBatchTTSGender(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    >
                      {batchTTSGenders.map((gender) => (
                        <option key={gender} value={gender}>
                          {gender}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600 mb-1 block">
                      {t("contentEditor.ttsSettings.speed")}
                    </label>
                    <select
                      value={batchTTSSpeed}
                      onChange={(e) => setBatchTTSSpeed(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    >
                      {batchTTSSpeeds.map((speed) => (
                        <option key={speed} value={speed}>
                          {speed}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>
          <DialogFooter className="pt-6 flex-shrink-0 border-t border-gray-200 mt-4">
            <Button
              variant="outline"
              onClick={() => setBatchPasteDialogOpen(false)}
              className="px-6 py-2 text-base"
            >
              {t("contentEditor.buttons.cancel")}
            </Button>
            <Button
              onClick={() =>
                handleBatchPaste(batchPasteAutoTTS, batchPasteAutoTranslate)
              }
              className="px-6 py-2 text-base bg-blue-600 hover:bg-blue-700"
            >
              {t("contentEditor.buttons.confirmPaste")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI 生成例句對話框 */}
      <Dialog open={aiGenerateModalOpen} onOpenChange={setAiGenerateModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold">
              {t("vocabularySet.modals.aiGenerateExamplesTitle")}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* 難度等級選擇 */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                {t("vocabularySet.labels.difficultyLevel")}
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
                {t("vocabularySet.labels.aiPrompt")}
              </label>
              <textarea
                value={aiGeneratePrompt}
                onChange={(e) => setAiGeneratePrompt(e.target.value)}
                placeholder={t("vocabularySet.placeholders.aiPromptExample")}
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
                  {t("vocabularySet.labels.translateTo")}
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
                <option value="中文">
                  {t("contentEditor.translationLanguages.chinese")}
                </option>
                <option value="日文">
                  {t("contentEditor.translationLanguages.japanese")}
                </option>
                <option value="韓文">
                  {t("contentEditor.translationLanguages.korean")}
                </option>
              </select>
            </div>

            {/* 生成目標提示 */}
            <div className="text-sm bg-amber-50 border border-amber-200 p-3 rounded-lg">
              {aiGenerateTargetIndex !== null ? (
                <div>
                  <span className="text-amber-700">
                    {t("vocabularySet.messages.willRegenerateFor", {
                      word: rows[aiGenerateTargetIndex]?.text || "",
                    })}
                  </span>
                  {rows[aiGenerateTargetIndex]?.example_sentence && (
                    <div className="text-amber-600 text-xs mt-1">
                      {t("vocabularySet.messages.existingWillBeOverwritten")}
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <span className="text-amber-700">
                    {t("vocabularySet.messages.wordsWillRegenerate", {
                      count: rows.filter((r) => r.text && r.text.trim()).length,
                    })}
                  </span>
                  <div className="text-amber-600 text-xs mt-1">
                    {t("vocabularySet.messages.allExistingExamples")}
                    {aiGenerateTranslate
                      ? t("vocabularySet.messages.andTranslations")
                      : ""}
                    {t("vocabularySet.messages.willBeOverwritten")}
                    {!aiGenerateTranslate &&
                      `，${t("vocabularySet.messages.translationFieldsCleared")}`}
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
              {t("contentEditor.buttons.cancel")}
            </Button>
            <Button
              onClick={handleAIGenerateSentences}
              disabled={isGeneratingAI}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isGeneratingAI
                ? t("vocabularySet.buttons.generating")
                : t("vocabularySet.buttons.generate")}
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
            disabled={isSaving}
            onClick={async () => {
              // 過濾掉空白項目
              let validRows = rows.filter((row) => row.text && row.text.trim());

              if (validRows.length === 0) {
                toast.error(t("contentEditor.messages.addAtLeastOneItem"));
                return;
              }

              if (!title || title.trim() === "") {
                toast.error(t("contentEditor.messages.enterTitle"));
                return;
              }

              // 開始儲存流程（翻譯 → 音檔 → 儲存 → 干擾選項生成）
              setIsSaving(true);

              try {
                // ========== Step 1: 自動生成缺少的翻譯 ==========
                const translationResult =
                  await autoGenerateTranslationsSilently(validRows);
                if (!translationResult.success) {
                  // 錯誤 toast 已在函數內顯示
                  setIsSaving(false);
                  return;
                }
                validRows = translationResult.updatedRows;

                // ========== Step 2: 自動生成缺少的音檔 ==========
                const audioResult = await autoGenerateAudioSilently(validRows);
                if (!audioResult.success) {
                  // 錯誤 toast 已在函數內顯示
                  setIsSaving(false);
                  return;
                }
                validRows = audioResult.updatedRows;

                // 更新 rows state（讓 UI 顯示生成的內容）
                setRows(
                  rows.map((row) => {
                    const updated = validRows.find((v) => v.id === row.id);
                    return updated || row;
                  }),
                );

                // ========== Step 3: 準備並儲存資料 ==========
                // 注意：例句為選填，不檢查是否缺少
                const saveData = {
                  title: title,
                  items: validRows.map((row) => {
                    // 根據選擇的語言取得對應的單字翻譯
                    const wordLang = row.selectedWordLanguage || "chinese";
                    let vocabularyTranslation = "";
                    if (wordLang === "chinese") {
                      vocabularyTranslation = row.definition || "";
                    } else if (wordLang === "english") {
                      vocabularyTranslation = row.translation || "";
                    } else if (wordLang === "japanese") {
                      vocabularyTranslation = row.japanese_translation || "";
                    } else if (wordLang === "korean") {
                      vocabularyTranslation = row.korean_translation || "";
                    }

                    // 根據選擇的語言取得對應的例句翻譯
                    const sentenceLang =
                      row.selectedSentenceLanguage || "chinese";
                    let exampleTranslation = "";
                    if (sentenceLang === "chinese") {
                      exampleTranslation =
                        row.example_sentence_translation || "";
                    } else if (sentenceLang === "japanese") {
                      exampleTranslation = row.example_sentence_japanese || "";
                    } else if (sentenceLang === "korean") {
                      exampleTranslation = row.example_sentence_korean || "";
                    }

                    return {
                      text: row.text.trim(),
                      // 統一翻譯欄位（新格式）
                      vocabulary_translation: vocabularyTranslation,
                      vocabulary_translation_lang: wordLang,
                      // 向後相容欄位（讓學生 API 能讀到 ContentItem.translation）
                      definition: vocabularyTranslation,
                      // 英文釋義向後相容
                      english_definition:
                        wordLang === "english"
                          ? vocabularyTranslation
                          : row.translation || "",
                      audio_url: row.audioUrl || row.audio_url || "",
                      image_url: row.imageUrl || "",
                      example_sentence: row.example_sentence || "",
                      example_sentence_translation: exampleTranslation,
                      example_sentence_translation_lang: sentenceLang,
                      parts_of_speech: row.partsOfSpeech || [],
                    };
                  }),
                  target_wpm: 60,
                  target_accuracy: 0.8,
                  time_limit_seconds: 180,
                };

                const existingContentId = editingContent?.id || content?.id;

                if (existingContentId) {
                  // 編輯模式：更新現有內容
                  try {
                    await apiClient.updateContent(existingContentId, saveData);

                    toast.success(t("contentEditor.messages.savingSuccess"));

                    if (onSave) {
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      await (onSave as (content?: any) => void | Promise<void>)(
                        {
                          id: existingContentId,
                          title: saveData.title,
                          items: saveData.items,
                        },
                      );
                    }
                  } catch (error) {
                    console.error("Failed to update content:", error);
                    toast.error(t("contentEditor.messages.savingFailed"));
                  }
                } else if (isCreating && lessonId) {
                  // 創建模式：新增內容
                  try {
                    const newContent = await apiClient.createContent(lessonId, {
                      type: "VOCABULARY_SET",
                      ...saveData,
                    });

                    toast.success(
                      t("contentEditor.messages.contentCreatedSuccess"),
                    );

                    if (onSave) {
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      await (onSave as (content?: any) => void | Promise<void>)(
                        newContent,
                      );
                    }
                  } catch (error) {
                    console.error("Failed to create content:", error);
                    toast.error(
                      t("contentEditor.messages.creatingContentFailed"),
                    );
                  }
                }
              } finally {
                setIsSaving(false);
              }
            }}
          >
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t("vocabularySet.saving") || "儲存中..."}
              </>
            ) : (
              t("contentEditor.buttons.save")
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
