import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { PointsBalance } from "../types/points";
import { apiClient } from "../lib/api";

interface Props {
  organizationId: string;
}

export const OrganizationPointsBalance: React.FC<Props> = ({
  organizationId,
}) => {
  const { t } = useTranslation();
  const [balance, setBalance] = useState<PointsBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const data = await apiClient.get<PointsBalance>(
          `/api/organizations/${organizationId}/points`,
        );
        setBalance(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchBalance();
  }, [organizationId]);

  if (loading) {
    return (
      <div className="animate-pulse">{t("organizationPoints.loading")}</div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600">
        {t("organizationPoints.error", { error })}
      </div>
    );
  }

  if (!balance) {
    return null;
  }

  const percentageUsed =
    balance.total_points > 0
      ? (balance.used_points / balance.total_points) * 100
      : 0;
  const isLow =
    balance.total_points > 0 &&
    balance.remaining_points < balance.total_points * 0.2;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">
        {t("organizationPoints.title")}
      </h3>

      {/* Balance Display */}
      <div className="mb-4">
        <div className="flex justify-between items-baseline mb-2">
          <span className="text-3xl font-bold">
            {balance.remaining_points.toLocaleString()}
          </span>
          <span className="text-gray-500">
            / {balance.total_points.toLocaleString()}{" "}
            {t("organizationPoints.total")}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full ${
              isLow ? "bg-red-600" : "bg-blue-600"
            }`}
            style={{ width: `${100 - percentageUsed}%` }}
          />
        </div>
      </div>

      {/* Low Balance Warning */}
      {isLow && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
          <p className="text-yellow-800 text-sm">
            {t("organizationPoints.lowWarning")}
          </p>
        </div>
      )}

      {/* Usage Stats */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-500">{t("organizationPoints.used")}</p>
          <p className="font-semibold">
            {balance.used_points.toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-gray-500">{t("organizationPoints.available")}</p>
          <p className="font-semibold">
            {balance.remaining_points.toLocaleString()}
          </p>
        </div>
      </div>

      {balance.last_points_update && (
        <p className="text-xs text-gray-400 mt-4">
          {t("organizationPoints.lastUpdated")}:{" "}
          {new Date(balance.last_points_update).toLocaleString()}
        </p>
      )}
    </div>
  );
};
