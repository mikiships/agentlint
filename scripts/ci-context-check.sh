#!/usr/bin/env bash
# ci-context-check.sh — Run agentlint check-context and emit GitHub Action outputs.
#
# Usage: ci-context-check.sh [context-file]
#
# Outputs (GitHub Actions):
#   freshness-score  — integer 0–100
#   context-findings — JSON array of findings
#
# Exit codes:
#   0 — no ERROR findings (warnings/info OK)
#   1 — one or more ERROR findings found
#   2 — context file not found (exits 0 with warning, non-blocking)

set -euo pipefail

CONTEXT_FILE="${1:-}"

# Locate file
if [ -n "$CONTEXT_FILE" ]; then
  if [ ! -f "$CONTEXT_FILE" ]; then
    echo "::warning::agentlint check-context: context file '$CONTEXT_FILE' not found. Skipping."
    exit 0
  fi
  FILE_ARG="$CONTEXT_FILE"
else
  # Auto-detect
  for name in AGENTS.md CLAUDE.md GEMINI.md .cursorrules; do
    if [ -f "$name" ]; then
      FILE_ARG="$name"
      break
    fi
  done
  if [ -z "${FILE_ARG:-}" ]; then
    echo "::warning::agentlint check-context: no context file found in $(pwd). Skipping."
    exit 0
  fi
fi

# Run check-context in JSON mode
JSON_OUT=$(agentlint check-context "$FILE_ARG" --format json 2>&1) || CHECK_EXIT=$?
CHECK_EXIT="${CHECK_EXIT:-0}"

# Parse outputs
SCORE=$(echo "$JSON_OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['freshness_score'])" 2>/dev/null || echo "0")
FINDINGS=$(echo "$JSON_OUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d['findings']))" 2>/dev/null || echo "[]")

# Emit to GITHUB_OUTPUT if available
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  {
    echo "freshness-score=$SCORE"
    echo "context-findings<<EOF"
    echo "$FINDINGS"
    echo "EOF"
  } >> "$GITHUB_OUTPUT"
fi

echo "agentlint context check: $FILE_ARG"
echo "Freshness score: $SCORE/100"

# Surface findings to job summary
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  agentlint check-context "$FILE_ARG" --format markdown >> "$GITHUB_STEP_SUMMARY" || true
fi

exit "$CHECK_EXIT"
