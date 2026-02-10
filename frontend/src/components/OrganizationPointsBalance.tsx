import React, { useEffect, useState } from "react";
import { PointsBalance } from "../types/points";
import { API_URL } from "../config/api";
import { useTeacherAuthStore } from "../stores/teacherAuthStore";

interface Props {
  organizationId: string;
}

export const OrganizationPointsBalance: React.FC<Props> = ({
  organizationId,
}) => {
  const token = useTeacherAuthStore((state) => state.token);
  const [balance, setBalance] = useState<PointsBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const response = await fetch(
          `${API_URL}/api/organizations/${organizationId}/points`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          },
        );

        if (!response.ok) {
          throw new Error("Failed to fetch points balance");
        }

        const data = await response.json();
        setBalance(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchBalance();
  }, [organizationId, token]);

  if (loading) {
    return <div className="animate-pulse">Loading points balance...</div>;
  }

  if (error) {
    return <div className="text-red-600">Error: {error}</div>;
  }

  if (!balance) {
    return null;
  }

  const percentageUsed = (balance.used_points / balance.total_points) * 100;
  const isLow = balance.remaining_points < balance.total_points * 0.2;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">AI Usage Points</h3>

      {/* Balance Display */}
      <div className="mb-4">
        <div className="flex justify-between items-baseline mb-2">
          <span className="text-3xl font-bold">
            {balance.remaining_points.toLocaleString()}
          </span>
          <span className="text-gray-500">
            / {balance.total_points.toLocaleString()} total
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
            ⚠️ Points running low. Contact admin to add more points.
          </p>
        </div>
      )}

      {/* Usage Stats */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-500">Used</p>
          <p className="font-semibold">
            {balance.used_points.toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-gray-500">Available</p>
          <p className="font-semibold">
            {balance.remaining_points.toLocaleString()}
          </p>
        </div>
      </div>

      {balance.last_points_update && (
        <p className="text-xs text-gray-400 mt-4">
          Last updated: {new Date(balance.last_points_update).toLocaleString()}
        </p>
      )}
    </div>
  );
};
