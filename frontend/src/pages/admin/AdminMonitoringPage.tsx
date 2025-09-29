import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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
  Zap
} from 'lucide-react';
import TestRecordingPanel from '@/components/admin/TestRecordingPanel';

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
  type: 'audio_upload' | 'ai_analysis';
  error: string;
  retry_count: number;
  resolved: boolean;
}

export default function AdminMonitoringPage() {
  const [audioStatus, setAudioStatus] = useState<AudioUploadStatus | null>(null);
  const [aiStatus, setAIStatus] = useState<AIAnalysisStatus | null>(null);
  const [retryStats, setRetryStats] = useState<RetryStatistics | null>(null);
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [isOnline, setIsOnline] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false); // 預設關閉自動更新
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const apiUrl = import.meta.env.VITE_API_URL || '';

  // Fetch all monitoring data
  const fetchMonitoringData = async () => {
    try {
      // Check backend connection
      const healthResponse = await fetch(`${apiUrl}/api/health`);
      setIsOnline(healthResponse.ok);

      // Fetch audio upload status
      const audioResponse = await fetch(`${apiUrl}/api/admin/audio-upload-status`);
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
      console.error('Failed to fetch monitoring data:', error);
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
    return new Date(timestamp).toLocaleString('zh-TW');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>載入監控資料中...</p>
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
            <h1 className="text-3xl font-bold">系統監控面板</h1>
            <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-300">
              <AlertCircle className="w-3 h-3 mr-1" />
              MOCK DATA
            </Badge>
            <Badge variant="outline" className="bg-gray-50 text-gray-500">
              TODO: 待實作真實數據
            </Badge>
          </div>
          <div className="flex items-center gap-4">
            <Badge variant={isOnline ? "default" : "destructive"}>
              {isOnline ? <Wifi className="w-4 h-4 mr-1" /> : <WifiOff className="w-4 h-4 mr-1" />}
              連線狀態: {isOnline ? '正常' : '離線'}
            </Badge>
            <Button
              onClick={fetchMonitoringData}
              size="sm"
              variant="outline"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              手動重新整理
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
            啟用自動更新 (每 5 秒)
          </label>
          {autoRefreshEnabled && (
            <Badge variant="outline" className="text-xs">
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
              自動更新中
            </Badge>
          )}
        </div>
      </div>

      {/* Test Tools Section - Always Available */}
      <div className="grid gap-6 mb-8 p-6 bg-blue-50 border-2 border-blue-200 rounded-lg">
        <h2 className="text-xl font-semibold flex items-center text-blue-800">
          <Zap className="w-5 h-5 mr-2" />
          即時測試工具 - 真實錄音與評分
        </h2>

        <TestRecordingPanel />
      </div>

      {/* Status Overview - TODO Style */}
      <div className="grid gap-6 mb-8 opacity-50">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            即時狀態
          </h2>
          <Badge variant="outline" className="text-xs">
            TODO: 待連接真實數據
          </Badge>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Audio Upload Status */}
          <Card className="bg-gray-50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center">
                  <FileAudio className="w-5 h-5 mr-2" />
                  錄音上傳狀態
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {audioStatus ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">總上傳數</p>
                      <p className="text-2xl font-bold">總上傳數: {audioStatus.total_uploads}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">成功率</p>
                      <p className="text-2xl font-bold text-green-600">
                        {getSuccessRate(audioStatus.successful, audioStatus.total_uploads)}%
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="flex items-center">
                        <CheckCircle className="w-4 h-4 mr-1 text-green-500" />
                        成功: {audioStatus.successful}
                      </span>
                      <span className="flex items-center">
                        <XCircle className="w-4 h-4 mr-1 text-red-500" />
                        失敗: {audioStatus.failed}
                      </span>
                    </div>
                    <Progress
                      value={getSuccessRate(audioStatus.successful, audioStatus.total_uploads)}
                      className="h-2"
                    />
                  </div>

                  <div className="pt-2 border-t text-xs text-gray-500">
                    最後更新: {formatTimestamp(audioStatus.last_updated)}
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">無資料</p>
              )}
            </CardContent>
          </Card>

          {/* AI Analysis Status */}
          <Card className="bg-gray-50">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center">
                  <Brain className="w-5 h-5 mr-2" />
                  AI 分析狀態
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {aiStatus ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">總分析數</p>
                      <p className="text-2xl font-bold">總分析數: {aiStatus.total_analyses}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">成功率</p>
                      <p className="text-2xl font-bold text-green-600">
                        {getSuccessRate(aiStatus.successful, aiStatus.total_analyses)}%
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="flex items-center">
                        <CheckCircle className="w-4 h-4 mr-1 text-green-500" />
                        成功: {aiStatus.successful}
                      </span>
                      <span className="flex items-center">
                        <XCircle className="w-4 h-4 mr-1 text-red-500" />
                        失敗: {aiStatus.failed}
                      </span>
                    </div>
                    <Progress
                      value={getSuccessRate(aiStatus.successful, aiStatus.total_analyses)}
                      className="h-2"
                    />
                  </div>

                  <div className="flex items-center text-sm text-gray-600">
                    <Clock className="w-4 h-4 mr-1" />
                    平均處理時間: {aiStatus.avg_processing_time}秒
                  </div>

                  <div className="pt-2 border-t text-xs text-gray-500">
                    最後更新: {formatTimestamp(aiStatus.last_updated)}
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">無資料</p>
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
            重試統計
          </h2>
          <Badge variant="outline" className="text-xs">
            TODO: 待連接真實數據
          </Badge>
        </div>

        {retryStats && (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Audio Upload Retry Stats */}
            <Card className="bg-gray-50">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">錄音上傳重試統計</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>總重試次數: {retryStats.audio_upload.total_retries}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-green-600">
                      重試後成功: {retryStats.audio_upload.successful_after_retry}
                    </span>
                    <span className="text-red-600">
                      重試後失敗: {retryStats.audio_upload.failed_after_retry}
                    </span>
                  </div>

                  <div className="pt-2 border-t">
                    <p className="text-sm text-gray-500 mb-2">重試分布</p>
                    <div className="space-y-1">
                      {Object.entries(retryStats.audio_upload.retry_distribution).map(([attempts, count]) => (
                        <div key={attempts} className="flex items-center text-sm">
                          <span className="w-20">第 {attempts} 次:</span>
                          <div className="flex-1 bg-gray-200 rounded-full h-4 mr-2">
                            <div
                              className="bg-blue-500 h-4 rounded-full"
                              style={{ width: `${(count / retryStats.audio_upload.total_retries) * 100}%` }}
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
                <CardTitle className="text-base">AI 分析重試統計</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>總重試次數: {retryStats.ai_analysis.total_retries}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-green-600">
                      重試後成功: {retryStats.ai_analysis.successful_after_retry}
                    </span>
                    <span className="text-red-600">
                      重試後失敗: {retryStats.ai_analysis.failed_after_retry}
                    </span>
                  </div>

                  <div className="pt-2 border-t">
                    <p className="text-sm text-gray-500 mb-2">重試分布</p>
                    <div className="space-y-1">
                      {Object.entries(retryStats.ai_analysis.retry_distribution).map(([attempts, count]) => (
                        <div key={attempts} className="flex items-center text-sm">
                          <span className="w-20">第 {attempts} 次:</span>
                          <div className="flex-1 bg-gray-200 rounded-full h-4 mr-2">
                            <div
                              className="bg-purple-500 h-4 rounded-full"
                              style={{ width: `${(count / retryStats.ai_analysis.total_retries) * 100}%` }}
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
            錯誤日誌
          </h2>
          <Badge variant="outline" className="text-xs">
            TODO: 待連接真實數據
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
                          <Badge variant={log.type === 'audio_upload' ? 'default' : 'secondary'}>
                            {log.type === 'audio_upload' ? '錄音上傳' : 'AI 分析'}
                          </Badge>
                          <Badge variant={log.resolved ? 'outline' : 'destructive'}>
                            {log.resolved ? '已解決' : '未解決'}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            重試 {log.retry_count} 次
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
                <p>目前沒有錯誤日誌</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
