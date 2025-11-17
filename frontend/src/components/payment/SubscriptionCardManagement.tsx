/**
 * 訂閱卡片管理組件
 * 顯示已儲存的信用卡、提供更換/刪除功能
 */

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CreditCardDisplay } from "./CreditCardDisplay";
import TapPayPayment from "./TapPayPayment";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import {
  CreditCard,
  Trash2,
  RefreshCw,
  AlertTriangle,
  Shield,
} from "lucide-react";

interface SavedCard {
  last_four: string;
  card_type: string;
  card_type_code: number;
  issuer: string;
  saved_at: string;
}

interface SavedCardResponse {
  has_card: boolean;
  card: SavedCard | null;
}

export const SubscriptionCardManagement: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [savedCard, setSavedCard] = useState<SavedCard | null>(null);
  const [showUpdateDialog, setShowUpdateDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showAutoRenewConfirm, setShowAutoRenewConfirm] = useState(false);
  const [pendingCardUpdate, setPendingCardUpdate] = useState(false);

  useEffect(() => {
    fetchSavedCard();
  }, []);

  const fetchSavedCard = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<SavedCardResponse>(
        "/api/payment/saved-card",
      );
      if (data.has_card && data.card) {
        setSavedCard(data.card);
      } else {
        setSavedCard(null);
      }
    } catch (error: unknown) {
      console.error("Failed to fetch saved card:", error);
      toast.error("無法載入信用卡資訊");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCard = async () => {
    try {
      setDeleting(true);
      const response = await apiClient.delete<{
        success: boolean;
        message: string;
        card_bound: boolean;
        auto_renew: boolean;
      }>("/api/payment/saved-card");

      // 🔴 PRD Rule 2: 刪除綁卡後，自動續訂已被關閉
      toast.success(response.message || "信用卡已解綁，自動續訂已關閉");
      setSavedCard(null);
      setShowDeleteDialog(false);

      // 觸發頁面重新載入訂閱狀態（包含 auto_renew）
      window.dispatchEvent(new CustomEvent("subscriptionStatusChanged"));
    } catch (error: unknown) {
      console.error("Failed to delete card:", error);
      const apiError = error as { response?: { data?: { detail?: string } } };
      toast.error(apiError.response?.data?.detail || "刪除信用卡失敗");
    } finally {
      setDeleting(false);
    }
  };

  const handleUpdateSuccess = async () => {
    // 🔴 PRD Rule 1: 綁卡成功後詢問是否啟用自動續訂
    setShowUpdateDialog(false);
    setShowAutoRenewConfirm(true);
    // 不要設為 true，讓用戶可以點擊按鈕
  };

  const handleAutoRenewChoice = async (enableAutoRenew: boolean) => {
    try {
      setShowAutoRenewConfirm(false);

      // 🔴 根據用戶選擇，呼叫對應 API 設定 auto_renew
      if (enableAutoRenew) {
        // 啟用自動續訂
        await apiClient.post("/api/teachers/subscription/reactivate");
      } else {
        // 確保自動續訂關閉（如果後端有設定的話）
        try {
          await apiClient.post("/api/teachers/subscription/cancel");
        } catch {
          // 如果本來就是關閉的，忽略錯誤
          console.log("Auto-renew already disabled or not set");
        }
      }

      // 重新載入卡片資訊
      await fetchSavedCard();

      // 觸發頁面更新訂閱狀態
      window.dispatchEvent(new CustomEvent("subscriptionStatusChanged"));

      if (enableAutoRenew) {
        toast.success("信用卡已綁定，自動續訂已啟用");
      } else {
        toast.success("信用卡已綁定，可手動續訂");
      }

      setPendingCardUpdate(false);
    } catch (error) {
      console.error("Failed to set auto-renew:", error);
      const apiError = error as { response?: { data?: { detail?: string } } };
      toast.error(apiError.response?.data?.detail || "設定失敗，請稍後再試");
      setPendingCardUpdate(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            付款方式管理
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">載入中...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            付款方式管理
          </CardTitle>
          <CardDescription>管理您的自動續訂付款方式</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {savedCard ? (
            <>
              {/* 已儲存的卡片 */}
              <div>
                <h3 className="text-sm font-medium mb-4">目前使用的信用卡</h3>
                <CreditCardDisplay card={savedCard} />
              </div>

              {/* 安全提示 */}
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription className="ml-2">
                  <strong>安全保障：</strong>
                  您的完整卡號不會儲存在我們的伺服器， 所有敏感資訊都由 TapPay
                  金流安全加密處理。
                </AlertDescription>
              </Alert>

              {/* 操作按鈕 */}
              <div className="flex gap-3">
                <Button
                  onClick={() => setShowUpdateDialog(true)}
                  variant="outline"
                  className="flex-1"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  更換信用卡
                </Button>
                <Button
                  onClick={() => setShowDeleteDialog(true)}
                  variant="outline"
                  className="flex-1 text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  刪除信用卡
                </Button>
              </div>
            </>
          ) : (
            <>
              {/* 沒有儲存卡片 */}
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="ml-2">
                  您尚未儲存付款方式。儲存信用卡後，系統將在每月 1 號自動續訂。
                </AlertDescription>
              </Alert>

              <Button
                onClick={() => setShowUpdateDialog(true)}
                className="w-full"
              >
                <CreditCard className="w-4 h-4 mr-2" />
                新增信用卡
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* 更換/新增信用卡 Dialog */}
      <Dialog open={showUpdateDialog} onOpenChange={setShowUpdateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{savedCard ? "更換信用卡" : "新增信用卡"}</DialogTitle>
            <DialogDescription>
              系統將進行 1 元授權測試以驗證信用卡，測試完成後會立即退款。
            </DialogDescription>
          </DialogHeader>

          <TapPayPayment
            amount={1}
            planName="Card Verification"
            isCardUpdate={true}
            onSuccess={handleUpdateSuccess}
            onClose={() => setShowUpdateDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* 刪除確認 Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              確認刪除信用卡
            </DialogTitle>
            <DialogDescription>
              刪除信用卡後，自動續訂功能將無法使用。
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 pt-2">
            <div className="text-sm text-gray-600">
              卡號：•••• {savedCard?.last_four}
            </div>
            <div className="text-sm font-medium text-orange-600">
              ⚠️ 下次續訂時需要手動付款
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={deleting}
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteCard}
              disabled={deleting}
            >
              {deleting ? "刪除中..." : "確認刪除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 🔴 PRD Rule 1: 自動續訂確認 Dialog */}
      <Dialog
        open={showAutoRenewConfirm}
        onOpenChange={setShowAutoRenewConfirm}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-blue-600">
              <RefreshCw className="w-5 h-5" />
              啟用自動續訂？
            </DialogTitle>
            <DialogDescription>
              ✅ 信用卡已成功綁定！是否要啟用自動續訂功能？
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 pt-2">
            <div className="bg-blue-50 p-3 rounded-lg text-sm space-y-2">
              <div className="font-medium text-blue-900">
                💡 自動續訂的好處：
              </div>
              <ul className="space-y-1 text-blue-800 ml-4">
                <li>• 每月 1 號自動扣款，不用擔心忘記續訂</li>
                <li>• 確保服務不中斷</li>
                <li>• 隨時可以取消，沒有綁約限制</li>
              </ul>
            </div>
            <div className="text-sm text-gray-600">
              ℹ️ 您隨時可以在訂閱管理頁面變更此設定
            </div>
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={() => handleAutoRenewChoice(false)}
              disabled={pendingCardUpdate}
              className="w-full sm:w-auto"
            >
              否，手動續訂
            </Button>
            <Button
              onClick={() => handleAutoRenewChoice(true)}
              disabled={pendingCardUpdate}
              className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white dark:text-white"
            >
              是，自動續訂
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
