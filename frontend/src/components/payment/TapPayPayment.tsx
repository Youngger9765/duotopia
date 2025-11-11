import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, CreditCard, Shield } from "lucide-react";
import { toast } from "sonner";
import SubscriptionProgressBanner from "../SubscriptionProgressBanner";
import { analyticsService } from "@/services/analyticsService";

interface TapPayPaymentProps {
  amount: number;
  planName: string;
  onPaymentSuccess?: (transactionId: string) => void;
  onPaymentError?: (error: string) => void;
  onCancel?: () => void;
  onSuccess?: () => void; // 用於卡片更新成功
  onClose?: () => void; // 用於關閉對話框
  isCardUpdate?: boolean; // 是否為卡片更新模式
}

const TapPayPayment: React.FC<TapPayPaymentProps> = ({
  amount,
  planName,
  onPaymentSuccess,
  onPaymentError,
  onCancel,
  onSuccess,
  isCardUpdate = false,
}) => {
  const [canSubmit, setCanSubmit] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [cardErrors, setCardErrors] = useState({
    number: "",
    expiry: "",
    ccv: "",
  });

  useEffect(() => {
    initializeTapPay();
  }, []);

  const initializeTapPay = () => {
    // TapPay 環境切換邏輯
    const SERVER_TYPE = import.meta.env.VITE_TAPPAY_SERVER_TYPE || "sandbox";

    // 根據環境自動選擇對應的 credentials
    const APP_ID = parseInt(
      SERVER_TYPE === "production"
        ? import.meta.env.VITE_TAPPAY_PRODUCTION_APP_ID || "164155"
        : import.meta.env.VITE_TAPPAY_SANDBOX_APP_ID || "164155",
    );
    const APP_KEY =
      SERVER_TYPE === "production"
        ? import.meta.env.VITE_TAPPAY_PRODUCTION_APP_KEY
        : import.meta.env.VITE_TAPPAY_SANDBOX_APP_KEY;

    if (!window.TPDirect) {
      console.error("TapPay SDK not loaded");
      toast.error("付款系統載入失敗，請重新整理頁面");

      // 📊 記錄 TapPay SDK 載入失敗
      analyticsService.logTapPayInitError("TapPay SDK not loaded");
      return;
    }

    // 延遲初始化，確保 DOM 已渲染
    setTimeout(() => {
      // 檢查元素是否存在
      const cardNumberEl = document.querySelector("#card-number");
      const expiryEl = document.querySelector("#card-expiration-date");
      const ccvEl = document.querySelector("#card-ccv");

      if (!cardNumberEl || !expiryEl || !ccvEl) {
        console.error("Payment form elements not found");
        return;
      }

      // Initialize SDK
      window.TPDirect.setupSDK(
        APP_ID,
        APP_KEY,
        SERVER_TYPE as "sandbox" | "production",
      );

      // Setup card fields
      const fields = {
        number: {
          element: "#card-number",
          placeholder: "**** **** **** ****",
        },
        expirationDate: {
          element: "#card-expiration-date",
          placeholder: "MM / YY",
        },
        ccv: {
          element: "#card-ccv",
          placeholder: "CVV",
        },
      };

      window.TPDirect.card.setup({
        fields: fields,
      });

      // Listen for card field updates
      window.TPDirect.card.onUpdate((update) => {
        setCanSubmit(update.canGetPrime);

        // Update error messages
        const errors = {
          number: "",
          expiry: "",
          ccv: "",
        };

        if (update.status.number === 1) {
          errors.number = "卡號格式不正確";
        }
        if (update.status.expiry === 1) {
          errors.expiry = "有效期限格式不正確";
        }
        if (update.status.ccv === 1) {
          errors.ccv = "安全碼格式不正確";
        }

        setCardErrors(errors);
      });

      setIsInitialized(true);
    }, 100);
  };

  // 🔧 修復：正確取得 token 和用戶資料
  const getAuthToken = (): string | null => {
    // 優先學生 token
    const studentAuth = localStorage.getItem("student-auth-storage");
    if (studentAuth) {
      try {
        const { state } = JSON.parse(studentAuth);
        if (state?.token) return state.token;
      } catch (e) {
        console.error("Failed to parse student auth:", e);
      }
    }

    // 檢查老師 token
    const teacherAuth = localStorage.getItem("teacher-auth-storage");
    if (teacherAuth) {
      try {
        const { state } = JSON.parse(teacherAuth);
        if (state?.token) return state.token;
      } catch (e) {
        console.error("Failed to parse teacher auth:", e);
      }
    }

    return null;
  };

  // 🔧 取得當前用戶資料（包含資料驗證）
  const getCurrentUser = (): {
    email: string;
    name: string;
    phone?: string;
  } => {
    // 優先檢查學生資料
    const studentAuth = localStorage.getItem("student-auth-storage");
    if (studentAuth) {
      try {
        const { state } = JSON.parse(studentAuth);
        if (state?.user) {
          const email = state.user.email?.trim();
          const name = state.user.name?.trim();

          // 驗證 email 格式
          if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            return {
              email,
              name: name || "User",
              phone: state.user.phone_number,
            };
          }
        }
      } catch (e) {
        console.error("Failed to parse student auth:", e);
      }
    }

    // 檢查老師資料
    const teacherAuth = localStorage.getItem("teacher-auth-storage");
    if (teacherAuth) {
      try {
        const { state } = JSON.parse(teacherAuth);
        if (state?.user) {
          const email = state.user.email?.trim();
          const name = state.user.name?.trim();

          // 驗證 email 格式
          if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            return {
              email,
              name: name || "User",
              phone: state.user.phone_number,
            };
          }
        }
      } catch (e) {
        console.error("Failed to parse teacher auth:", e);
      }
    }

    // 預設值（不應該發生，因為前面已檢查 token）
    console.warn("No valid user data found, using defaults");
    return { email: "user@example.com", name: "User" };
  };

  const handleSubmit = async () => {
    if (!canSubmit) {
      toast.error("請檢查信用卡資訊是否完整");
      return;
    }

    setIsProcessing(true);

    // Get Prime Token from TapPay
    window.TPDirect.card.getPrime(async (result) => {
      if (result.status !== 0) {
        console.error(
          "TapPay getPrime 失敗，status:",
          result.status,
          "msg:",
          result.msg,
        );

        // 📊 記錄 TapPay Prime 取得失敗
        analyticsService.logTapPayPrimeError(
          result.status,
          result.msg || "無法取得付款憑證",
          undefined, // cardStatus
        );

        if (onPaymentError) onPaymentError(result.msg || "無法取得付款憑證");
        toast.error(result.msg || "付款失敗");
        setIsProcessing(false);
        return;
      }

      // Get prime from card object
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const prime = (result as any).card?.prime || result.prime;

      if (!prime) {
        console.error("Prime token 不存在於 result.card.prime 或 result.prime");
        if (onPaymentError)
          onPaymentError("無法取得付款憑證 (prime token 為空)");
        toast.error("無法取得付款憑證");
        setIsProcessing(false);
        return;
      }

      try {
        // 🔧 修復：取得正確的 auth token 和用戶資料
        const authToken = getAuthToken();
        if (!authToken) {
          if (onPaymentError) onPaymentError("請先登入");
          toast.error("請先登入");
          setIsProcessing(false);
          return;
        }

        const currentUser = getCurrentUser();

        // 決定使用哪個 API endpoint
        const apiEndpoint = isCardUpdate
          ? `${import.meta.env.VITE_API_URL}/api/payment/update-card`
          : `${import.meta.env.VITE_API_URL}/api/payment/process`;

        const requestBody = isCardUpdate
          ? {
              prime: prime,
              cardholder: {
                name: currentUser.name,
                email: currentUser.email,
                phone_number: currentUser.phone || "+886912345678",
              },
            }
          : {
              prime: prime,
              amount: amount,
              plan_name: planName,
              details: {
                item_name: `Duotopia ${planName}`,
                item_price: amount,
              },
              cardholder: {
                name: currentUser.name,
                email: currentUser.email,
                phone_number: currentUser.phone || "+886912345678",
              },
            };

        // Real TapPay payment processing or card update
        const response = await fetch(apiEndpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify(requestBody),
        });

        // Check if response is JSON
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
          throw new Error("Server error: Invalid response format");
        }

        const data = await response.json();

        if (response.ok && data.success) {
          if (isCardUpdate) {
            // 卡片更新成功
            if (onSuccess) onSuccess();
            toast.success("信用卡更新成功！");
          } else {
            // 付款成功
            if (onPaymentSuccess) onPaymentSuccess(data.transaction_id);
            toast.success("付款成功！");
          }
        } else {
          // 📊 記錄付款 API 失敗
          analyticsService.logPaymentApiError(
            amount,
            planName,
            data.message || "付款處理失敗",
            response.status,
            data,
          );
          // Handle FastAPI validation errors (422)
          let errorMsg = data.message || "付款處理失敗";

          // 🎉 檢查是否為免費優惠期間提醒
          if (
            errorMsg.includes("免費優惠期間") ||
            errorMsg.includes("未來將會開放儲值")
          ) {
            // 顯示友善的提醒訊息
            toast.info(errorMsg, {
              duration: 5000,
            });
            if (onPaymentError) onPaymentError(errorMsg);
            return; // 不throw error
          }

          if (data.detail && Array.isArray(data.detail)) {
            // FastAPI validation error format
            console.error(
              "完整驗證錯誤:",
              JSON.stringify(data.detail, null, 2),
            );
            const validationErrors = data.detail
              .map((err: { loc?: string[]; msg: string }) => {
                const field = err.loc ? err.loc.join(".") : "unknown";
                return `${field}: ${err.msg}`;
              })
              .join(", ");
            errorMsg = `驗證錯誤: ${validationErrors}`;
          } else if (data.detail) {
            errorMsg = data.detail;
          }

          throw new Error(errorMsg);
        }
      } catch (error) {
        const errorMsg =
          error instanceof Error
            ? error.message
            : isCardUpdate
              ? "信用卡更新發生錯誤"
              : "付款處理發生錯誤";
        if (onPaymentError) onPaymentError(errorMsg);
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
            <span className="text-lg font-semibold">
              NT$ {amount.toLocaleString()}
            </span>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Security Badge */}
          <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg border border-green-200">
            <Shield className="h-4 w-4 text-green-600" />
            <span className="text-sm text-green-800">
              使用 TapPay 安全加密技術保護您的付款資訊
            </span>
          </div>

          {/* Card Number */}
          <div>
            <label className="block text-sm font-medium mb-2">卡號</label>
            <div className="relative">
              <div
                id="card-number"
                className={`tappay-field border rounded-lg px-4 py-3 bg-white ${
                  cardErrors.number ? "border-red-500" : "border-gray-300"
                } focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500`}
                style={{ height: "48px" }}
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
                  cardErrors.expiry ? "border-red-500" : "border-gray-300"
                } focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500`}
                style={{ height: "48px" }}
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
                  cardErrors.ccv ? "border-red-500" : "border-gray-300"
                } focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500`}
                style={{ height: "48px" }}
              />
              {cardErrors.ccv && (
                <p className="text-red-500 text-xs mt-1">{cardErrors.ccv}</p>
              )}
            </div>
          </div>

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
            <img
              src="https://img.icons8.com/color/48/visa.png"
              alt="Visa"
              className="h-8"
            />
            <img
              src="https://img.icons8.com/color/48/mastercard.png"
              alt="Mastercard"
              className="h-8"
            />
            <img
              src="https://img.icons8.com/color/48/jcb.png"
              alt="JCB"
              className="h-8"
            />
            <img
              src="https://img.icons8.com/color/48/amex.png"
              alt="AMEX"
              className="h-8"
            />
          </div>

          {/* Prorated Payment Notice - 移至底部 */}
          {!isCardUpdate && (
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200 mt-4">
              <p className="text-sm text-blue-800 font-medium mb-1">
                💡 首月比例計費
              </p>
              <p className="text-xs text-blue-700">
                本次付款按本月剩餘天數比例計算。下個月 1 號起，將以全額 (NT${" "}
                {planName === "Tutor Teachers" ? "230" : "330"}) 自動續訂。
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TapPayPayment;
