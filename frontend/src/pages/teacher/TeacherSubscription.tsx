import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  CreditCard,
  Calendar,
  DollarSign,
  CheckCircle,
  XCircle,
  Clock,
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import TeacherLayout from '@/components/TeacherLayout';
import TeacherSubscriptionBanner from '@/components/TeacherSubscriptionBanner';

interface SubscriptionInfo {
  status: string;
  plan: string | null;
  end_date: string | null;
  days_remaining: number;
  is_active: boolean;
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

export default function TeacherSubscription() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    fetchSubscriptionData();
  }, []);

  const fetchSubscriptionData = async () => {
    try {
      setLoading(true);

      const token = localStorage.getItem('token');
      const apiUrl = import.meta.env.VITE_API_URL;

      // 獲取訂閱狀態
      const subResponse = await fetch(`${apiUrl}/subscription/status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (subResponse.ok) {
        const subData = await subResponse.json();
        console.log('Subscription data:', subData);
        setSubscription(subData);
      } else {
        console.error('Failed to fetch subscription:', subResponse.status);
      }

      // 獲取付款歷史
      const txnResponse = await fetch(`${apiUrl}/api/payment/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (txnResponse.ok) {
        const txnData = await txnResponse.json();
        console.log('Transaction data:', txnData);
        setTransactions(txnData.transactions || []);
      } else {
        console.error('Failed to fetch transactions:', txnResponse.status);
      }

    } catch (error) {
      console.error('Failed to fetch subscription data:', error);
      toast.error('載入訂閱資料失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = () => {
    navigate('/pricing');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />成功</Badge>;
      case 'FAILED':
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />失敗</Badge>;
      case 'PENDING':
        return <Badge variant="secondary"><Clock className="w-3 h-3 mr-1" />處理中</Badge>;
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
      {/* 訂閱狀態橫幅 */}
      {subscription && (
        <TeacherSubscriptionBanner
          isActive={subscription.is_active}
          endDate={subscription.end_date}
          daysRemaining={subscription.days_remaining}
          plan={subscription.plan}
        />
      )}

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
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-xl font-semibold">{subscription.plan || '未知方案'}</h3>
                    <Badge className="bg-green-500">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      有效
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">訂閱狀態良好</p>
                </div>
                <Button onClick={handleUpgrade} variant="outline">
                  升級方案
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>

              <Separator />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-blue-600 mt-1" />
                  <div>
                    <p className="text-sm text-gray-600">到期日</p>
                    <p className="font-semibold">
                      {subscription.end_date ? formatDate(subscription.end_date) : 'N/A'}
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
              </div>

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
              <h3 className="text-lg font-semibold text-gray-900 mb-2">尚未訂閱</h3>
              <p className="text-gray-600 mb-4">選擇適合您的訂閱方案，開始使用完整功能</p>
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
          <CardDescription>
            最近 10 筆交易記錄
          </CardDescription>
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
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <CreditCard className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold">{txn.subscription_type}</h4>
                      <p className="text-sm text-gray-600">
                        {formatDate(txn.created_at)}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        訂閱 {txn.months} 個月
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-semibold text-lg">
                        {txn.currency} ${txn.amount}
                      </p>
                      <p className="text-xs text-gray-500">{txn.type}</p>
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
    </TeacherLayout>
  );
}
