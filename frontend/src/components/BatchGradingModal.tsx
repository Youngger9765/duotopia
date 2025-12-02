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
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { Loader2, CheckCircle } from "lucide-react";

// Teacher's decision for each student
type TeacherDecision = "RETURNED" | "GRADED" | null;

interface BatchGradingResult {
  student_id: number;
  student_name: string;
  total_score: number;
  missing_items: number;
  total_items: number;
  completed_items: number;
  avg_pronunciation: number;
  avg_accuracy: number;
  avg_fluency: number;
  avg_completeness: number;
  feedback?: string;
  status: string;
}

interface BatchGradingResponse {
  total_students: number;
  results: BatchGradingResult[];
}

interface BatchGradeFinalizeResponse {
  returned_count: number;
  graded_count: number;
  unchanged_count: number;
  total_count: number;
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
  const [teacherDecisions, setTeacherDecisions] = useState<
    Record<number, TeacherDecision>
  >({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      // Reset state when modal opens
      setResults(null);
      setProgress(null);
      setTeacherDecisions({});
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
        },
      );

      setResults(response.results);
      setProgress({
        current: response.total_students,
        total: response.total_students,
      });

      // Initialize all students' decisions to null (pending)
      const initialDecisions: Record<number, TeacherDecision> = {};
      response.results.forEach((r) => {
        initialDecisions[r.student_id] = null;
      });
      setTeacherDecisions(initialDecisions);

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

  const handleSubmitSingleStudent = async (studentId: number) => {
    const decision = teacherDecisions[studentId];
    if (!decision) {
      toast.warning(t("batchGrading.selectDecisionFirst"));
      return;
    }

    setIsSubmitting(true);
    try {
      await apiClient.post<BatchGradeFinalizeResponse>(
        `/api/teachers/assignments/${assignmentId}/finalize-batch-grade`,
        {
          classroom_id: classroomId,
          teacher_decisions: { [studentId]: decision },
        },
      );

      const studentName =
        results?.find((r) => r.student_id === studentId)?.student_name || "";
      toast.success(
        t("batchGrading.singleSubmitSuccess", { name: studentName }),
      );

      // Remove student from list
      setResults(
        (prev) => prev?.filter((r) => r.student_id !== studentId) || null,
      );
    } catch (error) {
      console.error("Error submitting single student:", error);
      toast.error(t("batchGrading.errorDescription"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitAll = async () => {
    setIsSubmitting(true);

    try {
      const response = await apiClient.post<BatchGradeFinalizeResponse>(
        `/api/teachers/assignments/${assignmentId}/finalize-batch-grade`,
        {
          classroom_id: classroomId,
          teacher_decisions: teacherDecisions,
        },
      );

      toast.success(
        t("batchGrading.allSubmitSuccess", {
          graded: response.graded_count,
          returned: response.returned_count,
          unchanged: response.unchanged_count,
        }),
      );

      onComplete?.();
      onOpenChange(false);
    } catch (error) {
      console.error("Error finalizing grading:", error);
      toast.error(t("batchGrading.errorDescription"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectAll = (decision: TeacherDecision) => {
    const allDecisions: Record<number, TeacherDecision> = {};
    results?.forEach((r) => {
      allDecisions[r.student_id] = decision;
    });
    setTeacherDecisions(allDecisions);
  };

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
              {/* Select All Controls */}
              <div className="flex gap-3 mb-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleSelectAll("GRADED")}
                >
                  {t("batchGrading.selectAllGraded")}
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleSelectAll("RETURNED")}
                >
                  {t("batchGrading.selectAllReturned")}
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleSelectAll(null)}
                >
                  {t("batchGrading.clearAll")}
                </Button>
              </div>

              {/* Results Table */}
              <div className="border dark:border-gray-700 rounded-lg overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-3 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.studentName")}
                      </th>
                      <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.pronunciation")}
                      </th>
                      <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.accuracy")}
                      </th>
                      <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.fluency")}
                      </th>
                      <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.completeness")}
                      </th>
                      <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.totalScore")}
                      </th>
                      <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.missingItems")}
                      </th>
                      <th className="px-3 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.decision")}
                      </th>
                      <th className="px-2 py-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("batchGrading.action")}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((result) => (
                      <tr
                        key={result.student_id}
                        className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                      >
                        <td className="px-3 py-3 text-sm dark:text-gray-300">
                          {result.student_name}
                        </td>
                        <td className="px-2 py-3 text-center text-sm">
                          <span className="text-blue-600 dark:text-blue-400">
                            {result.avg_pronunciation.toFixed(0)}
                          </span>
                        </td>
                        <td className="px-2 py-3 text-center text-sm">
                          <span className="text-purple-600 dark:text-purple-400">
                            {result.avg_accuracy.toFixed(0)}
                          </span>
                        </td>
                        <td className="px-2 py-3 text-center text-sm">
                          <span className="text-teal-600 dark:text-teal-400">
                            {result.avg_fluency.toFixed(0)}
                          </span>
                        </td>
                        <td className="px-2 py-3 text-center text-sm">
                          <span className="text-indigo-600 dark:text-indigo-400">
                            {result.avg_completeness.toFixed(0)}
                          </span>
                        </td>
                        <td className="px-2 py-3 text-center">
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
                        <td className="px-2 py-3 text-center text-sm dark:text-gray-300">
                          {result.missing_items > 0 ? (
                            <span className="text-red-600 dark:text-red-400 font-medium">
                              {result.missing_items}
                            </span>
                          ) : (
                            <span className="text-green-600 dark:text-green-400">
                              0
                            </span>
                          )}
                        </td>

                        {/* Radio Button Decision Column */}
                        <td className="px-4 py-3">
                          <div className="flex flex-col gap-2">
                            <label className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="radio"
                                name={`decision-${result.student_id}`}
                                value="GRADED"
                                checked={
                                  teacherDecisions[result.student_id] ===
                                  "GRADED"
                                }
                                onChange={() =>
                                  setTeacherDecisions((prev) => ({
                                    ...prev,
                                    [result.student_id]: "GRADED",
                                  }))
                                }
                                className="h-4 w-4"
                              />
                              <span className="text-sm text-green-600 dark:text-green-400">
                                ✓ {t("batchGrading.decisionGraded")}
                              </span>
                            </label>

                            <label className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="radio"
                                name={`decision-${result.student_id}`}
                                value="RETURNED"
                                checked={
                                  teacherDecisions[result.student_id] ===
                                  "RETURNED"
                                }
                                onChange={() =>
                                  setTeacherDecisions((prev) => ({
                                    ...prev,
                                    [result.student_id]: "RETURNED",
                                  }))
                                }
                                className="h-4 w-4"
                              />
                              <span className="text-sm text-red-600 dark:text-red-400">
                                ↩ {t("batchGrading.decisionReturned")}
                              </span>
                            </label>

                            <label className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="radio"
                                name={`decision-${result.student_id}`}
                                value=""
                                checked={
                                  teacherDecisions[result.student_id] === null
                                }
                                onChange={() =>
                                  setTeacherDecisions((prev) => ({
                                    ...prev,
                                    [result.student_id]: null,
                                  }))
                                }
                                className="h-4 w-4"
                              />
                              <span className="text-sm text-gray-500 dark:text-gray-400">
                                ⏸ {t("batchGrading.decisionPending")}
                              </span>
                            </label>
                          </div>
                        </td>

                        {/* Single Submit Button */}
                        <td className="px-4 py-3 text-center">
                          <Button
                            size="sm"
                            onClick={() =>
                              handleSubmitSingleStudent(result.student_id)
                            }
                            disabled={
                              !teacherDecisions[result.student_id] ||
                              isSubmitting
                            }
                          >
                            {t("batchGrading.submitSingle")}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>

        <DialogFooter className="gap-2 mt-6">
          <div className="flex w-full justify-end items-center">
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                {t("common.cancel")}
              </Button>
              <Button
                onClick={handleSubmitAll}
                disabled={isSubmitting || loading}
                className="min-w-[100px]"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t("batchGrading.processing")}
                  </>
                ) : (
                  <>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    {t("batchGrading.submitAll")}
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
