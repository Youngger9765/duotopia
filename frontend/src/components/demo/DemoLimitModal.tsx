/**
 * Demo Limit Modal
 *
 * Displays when user has exceeded their daily demo quota.
 * Encourages registration while providing reset time info.
 */

import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DemoLimitModalProps {
  open: boolean;
  onClose: () => void;
  resetAt: string;
  limit?: number;
}

export function DemoLimitModal({
  open,
  onClose,
  resetAt,
  limit = 60,
}: DemoLimitModalProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();

  // Format reset time for display
  const formatResetTime = (isoString: string): string => {
    try {
      const date = new Date(isoString);
      return date.toLocaleString("zh-TW", {
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "明天";
    }
  };

  const resetTimeDisplay = formatResetTime(resetAt);

  const handleRegister = () => {
    onClose();
    navigate("/register");
  };

  const handleLogin = () => {
    onClose();
    navigate("/login");
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl">
            {t("demo.limitReached.title")}
          </DialogTitle>
          <DialogDescription className="pt-2">
            {t("demo.limitReached.description", { limit })}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Registration CTA */}
          <div className="rounded-lg bg-blue-50 p-4 border border-blue-100">
            <p className="font-medium text-blue-900">
              {t("demo.limitReached.ctaTitle")}
            </p>
            <p className="mt-1 text-sm text-blue-700">
              {t("demo.limitReached.ctaDescription")}
            </p>
          </div>

          {/* Reset time info */}
          <p className="text-sm text-muted-foreground text-center">
            {t("demo.limitReached.resetInfo", {
              resetTime: resetTimeDisplay,
            })}
          </p>
        </div>

        <DialogFooter className="flex-col gap-2 sm:flex-row">
          <Button variant="outline" onClick={handleLogin} className="w-full sm:w-auto">
            {t("demo.limitReached.login")}
          </Button>
          <Button onClick={handleRegister} className="w-full sm:w-auto">
            {t("demo.limitReached.register")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
