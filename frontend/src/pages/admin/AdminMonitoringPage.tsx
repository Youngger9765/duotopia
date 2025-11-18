import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  RefreshCw,
  Activity,
  AlertCircle,
  CheckCircle,
  XCircle,
  Brain,
  Clock,
  Wifi,
  WifiOff,
  BarChart3,
  FileAudio,
  Zap,
} from "lucide-react";
import TestRecordingPanel from "@/components/admin/TestRecordingPanel";

interface AudioUploadStatus {
  total_uploads: number;
  successful: number;
  failed: number;
  in_progress: number;
  retry_count: number;
  last_updated: string;
}

interface AIAnalysisStatus {
  total_analyses: number;
  successful: number;
  failed: number;
  in_queue: number;
  avg_processing_time: number;
  last_updated: string;
}

interface RetryStatistics {
  audio_upload: {
    total_retries: number;
    successful_after_retry: number;
    failed_after_retry: number;
    retry_distribution: Record<string, number>;
  };
  ai_analysis: {
    total_retries: number;
    successful_after_retry: number;
    failed_after_retry: number;
    retry_distribution: Record<string, number>;
  };
}

interface ErrorLog {
  id: number;
  timestamp: string;
  type: "audio_upload" | "ai_analysis";
  error: string;
  retry_count: number;
  resolved: boolean;
}

export default function AdminMonitoringPage() {
  const { t } = useTranslation();
  const [audioStatus, setAudioStatus] = useState<AudioUploadStatus | null>(
    null,
  );
  const [aiStatus, setAIStatus] = useState<AIAnalysisStatus | null>(null);
  const [retryStats, setRetryStats] = useState<RetryStatistics | null>(null);
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [isOnline, setIsOnline] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const apiUrl = import.meta.env.VITE_API_URL || "";

  // Fetch all monitoring data
  const fetchMonitoringData = async () => {
    try {
      // Check backend connection
      const healthResponse = await fetch(`${apiUrl}/api/health`);
      setIsOnline(healthResponse.ok);

      // Fetch audio upload status
      const audioResponse = await fetch(
        `${apiUrl}/api/admin/audio-upload-status`,
      );
      if (audioResponse.ok) {
        const data = await audioResponse.json();
        setAudioStatus(data);
      }

      // Fetch AI analysis status
      const aiResponse = await fetch(`${apiUrl}/api/admin/ai-analysis-status`);
      if (aiResponse.ok) {
        const data = await aiResponse.json();
        setAIStatus(data);
      }

      // Fetch retry statistics
      const retryResponse = await fetch(`${apiUrl}/api/admin/retry-statistics`);
      if (retryResponse.ok) {
        const data = await retryResponse.json();
        setRetryStats(data);
      }

      // Fetch error logs
      const errorResponse = await fetch(`${apiUrl}/api/admin/error-logs`);
      if (errorResponse.ok) {
        const data = await errorResponse.json();
        setErrorLogs(data);
      }
    } catch (error) {
      console.error("Failed to fetch monitoring data:", error);
      setIsOnline(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Setup auto-refresh
  useEffect(() => {
    fetchMonitoringData();

    // Only auto-refresh if enabled
    if (autoRefreshEnabled) {
      intervalRef.current = setInterval(() => {
        fetchMonitoringData();
      }, 5000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefreshEnabled]);

  const getSuccessRate = (successful: number, total: number) => {
    if (total === 0) return 0;
    return Math.round((successful / total) * 100);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString("zh-TW");
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>{t("adminMonitoring.loading")}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold">{t("adminMonitoring.title")}</h1>
            <Badge
              variant="secondary"
              className="bg-yellow-100 text-yellow-800 border-yellow-300"
            >
              <AlertCircle className="w-3 h-3 mr-1" />
              {t("adminMonitoring.badges.mockData")}
            </Badge>
            <Badge variant="outline" className="bg-gray-50 text-gray-500">
              {t("adminMonitoring.badges.todoReal")}
            </Badge>
          </div>
          <div className="flex items-center gap-4">
            <Badge variant={isOnline ? "default" : "destructive"}>
              {isOnline ? (
                <Wifi className="w-4 h-4 mr-1" />
              ) : (
                <WifiOff className="w-4 h-4 mr-1" />
              )}
              {t("adminMonitoring.connectionStatus")}:{" "}
              {isOnline
                ? t("adminMonitoring.online")
                : t("adminMonitoring.offline")}
            </Badge>
            <Button onClick={fetchMonitoringData} size="sm" variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              {t("adminMonitoring.buttons.manualRefresh")}
            </Button>
          </div>
        </div>

        {/* Auto-refresh toggle */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            id="auto-refresh"
            checked={autoRefreshEnabled}
            onChange={(e) => setAutoRefreshEnabled(e.target.checked)}
            className="rounded"
          />
          <label htmlFor="auto-refresh" className="cursor-pointer">
            {t("adminMonitoring.autoRefresh.label")}
          </label>
          {autoRefreshEnabled && (
            <Badge variant="outline" className="text-xs">
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
              {t("adminMonitoring.autoRefresh.active")}
            </Badge>
          )}
        </div>
      </div>

      {/* Test Tools Section - Always Available */}
      <div className="grid gap-6 mb-8 p-6 bg-blue-50 border-2 border-blue-200 rounded-lg">
        <h2 className="text-xl font-semibold flex items-center text-blue-800">
          <Zap className="w-5 h-5 mr-2" />
          {t("adminMonitoring.testTools.title")}
        </h2>

        <TestRecordingPanel />
      </div>

      {/* Status Overview - TODO Style */}
      <div className="grid gap-6 mb-8 opacity-50">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            {t("adminMonitoring.statusOverview.title")}
          </h2>
          <Badge variant="outline" className="text-xs">
            {t("adminMonitoring.badges.todoConnect")}
          </Badge>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Audio Upload Status */}
          <Card className="bg-gray-50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center">
                  <FileAudio className="w-5 h-5 mr-2" />
                  {t("adminMonitoring.audioUpload.title")}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {audioStatus ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">
                        {t("adminMonitoring.audioUpload.totalUploads")}
                      </p>
                      <p className="text-2xl font-bold">
                        {audioStatus.total_uploads}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">
                        {t("adminMonitoring.audioUpload.successRate")}
                      </p>
                      <p className="text-2xl font-bold text-green-600">
                        {getSuccessRate(
                          audioStatus.successful,
                          audioStatus.total_uploads,
                        )}
                        %
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="flex items-center">
                        <CheckCircle className="w-4 h-4 mr-1 text-green-500" />
                        {t("adminMonitoring.audioUpload.successful")}:{" "}
                        {audioStatus.successful}
                      </span>
                      <span className="flex items-center">
                        <XCircle className="w-4 h-4 mr-1 text-red-500" />
                        {t("adminMonitoring.audioUpload.failed")}:{" "}
                        {audioStatus.failed}
                      </span>
                    </div>
                    <Progress
                      value={getSuccessRate(
                        audioStatus.successful,
                        audioStatus.total_uploads,
                      )}
                      className="h-2"
                    />
                  </div>

                  <div className="pt-2 border-t text-xs text-gray-500">
                    {t("adminMonitoring.lastUpdated")}:{" "}
                    {formatTimestamp(audioStatus.last_updated)}
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">{t("adminMonitoring.noData")}</p>
              )}
            </CardContent>
          </Card>

          {/* AI Analysis Status */}
          <Card className="bg-gray-50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center">
                  <Brain className="w-5 h-5 mr-2" />
                  {t("adminMonitoring.aiAnalysis.title")}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {aiStatus ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">
                        {t("adminMonitoring.aiAnalysis.totalAnalyses")}
                      </p>
                      <p className="text-2xl font-bold">
                        {aiStatus.total_analyses}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">
                        {t("adminMonitoring.aiAnalysis.successRate")}
                      </p>
                      <p className="text-2xl font-bold text-green-600">
                        {getSuccessRate(
                          aiStatus.successful,
                          aiStatus.total_analyses,
                        )}
                        %
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="flex items-center">
                        <CheckCircle className="w-4 h-4 mr-1 text-green-500" />
                        {t("adminMonitoring.aiAnalysis.successful")}:{" "}
                        {aiStatus.successful}
                      </span>
                      <span className="flex items-center">
                        <XCircle className="w-4 h-4 mr-1 text-red-500" />
                        {t("adminMonitoring.aiAnalysis.failed")}:{" "}
                        {aiStatus.failed}
                      </span>
                    </div>
                    <Progress
                      value={getSuccessRate(
                        aiStatus.successful,
                        aiStatus.total_analyses,
                      )}
                      className="h-2"
                    />
                  </div>

                  <div className="flex items-center text-sm text-gray-600">
                    <Clock className="w-4 h-4 mr-1" />
                    {t("adminMonitoring.aiAnalysis.avgProcessingTime")}:{" "}
                    {aiStatus.avg_processing_time}
                    {t("adminMonitoring.seconds")}
                  </div>

                  <div className="pt-2 border-t text-xs text-gray-500">
                    {t("adminMonitoring.lastUpdated")}:{" "}
                    {formatTimestamp(aiStatus.last_updated)}
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">{t("adminMonitoring.noData")}</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Retry Statistics - TODO Style */}
      <div className="grid gap-6 mb-8 opacity-50">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            {t("adminMonitoring.retryStats.title")}
          </h2>
          <Badge variant="outline" className="text-xs">
            {t("adminMonitoring.badges.todoConnect")}
          </Badge>
        </div>

        {retryStats && (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Audio Upload Retry Stats */}
            <Card className="bg-gray-50">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">
                  {t("adminMonitoring.retryStats.audioUpload")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>
                      {t("adminMonitoring.retryStats.totalRetries")}:{" "}
                      {retryStats.audio_upload.total_retries}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-green-600">
                      {t("adminMonitoring.retryStats.successfulAfterRetry")}:{" "}
                      {retryStats.audio_upload.successful_after_retry}
                    </span>
                    <span className="text-red-600">
                      {t("adminMonitoring.retryStats.failedAfterRetry")}:{" "}
                      {retryStats.audio_upload.failed_after_retry}
                    </span>
                  </div>

                  <div className="pt-2 border-t">
                    <p className="text-sm text-gray-500 mb-2">
                      {t("adminMonitoring.retryStats.retryDistribution")}
                    </p>
                    <div className="space-y-1">
                      {Object.entries(
                        retryStats.audio_upload.retry_distribution,
                      ).map(([attempts, count]) => (
                        <div
                          key={attempts}
                          className="flex items-center text-sm"
                        >
                          <span className="w-20">
                            {t("adminMonitoring.retryStats.attempt", {
                              number: attempts,
                            })}
                            :
                          </span>
                          <div className="flex-1 bg-gray-200 rounded-full h-4 mr-2">
                            <div
                              className="bg-blue-500 h-4 rounded-full"
                              style={{
                                width: `${(count / retryStats.audio_upload.total_retries) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="w-10 text-right">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AI Analysis Retry Stats */}
            <Card className="bg-gray-50">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">
                  {t("adminMonitoring.retryStats.aiAnalysis")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>
                      {t("adminMonitoring.retryStats.totalRetries")}:{" "}
                      {retryStats.ai_analysis.total_retries}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-green-600">
                      {t("adminMonitoring.retryStats.successfulAfterRetry")}:{" "}
                      {retryStats.ai_analysis.successful_after_retry}
                    </span>
                    <span className="text-red-600">
                      {t("adminMonitoring.retryStats.failedAfterRetry")}:{" "}
                      {retryStats.ai_analysis.failed_after_retry}
                    </span>
                  </div>

                  <div className="pt-2 border-t">
                    <p className="text-sm text-gray-500 mb-2">
                      {t("adminMonitoring.retryStats.retryDistribution")}
                    </p>
                    <div className="space-y-1">
                      {Object.entries(
                        retryStats.ai_analysis.retry_distribution,
                      ).map(([attempts, count]) => (
                        <div
                          key={attempts}
                          className="flex items-center text-sm"
                        >
                          <span className="w-20">
                            {t("adminMonitoring.retryStats.attempt", {
                              number: attempts,
                            })}
                            :
                          </span>
                          <div className="flex-1 bg-gray-200 rounded-full h-4 mr-2">
                            <div
                              className="bg-purple-500 h-4 rounded-full"
                              style={{
                                width: `${(count / retryStats.ai_analysis.total_retries) * 100}%`,
                              }}
                            />
                          </div>
                          <span className="w-10 text-right">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Error Logs - TODO Style */}
      <div className="grid gap-6 opacity-50">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            {t("adminMonitoring.errorLogs.title")}
          </h2>
          <Badge variant="outline" className="text-xs">
            {t("adminMonitoring.badges.todoConnect")}
          </Badge>
        </div>

        <Card className="bg-gray-50">
          <CardContent className="p-0">
            {errorLogs.length > 0 ? (
              <div className="divide-y">
                {errorLogs.slice(0, 10).map((log) => (
                  <div key={log.id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant={
                              log.type === "audio_upload"
                                ? "default"
                                : "secondary"
                            }
                          >
                            {log.type === "audio_upload"
                              ? t("adminMonitoring.errorLogs.audioUpload")
                              : t("adminMonitoring.errorLogs.aiAnalysis")}
                          </Badge>
                          <Badge
                            variant={log.resolved ? "outline" : "destructive"}
                          >
                            {log.resolved
                              ? t("adminMonitoring.errorLogs.resolved")
                              : t("adminMonitoring.errorLogs.unresolved")}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {t("adminMonitoring.errorLogs.retryCount", {
                              count: log.retry_count,
                            })}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700">{log.error}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatTimestamp(log.timestamp)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500">
                <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                <p>{t("adminMonitoring.errorLogs.noErrors")}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
