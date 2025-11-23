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
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertTriangle,
  RefreshCcw,
  Loader2,
  Database,
  Clock,
  BarChart3,
  Search,
  Chrome,
  AlertCircle,
  Download,
  Edit,
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
interface AudioErrorStats {
  total_errors: number;
  period: { start: string; end: string };
  error_by_type: Array<{ error_type: string; count: number }>;
  error_by_date: Array<{ date: string; count: number }>;
  error_by_browser: Array<{ browser: string; count: number }>;
  data_available: boolean;
  message?: string;
  error?: string;
}

interface AudioError {
  timestamp: string;
  error_type: string;
  error_code?: string;
  error_message: string;
  audio_url: string;
  student_id?: number;
  assignment_id?: number;
  student_name?: string;
  classroom_id?: number;
  classroom_name?: string;
  teacher_id?: number;
  teacher_name?: string;
  browser: string;
  platform: string;
  device_model?: string;
  is_mobile: boolean;
}

interface AudioErrorList {
  total: number;
  data: AudioError[];
  has_more: boolean;
  error?: string;
}

interface AudioErrorHealth {
  status: string;
  bigquery_connected: boolean;
  table_available?: boolean;
  table_id?: string;
  message?: string;
  error?: string;
}

export default function AdminAudioErrorDashboard() {
  const [stats, setStats] = useState<AudioErrorStats | null>(null);
  const [health, setHealth] = useState<AudioErrorHealth | null>(null);
  const [errorList, setErrorList] = useState<AudioErrorList | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [days, setDays] = useState(7);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(20);
  const [showCustomDays, setShowCustomDays] = useState(false);
  const [customDaysInput, setCustomDaysInput] = useState("");

  useEffect(() => {
    fetchAllData();
  }, [days, currentPage]);

  useEffect(() => {
    // Reset to page 0 when search term changes
    if (currentPage !== 0) {
      setCurrentPage(0);
    } else {
      fetchErrorList();
    }
  }, [searchTerm]);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      await Promise.all([fetchHealth(), fetchStats(), fetchErrorList()]);
    } finally {
      setLoading(false);
    }
  };

  const fetchHealth = async () => {
    try {
      const healthResponse = await apiClient.get<AudioErrorHealth>(
        "/api/admin/audio-errors/health",
      );
      setHealth(healthResponse);
    } catch (error) {
      console.error("Failed to fetch health:", error);
    }
  };

  const fetchStats = async () => {
    try {
      const statsResponse = await apiClient.get<AudioErrorStats>(
        `/api/admin/audio-errors/stats?days=${days}`,
      );
      setStats(statsResponse);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const fetchErrorList = async () => {
    try {
      const offset = currentPage * pageSize;
      const listResponse = await apiClient.get<AudioErrorList>(
        `/api/admin/audio-errors/list?days=${days}&limit=${pageSize}&offset=${offset}${
          searchTerm ? `&search=${encodeURIComponent(searchTerm)}` : ""
        }`,
      );
      setErrorList(listResponse);
    } catch (error) {
      console.error("Failed to fetch error list:", error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAllData();
    setRefreshing(false);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("zh-TW", {
      month: "short",
      day: "numeric",
    });
  };

  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString("zh-TW");
  };

  const handleCustomDays = () => {
    const customDays = parseInt(customDaysInput);
    if (customDays && customDays > 0 && customDays <= 365) {
      setDays(customDays);
      setShowCustomDays(false);
      setCustomDaysInput("");
    } else {
      alert("請輸入 1-365 之間的天數");
    }
  };

  const downloadCSV = async () => {
    if (!errorList || !errorList.data || errorList.data.length === 0) {
      alert("沒有資料可以下載");
      return;
    }

    // CSV 標題
    const headers = [
      "時間",
      "錯誤類型",
      "學生姓名",
      "學生ID",
      "班級名稱",
      "班級ID",
      "老師姓名",
      "老師ID",
      "作業ID",
      "瀏覽器/平台",
      "錯誤訊息",
      "音檔URL",
    ];

    // CSV 資料行
    const rows = errorList.data.map((error) => {
      // 組合瀏覽器/平台資訊
      let browserPlatform = error.browser || "";
      if (error.platform) {
        browserPlatform += ` (${error.platform})`;
      }
      if (error.is_mobile) {
        browserPlatform += " 📱";
      }

      return [
        formatDateTime(error.timestamp),
        error.error_type || "",
        error.student_name || "N/A",
        error.student_id?.toString() || "N/A",
        error.classroom_name || "N/A",
        error.classroom_id?.toString() || "N/A",
        error.teacher_name || "N/A",
        error.teacher_id?.toString() || "N/A",
        error.assignment_id?.toString() || "N/A",
        browserPlatform,
        `"${(error.error_message || "").replace(/"/g, '""')}"`, // 處理引號
        error.audio_url || "",
      ];
    });

    // 組合 CSV 內容
    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.join(",")),
    ].join("\n");

    // 加上 BOM 讓 Excel 正確識別 UTF-8
    const BOM = "\uFEFF";
    const blob = new Blob([BOM + csvContent], {
      type: "text/csv;charset=utf-8;",
    });

    // 下載
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `audio_errors_${new Date().toISOString().split("T")[0]}.csv`,
    );
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Render Loading State
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">錄音錯誤監控</h2>
          <p className="text-muted-foreground text-sm">
            監控學生錄音播放錯誤，快速定位問題
          </p>
        </div>

        {/* System Health - Compact */}
        {health && (
          <div className="flex items-center gap-3 text-sm bg-gray-50 dark:bg-gray-800 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700">
            <Database className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            <span className="font-medium">系統狀態</span>
            <span className="text-gray-600 dark:text-gray-400">
              BigQuery: {health.bigquery_connected ? "✅" : "❌"}
            </span>
            {health.table_available !== undefined && (
              <span className="text-gray-600 dark:text-gray-400">
                資料表: {health.table_available ? "✅" : "⚠️"}
              </span>
            )}
            <span className="text-blue-600 dark:text-blue-400 text-xs">
              📊 學生資料：生產環境 Supabase
            </span>
          </div>
        )}
      </div>

      {/* Controls - Days Selection & Refresh */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
          <Button
            onClick={() => setDays(7)}
            variant={days === 7 ? "default" : "ghost"}
            size="sm"
            className={
              days === 7
                ? "bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-500 dark:hover:bg-blue-600"
                : "dark:text-gray-200 dark:hover:bg-gray-700"
            }
          >
            最近 7 天
          </Button>
          <Button
            onClick={() => setDays(14)}
            variant={days === 14 ? "default" : "ghost"}
            size="sm"
            className={
              days === 14
                ? "bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-500 dark:hover:bg-blue-600"
                : "dark:text-gray-200 dark:hover:bg-gray-700"
            }
          >
            最近 14 天
          </Button>
          <Button
            onClick={() => setDays(30)}
            variant={days === 30 ? "default" : "ghost"}
            size="sm"
            className={
              days === 30
                ? "bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-500 dark:hover:bg-blue-600"
                : "dark:text-gray-200 dark:hover:bg-gray-700"
            }
          >
            最近 30 天
          </Button>
          <Button
            onClick={() => setDays(90)}
            variant={days === 90 ? "default" : "ghost"}
            size="sm"
            className={
              days === 90
                ? "bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-500 dark:hover:bg-blue-600"
                : "dark:text-gray-200 dark:hover:bg-gray-700"
            }
          >
            最近三個月
          </Button>
          {!showCustomDays ? (
            <div className="flex items-center gap-1">
              <Button
                onClick={() => setShowCustomDays(true)}
                variant={![7, 14, 30, 90].includes(days) ? "default" : "ghost"}
                size="sm"
                className={
                  ![7, 14, 30, 90].includes(days)
                    ? "bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-500 dark:hover:bg-blue-600"
                    : "dark:text-gray-200 dark:hover:bg-gray-700"
                }
              >
                {![7, 14, 30, 90].includes(days)
                  ? `最近 ${days} 天`
                  : "自訂天數"}
              </Button>
              {![7, 14, 30, 90].includes(days) && (
                <Button
                  onClick={() => setShowCustomDays(true)}
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 dark:text-gray-200 dark:hover:bg-gray-700"
                  title="修改天數"
                >
                  <Edit className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <Input
                type="number"
                placeholder="天數"
                value={customDaysInput}
                onChange={(e) => setCustomDaysInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCustomDays();
                  if (e.key === "Escape") {
                    setShowCustomDays(false);
                    setCustomDaysInput("");
                  }
                }}
                className="w-20 h-8 text-sm dark:bg-gray-700 dark:text-white"
                autoFocus
                min="1"
                max="365"
              />
              <Button
                onClick={handleCustomDays}
                size="sm"
                variant="ghost"
                className="h-8 px-2 dark:text-gray-200"
              >
                ✓
              </Button>
              <Button
                onClick={() => {
                  setShowCustomDays(false);
                  setCustomDaysInput("");
                }}
                size="sm"
                variant="ghost"
                className="h-8 px-2 dark:text-gray-200"
              >
                ✕
              </Button>
            </div>
          )}
        </div>
        <Button
          onClick={handleRefresh}
          disabled={refreshing}
          variant="outline"
          size="sm"
        >
          <RefreshCcw
            className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`}
          />
          刷新
        </Button>
      </div>

      {/* Stats Cards - Compact */}
      {stats && stats.data_available && (
        <div className="grid gap-3 md:grid-cols-3">
          <Card className="border-l-4 border-l-red-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3">
              <CardTitle className="text-xs font-medium text-gray-600 dark:text-gray-400">
                總錯誤數
              </CardTitle>
              <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
            </CardHeader>
            <CardContent className="pb-3">
              <div className="text-xl font-bold">{stats.total_errors}</div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatDate(stats.period.start)} -{" "}
                {formatDate(stats.period.end)}
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-orange-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3">
              <CardTitle className="text-xs font-medium text-gray-600 dark:text-gray-400">
                最常見錯誤
              </CardTitle>
              <AlertCircle className="h-3.5 w-3.5 text-orange-500" />
            </CardHeader>
            <CardContent className="pb-3">
              <div className="text-xl font-bold truncate">
                {stats.error_by_type[0]?.error_type || "N/A"}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {stats.error_by_type[0]?.count || 0} 次錯誤
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3">
              <CardTitle className="text-xs font-medium text-gray-600 dark:text-gray-400">
                主要瀏覽器
              </CardTitle>
              <Chrome className="h-3.5 w-3.5 text-blue-500" />
            </CardHeader>
            <CardContent className="pb-3">
              <div className="text-xl font-bold">
                {stats.error_by_browser[0]?.browser || "N/A"}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {stats.error_by_browser[0]?.count || 0} 次錯誤
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Charts */}
      {stats && stats.data_available && (
        <div className="grid gap-4 md:grid-cols-2">
          {/* Error Trend Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                錯誤趨勢
              </CardTitle>
              <CardDescription>每日錯誤數量變化</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats.error_by_date}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatDate}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(label) => formatDate(label as string)}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="count"
                    name="錯誤數"
                    stroke="#ef4444"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Error Type Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                錯誤類型分布
              </CardTitle>
              <CardDescription>按錯誤類型統計</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={stats.error_by_type.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="error_type"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                  />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" name="錯誤數" fill="#f59e0b" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Error List Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>錯誤詳細列表</CardTitle>
              <CardDescription>
                顯示所有錄音錯誤的詳細資訊（學生、作業、錯誤類型）
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="搜尋錯誤訊息或音檔..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 w-[300px]"
                />
              </div>
              <Button
                onClick={downloadCSV}
                variant="outline"
                disabled={
                  !errorList || !errorList.data || errorList.data.length === 0
                }
              >
                <Download className="h-4 w-4 mr-2" />
                下載 CSV
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {errorList && errorList.data && errorList.data.length > 0 ? (
            <>
              <div className="rounded-md border overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead className="h-9 py-2 text-xs whitespace-nowrap">
                        時間
                      </TableHead>
                      <TableHead className="h-9 py-2 text-xs whitespace-nowrap">
                        錯誤類型
                      </TableHead>
                      <TableHead className="h-9 py-2 text-xs whitespace-nowrap">
                        學生姓名
                      </TableHead>
                      <TableHead className="h-9 py-2 text-xs text-center whitespace-nowrap">
                        學生ID
                      </TableHead>
                      <TableHead className="h-9 py-2 text-xs whitespace-nowrap">
                        班級名稱
                      </TableHead>
                      <TableHead className="h-9 py-2 text-xs text-center whitespace-nowrap">
                        班級ID
                      </TableHead>
                      <TableHead className="h-9 py-2 text-xs whitespace-nowrap">
                        老師姓名
                      </TableHead>
                      <TableHead className="h-9 py-2 text-xs text-center whitespace-nowrap">
                        老師ID
                      </TableHead>
                      <TableHead className="h-9 py-2 text-xs text-center whitespace-nowrap">
                        作業ID
                      </TableHead>
                      <TableHead className="h-9 py-2 text-xs whitespace-nowrap">
                        瀏覽器/平台
                      </TableHead>
                      <TableHead className="h-9 py-2 text-xs">
                        錯誤訊息
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {errorList.data.map((error, index) => (
                      <TableRow key={index} className="h-10">
                        <TableCell className="py-1.5 text-xs text-gray-600 dark:text-gray-400 whitespace-nowrap">
                          {formatDateTime(error.timestamp)}
                        </TableCell>
                        <TableCell className="py-1.5 whitespace-nowrap">
                          <span className="inline-flex items-center rounded-full bg-red-100 dark:bg-red-900/30 px-2 py-0.5 text-xs font-medium text-red-700 dark:text-red-400">
                            {error.error_type}
                          </span>
                        </TableCell>
                        <TableCell className="py-1.5 text-xs whitespace-nowrap">
                          {error.student_name || (
                            <span className="text-gray-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="py-1.5 text-xs text-center font-mono">
                          {error.student_id || (
                            <span className="text-gray-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="py-1.5 text-xs whitespace-nowrap">
                          {error.classroom_name || (
                            <span className="text-gray-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="py-1.5 text-xs text-center font-mono">
                          {error.classroom_id || (
                            <span className="text-gray-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="py-1.5 text-xs whitespace-nowrap">
                          {error.teacher_name || (
                            <span className="text-gray-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="py-1.5 text-xs text-center font-mono">
                          {error.teacher_id || (
                            <span className="text-gray-400">—</span>
                          )}
                        </TableCell>
                        <TableCell className="py-1.5 text-xs text-center font-mono">
                          {error.assignment_id || "—"}
                        </TableCell>
                        <TableCell className="py-1.5 text-xs whitespace-nowrap">
                          {error.browser}
                          {error.platform && (
                            <span className="text-gray-500">
                              {" "}
                              ({error.platform})
                            </span>
                          )}
                          {error.is_mobile && <span className="ml-1">📱</span>}
                        </TableCell>
                        <TableCell
                          className="py-1.5 max-w-[200px] truncate text-xs"
                          title={error.error_message}
                        >
                          {error.error_message}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-muted-foreground">
                  顯示 {currentPage * pageSize + 1} -{" "}
                  {Math.min((currentPage + 1) * pageSize, errorList.total || 0)}{" "}
                  筆， 共 {errorList.total || 0} 筆
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                    disabled={currentPage === 0}
                  >
                    上一頁
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage((p) => p + 1)}
                    disabled={!errorList.has_more}
                  >
                    下一頁
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <AlertCircle className="mx-auto h-12 w-12 mb-4 opacity-20" />
              <p className="text-lg font-medium">沒有找到錯誤記錄</p>
              <p className="text-sm">
                {searchTerm
                  ? "請嘗試其他搜尋關鍵字"
                  : stats?.message || "選擇的時間範圍內沒有錄音錯誤"}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* No Data Message */}
      {stats && !stats.data_available && (
        <Alert>
          <Clock className="h-4 w-4" />
          <AlertDescription>
            {stats.message || "等待錯誤日誌資料..."}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
