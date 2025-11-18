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
      ["學生姓名", "班級", "生日"],
      ["王小明", "A班", "2012-01-01"],
      ["李小華", "A班", "2012-02-15"],
      ["張小美", "B班", "2012-03-20"],
    ];

    const ws = XLSX.utils.aoa_to_sheet(template);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "學生名單");

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
    saveAs(blob, "學生批次匯入範本.xlsx");

    toast.success(t("dialogs.studentImportDialog.success.templateDownloaded"));
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
      toast.error(t("dialogs.studentImportDialog.errors.invalidFileType"));
    }
  };

  // 處理資料
  const processData = (data: string[][]) => {
    if (data.length < 2) {
      toast.error("檔案沒有資料");
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
      toast.error("找不到「姓名」欄位");
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
        studentErrors.push("姓名太短");
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
              "生日格式錯誤（請使用 YYYYMMDD、YYYY-MM-DD 或 YYYY/MM/DD）",
            );
          }
        }

        // 驗證日期是否合理
        if (formattedBirthdate) {
          const date = new Date(formattedBirthdate);
          const year = parseInt(formattedBirthdate.slice(0, 4));
          if (isNaN(date.getTime()) || year < 2000 || year > 2020) {
            studentErrors.push("生日日期不合理（應為 2000-2020 年）");
            formattedBirthdate = "";
          }
        }
      }

      // 驗證班級名稱
      if (className) {
        const classExists = classrooms.some((c) => c.name === className);
        if (!classExists) {
          uniqueNewClassrooms.add(className);
          studentErrors.push(`班級「${className}」不存在`);
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
      toast.error("沒有找到有效的學生資料");
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
      toast.error("沒有有效的學生資料可以匯入");
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
          .map((err) => `第${err.row}行 - ${err.name}: ${err.error}`)
          .join("\n");
        toast.error(`部分學生匯入失敗:\n${errorMessages}`);
      }

      if (successCount > 0) {
        toast.success(
          t("dialogs.studentImportDialog.success.imported", {
            count: successCount,
          }),
        );
        onSuccess(); // 更新父組件的資料
        // 不自動關閉，讓用戶查看結果
      }
    } catch (error) {
      console.error("Import failed:", error);
      toast.error(t("dialogs.studentImportDialog.errors.importFailed"));
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
            批次匯入學生
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* 步驟說明 */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-medium mb-2">匯入步驟：</h3>
            <ol className="list-decimal list-inside space-y-1 text-sm">
              <li>下載範本檔案</li>
              <li>填寫學生資料（姓名、班級、生日）</li>
              <li>上傳填寫好的檔案</li>
              <li>確認資料無誤後執行匯入</li>
            </ol>
          </div>

          {/* 重複處理選項 */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium mb-2">重複學生處理方式：</h3>
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
                <span>跳過重複（預設）- 保留現有學生，跳過重複的資料</span>
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
                <span>
                  更新資料 - 用新資料更新現有學生的生日（如密碼未改過也會更新）
                </span>
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
                <span>加上編號 - 在重複的姓名後加上編號（如：王小明-2）</span>
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
              下載範本
            </Button>

            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              className="flex-1"
              disabled={importing}
            >
              <Upload className="h-4 w-4 mr-2" />
              選擇檔案
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
                    發現以下班級尚未建立：
                  </p>
                  <ul className="list-disc list-inside text-sm">
                    {missingClassrooms.map((name, index) => (
                      <li key={index}>{name}</li>
                    ))}
                  </ul>
                  <p className="text-sm text-yellow-700 mt-2">
                    請先到「我的班級」頁面建立這些班級後，再重新上傳檔案。
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open("/teacher/classrooms", "_blank")}
                    className="mt-2"
                  >
                    前往「我的班級」
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* 預覽資料 */}
          {preview.length > 0 && (
            <div>
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium">預覽資料</h3>
                <div className="text-sm text-gray-600">
                  有效: {preview.filter((s) => s.isValid).length} / 總計:{" "}
                  {preview.length}
                </div>
              </div>

              <div className="border rounded-lg max-h-96 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left">狀態</th>
                      <th className="px-4 py-2 text-left">姓名</th>
                      <th className="px-4 py-2 text-left">班級</th>
                      <th className="px-4 py-2 text-left">生日</th>
                      <th className="px-4 py-2 text-left">錯誤訊息</th>
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
                    <p className="font-semibold text-lg">匯入完成</p>
                    <div className="flex gap-4">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        <span>
                          成功匯入: <strong>{successCount}</strong> 位學生
                        </span>
                      </div>
                      {failCount > 0 && (
                        <div className="flex items-center gap-2">
                          <X className="h-4 w-4 text-red-600" />
                          <span>
                            匯入失敗: <strong>{failCount}</strong> 位學生
                          </span>
                        </div>
                      )}
                    </div>
                    {duplicateAction === "skip" && successCount > 0 && (
                      <p className="text-sm text-gray-600">
                        已跳過重複的學生資料
                      </p>
                    )}
                    {duplicateAction === "update" && successCount > 0 && (
                      <p className="text-sm text-gray-600">
                        已更新重複學生的資料
                      </p>
                    )}
                    {duplicateAction === "add_suffix" && successCount > 0 && (
                      <p className="text-sm text-gray-600">
                        重複的學生已加上編號區分
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
                    <p className="font-medium">下一步：</p>
                    <ul className="list-disc list-inside text-sm space-y-1">
                      <li>學生預設密碼為生日（格式：YYYYMMDD）</li>
                      <li>請提醒學生首次登入後修改密碼</li>
                      <li>可以到「我的學生」頁面查看匯入的學生</li>
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
              取消
            </Button>
            {successCount > 0 || failCount > 0 ? (
              <Button onClick={handleClose} variant="default">
                完成
              </Button>
            ) : (
              <Button
                onClick={handleImport}
                disabled={
                  preview.filter((s) => s.isValid).length === 0 || importing
                }
              >
                {importing
                  ? "匯入中..."
                  : `匯入 ${preview.filter((s) => s.isValid).length} 位學生`}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
