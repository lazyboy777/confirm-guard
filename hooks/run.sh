#!/usr/bin/env bash
# Cross-platform Python launcher for confirm-guard
# macOS/Linux: python3  |  Windows (Git Bash): python
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if command -v python3 &>/dev/null; then
    exec python3 "$SCRIPT_DIR/confirm-dialog.py"
elif command -v python &>/dev/null; then
    exec python "$SCRIPT_DIR/confirm-dialog.py"
else
    exit 0
fi
