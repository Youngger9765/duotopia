import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  text?: string;
  className?: string;
}

/**
 * LoadingSpinner - Unified loading state component
 */
export function LoadingSpinner({
  size = "md",
  text = "載入中...",
  className,
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  };

  const textSizeClasses = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg",
  };

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-8",
        className,
      )}
    >
      <Loader2
        className={cn("animate-spin text-blue-600", sizeClasses[size])}
      />
      {text && (
        <p className={cn("text-gray-500 mt-3", textSizeClasses[size])}>
          {text}
        </p>
      )}
    </div>
  );
}
