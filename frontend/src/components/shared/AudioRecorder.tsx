import { useState, useRef, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import AudioPlayer from "./AudioPlayer";
import { Mic, MicOff, Square, RotateCcw, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AudioErrorData } from "@/utils/audioErrorLogger";
import { toast } from "sonner";

interface AudioRecorderProps {
  // Core props
  onRecordingComplete?: (blob: Blob, url: string) => void;
  onRecordingStart?: () => void;
  onRecordingStop?: () => void;
  onError?: (error: AudioErrorData) => void; // 錯誤回調

  // Display props
  title?: string;
  description?: string;
  suggestedDuration?: number;
  readOnly?: boolean;
  disabled?: boolean;

  // Existing recording
  existingAudioUrl?: string;
  onReRecord?: () => void;

  // Status display
  status?: "idle" | "recording" | "completed" | "error";
  errorMessage?: string;

  // UI customization
  variant?: "default" | "compact" | "minimal";
  className?: string;
  showProgress?: boolean;
  showTimer?: boolean;
  autoStop?: number; // Auto stop after X seconds
}

export default function AudioRecorder({
  onRecordingComplete,
  onRecordingStart,
  onRecordingStop,
  onError,
  title,
  description,
  suggestedDuration = 60,
  readOnly = false,
  disabled = false,
  existingAudioUrl,
  onReRecord,
  status: externalStatus = "idle",
  errorMessage,
  variant = "default",
  className,
  showProgress = true,
  showTimer = true,
  autoStop,
}: AudioRecorderProps) {
  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [localAudioUrl, setLocalAudioUrl] = useState<string | null>(
    existingAudioUrl || null,
  );
  const [status, setStatus] = useState<
    "idle" | "recording" | "completed" | "error"
  >(externalStatus);

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Update status from external prop
  useEffect(() => {
    setStatus(externalStatus);
  }, [externalStatus]);

  // Update audio URL from external prop
  useEffect(() => {
    if (existingAudioUrl && existingAudioUrl !== localAudioUrl) {
      setLocalAudioUrl(existingAudioUrl);
    }
  }, [existingAudioUrl]);

  // Format time helper
  const formatTime = useCallback((seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }, []);

  // TODO: 重構錄音邏輯 - 代碼重複問題
  // 1. 抽出 useMediaRecorder hook 共用邏輯
  // 2. AudioRecorder.tsx 和 StudentActivityPage.tsx 都使用這個 hook
  // 3. 避免維護兩份相同的 MediaRecorder 邏輯
  // See: StudentActivityPage.tsx 有相同的邏輯

  // 🎯 跨瀏覽器格式偵測
  const getSupportedMimeType = useCallback(() => {
    const types = [
      "audio/webm;codecs=opus", // Chrome/Firefox 首選
      "audio/webm", // Chrome/Firefox 備用
      "audio/mp4", // Safari/iOS 必須
      "audio/ogg;codecs=opus", // Firefox 備用
    ];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        console.log(`✅ AudioRecorder using MIME type: ${type}`);
        return type;
      }
    }

    console.warn("⚠️ No supported MIME type found, using default");
    return ""; // 讓瀏覽器自動選擇
  }, []);

  // Start recording
  const startRecording = useCallback(async () => {
    if (readOnly || disabled) return;

    try {
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Create media recorder with auto-detected MIME type
      const mimeType = getSupportedMimeType();
      const options = mimeType ? { mimeType } : {};
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      console.log(
        `🎙️ AudioRecorder initialized with: ${mediaRecorder.mimeType}`,
      );

      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, {
          type: mediaRecorder.mimeType || "audio/webm",
        });
        const audioUrl = URL.createObjectURL(audioBlob);

        // 驗證錄音檔案
        console.log("🎤 Recording completed:", {
          size: audioBlob.size,
          type: audioBlob.type,
          duration: recordingTime,
        });

        // 檢查檔案大小（小於 1KB 可能有問題）
        if (audioBlob.size < 1000) {
          console.error("⚠️ Recording file too small:", audioBlob.size);

          // 顯示錯誤訊息給使用者
          toast.error("錄音失敗", {
            description: "錄音檔案異常，請重新錄音",
          });

          // 通知父元件處理錯誤
          if (onError) {
            onError({
              errorType: "recording_too_small",
              audioUrl: audioUrl,
              audioSize: audioBlob.size,
              audioDuration: recordingTime,
              contentType: audioBlob.type,
            });
          }

          setStatus("error");
          setIsRecording(false);

          // Clean up
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
          }
          return;
        }

        // 🎯 關鍵：驗證錄音是否可以播放
        try {
          const testAudio = new Audio(audioUrl);

          // 等待 metadata 載入（最多等 5 秒）
          const loadPromise = new Promise<boolean>((resolve) => {
            const timeout = setTimeout(() => {
              console.error("⏱️ Audio metadata load timeout");
              resolve(false);
            }, 5000);

            testAudio.addEventListener("loadedmetadata", () => {
              clearTimeout(timeout);
              console.log(
                "✅ Audio metadata loaded, duration:",
                testAudio.duration,
              );

              // 檢查 duration 是否有效（處理 Safari iOS Infinity 問題）
              if (
                !testAudio.duration ||
                isNaN(testAudio.duration) ||
                !isFinite(testAudio.duration) || // 排除 Infinity
                testAudio.duration === 0
              ) {
                console.error("❌ Invalid audio duration:", testAudio.duration);
                resolve(false);
              } else {
                resolve(true);
              }
            });

            testAudio.addEventListener("error", (e) => {
              clearTimeout(timeout);
              console.error("❌ Audio load error:", e);
              resolve(false);
            });

            // 強制載入
            testAudio.load();
          });

          const isValid = await loadPromise;

          if (!isValid) {
            console.error("⚠️ Recording validation failed");

            // 顯示錯誤訊息給使用者
            toast.error("錄音驗證失敗", {
              description:
                "錄音可能無法正常播放，請重新錄音。建議檢查麥克風設定或嘗試使用 Chrome 瀏覽器。",
            });

            // 通知父元件處理錯誤
            if (onError) {
              onError({
                errorType: "recording_validation_failed",
                audioUrl: audioUrl,
                audioSize: audioBlob.size,
                audioDuration: 0,
                contentType: audioBlob.type,
              });
            }

            setStatus("error");
            setIsRecording(false);

            // Clean up
            if (streamRef.current) {
              streamRef.current.getTracks().forEach((track) => track.stop());
              streamRef.current = null;
            }
            if (timerRef.current) {
              clearInterval(timerRef.current);
              timerRef.current = null;
            }
            return;
          }

          // ✅ 驗證通過，設定錄音
          console.log("✅ Recording validation passed");

          // 顯示成功訊息
          toast.success("錄音完成", {
            description: "錄音已通過驗證，可以正常播放",
          });

          setLocalAudioUrl(audioUrl);
          setStatus("completed");
          setIsRecording(false);

          // Clean up stream
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }

          // Clear timer
          if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
          }

          // Callback with recording
          if (onRecordingComplete) {
            onRecordingComplete(audioBlob, audioUrl);
          }

          if (onRecordingStop) {
            onRecordingStop();
          }
        } catch (error) {
          console.error("❌ Recording validation error:", error);

          // 顯示錯誤訊息給使用者
          toast.error("錄音處理失敗", {
            description: "無法驗證錄音，請重新錄音",
          });

          // 通知父元件處理錯誤
          if (onError) {
            onError({
              errorType: "recording_validation_error",
              audioUrl: audioUrl,
              audioSize: audioBlob.size,
              errorMessage: String(error),
              contentType: audioBlob.type,
            });
          }

          setStatus("error");
          setIsRecording(false);

          // Clean up
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
          }
        }
      };

      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      setStatus("recording");
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          const newTime = prev + 1;
          // Auto stop if configured
          if (autoStop && newTime >= autoStop) {
            stopRecording();
          }
          return newTime;
        });
      }, 1000);

      if (onRecordingStart) {
        onRecordingStart();
      }
    } catch (error) {
      console.error("Failed to start recording:", error);

      // 顯示錯誤訊息
      toast.error("無法開始錄音", {
        description: "請檢查麥克風權限，或嘗試重新整理頁面",
      });

      setStatus("error");
      setIsRecording(false);
    }
  }, [
    readOnly,
    disabled,
    onRecordingComplete,
    onRecordingStart,
    onRecordingStop,
    autoStop,
  ]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
    }
  }, [isRecording]);

  // Re-record
  const handleReRecord = useCallback(() => {
    if (readOnly || disabled) return;

    // Clear existing recording
    setLocalAudioUrl(null);
    setStatus("idle");
    setRecordingTime(0);

    if (onReRecord) {
      onReRecord();
    }

    // Start new recording
    startRecording();
  }, [readOnly, disabled, onReRecord, startRecording]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (localAudioUrl && localAudioUrl.startsWith("blob:")) {
        URL.revokeObjectURL(localAudioUrl);
      }
    };
  }, [localAudioUrl]);

  // Render based on variant
  const renderRecordingControls = () => {
    if (variant === "minimal") {
      return (
        <div className="flex items-center gap-3">
          {!isRecording && !localAudioUrl && (
            <Button
              size="sm"
              variant="outline"
              onClick={startRecording}
              disabled={readOnly || disabled}
            >
              <Mic className="w-4 h-4" />
            </Button>
          )}

          {isRecording && (
            <>
              <Button size="sm" variant="destructive" onClick={stopRecording}>
                <Square className="w-4 h-4" />
              </Button>
              {showTimer && (
                <span className="text-sm font-medium text-red-600">
                  {formatTime(recordingTime)}
                </span>
              )}
            </>
          )}

          {localAudioUrl && !isRecording && (
            <AudioPlayer
              audioUrl={localAudioUrl}
              variant="minimal"
              showTitle={false}
              onError={onError}
            />
          )}
        </div>
      );
    }

    if (variant === "compact") {
      return (
        <div className="space-y-3">
          {!isRecording && !localAudioUrl && (
            <Button
              className="w-full"
              onClick={startRecording}
              disabled={readOnly || disabled}
            >
              <Mic className="w-4 h-4 mr-2" />
              {readOnly ? "檢視模式" : "開始錄音"}
            </Button>
          )}

          {isRecording && (
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={stopRecording}
                className="flex-1"
              >
                <MicOff className="w-4 h-4 mr-2" />
                停止錄音
              </Button>
              <Badge variant="destructive" className="animate-pulse">
                {formatTime(recordingTime)}
              </Badge>
            </div>
          )}

          {localAudioUrl && !isRecording && (
            <div className="space-y-2">
              <AudioPlayer
                audioUrl={localAudioUrl}
                variant={readOnly ? "minimal" : "compact"}
                className="mb-2"
                onError={onError}
              />
              {!readOnly && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleReRecord}
                  disabled={disabled}
                  className="w-full"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  重新錄音
                </Button>
              )}
            </div>
          )}
        </div>
      );
    }

    // Default variant
    return (
      <div className="space-y-4">
        {/* Recording button or status */}
        {!isRecording && !localAudioUrl && (
          <div className="text-center space-y-3">
            <Button
              size="lg"
              onClick={startRecording}
              disabled={readOnly || disabled}
              className="px-8"
            >
              <Mic className="w-5 h-5 mr-2" />
              {readOnly ? "檢視模式" : "開始錄音"}
            </Button>
            {description && (
              <p className="text-sm text-gray-600">
                {readOnly ? "檢視模式中無法錄音" : description}
              </p>
            )}
          </div>
        )}

        {/* Recording in progress */}
        {isRecording && (
          <div className="space-y-4">
            <div className="flex flex-col items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
                <span className="text-lg font-medium">
                  {formatTime(recordingTime)}
                </span>
              </div>
              <Button size="lg" variant="outline" onClick={stopRecording}>
                <Square className="w-5 h-5 mr-2" />
                停止錄音
              </Button>
            </div>

            {/* Progress bar */}
            {showProgress && suggestedDuration > 0 && (
              <div className="w-full">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>建議錄音時長</span>
                  <span>
                    {Math.min(
                      100,
                      Math.round((recordingTime / suggestedDuration) * 100),
                    )}
                    %
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-red-500 transition-all duration-1000"
                    style={{
                      width: `${Math.min(100, (recordingTime / suggestedDuration) * 100)}%`,
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Recording completed */}
        {localAudioUrl && !isRecording && (
          <div className="space-y-4">
            <AudioPlayer
              audioUrl={localAudioUrl}
              title="已錄製音檔"
              onError={onError}
            />
            {!readOnly && (
              <div className="flex justify-center">
                <Button
                  variant="outline"
                  onClick={handleReRecord}
                  disabled={disabled}
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  重新錄音
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Error state */}
        {status === "error" && (
          <div className="flex items-center gap-2 text-red-600 justify-center">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm">
              {errorMessage || "錄音失敗，請檢查麥克風權限"}
            </span>
          </div>
        )}
      </div>
    );
  };

  return (
    <Card className={cn("p-6", className)}>
      {title && (
        <div className="mb-4">
          <h3 className="font-medium flex items-center gap-2">
            <Mic className="w-5 h-5" />
            {title}
          </h3>
        </div>
      )}
      {renderRecordingControls()}
    </Card>
  );
}
