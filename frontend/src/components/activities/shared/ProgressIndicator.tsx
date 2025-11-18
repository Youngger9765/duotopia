/**
 * ProgressIndicator - 進度指示器組件
 *
 * 顯示當前題目進度和完成百分比
 */

import React from "react";

interface ProgressIndicatorProps {
  current: number;
  total: number;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  current,
  total,
}) => {
  const percentage = Math.round((current / total) * 100);

  return (
    <div className="progress-indicator">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-medium text-gray-700">
          第 {current} 題 / 共 {total} 題
        </div>
        <div className="text-sm font-semibold text-blue-600">{percentage}%</div>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

export default ProgressIndicator;
