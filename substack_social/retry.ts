const DEFAULT_ATTEMPTS = 3;
const BASE_DELAY_MS = 1_000;

/**
 * Retry a network call up to `attempts` times with exponential back-off.
 * On each failure it logs the attempt number, label, and error message so
 * callers get clear visibility into transient failures without aborting the run.
 * The final failure re-throws so the surrounding try/catch can decide whether
 * to skip or propagate.
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
      if (i < attempts) {
        const delay = BASE_DELAY_MS * Math.pow(2, i - 1);
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
