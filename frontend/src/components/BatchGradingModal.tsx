import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { Loader2, Pause, X } from "lucide-react";

interface BatchGradingResult {
  student_id: number;
  student_name: string;
  total_score: number;
  missing_items_count: number;
  avg_pronunciation: number;
  avg_accuracy: number;
  avg_fluency: number;
  avg_completeness: number;
  status: "GRADED" | "RETURNED";
}

interface BatchGradingResponse {
  total_students: number;
  results: BatchGradingResult[];
}

interface BatchGradingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  assignmentId: number;
  classroomId: number;
  onComplete?: () => void;
}

export default function BatchGradingModal({
  open,
  onOpenChange,
  assignmentId,
  classroomId,
  onComplete,
}: BatchGradingModalProps) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<{
    current: number;
    total: number;
  } | null>(null);
  const [results, setResults] = useState<BatchGradingResult[] | null>(null);
  const [returnForCorrection, setReturnForCorrection] = useState<
    Record<number, boolean>
  >({});

  useEffect(() => {
    if (open) {
      // Reset state when modal opens
      setResults(null);
      setProgress(null);
      setReturnForCorrection({});
      // Automatically start grading
      handleStartGrading();
    }
  }, [open]);

  const handleStartGrading = async () => {
    setLoading(true);
    setProgress({ current: 0, total: 0 });

    try {
      const response = await apiClient.post<BatchGradingResponse>(
        `/api/teachers/assignments/${assignmentId}/batch-grade`,
        {
          classroom_id: classroomId,
          return_for_correction: {},
        },
      );

      setResults(response.results);
      setProgress({
        current: response.total_students,
        total: response.total_students,
      });

      toast.success(
        t("batchGrading.messages.success", {
          count: response.total_students,
        }),
      );
    } catch (error) {
      console.error("Batch grading failed:", error);
      toast.error(t("batchGrading.messages.error"));
      onOpenChange(false);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleReturn = (studentId: number) => {
    setReturnForCorrection((prev) => ({
      ...prev,
      [studentId]: !prev[studentId],
    }));
  };

  const handleClose = async () => {
    // If there are students marked for return, update their status
    const studentsToReturn = Object.entries(returnForCorrection)
      .filter(([, shouldReturn]) => shouldReturn)
      .map(([id]) => parseInt(id));

    if (studentsToReturn.length > 0) {
      try {
        // Call API to update status to RETURNED for selected students
        await apiClient.post(
          `/api/teachers/assignments/${assignmentId}/batch-grade`,
          {
            classroom_id: classroomId,
            return_for_correction: returnForCorrection,
          },
        );
        toast.success(
          t("batchGrading.messages.returnSuccess", {
            count: studentsToReturn.length,
          }),
        );
      } catch (error) {
        console.error("Failed to update return status:", error);
        toast.error(t("batchGrading.messages.returnError"));
      }
    }

    onComplete?.();
    onOpenChange(false);
  };

  const calculateAverageScores = () => {
    if (!results || results.length === 0) {
      return {
        avgAccuracy: 0,
        avgFluency: 0,
        avgPronunciation: 0,
        avgCompleteness: 0,
      };
    }

    return {
      avgAccuracy:
        results.reduce((sum, r) => sum + r.avg_accuracy, 0) / results.length,
      avgFluency:
        results.reduce((sum, r) => sum + r.avg_fluency, 0) / results.length,
      avgPronunciation:
        results.reduce((sum, r) => sum + r.avg_pronunciation, 0) /
        results.length,
      avgCompleteness:
        results.reduce((sum, r) => sum + r.avg_completeness, 0) /
        results.length,
    };
  };

  const averages = calculateAverageScores();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">
            {t("batchGrading.title")}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Progress Section */}
          {loading && progress && (
            <div className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
              <span className="font-medium text-blue-900 dark:text-blue-300">
                {t("batchGrading.progress", {
                  current: progress.current,
                  total: progress.total,
                })}
              </span>
            </div>
          )}

          {/* Results Section */}
          {results && (
            <>
              {/* Average Scores */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {t("batchGrading.averageAccuracy")}
                  </span>
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {averages.avgAccuracy.toFixed(1)}
                  </div>
                </div>
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {t("batchGrading.averageFluency")}
                  </span>
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {averages.avgFluency.toFixed(1)}
                  </div>
                </div>
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {t("batchGrading.averagePronunciation")}
                  </span>
                  <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {averages.avgPronunciation.toFixed(1)}
                  </div>
                </div>
                <div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {t("batchGrading.averageCompleteness")}
                  </span>
                  <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    {averages.avgCompleteness.toFixed(1)}
                  </div>
                </div>
              </div>

              {/* Results Table */}
              <div className="border dark:border-gray-700 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.studentName")}
                      </th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.totalScore")}
                      </th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.missingItems")}
                      </th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.returnForCorrection")}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((result) => (
                      <tr
                        key={result.student_id}
                        className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                      >
                        <td className="px-4 py-3 text-sm dark:text-gray-300">
                          {result.student_name}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span
                            className={`font-bold ${
                              result.total_score >= 80
                                ? "text-green-600 dark:text-green-400"
                                : "text-red-600 dark:text-red-400"
                            }`}
                          >
                            {result.total_score.toFixed(1)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center text-sm dark:text-gray-300">
                          {result.missing_items_count > 0 ? (
                            <span className="text-red-600 dark:text-red-400 font-medium">
                              {result.missing_items_count}
                            </span>
                          ) : (
                            <span className="text-green-600 dark:text-green-400">
                              0
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex justify-center">
                            <Checkbox
                              checked={returnForCorrection[result.student_id]}
                              onCheckedChange={() =>
                                handleToggleReturn(result.student_id)
                              }
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>

        <DialogFooter className="flex gap-2">
          {loading ? (
            <Button variant="outline" disabled>
              <Pause className="h-4 w-4 mr-2" />
              {t("batchGrading.pause")}
            </Button>
          ) : (
            <Button variant="outline" onClick={handleClose}>
              <X className="h-4 w-4 mr-2" />
              {t("batchGrading.close")}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
