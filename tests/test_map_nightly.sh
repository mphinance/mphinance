#!/usr/bin/env bash
# Exercises tools/map_nightly.sh against stub tools and a throwaway git remote.
# Nothing is posted, no network, no real repo touched.   bash tests/test_map_nightly.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
PASS=0; FAILS=0

ok()   { PASS=$((PASS+1)); printf "  ok    %s\n" "$1"; }
bad()  { FAILS=$((FAILS+1)); printf "  FAIL  %s\n" "$1"; }
expect() { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (want '$3', got '$2')"; fi; }
has()  { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1 (missing '$3')"; fi; }
hasnt(){ if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1 (found '$3')"; else ok "$1"; fi; }

mk() {  # fresh remote + working clone ($R) + a second clone ($B) that can move the remote
  N=$1; rm -rf "$T/$N"; mkdir -p "$T/$N"; cd "$T/$N" || exit 1
  git init -q --bare remote.git
  git clone -q remote.git r 2>/dev/null; B="$T/$N/b"; R="$T/$N/r"
  cd r && git checkout -q -b work
  mkdir -p tools data/gamma_maps docs/gamma-record
  cp "$HERE/tools/repo_sync.sh" "$HERE/tools/map_nightly.sh" tools/
  echo '[]' > data/gamma_maps/SPY.json; echo '[]' > data/gamma_maps/CHANGELOG.json
  echo '# improve' > data/gamma_maps/IMPROVE.md; echo '<html/>' > docs/gamma-record/index.html
  echo 'old ledger backup' > data/gamma_maps/SPY.json.bak
  cat > tools/gamma_tomorrow.mjs <<'EOS'
#!/usr/bin/env bash
out=""; while [ $# -gt 0 ]; do [ "$1" = "--out" ] && out="$2"; shift; done
case "${STUB_TOOL:-ok}" in
  fail) echo "boom"; exit 1;;
  holiday) echo "Nothing to post: the market is closed"; exit 0;;
esac
mkdir -p "$out"; echo '{}' > "$out/spy.json"; head -c 70000 /dev/zero > "$out/spy.png"
echo "row $(date +%s%N)" >> data/gamma_maps/SPY.json
echo "bak $(date +%s%N)" >> data/gamma_maps/SPY.json.bak
echo "record so far: 35 session(s) graded"
if [ -n "${STUB_REMOTE_MOVES:-}" ]; then
  ( cd "$STUB_B" && git pull -q --ff-only && echo x >> other.txt && git add other.txt && git commit -qm other && git push -q origin HEAD:work )
fi
echo "$out/spy.png"; echo "$out/spy.json"
EOS
  cat > tools/map_sanity.py <<'EOS'
import os, sys
print("sanity stub"); sys.exit(int(os.environ.get("STUB_SANITY_RC", "0")))
EOS
  cat > tools/post_gamma_note.py <<'EOS'
import os, sys
dry = "--dry-run" in sys.argv
mode = os.environ.get("STUB_DRY" if dry else "STUB_POST", "ok")
if mode == "already":
    sys.exit("already posted a note today (2026-11-29); use --force to override")
if mode == "held":
    print("changelog HELD: too long"); sys.exit(0)
if mode == "fail":
    print("Traceback: 401 Unauthorized"); sys.exit(1)
print("caption preview" if dry else "posted note 4242")
EOS
  git add -A && git commit -qm init && git push -q -u origin work
  git clone -q -b work ../remote.git ../b
}

run() {  # run wrapper in $R, capture stdout+stderr into OUTPUT and rc into RC
  OUTPUT=$(cd "$R" && env MAP_REPO="$R" MAP_OUT="$T/out" MAP_NODE=bash MAP_FORCE_LATE=1 MAP_ALLOW_OPEN=1 \
       STUB_B="$B" "$@" bash "$R/tools/map_nightly.sh" 2>&1); RC=$?
}
head_of() { git -C "$1" rev-parse HEAD; }
remote_head() { git -C "$T/$N/remote.git" rev-parse work; }
ahead() { git -C "$R" fetch -q origin; git -C "$R" rev-list --count origin/work..HEAD; }
clean() { git -C "$R" status --porcelain --untracked-files=no | wc -l | tr -d ' '; }
commits() { git -C "$R" rev-list --count HEAD; }

echo "1  happy path, live"
mk t1; base=$(commits); run
expect "exit 0" "$RC" 0
has "reports the note" "$OUTPUT" "Tomorrow's Map: posted note 4242"
has "delivers the chart" "$OUTPUT" "MEDIA:$T/out/spy.png"
expect "one new commit" "$(( $(commits) - base ))" 1
expect "pushed (remote == local)" "$(remote_head)" "$(head_of "$R")"
expect "tree clean, scratch backup put back" "$(clean)" 0

echo "2  holiday: silent skip"
mk t2; base=$(commits); run env STUB_TOOL=holiday
expect "exit 0" "$RC" 0
expect "prints nothing" "$OUTPUT" ""
expect "no commit" "$(commits)" "$base"
expect "tree clean" "$(clean)" 0

echo "3  sanity fails: loud, ledger put back, nothing posted"
mk t3; base=$(commits); run env STUB_SANITY_RC=1
expect "exit 1" "$RC" 1
has "names the step" "$OUTPUT" "MAP NIGHTLY FAILED at: sanity check"
hasnt "never posted" "$OUTPUT" "posted note"
expect "ledger reverted" "$(clean)" 0
expect "no commit" "$(commits)" "$base"

echo "4  post fails: exit 3, ledger put back"
mk t4; base=$(commits); run env STUB_POST=fail
expect "exit 3" "$RC" 3
has "names the step" "$OUTPUT" "POST FAILED"
expect "ledger reverted" "$(clean)" 0
expect "no commit" "$(commits)" "$base"

echo "5  already posted today: continues and commits"
mk t5; base=$(commits); run env STUB_POST=already STUB_DRY=already
expect "exit 0" "$RC" 0
has "says so" "$OUTPUT" "already posted earlier today"
expect "commit made" "$(( $(commits) - base ))" 1
expect "tree clean, scratch backup put back" "$(clean)" 0

echo "6  dry run: nothing posted or committed, tree restored"
mk t6; base=$(commits); run env MAP_DRY_RUN=1
expect "exit 0" "$RC" 0
has "says dry run" "$OUTPUT" "DRY RUN"
expect "no commit" "$(commits)" "$base"
expect "tree clean" "$(clean)" 0

echo "7  remote moves mid-run: rebase and push"
mk t7; base=$(commits); run env STUB_REMOTE_MOVES=1
expect "exit 0" "$RC" 0
expect "in sync after" "$(remote_head)" "$(head_of "$R")"
expect "nothing ahead" "$(ahead)" 0

echo "8  outside the window: refuses before doing anything"
mk t8; base=$(commits)
OUTPUT=$(cd "$R" && env -u MAP_FORCE_LATE MAP_REPO="$R" MAP_OUT="$T/out" MAP_NODE=bash MAP_HOUR=10 bash "$R/tools/map_nightly.sh" 2>&1); RC=$?
expect "exit 1" "$RC" 1
has "explains" "$OUTPUT" "outside the 20:00-23:59 ET window"
expect "no commit" "$(commits)" "$base"

echo; echo "passed $PASS, failed $FAILS"
[ "$FAILS" -eq 0 ]
