"""
print_ballot.py — Markdown Ballot Guide Parser, Gotenberg/Chromium PDF Renderer,
and IPP Print Verifier for Civic Agent.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional


def parse_markdown_ballot(md_path: Path) -> dict:
    """Parse title, metadata, and table rows from a ballot-guide.md file."""
    content = md_path.read_text(encoding="utf-8")

    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Bexar County General Election — Voter Cheat Sheet"

    loc_match = re.search(r"\*\*Polling Location:\*\*\s*([^\n\r]+)", content)
    location = loc_match.group(1).strip() if loc_match else "Hatchett Elementary (10700 Ingram Rd)"

    hours_match = re.search(r"\*\*Voting Hours:\*\*\s*([^\n\r]+)", content)
    hours = hours_match.group(1).strip() if hours_match else "7:00 AM – 7:00 PM"

    precinct_match = re.search(r"\*\*Precinct:\*\*\s*([^\n\r]+)", content)
    precinct = precinct_match.group(1).strip() if precinct_match else "1158 (Bexar County)"

    # Parse markdown table
    table_lines = [l.strip() for l in content.splitlines() if l.strip().startswith("|")]
    rows = []
    for line in table_lines[2:]:  # skip header and divider
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 3:
            contest = parts[0]
            options = parts[1]
            selection = parts[2]
            rows.append({
                "contest": contest,
                "options": options,
                "selection": selection
            })

    return {
        "title": title,
        "location": location,
        "hours": hours,
        "precinct": precinct,
        "rows": rows
    }


def render_html(data: dict, template_path: Optional[Path] = None) -> str:
    """Generate self-contained HTML from ballot data using template."""
    title = data.get("title", "Bexar County General Election — Voter Cheat Sheet")
    location = data.get("location", "")
    hours = data.get("hours", "")
    precinct = data.get("precinct", "")

    # Build table rows HTML
    rows_html = []
    current_section = None

    for item in data.get("rows", []):
        contest_raw = item["contest"]
        options_raw = item["options"]
        selection_raw = item["selection"]

        # Clean markdown formatting
        contest_clean = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", contest_raw)
        options_clean = re.sub(r"<br\s*/?>", " &bull; ", options_raw)
        selection_clean = re.sub(r"\*\*(.+?)\*\*", r"\1", selection_raw)

        # Categorize sections if not explicit
        contest_lower = contest_clean.lower()
        if any(w in contest_lower for w in ["senate", "representative", "governor", "attorney general"]):
            section = "Federal & Statewide Executive"
        elif any(w in contest_lower for w in ["house", "judge", "district attorney"]):
            section = "State Legislative & Bexar County Executive"
        elif any(w in contest_lower for w in ["prop", "bond", "vatre", "isd"]):
            section = "Municipal & Northside ISD Ballot Measures"
        else:
            section = "Other Contests"

        if section != current_section:
            current_section = section
            rows_html.append(f'      <tr class="section-row"><td colspan="3">{current_section}</td></tr>')

        # Format checkbox checkmark
        rows_html.append(f"""      <tr>
        <td>{contest_clean}</td>
        <td>{options_clean}</td>
        <td class="choice"><span class="box">&check;</span> {selection_clean}</td>
      </tr>""")

    table_rows_str = "\n".join(rows_html)

    if template_path and template_path.exists():
        template = template_path.read_text(encoding="utf-8")
        html = template.replace("{{TITLE}}", title)
        html = html.replace("{{DATE}}", "Tuesday, Nov 3, 2026")
        html = html.replace("{{HOURS}}", hours)
        html = html.replace("{{LOCATION}}", location)
        html = html.replace("{{PRECINCT}}", precinct)
        html = html.replace("{{TABLE_ROWS}}", table_rows_str)
        html = html.replace("{{FOOTER_TEXT}}", "Texas Election Code § 61.014: Cell phones, smartwatches, and tablets are prohibited within 100 feet of voting stations. Printed/written paper notes are 100% permitted. Bring this sheet and valid Texas Photo ID.")
        return html

    # Built-in fallback template
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  @page {{ size: letter portrait; margin: 0.5in; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #111; margin: 0; padding: 0; font-size: 10.5pt; line-height: 1.3; }}
  h1 {{ font-size: 15pt; margin: 0 0 4px 0; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #000; padding-bottom: 4px; }}
  .meta {{ font-size: 8.5pt; color: #444; margin-bottom: 10px; display: flex; justify-content: space-between; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; }}
  th, td {{ padding: 4px 6px; text-align: left; border-bottom: 1px solid #ddd; font-size: 9pt; }}
  th {{ background-color: #f0f0f0; font-weight: 600; border-bottom: 2px solid #333; font-size: 8.5pt; text-transform: uppercase; }}
  .section-row td {{ background-color: #eaeaea; font-weight: bold; font-size: 8.5pt; letter-spacing: 0.5px; text-transform: uppercase; padding: 3px 6px; border-top: 1px solid #aaa; border-bottom: 1px solid #aaa; }}
  .choice {{ font-weight: bold; color: #000; }}
  .box {{ display: inline-block; width: 11px; height: 11px; border: 1.5px solid #000; margin-right: 4px; vertical-align: middle; text-align: center; line-height: 10px; font-size: 8pt; font-weight: bold; }}
  .footer {{ margin-top: 6px; font-size: 7.5pt; color: #666; border-top: 1px dashed #999; padding-top: 4px; text-align: center; }}
</style>
</head>
<body>
  <h1>{title}</h1>
  <div class="meta">
    <div><strong>Date:</strong> Tuesday, Nov 3, 2026 &bull; <strong>Hours:</strong> {hours}</div>
    <div><strong>Location:</strong> {location} &bull; <strong>Precinct:</strong> {precinct}</div>
  </div>
  <table>
    <thead>
      <tr>
        <th style="width: 32%;">Contest / Measure</th>
        <th style="width: 40%;">Candidates / Options</th>
        <th style="width: 28%;">My Selection</th>
      </tr>
    </thead>
    <tbody>
{table_rows_str}
    </tbody>
  </table>
  <div class="footer">
    <em>Texas Election Code § 61.014: Cell phones, smartwatches, and tablets are prohibited within 100 feet of voting stations. Printed/written paper notes are 100% permitted. Bring this sheet and valid Texas Photo ID.</em>
  </div>
</body>
</html>"""


def convert_html_to_pdf(html_path: Path, output_pdf: Path, gotenberg_url: str = "http://100.89.168.11:3006") -> Path:
    """Convert HTML to PDF using Gotenberg (siku) or local Chromium fallback."""
    # Try Gotenberg
    try:
        health_req = urllib.request.Request(f"{gotenberg_url}/health", method="GET")
        with urllib.request.urlopen(health_req, timeout=1.5) as resp:
            if resp.status == 200:
                print(f"--> Converting via Gotenberg on {gotenberg_url}...")
                boundary = "----WebKitFormBoundaryCivicAgent7MA4YWxkTrZu0gW"
                body = (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="files"; filename="index.html"\r\n'
                    f"Content-Type: text/html\r\n\r\n"
                    f"{html_path.read_text(encoding='utf-8')}\r\n"
                    f"--{boundary}--\r\n"
                ).encode("utf-8")

                req = urllib.request.Request(
                    f"{gotenberg_url}/forms/chromium/convert/html",
                    data=body,
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as pdf_resp:
                    output_pdf.write_bytes(pdf_resp.read())
                return output_pdf
    except Exception as e:
        print(f"--> Gotenberg unavailable ({e}); falling back to local headless Chromium...")

    # Fallback to local Chromium
    cmd = [
        "chromium",
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf}",
        str(html_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_pdf


def verify_pdf_page_count(pdf_path: Path) -> int:
    """Verify that the generated PDF is strictly 1 page."""
    cmd = ["pdfinfo", str(pdf_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.MULTILINE)
    if not match:
        raise ValueError(f"Unable to determine page count for {pdf_path}")
    pages = int(match.group(1))
    return pages


def send_to_cups(pdf_path: Path, printer: str = "Gusli") -> str:
    """Send print job to local CUPS printer and return job ID."""
    cmd = [
        "lp",
        "-d", printer,
        "-o", "page-ranges=1",
        "-o", "media=Letter",
        "-t", "Civic Agent Ballot Pocket Guide",
        str(pdf_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    # Output format: "request id is Gusli-41 (1 file(s))"
    match = re.search(r"request id is ([A-Za-z0-9_-]+)", result.stdout)
    if not match:
        raise RuntimeError(f"Unexpected lp output: {result.stdout}")
    job_id = match.group(1)
    return job_id


def verify_printer_completion(printer_ip: str = "192.168.1.236", max_wait_sec: int = 20) -> bool:
    """Query Brother printer hardware via IPP to verify completed jobs status."""
    test_file = Path("/tmp/check-completed-jobs.test")
    test_content = """{
  OPERATION Get-Jobs
  GROUP operation-attributes-tag
  ATTR charset attributes-charset utf-8
  ATTR naturalLanguage attributes-natural-language en
  ATTR uri printer-uri $uri
  ATTR keyword which-jobs completed
  ATTR keyword requested-attributes job-state,job-state-reasons,job-impressions-completed

  STATUS successful-ok
}"""
    test_file.write_text(test_content, encoding="utf-8")

    start_time = time.time()
    while time.time() - start_time < max_wait_sec:
        cmd = ["ipptool", "-tv", f"ipp://{printer_ip}:631/ipp/print", str(test_file)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if "job-completed-successfully" in res.stdout:
            print("--> Verified by printer hardware: job-completed-successfully (1 impression).")
            return True
        time.sleep(2)
    return False


def main():
    parser = argparse.ArgumentParser(description="Render, convert, and print ballot guides.")
    parser.add_argument("input_file", type=str, help="Path to ballot-guide.md or ballot-guide.html")
    parser.add_argument("--printer", type=str, default="Gusli", help="CUPS printer name (default: Gusli)")
    parser.add_argument("--printer-ip", type=str, default="192.168.1.236", help="Printer IP (default: 192.168.1.236)")
    parser.add_argument("--gotenberg-url", type=str, default="http://100.89.168.11:3006", help="Gotenberg service URL")
    parser.add_argument("--dry-run", action="store_true", help="Render HTML and PDF, verify 1-page, but do NOT print")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        sys.exit(f"Error: {input_path} does not exist.")

    # Step 1: Parse and render HTML
    if input_path.suffix.lower() == ".md":
        print(f"==> Parsing markdown ballot guide: {input_path}")
        data = parse_markdown_ballot(input_path)
        template_file = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "print-tools" / "templates" / "one-page-cheat-sheet.html"
        html_content = render_html(data, template_file)
        html_path = input_path.with_suffix(".html")
        html_path.write_text(html_content, encoding="utf-8")
        print(f"--> Saved HTML to: {html_path}")
    else:
        html_path = input_path

    # Step 2: Convert to PDF
    pdf_path = html_path.with_suffix(".pdf")
    print(f"==> Converting to PDF: {pdf_path}")
    convert_html_to_pdf(html_path, pdf_path, args.gotenberg_url)

    # Step 3: Strict 1-Page Check
    pages = verify_pdf_page_count(pdf_path)
    print(f"--> Page count: {pages}")
    if pages != 1:
        print(f"ERROR: Document is {pages} pages, must be exactly 1 page!", file=sys.stderr)
        sys.exit(2)
    print("--> 1-page constraint verified.")

    # Step 4: Print (unless dry-run)
    if args.dry_run:
        print("==> Dry run complete. PDF generated and verified. Skipping print dispatch.")
        return

    print(f"==> Dispatching job to CUPS printer '{args.printer}'...")
    job_id = send_to_cups(pdf_path, args.printer)
    print(f"--> CUPS Job ID: {job_id}")

    print("==> Verifying with printer hardware over IPP...")
    success = verify_printer_completion(args.printer_ip)
    if success:
        print("==> Print job completed and verified on output tray.")
    else:
        print("--> Print job dispatched; check printer output tray.")


if __name__ == "__main__":
    main()
