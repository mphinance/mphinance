#!/usr/bin/env bash
#
# install.sh — install the sub-claude skill system-wide (~/.claude/skills/).
#
# Why system-wide: sub-claude is a generic dev utility, not repo-specific
# logic. Installed here it's available to EVERY repo you open with Claude Code
# (mphinance, all the TraderDaddy repos, anything future) — one copy, one place
# to update — instead of a stale copy vendored into each repo.
#
# Usage (run on the machine where you actually run Claude Code, e.g. the VPS):
#     bash ~/path/to/mphinance/.claude/skills/sub-claude/install.sh
#
# It's self-locating (copies its own sibling files) and idempotent — re-run it
# any time to update the system-wide copy after pulling a new version.
#
# Override the target with SKILLS_DIR, e.g.:
#     SKILLS_DIR=/opt/claude/skills bash install.sh
#
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${SKILLS_DIR:-$HOME/.claude/skills}"
DEST_DIR="$SKILLS_DIR/sub-claude"

if [[ ! -f "$SRC_DIR/scripts/sub_claude.py" ]]; then
    echo "error: can't find scripts/sub_claude.py next to this installer ($SRC_DIR)" >&2
    echo "       run install.sh from inside the skill directory it ships in." >&2
    exit 1
fi

echo "Installing sub-claude"
echo "  from: $SRC_DIR"
echo "  to:   $DEST_DIR"

mkdir -p "$DEST_DIR/scripts"
cp "$SRC_DIR/SKILL.md" "$DEST_DIR/SKILL.md"
cp "$SRC_DIR/scripts/sub_claude.py" "$DEST_DIR/scripts/sub_claude.py"
chmod +x "$DEST_DIR/scripts/sub_claude.py"

# Sanity check: the worker script must at least parse under the local python.
if command -v python3 >/dev/null 2>&1; then
    if python3 -m py_compile "$DEST_DIR/scripts/sub_claude.py"; then
        echo "  ✓ sub_claude.py compiles"
    else
        echo "  ! sub_claude.py failed to compile — check your python3" >&2
    fi
    rm -rf "$DEST_DIR/scripts/__pycache__"  # don't leave build artifacts behind
fi

echo
echo "Done. sub-claude is now available to every repo on this machine."
echo "Invoke the script directly as:"
echo "  python3 $DEST_DIR/scripts/sub_claude.py <input.csv> --prompt ... --output ..."
echo
echo "Note: it shells out to the 'claude' CLI, so make sure that's on PATH."
