const DEFAULT_ATTEMPTS = 3;
const BASE_DELAY_MS = 1_000;
const MAX_DELAY_MS = 15_000;

/**
 * Pull an HTTP status code out of an error, whatever shape it came in as.
 * The vendored substack-api fork's http-client throws `Error("HTTP 404: ...")`
 * for statuses it catches itself, while axios throws `AxiosError` (status on
 * `err.response.status`) for everything it rejects on its own. Returns null
 * when no status can be found (network error, timeout, etc).
 */
export function extractStatus(err: any): number | null {
  const fromResponse = err?.response?.status;
  if (typeof fromResponse === 'number') return fromResponse;
  const match = /(?:HTTP|status code)\s+(\d{3})/i.exec(String(err?.message ?? ''));
  return match ? parseInt(match[1], 10) : null;
}

/**
 * A 4xx other than 429 means the request itself is wrong or the session is
 * dead (bad/expired SID) — retrying it with backoff just delays a failure
 * that will never succeed. Everything else (5xx, network errors, timeouts,
 * unknown, and 429 rate-limits) is worth another attempt.
 */
export function isRetryable(status: number | null): boolean {
  if (status === null) return true;
  if (status === 429) return true;
  return status < 400 || status >= 500;
}

function retryAfterMs(err: any): number | null {
  const header = err?.response?.headers?.['retry-after'];
  if (header === undefined || header === null) return null;
  const seconds = parseInt(header, 10);
  return Number.isFinite(seconds) ? seconds * 1000 : null;
}

/**
 * Retry a network call up to `attempts` times with exponential back-off.
 * On each failure it logs the attempt number, label, and error message so
 * callers get clear visibility into transient failures without aborting the run.
 * Non-retryable client errors (401/403/404/...) fail immediately with a
 * distinct log line instead of burning through all attempts. The final
 * failure re-throws so the surrounding try/catch can decide whether to skip
 * or propagate.
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  label: string,
  attempts = DEFAULT_ATTEMPTS,
): Promise<T> {
  let lastErr: unknown;
  for (let i = 1; i <= attempts; i++) {
    try {
      return await fn();
    } catch (err: any) {
      lastErr = err;
      const status = extractStatus(err);
      if (!isRetryable(status)) {
        console.error(
          `[retry] ${label} failed with non-retryable HTTP ${status} — not retrying: ${err?.message ?? err}`,
        );
        throw err;
      }
      if (i < attempts) {
        const delay = Math.min(
          retryAfterMs(err) ?? BASE_DELAY_MS * Math.pow(2, i - 1),
          MAX_DELAY_MS,
        );
        console.warn(
          `[retry ${i}/${attempts}] ${label}: ${err?.message ?? err} — retrying in ${delay}ms`,
        );
        await new Promise<void>(r => setTimeout(r, delay));
      } else {
        console.error(
          `[retry] ${label} failed after ${attempts} attempts: ${err?.message ?? err}`,
        );
      }
    }
  }
  throw lastErr;
}

/**
 * Retry a boolean connectivity check until it returns true. Substack's
 * `testConnectivity()` swallows its underlying error and just returns false,
 * so a one-shot call can't tell a dead SID apart from a network blip — this
 * gives transient failures a few chances before a caller reports "SID might
 * be expired".
 */
export async function checkConnectivity(
  check: () => Promise<boolean>,
  attempts = DEFAULT_ATTEMPTS,
): Promise<boolean> {
  for (let i = 1; i <= attempts; i++) {
    if (await check()) return true;
    if (i < attempts) {
      const delay = BASE_DELAY_MS * Math.pow(2, i - 1);
      console.warn(
        `[retry ${i}/${attempts}] testConnectivity: not connected yet — retrying in ${delay}ms`,
      );
      await new Promise<void>(r => setTimeout(r, delay));
    }
  }
  return false;
}
