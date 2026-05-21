# How We Are Building It (Implementation Plan)

This document outlines the technical implementation steps for the Civic Agent project.

## Step 1: Project Initialization

### Package Manager: `uv`
We use `uv` for fast Python dependency management:
```bash
uv init --python 3.12
uv add google-api-python-client pytest
uv add --dev pytest
```

### Project Structure
```
civic-agent/
├── .opencode/agents/        # OpenCode agent definitions (committed)
│   └── civic-researcher.md
├── .env                      # Personal data (gitignored)
├── .env.example              # Template for required env vars
├── .gitignore
├── output/                   # Timestamped election data (gitignored)
│   └── 20260521_120000/    # Example timestamped folder
│       ├── elections.json
│       ├── voter_info.json
│       └── election_summary.md
├── src/civic_agent/
│   ├── __init__.py
│   ├── api.py               # Google Civic API client
│   └── calendar.py          # Optional .ics generator
├── tests/
│   └── test_api.py
├── docs/                     # Comprehensive documentation
│   ├── 01-problem.md
│   ├── 02-past-solutions.md
│   ├── 03-why-failed.md
│   ├── 04-our-solution.md
│   ├── 05-implementation.md (this file)
│   └── 06-troubleshooting.md
└── pyproject.toml
```

---

## Step 2: Google Civic API Integration

### Authentication
- **API Key only** (no OAuth needed for public election data)
- Store key in `.env` as `GOOGLE_CIVIC_API_KEY`
- Address stored in `.env` as `CIVIC_ADDRESS`

### API Endpoints Used
1. **Elections Query** (`/civicinfo/v2/elections?key=API_KEY`)
   - Returns list of available elections with IDs and dates
2. **Voter Info Query** (`/civicinfo/v2/voterinfo?key=API_KEY&address=...&electionId=...`)
   - Returns detailed ballot information for a specific election and address

### Python Implementation (`src/civic_agent/api.py`)
```python
from googleapiclient.discovery import build

# Build service with API key (not OAuth)
service = build("civicinfo", "v2", developerKey=api_key)

# Get elections
result = service.elections().electionQuery().execute()

# Get voter info for specific election
voter_info = service.elections().voterInfoQuery(
    body={"address": address, "electionId": election_id}
).execute()
```

---

## Step 3: Timestamped Output Structure

Election data is saved to `output/{timestamp}/` directories:

- **Format**: `YYYYMMDD_HHMMSS` (e.g., `20260521_143022`)
- **Files generated**:
  - `elections.json` - List of available elections
  - `voter_info.json` - Detailed ballot/contest data
  - `election_summary.md` - Human-readable summary for the OpenCode agent

This allows:
- **Historical tracking**: See what was on your ballot in past elections
- **Change detection**: Compare election data over time
- **Agent readability**: The `.md` summary is easy for the AI to parse

---

## Step 4: OpenCode Agent Definition

### Location
Project-specific: `.opencode/agents/civic-researcher.md`

### Key Configuration
```yaml
---
description: Civic voting researcher. Use for election info, candidate research...
mode: primary
temperature: 0.2
permission:
  read: allow
  edit: deny
  write: deny
  bash: deny
  skill: allow      # For web-search (SearXNG)
  webfetch: allow   # For reading candidate websites
---
```

### Agent Workflow
1. Check current time (using time-tools skill)
2. Find most recent `output/{timestamp}/` directory
3. Read `election_summary.md` for quick overview
4. Use web-search skill for candidate news/research
5. Cite sources in responses

---

## Step 5: Testing Strategy

### Unit Tests (`tests/test_api.py`)
- Mock API responses to avoid real API calls during testing
- Test JSON parsing and file output
- Test timestamped directory creation

### Manual Testing
1. **Python tool**: `uv run python src/civic_agent/api.py`
2. **OpenCode agent**: Switch to `civic-researcher` and ask: "What's on my ballot for the next election?"
3. **Verify read-only**: Attempt to edit a file (should be denied)

---

## Step 6: Git Setup

### Files to Commit
- `.opencode/agents/civic-researcher.md` (agent definition)
- `src/civic_agent/` (Python source)
- `tests/` (test files)
- `docs/` (documentation)
- `.env.example` (template)
- `.gitignore`

### Files to Gitignore
- `.env` (personal data)
- `output/` (election data, contains personal address)
- `.venv/` (virtual environment)
- `__pycache__/`

---

## Future Enhancements (Not in Initial Scope)

- **.ics Calendar Generator**: Parse election dates and create calendar events
- **Push Notifications**: Integrate with system notifications
- **Candidate Database**: Build a local cache of candidate info with sources
- **Multi-address Support**: Track elections for multiple addresses (e.g., work + home)
