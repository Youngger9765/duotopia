/**
 * 錯誤日誌 Context - 提供全域的 studentId 和 assignmentId
 *
 * 使用方式：
 * 1. 在需要追蹤的頁面使用 setErrorLoggingContext 設定 ID
 * 2. audioErrorLogger 會自動使用這些 ID
 */

interface ErrorLoggingContext {
  studentId?: number;
  assignmentId?: number;
}

// 全域 context（不需要 React Context，因為 logAudioError 是純函數）
let globalErrorContext: ErrorLoggingContext = {
  studentId: undefined,
  assignmentId: undefined,
};

/**
 * 設定錯誤日誌的 context（在頁面層級呼叫）
 *
 * @example
 * // 在 StudentActivityPage.tsx
 * useEffect(() => {
 *   setErrorLoggingContext({
 *     studentId: student?.id,
 *     assignmentId: parseInt(assignmentId),
 *   });
 *
 *   // Cleanup
 *   return () => clearErrorLoggingContext();
 * }, [student, assignmentId]);
 */
export function setErrorLoggingContext(context: ErrorLoggingContext): void {
  globalErrorContext = { ...context };
  console.log("📝 Error logging context set:", globalErrorContext);
}

/**
 * 清除錯誤日誌 context（在頁面卸載時呼叫）
 */
export function clearErrorLoggingContext(): void {
  globalErrorContext = {
    studentId: undefined,
    assignmentId: undefined,
  };
  console.log("🧹 Error logging context cleared");
}

/**
 * 取得當前的錯誤日誌 context
 */
export function getErrorLoggingContext(): ErrorLoggingContext {
  return { ...globalErrorContext };
}
