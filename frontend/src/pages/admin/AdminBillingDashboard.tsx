import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DollarSign,
  TrendingUp,
  AlertTriangle,
  RefreshCcw,
  Loader2,
  Database,
  Clock,
  BarChart3,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// Types
interface BillingSummary {
  total_cost: number;
  period: { start: string; end: string };
  top_services: Array<{ service: string; cost: number }>;
  daily_costs: Array<{ date: string; cost: number }>;
  data_available: boolean;
  message?: string;
  error?: string;
}

// interface ServiceBreakdown {
//   service: string;
//   total_cost: number;
//   period: { start: string; end: string };
//   daily_breakdown: Array<{ date: string; cost: number }>;
//   sku_breakdown: Array<{ sku: string; cost: number }>;
//   data_available: boolean;
// }

interface AnomalyCheck {
  has_anomaly: boolean;
  current_period: { cost: number; period: { start: string; end: string } };
  previous_period: { cost: number; period: { start: string; end: string } };
  increase_percent: number;
  anomalies: Array<{
    service: string;
    current_cost: number;
    previous_cost: number;
    increase_percent: number;
  }>;
  data_available: boolean;
  message?: string;
}

interface BillingHealth {
  status: string;
  bigquery_connected: boolean;
  tables_available?: boolean;
  dataset?: string;
  message?: string;
  error?: string;
}

export default function AdminBillingDashboard() {
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [health, setHealth] = useState<BillingHealth | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyCheck | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [days, setDays] = useState(30);

  useEffect(() => {
    fetchAllData();
  }, [days]);

  const fetchAllData = async () => {
    try {
      setLoading(true);

      // Fetch health status
      const healthResponse = await apiClient.get<BillingHealth>(
        "/api/admin/billing/health",
      );
      setHealth(healthResponse);

      // Fetch billing summary
      const summaryResponse = await apiClient.get<BillingSummary>(
        `/api/admin/billing/summary?days=${days}`,
      );
      setSummary(summaryResponse);

      // Fetch anomaly check
      const anomalyResponse = await apiClient.get<AnomalyCheck>(
        `/api/admin/billing/anomaly-check?threshold_percent=50&days=${Math.min(
          days,
          30,
        )}`,
      );
      setAnomalies(anomalyResponse);
    } catch (error) {
      console.error("Failed to fetch billing data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAllData();
    setRefreshing(false);
  };

  const formatCurrency = (amount: number) => {
    return `$${amount.toFixed(2)}`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const dataAvailable = summary?.data_available && health?.bigquery_connected;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">GCP 費用監控</h2>
          <p className="text-muted-foreground">
            即時追蹤 Google Cloud Platform 費用
          </p>
        </div>
        <div className="flex gap-3 items-center">
          <Select
            value={days.toString()}
            onValueChange={(value) => setDays(parseInt(value))}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">過去 7 天</SelectItem>
              <SelectItem value="30">過去 30 天</SelectItem>
              <SelectItem value="60">過去 60 天</SelectItem>
              <SelectItem value="90">過去 90 天</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCcw className="h-4 w-4" />
            )}
            <span className="ml-2">重新整理</span>
          </Button>
        </div>
      </div>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            系統狀態
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-3">
              <div
                className={`h-3 w-3 rounded-full ${
                  health?.bigquery_connected
                    ? "bg-green-500 animate-pulse"
                    : "bg-red-500"
                }`}
              />
              <div>
                <p className="text-sm font-medium">BigQuery 連線</p>
                <p className="text-xs text-muted-foreground">
                  {health?.bigquery_connected ? "已連線" : "未連線"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div
                className={`h-3 w-3 rounded-full ${
                  health?.tables_available
                    ? "bg-green-500 animate-pulse"
                    : "bg-yellow-500"
                }`}
              />
              <div>
                <p className="text-sm font-medium">資料可用性</p>
                <p className="text-xs text-muted-foreground">
                  {health?.tables_available ? "資料已匯入" : "等待匯入"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">更新頻率</p>
                <p className="text-xs text-muted-foreground">每小時更新</p>
              </div>
            </div>
          </div>

          {!dataAvailable && (
            <Alert className="mt-4">
              <AlertDescription>
                {summary?.message ||
                  health?.message ||
                  "等待 GCP 匯出資料（啟用後需 24 小時）"}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="border-l-4 border-l-blue-500 shadow-lg hover:shadow-xl transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">
              總費用
            </CardTitle>
            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
              <DollarSign className="h-5 w-5 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {formatCurrency(summary?.total_cost || 0)}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {summary?.period.start} ~ {summary?.period.end}
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500 shadow-lg hover:shadow-xl transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">
              Top 服務
            </CardTitle>
            <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center">
              <BarChart3 className="h-5 w-5 text-purple-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600 truncate">
              {summary?.top_services?.[0]?.service || "N/A"}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {formatCurrency(summary?.top_services?.[0]?.cost || 0)}
            </p>
          </CardContent>
        </Card>

        <Card
          className={`border-l-4 shadow-lg hover:shadow-xl transition-shadow ${
            anomalies?.increase_percent && anomalies.increase_percent > 50
              ? "border-l-red-500"
              : anomalies?.increase_percent && anomalies.increase_percent > 0
                ? "border-l-orange-500"
                : "border-l-green-500"
          }`}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">
              費用增長
            </CardTitle>
            <div
              className={`h-10 w-10 rounded-full flex items-center justify-center ${
                anomalies?.increase_percent && anomalies.increase_percent > 50
                  ? "bg-red-100"
                  : anomalies?.increase_percent &&
                      anomalies.increase_percent > 0
                    ? "bg-orange-100"
                    : "bg-green-100"
              }`}
            >
              <TrendingUp
                className={`h-5 w-5 ${
                  anomalies?.increase_percent && anomalies.increase_percent > 50
                    ? "text-red-600"
                    : anomalies?.increase_percent &&
                        anomalies.increase_percent > 0
                      ? "text-orange-600"
                      : "text-green-600"
                }`}
              />
            </div>
          </CardHeader>
          <CardContent>
            <div
              className={`text-3xl font-bold ${
                anomalies?.increase_percent && anomalies.increase_percent > 50
                  ? "text-red-600"
                  : anomalies?.increase_percent &&
                      anomalies.increase_percent > 0
                    ? "text-orange-600"
                    : "text-green-600"
              }`}
            >
              {anomalies?.increase_percent !== undefined
                ? `${anomalies.increase_percent > 0 ? "+" : ""}${anomalies.increase_percent.toFixed(1)}%`
                : "N/A"}
            </div>
            <p className="text-xs text-gray-500 mt-2">相較前期 {days} 天</p>
          </CardContent>
        </Card>

        <Card
          className={`border-l-4 shadow-lg hover:shadow-xl transition-shadow ${
            anomalies?.has_anomaly
              ? "border-l-red-500 bg-red-50"
              : "border-l-green-500"
          }`}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">
              異常警報
            </CardTitle>
            <div
              className={`h-10 w-10 rounded-full flex items-center justify-center ${
                anomalies?.has_anomaly ? "bg-red-100" : "bg-green-100"
              }`}
            >
              <AlertTriangle
                className={`h-5 w-5 ${
                  anomalies?.has_anomaly
                    ? "text-red-600 animate-pulse"
                    : "text-green-600"
                }`}
              />
            </div>
          </CardHeader>
          <CardContent>
            <div
              className={`text-3xl font-bold ${
                anomalies?.has_anomaly ? "text-red-600" : "text-green-600"
              }`}
            >
              {anomalies?.anomalies?.length || 0}
            </div>
            <p
              className={`text-xs mt-2 font-medium ${
                anomalies?.has_anomaly ? "text-red-700" : "text-green-700"
              }`}
            >
              {anomalies?.has_anomaly ? "⚠️ 偵測到異常" : "✓ 正常"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Anomaly Alerts */}
      {anomalies?.has_anomaly && anomalies.anomalies.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="font-semibold mb-2">
              偵測到 {anomalies.anomalies.length} 個費用異常
            </div>
            <ul className="list-disc list-inside space-y-1">
              {anomalies.anomalies.map((anomaly, idx) => (
                <li key={idx} className="text-sm">
                  <strong>{anomaly.service}</strong>: $
                  {anomaly.previous_cost.toFixed(2)} → $
                  {anomaly.current_cost.toFixed(2)} (
                  {anomaly.increase_percent > 0 ? "+" : ""}
                  {anomaly.increase_percent.toFixed(1)}%)
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {dataAvailable && (
        <>
          {/* Daily Cost Trend */}
          <Card>
            <CardHeader>
              <CardTitle>每日費用趨勢</CardTitle>
              <CardDescription>過去 {days} 天的 GCP 費用變化</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={summary?.daily_costs || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatDate}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number) => formatCurrency(value)}
                    labelFormatter={(label) => `日期: ${label}`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="cost"
                    stroke="#8884d8"
                    name="費用 (USD)"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Top Services */}
          <Card>
            <CardHeader>
              <CardTitle>服務費用排行</CardTitle>
              <CardDescription>過去 {days} 天的 Top 10 服務</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={summary?.top_services?.slice(0, 10) || []}
                  layout="vertical"
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis
                    dataKey="service"
                    type="category"
                    width={150}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Legend />
                  <Bar dataKey="cost" fill="#82ca9d" name="費用 (USD)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </>
      )}

      {!dataAvailable && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">等待資料匯入</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                BigQuery Billing Export 已啟用，資料將在 24
                小時內開始匯入。請稍後再回來查看費用資料。
              </p>
              <div className="mt-6">
                <Button onClick={handleRefresh} variant="outline">
                  <RefreshCcw className="h-4 w-4 mr-2" />
                  檢查資料狀態
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
