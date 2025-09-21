import { useState, useEffect } from 'react';

interface SubscriptionStatus {
  status: string;
  days_remaining: number;
  end_date: string | null;
}

interface UpdateResponse {
  status: SubscriptionStatus;
  message: string;
}

interface UpdateParams {
  months?: number;
}

export default function TestSubscription() {
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || window.location.origin.replace(':5173', ':8080');
      const response = await fetch(`${apiUrl}/api/test/subscription/status`);
      const data: SubscriptionStatus = await response.json();
      setStatus(data);
    } catch {
      console.error('Failed to fetch status');
    }
  };

  const updateStatus = async (action: string, params?: UpdateParams) => {
    setLoading(true);
    setMessage('');

    try {
      const apiUrl = import.meta.env.VITE_API_URL || window.location.origin.replace(':5173', ':8080');
      const response = await fetch(`${apiUrl}/api/test/subscription/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, ...params }),
      });

      const data: UpdateResponse = await response.json();
      setStatus(data.status);
      setMessage(data.message);

      setTimeout(() => setMessage(''), 3000);
    } catch {
      setMessage('操作失敗');
    } finally {
      setLoading(false);
    }
  };

  const getStatusText = (s: string) => {
    const map: Record<string, string> = {
      'subscribed': '已訂閱',
      'expired': '未訂閱'
    };
    return map[s] || s;
  };

  const getStatusColor = (s: string) => {
    const map: Record<string, string> = {
      'subscribed': 'bg-green-100 text-green-800',
      'expired': 'bg-gray-100 text-gray-800'
    };
    return map[s] || 'bg-gray-100';
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">訂閱狀態測試工具</h1>

      {/* 當前狀態 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">當前狀態</h2>
        {status ? (
          <div className="space-y-2">
            <div className="flex items-center gap-4">
              <span className="text-gray-600">狀態：</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status.status)}`}>
                {getStatusText(status.status)}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-gray-600">剩餘天數：</span>
              <span className="font-medium">{status.days_remaining} 天</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-gray-600">到期日：</span>
              <span className="font-medium">
                {status.end_date ? new Date(status.end_date).toLocaleDateString('zh-TW') : '無'}
              </span>
            </div>
          </div>
        ) : (
          <div>載入中...</div>
        )}
      </div>

      {/* 訊息顯示 */}
      {message && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-6">
          {message}
        </div>
      )}

      {/* 快速切換 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">快速切換狀態</h2>
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => updateStatus('set_subscribed')}
            disabled={loading}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
          >
            已訂閱（有天數）
          </button>
          <button
            onClick={() => updateStatus('set_expired')}
            disabled={loading}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
          >
            未訂閱（沒天數）
          </button>
        </div>
      </div>

      {/* 充值 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">充值訂閱</h2>
        <div className="flex gap-2">
          <button
            onClick={() => updateStatus('add_months', { months: 1 })}
            disabled={loading}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
          >
            +1月
          </button>
          <button
            onClick={() => updateStatus('add_months', { months: 3 })}
            disabled={loading}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
          >
            +3月
          </button>
          <button
            onClick={() => updateStatus('add_months', { months: 6 })}
            disabled={loading}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
          >
            +6月
          </button>
          <button
            onClick={() => updateStatus('add_months', { months: 12 })}
            disabled={loading}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
          >
            +12月
          </button>
        </div>
      </div>

      {/* 進階操作 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">進階操作</h2>
        <div className="space-y-2">
          <button
            onClick={() => updateStatus('reset_to_new')}
            disabled={loading}
            className="w-full px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
          >
            重置為新帳號（30天試用）
          </button>
          <button
            onClick={() => updateStatus('expire_tomorrow')}
            disabled={loading}
            className="w-full px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
          >
            設定明天到期
          </button>
          <button
            onClick={() => updateStatus('expire_in_week')}
            disabled={loading}
            className="w-full px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
          >
            設定一週後到期
          </button>
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="w-full px-4 py-2 border border-blue-300 text-blue-600 rounded hover:bg-blue-50 disabled:opacity-50"
          >
            🔄 重新載入
          </button>
        </div>
      </div>

      <div className="mt-6 text-sm text-gray-500 text-center">
        測試帳號：demo@duotopia.com | 此工具直接操作資料庫，無需登入
      </div>
    </div>
  );
}
