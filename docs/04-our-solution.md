# Why What We're Doing is Different

The Civic Agent project takes a fundamentally different approach: **push-based, personalized, AI-enhanced civic information** that integrates directly into the voter's daily workflow.

## The Push-Based Model

Instead of requiring voters to remember to check for elections, we **push** election information to them:

1. **Google Civic API**: Official election data is fetched automatically based on the voter's address
2. **Calendar Integration**: Election dates are exported as `.ics` files that sync to Google Calendar, Apple Calendar, or Outlook
3. **Automatic Reminders**: Once in a calendar system, the voter gets their normal notifications (1 week before, 1 day before, etc.)
4. **Timestamped History**: Election data is saved in timestamped folders (`output/20260521_120000/`), building a personal archive of elections over time

## Hyper-Local Personalization

The Google Civic API provides election data specific to an exact address:
- **Your specific ballot**: Not a generic "Texas Senate" race, but "Texas Senate District 25" with your specific candidates
- **Open primary awareness**: The AI researcher can explain that you can choose which party's primary to vote in
- **Runoff tracking**: Automatically detects if a race went to runoff and adds that date
- **Local propositions**: Includes city charter amendments, school bond issues, and county measures

## AI-Enhanced Research (The Civic Researcher Agent)

Unlike static websites, the OpenCode Civic Researcher agent:
- **Researches candidates on demand**: "Tell me about John Cornyn's recent voting record" triggers a web search
- **Summarizes platforms**: Pulls from multiple sources (candidate websites, Ballotpedia, recent news)
- **Explains voting rules**: "Can I vote in the runoff if I missed the primary?" → Yes, in Texas you can
- **Cites sources**: Always provides links to original information
- **Read-only safety**: The agent cannot modify files or execute code—it's purely a research tool

## Personal Workflow Integration

The project fits into existing workflows:
1. **Calendar**: `.ics` files import to any calendar app → automatic notifications
2. **Terminal**: Run `uv run python src/civic_agent/api.py` to refresh election data
3. **OpenCode**: Switch to `civic-researcher` agent to ask questions about elections/candidates
4. **Git-tracked**: Election data is timestamped and stored in `output/`, building a history over time

## The Time Dimension

By timestamping all election data outputs:
- **Historical record**: Look back at what was on your ballot in previous elections
- **Change tracking**: See how your district boundaries change over time
- **Participation tracking**: Know which elections you actually voted in vs. missed

## Privacy by Design

- **Personal data in `.env`**: Address and API keys are gitignored, never committed
- **Read-only agent**: The Civic Researcher cannot access system files or execute code
- **Local-first**: Election data is fetched and stored locally, not sent to third-party AI services (the agent runs locally via OpenCode)

## Summary of Differences

| Feature | Past Solutions | Civic Agent |
|---------|---------------|-------------|
| Model | Pull (you check) | Push (calendar notifications) |
| Personalization | Generic / Manual entry | Automatic from address |
| Candidate Research | Static pages | AI-enhanced, on-demand |
| Calendar Integration | None | `.ics` export |
| Local Nuance | Often missed | Hyper-local via Google Civic API |
| History Tracking | None | Timestamped output folders |
| Privacy | Varies | Local-first, `.env` for personal data |
| Workflow Integration | Separate website | Part of daily tools (calendar, terminal) |
