#!/usr/bin/env bash
# render_and_print.sh — Convert Ballot Guide Markdown/HTML to 1-Page PDF and Print
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

INPUT_FILE="${1:-$REPO_ROOT/elections/2026-11-03_texas-general/ballot-guide.md}"
PRINTER_NAME="${2:-Gusli}"

exec uv run python "$REPO_ROOT/src/civic_agent/print_ballot.py" "$INPUT_FILE" --printer "$PRINTER_NAME" "$@"
