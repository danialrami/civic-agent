# How We Are Building It (Implementation Plan)

This document outlines the technical implementation steps for the Civic Agent project.

## Step 1: Project Initialization

### Package Manager: `uv`
We use `uv` for fast Python dependency management:
```bash
uv init --python 3.12
uv add google-api-python-client python-dotenv pytest
uv add --dev pytest
```

### Project Structure
```
civic-agent/
├── .opencode/agents/        # OpenCode agent definitions (committed)
│   └── civic-researcher.md
├── .env                      # Personal data (gitignored)
├── .env.example              # Template for required env vars
├── output/                   # Timestamped election data (gitignored)
│   └── 20260521_125655/     # Example timestamped folder
│       ├── metadata.json      # NEW: election metadata + freshness info
│       ├── elections.json
│       ├── voter_info.json
│       └── election_summary.md
├── src/civic_agent/
│   ├── __init__.py
│   ├── api.py               # Google Civic API client (v2 with CLI flags)
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

## Step 2: Google Civic API Integration (v2)

### Authentication
- **API Key only** (no OAuth needed for public election data)
- Store key in `.env` as `GOOGLE_CIVIC_API_KEY`
- Address stored in `.env` as `CIVIC_ADDRESS`

### CLI Flags (New in v2)
```bash
# Default: 90 days ahead, auto-detect state
uv run python src/civic_agent/api.py

# Target specific election
uv run python src/civic_agent/api.py --election-id 11256

# Look up to 90 days ahead
uv run python src/civic_agent/api.py --days-ahead 90

# Force refresh even if data is recent
uv run python src/civic_agent/api.py --force-refresh

# Show detailed help
uv run python src/civic_agent/api.py --help
```

### API Endpoints Used
1. **Elections Query** (`/civicinfo/v2/elections?key=API_KEY`)
   - Returns list of available elections with IDs and dates
2. **Voter Info Query** (`/civicinfo/v2/voterinfo?key=API_KEY&address=...&electionId=...`)
   - Returns detailed ballot information for a specific election and address

### New Features in v2
- **Filter past elections**: Only shows elections within `--days-ahead` (default: 90)
- **Sort by date**: Closest election first
- **Generate `metadata.json`**: Includes freshness info, CLI command used, next election
- **Auto-cleanup**: Keeps only newest 100 timestamped directories (configurable via `--keep-dirs`)
- **State auto-detection**: Finds elections matching user's state from address

---

## Step 3: metadata.json Format (New)

Generated in each timestamped directory:

```json
{
  "generated_at": "2026-05-21T12:56:55.441727",
  "generated_at_human": "May 21, 2026 at 12:56 PM",
  "days_since_generated": 0,
  "cli_command": "uv run python src/civic_agent/api.py",
  "upcoming_elections": [
    {"name": "Texas Democratic Primary Runoff", "date": "2026-05-26", "id": "11098", "days_until": 5}
  ],
  "next_election": {
    "name": "Texas Democratic Primary Runoff",
    "date": "2026-05-26",
    "id": "11098",
    "days_until": 5
  }
}
```

The agent reads `metadata.json` FIRST to:
- Check if data is stale (`days_since_generated` > 30)
- Find the next election (`next_election`)
- Know what CLI command was used (for reproducibility)

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
  bash:
    "uv run python src/civic_agent/api.py*": allow  # ONLY this command
    "*": deny
  skill: allow      # For web-search (SearXNG)
  webfetch: allow   # For reading candidate websites
---
```

### Autonomous Workflow (New)
When user asks "What's the next election?":

1. **Get current time** (time-tools skill)
2. **Read `output/` directory** → find most recent timestamped dir
3. **Read `metadata.json`** from that directory:
   - If `next_election.date` is in the past OR `days_since_generated` > 30:
     - **AUTOMATICALLY RUN**: `uv run python src/civic_agent/api.py`
     - Wait for completion, re-read `metadata.json`
   - Otherwise, use existing data
4. **Answer the question** using `election_summary.md` + web-search

---

## Step 5: Testing Strategy

### Unit Tests (`tests/test_api.py`)
- Mock API responses to avoid real API calls during testing
- Test JSON parsing and file output
- Test timestamped directory creation
- Test `metadata.json` generation

### Manual Testing
1. **Python tool**: `uv run python src/civic_agent/api.py`
2. **OpenCode agent**: Switch to `civic-researcher` and ask: "What's the next election?"
3. **Verify autonomous refresh**: Wait until data is 30+ days old, ask again - agent should auto-run api.py
4. **Verify read-only**: Attempt to edit a file (should be denied)

---

## Step 6: Git Setup

### Files to Commit
- `.opencode/agents/civic-researcher.md` (agent definition)
- `src/civic_agent/` (Python source v2 with CLI flags)
- `tests/` (test files)
- `docs/` (documentation)
- `.env.example` (template)
- `.gitignore`

### Files to Gitignore
- `.env` (personal data)
- `output/` (election data, contains personal address)
- `output/` (election data, contains personal address)
- `.venv/` (virtual environment)
- `__pycache__/`

---

## Future Enhancements (Not in Initial Scope)

- **.ics Calendar Generator**: Parse election dates and create calendar events
- **Push Notifications**: Integrate with system notifications
- **Candidate Database**: Build a local cache of candidate info with sources
- **Multi-address Support**: Track elections for multiple addresses (e.g., work + home)
- **Agent Auto-refresh Cron**: Schedule periodic `api.py` runs via system cron

