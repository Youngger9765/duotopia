import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CreditCard, Shield, Info } from 'lucide-react';
import { toast } from 'sonner';
import SubscriptionProgressBanner from '../SubscriptionProgressBanner';

interface TapPayPaymentProps {
  amount: number;
  planName: string;
  onPaymentSuccess: (transactionId: string) => void;
  onPaymentError: (error: string) => void;
  onCancel?: () => void;
}

const TapPayPayment: React.FC<TapPayPaymentProps> = ({
  amount,
  planName,
  onPaymentSuccess,
  onPaymentError,
  onCancel
}) => {
  const [canSubmit, setCanSubmit] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [cardErrors, setCardErrors] = useState({
    number: '',
    expiry: '',
    ccv: ''
  });

  useEffect(() => {
    initializeTapPay();
  }, []);

  const initializeTapPay = () => {
    // TapPay App credentials from environment variables
    const APP_ID = parseInt(import.meta.env.VITE_TAPPAY_APP_ID || '164155');
    const APP_KEY = import.meta.env.VITE_TAPPAY_APP_KEY;
    const SERVER_TYPE = import.meta.env.VITE_TAPPAY_SERVER_TYPE || 'sandbox';

    if (!window.TPDirect) {
      console.error('TapPay SDK not loaded');
      toast.error('付款系統載入失敗，請重新整理頁面');
      return;
    }

    // 延遲初始化，確保 DOM 已渲染
    setTimeout(() => {
      // 檢查元素是否存在
      const cardNumberEl = document.querySelector('#card-number');
      const expiryEl = document.querySelector('#card-expiration-date');
      const ccvEl = document.querySelector('#card-ccv');

      if (!cardNumberEl || !expiryEl || !ccvEl) {
        console.error('Payment form elements not found');
        return;
      }

      // Initialize SDK
      window.TPDirect.setupSDK(
        APP_ID,
        APP_KEY,
        SERVER_TYPE as 'sandbox' | 'production'
      );

      // Setup card fields
      const fields = {
        number: {
          element: '#card-number',
          placeholder: '**** **** **** ****'
        },
        expirationDate: {
          element: '#card-expiration-date',
          placeholder: 'MM / YY'
        },
        ccv: {
          element: '#card-ccv',
          placeholder: 'CVV'
        }
      };

      window.TPDirect.card.setup({
        fields: fields
      });

      // Listen for card field updates
      window.TPDirect.card.onUpdate((update) => {
        setCanSubmit(update.canGetPrime);

        // Update error messages
        const errors = {
          number: '',
          expiry: '',
          ccv: ''
        };

        if (update.status.number === 1) {
          errors.number = '卡號格式不正確';
        }
        if (update.status.expiry === 1) {
          errors.expiry = '有效期限格式不正確';
        }
        if (update.status.ccv === 1) {
          errors.ccv = '安全碼格式不正確';
        }

        setCardErrors(errors);
      });

      setIsInitialized(true);
    }, 100);
  };

  const handleSubmit = async () => {
    if (!canSubmit) {
      toast.error('請檢查信用卡資訊是否完整');
      return;
    }

    setIsProcessing(true);

    // Get Prime Token from TapPay
    window.TPDirect.card.getPrime(async (result) => {
      console.log('TapPay getPrime 完整結果:', JSON.stringify(result, null, 2));
      console.log('所有欄位:', Object.keys(result));

      if (result.status !== 0) {
        console.error('TapPay getPrime 失敗，status:', result.status, 'msg:', result.msg);
        onPaymentError(result.msg || '無法取得付款憑證');
        toast.error(result.msg || '付款失敗');
        setIsProcessing(false);
        return;
      }

      // Get prime from card object
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const prime = (result as any).card?.prime || result.prime;

      if (!prime) {
        console.error('Prime token 不存在！完整結果:', result);
        onPaymentError('無法取得付款憑證 (prime token 為空)');
        toast.error('無法取得付款憑證');
        setIsProcessing(false);
        return;
      }

      console.log('Prime token 取得成功:', prime.substring(0, 20) + '...');

      try {
        // Real TapPay payment processing
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/payment/process`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            prime: prime,
            amount: amount,
            plan_name: planName,
            details: {
              item_name: `Duotopia ${planName}`,
              item_price: amount
            },
            cardholder: {
              name: 'User',
              email: 'user@example.com',
              phone_number: '+886912345678'
            }
          })
        });

        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
          throw new Error('Server error: Invalid response format');
        }

        const data = await response.json();

        if (response.ok && data.success) {
          onPaymentSuccess(data.transaction_id);
          toast.success('付款成功！');
        } else {
          // Handle FastAPI validation errors (422)
          let errorMsg = data.message || '付款處理失敗';

          if (data.detail && Array.isArray(data.detail)) {
            // FastAPI validation error format
            console.error('完整驗證錯誤:', JSON.stringify(data.detail, null, 2));
            const validationErrors = data.detail.map((err: {loc?: string[]; msg: string}) => {
              const field = err.loc ? err.loc.join('.') : 'unknown';
              return `${field}: ${err.msg}`;
            }).join(', ');
            errorMsg = `驗證錯誤: ${validationErrors}`;
          } else if (data.detail) {
            errorMsg = data.detail;
          }

          throw new Error(errorMsg);
        }
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : '付款處理發生錯誤';
        onPaymentError(errorMsg);
        toast.error(errorMsg);
      } finally {
        setIsProcessing(false);
      }
    });
  };

  return (
    <div className="space-y-4">
      <SubscriptionProgressBanner
        currentStep="payment"
        selectedPlan={planName}
      />

      <Card className="w-full max-w-lg mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            信用卡付款
          </CardTitle>
          <div className="flex items-center justify-between mt-2">
            <span className="text-sm text-gray-600">方案: {planName}</span>
            <span className="text-lg font-semibold">NT$ {amount.toLocaleString()}</span>
          </div>
        </CardHeader>

      <CardContent className="space-y-4">
        {/* Security Badge */}
        <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg border border-green-200">
          <Shield className="h-4 w-4 text-green-600" />
          <span className="text-sm text-green-800">使用 TapPay 安全加密技術保護您的付款資訊</span>
        </div>

        {/* Card Number */}
        <div>
          <label className="block text-sm font-medium mb-2">卡號</label>
          <div className="relative">
            <div
              id="card-number"
              className={`tappay-field border rounded-lg px-4 py-3 bg-white ${
                cardErrors.number ? 'border-red-500' : 'border-gray-300'
              } focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500`}
              style={{ height: '48px' }}
            />
            {cardErrors.number && (
              <p className="text-red-500 text-xs mt-1">{cardErrors.number}</p>
            )}
          </div>
        </div>

        {/* Expiry and CVV */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">有效期限</label>
            <div
              id="card-expiration-date"
              className={`tappay-field border rounded-lg px-4 py-3 bg-white ${
                cardErrors.expiry ? 'border-red-500' : 'border-gray-300'
              } focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500`}
              style={{ height: '48px' }}
            />
            {cardErrors.expiry && (
              <p className="text-red-500 text-xs mt-1">{cardErrors.expiry}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">安全碼</label>
            <div
              id="card-ccv"
              className={`tappay-field border rounded-lg px-4 py-3 bg-white ${
                cardErrors.ccv ? 'border-red-500' : 'border-gray-300'
              } focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500`}
              style={{ height: '48px' }}
            />
            {cardErrors.ccv && (
              <p className="text-red-500 text-xs mt-1">{cardErrors.ccv}</p>
            )}
          </div>
        </div>

        {/* Test Mode Info */}
        <Alert className="bg-blue-50 border-blue-200">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-2">
              <Info className="h-4 w-4 text-blue-600 mt-0.5" />
              <AlertDescription className="text-blue-800">
                <strong>測試模式</strong><br />
                測試卡號: 4242 4242 4242 4242<br />
                有效期限: 任何未來日期 | CVV: 123
              </AlertDescription>
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText('4242 4242 4242 4242');
                  toast.success('已複製卡號');
                }}
                className="text-xs"
              >
                複製卡號
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText('12/28');
                  toast.success('已複製期限');
                }}
                className="text-xs"
              >
                複製期限
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText('123');
                  toast.success('已複製 CVV');
                }}
                className="text-xs"
              >
                複製 CVV
              </Button>
            </div>
          </div>
        </Alert>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-2">
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit || isProcessing || !isInitialized}
            className="flex-1"
          >
            {isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                處理中...
              </>
            ) : (
              <>支付 NT$ {amount.toLocaleString()}</>
            )}
          </Button>

          {onCancel && (
            <Button
              variant="outline"
              onClick={onCancel}
              disabled={isProcessing}
            >
              取消
            </Button>
          )}
        </div>

        {/* Card Brands */}
        <div className="flex items-center justify-center gap-2 pt-2">
          <img src="https://img.icons8.com/color/48/visa.png" alt="Visa" className="h-8" />
          <img src="https://img.icons8.com/color/48/mastercard.png" alt="Mastercard" className="h-8" />
          <img src="https://img.icons8.com/color/48/jcb.png" alt="JCB" className="h-8" />
          <img src="https://img.icons8.com/color/48/amex.png" alt="AMEX" className="h-8" />
        </div>
      </CardContent>
    </Card>
    </div>
  );
};

export default TapPayPayment;
