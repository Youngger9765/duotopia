import { useState } from "react";
import { useTranslation } from "react-i18next";
import { QRCodeSVG } from "qrcode.react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Copy, Check } from "lucide-react";

interface ShareStudentLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  teacherEmail: string;
}

export function ShareStudentLoginModal({
  isOpen,
  onClose,
  teacherEmail,
}: ShareStudentLoginModalProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  // Generate the shareable URL with teacher email parameter
  const baseUrl = window.location.origin;
  const shareUrl = `${baseUrl}/student/login?teacher_email=${encodeURIComponent(teacherEmail)}`;

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("teacherDashboard.shareModal.title")}</DialogTitle>
          <DialogDescription>
            {t("teacherDashboard.shareModal.description")}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* QR Code Section */}
          <div className="flex flex-col items-center space-y-3">
            <p className="text-sm font-medium text-gray-700">
              {t("teacherDashboard.shareModal.scanQR")}
            </p>
            <div className="p-4 bg-white border-2 border-gray-200 rounded-lg">
              <QRCodeSVG
                value={shareUrl}
                size={200}
                level="H"
                includeMargin={true}
              />
            </div>
          </div>

          {/* URL Copy Section */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">
              {t("teacherDashboard.shareModal.shareLink")}
            </p>
            <div className="flex space-x-2">
              <Input
                value={shareUrl}
                readOnly
                className="flex-1 text-sm"
                onClick={(e) => e.currentTarget.select()}
              />
              <Button
                onClick={handleCopyLink}
                variant="outline"
                size="sm"
                className="flex-shrink-0"
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4 mr-1" />
                    {t("teacherDashboard.shareModal.copied")}
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-1" />
                    {t("teacherDashboard.shareModal.copyLink")}
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              {t("teacherDashboard.shareModal.instructions")}
            </p>
          </div>
        </div>

        <div className="flex justify-end mt-4">
          <Button onClick={onClose} variant="outline">
            {t("common.close")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
