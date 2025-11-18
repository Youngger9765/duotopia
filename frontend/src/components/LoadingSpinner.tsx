import { Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";

interface LoadingSpinnerProps {
  message?: string;
  size?: "sm" | "md" | "lg";
  fullPage?: boolean;
}

export default function LoadingSpinner({
  message,
  size = "md",
  fullPage = false,
}: LoadingSpinnerProps) {
  const { t } = useTranslation();
  const sizeClasses = {
    sm: "h-8 w-8",
    md: "h-12 w-12",
    lg: "h-16 w-16",
  };

  const textSizeClasses = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg",
  };

  const containerClasses = fullPage
    ? "flex items-center justify-center min-h-[60vh]"
    : "flex items-center justify-center min-h-[400px]";

  return (
    <div className={containerClasses}>
      <div className="text-center space-y-4">
        {/* Primary spinning loader with better visibility */}
        <div className="relative">
          <Loader2
            className={`${sizeClasses[size]} text-blue-600 animate-spin mx-auto`}
            strokeWidth={2.5}
          />
          {/* Pulsing background circle for better visibility */}
          <div
            className={`absolute inset-0 ${sizeClasses[size]} bg-blue-100 rounded-full animate-pulse mx-auto opacity-30`}
          />
        </div>

        {/* Loading text with animation */}
        <div className="space-y-2">
          <p className={`${textSizeClasses[size]} font-medium text-gray-700`}>
            {message || t("common.loading")}
          </p>
          <div className="flex justify-center space-x-1">
            <span
              className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
              style={{ animationDelay: "0ms" }}
            ></span>
            <span
              className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
              style={{ animationDelay: "150ms" }}
            ></span>
            <span
              className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
              style={{ animationDelay: "300ms" }}
            ></span>
          </div>
        </div>
      </div>
    </div>
  );
}
