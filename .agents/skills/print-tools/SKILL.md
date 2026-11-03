---
name: print-tools
description: Print documents, cheat sheets, and PDFs to the network Brother printer (Gusli / MFC-J5340DW) using CUPS or IPP Everywhere. Render HTML/Markdown to 1-page print-ready PDFs using Gotenberg on siku (port 3006) or local headless Chromium. Use when asked to print, generate a printable PDF, check printer status, or manage print queues.
---

# Print Tools Skill

Operational guide and automation for rendering single-page documents and driving print jobs to the homelab network printer.

---

## 1. Network Printer Hardware & Setup

* **Model:** Brother MFC-J5340DW (Color Inkjet, Duplex, Tabloid/A3 capable)
* **CUPS / mDNS Name:** `Gusli`
* **Network IP:** `192.168.1.236` (port 631, IPP Everywhere / AirPrint)
* **Local CUPS Destination:** Default printer is set to `Gusli` via `ipp://192.168.1.236:631/ipp/print`.

---

## 2. PDF Rendering Strategies

When converting Markdown or HTML into a crisp, single-page printable PDF:

### Option A: Gotenberg Service on `siku` (Recommended)
Gotenberg 8 runs in Docker on homelab host `siku` (`100.89.168.11:3006` or `siku:3006`).

```bash
# Convert HTML to PDF via Gotenberg
curl -s --request POST 'http://100.89.168.11:3006/forms/chromium/convert/html' \
  --form 'files=@input.html;filename=index.html' \
  -o output.pdf

# Convert Markdown directly via Gotenberg
curl -s --request POST 'http://100.89.168.11:3006/forms/chromium/convert/markdown' \
  --form 'files=@index.html;filename=index.html' \
  --form 'files=@document.md;filename=document.md' \
  -o output.pdf
```

### Option B: Local Headless Chromium Fallback
If `siku` is unreachable or offline, use the local Chromium installation on `kora`:

```bash
chromium --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=output.pdf input.html
```

---

## 3. Strict 1-Page Enforcement

Always verify that the generated PDF does not spill over onto a second page:

```bash
# Check page count
pdfinfo output.pdf | grep "Pages:"
# Expected: Pages: 1
```

If `Pages:` > 1, adjust CSS margins, padding, or table line-height in the HTML template before sending to the printer.

---

## 4. Driving the Print Job

Print directly via CUPS using standard LP options:

```bash
# Print 1-page letter document to default printer (Gusli)
lp -o page-ranges=1 -o media=Letter output.pdf

# Check queue status
lpstat -o

# Check printer hardware status
lpstat -p Gusli
```

---

## 5. Bundled Scripts & Templates

* `scripts/render_and_print.sh`: End-to-end wrapper script that converts HTML/MD to PDF and prints it.
* `templates/one-page-cheat-sheet.html`: CSS-tuned single-page layout with high-contrast borders and checkbox styling.
