#!/bin/bash
# One-step Git Add, Commit, Push

if [ -z "$1" ]
then
      MSG="Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')"
else
      MSG="$1"
fi

git add .
git commit -m "$MSG"
git push
