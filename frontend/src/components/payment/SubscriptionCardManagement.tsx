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
      await apiClient.delete("/api/payment/saved-card");
      toast.success("信用卡已刪除");
      setSavedCard(null);
      setShowDeleteDialog(false);
    } catch (error: unknown) {
      console.error("Failed to delete card:", error);
      const apiError = error as { response?: { data?: { detail?: string } } };
      toast.error(apiError.response?.data?.detail || "刪除信用卡失敗");
    } finally {
      setDeleting(false);
    }
  };

  const handleUpdateSuccess = async () => {
    toast.success("信用卡已更新");
    setShowUpdateDialog(false);
    await fetchSavedCard();
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
            <DialogDescription className="space-y-2 pt-2">
              <p>刪除信用卡後，自動續訂功能將無法使用。</p>
              <p className="text-sm text-gray-600">
                卡號：•••• {savedCard?.last_four}
              </p>
              <p className="text-sm font-medium text-orange-600">
                ⚠️ 下次續訂時需要手動付款
              </p>
            </DialogDescription>
          </DialogHeader>

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
    </>
  );
};
