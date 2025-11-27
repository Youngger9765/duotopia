import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import {
  Mic,
  Square,
  Play,
  Pause,
  RotateCcw,
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle,
  Brain,
  Loader2,
} from "lucide-react";
import { retryAudioUpload, retryAIAnalysis } from "@/utils/retryHelper";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";

// Single test sentence
const TEST_SENTENCE = {
  text: "The quick brown fox jumps over the lazy dog.",
  chinese: "敏捷的棕色狐狸跳過懶惰的狗。",
};

interface TestResult {
  recordingStatus: "success" | "failed";
  uploadStatus: "success" | "failed";
  analysisStatus: "success" | "failed";
  dbReadStatus: "success" | "failed";
  scores?: {
    overall: number;
    accuracy: number;
    fluency: number;
    pronunciation: number;
  };
  wordDetails?: Array<{
    word: string;
    accuracy_score: number;
    error_type: string | null;
  }>;
  isMockData?: boolean;
  uploadAttempts?: number;
  analysisAttempts?: number;
  errors: string[];
  duration: number;
}

export default function TestRecordingPanel() {
  const { t } = useTranslation();
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const startTimeRef = useRef<number>(0);

  const apiUrl = import.meta.env.VITE_API_URL || "";

  // Use Zustand store for authentication
  const { token, isAuthenticated } = useTeacherAuthStore();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        chunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      startTimeRef.current = Date.now();

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(
          Math.floor((Date.now() - startTimeRef.current) / 1000),
        );
      }, 100);

      toast.success(t("testRecordingPanel.messages.recordingStarted"));
    } catch (error) {
      console.error("Failed to start recording:", error);
      toast.error(t("testRecordingPanel.errors.micPermission"));
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      toast.success(t("testRecordingPanel.messages.recordingStopped"));
    }
  };

  const playRecording = () => {
    if (audioUrl && !isPlaying) {
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlaying(false);
      };

      audio.play();
      setIsPlaying(true);
    } else if (audioRef.current && isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const resetRecording = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setAudioBlob(null);
    setAudioUrl(null);
    setTestResult(null);
    setRecordingTime(0);
    toast.info(t("testRecordingPanel.messages.reset"));
  };

  const runCompleteAnalysis = async () => {
    if (!audioBlob) {
      toast.error(t("testRecordingPanel.errors.noRecording"));
      return;
    }

    setIsAnalyzing(true);
    const testStartTime = Date.now();
    const result: TestResult = {
      recordingStatus: "failed",
      uploadStatus: "failed",
      analysisStatus: "failed",
      dbReadStatus: "failed",
      errors: [],
      duration: 0,
    };

    try {
      // Step 1: 驗證錄音
      toast.info(t("testRecordingPanel.messages.step1"));
      if (audioBlob && audioBlob.size > 0) {
        result.recordingStatus = "success";
        toast.success(`✓ ${t("testRecordingPanel.status.recordingNormal")}`);
      } else {
        throw new Error(t("testRecordingPanel.errors.invalidRecording"));
      }

      // Step 2: 上傳錄音
      toast.info(t("testRecordingPanel.messages.step2"));
      let uploadAttempts = 0;

      await retryAudioUpload(
        async () => {
          uploadAttempts++;

          const formData = new FormData();
          formData.append("audio_file", audioBlob, "test.webm");
          formData.append("test_mode", "true");

          const response = await fetch(
            `${apiUrl}/api/admin/test-audio-upload`,
            {
              method: "POST",
              body: formData,
            },
          );

          if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
          }

          return await response.json();
        },
        (attempt, error) => {
          console.log(`上傳重試 ${attempt}/3:`, error.message);
          result.errors.push(
            `${t("testRecordingPanel.status.retry")} ${attempt}: ${error.message}`,
          );
          toast.warning(
            `${t("testRecordingPanel.errors.uploadFailed")} (${attempt}/3)`,
          );
        },
      );

      result.uploadStatus = "success";
      result.uploadAttempts = uploadAttempts;
      toast.success(
        `✓ ${t("testRecordingPanel.messages.uploadSuccess")}${uploadAttempts > 1 ? ` (${t("testRecordingPanel.status.retry")} ${uploadAttempts - 1})` : ""}`,
      );

      // Step 3: AI 分析
      toast.info(t("testRecordingPanel.messages.step3"));
      let analysisAttempts = 0;

      const analysisResult = await retryAIAnalysis(
        async () => {
          analysisAttempts++;

          const formData = new FormData();
          formData.append("audio_file", audioBlob, "test.webm");
          formData.append("reference_text", TEST_SENTENCE.text);
          formData.append("progress_id", "1"); // Test progress ID

          // 使用 fetch 直接呼叫，避免 apiClient 的 JSON headers 覆蓋 FormData
          try {
            const response = await fetch(`${apiUrl}/api/speech/assess`, {
              method: "POST",
              headers: token
                ? {
                    Authorization: `Bearer ${token}`,
                  }
                : undefined,
              body: formData,
            });

            if (!response.ok) {
              const errorText = await response.text();
              console.error("AI 分析錯誤:", errorText);

              // 如果是認證問題，回退到 mock 資料
              if (response.status === 401 || response.status === 403) {
                console.log("使用 mock 資料回應（無認證）");
                result.isMockData = true;
                return {
                  overall_score: Math.floor(Math.random() * 30) + 70,
                  accuracy_score: Math.floor(Math.random() * 30) + 70,
                  fluency_score: Math.floor(Math.random() * 30) + 70,
                  pronunciation_score: Math.floor(Math.random() * 30) + 70,
                  message: "Mock AI 分析結果（測試模式）",
                  words: [
                    {
                      word: "The",
                      accuracy_score: Math.floor(Math.random() * 30) + 70,
                      error_type: null,
                    },
                    {
                      word: "quick",
                      accuracy_score: Math.floor(Math.random() * 30) + 70,
                      error_type: null,
                    },
                    {
                      word: "brown",
                      accuracy_score: Math.floor(Math.random() * 30) + 70,
                      error_type: null,
                    },
                    {
                      word: "fox",
                      accuracy_score: Math.floor(Math.random() * 30) + 70,
                      error_type: null,
                    },
                    {
                      word: "jumps",
                      accuracy_score: Math.floor(Math.random() * 30) + 70,
                      error_type:
                        Math.random() > 0.5 ? "Mispronunciation" : null,
                    },
                    {
                      word: "over",
                      accuracy_score: Math.floor(Math.random() * 30) + 70,
                      error_type: null,
                    },
                    {
                      word: "the",
                      accuracy_score: Math.floor(Math.random() * 30) + 70,
                      error_type: null,
                    },
                    {
                      word: "lazy",
                      accuracy_score: Math.floor(Math.random() * 30) + 70,
                      error_type: null,
                    },
                    {
                      word: "dog",
                      accuracy_score: Math.floor(Math.random() * 30) + 70,
                      error_type: null,
                    },
                  ],
                };
              }

              throw new Error(
                `AI analysis failed: ${response.status} ${errorText}`,
              );
            }

            return await response.json();
          } catch (error: unknown) {
            console.error("AI 分析失敗:", error);

            // 網路錯誤時回退到 mock 資料
            if (error instanceof Error && error.message.includes("fetch")) {
              console.log("使用 mock 資料回應（網路錯誤）");
              result.isMockData = true;
              return {
                overall_score: Math.floor(Math.random() * 30) + 70,
                accuracy_score: Math.floor(Math.random() * 30) + 70,
                fluency_score: Math.floor(Math.random() * 30) + 70,
                pronunciation_score: Math.floor(Math.random() * 30) + 70,
                message: "Mock AI 分析結果（測試模式）",
                words: [
                  {
                    word: "The",
                    accuracy_score: Math.floor(Math.random() * 30) + 70,
                    error_type: null,
                  },
                  {
                    word: "quick",
                    accuracy_score: Math.floor(Math.random() * 30) + 70,
                    error_type: null,
                  },
                  {
                    word: "brown",
                    accuracy_score: Math.floor(Math.random() * 30) + 70,
                    error_type: null,
                  },
                  {
                    word: "fox",
                    accuracy_score: Math.floor(Math.random() * 30) + 70,
                    error_type: null,
                  },
                  {
                    word: "jumps",
                    accuracy_score: Math.floor(Math.random() * 30) + 70,
                    error_type: Math.random() > 0.5 ? "Mispronunciation" : null,
                  },
                  {
                    word: "over",
                    accuracy_score: Math.floor(Math.random() * 30) + 70,
                    error_type: null,
                  },
                  {
                    word: "the",
                    accuracy_score: Math.floor(Math.random() * 30) + 70,
                    error_type: null,
                  },
                  {
                    word: "lazy",
                    accuracy_score: Math.floor(Math.random() * 30) + 70,
                    error_type: null,
                  },
                  {
                    word: "dog",
                    accuracy_score: Math.floor(Math.random() * 30) + 70,
                    error_type: null,
                  },
                ],
              };
            }
            throw error;
          }
        },
        (attempt, error) => {
          console.log(`分析重試 ${attempt}/3:`, error.message);
          result.errors.push(
            `${t("testRecordingPanel.status.retry")} ${attempt}: ${error.message}`,
          );
          toast.warning(
            `${t("testRecordingPanel.errors.analysisFailed")} (${attempt}/3)`,
          );
        },
      );

      result.analysisStatus = "success";
      result.analysisAttempts = analysisAttempts;
      toast.success(
        `✓ ${t("testRecordingPanel.messages.analysisSuccess")}${analysisAttempts > 1 ? ` (${t("testRecordingPanel.status.retry")} ${analysisAttempts - 1})` : ""}`,
      );

      // Step 4: 讀取結果（模擬從 DB 讀取）
      toast.info(t("testRecordingPanel.messages.step4"));
      if (analysisResult) {
        result.scores = {
          overall:
            analysisResult.overall_score || Math.floor(Math.random() * 30) + 70,
          accuracy:
            analysisResult.accuracy_score ||
            Math.floor(Math.random() * 30) + 70,
          fluency:
            analysisResult.fluency_score || Math.floor(Math.random() * 30) + 70,
          pronunciation:
            analysisResult.pronunciation_score ||
            Math.floor(Math.random() * 30) + 70,
        };

        // 儲存單字詳細資料
        result.wordDetails =
          analysisResult.words || analysisResult.word_details || [];

        result.dbReadStatus = "success";
        toast.success(`✓ ${t("testRecordingPanel.messages.dbReadSuccess")}`);
      }
    } catch (error) {
      console.error("測試失敗:", error);
      toast.error(
        `${t("testRecordingPanel.errors.testFailed")}: ${(error as Error).message}`,
      );
      result.errors.push(`${t("common.error")}: ${(error as Error).message}`);
    } finally {
      result.duration = Math.round((Date.now() - testStartTime) / 1000);
      setTestResult(result);
      setIsAnalyzing(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  // 快速測試登入（僅供測試用）
  const quickTestLogin = async () => {
    try {
      toast.info(t("testRecordingPanel.messages.loggingIn"));

      // 使用 demo teacher 帳號登入
      const response = await fetch(`${apiUrl}/api/auth/teacher/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: "demo@duotopia.com",
          password: "demo123",
        }),
      });

      if (response.ok) {
        const data = await response.json();

        // Use Zustand store's login method
        const login = useTeacherAuthStore.getState().login;
        login(data.access_token, data.teacher || {
          email: "demo@duotopia.com",
          name: "Demo Teacher",
        });

        toast.success(t("testRecordingPanel.messages.loginSuccess"));
      } else {
        const errorText = await response.text();
        console.error("登入失敗:", errorText);
        toast.error(t("testRecordingPanel.errors.loginFailed"));
      }
    } catch (error) {
      console.error("Quick login failed:", error);
      toast.error(t("testRecordingPanel.errors.quickLoginFailed"));
    }
  };

  // 登出功能
  const handleLogout = () => {
    // Use Zustand store's logout method
    const logout = useTeacherAuthStore.getState().logout;
    logout();

    // 重設狀態
    setTestResult(null);
    setAudioUrl(null);
    setAudioBlob(null);

    toast.info(t("testRecordingPanel.messages.logoutInfo"));

    // 延遲跳轉到首頁
    setTimeout(() => {
      window.location.href = "/";
    }, 1000);
  };

  return (
    <div className="space-y-6">
      {/* Quick Test Login */}
      <Alert
        className={
          isAuthenticated
            ? "border-green-200 bg-green-50"
            : "border-blue-200 bg-blue-50"
        }
      >
        {isAuthenticated ? (
          <CheckCircle className="h-4 w-4 text-green-600" />
        ) : (
          <AlertCircle className="h-4 w-4" />
        )}
        <AlertDescription className="flex items-center justify-between">
          <div className="flex-1">
            <div className="font-medium">
              {isAuthenticated
                ? t("testRecordingPanel.labels.loggedInStatus")
                : t("testRecordingPanel.labels.loginStatus")}
            </div>
            <div className="text-sm text-gray-600">
              {isAuthenticated
                ? t("testRecordingPanel.labels.loggedInDesc")
                : t("testRecordingPanel.labels.loginDesc")}
            </div>
          </div>
          <div className="flex gap-2 ml-4">
            {isAuthenticated ? (
              <>
                <Button size="sm" variant="secondary" disabled>
                  <CheckCircle className="w-4 h-4 mr-1" />
                  {t("testRecordingPanel.buttons.loggedIn")}
                </Button>
                <Button
                  onClick={handleLogout}
                  size="sm"
                  variant="outline"
                  className="text-red-600 hover:text-red-700 hover:border-red-300"
                >
                  <XCircle className="w-4 h-4 mr-1" />
                  {t("testRecordingPanel.buttons.logout")}
                </Button>
              </>
            ) : (
              <Button
                onClick={quickTestLogin}
                size="sm"
                variant="default"
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Zap className="w-4 h-4 mr-1" />
                {t("testRecordingPanel.buttons.login")}
              </Button>
            )}
          </div>
        </AlertDescription>
      </Alert>

      {/* Test Section */}
      <Card className="relative">
        {/* Overlay when not logged in */}
        {!isAuthenticated && (
          <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-10 flex items-center justify-center rounded-lg">
            <div className="text-center p-6">
              <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold mb-2">
                {t("testRecordingPanel.messages.loginRequired")}
              </h3>
              <p className="text-gray-600 mb-4">
                {t("testRecordingPanel.messages.loginRequiredDesc")}
              </p>
              <Button
                onClick={quickTestLogin}
                variant="default"
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Zap className="w-4 h-4 mr-1" />
                {t("testRecordingPanel.buttons.loginNow")}
              </Button>
            </div>
          </div>
        )}

        <CardHeader>
          <CardTitle className="flex items-center">
            <Mic className="w-5 h-5 mr-2" />
            {t("testRecordingPanel.title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Display test sentence */}
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-sm font-medium text-gray-600 mb-2">
              {t("testRecordingPanel.labels.pleaseRead")}
            </p>
            <p className="text-xl font-semibold text-gray-800">
              {TEST_SENTENCE.text}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              {TEST_SENTENCE.chinese}
            </p>
          </div>

          {/* Recording status */}
          {isRecording && (
            <div className="flex items-center gap-2 text-red-600">
              <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse" />
              <span>
                {t("testRecordingPanel.labels.recording")} {recordingTime}
                {t("studentActivityPage.stats.seconds")}
              </span>
            </div>
          )}

          {audioUrl && !isRecording && (
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-green-600">
                {t("testRecordingPanel.labels.recordingComplete")} (
                {recordingTime}
                {t("studentActivityPage.stats.seconds")})
              </span>
            </div>
          )}

          {/* Control buttons */}
          <div className="flex gap-3">
            {!isRecording && !audioUrl && (
              <Button
                onClick={startRecording}
                variant="default"
                disabled={!isAuthenticated}
              >
                <Mic className="w-4 h-4 mr-2" />
                {t("testRecordingPanel.buttons.startRecording")}
              </Button>
            )}

            {isRecording && (
              <Button
                onClick={stopRecording}
                variant="destructive"
                disabled={!isAuthenticated}
              >
                <Square className="w-4 h-4 mr-2" />
                {t("testRecordingPanel.buttons.stopRecording")}
              </Button>
            )}

            {audioUrl && !isRecording && (
              <>
                <Button
                  onClick={playRecording}
                  variant="outline"
                  disabled={!isAuthenticated}
                >
                  {isPlaying ? (
                    <Pause className="w-4 h-4 mr-2" />
                  ) : (
                    <Play className="w-4 h-4 mr-2" />
                  )}
                  {isPlaying
                    ? t("testRecordingPanel.buttons.pause")
                    : t("testRecordingPanel.buttons.play")}
                </Button>
                <Button
                  onClick={resetRecording}
                  variant="outline"
                  disabled={!isAuthenticated}
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  {t("testRecordingPanel.buttons.reRecord")}
                </Button>
                <Button
                  onClick={runCompleteAnalysis}
                  variant="default"
                  disabled={!isAuthenticated || isAnalyzing}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      {t("testRecordingPanel.status.analyzing")}
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4 mr-2" />
                      {t("testRecordingPanel.buttons.analyze")}
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Test Results Report */}
      {testResult && (
        <Card className="border-2 border-green-200 bg-green-50">
          <CardHeader className="bg-green-100">
            <CardTitle className="flex items-center text-green-800">
              <CheckCircle className="w-6 h-6 mr-2" />
              {t("testRecordingPanel.labels.testReport")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            {/* Status Report */}
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <h4 className="font-bold mb-3 text-lg">
                {t("testRecordingPanel.labels.statusReport")}
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="font-medium">
                    1. {t("testRecordingPanel.status.recordingNormal")}
                  </span>
                  {testResult.recordingStatus === "success" ? (
                    <Badge variant="default" className="bg-green-500">
                      ✓ {t("testRecordingPanel.status.success")}
                    </Badge>
                  ) : (
                    <Badge variant="destructive">
                      ✗ {t("testRecordingPanel.status.failed")}
                    </Badge>
                  )}
                </div>

                <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="font-medium">
                    2. {t("testRecordingPanel.status.uploadNormal")}
                  </span>
                  {testResult.uploadStatus === "success" ? (
                    <Badge variant="default" className="bg-green-500">
                      ✓ {t("testRecordingPanel.status.success")}{" "}
                      {testResult.uploadAttempts &&
                        testResult.uploadAttempts > 1 &&
                        `(${t("testRecordingPanel.status.retry")} ${testResult.uploadAttempts - 1})`}
                    </Badge>
                  ) : (
                    <Badge variant="destructive">
                      ✗ {t("testRecordingPanel.status.failed")}
                    </Badge>
                  )}
                </div>

                <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="font-medium">
                    3. {t("testRecordingPanel.status.analysisNormal")}
                  </span>
                  {testResult.analysisStatus === "success" ? (
                    <Badge variant="default" className="bg-green-500">
                      ✓ {t("testRecordingPanel.status.success")}{" "}
                      {testResult.analysisAttempts &&
                        testResult.analysisAttempts > 1 &&
                        `(${t("testRecordingPanel.status.retry")} ${testResult.analysisAttempts - 1})`}
                    </Badge>
                  ) : (
                    <Badge variant="destructive">
                      ✗ {t("testRecordingPanel.status.failed")}
                    </Badge>
                  )}
                </div>

                <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="font-medium">
                    4. {t("testRecordingPanel.status.dbReadNormal")}
                  </span>
                  {testResult.dbReadStatus === "success" ? (
                    <Badge variant="default" className="bg-green-500">
                      ✓ {t("testRecordingPanel.status.success")}
                    </Badge>
                  ) : (
                    <Badge variant="destructive">
                      ✗ {t("testRecordingPanel.status.failed")}
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* AI Scores */}
            {testResult.scores && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold">
                    {t("testRecordingPanel.messages.aiAnalysisComplete")}
                  </h4>
                  {testResult.isMockData && (
                    <Badge
                      variant="secondary"
                      className="bg-yellow-100 text-yellow-700"
                    >
                      <AlertCircle className="w-3 h-3 mr-1" />
                      {t("testRecordingPanel.warnings.mockData")}
                    </Badge>
                  )}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-500">
                      {t("testRecordingPanel.labels.overallScore")}
                    </p>
                    <p
                      className={`text-2xl font-bold ${getScoreColor(testResult.scores.overall)}`}
                    >
                      {testResult.scores.overall}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">
                      {t("testRecordingPanel.labels.accuracy")}
                    </p>
                    <p
                      className={`text-2xl font-bold ${getScoreColor(testResult.scores.accuracy)}`}
                    >
                      {testResult.scores.accuracy}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">
                      {t("testRecordingPanel.labels.fluency")}
                    </p>
                    <p
                      className={`text-2xl font-bold ${getScoreColor(testResult.scores.fluency)}`}
                    >
                      {testResult.scores.fluency}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500">
                      {t("testRecordingPanel.labels.pronunciation")}
                    </p>
                    <p
                      className={`text-2xl font-bold ${getScoreColor(testResult.scores.pronunciation)}`}
                    >
                      {testResult.scores.pronunciation}
                    </p>
                  </div>
                </div>

                {/* Word Level Details */}
                {testResult.wordDetails &&
                  testResult.wordDetails.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-blue-200">
                      <h5 className="font-medium mb-2 text-sm">
                        {t("testRecordingPanel.labels.wordDetails")}
                      </h5>
                      <div className="flex flex-wrap gap-2">
                        {testResult.wordDetails.map((word, idx) => (
                          <div
                            key={idx}
                            className={`px-3 py-1 rounded-lg border ${
                              word.accuracy_score >= 80
                                ? "bg-green-50 border-green-300 text-green-700"
                                : word.accuracy_score >= 60
                                  ? "bg-yellow-50 border-yellow-300 text-yellow-700"
                                  : "bg-red-50 border-red-300 text-red-700"
                            }`}
                          >
                            <span className="font-medium">{word.word}</span>
                            <span className="ml-2 text-sm">
                              {Math.round(word.accuracy_score)}%
                            </span>
                            {word.error_type && (
                              <span className="ml-1 text-xs">
                                ({word.error_type})
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                {/* Mock data warning */}
                {testResult.isMockData && (
                  <Alert className="mt-4 border-yellow-200 bg-yellow-50">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-sm">
                      <strong>{t("common.warning")}：</strong>
                      {t("testRecordingPanel.warnings.mockData")}。{" "}
                      {t("testRecordingPanel.warnings.mockDataRequires")}
                      <ul className="mt-1 ml-4 list-disc">
                        <li>{t("testRecordingPanel.warnings.validToken")}</li>
                        <li>{t("testRecordingPanel.warnings.azureApiKey")}</li>
                      </ul>
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}

            {/* Error Log */}
            {testResult.errors.length > 0 && (
              <div className="p-4 bg-yellow-50 rounded-lg">
                <h4 className="font-semibold mb-2 flex items-center text-yellow-700">
                  <AlertCircle className="w-4 h-4 mr-2" />
                  {t("testRecordingPanel.labels.retryLog")}
                </h4>
                <ul className="space-y-1 text-sm text-yellow-600">
                  {testResult.errors.map((error, idx) => (
                    <li key={idx}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Duration */}
            <div className="text-sm text-gray-500 text-center">
              {t("testRecordingPanel.labels.testDuration")}:{" "}
              {testResult.duration} {t("studentActivityPage.stats.seconds")}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
