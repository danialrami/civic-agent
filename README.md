# Civic Agent

A local civic voting assistant that combines a Python data-fetching tool with an OpenCode AI agent to help you stay informed about elections, candidates, and voting rules in your area.

## Quick Start

### 1. Prerequisites

- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
- **Google Civic Information API Key** - Get one from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- **[OpenCode](https://opencode.ai)** - AI coding assistant (for the civic-researcher agent)

### 2. Setup

```bash
# Clone the repo
git clone git@github.com:danialrami/civic-agent.git
cd civic-agent

# Create your .env file
cp .env.example .env

# Edit .env with your credentials
# CIVIC_ADDRESS=your_address_here (e.g., "123 Main St, San Antonio, TX 78201")
# GOOGLE_CIVIC_API_KEY=your_api_key_here
```

### 3. Fetch Election Data

```bash
# Default: Look 90 days ahead, auto-detect your state
uv run python src/civic_agent/api.py

# See all CLI options
uv run python src/civic_agent/api.py --help

# Target specific election by ID
uv run python src/civic_agent/api.py --election-id 11256

# Look further ahead
uv run python src/civic_agent/api.py --days-ahead 180
```

This generates timestamped data in `output/{YYYYMMDD_HHMMSS}/`:
- `metadata.json` - Election metadata, freshness info, next election
- `elections.json` - Full list of available elections
- `voter_info.json` - Detailed ballot/contest data for target election
- `election_summary.md` - Human-readable summary (used by the AI agent)

### 4. Use the OpenCode Agent

```bash
# Open opencode in this repo
opencode .

# Switch to civic-researcher agent (Tab key)
# Then ask questions like:
# - "What's the next election?"
# - "Tell me about the Senate race"
# - "Who's on my ballot for the runoff?"
```

The agent will:
- Automatically check if election data is stale (>30 days old)
- Auto-refresh by running `uv run python src/civic_agent/api.py`
- Read `metadata.json` and `election_summary.md` to answer your questions
- Use web-search (SearXNG) to research candidates and recent news
- Provide sourced, non-partisan information about elections

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User (You)                              │
│                      │
│  "What's the next election?"                        │
└────────────────────────────┬──────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            OpenCode: civic-researcher.md                    │
│                      │
│  • Mode: primary (switched to directly)              │
│  • Temperature: 0.2 (factual responses)              │
│  • Permissions: read-only (can run api.py only)      │
│                      │
│  Workflow:                                       │
│  1. Get current time (time-tools skill)              │
│  2. Read output/ → find most recent directory        │
│  3. Read metadata.json → check freshness              │
│  4. IF stale (>30 days) → auto-run api.py         │
│  5. Answer using election_summary.md + web-search     │
└────────────────────────────┬──────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Python Tool: src/civic_agent/api.py               │
│                      │
│  • Google Civic API (elections + voter info)       │
│  • Filters future elections (default: 90 days ahead)   │
│  • Generates metadata.json with next_election info      │
│  • Auto-cleans old directories (keeps newest 100)    │
│  • CLI flags: --election-id, --days-ahead, --help  │
└─────────────────────────────────────────────────────────────┘
```

### The OpenCode Agent (`.opencode/agents/civic-researcher.md`)

The agent is a **read-only civic researcher** that helps you understand voting options:

**Capabilities:**
- ✅ Research elections, candidates, voting dates
- ✅ Read election data files (local, no data sent to external AI services)
- ✅ Use web-search (SearXNG) for candidate news and platforms
- ✅ Get current time to determine upcoming vs. past elections
- ✅ Auto-refresh stale data (>30 days old)

**Restrictions:**
- 🚫 Cannot write/edit files (read-only for safety)
- 🚫 Can only run `uv run python src/civic_agent/api.py*` (no other bash commands)
- 🚫 Does not provide legal advice or partisan recommendations

**Autonomous Workflow:**
1. You ask: *"What's the next election?"*
2. Agent checks `metadata.json` from most recent `output/{timestamp}/`
3. If `next_election` is past OR `days_since_generated > 30`:
   - Agent auto-runs `uv run python src/civic_agent/api.py`
   - Waits for completion, re-reads fresh `metadata.json`
4. Answers your question using `election_summary.md` + web-search

### The Python Tool (`src/civic_agent/api.py`)

Fetches election data from the **Google Civic Information API**:

**CLI Flags:**
```bash
# Show all options
uv run python src/civic_agent/api.py --help

# Default behavior
uv run python src/civic_agent/api.py
# - Looks 90 days ahead
# - Auto-detects your state from CIVIC_ADDRESS
# - Targets the closest upcoming election

# Target specific election
uv run python src/civic_agent/api.py --election-id 11256

# Extend look-ahead period
uv run python src/civic_agent/api.py --days-ahead 180

# Force refresh even if data is recent
uv run python src/civic_agent/api.py --force-refresh

# Keep more/fewer timestamped directories
uv run python src/civic_agent/api.py --keep-dirs 50
```

**Output Structure:**
```
output/
└── 20260521_125655/          # Timestamped directory
    ├── metadata.json       # ⭐ START HERE: next election, freshness
    ├── elections.json      # Full election list
    ├── voter_info.json    # Detailed ballot data
    └── election_summary.md # Human-readable (used by agent)
```

**`metadata.json` Format:**
```json
{
  "generated_at": "2026-05-21T12:56:55",
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

---

## Documentation

Comprehensive guides in `docs/`:

| Document | Description |
|----------|-------------|
| `docs/01-problem.md` | The friction of local voting and why it matters |
| `docs/02-past-solutions.md` | Past solutions and why they failed |
| `docs/03-why-failed.md` | Why pull-based systems don't work |
| `docs/04-our-solution.md` | Push-based approach with AI researcher |
| `docs/05-implementation.md` | Technical implementation details |
| `docs/06-troubleshooting.md` | Common issues and solutions |

---

## Example Usage

### Short-Term (Data Fresh, <7 Days Old)

```
User: "What's the next election?"

Civic Researcher:
  The next election is **Texas Democratic Primary Runoff** on May 26, 2026 (5 days away).
  
  According to my data (generated today), you have several contests:
  - U.S. Senate: John Cornyn vs. Ken Paxton (Republican)
  - Attorney General: Mayes Middleton vs. Chip Roy (Republican)
  - Lieutenant Governor: Vikki Goodwin vs. Marcos Vélez (Democratic)
  
  Early voting runs May 18-22. Election Day is May 26, 7 AM - 7 PM.
  
  [Searches web for latest poll results...]
  Recent polls show Paxton leading Cornyn 48% to 45% (University of Houston, May 5).
```

### Long-Term (Data Stale, >30 Days Old)

```
User: "What's the next election?" (in June, after May 26 passed)

Civic Researcher:
  Let me check my election data...
  [Reads metadata.json - sees May 26 is PAST, days_since_generated = 35]
  
  My data is 35 days old and May 26 has passed. Refreshing now...
  [Auto-runs: uv run python src/civic_agent/api.py]
  
  [Re-reads new metadata.json]
  The next election is **District of Columbia Primary** on June 16, 2026 (12 days away).
```

---

## Project Structure

```
civic-agent/
├── .opencode/agents/
│   └── civic-researcher.md    # OpenCode agent definition
├── .env.example              # Template for API key + address
├── output/                   # Timestamped election data (gitignored)
├── src/civic_agent/
│   ├── __init__.py
│   ├── api.py               # Google Civic API client (v2)
│   └── calendar.py          # Optional .ics generator (placeholder)
├── tests/
│   └── test_api.py
├── docs/                     # Comprehensive documentation
│   ├── 01-problem.md
│   ├── 02-past-solutions.md
│   ├── 03-why-failed.md
│   ├── 04-our-solution.md
│   ├── 05-implementation.md
│   └── 06-troubleshooting.md
└── pyproject.toml
```

---

## Git Info

**Tracked (will be pushed):**
- `.opencode/agents/civic-researcher.md` (agent definition)
- `src/civic_agent/` (Python source)
- `tests/` (test files)
- `docs/` (documentation, except `opencode-sessions/` and `gemini/`)
- `.env.example` (template)

**Gitignored (NOT pushed):**
- `.env` (personal API key + address)
- `output/` (election data with personal address)
- `docs/opencode-sessions/` (session transcripts)
- `docs/gemini/` (chat exports)
- `.venv/` (virtual environment)

---

## Troubleshooting

### API Key Issues
1. Get an API key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Enable "Civic Information API" in your project
3. Create credentials → API Key (not OAuth)
4. Copy `.env.example` to `.env` and fill in your values

### Agent Not working
1. Verify agent file is at `.opencode/agents/civic-researcher.md`
2. Check permissions: agent can only run `uv run python src/civic_agent/api.py*`
3. Restart OpenCode to reload agent definitions

### Full troubleshooting guide: `docs/06-troubleshooting.md`

---

## License

[MIT License](LICENSE) (or specify your preferred license)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Acknowledgments

- [Google Civic Information API](https://developers.google.com/civic-information/) for election data
- [OpenCode](https://opencode.ai) for the agent framework
- [opencode-agent-definitions](https://github.com/anomalyco/opencode-agent-definitions) for agent creation guides
