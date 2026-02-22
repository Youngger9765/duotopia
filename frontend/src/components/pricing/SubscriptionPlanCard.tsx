import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, CheckCircle, Star, Users, CreditCard } from "lucide-react";
import { useTranslation } from "react-i18next";

export interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  monthlyPrice: number;
  pointsPerMonth: number;
  pointsLabel?: string; // override default "X 點/月" display
  studentCapacity: string;
  features: string[];
  popular?: boolean;
}

interface SubscriptionPlanCardProps {
  plan: SubscriptionPlan;
  onSelect?: (plan: SubscriptionPlan) => void;
  disabled?: boolean;
  disabledText?: string;
  ctaText: string;
  isCurrent?: boolean;
}

export function SubscriptionPlanCard({
  plan,
  onSelect,
  disabled,
  disabledText,
  ctaText,
  isCurrent,
}: SubscriptionPlanCardProps) {
  const { t } = useTranslation();

  const hasGradientBorder = isCurrent || (plan.popular && !isCurrent);

  const cardClassName = [
    "relative p-5 hover:shadow-xl transition-all duration-300 flex flex-col",
    hasGradientBorder ? "border-2 border-transparent" : "",
    plan.popular && !isCurrent ? "scale-105" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const blueGradient =
    "linear-gradient(145deg, #101f6b, #204dc0, #5b8def, #204dc0, #101f6b)";
  const goldGradient =
    "linear-gradient(145deg, #b8860b, #daa520, #ffd700, #daa520, #b8860b)";

  const cardStyle = isCurrent
    ? {
        backgroundImage: `linear-gradient(white, white), ${blueGradient}`,
        backgroundOrigin: "border-box" as const,
        backgroundClip: "padding-box, border-box",
        boxShadow: "0 0 18px rgba(32,77,192,0.35)",
      }
    : plan.popular
      ? {
          backgroundImage: `linear-gradient(white, white), ${goldGradient}`,
          backgroundOrigin: "border-box" as const,
          backgroundClip: "padding-box, border-box",
          boxShadow: "0 0 18px rgba(218,165,32,0.35)",
        }
      : undefined;

  return (
    <Card className={cardClassName} style={cardStyle}>
      {isCurrent && (
        <Badge
          className="absolute -top-3 left-1/2 transform -translate-x-1/2 text-white"
          style={{ backgroundColor: "#204dc0" }}
        >
          <CheckCircle className="w-3 h-3 mr-1" />
          {t("pricing.actions.currentPlan")}
        </Badge>
      )}
      {plan.popular && !isCurrent && (
        <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-amber-500 text-white">
          <Star className="w-3 h-3 mr-1" />
          {t("pricing.card.popular")}
        </Badge>
      )}

      <div className="text-center mb-4">
        <h3 className="text-xl font-bold text-gray-900 mb-1">{plan.name}</h3>
        <p className="text-sm text-gray-600">{plan.description}</p>
        <div className="flex items-center justify-center mt-2 text-sm text-gray-500">
          <Users className="w-4 h-4 mr-1.5" />
          <span>{plan.studentCapacity}</span>
        </div>
      </div>

      {/* Price Block */}
      <div className="mb-5">
        <div className="bg-blue-50 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">{t("pricing.billing.monthly")}</span>
            <div className="text-right">
              <span className="text-2xl font-bold text-gray-900">
                NT$ {plan.monthlyPrice}
              </span>
              <span className="text-gray-600 ml-1">{t("pricing.billing.perMonth")}</span>
            </div>
          </div>
          <div className="mt-1 text-sm text-blue-700 font-medium">
            {plan.pointsLabel || `${plan.pointsPerMonth.toLocaleString()} ${t("pricing.billing.pointsPerMonth")}`}
          </div>
        </div>
      </div>

      <ul className="space-y-2 mb-5">
        {plan.features.map((feature, idx) => (
          <li key={idx} className="flex items-start">
            <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span className="text-gray-700">{feature}</span>
          </li>
        ))}
      </ul>

      {/* Spacer to push button to bottom */}
      <div className="flex-1" />

      <Button
        onClick={() => onSelect?.(plan)}
        disabled={disabled}
        className={`w-full ${
          disabled
            ? "bg-gray-300 cursor-not-allowed text-gray-500"
            : plan.popular
              ? "bg-amber-500 hover:bg-amber-600 text-white"
              : "bg-gray-800 hover:bg-gray-900 text-white"
        }`}
      >
        <CreditCard className="mr-2 h-4 w-4" />
        {disabled ? disabledText : ctaText}
      </Button>
    </Card>
  );
}
