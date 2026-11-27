#!/usr/bin/env bash
# Tomorrow's Map, nightly, deterministic. No agent in the loop.
#
#   tools/map_nightly.sh            run for real (21:00 ET Sun-Thu from a scheduler)
#   MAP_DRY_RUN=1 tools/map_nightly.sh   run everything except posting and committing,
#                                        then put the tool-owned files back
#
# Flow: sync repo -> build the map -> sanity-check it -> poster dry run -> post ->
# commit the four tool-owned files -> push -> verify local == remote.
# Anything that goes wrong prints "MAP NIGHTLY FAILED at: <step>" plus the last log
# lines on stdout and exits non-zero, which the scheduler delivers as a failure.
# A night with no session (holiday) prints nothing and exits 0.
#
# Exit codes: 0 ok or silent skip | 1 failed before posting | 2 posted but not pushed
#             3 post failed | 4 commit failed | 5 sync check failed | 127 missing tool
#
# Test hooks (env): MAP_REPO MAP_OUT MAP_NODE MAP_HOUR MAP_FORCE_LATE MAP_ALLOW_OPEN
set -uo pipefail
export TZ=America/New_York

R="${MAP_REPO:-/home/mph/mphinance}"
OUT="${MAP_OUT:-$HOME/.hermes/state/map}"
NODE="${MAP_NODE:-node}"
FILES="data/gamma_maps/SPY.json data/gamma_maps/CHANGELOG.json data/gamma_maps/IMPROVE.md docs/gamma-record/index.html"
# The tool also rewrites this tracked scratch backup of the previous ledger. It is never
# committed; put it back so the tree stays clean (found in the 2026-11-27 dry run).
SCRATCH="data/gamma_maps/SPY.json.bak"

LOG=$(mktemp)
trap 'rm -f "$LOG" "$LOG".*' EXIT

revert() { for f in $FILES $SCRATCH; do git checkout -q -- "$f" 2>/dev/null || true; done; }
fail() { echo "MAP NIGHTLY FAILED at: $1"; tail -n 15 "$LOG"; exit "${2:-1}"; }

cd "$R" || fail "cd $R"
mkdir -p "$OUT"
command -v "$NODE" >/dev/null && command -v python3 >/dev/null && command -v git >/dev/null \
  || fail "node, python3 or git missing" 127

H=$((10#${MAP_HOUR:-$(date +%H)}))
if [ "$H" -lt 20 ] && [ -z "${MAP_FORCE_LATE:-}" ]; then
  fail "outside the 20:00-23:59 ET window (hour is $H); the book is not settled yet"
fi

bash tools/repo_sync.sh pre >>"$LOG" 2>&1 || fail "repo_sync pre (behind, diverged or blocked)"

"$NODE" tools/gamma_tomorrow.mjs SPY --out "$OUT" >"$LOG.tool" 2>&1; rc=$?
cat "$LOG.tool" >>"$LOG"
[ "$rc" -eq 0 ] || { revert; fail "map tool exited $rc"; }

# A non-session night (holiday): the tool says so and writes nothing. Stay silent.
if grep -q "Nothing to post" "$LOG.tool"; then
  revert
  exit 0
fi

SIDE=$(tail -n1 "$LOG.tool")
PNG=$(tail -n2 "$LOG.tool" | head -n1)
{ [ -f "$SIDE" ] && [ -f "$PNG" ]; } || { revert; fail "tool did not write a sidecar and a chart"; }

SANITY_ARGS=""
[ -n "${MAP_ALLOW_OPEN:-}" ] && SANITY_ARGS="--allow-open"
python3 tools/map_sanity.py "$SIDE" "$PNG" $SANITY_ARGS >>"$LOG" 2>&1 \
  || { revert; fail "sanity check (ledger put back, nothing posted)"; }

python3 tools/post_gamma_note.py "$SIDE" --dry-run --no-discord >"$LOG.dry" 2>&1; rc=$?
cat "$LOG.dry" >>"$LOG"
if [ "$rc" -ne 0 ] && ! grep -q "already posted a note today" "$LOG.dry"; then
  revert; fail "poster dry run"
fi
if grep -qE "changelog HELD|NaN|undefined" "$LOG.dry"; then
  revert; fail "caption problem (HELD, NaN or undefined)"
fi

if [ -n "${MAP_DRY_RUN:-}" ]; then
  revert
  echo "Tomorrow's Map: DRY RUN, nothing posted or committed"
  grep -E "^(record so far|in flight):" "$LOG.tool"
  echo "MEDIA:$PNG"
  exit 0
fi

python3 tools/post_gamma_note.py "$SIDE" --no-discord >"$LOG.post" 2>&1
cat "$LOG.post" >>"$LOG"
if grep -q "^posted note " "$LOG.post"; then
  NOTE=$(grep -m1 "^posted note " "$LOG.post")
elif grep -q "already posted a note today" "$LOG.post"; then
  NOTE="already posted earlier today"
else
  revert; fail "POST FAILED (Substack cookie expired?)" 3
fi

for f in $FILES; do [ -e "$f" ] && git add -f -- "$f" >>"$LOG" 2>&1; done
if ! git diff --cached --quiet; then
  git commit -q -m "gamma-tomorrow: ledger through $(date +%F)" >>"$LOG" 2>&1 || fail "git commit after posting ($NOTE)" 4
  BR=$(git rev-parse --abbrev-ref HEAD)
  if ! git push -q origin "$BR" >>"$LOG" 2>&1; then
    { git pull -q --rebase --autostash origin "$BR" && git push -q origin "$BR"; } >>"$LOG" 2>&1 \
      || fail "POSTED ($NOTE) BUT NOT PUSHED" 2
  fi
fi

git checkout -q -- "$SCRATCH" 2>/dev/null || true
bash tools/repo_sync.sh post >>"$LOG" 2>&1 || fail "repo_sync post after posting ($NOTE)" 5

echo "Tomorrow's Map: $NOTE"
grep -E "^(record so far|last call):" "$LOG.tool" || true
echo "MEDIA:$PNG"
