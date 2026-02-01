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
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { apiClient, ApiError } from "@/lib/api";
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

// 翻譯語言選項
type TranslationLanguage = "chinese" | "japanese" | "korean";

// Language constants - labels will be translated dynamically using t()
const TRANSLATION_LANGUAGES = [
  { value: "chinese" as const, labelKey: "chinese", code: "zh-TW" },
  { value: "japanese" as const, labelKey: "japanese", code: "ja" },
  { value: "korean" as const, labelKey: "korean", code: "ko" },
];

interface ContentRow {
  id: string | number;
  text: string;
  definition: string;
  audioUrl?: string;
  audio_url?: string;
  translation?: string;
  japanese_translation?: string;
  korean_translation?: string;
  selectedLanguage?: TranslationLanguage; // 最後選擇的語言
  audioSettings?: {
    accent: string;
    gender: string;
    speed: string;
  };
  // Phase 1: Example sentence fields
  example_sentence?: string;
  example_sentence_translation?: string;
  example_sentence_definition?: string;
  has_student_progress?: boolean; // 是否有學生進度
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
    value: string,
  ) => void;
  handleRemoveRow: (index: number) => void;
  handleDuplicateRow: (index: number) => void;
  handleOpenTTSModal: (row: ContentRow) => void;
  handleRemoveAudio: (index: number) => void;
  handleGenerateSingleDefinition: (index: number) => Promise<void>;
  handleGenerateSingleDefinitionWithLang: (
    index: number,
    lang: TranslationLanguage,
  ) => Promise<void>;
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
  rowsLength,
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

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex flex-col sm:flex-row items-start sm:items-center gap-2 p-3 bg-gray-50 rounded-lg"
    >
      <div className="flex items-center gap-1 w-full sm:w-auto">
        {/* Drag handle - ONLY this triggers drag */}
        <div
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing touch-none"
          title={t("contentEditor.tooltips.dragToReorder")}
        >
          <GripVertical className="h-5 w-5 text-gray-400 hover:text-gray-700 transition-colors" />
        </div>
        <span className="text-sm font-medium text-gray-600 w-6">
          {index + 1}
        </span>
      </div>

      <div className="flex-1 w-full space-y-2">
        {/* Text input */}
        <div className="relative">
          <input
            type="text"
            value={row.text}
            onChange={(e) => handleUpdateRow(index, "text", e.target.value)}
            className="w-full px-3 py-2 pr-20 border rounded-md text-sm"
            placeholder={t("contentEditor.placeholders.enterText")}
            maxLength={200}
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-1">
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
                    toast.error(
                      t("contentEditor.messages.cannotPlayRecording"),
                    );
                  });
                }}
                className="p-1 rounded text-green-600 hover:bg-green-100"
                title={t("contentEditor.tooltips.playAudio")}
              >
                <Play className="h-4 w-4" />
              </button>
            )}
            <button
              onClick={() => handleOpenTTSModal(row)}
              className={`p-1 rounded ${
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
                className="p-1 rounded text-red-600 hover:bg-red-100"
                title={t("contentEditor.tooltips.removeAudio")}
              >
                <Trash2 className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>

        {/* Translation textarea */}
        <div className="space-y-2">
          <div className="relative">
            <textarea
              value={(() => {
                const lang = row.selectedLanguage || "chinese";
                if (lang === "chinese") return row.definition || "";
                if (lang === "japanese") return row.japanese_translation || "";
                if (lang === "korean") return row.korean_translation || "";
                return row.definition || "";
              })()}
              onChange={(e) => {
                const lang = row.selectedLanguage || "chinese";
                let field: keyof ContentRow = "definition";
                if (lang === "japanese") field = "japanese_translation";
                else if (lang === "korean") field = "korean_translation";
                handleUpdateRow(index, field, e.target.value);
              }}
              className="w-full px-3 py-2 pr-24 border rounded-md text-sm resize-none"
              placeholder={(() => {
                const lang = row.selectedLanguage || "chinese";
                const langConfig = TRANSLATION_LANGUAGES.find(
                  (l) => l.value === lang,
                );
                return `${t(`contentEditor.translationLanguages.${langConfig?.labelKey || "chinese"}`)}`;
              })()}
              rows={2}
              maxLength={500}
            />
            <div className="absolute right-2 top-2 flex items-center space-x-1">
              <select
                value={row.selectedLanguage || "chinese"}
                onChange={(e) => {
                  const newLang = e.target.value as TranslationLanguage;
                  handleUpdateRow(index, "selectedLanguage", newLang);
                  // Auto-generate when switching language
                  if (row.text && row.text.trim()) {
                    setTimeout(() => {
                      handleGenerateSingleDefinitionWithLang(index, newLang);
                    }, 100);
                  }
                }}
                className="px-1 py-0.5 border rounded text-xs bg-white"
              >
                {TRANSLATION_LANGUAGES.map((lang) => (
                  <option key={lang.value} value={lang.value}>
                    {t(`contentEditor.translationLanguages.${lang.labelKey}`)}
                  </option>
                ))}
              </select>
              <button
                onClick={() => handleGenerateSingleDefinition(index)}
                className="p-1 rounded hover:bg-gray-200 text-gray-600 flex items-center gap-0.5"
                title={t("contentEditor.messages.generatingTranslation")}
              >
                <Globe className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-1 w-full sm:w-auto justify-end">
        <button
          onClick={() => handleDuplicateRow(index)}
          className="p-1 rounded hover:bg-gray-200"
          title={t("contentEditor.tooltips.duplicate")}
        >
          <Copy className="h-4 w-4 text-gray-600" />
        </button>
        <button
          onClick={() => handleRemoveRow(index)}
          className={`p-1 rounded ${
            row.has_student_progress || rowsLength <= 1
              ? "cursor-not-allowed"
              : "hover:bg-gray-200"
          }`}
          title={
            row.has_student_progress
              ? t("contentEditor.tooltips.cannotDeleteWithProgress")
              : t("contentEditor.tooltips.delete")
          }
          disabled={rowsLength <= 1 || row.has_student_progress}
        >
          <Trash2
            className={`h-4 w-4 ${
              rowsLength <= 1 || row.has_student_progress
                ? "text-gray-300"
                : "text-gray-600"
            }`}
          />
        </button>
      </div>
    </div>
  );
}

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
  isAssignmentCopy?: boolean; // 是否為作業副本（需要特別處理刪除）
}

export default function ReadingAssessmentPanel({
  content,
  editingContent,
  onUpdateContent,
  onSave,
  lessonId,
  isCreating = false,
  isAssignmentCopy = false,
}: ReadingAssessmentPanelProps) {
  const { t } = useTranslation();
  const [title, setTitle] = useState("");
  const [rows, setRows] = useState<ContentRow[]>([
    {
      id: "1",
      text: "",
      definition: "",
      translation: "",
      selectedLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
      example_sentence_definition: "",
    },
    {
      id: "2",
      text: "",
      definition: "",
      translation: "",
      selectedLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
      example_sentence_definition: "",
    },
    {
      id: "3",
      text: "",
      definition: "",
      translation: "",
      selectedLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
      example_sentence_definition: "",
    },
  ]);
  const [selectedRow, setSelectedRow] = useState<ContentRow | null>(null);
  const [ttsModalOpen, setTtsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [batchPasteDialogOpen, setBatchPasteDialogOpen] = useState(false);
  const [batchPasteText, setBatchPasteText] = useState("");
  const [batchPasteAutoTTS, setBatchPasteAutoTTS] = useState(false);
  const [batchPasteAutoTranslate, setBatchPasteAutoTranslate] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true); // 🔥 標記是否為初始載入

  // TTS settings for batch paste (Issue #121)
  const [batchTTSAccent, setBatchTTSAccent] = useState("American English");
  const [batchTTSGender, setBatchTTSGender] = useState("Male");
  const [batchTTSSpeed, setBatchTTSSpeed] = useState("Normal x1");
  const [isBatchGeneratingTTS, setIsBatchGeneratingTTS] = useState(false); // 批次生成 TTS 中
  const [isBatchGeneratingTranslation, setIsBatchGeneratingTranslation] =
    useState(false); // 批次生成翻譯中

  // 計算是否有批次操作正在進行
  const isBatchProcessing =
    isBatchGeneratingTTS || isBatchGeneratingTranslation;

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
      setIsInitialLoad(true); // 🔥 標記為初始載入
      loadContentData();
    } else if (editingContent?.id) {
      // 🔥 如果有 editingContent，直接使用它（不需要重新載入）
      setIsInitialLoad(true);
      setTitle(editingContent.title || "");
      if (editingContent.items && Array.isArray(editingContent.items)) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const convertedRows = (editingContent.items as any[]).map(
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (item: any, index: number) => ({
            id: item.id || (index + 1).toString(),
            text: item.text || "",
            definition: item.definition || "",
            translation: item.translation || "",
            audioUrl: item.audio_url || "",
            selectedLanguage: "chinese" as TranslationLanguage,
            has_student_progress: item.has_student_progress || false, // 🔥 保留學生進度狀態
          }),
        );
        setRows(convertedRows);
      }
      setIsLoading(false);
      setTimeout(() => {
        setIsInitialLoad(false);
      }, 100);
    }
  }, [content?.id, editingContent?.id]);

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
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const convertedRows = (data.items as any[]).map(
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (item: any, index: number): ContentRow => {
            // Convert legacy "english" to "chinese" (default)
            const rawLang = item.selectedLanguage || "chinese";
            const savedLang: TranslationLanguage =
              rawLang === "english" ||
              rawLang === "chinese" ||
              rawLang === "japanese" ||
              rawLang === "korean"
                ? rawLang === "english"
                  ? "chinese"
                  : rawLang
                : "chinese";

            return {
              id: item.id || (index + 1).toString(),
              text: item.text || "",
              definition: item.definition || "", // 中文翻譯
              translation: item.english_definition || "", // 英文釋義
              audioUrl: item.audio_url || "",
              selectedLanguage: savedLang,
              japanese_translation: item.japanese_translation || "",
              korean_translation: item.korean_translation || "",
              example_sentence: item.example_sentence || "",
              example_sentence_translation:
                item.example_sentence_translation || "",
              example_sentence_definition:
                item.example_sentence_definition || "",
              has_student_progress: item.has_student_progress || false, // 🔥 保留學生進度狀態
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
      // 🔥 載入完成後，等待一個 tick 再標記為非初始載入
      setTimeout(() => {
        setIsInitialLoad(false);
      }, 100);
    }
  };

  // Update parent when data changes (但不包括初始載入)
  useEffect(() => {
    if (!onUpdateContent || isInitialLoad) return; // 🔥 初始載入時不觸發

    const items = rows.map((row) => ({
      text: row.text,
      definition: row.definition, // 中文翻譯
      translation: row.translation, // 英文釋義
      audio_url: row.audioUrl,
      selectedLanguage: row.selectedLanguage, // 記錄最後選擇的語言
      example_sentence: row.example_sentence,
      example_sentence_translation: row.example_sentence_translation,
      example_sentence_definition: row.example_sentence_definition,
    }));

    onUpdateContent({
      ...editingContent,
      title,
      items,
    });
  }, [rows, title, isInitialLoad]);

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
      selectedLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
      example_sentence_definition: "",
    };
    setRows([...rows, newRow]);
  };

  const handleDeleteRow = (index: number) => {
    if (rows.length <= 1) {
      toast.error(t("contentEditor.messages.minRowsRequired"));
      return;
    }

    // 檢查此題目是否有學生進度
    if (rows[index].has_student_progress) {
      toast.error(t("contentEditor.messages.cannotDeleteWithProgress"));
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
    value: string | "chinese" | "english",
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
          selectedLanguage: row.selectedLanguage,
        }));

        await apiClient.updateContent(editingContent.id, {
          title: title || editingContent.title,
          items,
        });

        toast.success(t("contentEditor.messages.audioRemoved"));
      } catch (error: unknown) {
        console.error("Failed to remove audio:", error);
        // 解析 ApiError 的結構化錯誤訊息
        if (error instanceof ApiError) {
          const detail = error.detail;
          const errorMessage =
            typeof detail === "object" && detail?.message
              ? detail.message
              : typeof detail === "string"
                ? detail
                : null;
          toast.error(
            errorMessage || t("contentEditor.messages.removeAudioFailed"),
          );
        } else {
          toast.error(t("contentEditor.messages.removeAudioFailed"));
        }
        // 恢復原始狀態
        const originalRows = [...rows];
        setRows(originalRows);
      }
    } else {
      toast.info(t("contentEditor.messages.audioRemoved"));
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
          selectedLanguage: row.selectedLanguage, // 記錄最後選擇的語言
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
          } catch (error: unknown) {
            console.error("Failed to update content:", error);
            // 解析 ApiError 的結構化錯誤訊息
            if (error instanceof ApiError) {
              const detail = error.detail;
              const errorMessage =
                typeof detail === "object" && detail?.message
                  ? detail.message
                  : typeof detail === "string"
                    ? detail
                    : null;
              toast.error(
                errorMessage ||
                  t("contentEditor.messages.updateFailedButAudioGenerated"),
              );
            } else {
              toast.error(
                t("contentEditor.messages.updateFailedButAudioGenerated"),
              );
            }
          }
        }

        // 關閉 modal 但不要關閉 panel
        setTtsModalOpen(false);
        setSelectedRow(null);
      }
    }
  };

  const handleBatchGenerateTTS = async () => {
    // 收集需要生成 TTS 的文字
    const textsToGenerate = rows
      .filter((row) => row.text && !row.audioUrl)
      .map((row) => row.text);

    if (textsToGenerate.length === 0) {
      toast.info(t("contentEditor.messages.allItemsHaveAudio"));
      return;
    }

    setIsBatchGeneratingTTS(true);
    try {
      toast.info(
        t("contentEditor.messages.generatingAudioFiles", {
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
        // 更新 rows 的 audioUrl
        const newRows = [...rows];
        let audioIndex = 0;

        for (let i = 0; i < newRows.length; i++) {
          if (newRows[i].text && !newRows[i].audioUrl) {
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
          selectedLanguage: row.selectedLanguage, // 記錄最後選擇的語言
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
          } catch (error: unknown) {
            console.error("Failed to save TTS:", error);
            // 解析 ApiError 的結構化錯誤訊息
            if (error instanceof ApiError) {
              const detail = error.detail;
              const errorMessage =
                typeof detail === "object" && detail?.message
                  ? detail.message
                  : typeof detail === "string"
                    ? detail
                    : null;
              toast.error(
                errorMessage ||
                  t("contentEditor.messages.savingFailedButAudioGenerated"),
              );
            } else {
              toast.error(
                t("contentEditor.messages.savingFailedButAudioGenerated"),
              );
            }
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
    } finally {
      setIsBatchGeneratingTTS(false);
    }
  };

  const handleGenerateSingleDefinition = async (index: number) => {
    const newRows = [...rows];
    const currentLang = newRows[index].selectedLanguage || "chinese";
    return handleGenerateSingleDefinitionWithLang(index, currentLang);
  };

  const handleGenerateSingleDefinitionWithLang = async (
    index: number,
    targetLang: TranslationLanguage,
  ) => {
    const newRows = [...rows];
    if (!newRows[index].text) {
      toast.error(t("contentEditor.messages.enterTextFirst"));
      return;
    }

    const langConfig = TRANSLATION_LANGUAGES.find(
      (l) => l.value === targetLang,
    );
    toast.info(t("contentEditor.messages.generatingTranslation"));

    try {
      const response = (await apiClient.translateText(
        newRows[index].text,
        langConfig?.code || "zh-TW",
      )) as { translation: string };

      // 根據目標語言寫入對應欄位
      if (targetLang === "chinese") {
        newRows[index].definition = response.translation;
      } else if (targetLang === "japanese") {
        newRows[index].japanese_translation = response.translation;
      } else if (targetLang === "korean") {
        newRows[index].korean_translation = response.translation;
      }
      // 記錄最後選擇的語言
      newRows[index].selectedLanguage = targetLang;

      setRows(newRows);
      toast.success(t("contentEditor.messages.translationComplete"));
    } catch (error) {
      console.error("Translation error:", error);
      toast.error(t("contentEditor.messages.translationFailed"));
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
      toast.info(t("contentEditor.messages.noItemsNeedTranslation"));
      return;
    }

    setIsBatchGeneratingTranslation(true);
    toast.info(t("contentEditor.messages.startingBatchTranslation"));
    const newRows = [...rows];

    try {
      // 收集需要中文翻譯的項目
      const needsChinese = itemsToTranslate.filter(
        (item) => !newRows[item.index].definition,
      );
      // 收集需要英文翻譯的項目
      const needsEnglish = itemsToTranslate.filter(
        (item) => !newRows[item.index].translation,
      );

      // 批次處理中文翻譯
      if (needsChinese.length > 0) {
        const chineseTexts = needsChinese.map((item) => item.text);
        const chineseResponse = await apiClient.batchTranslate(
          chineseTexts,
          "zh-TW",
        );
        const chineseTranslations =
          (chineseResponse as { translations?: string[] }).translations || [];

        needsChinese.forEach((item, idx) => {
          newRows[item.index].definition =
            chineseTranslations[idx] || item.text;
          // 不清空英文欄位，保留兩種語言
        });
      }

      // 批次處理英文釋義
      if (needsEnglish.length > 0) {
        const englishTexts = needsEnglish.map((item) => item.text);
        const englishResponse = await apiClient.batchTranslate(
          englishTexts,
          "en",
        );
        const englishTranslations =
          (englishResponse as { translations?: string[] }).translations || [];

        needsEnglish.forEach((item, idx) => {
          newRows[item.index].translation =
            englishTranslations[idx] || item.text;
          // 不清空中文欄位，保留兩種語言
        });
      }

      // 批次翻譯時預設使用中文
      itemsToTranslate.forEach((item) => {
        if (!newRows[item.index].selectedLanguage) {
          newRows[item.index].selectedLanguage = "chinese";
        }
      });

      setRows(newRows);
      toast.success(
        t("contentEditor.messages.batchTranslationComplete", {
          count: itemsToTranslate.length,
        }),
      );
    } catch (error) {
      console.error("Batch translation error:", error);
      toast.error(t("contentEditor.messages.batchTranslationFailed"));
    } finally {
      setIsBatchGeneratingTranslation(false);
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
      selectedLanguage: "chinese",
      example_sentence: "",
      example_sentence_translation: "",
      example_sentence_definition: "",
    }));

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
        toast.error(t("contentEditor.messages.batchProcessingFailed"));
        return;
      }
    }

    // 合併新舊項目
    const updatedRows = [...nonEmptyRows, ...newItems];

    // 更新前端狀態
    setRows(updatedRows);

    const existingContentId = editingContent?.id || content?.id;

    if (existingContentId) {
      // 編輯模式：直接儲存到資料庫
      try {
        const saveData = {
          title: title,
          items: updatedRows.map((row) => ({
            text: row.text.trim(),
            definition: row.definition || "",
            english_definition: row.translation || "",
            translation: row.definition || "",
            selectedLanguage: row.selectedLanguage || "chinese",
            audio_url: row.audioUrl || row.audio_url || "",
          })),
          target_wpm: 60,
          target_accuracy: 0.8,
          time_limit_seconds: 180,
        };

        await apiClient.updateContent(existingContentId, saveData);
        toast.success(
          t("contentEditor.messages.itemsAddedAndSaved", {
            added: lines.length,
            total: updatedRows.length,
          }),
        );
      } catch (error) {
        console.error("Failed to save batch paste:", error);
        toast.error(t("contentEditor.messages.batchProcessingFailed"));
        return;
      }
    } else {
      // 新增模式：只更新本地狀態，不儲存到資料庫
      // 使用者需要按「儲存」按鈕才會真正創建內容
      if (onUpdateContent) {
        onUpdateContent({
          ...editingContent,
          title,
          items: updatedRows.map((row) => ({
            text: row.text,
            definition: row.definition,
            translation: row.translation,
            audio_url: row.audioUrl || row.audio_url || "",
            selectedLanguage: row.selectedLanguage,
          })),
        });
      }
      toast.success(
        t("contentEditor.messages.itemsAddedSaveToComplete", {
          added: lines.length,
          total: updatedRows.length,
        }),
      );
    }

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
    <div className="flex flex-col h-full">
      {/* Fixed Header Section */}
      <div className="flex-shrink-0 space-y-4 pb-4">
        {/* Assignment Copy Warning Banner */}
        {isAssignmentCopy && (
          <div className="bg-orange-50 border-l-4 border-orange-400 p-4 rounded-md">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-orange-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-orange-800">
                  <span className="font-medium">
                    {t("contentEditor.warnings.assignmentCopy")}
                  </span>
                  <br />
                  {t("contentEditor.warnings.assignmentCopyDescription")}
                </p>
              </div>
            </div>
          </div>
        )}

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
            disabled={isBatchProcessing}
            className="bg-blue-100 hover:bg-blue-200 border-blue-300 disabled:opacity-50"
            title={t("readingAssessmentPanel.batchActions.batchPasteTooltip")}
          >
            <Clipboard className="h-4 w-4 mr-1" />
            {t("readingAssessmentPanel.batchActions.batchPaste")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleBatchGenerateTTS}
            disabled={isBatchProcessing}
            className="bg-yellow-100 hover:bg-yellow-200 border-yellow-300 disabled:opacity-50"
            title={t(
              "readingAssessmentPanel.batchActions.batchGenerateTTSTooltip",
            )}
          >
            {isBatchGeneratingTTS ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Volume2 className="h-4 w-4 mr-1" />
            )}
            {isBatchGeneratingTTS
              ? t("readingAssessmentPanel.batchActions.generatingTTS")
              : t("readingAssessmentPanel.batchActions.batchGenerateTTS")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleBatchGenerateDefinitions()}
            disabled={isBatchProcessing}
            className="bg-green-100 hover:bg-green-200 border-green-300 disabled:opacity-50"
            title={t(
              "readingAssessmentPanel.batchActions.batchGenerateTranslationTooltip",
            )}
          >
            {isBatchGeneratingTranslation ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Globe className="h-4 w-4 mr-1" />
            )}
            {isBatchGeneratingTranslation
              ? t("readingAssessmentPanel.batchActions.generatingTranslation")
              : t(
                  "readingAssessmentPanel.batchActions.batchGenerateTranslation",
                )}
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
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 min-h-0">
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
              {t("contentEditor.buttons.addItem")}
            </button>
          </div>
        </SortableContext>
      </DndContext>

      {/* Footer with Save Button */}
      {onSave && (
        <div className="flex-shrink-0 pt-4 mt-4 border-t border-gray-200 sticky bottom-0 bg-white z-10">
          <div className="flex justify-end gap-3">
            <Button
              size="lg"
              disabled={isBatchProcessing}
              className="px-8 bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={async () => {
                // 過濾掉空白項目
                const validRows = rows.filter(
                  (row) => row.text && row.text.trim(),
                );

                if (validRows.length === 0) {
                  toast.error(t("contentEditor.messages.addAtLeastOneItem"));
                  return;
                }

                if (!title || title.trim() === "") {
                  toast.error(t("contentEditor.messages.enterTitle"));
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
                    selectedLanguage: row.selectedLanguage || "chinese",
                    audio_url: row.audioUrl || row.audio_url || "",
                  })),
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
                  } catch (error: unknown) {
                    console.error("Failed to update content:", error);
                    // 解析 ApiError 的結構化錯誤訊息
                    if (error instanceof ApiError) {
                      const detail = error.detail;
                      const errorMessage =
                        typeof detail === "object" && detail?.message
                          ? detail.message
                          : typeof detail === "string"
                            ? detail
                            : null;
                      toast.error(
                        errorMessage ||
                          t("contentEditor.messages.savingFailed"),
                      );
                    } else {
                      toast.error(t("contentEditor.messages.savingFailed"));
                    }
                  }
                } else if (isCreating && lessonId) {
                  // 創建模式：新增內容
                  try {
                    const newContent = await apiClient.createContent(lessonId, {
                      type: "EXAMPLE_SENTENCES",
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
                  } catch (error: unknown) {
                    console.error("Failed to create content:", error);
                    // 解析 ApiError 的結構化錯誤訊息
                    if (error instanceof ApiError) {
                      const detail = error.detail;
                      const errorMessage =
                        typeof detail === "object" && detail?.message
                          ? detail.message
                          : typeof detail === "string"
                            ? detail
                            : null;
                      toast.error(
                        errorMessage ||
                          t("contentEditor.messages.creatingContentFailed"),
                      );
                    } else {
                      toast.error(
                        t("contentEditor.messages.creatingContentFailed"),
                      );
                    }
                  }
                }
              }}
            >
              {isBatchProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {t("contentEditor.buttons.processing")}
                </>
              ) : (
                t("contentEditor.buttons.save")
              )}
            </Button>
          </div>
        </div>
      )}

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
                placeholder="put&#10;Put it away.&#10;It's time to put everything away. Right now."
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
    </div>
  );
}
