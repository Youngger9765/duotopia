/**
 * 信用卡示意圖組件
 * 顯示已儲存的信用卡資訊（遮蔽敏感資訊）
 */

import React from "react";
import { CreditCard } from "lucide-react";

interface SavedCard {
  last_four: string;
  card_type: string;
  card_type_code: number;
  issuer: string;
  saved_at: string;
}

interface CreditCardDisplayProps {
  card: SavedCard;
  className?: string;
}

// 卡別顏色和圖示
const CARD_STYLES: Record<number, { gradient: string; logo: string }> = {
  1: {
    // VISA
    gradient: "from-blue-500 to-blue-700",
    logo: "VISA",
  },
  2: {
    // MasterCard
    gradient: "from-orange-500 to-red-600",
    logo: "Mastercard",
  },
  3: {
    // JCB
    gradient: "from-green-500 to-green-700",
    logo: "JCB",
  },
  4: {
    // Union Pay
    gradient: "from-red-500 to-red-700",
    logo: "UnionPay",
  },
  5: {
    // American Express
    gradient: "from-teal-500 to-teal-700",
    logo: "AMEX",
  },
};

export const CreditCardDisplay: React.FC<CreditCardDisplayProps> = ({
  card,
  className = "",
}) => {
  const style = CARD_STYLES[card.card_type_code] || CARD_STYLES[1];

  return (
    <div className={`relative w-full max-w-sm ${className}`}>
      {/* 信用卡背景 */}
      <div
        className={`
          relative rounded-xl p-6 shadow-xl
          bg-gradient-to-br ${style.gradient}
          text-white
          aspect-[1.586/1]
          transform transition-all hover:scale-105
        `}
      >
        {/* 卡片裝飾圖案 */}
        <div className="absolute top-4 right-4 opacity-20">
          <CreditCard size={48} />
        </div>

        {/* 卡片品牌 Logo */}
        <div className="absolute top-6 left-6">
          <div className="text-xl font-bold tracking-wider">{style.logo}</div>
        </div>

        {/* 卡號（遮蔽） */}
        <div className="absolute bottom-16 left-6 right-6">
          <div className="flex items-center gap-2 font-mono text-lg tracking-wider">
            <span>••••</span>
            <span>••••</span>
            <span>••••</span>
            <span className="font-bold">{card.last_four}</span>
          </div>
        </div>

        {/* 發卡銀行 */}
        <div className="absolute bottom-6 left-6">
          <div className="text-xs opacity-80">發卡銀行</div>
          <div className="text-sm font-medium">{card.issuer || "未知銀行"}</div>
        </div>

        {/* 卡片類型 */}
        <div className="absolute bottom-6 right-6 text-right">
          <div className="text-xs opacity-80">卡別</div>
          <div className="text-sm font-medium">{card.card_type}</div>
        </div>
      </div>

      {/* 儲存時間 */}
      {card.saved_at && (
        <div className="mt-2 text-xs text-gray-500 text-center">
          綁定於{" "}
          {new Date(card.saved_at).toLocaleDateString("zh-TW", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
          })}
        </div>
      )}
    </div>
  );
};

/**
 * 簡化版信用卡顯示（用於列表）
 */
export const CreditCardBadge: React.FC<{ card: SavedCard }> = ({ card }) => {
  const style = CARD_STYLES[card.card_type_code] || CARD_STYLES[1];

  return (
    <div
      className={`
      inline-flex items-center gap-2 px-3 py-2 rounded-lg
      bg-gradient-to-r ${style.gradient}
      text-white text-sm font-medium
    `}
    >
      <CreditCard size={16} />
      <span>{card.card_type}</span>
      <span className="font-mono">•••• {card.last_four}</span>
    </div>
  );
};
