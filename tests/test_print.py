"""
Tests for print_ballot module.
"""

from pathlib import Path
from civic_agent.print_ballot import parse_markdown_ballot, render_html


def test_parse_markdown_ballot(tmp_path):
    md_content = """# Pocket Ballot Guide: November 3, 2026

**Polling Location:** Hatchett Elementary School
**Voting Hours:** 7:00 AM – 7:00 PM
**Precinct:** 1158

---

| Office / Proposition | Candidates / Options | My Selection |
| :--- | :--- | :--- |
| **U.S. Senate** | [ ] Ken Paxton (R)<br>[X] James Talarico (D) | **James Talarico (D)** |
| **Texas Governor** | [ ] Greg Abbott (R)<br>[X] Gina Hinojosa (D) | **Gina Hinojosa (D)** |
"""
    test_md = tmp_path / "test_ballot.md"
    test_md.write_text(md_content, encoding="utf-8")

    parsed = parse_markdown_ballot(test_md)
    assert "Pocket Ballot Guide" in parsed["title"]
    assert "Hatchett Elementary" in parsed["location"]
    assert "1158" in parsed["precinct"]
    assert len(parsed["rows"]) == 2
    assert "James Talarico" in parsed["rows"][0]["selection"]


def test_render_html_contains_required_elements():
    data = {
        "title": "My Ballot Guide",
        "location": "Vote Center 1",
        "hours": "7 AM - 7 PM",
        "precinct": "1158",
        "rows": [
            {
                "contest": "**U.S. Senate**",
                "options": "Candidate A &bull; Candidate B",
                "selection": "**Candidate B**"
            }
        ]
    }
    html = render_html(data)
    assert "My Ballot Guide" in html
    assert "Vote Center 1" in html
    assert "U.S. Senate" in html
    assert "Candidate B" in html
    assert "@page" in html
