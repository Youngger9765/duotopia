// Shared print HTML generation for sticky note views
// Used by both single-print (AssignmentStickyNote modal) and batch-print (ClassroomDetail)

export const STATUS_HEX: Record<
  string,
  { dot: string; bg: string; border: string; symbol: string; fontSize?: string }
> = {
  NOT_STARTED: {
    dot: "#9ca3af",
    bg: "#f9fafb",
    border: "#e5e7eb",
    symbol: "○",
  },
  IN_PROGRESS: {
    dot: "#3b82f6",
    bg: "#eff6ff",
    border: "#bfdbfe",
    symbol: "►",
  },
  SUBMITTED: {
    dot: "#eab308",
    bg: "#fefce8",
    border: "#fde68a",
    symbol: "★",
  },
  RETURNED: {
    dot: "#f97316",
    bg: "#fff7ed",
    border: "#fed7aa",
    symbol: "✗",
  },
  RESUBMITTED: {
    dot: "#a855f7",
    bg: "#faf5ff",
    border: "#e9d5ff",
    symbol: "◆",
    fontSize: "20px",
  },
  GRADED: {
    dot: "#22c55e",
    bg: "#f0fdf4",
    border: "#bbf7d0",
    symbol: "✓",
  },
};

// Status label config (matches STATUS_CONFIG in AssignmentStickyNote.tsx)
const STATUS_LABELS: Record<string, string> = {
  NOT_STARTED: "stickyNote.status.notStarted",
  IN_PROGRESS: "stickyNote.status.inProgress",
  SUBMITTED: "stickyNote.status.submitted",
  RETURNED: "stickyNote.status.returned",
  RESUBMITTED: "stickyNote.status.resubmitted",
  GRADED: "stickyNote.status.graded",
};

export interface PrintStudent {
  student_number: number;
  student_name: string;
  score?: number;
  status: string;
}

export interface PrintOptions {
  showNumber: boolean;
  showName: boolean;
  showScore: boolean;
}

/**
 * Build the HTML for a single sticky note page.
 * @param title Assignment title
 * @param students Sorted, filtered student list
 * @param statusCounts Record of status → count
 * @param options Display toggle options
 * @param t i18n translation function
 */
export function buildStickyNotePageHtml(
  title: string,
  students: PrintStudent[],
  statusCounts: Record<string, number>,
  options: PrintOptions,
  t: (key: string) => string,
): string {
  const { showNumber, showName, showScore } = options;

  // Legend
  const legendHtml = Object.entries(STATUS_LABELS)
    .map(([key, labelKey]) => {
      const hex = STATUS_HEX[key] || STATUS_HEX.NOT_STARTED;
      const count = statusCounts[key] || 0;
      return `<span style="display:inline-flex;align-items:center;gap:4px;margin-right:12px">
        <span style="font-size:${hex.fontSize || "14px"};font-weight:bold;color:${hex.dot};line-height:1">${hex.symbol}</span>
        <span>${t(labelKey)}${count ? ` (${count})` : ""}</span>
      </span>`;
    })
    .join("");

  // Student cards
  const cardsHtml = students
    .map((student) => {
      const hex = STATUS_HEX[student.status] || STATUS_HEX.NOT_STARTED;
      const hasNumber = student.student_number > 0;
      const parts: string[] = [];
      if (showNumber && hasNumber) {
        parts.push(
          `<div style="font-weight:bold;font-size:16px">${student.student_number}</div>`,
        );
      }
      if (showName) {
        parts.push(
          `<div style="font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%">${student.student_name}</div>`,
        );
      }
      if (showScore) {
        parts.push(
          `<div style="font-size:10px;color:#6b7280">${student.score != null ? student.score : "-"}</div>`,
        );
      }
      return `<div style="position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:6px;border-radius:8px;border:1px solid ${hex.border};background:${hex.bg};min-height:56px;text-align:center;overflow:hidden">
        <span style="position:absolute;top:1px;right:4px;font-size:${hex.fontSize || "14px"};font-weight:bold;color:${hex.dot};line-height:1">${hex.symbol}</span>
        ${parts.join("")}
      </div>`;
    })
    .join("");

  return `<div class="page">
  <h2>${title}</h2>
  <div class="legend">${legendHtml}</div>
  <div class="grid">${cardsHtml}</div>
  <div class="footer">
    <img src="https://storage.googleapis.com/duotopia-social-media-videos/website/logo/logo_row_nobg.png" alt="Duotopia" class="logo" />
    <div>${t("stickyNote.copyright")}</div>
  </div>
</div>`;
}

/**
 * Open a print window with one or more sticky note pages.
 */
export function openPrintWindow(pagesHtml: string[]): void {
  const printWindow = window.open("", "_blank");
  if (!printWindow) return;

  const allPages = pagesHtml.join("");

  printWindow.document.write(`<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Print</title>
<style>
  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }
  body { font-family: -apple-system, "Microsoft JhengHei", sans-serif; padding: 20px; margin: 0; }
  h2 { text-align: center; margin-bottom: 8px; }
  .legend { text-align: center; font-size: 12px; margin-bottom: 16px; }
  .grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
  .footer { text-align: center; font-size: 10px; color: #9ca3af; margin-top: 16px; padding-top: 8px; border-top: 1px solid #e5e7eb; }
  .footer .logo { height: 20px; margin: 0 auto 4px; display: block; }
  .page { page-break-after: always; }
  .page:last-child { page-break-after: auto; }
  @media print { body { padding: 10px; } }
</style>
</head><body>
  ${allPages}
  <script>window.onload=function(){window.print();window.onafterprint=function(){window.close();}}<` + `/script>
</body></html>`);
  printWindow.document.close();
}
