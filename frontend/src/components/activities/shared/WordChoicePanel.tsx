/**
 * WordChoicePanel - 單字選擇面板組件
 *
 * 顯示可選擇的單字按鈕
 */

import React from "react";
import { cn } from "@/lib/utils";

interface WordChoicePanelProps {
  words: string[];
  onWordClick: (word: string) => void;
  disabled?: boolean;
  variant?: "writing" | "listening";
}

const WordChoicePanel: React.FC<WordChoicePanelProps> = ({
  words,
  onWordClick,
  disabled = false,
  variant = "writing",
}) => {
  const baseColor = variant === "listening" ? "purple" : "blue";

  return (
    <div className="word-choices">
      <div className="text-sm font-medium mb-3 text-gray-700">選擇單字：</div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {words.map((word, idx) => (
          <button
            key={idx}
            onClick={() => !disabled && onWordClick(word)}
            disabled={disabled}
            className={cn(
              "px-4 py-3 bg-white border-2 rounded-lg font-medium transition-all",
              disabled
                ? "opacity-50 cursor-not-allowed border-gray-300 text-gray-500"
                : baseColor === "purple"
                ? "border-purple-300 text-purple-900 hover:bg-purple-50 hover:border-purple-400 active:scale-95"
                : "border-blue-300 text-blue-900 hover:bg-blue-50 hover:border-blue-400 active:scale-95"
            )}
          >
            {word}
          </button>
        ))}
      </div>
    </div>
  );
};

export default WordChoicePanel;
