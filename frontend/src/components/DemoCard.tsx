/**
 * Demo Card Component
 * Display card for each demo practice mode on homepage
 * Enhanced with better hover effects for clickability
 */

import { cn } from "@/lib/utils";
import { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ArrowRight, Play } from "lucide-react";

interface DemoCardProps {
  icon: ReactNode;
  title: string;
  description: string;
  onClick: () => void;
  gradient: string;
  disabled?: boolean;
}

export function DemoCard({
  icon,
  title,
  description,
  onClick,
  gradient,
  disabled = false,
}: DemoCardProps) {
  const { t } = useTranslation();

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        // Base styles
        "group relative overflow-hidden rounded-2xl p-5 text-left transition-all duration-300",
        "border-2 border-gray-200 bg-white cursor-pointer",
        // Shadow and transform on hover
        "shadow-md hover:shadow-xl hover:-translate-y-2",
        // Ring effect for focus/hover
        "hover:border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
        // Disabled state
        disabled &&
          "opacity-50 cursor-not-allowed hover:shadow-md hover:translate-y-0 hover:border-gray-200",
      )}
    >
      {/* Gradient background on hover */}
      <div
        className={cn(
          "absolute inset-0 bg-gradient-to-br opacity-0 transition-opacity duration-300",
          "group-hover:opacity-10",
          gradient,
          disabled && "group-hover:opacity-0",
        )}
      />

      {/* Play button overlay - appears on hover */}
      {!disabled && (
        <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-all duration-300 transform scale-75 group-hover:scale-100">
          <div
            className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center",
              "bg-gradient-to-br text-white shadow-lg",
              gradient,
            )}
          >
            <Play className="h-4 w-4 ml-0.5" fill="currentColor" />
          </div>
        </div>
      )}

      {/* Icon container */}
      <div
        className={cn(
          "relative w-12 h-12 rounded-xl flex items-center justify-center mb-3",
          "bg-gradient-to-br text-white shadow-md",
          "group-hover:scale-110 group-hover:shadow-lg transition-all duration-300",
          gradient,
        )}
      >
        {icon}
      </div>

      {/* Content */}
      <div className="relative">
        <h3 className="text-base font-semibold text-gray-900 mb-1.5 group-hover:text-gray-800">
          {title}
        </h3>
        <p className="text-sm text-gray-600 leading-relaxed line-clamp-2">
          {description}
        </p>
      </div>

      {/* CTA indicator - enhanced with animation */}
      <div className="relative mt-3 flex items-center text-sm font-medium text-gray-500 group-hover:text-blue-600 transition-colors">
        <span className="group-hover:underline">
          {t("home.demo.tryNow", "立即體驗")}
        </span>
        <ArrowRight className="ml-1.5 h-4 w-4 transform group-hover:translate-x-1 transition-transform" />
      </div>

      {/* Bottom border indicator - shows on hover */}
      <div
        className={cn(
          "absolute bottom-0 left-0 right-0 h-1 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left",
          "bg-gradient-to-r",
          gradient,
          disabled && "group-hover:scale-x-0",
        )}
      />
    </button>
  );
}
