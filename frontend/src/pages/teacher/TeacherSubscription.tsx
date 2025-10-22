import { useState, useEffect } from "react";
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
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import TeacherLayout from "@/components/TeacherLayout";
import TapPayPayment from "@/components/payment/TapPayPayment";
import { apiClient } from "@/lib/api";

interface SubscriptionInfo {
  status: string;
  plan: string | null;
  end_date: string | null;
  days_remaining: number;
  is_active: boolean;
  auto_renew: boolean;
  cancelled_at: string | null;
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

// 方案價格對照表
const PLAN_PRICES: Record<string, number> = {
  "Tutor Teachers": 230,
  "School Teachers": 330,
};

export default function TeacherSubscription() {
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(
    null,
  );
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [showRenewalDialog, setShowRenewalDialog] = useState(false);
  const [showUpgradeDialog, setShowUpgradeDialog] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [selectedUpgradePlan, setSelectedUpgradePlan] = useState<{
    name: string;
    price: number;
  } | null>(null);

  useEffect(() => {
    fetchSubscriptionData();
  }, []);

  const fetchSubscriptionData = async () => {
    try {
      setLoading(true);

      // 獲取訂閱狀態
      try {
        const subData = await apiClient.get<SubscriptionInfo>(
          "/subscription/status",
        );
        console.log("Subscription data:", subData);
        setSubscription(subData);
      } catch (error) {
        console.error("Failed to fetch subscription:", error);
      }

      // 獲取付款歷史
      try {
        const txnData = await apiClient.get<{ transactions: Transaction[] }>(
          "/api/payment/history",
        );
        console.log("Transaction data:", txnData);
        setTransactions(txnData.transactions || []);
      } catch (error) {
        console.error("Failed to fetch transactions:", error);
      }
    } catch (error) {
      console.error("Failed to fetch subscription data:", error);
      toast.error("載入訂閱資料失敗");
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = () => {
    setShowUpgradeDialog(true);
  };

  const handleSelectUpgradePlan = (planName: string, price: number) => {
    setSelectedUpgradePlan({ name: planName, price });
  };

  const handleUpgradeSuccess = async (transactionId: string) => {
    toast.success(`升級成功！交易編號：${transactionId}`);
    setShowUpgradeDialog(false);
    setSelectedUpgradePlan(null);
    // Refresh subscription data
    await fetchSubscriptionData();
  };

  const handleUpgradeError = (error: string) => {
    // 🎉 檢查是否為免費優惠期間提醒
    if (error.includes("免費優惠期間") || error.includes("未來將會開放儲值")) {
      toast.info(error, {
        duration: 6000,
      });
      // 關閉對話框
      setShowUpgradeDialog(false);
      setSelectedUpgradePlan(null);
    } else {
      toast.error(`升級失敗：${error}`);
    }
  };

  const handleRenewal = () => {
    setShowRenewalDialog(true);
  };

  const handleRenewalSuccess = async (transactionId: string) => {
    toast.success(`續訂成功！交易編號：${transactionId}`);
    setShowRenewalDialog(false);
    // Refresh subscription data
    await fetchSubscriptionData();
  };

  const handleRenewalError = (error: string) => {
    // 🎉 檢查是否為免費優惠期間提醒
    if (error.includes("免費優惠期間") || error.includes("未來將會開放儲值")) {
      toast.info(error, {
        duration: 6000,
      });
      // 關閉對話框
      setShowRenewalDialog(false);
    } else {
      toast.error(`續訂失敗：${error}`);
    }
  };

  const handleCancelSubscription = async () => {
    try {
      await apiClient.post("/api/teachers/subscription/cancel");
      toast.success("已成功取消自動續訂");
      setShowCancelDialog(false);
      await fetchSubscriptionData();
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || "取消失敗");
    }
  };

  const handleReactivateSubscription = async () => {
    try {
      await apiClient.post("/api/teachers/subscription/reactivate");
      toast.success("已重新啟用自動續訂");
      await fetchSubscriptionData();
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || "啟用失敗");
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
            成功
          </Badge>
        );
      case "FAILED":
        return (
          <Badge variant="destructive">
            <XCircle className="w-3 h-3 mr-1" />
            失敗
          </Badge>
        );
      case "PENDING":
        return (
          <Badge variant="secondary">
            <Clock className="w-3 h-3 mr-1" />
            處理中
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
          <h1 className="text-3xl font-bold text-gray-900">訂閱管理</h1>
          <p className="text-gray-600 mt-2">管理您的訂閱方案與付款記錄</p>
        </div>

        {/* 訂閱狀態卡片 */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="w-5 h-5" />
              當前訂閱狀態
            </CardTitle>
          </CardHeader>
          <CardContent>
            {subscription && subscription.is_active ? (
              <div className="space-y-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-xl font-semibold">
                        {subscription.plan || "未知方案"}
                      </h3>
                      <Badge className="bg-green-500">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        有效
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">訂閱狀態良好</p>
                  </div>
                  <div className="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
                    <Button
                      onClick={handleRenewal}
                      className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white w-full sm:w-auto"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      續訂加值 30 天
                    </Button>
                    <Button
                      onClick={handleUpgrade}
                      variant="outline"
                      className="w-full sm:w-auto"
                    >
                      升級方案
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                    {subscription.auto_renew && (
                      <Button
                        onClick={() => setShowCancelDialog(true)}
                        variant="outline"
                        className="w-full sm:w-auto text-red-600 hover:text-red-700 hover:border-red-300"
                      >
                        <XCircle className="w-4 h-4 mr-2" />
                        取消續訂
                      </Button>
                    )}
                  </div>
                </div>

                <Separator />

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-blue-600 mt-1" />
                    <div>
                      <p className="text-sm text-gray-600">到期日</p>
                      <p className="font-semibold">
                        {subscription.end_date
                          ? formatDate(subscription.end_date)
                          : "N/A"}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Clock className="w-5 h-5 text-blue-600 mt-1" />
                    <div>
                      <p className="text-sm text-gray-600">剩餘天數</p>
                      <p className="font-semibold">
                        {subscription.days_remaining} 天
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <RefreshCw className="w-5 h-5 text-blue-600 mt-1" />
                    <div>
                      <p className="text-sm text-gray-600">自動續訂</p>
                      {subscription.auto_renew ? (
                        <p className="font-semibold text-green-600">已啟用</p>
                      ) : (
                        <div>
                          <p className="font-semibold text-orange-600">
                            已取消
                          </p>
                          <Button
                            onClick={handleReactivateSubscription}
                            size="sm"
                            variant="link"
                            className="h-auto p-0 text-blue-600"
                          >
                            重新啟用
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* 取消續訂警告提示 */}
                {!subscription.auto_renew && (
                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                    <p className="text-orange-800 text-sm">
                      ⚠️ 您已取消自動續訂，訂閱將於{" "}
                      {subscription.end_date
                        ? formatDate(subscription.end_date)
                        : "到期日"}{" "}
                      到期後失效
                    </p>
                  </div>
                )}

                {subscription.days_remaining <= 7 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-yellow-800 text-sm">
                      ⚠️ 您的訂閱即將到期，請及時續訂以繼續使用服務
                    </p>
                    <Button
                      onClick={handleUpgrade}
                      className="mt-3 bg-yellow-600 hover:bg-yellow-700"
                      size="sm"
                    >
                      立即續訂
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <XCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  尚未訂閱
                </h3>
                <p className="text-gray-600 mb-4">
                  選擇適合您的訂閱方案，開始使用完整功能
                </p>
                <Button onClick={handleUpgrade}>
                  查看訂閱方案
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 付款歷史 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              付款歷史
            </CardTitle>
            <CardDescription>最近 10 筆交易記錄</CardDescription>
          </CardHeader>
          <CardContent>
            {transactions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <DollarSign className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>目前沒有交易記錄</p>
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
                          訂閱 {txn.months} 個月
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
      </div>

      {/* 升級方案對話框 */}
      <Dialog open={showUpgradeDialog} onOpenChange={setShowUpgradeDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>升級訂閱方案</DialogTitle>
            <DialogDescription>選擇更適合您的方案</DialogDescription>
          </DialogHeader>

          {!selectedUpgradePlan ? (
            <div className="grid md:grid-cols-2 gap-4">
              {/* Tutor Teachers 方案 */}
              <Card
                className={`cursor-pointer transition-all ${subscription?.plan === "Tutor Teachers" ? "border-green-500 bg-green-50" : "hover:border-blue-500"}`}
              >
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Tutor Teachers</span>
                    {subscription?.plan === "Tutor Teachers" && (
                      <Badge className="bg-green-500">當前方案</Badge>
                    )}
                  </CardTitle>
                  <CardDescription>適合個人家教老師</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="mb-4">
                    <span className="text-3xl font-bold">TWD $230</span>
                    <span className="text-gray-600">/月</span>
                  </div>
                  <ul className="space-y-2 mb-4">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm">無限學生數</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm">作業管理</span>
                    </li>
                  </ul>
                  {/* 顯示按鈕條件：不是此方案，或是此方案但已過期 */}
                  {(subscription?.plan !== "Tutor Teachers" ||
                    !subscription?.is_active) && (
                    <Button
                      onClick={() =>
                        handleSelectUpgradePlan("Tutor Teachers", 230)
                      }
                      className="w-full"
                      variant="outline"
                    >
                      {subscription?.plan === "Tutor Teachers"
                        ? "續訂方案"
                        : "選擇此方案"}
                    </Button>
                  )}
                </CardContent>
              </Card>

              {/* School Teachers 方案 */}
              <Card
                className={`cursor-pointer transition-all ${subscription?.plan === "School Teachers" ? "border-green-500 bg-green-50" : "hover:border-blue-500"}`}
              >
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>School Teachers</span>
                    {subscription?.plan === "School Teachers" && (
                      <Badge className="bg-green-500">當前方案</Badge>
                    )}
                  </CardTitle>
                  <CardDescription>適合學校或補習班老師</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="mb-4">
                    <span className="text-3xl font-bold">TWD $330</span>
                    <span className="text-gray-600">/月</span>
                  </div>
                  <ul className="space-y-2 mb-4">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm">無限學生數</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm">作業管理</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm">多班級管理</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm">批次作業指派</span>
                    </li>
                  </ul>
                  {/* 顯示按鈕條件：不是此方案，或是此方案但已過期 */}
                  {(subscription?.plan !== "School Teachers" ||
                    !subscription?.is_active) && (
                    <Button
                      onClick={() =>
                        handleSelectUpgradePlan("School Teachers", 330)
                      }
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      {subscription?.plan === "School Teachers"
                        ? "續訂方案"
                        : "選擇此方案"}
                    </Button>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <TapPayPayment
              amount={selectedUpgradePlan.price}
              planName={selectedUpgradePlan.name}
              onPaymentSuccess={handleUpgradeSuccess}
              onPaymentError={handleUpgradeError}
              onCancel={() => setSelectedUpgradePlan(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* 續訂加值對話框 */}
      <Dialog open={showRenewalDialog} onOpenChange={setShowRenewalDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>續訂加值 - {subscription?.plan}</DialogTitle>
            <DialogDescription>延長您的訂閱期限 30 天</DialogDescription>
          </DialogHeader>

          {subscription && (
            <div className="mb-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-gray-600">當前到期日</p>
                  <p className="font-semibold">
                    {subscription.end_date
                      ? formatDate(subscription.end_date)
                      : "N/A"}
                  </p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-600">續訂後到期日</p>
                  <p className="font-semibold text-blue-600">
                    {subscription.end_date
                      ? formatDate(
                          new Date(
                            new Date(subscription.end_date).getTime() +
                              30 * 24 * 60 * 60 * 1000,
                          ).toISOString(),
                        )
                      : "N/A"}
                  </p>
                </div>
              </div>
            </div>
          )}

          <TapPayPayment
            amount={PLAN_PRICES[subscription?.plan || "Tutor Teachers"] || 230}
            planName={subscription?.plan || "Tutor Teachers"}
            onPaymentSuccess={handleRenewalSuccess}
            onPaymentError={handleRenewalError}
            onCancel={() => setShowRenewalDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* 取消續訂確認對話框 */}
      <Dialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>確認取消自動續訂？</DialogTitle>
            <DialogDescription>
              取消後您的訂閱將繼續有效至到期日，之後將不會自動續訂
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
              <h4 className="font-semibold mb-2">取消後會發生什麼？</h4>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>
                    訂閱繼續有效至{" "}
                    {subscription?.end_date
                      ? formatDate(subscription.end_date)
                      : "到期日"}
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                  <span>到期後將無法使用進階功能</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>您可以隨時重新啟用自動續訂</span>
                </li>
              </ul>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={() => setShowCancelDialog(false)}
                variant="outline"
                className="flex-1"
              >
                返回
              </Button>
              <Button
                onClick={handleCancelSubscription}
                variant="destructive"
                className="flex-1"
              >
                確認取消
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </TeacherLayout>
  );
}
