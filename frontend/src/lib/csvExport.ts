/**
 * CSV Export Utility
 *
 * 提供通用的 CSV 匯出功能
 */

export interface CSVColumn<T = Record<string, unknown>> {
  header: string;
  accessor: string | ((row: T) => string | number);
}

/**
 * 將資料匯出為 CSV 檔案
 * @param data 資料陣列
 * @param columns 欄位定義
 * @param filename 檔案名稱（不含副檔名）
 */
export function exportToCSV<T = Record<string, unknown>>(
  data: T[],
  columns: CSVColumn<T>[],
  filename: string,
): void {
  if (!data || data.length === 0) {
    alert("No data to export");
    return;
  }

  // 建立 CSV header
  const headers = columns.map((col) => col.header).join(",");

  // 建立 CSV rows
  const rows = data.map((row) => {
    return columns
      .map((col) => {
        let value: string | number;

        // 取得欄位值
        if (typeof col.accessor === "function") {
          value = col.accessor(row);
        } else {
          value = (row as Record<string, unknown>)[col.accessor] as
            | string
            | number;
        }

        // 處理 null/undefined
        if (value === null || value === undefined) {
          return "";
        }

        // 轉換為字串
        const stringValue = String(value);

        // CSV 跳脫：如果包含逗號、引號或換行，用引號包起來
        if (
          stringValue.includes(",") ||
          stringValue.includes('"') ||
          stringValue.includes("\n")
        ) {
          // 引號要 double escape
          return `"${stringValue.replace(/"/g, '""')}"`;
        }

        return stringValue;
      })
      .join(",");
  });

  // 組合完整 CSV
  const csvContent = [headers, ...rows].join("\n");

  // 加上 UTF-8 BOM 讓 Excel 正確顯示中文
  const BOM = "\uFEFF";
  const blob = new Blob([BOM + csvContent], {
    type: "text/csv;charset=utf-8;",
  });

  // 建立下載連結
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}.csv`);
  link.style.visibility = "hidden";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // 釋放 URL
  URL.revokeObjectURL(url);
}

/**
 * 格式化日期為 YYYY-MM-DD
 */
export function formatDate(dateString: string | null): string {
  if (!dateString) return "";
  return new Date(dateString).toISOString().split("T")[0];
}

/**
 * 格式化金額
 */
export function formatAmount(amount: number | null): string {
  if (amount === null || amount === undefined) return "";
  return `NT$ ${amount.toLocaleString()}`;
}
