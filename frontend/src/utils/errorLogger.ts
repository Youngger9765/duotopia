/**
 * Centralized error logging utility
 * 
 * - Development: Logs full error details to console
 * - Production: Logs sanitized errors, can send to error tracking service
 */

const isDevelopment = import.meta.env.MODE === "development" || import.meta.env.DEV;

/**
 * Sanitize error to remove sensitive information
 */
function sanitizeError(error: unknown): string {
  if (error instanceof Error) {
    // Remove stack traces and sensitive data in production
    if (!isDevelopment) {
      return error.message;
    }
    return error.stack || error.message;
  }
  
  if (typeof error === "string") {
    return error;
  }
  
  try {
    return JSON.stringify(error);
  } catch {
    return "Unknown error";
  }
}

/**
 * Log error with appropriate level based on environment
 * 
 * @param context - Context where error occurred (e.g., "Failed to fetch school")
 * @param error - Error object or message
 * @param additionalInfo - Optional additional information
 */
export function logError(
  context: string,
  error: unknown,
  additionalInfo?: Record<string, unknown>
): void {
  const sanitized = sanitizeError(error);
  
  if (isDevelopment) {
    // Development: Full error details
    console.error(`[${context}]`, error, additionalInfo || "");
  } else {
    // Production: Sanitized error only
    console.error(`[${context}]`, sanitized);
    
    // TODO: Send to error tracking service (e.g., Sentry, LogRocket)
    // Example:
    // if (window.Sentry) {
    //   window.Sentry.captureException(error, {
    //     tags: { context },
    //     extra: additionalInfo,
    //   });
    // }
  }
}

/**
 * Log warning (always shown, but less verbose in production)
 */
export function logWarning(
  context: string,
  message: string,
  additionalInfo?: Record<string, unknown>
): void {
  if (isDevelopment) {
    console.warn(`[${context}]`, message, additionalInfo || "");
  } else {
    console.warn(`[${context}]`, message);
  }
}

/**
 * Log info (only in development)
 */
export function logInfo(
  context: string,
  message: string,
  data?: unknown
): void {
  if (isDevelopment) {
    console.log(`[${context}]`, message, data || "");
  }
}

