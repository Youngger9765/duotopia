/**
 * 訂閱卡片管理組件
 * 顯示已儲存的信用卡、提供更換/刪除功能
 */

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
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
      toast.error(t("subscriptionCardManagement.messages.loadFailed"));
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
      toast.success(
        response.message ||
          t("subscriptionCardManagement.messages.deleteSuccess"),
      );
      setSavedCard(null);
      setShowDeleteDialog(false);

      // 觸發頁面重新載入訂閱狀態（包含 auto_renew）
      window.dispatchEvent(new CustomEvent("subscriptionStatusChanged"));
    } catch (error: unknown) {
      console.error("Failed to delete card:", error);
      const apiError = error as { response?: { data?: { detail?: string } } };
      toast.error(
        apiError.response?.data?.detail ||
          t("subscriptionCardManagement.messages.deleteFailed"),
      );
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
        toast.success(t("subscriptionCardManagement.messages.cardBound"));
      } else {
        toast.success(t("subscriptionCardManagement.messages.cardBoundManual"));
      }

      setPendingCardUpdate(false);
    } catch (error) {
      console.error("Failed to set auto-renew:", error);
      const apiError = error as { response?: { data?: { detail?: string } } };
      toast.error(
        apiError.response?.data?.detail ||
          t("subscriptionCardManagement.messages.settingFailed"),
      );
      setPendingCardUpdate(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            {t("subscriptionCardManagement.title")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            {t("subscriptionCardManagement.loading")}
          </div>
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
            {t("subscriptionCardManagement.title")}
          </CardTitle>
          <CardDescription>
            {t("subscriptionCardManagement.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {savedCard ? (
            <>
              {/* 已儲存的卡片 */}
              <div>
                <h3 className="text-sm font-medium mb-4">
                  {t("subscriptionCardManagement.currentCard.title")}
                </h3>
                <CreditCardDisplay card={savedCard} />
              </div>

              {/* 安全提示 */}
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription className="ml-2">
                  <strong>
                    {t("subscriptionCardManagement.security.title")}
                  </strong>
                  {t("subscriptionCardManagement.security.description")}
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
                  {t("subscriptionCardManagement.buttons.updateCard")}
                </Button>
                <Button
                  onClick={() => setShowDeleteDialog(true)}
                  variant="outline"
                  className="flex-1 text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  {t("subscriptionCardManagement.buttons.deleteCard")}
                </Button>
              </div>
            </>
          ) : (
            <>
              {/* 沒有儲存卡片 */}
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="ml-2">
                  {t("subscriptionCardManagement.noCard.warning")}
                </AlertDescription>
              </Alert>

              <Button
                onClick={() => setShowUpdateDialog(true)}
                className="w-full"
              >
                <CreditCard className="w-4 h-4 mr-2" />
                {t("subscriptionCardManagement.buttons.addCard")}
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* 更換/新增信用卡 Dialog */}
      <Dialog open={showUpdateDialog} onOpenChange={setShowUpdateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {savedCard
                ? t("subscriptionCardManagement.dialogs.update.title")
                : t("subscriptionCardManagement.dialogs.update.titleNew")}
            </DialogTitle>
            <DialogDescription>
              {t("subscriptionCardManagement.dialogs.update.description")}
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
              {t("subscriptionCardManagement.dialogs.delete.title")}
            </DialogTitle>
            <DialogDescription>
              {t("subscriptionCardManagement.dialogs.delete.description")}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 pt-2">
            <div className="text-sm text-gray-600">
              {t("subscriptionCardManagement.dialogs.delete.cardInfo", {
                lastFour: savedCard?.last_four,
              })}
            </div>
            <div className="text-sm font-medium text-orange-600">
              {t("subscriptionCardManagement.dialogs.delete.warning")}
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={deleting}
            >
              {t("subscriptionCardManagement.buttons.cancel")}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteCard}
              disabled={deleting}
            >
              {deleting
                ? t("subscriptionCardManagement.buttons.deleting")
                : t("subscriptionCardManagement.buttons.confirmDelete")}
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
              {t("subscriptionCardManagement.dialogs.autoRenew.title")}
            </DialogTitle>
            <DialogDescription>
              {t("subscriptionCardManagement.dialogs.autoRenew.description")}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 pt-2">
            <div className="bg-blue-50 p-3 rounded-lg text-sm space-y-2">
              <div className="font-medium text-blue-900">
                {t(
                  "subscriptionCardManagement.dialogs.autoRenew.benefits.title",
                )}
              </div>
              <ul className="space-y-1 text-blue-800 ml-4">
                <li>
                  {t(
                    "subscriptionCardManagement.dialogs.autoRenew.benefits.monthly",
                  )}
                </li>
                <li>
                  {t(
                    "subscriptionCardManagement.dialogs.autoRenew.benefits.continuous",
                  )}
                </li>
                <li>
                  {t(
                    "subscriptionCardManagement.dialogs.autoRenew.benefits.flexible",
                  )}
                </li>
              </ul>
            </div>
            <div className="text-sm text-gray-600">
              {t("subscriptionCardManagement.dialogs.autoRenew.note")}
            </div>
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={() => handleAutoRenewChoice(false)}
              disabled={pendingCardUpdate}
              className="w-full sm:w-auto"
            >
              {t("subscriptionCardManagement.buttons.no")}
            </Button>
            <Button
              onClick={() => handleAutoRenewChoice(true)}
              disabled={pendingCardUpdate}
              className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white dark:text-white"
            >
              {t("subscriptionCardManagement.buttons.yes")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
