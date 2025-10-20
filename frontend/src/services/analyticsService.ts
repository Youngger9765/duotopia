/**
 * Analytics Service - 前端錯誤收集到後端 (後端再送到 BigQuery)
 */

import { apiClient } from "../lib/api";

export interface PaymentErrorData {
  // 基本資訊
  timestamp: string;
  environment: string;

  // 錯誤資訊
  errorStage: string; // tappay_sdk, prime_generation, api_request, response_parsing
  errorMessage: string;
  errorCode?: string;
  stackTrace?: string;

  // 交易資訊
  amount?: number;
  planName?: string;

  // TapPay 相關
  tapPayStatus?: string;
  tapPayMessage?: string;
  canGetPrime?: boolean;

  // 瀏覽器資訊
  userAgent: string;
  url: string;

  // 額外資訊
  additionalContext?: Record<string, unknown>;
}

class AnalyticsService {
  /**
   * 記錄前端付款錯誤到後端 (後端會送到 BigQuery)
   */
  async logPaymentError(errorData: PaymentErrorData): Promise<void> {
    try {
      await apiClient.post("/api/payment/log-frontend-error", {
        ...errorData,
        timestamp: errorData.timestamp || new Date().toISOString(),
        environment: import.meta.env.MODE,
        userAgent: errorData.userAgent || navigator.userAgent,
        url: errorData.url || window.location.href,
      });
    } catch (error) {
      // 靜默失敗，不影響用戶體驗
      console.error("Failed to log payment error to analytics:", error);
    }
  }

  /**
   * 記錄 TapPay SDK 初始化錯誤
   */
  logTapPayInitError(error: Error | string): void {
    this.logPaymentError({
      timestamp: new Date().toISOString(),
      environment: import.meta.env.MODE,
      errorStage: "tappay_sdk",
      errorMessage: typeof error === "string" ? error : error.message,
      stackTrace: error instanceof Error ? error.stack : undefined,
      userAgent: navigator.userAgent,
      url: window.location.href,
    });
  }

  /**
   * 記錄 TapPay Prime Token 取得錯誤
   */
  logTapPayPrimeError(
    status: number,
    message: string,
    cardStatus?: { number?: number; expiry?: number; ccv?: number },
  ): void {
    this.logPaymentError({
      timestamp: new Date().toISOString(),
      environment: import.meta.env.MODE,
      errorStage: "prime_generation",
      errorMessage: message,
      errorCode: status.toString(),
      tapPayStatus: status.toString(),
      tapPayMessage: message,
      additionalContext: {
        cardStatus,
      },
      userAgent: navigator.userAgent,
      url: window.location.href,
    });
  }

  /**
   * 記錄付款 API 請求錯誤
   */
  logPaymentApiError(
    amount: number,
    planName: string,
    error: Error | string,
    responseStatus?: number,
    responseBody?: unknown,
  ): void {
    this.logPaymentError({
      timestamp: new Date().toISOString(),
      environment: import.meta.env.MODE,
      errorStage: "api_request",
      errorMessage: typeof error === "string" ? error : error.message,
      stackTrace: error instanceof Error ? error.stack : undefined,
      amount,
      planName,
      errorCode: responseStatus?.toString(),
      additionalContext: {
        responseStatus,
        responseBody,
      },
      userAgent: navigator.userAgent,
      url: window.location.href,
    });
  }

  /**
   * 記錄認證錯誤 (401)
   */
  logAuthenticationError(amount: number, planName: string): void {
    this.logPaymentError({
      timestamp: new Date().toISOString(),
      environment: import.meta.env.MODE,
      errorStage: "authentication",
      errorMessage: "User not authenticated or token expired",
      errorCode: "401",
      amount,
      planName,
      additionalContext: {
        hasToken: !!localStorage.getItem("teacher-auth-storage"),
        hasStudentToken: !!localStorage.getItem("student-auth-storage"),
      },
      userAgent: navigator.userAgent,
      url: window.location.href,
    });
  }
}

export const analyticsService = new AnalyticsService();
