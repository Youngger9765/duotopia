import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  CreditCard,
  Calendar,
  DollarSign,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  ArrowRight,
  Gauge,
  TrendingUp,
  Users,
  FileText,
} from "lucide-react";
import { toast } from "sonner";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import TeacherLayout from "@/components/TeacherLayout";
import TapPayPayment from "@/components/payment/TapPayPayment";
import { SubscriptionCardManagement } from "@/components/payment/SubscriptionCardManagement";
import { apiClient } from "@/lib/api";

interface SubscriptionInfo {
  status: string;
  plan: string | null;
  end_date: string | null;
  days_remaining: number;
  is_active: boolean;
  auto_renew: boolean;
  cancelled_at: string | null;
  quota_used?: number;
  quota_total?: number;
  quota_remaining?: number;
}

interface SavedCardInfo {
  has_card: boolean;
  card: {
    last_four: string;
    card_type: string;
    issuer: string;
  } | null;
}

interface Transaction {
  id: number;
  type: string;
  amount: number;
  currency: string;
  status: string;
  months: number;
  created_at: string;
  subscription_type: string;
}

interface QuotaUsageAnalytics {
  summary: {
    total_used: number;
    total_quota: number;
    percentage: number;
  };
  daily_usage: Array<{ date: string; seconds: number }>;
  top_students: Array<{
    student_id: number;
    name: string;
    seconds: number;
    count: number;
  }>;
  top_assignments: Array<{
    assignment_id: number;
    title: string;
    seconds: number;
    students: number;
  }>;
  feature_breakdown: Record<string, number>;
}

export default function TeacherSubscription() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(
    null,
  );
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [analytics, setAnalytics] = useState<QuotaUsageAnalytics | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showUpgradeDialog, setShowUpgradeDialog] = useState(false);
  const [selectedUpgradePlan, setSelectedUpgradePlan] = useState<{
    name: string;
    price: number;
  } | null>(null);
  const [savedCardInfo, setSavedCardInfo] = useState<SavedCardInfo | null>(
    null,
  );

  useEffect(() => {
    fetchSubscriptionData();

    // 🔴 PRD Rule 2: 監聽信用卡刪除事件，重新載入訂閱狀態（auto_renew 會被關閉）
    const handleSubscriptionChanged = () => {
      fetchSubscriptionData();
    };

    window.addEventListener(
      "subscriptionStatusChanged",
      handleSubscriptionChanged,
    );

    return () => {
      window.removeEventListener(
        "subscriptionStatusChanged",
        handleSubscriptionChanged,
      );
    };
  }, []);

  const fetchSubscriptionData = async () => {
    try {
      setLoading(true);

      // 獲取訂閱狀態
      try {
        const subData = await apiClient.get<SubscriptionInfo>(
          "/api/subscription/status",
        );
        setSubscription(subData);
      } catch (error) {
        console.error("Failed to fetch subscription:", error);
        // If 401, user is not logged in - show appropriate message
        if (error && typeof error === "object" && "status" in error) {
          if (error.status === 401) {
            toast.error(t("teacherSubscription.messages.pleaseLogin"));
          } else if (error.status === 403) {
            toast.error(t("teacherSubscription.messages.permissionDenied"));
          } else {
            toast.error(
              t("teacherSubscription.messages.loadSubscriptionFailed"),
            );
          }
        } else {
          toast.error(t("teacherSubscription.messages.loadSubscriptionFailed"));
        }
      }

      // 🔴 獲取綁卡狀態（用於判斷是否能啟用自動續訂）
      try {
        const cardData = await apiClient.get<SavedCardInfo>(
          "/api/payment/saved-card",
        );
        setSavedCardInfo(cardData);
      } catch (error) {
        console.error("Failed to fetch card info:", error);
        setSavedCardInfo(null);
      }

      // 獲取付款歷史
      try {
        const txnData = await apiClient.get<{ transactions: Transaction[] }>(
          "/api/payment/history",
        );
        setTransactions(txnData.transactions || []);
      } catch (error) {
        console.error("Failed to fetch transactions:", error);
      }
    } catch (error) {
      console.error("Failed to fetch subscription data:", error);
      toast.error(t("teacherSubscription.messages.loadSubscriptionFailed"));
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      setAnalyticsLoading(true);
      const data = await apiClient.get<QuotaUsageAnalytics>(
        "/api/teachers/quota-usage",
      );
      setAnalytics(data);
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
      toast.error(t("teacherSubscription.messages.loadAnalyticsFailed"));
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const handleUpgrade = () => {
    setShowUpgradeDialog(true);
  };

  // 計算首月比例付款金額
  const calculateProratedAmount = (fullPrice: number): number => {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth(); // 0-11

    // 計算當月天數
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    // 計算到月底的剩餘天數（包含今天）
    const currentDay = now.getDate();
    const remainingDays = daysInMonth - currentDay + 1;

    // 按比例計算（四捨五入）
    return Math.round(fullPrice * (remainingDays / daysInMonth));
  };

  const handleSelectUpgradePlan = (planName: string, price: number) => {
    // 計算首月比例金額
    const proratedAmount = calculateProratedAmount(price);
    setSelectedUpgradePlan({ name: planName, price: proratedAmount });
  };

  const handleUpgradeSuccess = async (transactionId: string) => {
    toast.success(
      t("teacherSubscription.messages.subscriptionSuccess", { transactionId }),
    );
    setShowUpgradeDialog(false);
    setSelectedUpgradePlan(null);
    await fetchSubscriptionData();
  };

  const handleUpgradeError = (error: string) => {
    toast.error(
      t("teacherSubscription.messages.subscriptionFailed", { error }),
    );
  };

  const handleCancelSubscription = async () => {
    try {
      await apiClient.post("/api/teachers/subscription/cancel");
      toast.success(t("teacherSubscription.messages.cancelSuccess"));
      setShowCancelDialog(false);
      await fetchSubscriptionData();
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(
        err.response?.data?.detail ||
          t("teacherSubscription.messages.cancelFailed"),
      );
    }
  };

  const handleReactivateSubscription = async () => {
    try {
      await apiClient.post("/api/teachers/subscription/reactivate");
      toast.success(t("teacherSubscription.messages.reactivateSuccess"));
      await fetchSubscriptionData();
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(
        err.response?.data?.detail ||
          t("teacherSubscription.messages.reactivateFailed"),
      );
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("zh-TW", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "SUCCESS":
        return (
          <Badge className="bg-green-500">
            <CheckCircle className="w-3 h-3 mr-1" />
            {t("teacherSubscription.status.success")}
          </Badge>
        );
      case "FAILED":
        return (
          <Badge variant="destructive">
            <XCircle className="w-3 h-3 mr-1" />
            {t("teacherSubscription.status.failed")}
          </Badge>
        );
      case "PENDING":
        return (
          <Badge variant="secondary">
            <Clock className="w-3 h-3 mr-1" />
            {t("teacherSubscription.status.pending")}
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      </div>
    );
  }

  return (
    <TeacherLayout>
      <div className="container mx-auto p-6 max-w-6xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            {t("teacherSubscription.title")}
          </h1>
          <p className="text-gray-600 mt-2">
            {t("teacherSubscription.description")}
          </p>
        </div>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6 h-auto p-1 bg-gray-100">
            <TabsTrigger
              value="overview"
              className="flex items-center gap-2 py-3 text-base font-medium data-[state=active]:bg-white data-[state=active]:shadow-sm"
            >
              <CreditCard className="w-5 h-5" />
              {t("teacherSubscription.tabs.overview")}
            </TabsTrigger>
            <TabsTrigger
              value="analytics"
              className="flex items-center gap-2 py-3 text-base font-medium data-[state=active]:bg-white data-[state=active]:shadow-sm"
              onClick={() => {
                if (!analytics) fetchAnalytics();
              }}
            >
              <TrendingUp className="w-5 h-5" />
              {t("teacherSubscription.tabs.analytics")}
            </TabsTrigger>
            <TabsTrigger
              value="history"
              className="flex items-center gap-2 py-3 text-base font-medium data-[state=active]:bg-white data-[state=active]:shadow-sm"
            >
              <DollarSign className="w-5 h-5" />
              {t("teacherSubscription.tabs.paymentHistory")}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* 訂閱狀態卡片 */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCard className="w-5 h-5" />
                  {t("teacherSubscription.subscription.currentStatus")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {subscription && subscription.is_active ? (
                  <div className="space-y-4">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-xl font-semibold">
                            {subscription.plan ||
                              t("teacherSubscription.subscription.unknownPlan")}
                          </h3>
                          <Badge
                            className={
                              subscription.plan === "30-Day Trial"
                                ? "bg-blue-500"
                                : "bg-green-500"
                            }
                          >
                            <CheckCircle className="w-3 h-3 mr-1" />
                            {subscription.plan === "30-Day Trial"
                              ? t("teacherSubscription.subscription.trial")
                              : t("teacherSubscription.subscription.active")}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          {subscription.plan === "30-Day Trial"
                            ? t(
                                "teacherSubscription.subscription.trialDescription",
                              )
                            : t("teacherSubscription.subscription.statusGood")}
                        </p>
                        <p className="text-sm text-blue-600 mt-1 font-medium">
                          {subscription.plan === "School Teachers"
                            ? t("teacherSubscription.subscription.quotaSchool")
                            : subscription.plan === "30-Day Trial"
                              ? t("teacherSubscription.subscription.quotaTrial")
                              : t(
                                  "teacherSubscription.subscription.quotaTutor",
                                )}
                        </p>
                      </div>
                      {subscription.plan === "30-Day Trial" && (
                        <div className="flex-shrink-0">
                          <Button
                            onClick={handleUpgrade}
                            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                          >
                            <TrendingUp className="w-4 h-4 mr-2" />
                            {t("teacherSubscription.buttons.upgradeToPaid")}
                          </Button>
                        </div>
                      )}
                    </div>

                    <Separator />

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="flex items-start gap-3">
                        <Calendar className="w-5 h-5 text-blue-600 mt-1" />
                        <div className="flex-1">
                          <p className="text-sm text-gray-600 mb-1">
                            {t("teacherSubscription.labels.expiryDate")}
                          </p>
                          <p className="font-semibold text-sm">
                            {subscription.end_date
                              ? formatDate(subscription.end_date)
                              : "N/A"}
                          </p>
                          <div className="mt-2">
                            <div className="flex items-center gap-3">
                              <div className="flex-1 bg-gray-200 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full transition-all ${
                                    subscription.days_remaining <= 7
                                      ? "bg-red-500"
                                      : subscription.days_remaining <= 14
                                        ? "bg-yellow-500"
                                        : "bg-green-500"
                                  }`}
                                  style={{
                                    width: `${Math.min(100, (subscription.days_remaining / 30) * 100)}%`,
                                  }}
                                />
                              </div>
                              <p className="font-semibold text-sm whitespace-nowrap">
                                {t("teacherSubscription.labels.daysRemaining", {
                                  days: subscription.days_remaining,
                                })}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-start gap-3">
                        <Gauge className="w-5 h-5 text-blue-600 mt-1" />
                        <div className="flex-1">
                          <p className="text-sm text-gray-600 mb-2">
                            {t("teacherSubscription.labels.quotaUsage")}
                          </p>
                          <div className="flex items-center gap-3">
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="h-2 rounded-full transition-all bg-blue-500"
                                style={{
                                  width: `${Math.min(100, ((subscription.quota_used || 0) / (subscription.quota_total || 10000)) * 100)}%`,
                                }}
                              />
                            </div>
                            <p className="font-semibold text-sm whitespace-nowrap">
                              {Math.min(
                                100,
                                Math.round(
                                  ((subscription.quota_used || 0) /
                                    (subscription.quota_total || 10000)) *
                                    100,
                                ),
                              )}
                              %
                            </p>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            {subscription.quota_used || 0} /{" "}
                            {(subscription.quota_total || 0).toLocaleString()}{" "}
                            {t("teacherSubscription.labels.points")}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3">
                        <RefreshCw className="w-5 h-5 text-blue-600 mt-1" />
                        <div className="flex-1">
                          <p className="text-sm text-gray-600 mb-2">
                            {t("teacherSubscription.labels.autoRenew")}
                          </p>
                          {subscription.auto_renew ? (
                            <div className="flex items-center gap-3">
                              <p className="font-semibold text-green-600">
                                {t("teacherSubscription.labels.enabled")}
                              </p>
                              <Button
                                onClick={() => setShowCancelDialog(true)}
                                size="sm"
                                variant="outline"
                                className="text-red-600 hover:text-red-700 hover:border-red-300"
                              >
                                <XCircle className="w-4 h-4 mr-2" />
                                {t("teacherSubscription.buttons.cancelRenewal")}
                              </Button>
                            </div>
                          ) : (
                            <div className="flex flex-col gap-2">
                              <div className="flex items-center gap-3">
                                <p className="font-semibold text-orange-600">
                                  {t("teacherSubscription.labels.cancelled")}
                                </p>
                                <Button
                                  onClick={handleReactivateSubscription}
                                  size="sm"
                                  variant="outline"
                                  className="text-blue-600 hover:text-blue-700 hover:border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
                                  disabled={!savedCardInfo?.has_card}
                                  title={
                                    !savedCardInfo?.has_card
                                      ? t(
                                          "teacherSubscription.messages.pleaseBindCard",
                                        )
                                      : ""
                                  }
                                >
                                  <RefreshCw className="w-4 h-4 mr-2" />
                                  {t(
                                    "teacherSubscription.buttons.enableRenewal",
                                  )}
                                </Button>
                              </div>
                              {!savedCardInfo?.has_card && (
                                <p className="text-xs text-gray-500">
                                  {t(
                                    "teacherSubscription.messages.pleaseBindCardIcon",
                                  )}
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* 取消續訂警告提示 */}
                    {!subscription.auto_renew && (
                      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                        <p className="text-orange-800 text-sm">
                          {t("teacherSubscription.warnings.renewalCancelled", {
                            date: subscription.end_date
                              ? formatDate(subscription.end_date)
                              : t("teacherSubscription.labels.expiryDate"),
                          })}
                        </p>
                      </div>
                    )}

                    {subscription.days_remaining <= 7 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <p className="text-yellow-800 text-sm">
                          {t(
                            "teacherSubscription.warnings.subscriptionExpiring",
                          )}
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <XCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {t("teacherSubscription.subscription.noSubscription")}
                    </h3>
                    <p className="text-gray-600 mb-4">
                      {t("teacherSubscription.subscription.choosePlan")}
                    </p>
                    <Button onClick={handleUpgrade}>
                      {t("teacherSubscription.buttons.viewPlans")}
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 💳 信用卡管理 */}
            <div data-card-management>
              <SubscriptionCardManagement />
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            {analyticsLoading ? (
              <div className="flex items-center justify-center h-64">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
              </div>
            ) : analytics ? (
              <>
                {/* 配額使用摘要 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Gauge className="w-5 h-5" />
                      {t("teacherSubscription.analytics.quotaSummary")}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">
                          {t("teacherSubscription.analytics.totalQuota")}
                        </p>
                        <p className="text-3xl font-bold text-blue-600">
                          {analytics.summary.total_quota}
                        </p>
                        <p className="text-xs text-gray-500">
                          {t("teacherSubscription.labels.points")}
                        </p>
                      </div>
                      <div className="text-center p-4 bg-orange-50 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">
                          {t("teacherSubscription.analytics.used")}
                        </p>
                        <p className="text-3xl font-bold text-orange-600">
                          {analytics.summary.total_used}
                        </p>
                        <p className="text-xs text-gray-500">
                          {t("teacherSubscription.labels.points")}
                        </p>
                      </div>
                      <div className="text-center p-4 bg-green-50 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">
                          {t("teacherSubscription.analytics.usageRate")}
                        </p>
                        <p className="text-3xl font-bold text-green-600">
                          {analytics.summary.percentage}%
                        </p>
                        <p className="text-xs text-gray-500">
                          {t("teacherSubscription.analytics.remaining", {
                            points:
                              analytics.summary.total_quota -
                              analytics.summary.total_used,
                          })}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* 每日使用趨勢 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="w-5 h-5" />
                      {t("teacherSubscription.analytics.dailyTrend")}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={analytics.daily_usage}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <RechartsTooltip />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="seconds"
                          stroke="#3b82f6"
                          name={t("teacherSubscription.analytics.usageSeconds")}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* 學生使用排行 & 作業使用排行 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Users className="w-5 h-5" />
                        {t("teacherSubscription.analytics.topStudents")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={analytics.top_students}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <RechartsTooltip />
                          <Bar
                            dataKey="seconds"
                            fill="#10b981"
                            name={t(
                              "teacherSubscription.analytics.usageSeconds",
                            )}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="w-5 h-5" />
                        {t("teacherSubscription.analytics.topAssignments")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={analytics.top_assignments}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="title" />
                          <YAxis />
                          <RechartsTooltip />
                          <Bar
                            dataKey="seconds"
                            fill="#f59e0b"
                            name={t(
                              "teacherSubscription.analytics.usageSeconds",
                            )}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">
                  {t("teacherSubscription.analytics.noData")}
                </p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="history">
            {/* 付款歷史 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5" />
                  {t("teacherSubscription.history.title")}
                </CardTitle>
                <CardDescription>
                  {t("teacherSubscription.history.description")}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {transactions.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <DollarSign className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>{t("teacherSubscription.history.noTransactions")}</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {transactions.map((txn) => (
                      <div
                        key={txn.id}
                        className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 border dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors gap-4"
                      >
                        <div className="flex items-start gap-4">
                          <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center flex-shrink-0">
                            <CreditCard className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                          </div>
                          <div>
                            <h4 className="font-semibold dark:text-gray-100">
                              {txn.subscription_type}
                            </h4>
                            <p className="text-sm text-gray-600 dark:text-gray-300">
                              {formatDate(txn.created_at)}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {t(
                                "teacherSubscription.history.subscriptionMonths",
                                { months: txn.months },
                              )}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center justify-between sm:justify-end gap-4">
                          <div className="text-left sm:text-right">
                            <p className="font-semibold text-lg dark:text-gray-100">
                              {txn.currency} ${txn.amount}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {txn.type}
                            </p>
                          </div>
                          {getStatusBadge(txn.status)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* 取消續訂確認對話框 */}
      <Dialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {t("teacherSubscription.dialogs.cancelTitle")}
            </DialogTitle>
            <DialogDescription>
              {t("teacherSubscription.dialogs.cancelDescription")}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
              <h4 className="font-semibold mb-2">
                {t("teacherSubscription.dialogs.whatHappens")}
              </h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>
                    {t("teacherSubscription.dialogs.remainsValidUntil", {
                      date: subscription?.end_date
                        ? formatDate(subscription.end_date)
                        : t("teacherSubscription.labels.expiryDate"),
                    })}
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                  <span>{t("teacherSubscription.dialogs.loseAccess")}</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{t("teacherSubscription.dialogs.canReactivate")}</span>
                </li>
              </ul>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={() => setShowCancelDialog(false)}
                variant="outline"
                className="flex-1"
              >
                {t("teacherSubscription.buttons.goBack")}
              </Button>
              <Button
                onClick={handleCancelSubscription}
                variant="destructive"
                className="flex-1"
              >
                {t("teacherSubscription.buttons.confirmCancel")}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 訂閱方案選擇對話框 */}
      <Dialog open={showUpgradeDialog} onOpenChange={setShowUpgradeDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{t("teacherSubscription.plans.title")}</DialogTitle>
            <DialogDescription>
              {t("teacherSubscription.plans.description")}
            </DialogDescription>
          </DialogHeader>

          {!selectedUpgradePlan ? (
            <div className="grid md:grid-cols-2 gap-6 py-4">
              {/* Tutor Teachers 方案 */}
              <Card className="border-2 hover:border-blue-500 transition-colors">
                <CardHeader>
                  <CardTitle>Tutor Teachers</CardTitle>
                  <CardDescription>
                    {t("teacherSubscription.plans.tutorDescription")}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold">NT$ 330</span>
                      <span className="text-gray-600">
                        {t("teacherSubscription.plans.perMonth")}
                      </span>
                    </div>
                    <div className="mt-2 p-2 bg-blue-50 rounded text-sm">
                      <span className="text-blue-700">
                        {t("teacherSubscription.plans.firstMonth", {
                          amount: calculateProratedAmount(330),
                        })}
                      </span>
                      <span className="text-gray-500 text-xs ml-1">
                        {t("teacherSubscription.plans.prorated")}
                      </span>
                    </div>
                  </div>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>
                        {t("teacherSubscription.plans.tutorFeature1")}
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>
                        {t("teacherSubscription.plans.tutorFeature2")}
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>
                        {t("teacherSubscription.plans.tutorFeature3")}
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>
                        {t("teacherSubscription.plans.tutorFeature4")}
                      </span>
                    </li>
                  </ul>
                  <Button
                    onClick={() =>
                      handleSelectUpgradePlan("Tutor Teachers", 330)
                    }
                    className="w-full"
                  >
                    {t("teacherSubscription.buttons.selectPlan")}
                  </Button>
                </CardContent>
              </Card>

              {/* School Teachers 方案 */}
              <Card className="border-2 border-blue-500 relative">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-blue-500">
                    {t("teacherSubscription.plans.recommended")}
                  </Badge>
                </div>
                <CardHeader>
                  <CardTitle>School Teachers</CardTitle>
                  <CardDescription>
                    {t("teacherSubscription.plans.schoolDescription")}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold">NT$ 660</span>
                      <span className="text-gray-600">
                        {t("teacherSubscription.plans.perMonth")}
                      </span>
                    </div>
                    <div className="mt-2 p-2 bg-blue-50 rounded text-sm">
                      <span className="text-blue-700">
                        {t("teacherSubscription.plans.firstMonth", {
                          amount: calculateProratedAmount(660),
                        })}
                      </span>
                      <span className="text-gray-500 text-xs ml-1">
                        {t("teacherSubscription.plans.prorated")}
                      </span>
                    </div>
                  </div>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>
                        {t("teacherSubscription.plans.schoolFeature1")}
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>
                        {t("teacherSubscription.plans.schoolFeature2")}
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>
                        {t("teacherSubscription.plans.schoolFeature3")}
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>
                        {t("teacherSubscription.plans.schoolFeature4")}
                      </span>
                    </li>
                  </ul>
                  <Button
                    onClick={() =>
                      handleSelectUpgradePlan("School Teachers", 660)
                    }
                    className="w-full"
                  >
                    {t("teacherSubscription.buttons.selectPlan")}
                  </Button>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="py-4">
              <TapPayPayment
                planName={selectedUpgradePlan.name}
                amount={selectedUpgradePlan.price}
                onPaymentSuccess={handleUpgradeSuccess}
                onPaymentError={handleUpgradeError}
                onCancel={() => {
                  setSelectedUpgradePlan(null);
                }}
              />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </TeacherLayout>
  );
}
