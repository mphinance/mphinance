#!/usr/bin/env bash
# repo_sync.sh pre|post [--strict]
#
# The standing sync rule for this repo, as a command.
#   pre   run BEFORE you touch anything: fetch, fast-forward if behind.
#   post  run AFTER you finish: fast-forward if the remote moved, push your
#         commits, then confirm local and remote are identical.
#
# Exit codes: 0 ok | 2 setup problem | 3 diverged | 4 fast-forward refused
#             5 --strict and tracked files are modified | 6 push failed
#             7 not in sync after post
#
# It never force-pushes, never resets, never stashes for you. Untracked files
# are ignored on purpose (this repo has many generated ones). Tracked-file edits
# only produce a warning unless you pass --strict.
set -u

mode="${1:-}"
strict=0
[ "${2:-}" = "--strict" ] && strict=1

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "repo_sync: not inside a git repo"; exit 2; }

branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "HEAD" ]; then
  echo "repo_sync: detached HEAD, check out a branch first"
  exit 2
fi

git fetch --quiet origin || { echo "repo_sync: fetch failed (network or auth)"; exit 2; }
up="origin/$branch"
git rev-parse --verify -q "$up" >/dev/null || { echo "repo_sync: no $up on the remote"; exit 2; }

behind=0
ahead=0
counts() {
  read -r behind ahead < <(git rev-list --left-right --count "$up"...HEAD)
}
dirty=$(git status --porcelain --untracked-files=no | wc -l)

case "$mode" in
  pre)
    counts
    if [ "$behind" -gt 0 ] && [ "$ahead" -gt 0 ]; then
      echo "repo_sync: DIVERGED (behind $behind, ahead $ahead). Resolve by hand, do not force."
      exit 3
    fi
    if [ "$behind" -gt 0 ]; then
      if ! git pull --ff-only --quiet; then
        echo "repo_sync: fast-forward refused (local edits in the way?). Stash or commit, then rerun."
        exit 4
      fi
      echo "repo_sync: fast-forwarded $behind commit(s)"
      counts
    fi
    if [ "$ahead" -gt 0 ]; then
      echo "repo_sync: WARNING $ahead unpushed commit(s) already here; run '$0 post' when you finish"
    fi
    if [ "$dirty" -gt 0 ]; then
      echo "repo_sync: WARNING $dirty tracked file(s) are modified"
      [ "$strict" -eq 1 ] && exit 5
    fi
    echo "repo_sync: pre ok at $(git rev-parse --short HEAD)"
    exit 0
    ;;
  post)
    counts
    if [ "$behind" -gt 0 ]; then
      if ! git pull --ff-only --quiet; then
        echo "repo_sync: remote moved and a fast-forward is not possible (diverged). Rebase by hand."
        exit 4
      fi
      counts
    fi
    if [ "$ahead" -gt 0 ]; then
      git push --quiet origin "$branch" || { echo "repo_sync: push failed"; exit 6; }
    fi
    git fetch --quiet origin
    counts
    if [ "$behind" -ne 0 ] || [ "$ahead" -ne 0 ]; then
      echo "repo_sync: NOT in sync (behind $behind, ahead $ahead)"
      exit 7
    fi
    if [ "$dirty" -gt 0 ]; then
      echo "repo_sync: WARNING $dirty tracked file(s) still modified and uncommitted"
      [ "$strict" -eq 1 ] && exit 5
    fi
    echo "repo_sync: post ok, in sync at $(git rev-parse --short HEAD)"
    exit 0
    ;;
  *)
    echo "usage: repo_sync.sh pre|post [--strict]"
    exit 2
    ;;
esac
