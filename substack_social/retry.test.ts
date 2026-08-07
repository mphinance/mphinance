/**
 * Manual validation script for retry.ts — this repo has no TS test runner
 * configured (see package.json), so this follows the same convention as the
 * Python side's "minimal check script" for areas without a formal suite.
 * Run with: npx ts-node retry.test.ts
 */
import * as assert from 'assert';
import { extractStatus, isRetryable, withRetry, checkConnectivity } from './retry';

function makeAxiosError(status: number, retryAfter?: string) {
  return {
    message: `Request failed with status code ${status}`,
    response: { status, headers: retryAfter ? { 'retry-after': retryAfter } : {} },
  };
}

// ── extractStatus ───────────────────────────────────────────────────────
assert.strictEqual(extractStatus(makeAxiosError(401)), 401, 'reads status from AxiosError.response.status');
assert.strictEqual(extractStatus(new Error('HTTP 404: Not Found')), 404, 'reads status from "HTTP nnn:" message text');
assert.strictEqual(extractStatus(new Error('Request failed with status code 429')), 429, 'reads status from axios default message text');
assert.strictEqual(extractStatus(new Error('socket hang up')), null, 'no status found on a plain network error');
assert.strictEqual(extractStatus(undefined), null, 'never throws on a missing error');

// ── isRetryable ─────────────────────────────────────────────────────────
assert.strictEqual(isRetryable(null), true, 'unknown-status errors (network/timeout) are retried');
assert.strictEqual(isRetryable(429), true, 'rate limits are retried');
assert.strictEqual(isRetryable(500), true, '5xx is retried');
assert.strictEqual(isRetryable(200), true, 'below 400 is retried (defensive — should not normally reach here)');
assert.strictEqual(isRetryable(401), false, 'auth failure is not retried');
assert.strictEqual(isRetryable(403), false, 'forbidden is not retried');
assert.strictEqual(isRetryable(404), false, 'not found is not retried');

// ── withRetry: non-retryable fails fast without exhausting attempts ─────
async function testWithRetryFailsFastOn401() {
  let calls = 0;
  await assert.rejects(
    withRetry(
      async () => {
        calls++;
        throw makeAxiosError(401);
      },
      'fails fast',
      3,
    ),
  );
  assert.strictEqual(calls, 1, 'a 401 should only be attempted once, not retried 3x');
}

// ── withRetry: retryable errors are retried up to `attempts` then re-thrown ─
async function testWithRetryExhaustsOn500() {
  let calls = 0;
  await assert.rejects(
    withRetry(
      async () => {
        calls++;
        throw makeAxiosError(500);
      },
      'exhausts',
      3,
    ),
  );
  assert.strictEqual(calls, 3, 'a 500 should be attempted the full 3 times');
}

// ── withRetry: succeeds once the underlying call stops failing ──────────
async function testWithRetrySucceedsAfterTransientFailure() {
  let calls = 0;
  const result = await withRetry(
    async () => {
      calls++;
      if (calls < 2) throw makeAxiosError(503);
      return 'ok';
    },
    'eventually succeeds',
    3,
  );
  assert.strictEqual(result, 'ok');
  assert.strictEqual(calls, 2);
}

// ── checkConnectivity: retries a false-returning (non-throwing) check ───
async function testCheckConnectivityRetriesFalse() {
  let calls = 0;
  const ok = await checkConnectivity(async () => {
    calls++;
    return calls >= 2;
  }, 3);
  assert.strictEqual(ok, true, 'should succeed once the check flips to true');
  assert.strictEqual(calls, 2);
}

async function testCheckConnectivityGivesUpAfterAttempts() {
  let calls = 0;
  const ok = await checkConnectivity(async () => {
    calls++;
    return false;
  }, 3);
  assert.strictEqual(ok, false);
  assert.strictEqual(calls, 3);
}

async function main() {
  await testWithRetryFailsFastOn401();
  await testWithRetryExhaustsOn500();
  await testWithRetrySucceedsAfterTransientFailure();
  await testCheckConnectivityRetriesFalse();
  await testCheckConnectivityGivesUpAfterAttempts();
  console.log('retry.test.ts: all checks passed');
}

main().catch((e) => {
  console.error('retry.test.ts FAILED:', e);
  process.exit(1);
});
