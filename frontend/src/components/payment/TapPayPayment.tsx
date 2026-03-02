import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Shield } from "lucide-react";
import { toast } from "sonner";
import SubscriptionProgressBanner from "../SubscriptionProgressBanner";
import { analyticsService } from "@/services/analyticsService";
import { useTranslation } from "react-i18next";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";
import { useStudentAuthStore } from "@/stores/studentAuthStore";

interface TapPayPaymentProps {
  amount: number;
  planName: string;
  onPaymentSuccess?: (transactionId: string) => void;
  onPaymentError?: (error: string) => void;
  onCancel?: () => void;
  onSuccess?: () => void; // 用於卡片更新成功
  onClose?: () => void; // 用於關閉對話框
  isCardUpdate?: boolean; // 是否為卡片更新模式
  apiEndpoint?: string; // Custom API endpoint (default: /api/payment/process)
  customPayload?: Record<string, unknown>; // Extra fields to merge into request body
}

const TapPayPayment: React.FC<TapPayPaymentProps> = ({
  amount,
  planName,
  onPaymentSuccess,
  onPaymentError,
  onCancel,
  onSuccess,
  isCardUpdate = false,
  apiEndpoint,
  customPayload,
}) => {
  const { t } = useTranslation();
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
      toast.error(t("payment.toast.systemLoadFailed"));

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
    const studentToken = useStudentAuthStore.getState().token;
    if (studentToken) return studentToken;

    // 檢查老師 token
    const teacherToken = useTeacherAuthStore.getState().token;
    if (teacherToken) return teacherToken;

    return null;
  };

  // 🔧 取得當前用戶資料（包含資料驗證）
  const getCurrentUser = (): {
    email: string;
    name: string;
    phone?: string;
  } => {
    // 優先檢查學生資料
    const studentUser = useStudentAuthStore.getState().user;
    if (studentUser) {
      const email = studentUser.email?.trim();
      const name = studentUser.name?.trim();

      // 驗證 email 格式
      if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        return {
          email,
          name: name || "User",
          phone: undefined, // StudentUser 沒有 phone 屬性
        };
      }
    }

    // 檢查老師資料
    const teacherUser = useTeacherAuthStore.getState().user;
    if (teacherUser) {
      const email = teacherUser.email?.trim();
      const name = teacherUser.name?.trim();

      // 驗證 email 格式
      if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        return {
          email,
          name: name || "User",
          phone: teacherUser.phone,
        };
      }
    }

    // 預設值（不應該發生，因為前面已檢查 token）
    console.warn("No valid user data found, using defaults");
    return { email: "user@example.com", name: "User" };
  };

  const handleSubmit = async () => {
    if (!canSubmit) {
      toast.error(t("payment.toast.checkCardInfo"));
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

        if (onPaymentError)
          onPaymentError(result.msg || t("payment.toast.cannotGetToken"));
        toast.error(result.msg || t("payment.toast.paymentFailed"));
        setIsProcessing(false);
        return;
      }

      // Get prime from card object
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const prime = (result as any).card?.prime || result.prime;

      if (!prime) {
        console.error("Prime token 不存在於 result.card.prime 或 result.prime");
        if (onPaymentError)
          onPaymentError(
            t("payment.toast.cannotGetToken") + " (prime token 為空)",
          );
        toast.error(t("payment.toast.cannotGetToken"));
        setIsProcessing(false);
        return;
      }

      try {
        // 🔧 修復：取得正確的 auth token 和用戶資料
        const authToken = getAuthToken();
        if (!authToken) {
          if (onPaymentError) onPaymentError(t("payment.toast.loginRequired"));
          toast.error(t("payment.toast.loginRequired"));
          setIsProcessing(false);
          return;
        }

        const currentUser = getCurrentUser();

        // 決定使用哪個 API endpoint
        const finalEndpoint = isCardUpdate
          ? `${import.meta.env.VITE_API_URL}/api/payment/update-card`
          : apiEndpoint
            ? `${import.meta.env.VITE_API_URL}${apiEndpoint}`
            : `${import.meta.env.VITE_API_URL}/api/payment/process`;

        const cardholderData = {
          name: currentUser.name,
          email: currentUser.email,
          phone_number: currentUser.phone || "+886912345678",
        };

        const requestBody = isCardUpdate
          ? {
              prime: prime,
              cardholder: cardholderData,
            }
          : {
              prime: prime,
              amount: amount,
              plan_name: planName,
              details: {
                item_name: `Duotopia ${planName}`,
                item_price: amount,
              },
              cardholder: cardholderData,
              ...customPayload,
            };

        // Real TapPay payment processing or card update
        const response = await fetch(finalEndpoint, {
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
            toast.success(t("payment.toast.cardUpdateSuccess"));
          } else {
            // 付款成功
            if (onPaymentSuccess) onPaymentSuccess(data.transaction_id);
            toast.success(t("payment.toast.paymentSuccess"));
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
    <div className="flex gap-4 p-2 sm:p-4">
      {/* Vertical stepper sidebar — hidden on mobile */}
      <div className="hidden sm:block flex-shrink-0 pr-4">
        <SubscriptionProgressBanner
          currentStep="payment"
          selectedPlan={planName}
          vertical
        />
      </div>

      {/* Payment form */}
      <Card className="w-full">
        <CardContent className="space-y-3 pt-5">
          {/* Security Badge */}
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-green-600 flex-shrink-0" />
            <span className="text-sm text-green-700">
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
        </CardContent>
      </Card>
    </div>
  );
};

export default TapPayPayment;
