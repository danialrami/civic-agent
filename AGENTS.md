# Agent Integration & Architecture Guide — `civic-agent`

> Operational guidelines, architectural contracts, and verification commands for AI coding agents.

`civic-agent` is a local civic voting assistant and election data retrieval system. It combines a deterministic Python CLI pipeline with autonomous AI research workflows to overcome voter friction and inform citizens about upcoming elections, ballot contests, candidates, and local voting rules.

---

## 1. Architecture & Core Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    User / Coding Agent                      │
│                              │                              │
│              "What's on my upcoming ballot?"                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Autonomous Agent Layer                      │
│                                                             │
│  • Agent Skill: .agents/skills/civic-researcher/SKILL.md    │
│  • OpenCode Persona: .opencode/agents/civic-researcher.md   │
│                                                             │
│  Decision Loop:                                             │
│  1. Check current time (time-tools skill)                   │
│  2. Read latest output/*/metadata.json                      │
│  3. IF days_since_generated > 30 OR next_election is past:  │
│        Auto-execute: uv run python src/civic_agent/api.py   │
│  4. Ground answers with election_summary.md + web search   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Deterministic Python Data Pipeline             │
│                                                             │
│  • src/civic_agent/api.py: Google Civic Information API     │
│  • src/civic_agent/calendar.py: .ics export generator       │
│  • Stores runs in timestamped output/YYYYMMDD_HHMMSS/       │
└─────────────────────────────────────────────────────────────┘
```

### The Pipeline Artifacts (`output/<timestamp>/`)
Every run of `uv run python src/civic_agent/api.py` outputs four artifacts into a timestamped directory:

1. **`metadata.json` (Primary Coordination Manifest)**:
   Contains freshness indicators, generation timestamp, and the `next_election` object:
   ```json
   {
     "generated_at": "2026-11-02T19:59:00.486964",
     "generated_at_human": "November 02, 2026 at 07:59 PM",
     "days_since_generated": 0,
     "cli_command": "uv run python src/civic_agent/api.py",
     "upcoming_elections": [
       {"name": "2026 General Midterm Election", "date": "2026-11-03", "id": "12000", "days_until": 1}
     ],
     "next_election": {
       "name": "2026 General Midterm Election",
       "date": "2026-11-03",
       "id": "12000",
       "days_until": 1
     }
   }
   ```
2. **`elections.json`**: Raw list of elections returned from Google Civic API.
3. **`voter_info.json`**: Detailed ballot data: contests, candidates, early voting sites, and polling places.
4. **`election_summary.md`**: Clean human and LLM-readable overview of upcoming contests and dates.

### The Deliberation Workspace (`elections/<YYYY-MM-DD>_<slug>/`)
To bridge the gap between raw data collection and the physical voting booth, candidate research and voter decisions are banked into date-versioned folders under `elections/`:

- **`research-dossier.md`**: Neutral, cited breakdown of every race, candidate platform, track record, and proposition.
- **`ballot-guide.md`**: Single-page, printable pocket cheat sheet designed to be taken into voting booths where cell phones are prohibited by state law.
- **`voter-decisions.md`**: Voter-maintained decision log tracking individual policy priorities, candidate leanings, and voting rationales.
- **`polling-consensus.md`**: Post-deliberation landscape analysis comparing reputable independent polling and consensus projections across chosen candidates.

### Two-Phase Deliberation & Repeatable Search Protocol
To ensure voter decisions are rooted in personal values rather than herd mentality or horse-race media narratives:
1. **Phase 1: Values-First (Blind) Deliberation**:
   - Always explain the constitutional/statutory powers of the office first.
   - Present candidate track records and policy platforms neutrally without polling bias.
   - Lock in user preferences across the ballot based on merits.
2. **Phase 2: Post-Selection Polling & Consensus Deep Dive**:
   - Only *after* the ballot selections are made, execute a structured multi-source polling query.
   - Repeatable search method: Query non-partisan academic and gold-standard pollsters (e.g., Texas Politics Project / UT Austin, Hobby School / UH, Marist, Emerson, YouGov), cross-referenced with local journalistic aggregates (Texas Tribune, San Antonio Report).
   - Document projected margins, turnout variables, and consensus outlook in `polling-consensus.md`.

---

## 2. Core Rules for AI Agents

1. **Check Freshness First**:
   Always read the latest `output/<timestamp>/metadata.json` before answering questions about upcoming elections. If the data is older than 30 days (`days_since_generated > 30`) or the `next_election.date` is in the past, run `uv run python src/civic_agent/api.py` to fetch fresh data.
2. **Deterministic & Sourced Claims**:
   Never guess or hallucinate election dates, registration deadlines, or ballot candidates. Ground all election dates in `output/` artifacts and verify candidate stances with reputable web search citations.
3. **Strict Non-Partisanship**:
   Summarize candidate backgrounds, platforms, and policy positions neutrally and factually. Do not make partisan endorsements or give formal legal advice.
4. **Read-Only Safety**:
   Do not modify, overwrite, or delete historical `output/` directories by hand. Let `api.py` manage directory pruning (`--keep-dirs`, default 100).
5. **Contract Verification Before Handoff**:
   Always verify changes against the test suite (`uv run pytest`) before concluding a task.

---

## 3. Essential Commands

```bash
# Run unit tests
uv run pytest

# Run election data retrieval pipeline (default: 90 days ahead)
uv run python src/civic_agent/api.py

# Query a custom look-ahead window (e.g. 180 days)
uv run python src/civic_agent/api.py --days-ahead 180

# Query a specific Google election ID
uv run python src/civic_agent/api.py --election-id 12000

# Force data refresh
uv run python src/civic_agent/api.py --force-refresh
```

---

## 4. Agent Definitions & Parity

This repository provides dual-layer agent support for maximum compatibility:

- **Agnostic Skill (`.agents/skills/civic-researcher/SKILL.md`)**:
  Follows the open [Agent Skills specification](https://agentskills.io). Automatically discovered and loaded by **pi**, **Claude Code**, **OpenCode**, and **Codex**. Can be explicitly triggered via `/skill:civic-researcher`.
- **OpenCode Persona (`.opencode/agents/civic-researcher.md`)**:
  Provides a native primary persona when running `opencode .` in the repository, locking down the harness environment with read-only permissions and gating bash execution strictly to `uv run python src/civic_agent/api.py*`.
