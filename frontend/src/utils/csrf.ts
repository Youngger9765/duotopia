/**
 * CSRF Protection Utilities
 *
 * Provides CSRF token management for state-changing HTTP requests.
 * Tokens are stored in sessionStorage and automatically refreshed.
 */

const CSRF_TOKEN_KEY = "csrf_token";
const TOKEN_EXPIRY_MS = 3600000; // 1 hour

interface CSRFTokenData {
  token: string;
  timestamp: number;
}

/**
 * Generate a cryptographically secure CSRF token
 */
function generateToken(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join(
    "",
  );
}

/**
 * Get or generate a CSRF token
 * Token is cached in sessionStorage and auto-refreshed after expiry
 */
export function getCSRFToken(): string {
  try {
    const stored = sessionStorage.getItem(CSRF_TOKEN_KEY);
    if (stored) {
      const data: CSRFTokenData = JSON.parse(stored);
      const age = Date.now() - data.timestamp;

      // Return cached token if not expired
      if (age < TOKEN_EXPIRY_MS) {
        return data.token;
      }
    }
  } catch (error) {
    console.warn("Failed to read CSRF token from storage:", error);
  }

  // Generate new token
  const token = generateToken();
  const data: CSRFTokenData = {
    token,
    timestamp: Date.now(),
  };

  try {
    sessionStorage.setItem(CSRF_TOKEN_KEY, JSON.stringify(data));
  } catch (error) {
    console.warn("Failed to store CSRF token:", error);
  }

  return token;
}

/**
 * Clear CSRF token (useful for logout)
 */
export function clearCSRFToken(): void {
  try {
    sessionStorage.removeItem(CSRF_TOKEN_KEY);
  } catch (error) {
    console.warn("Failed to clear CSRF token:", error);
  }
}

/**
 * Get headers with CSRF token for state-changing requests
 */
export function getCSRFHeaders(additionalHeaders: HeadersInit = {}): Headers {
  const headers = new Headers(additionalHeaders);
  headers.set("X-CSRF-Token", getCSRFToken());
  return headers;
}
