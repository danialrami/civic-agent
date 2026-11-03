#!/usr/bin/env bash
# render_and_print.sh — Convert HTML to 1-page PDF and drive print job to Gusli (Brother MFC-J5340DW)
set -euo pipefail

INPUT_FILE="${1:-}"
PRINTER_NAME="${2:-Gusli}"
SIKU_HOST="${SIKU_HOST:-100.89.168.11}"
GOTENBERG_PORT="${GOTENBERG_PORT:-3006}"

if [[ -z "$INPUT_FILE" || ! -f "$INPUT_FILE" ]]; then
  echo "Usage: $0 <input.html> [printer_name]" >&2
  exit 1
fi

OUTPUT_PDF="${INPUT_FILE%.*}.pdf"

echo "==> Rendering PDF from $INPUT_FILE..."

# Strategy 1: Try Gotenberg on siku
if curl -s -m 2 "http://${SIKU_HOST}:${GOTENBERG_PORT}/health" | grep -q "up" 2>/dev/null; then
  echo "--> Using Gotenberg service on siku:${GOTENBERG_PORT}..."
  curl -s --request POST "http://${SIKU_HOST}:${GOTENBERG_PORT}/forms/chromium/convert/html" \
    --form "files=@${INPUT_FILE};filename=index.html" \
    -o "$OUTPUT_PDF"
else
  # Strategy 2: Fallback to local headless Chromium
  echo "--> Gotenberg unreachable; falling back to local headless Chromium..."
  chromium --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$OUTPUT_PDF" "$INPUT_FILE" >/dev/null 2>&1
fi

# Verify page count
PAGE_COUNT=$(pdfinfo "$OUTPUT_PDF" | awk '/^Pages:/ {print $2}')
echo "--> Generated PDF page count: $PAGE_COUNT"

if [[ "$PAGE_COUNT" -ne 1 ]]; then
  echo "WARNING: PDF has $PAGE_COUNT pages, not 1! Adjust CSS margins or table padding." >&2
fi

# Send to printer
echo "==> Sending to printer '$PRINTER_NAME' (Letter, 1-page forced)..."
lp -d "$PRINTER_NAME" -o page-ranges=1 -o media=Letter "$OUTPUT_PDF"

echo "==> Print job dispatched successfully."
