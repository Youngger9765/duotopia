/**
 * Demo Card Component
 * Display card for each demo practice mode on homepage
 */

import { cn } from "@/lib/utils";
import { ReactNode } from "react";

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
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "group relative overflow-hidden rounded-2xl p-6 text-left transition-all duration-300",
        "border border-gray-200 bg-white shadow-lg",
        "hover:shadow-2xl hover:-translate-y-1",
        disabled && "opacity-50 cursor-not-allowed hover:shadow-lg hover:translate-y-0"
      )}
    >
      {/* Gradient background on hover */}
      <div
        className={cn(
          "absolute inset-0 bg-gradient-to-br opacity-0 transition-opacity duration-300",
          "group-hover:opacity-10",
          gradient
        )}
      />

      {/* Icon container */}
      <div
        className={cn(
          "relative w-14 h-14 rounded-xl flex items-center justify-center mb-4",
          "bg-gradient-to-br text-white",
          "group-hover:scale-110 transition-transform duration-300",
          gradient
        )}
      >
        {icon}
      </div>

      {/* Content */}
      <div className="relative">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-sm text-gray-600">{description}</p>
      </div>

      {/* Arrow indicator */}
      <div className="relative mt-4 flex items-center text-sm font-medium text-gray-500 group-hover:text-blue-600 transition-colors">
        立即體驗
        <svg
          className="ml-1 h-4 w-4 transform group-hover:translate-x-1 transition-transform"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      </div>
    </button>
  );
}
