import { useState, useEffect } from "react";
import { Gauge, Plus, Minus, TrendingUp, TrendingDown } from "lucide-react";

interface SubscriptionStatus {
  status: string;
  days_remaining: number;
  end_date: string | null;
  plan?: string;
  quota_used?: number;
}

interface UpdateResponse {
  status: SubscriptionStatus;
  message: string;
}

interface UpdateParams {
  months?: number;
}

interface QuotaState {
  used: number;
  total: number;
  plan: "Tutor Teachers" | "School Teachers";
}

export default function TestSubscription() {
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const [quota, setQuota] = useState<QuotaState>({
    used: 0,
    total: 1800,
    plan: "Tutor Teachers",
  });

  const [customAmount, setCustomAmount] = useState<string>("100");

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const apiUrl =
        import.meta.env.VITE_API_URL ||
        window.location.origin.replace(":5173", ":8080");
      const response = await fetch(`${apiUrl}/api/test/subscription/status`);
      const data: SubscriptionStatus = await response.json();
      setStatus(data);

      // 同步更新 quota state（包含 used）
      if (data.plan) {
        setQuota((prev) => ({
          ...prev,
          plan: data.plan as "Tutor Teachers" | "School Teachers",
          total: data.plan === "School Teachers" ? 4000 : 1800,
          used: data.quota_used || 0,
        }));
      }
    } catch {
      console.error("Failed to fetch status");
    }
  };

  const updateStatus = async (action: string, params?: UpdateParams) => {
    setLoading(true);
    setMessage("");

    try {
      const apiUrl =
        import.meta.env.VITE_API_URL ||
        window.location.origin.replace(":5173", ":8080");
      const response = await fetch(`${apiUrl}/api/test/subscription/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, ...params }),
      });

      const data: UpdateResponse = await response.json();
      setStatus(data.status);
      setMessage(data.message);

      setTimeout(() => setMessage(""), 3000);
    } catch {
      setMessage("操作失敗");
    } finally {
      setLoading(false);
    }
  };

  const getStatusText = (s: string) => {
    const map: Record<string, string> = {
      subscribed: "已訂閱",
      expired: "未訂閱",
    };
    return map[s] || s;
  };

  const getStatusColor = (s: string) => {
    const map: Record<string, string> = {
      subscribed: "bg-green-100 text-green-800",
      expired: "bg-gray-100 text-gray-800",
    };
    return map[s] || "bg-gray-100";
  };

  // 配額相關函數
  const percentage = Math.min(100, (quota.used / quota.total) * 100);
  const remainingPercentage = 100 - percentage;

  const getProgressColor = () => {
    if (remainingPercentage <= 20) return "bg-red-500";
    if (remainingPercentage <= 50) return "bg-yellow-500";
    return "bg-blue-500";
  };

  const updateUsed = async (delta: number) => {
    try {
      const apiUrl =
        import.meta.env.VITE_API_URL ||
        window.location.origin.replace(":5173", ":8080");

      const response = await fetch(`${apiUrl}/api/test/subscription/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "update_quota", quota_delta: delta }),
      });

      if (response.ok) {
        const data: UpdateResponse = await response.json();
        // 更新本地狀態
        setQuota((prev) => ({
          ...prev,
          used: data.status.quota_used || 0,
        }));
        setMessage(data.message);
        setTimeout(() => setMessage(""), 3000);
      }
    } catch (error) {
      console.error("更新配額失敗:", error);
      setMessage("更新配額失敗");
    }
  };

  const resetQuota = async () => {
    try {
      const apiUrl =
        import.meta.env.VITE_API_URL ||
        window.location.origin.replace(":5173", ":8080");

      const response = await fetch(`${apiUrl}/api/test/subscription/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "update_quota", quota_delta: -quota.used }),
      });

      if (response.ok) {
        const data: UpdateResponse = await response.json();
        setQuota((prev) => ({ ...prev, used: 0 }));
        setMessage(data.message);
        setTimeout(() => setMessage(""), 3000);
      }
    } catch (error) {
      console.error("重置配額失敗:", error);
      setMessage("重置配額失敗");
    }
  };

  const togglePlan = async () => {
    const newPlan =
      quota.plan === "Tutor Teachers" ? "School Teachers" : "Tutor Teachers";

    try {
      const apiUrl =
        import.meta.env.VITE_API_URL ||
        window.location.origin.replace(":5173", ":8080");

      const response = await fetch(`${apiUrl}/api/test/subscription/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "change_plan", plan: newPlan }),
      });

      if (response.ok) {
        // 成功後更新前端狀態
        setQuota((prev) => ({
          ...prev,
          plan: newPlan,
          total: newPlan === "School Teachers" ? 4000 : 1800,
        }));
        setMessage(`已切換方案至 ${newPlan}`);
        setTimeout(() => setMessage(""), 3000);

        // 重新載入訂閱頁面資料
        window.location.reload();
      }
    } catch (error) {
      console.error("切換方案失敗:", error);
      setMessage("切換方案失敗");
    }
  };

  const quickButtons = [
    { label: "+10秒", value: 10, icon: Plus },
    { label: "+100秒", value: 100, icon: Plus },
    { label: "+500秒", value: 500, icon: TrendingUp },
    { label: "+1000秒", value: 1000, icon: TrendingUp },
    { label: "-10秒", value: -10, icon: Minus },
    { label: "-100秒", value: -100, icon: Minus },
    { label: "-500秒", value: -500, icon: TrendingDown },
    { label: "-1000秒", value: -1000, icon: TrendingDown },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            訂閱 & 配額測試控制台
          </h1>
          <p className="text-gray-600">
            測試帳號：demo@duotopia.com | 僅供開發測試使用
          </p>
        </div>

        {/* 訊息顯示 */}
        {message && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-6">
            {message}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左側：訂閱狀態管理 */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-blue-600">
                📅 訂閱狀態管理
              </h2>

              {/* 當前狀態 */}
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                  當前狀態
                </h3>
                {status ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">狀態：</span>
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status.status)}`}
                      >
                        {getStatusText(status.status)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">剩餘天數：</span>
                      <span className="font-medium">
                        {status.days_remaining} 天
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">到期日：</span>
                      <span className="font-medium text-sm">
                        {status.end_date
                          ? new Date(status.end_date).toLocaleDateString(
                              "zh-TW"
                            )
                          : "無"}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">載入中...</div>
                )}
              </div>

              {/* 快速切換 */}
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  快速切換狀態
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => updateStatus("set_subscribed")}
                    disabled={loading}
                    className="px-3 py-2 bg-green-500 text-white rounded text-sm hover:bg-green-600 disabled:opacity-50"
                  >
                    已訂閱
                  </button>
                  <button
                    onClick={() => updateStatus("set_expired")}
                    disabled={loading}
                    className="px-3 py-2 bg-gray-500 text-white rounded text-sm hover:bg-gray-600 disabled:opacity-50"
                  >
                    未訂閱
                  </button>
                </div>
              </div>

              {/* 進階操作 */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  進階操作
                </h3>
                <div className="space-y-2">
                  <button
                    onClick={() => updateStatus("reset_to_new")}
                    disabled={loading}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                  >
                    重置為新帳號（30天試用）
                  </button>
                  <button
                    onClick={() => updateStatus("expire_tomorrow")}
                    disabled={loading}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                  >
                    設定明天到期
                  </button>
                  <button
                    onClick={() => updateStatus("expire_in_week")}
                    disabled={loading}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                  >
                    設定一週後到期
                  </button>
                  <button
                    onClick={fetchStatus}
                    disabled={loading}
                    className="w-full px-3 py-2 text-sm border border-blue-300 text-blue-600 rounded hover:bg-blue-50 disabled:opacity-50"
                  >
                    🔄 重新載入
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 右側：配額管理 */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-indigo-600 flex items-center gap-2">
                <Gauge className="w-5 h-5" />
                配額管理（前端模擬）
              </h2>

              {/* Plan Selector */}
              <div className="mb-4 flex items-center justify-between bg-gray-50 rounded-lg p-3">
                <div>
                  <p className="text-xs text-gray-600 mb-1">目前方案</p>
                  <p className="font-bold text-blue-600">{quota.plan}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {quota.plan === "School Teachers"
                      ? "4000 秒/月 (66 分鐘)"
                      : "1800 秒/月 (30 分鐘)"}
                  </p>
                </div>
                <button
                  onClick={togglePlan}
                  className="px-3 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700"
                >
                  切換方案
                </button>
              </div>

              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-medium text-gray-700">
                    配額使用進度
                  </span>
                  <span className="text-xs font-bold text-gray-900">
                    {percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-3 rounded-full transition-all duration-300 ${getProgressColor()}`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-xs text-gray-600 mb-1">已使用</p>
                  <p className="text-lg font-bold text-blue-600">
                    {quota.used}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(quota.used / 60).toFixed(1)} 分
                  </p>
                </div>
                <div className="bg-green-50 rounded-lg p-3">
                  <p className="text-xs text-gray-600 mb-1">剩餘</p>
                  <p className="text-lg font-bold text-green-600">
                    {quota.total - quota.used}
                  </p>
                  <p className="text-xs text-gray-500">
                    {((quota.total - quota.used) / 60).toFixed(1)} 分
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-600 mb-1">總配額</p>
                  <p className="text-lg font-bold text-gray-700">
                    {quota.total}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(quota.total / 60).toFixed(1)} 分
                  </p>
                </div>
              </div>

              {/* Quick Action Buttons */}
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  快速調整
                </h3>
                <div className="grid grid-cols-4 gap-2">
                  {quickButtons.map((btn) => {
                    const Icon = btn.icon;
                    const isPositive = btn.value > 0;
                    return (
                      <button
                        key={btn.label}
                        onClick={() => updateUsed(btn.value)}
                        className={`px-2 py-2 rounded text-xs font-semibold transition-all hover:scale-105 active:scale-95 flex flex-col items-center justify-center gap-1 ${
                          isPositive
                            ? "bg-green-500 hover:bg-green-600 text-white"
                            : "bg-red-500 hover:bg-red-600 text-white"
                        }`}
                      >
                        <Icon className="w-3 h-3" />
                        {btn.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Custom Amount */}
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  自訂調整
                </h3>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={customAmount}
                    onChange={(e) => setCustomAmount(e.target.value)}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="輸入秒數"
                  />
                  <button
                    onClick={() => updateUsed(parseInt(customAmount) || 0)}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 flex items-center gap-1"
                  >
                    <Plus className="w-3 h-3" />+
                  </button>
                  <button
                    onClick={() => updateUsed(-(parseInt(customAmount) || 0))}
                    className="px-4 py-2 bg-orange-600 text-white text-sm rounded hover:bg-orange-700 flex items-center gap-1"
                  >
                    <Minus className="w-3 h-3" />-
                  </button>
                </div>
              </div>

              {/* Reset Button */}
              <button
                onClick={resetQuota}
                className="w-full px-4 py-2 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 font-semibold"
              >
                重置配額（歸零）
              </button>

              {/* Debug Info */}
              <div className="mt-4 bg-gray-800 text-gray-100 rounded p-3 font-mono text-xs">
                <p className="text-gray-400 mb-1">Debug:</p>
                <pre className="text-xs">{JSON.stringify(quota, null, 2)}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
