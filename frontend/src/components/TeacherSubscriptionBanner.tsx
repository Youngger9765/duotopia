import React from 'react';
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

interface TeacherSubscriptionBannerProps {
  isActive: boolean;
  endDate: string | null;
  daysRemaining: number;
  plan: string | null;
}

export default function TeacherSubscriptionBanner({
  isActive,
  endDate,
  daysRemaining,
  plan
}: TeacherSubscriptionBannerProps) {
  const navigate = useNavigate();

  // 已訂閱且有效
  if (isActive && endDate) {
    const isExpiringSoon = daysRemaining <= 7;

    return (
      <div className={`border-b px-4 py-3 ${
        isExpiringSoon
          ? 'bg-yellow-50 border-yellow-200'
          : 'bg-green-50 border-green-200'
      }`}>
        <div className="container mx-auto max-w-6xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isExpiringSoon ? (
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
              ) : (
                <CheckCircle className="w-5 h-5 text-green-600" />
              )}
              <div>
                <div className={`font-semibold ${
                  isExpiringSoon ? 'text-yellow-800' : 'text-green-800'
                }`}>
                  訂閱狀態：已訂閱
                </div>
                <div className={`text-sm ${
                  isExpiringSoon ? 'text-yellow-700' : 'text-green-700'
                }`}>
                  您的訂閱在 {daysRemaining} 天後到期
                </div>
                <div className={`text-xs mt-1 ${
                  isExpiringSoon ? 'text-yellow-600' : 'text-green-600'
                }`}>
                  到期日: {new Date(endDate).toLocaleDateString('zh-TW')}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className={`text-3xl font-bold ${
                  isExpiringSoon ? 'text-yellow-600' : 'text-green-600'
                }`}>
                  {daysRemaining}
                </div>
                <div className={`text-sm ${
                  isExpiringSoon ? 'text-yellow-700' : 'text-green-700'
                }`}>
                  剩餘天數
                </div>
              </div>

              {isExpiringSoon && (
                <Button
                  onClick={() => navigate('/pricing')}
                  className="bg-yellow-600 hover:bg-yellow-700"
                >
                  立即續訂
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 未訂閱或已過期
  return (
    <div className="bg-red-50 border-b border-red-200 px-4 py-3">
      <div className="container mx-auto max-w-6xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <XCircle className="w-5 h-5 text-red-600" />
            <div>
              <div className="font-semibold text-red-800">
                訂閱狀態：未訂閱
              </div>
              <div className="text-sm text-red-700">
                您目前沒有有效的訂閱方案
              </div>
            </div>
          </div>

          <Button
            onClick={() => navigate('/pricing')}
            className="bg-red-600 hover:bg-red-700"
          >
            查看訂閱方案
          </Button>
        </div>
      </div>
    </div>
  );
}
