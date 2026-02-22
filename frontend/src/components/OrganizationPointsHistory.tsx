import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { PointsHistory, PointsLogItem } from "../types/points";
import { apiClient } from "../lib/api";

interface Props {
  organizationId: string;
}

export const OrganizationPointsHistory: React.FC<Props> = ({
  organizationId,
}) => {
  const { t } = useTranslation();
  const [history, setHistory] = useState<PointsHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const limit = 20;

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        setError(null);
        const offset = page * limit;

        const data = await apiClient.get<PointsHistory>(
          `/api/organizations/${organizationId}/points/history?limit=${limit}&offset=${offset}`,
        );
        setHistory(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [organizationId, page]);

  if (loading) {
    return (
      <div className="animate-pulse">
        {t("organizationPoints.loadingHistory")}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600">
        {t("organizationPoints.error", { error })}
      </div>
    );
  }

  if (!history || history.items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">
          {t("organizationPoints.history.title")}
        </h3>
        <p className="text-gray-500">{t("organizationPoints.history.empty")}</p>
      </div>
    );
  }

  const totalPages = Math.ceil(history.total / limit);

  const getFeatureTypeBadge = (featureType: string | null) => {
    const badges: Record<string, string> = {
      ai_generation: "bg-purple-100 text-purple-800",
      translation: "bg-blue-100 text-blue-800",
      default: "bg-gray-100 text-gray-800",
    };

    return badges[featureType || "default"] || badges.default;
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold">
          {t("organizationPoints.history.title")}
        </h3>
        <p className="text-sm text-gray-500">
          {t("organizationPoints.history.totalEntries", {
            count: history.total,
          })}
        </p>
      </div>

      {/* History Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t("organizationPoints.history.date")}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t("organizationPoints.history.user")}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t("organizationPoints.history.feature")}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t("organizationPoints.history.description")}
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t("organizationPoints.history.points")}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {history.items.map((item: PointsLogItem) => (
              <tr key={item.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(item.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {item.teacher_name || t("organizationPoints.history.unknown")}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getFeatureTypeBadge(
                      item.feature_type,
                    )}`}
                  >
                    {item.feature_type || "N/A"}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {item.description || "-"}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-gray-900">
                  -{item.points_used.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-gray-50 px-6 py-3 flex items-center justify-between border-t">
          <div className="text-sm text-gray-700">
            {t("organizationPoints.history.showing", {
              from: page * limit + 1,
              to: Math.min((page + 1) * limit, history.total),
              total: history.total,
            })}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 0}
              className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              {t("organizationPoints.history.previous")}
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page >= totalPages - 1}
              className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              {t("organizationPoints.history.next")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
