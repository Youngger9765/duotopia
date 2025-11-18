import { useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Upload,
  Download,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
  X,
} from "lucide-react";
import Papa from "papaparse";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { Classroom } from "@/types";
import { useTranslation } from "react-i18next";

interface StudentImportDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  classrooms: Classroom[];
}

interface ImportStudent {
  name: string;
  birthdate: string;
  className?: string;
  isValid: boolean;
  errors: string[];
}

export function StudentImportDialog({
  open,
  onClose,
  onSuccess,
  classrooms,
}: StudentImportDialogProps) {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);
  const [preview, setPreview] = useState<ImportStudent[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [successCount, setSuccessCount] = useState(0);
  const [failCount, setFailCount] = useState(0);
  const [missingClassrooms, setMissingClassrooms] = useState<string[]>([]);
  const [duplicateAction, setDuplicateAction] = useState<
    "skip" | "update" | "add_suffix"
  >("skip");

  // 下載範本
  const downloadTemplate = () => {
    const template = [
      [
        t("studentImportDialog.template.columnName"),
        t("studentImportDialog.template.columnClassroom"),
        t("studentImportDialog.template.columnBirthdate"),
      ],
      [
        t("studentImportDialog.template.sampleName1"),
        t("studentImportDialog.template.sampleClassroom1"),
        "2012-01-01",
      ],
      [
        t("studentImportDialog.template.sampleName2"),
        t("studentImportDialog.template.sampleClassroom1"),
        "2012-02-15",
      ],
      [
        t("studentImportDialog.template.sampleName3"),
        t("studentImportDialog.template.sampleClassroom2"),
        "2012-03-20",
      ],
    ];

    const ws = XLSX.utils.aoa_to_sheet(template);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(
      wb,
      ws,
      t("studentImportDialog.template.sheetName"),
    );

    // 設定欄寬
    ws["!cols"] = [
      { wch: 15 }, // 學生姓名
      { wch: 10 }, // 班級
      { wch: 12 }, // 生日
    ];

    const excelBuffer = XLSX.write(wb, { bookType: "xlsx", type: "array" });
    const blob = new Blob([excelBuffer], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    saveAs(blob, t("studentImportDialog.template.fileName"));

    toast.success(t("studentImportDialog.success.templateDownloaded"));
  };

  // 解析檔案
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const fileType = file.name.split(".").pop()?.toLowerCase();

    if (fileType === "csv") {
      Papa.parse(file, {
        complete: (results) => {
          processData(results.data as string[][]);
        },
        encoding: "UTF-8",
        skipEmptyLines: true,
      });
    } else if (fileType === "xlsx" || fileType === "xls") {
      const reader = new FileReader();
      reader.onload = (e) => {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: "array" });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(firstSheet, {
          header: 1,
        }) as string[][];
        processData(jsonData);
      };
      reader.readAsArrayBuffer(file);
    } else {
      toast.error(t("studentImportDialog.errors.invalidFileType"));
    }
  };

  // 處理資料
  const processData = (data: string[][]) => {
    if (data.length < 2) {
      toast.error(t("studentImportDialog.errors.noData"));
      return;
    }

    // 解析標題列（支援中文和英文）
    const headers = data[0].map((h) => h?.toLowerCase().trim() || "");

    // 尋找欄位索引
    const nameIndex = headers.findIndex(
      (h) => h.includes("姓名") || h.includes("name") || h.includes("學生"),
    );
    const classIndex = headers.findIndex(
      (h) =>
        h.includes("班級") || h.includes("class") || h.includes("classroom"),
    );
    const birthIndex = headers.findIndex(
      (h) => h.includes("生日") || h.includes("birth") || h.includes("date"),
    );

    if (nameIndex === -1) {
      toast.error(t("studentImportDialog.errors.noName"));
      return;
    }

    const students: ImportStudent[] = [];
    const importErrors: string[] = [];
    const uniqueNewClassrooms = new Set<string>();

    // 處理每一列資料（跳過標題列）
    for (let i = 1; i < data.length; i++) {
      const row = data[i];
      if (!row || row.length === 0) continue;

      const name = String(row[nameIndex] || "").trim();
      const className =
        classIndex !== -1 ? String(row[classIndex] || "").trim() : undefined;
      const birthdate =
        birthIndex !== -1 ? String(row[birthIndex] || "").trim() : "";

      if (!name) continue;

      const studentErrors: string[] = [];

      // 驗證姓名
      if (name.length < 2) {
        studentErrors.push(t("studentImportDialog.errors.nameTooShort"));
      }

      // 驗證生日格式
      let formattedBirthdate = "";
      if (birthdate) {
        // 移除空白
        const cleanDate = birthdate.trim();

        // 1. 檢查 YYYYMMDD 格式 (20120101)
        if (/^\d{8}$/.test(cleanDate)) {
          const year = cleanDate.slice(0, 4);
          const month = cleanDate.slice(4, 6);
          const day = cleanDate.slice(6, 8);
          formattedBirthdate = `${year}-${month}-${day}`;
        }
        // 2. 檢查 YYYY-MM-DD 格式 (2012-01-01)
        else if (/^\d{4}-\d{1,2}-\d{1,2}$/.test(cleanDate)) {
          const parts = cleanDate.split("-");
          const year = parts[0];
          const month = parts[1].padStart(2, "0");
          const day = parts[2].padStart(2, "0");
          formattedBirthdate = `${year}-${month}-${day}`;
        }
        // 3. 檢查 YYYY/MM/DD 格式 (2012/01/01)
        else if (/^\d{4}\/\d{1,2}\/\d{1,2}$/.test(cleanDate)) {
          const parts = cleanDate.split("/");
          const year = parts[0];
          const month = parts[1].padStart(2, "0");
          const day = parts[2].padStart(2, "0");
          formattedBirthdate = `${year}-${month}-${day}`;
        }
        // 4. 檢查是否為 Excel 序列號格式（數字）
        else {
          const numericDate = Number(cleanDate);
          if (
            !isNaN(numericDate) &&
            numericDate > 25569 &&
            numericDate < 50000
          ) {
            // Excel 日期序列號轉換（從 1900-01-01 開始）
            const excelDate = new Date((numericDate - 25569) * 86400 * 1000);
            const year = excelDate.getFullYear();
            const month = String(excelDate.getMonth() + 1).padStart(2, "0");
            const day = String(excelDate.getDate()).padStart(2, "0");
            formattedBirthdate = `${year}-${month}-${day}`;
          } else {
            studentErrors.push(
              t("studentImportDialog.errors.invalidBirthdate"),
            );
          }
        }

        // 驗證日期是否合理
        if (formattedBirthdate) {
          const date = new Date(formattedBirthdate);
          const year = parseInt(formattedBirthdate.slice(0, 4));
          if (isNaN(date.getTime()) || year < 2000 || year > 2020) {
            studentErrors.push(
              t("studentImportDialog.errors.unreasonableBirthdate"),
            );
            formattedBirthdate = "";
          }
        }
      }

      // 驗證班級名稱
      if (className) {
        const classExists = classrooms.some((c) => c.name === className);
        if (!classExists) {
          uniqueNewClassrooms.add(className);
          studentErrors.push(
            t("studentImportDialog.errors.classroomNotFound", {
              name: className,
            }),
          );
        }
      }

      students.push({
        name,
        birthdate: formattedBirthdate || "",
        className,
        isValid: studentErrors.length === 0,
        errors: studentErrors,
      });
    }

    if (students.length === 0) {
      toast.error(t("studentImportDialog.errors.noValidData"));
      return;
    }

    // 設定缺少的班級列表
    const missingList = Array.from(uniqueNewClassrooms);
    setMissingClassrooms(missingList);
    setPreview(students);
    setErrors(importErrors);
  };

  // 執行匯入
  const handleImport = async () => {
    const validStudents = preview.filter((s) => s.isValid);

    if (validStudents.length === 0) {
      toast.error(t("studentImportDialog.errors.noValidData"));
      return;
    }

    setImporting(true);

    try {
      // Call backend API to batch import students with duplicate action
      const response = (await apiClient.batchImportStudents(
        validStudents.map((student) => ({
          name: student.name,
          classroom_name: student.className || "",
          birthdate: student.birthdate,
        })),
        duplicateAction,
      )) as {
        success_count?: number;
        error_count?: number;
        errors?: Array<{ row: number; name: string; error: string }>;
      };

      const successCount = response.success_count || 0;
      const errorCount = response.error_count || 0;

      setSuccessCount(successCount);
      setFailCount(errorCount);

      // Handle any errors from the API
      if (response.errors && response.errors.length > 0) {
        const errorMessages = response.errors
          .map(
            (err) =>
              `${t("studentImportDialog.validation.row")}${err.row} - ${err.name}: ${err.error}`,
          )
          .join("\n");
        toast.error(
          t("studentImportDialog.errors.importPartialFailed", {
            errors: errorMessages,
          }),
        );
      }

      if (successCount > 0) {
        toast.success(
          t("studentImportDialog.success.imported", {
            count: successCount,
          }),
        );
        onSuccess(); // 更新父組件的資料
        // 不自動關閉，讓用戶查看結果
      }
    } catch (error) {
      console.error("Import failed:", error);
      toast.error(t("studentImportDialog.errors.importFailed"));
    } finally {
      setImporting(false);
    }
  };

  // 關閉對話框
  const handleClose = () => {
    setPreview([]);
    setErrors([]);
    setSuccessCount(0);
    setFailCount(0);
    setMissingClassrooms([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            {t("studentImportDialog.title")}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* 步驟說明 */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-medium mb-2">
              {t("studentImportDialog.steps.title")}
            </h3>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              <li>{t("studentImportDialog.steps.step1")}</li>
              <li>{t("studentImportDialog.steps.step2")}</li>
              <li>{t("studentImportDialog.steps.step3")}</li>
              <li>{t("studentImportDialog.steps.step4")}</li>
            </ol>
          </div>

          {/* 重複處理選項 */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium mb-2">
              {t("studentImportDialog.duplicateAction.title")}
            </h3>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="duplicateAction"
                  value="skip"
                  checked={duplicateAction === "skip"}
                  onChange={(e) => setDuplicateAction(e.target.value as "skip")}
                  className="text-blue-600"
                />
                <span>{t("studentImportDialog.duplicateAction.skip")}</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="duplicateAction"
                  value="update"
                  checked={duplicateAction === "update"}
                  onChange={(e) =>
                    setDuplicateAction(e.target.value as "update")
                  }
                  className="text-blue-600"
                />
                <span>{t("studentImportDialog.duplicateAction.update")}</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="duplicateAction"
                  value="add_suffix"
                  checked={duplicateAction === "add_suffix"}
                  onChange={(e) =>
                    setDuplicateAction(e.target.value as "add_suffix")
                  }
                  className="text-blue-600"
                />
                <span>
                  {t("studentImportDialog.duplicateAction.addSuffix")}
                </span>
              </label>
            </div>
          </div>

          {/* 操作按鈕 */}
          <div className="flex gap-4">
            <Button
              variant="outline"
              onClick={downloadTemplate}
              className="flex-1"
            >
              <Download className="h-4 w-4 mr-2" />
              {t("studentImportDialog.buttons.downloadTemplate")}
            </Button>

            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              className="flex-1"
              disabled={importing}
            >
              <Upload className="h-4 w-4 mr-2" />
              {t("studentImportDialog.buttons.selectFile")}
            </Button>

            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {/* 錯誤訊息 */}
          {errors.length > 0 && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <ul className="list-disc list-inside">
                  {errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {/* 缺少班級提醒 */}
          {missingClassrooms.length > 0 && (
            <Alert className="border-yellow-200 bg-yellow-50">
              <AlertCircle className="h-4 w-4 text-yellow-600" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-medium text-yellow-800">
                    {t("studentImportDialog.missingClassrooms.title")}
                  </p>
                  <ul className="list-disc list-inside text-sm">
                    {missingClassrooms.map((name, index) => (
                      <li key={index}>{name}</li>
                    ))}
                  </ul>
                  <p className="text-sm text-yellow-700 mt-2">
                    {t("studentImportDialog.missingClassrooms.instruction")}
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open("/teacher/classrooms", "_blank")}
                    className="mt-2"
                  >
                    {t("studentImportDialog.buttons.goToClassrooms")}
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* 預覽資料 */}
          {preview.length > 0 && (
            <div>
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium">
                  {t("studentImportDialog.preview.title")}
                </h3>
                <div className="text-sm text-gray-600">
                  {t("studentImportDialog.preview.valid")}:{" "}
                  {preview.filter((s) => s.isValid).length} /{" "}
                  {t("studentImportDialog.preview.total")}: {preview.length}
                </div>
              </div>

              <div className="border rounded-lg max-h-96 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left">
                        {t("studentImportDialog.preview.status")}
                      </th>
                      <th className="px-4 py-2 text-left">
                        {t("studentImportDialog.preview.name")}
                      </th>
                      <th className="px-4 py-2 text-left">
                        {t("studentImportDialog.preview.classroom")}
                      </th>
                      <th className="px-4 py-2 text-left">
                        {t("studentImportDialog.preview.birthdate")}
                      </th>
                      <th className="px-4 py-2 text-left">
                        {t("studentImportDialog.preview.errors")}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.map((student, index) => (
                      <tr
                        key={index}
                        className={student.isValid ? "" : "bg-red-50"}
                      >
                        <td className="px-4 py-2">
                          {student.isValid ? (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          ) : (
                            <X className="h-4 w-4 text-red-500" />
                          )}
                        </td>
                        <td className="px-4 py-2">{student.name}</td>
                        <td className="px-4 py-2">
                          {student.className || "-"}
                        </td>
                        <td className="px-4 py-2">
                          {student.birthdate || "-"}
                        </td>
                        <td className="px-4 py-2 text-red-600">
                          {student.errors.join(", ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 匯入結果 */}
          {(successCount > 0 || failCount > 0) && (
            <div className="space-y-3">
              <Alert
                className={
                  successCount > 0
                    ? "border-green-200 bg-green-50"
                    : "border-red-200 bg-red-50"
                }
              >
                {successCount > 0 ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-600" />
                )}
                <AlertDescription>
                  <div className="space-y-2">
                    <p className="font-semibold text-lg">
                      {t("studentImportDialog.result.title")}
                    </p>
                    <div className="flex gap-4">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        <span>
                          {t("studentImportDialog.result.success", {
                            count: successCount,
                          })}
                        </span>
                      </div>
                      {failCount > 0 && (
                        <div className="flex items-center gap-2">
                          <X className="h-4 w-4 text-red-600" />
                          <span>
                            {t("studentImportDialog.result.failed", {
                              count: failCount,
                            })}
                          </span>
                        </div>
                      )}
                    </div>
                    {duplicateAction === "skip" && successCount > 0 && (
                      <p className="text-sm text-gray-600">
                        {t("studentImportDialog.result.skipped")}
                      </p>
                    )}
                    {duplicateAction === "update" && successCount > 0 && (
                      <p className="text-sm text-gray-600">
                        {t("studentImportDialog.result.updated")}
                      </p>
                    )}
                    {duplicateAction === "add_suffix" && successCount > 0 && (
                      <p className="text-sm text-gray-600">
                        {t("studentImportDialog.result.numbered")}
                      </p>
                    )}
                  </div>
                </AlertDescription>
              </Alert>

              {/* 下一步提示 */}
              <Alert className="border-blue-200 bg-blue-50">
                <AlertCircle className="h-4 w-4 text-blue-600" />
                <AlertDescription>
                  <div className="space-y-2">
                    <p className="font-medium">
                      {t("studentImportDialog.nextSteps.title")}
                    </p>
                    <ul className="list-disc list-inside text-sm space-y-1">
                      <li>{t("studentImportDialog.nextSteps.step1")}</li>
                      <li>{t("studentImportDialog.nextSteps.step2")}</li>
                      <li>{t("studentImportDialog.nextSteps.step3")}</li>
                    </ul>
                  </div>
                </AlertDescription>
              </Alert>
            </div>
          )}

          {/* 操作按鈕 */}
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={importing}
            >
              {t("studentImportDialog.buttons.cancel")}
            </Button>
            {successCount > 0 || failCount > 0 ? (
              <Button onClick={handleClose} variant="default">
                {t("studentImportDialog.buttons.done")}
              </Button>
            ) : (
              <Button
                onClick={handleImport}
                disabled={
                  preview.filter((s) => s.isValid).length === 0 || importing
                }
              >
                {importing
                  ? t("studentImportDialog.buttons.importing")
                  : t("studentImportDialog.buttons.import", {
                      count: preview.filter((s) => s.isValid).length,
                    })}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
