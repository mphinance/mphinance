#!/usr/bin/env bash
# run_daily_review.sh — durable OS-cron floor for the Daily Review.
#
# Runs the dossier pipeline in DRY-RUN mode on this box (the Hetzner box) to
# produce fresh charts + the private push payload (dossier/private/
# daily_review_push.json) locally. DRY-RUN means it does NOT git-commit or post
# the PUBLIC teaser — GitHub Actions remains the public publisher (never run the
# full pipeline on both → double-commit/post).
#
# Delivery:
#   - If WEBHOOK_DAILY_REVIEW is set, the pipeline's emit_push posts the private
#     review to that Discord webhook now (Claude-independent floor → Discord
#     mobile push works even if no Claude session is alive).
#   - The native phone push (PushNotification) is done separately by the Claude
#     scheduled task, which reads the push file this script produced.
#
# Wire into cron (weekdays, ~11:00 UTC, a few min before the Claude push task):
#   3 11 * * 1-5 /home/mph/mphinance/dossier/run_daily_review.sh >> /home/mph/daily-review.log 2>&1

set -euo pipefail

REPO="/home/mph/mphinance"
VENV_PY="$REPO/.venv/bin/python"

cd "$REPO"

# Keep the box's working copy current with its branch (best-effort; never abort).
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
git pull --ff-only origin "$BRANCH" 2>/dev/null || echo "[run_daily_review] git pull skipped (non-ff or offline)"

echo "[run_daily_review] $(date -u +%Y-%m-%dT%H:%M:%SZ) starting dry-run on $BRANCH"
"$VENV_PY" -m dossier.generate --dry-run --no-pdf
echo "[run_daily_review] $(date -u +%Y-%m-%dT%H:%M:%SZ) done"
