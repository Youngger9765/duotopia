/**
 * PermissionBanner - Permission restriction notice for organization mode
 *
 * Displays an informational banner explaining that teachers have
 * restricted permissions in organization/school context.
 */

import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { AlertCircle, X } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

const STORAGE_KEY = "workspace:permission-banner-dismissed";

export const PermissionBanner: React.FC = () => {
  const { t } = useTranslation();
  const [isDismissed, setIsDismissed] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) === "true";
  });

  const handleDismiss = () => {
    setIsDismissed(true);
    localStorage.setItem(STORAGE_KEY, "true");
  };

  if (isDismissed) {
    return null;
  }

  return (
    <Alert className="mx-3 mb-4 border-l-4 border-amber-400 bg-amber-50 dark:bg-amber-900/20">
      <div className="flex items-start gap-3">
        <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1 space-y-1">
          <div className="text-sm font-medium text-amber-800 dark:text-amber-300">
            {t("workspace.organization.bannerTitle")}
          </div>
          <AlertDescription className="text-xs text-amber-700 dark:text-amber-400">
            {t("workspace.organization.bannerDescription")}
          </AlertDescription>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 hover:bg-amber-100 dark:hover:bg-amber-900/40"
          onClick={handleDismiss}
        >
          <X className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
          <span className="sr-only">{t("workspace.permissions.close")}</span>
        </Button>
      </div>
    </Alert>
  );
};

export default PermissionBanner;
