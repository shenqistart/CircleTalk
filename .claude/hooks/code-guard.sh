#!/usr/bin/env bash
# code-guard.sh — PostToolUse hook for Edit/Write operations
# Runs lint + type check on modified files

set -euo pipefail

TOOL_INPUT="${1:-}"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Extract file path from tool input
FILE_PATH=""
if echo "$TOOL_INPUT" | grep -q '"file_path"'; then
    FILE_PATH=$(echo "$TOOL_INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//;s/"$//')
fi

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Phase 1: Lint & Type Check
ERRORS=0

# Python files
if [[ "$FILE_PATH" == *.py ]]; then
    # Ruff format
    if command -v ruff &>/dev/null; then
        ruff format "$FILE_PATH" 2>/dev/null || true
        if ! ruff check "$FILE_PATH" 2>/dev/null; then
            echo "::error::ruff check failed for $FILE_PATH"
            ERRORS=1
        fi
    fi
fi

# TypeScript/TSX files
if [[ "$FILE_PATH" == *.ts || "$FILE_PATH" == *.tsx ]]; then
    FRONTEND_DIR="$PROJECT_ROOT/apps/frontend"
    if [ -d "$FRONTEND_DIR" ] && command -v npx &>/dev/null; then
        cd "$FRONTEND_DIR"
        npx eslint "$FILE_PATH" --no-error-on-unmatched-pattern 2>/dev/null || {
            echo "::error::eslint failed for $FILE_PATH"
            ERRORS=1
        }
        cd "$PROJECT_ROOT"
    fi
fi

# Phase 2: File modification tracking
STATE_DIR="$PROJECT_ROOT/.claude/state"
mkdir -p "$STATE_DIR"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $FILE_PATH" >> "$STATE_DIR/modified-files.log" 2>/dev/null || true

if [ "$ERRORS" -ne 0 ]; then
    exit 2
fi

exit 0
