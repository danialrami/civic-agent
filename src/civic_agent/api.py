"""
Google Civic Information API client for retrieving election data.
Usage:
    uv run python src/civic_agent/api.py                    # Default: 90 days ahead, auto-detect state
    uv run python src/civic_agent/api.py --election-id 11256   # Target specific election
    uv run python src/civic_agent/api.py --days-ahead 90        # Look up to 90 days ahead
    uv run python src/civic_agent/api.py --help                 # Show detailed help
"""

import os
import json
import argparse
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Google Civic Information API client for retrieving election data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python src/civic_agent/api.py                    # Default: 90 days ahead, auto-detect state
  uv run python src/civic_agent/api.py --election-id 11256   # Target specific election
  uv run python src/civic_agent/api.py --days-ahead 90        # Look up to 90 days ahead
  uv run python src/civic_agent/api.py --help                  # Show this help message
"""
    )
    parser.add_argument(
        "--election-id",
        type=str,
        default=None,
        help="Target specific election ID (e.g., '11256' for Texas GOP runoff)"
    )
    parser.add_argument(
        "--days-ahead",
        type=int,
        default=90,
        help="How many days ahead to look for elections (default: 90)"
    )
    parser.add_argument(
        "--keep-dirs",
        type=int,
        default=100,
        help="Number of most recent timestamped directories to keep (default: 100)"
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force refresh even if data is recent"
    )
    return parser.parse_args()


def load_env():
    """Load address and API key from .env file."""
    load_dotenv()
    
    address = os.getenv("CIVIC_ADDRESS", "")
    api_key = os.getenv("GOOGLE_CIVIC_API_KEY", "")
    
    if not address or address == "your_address_here":
        raise ValueError("CIVIC_ADDRESS not set in .env file")
    if not api_key or api_key == "your_api_key_here":
        raise ValueError("GOOGLE_CIVIC_API_KEY not set in .env file")
    
    return address, api_key


def get_elections(api_key: str) -> list[dict]:
    """Fetch available elections from Google Civic API."""
    service = build("civicinfo", "v2", developerKey=api_key)
    
    try:
        result = service.elections().electionQuery().execute()
        return result.get("elections", [])
    except HttpError as e:
        raise RuntimeError(f"Failed to fetch elections: {e}")


def get_voter_info(api_key: str, address: str, election_id: Optional[str] = None) -> dict:
    """Fetch detailed voter information for a specific election and address."""
    service = build("civicinfo", "v2", developerKey=api_key)
    
    params = {"address": address}
    if election_id:
        params["electionId"] = election_id
    
    try:
        result = service.elections().voterInfoQuery(**params).execute()
        return result
    except HttpError as e:
        raise RuntimeError(f"Failed to fetch voter info: {e}")


def filter_future_elections(elections: list[dict], days_ahead: int = 90) -> list[dict]:
    """Filter to elections within `days_ahead` days from now, sort by date."""
    today = date.today()
    cutoff = date(today.year, today.month, today.day)
    max_date = date.fromordinal(cutoff.toordinal() + days_ahead)
    
    future = []
    for election in elections:
        if election.get("id") == "2000":  # Skip VIP test election
            continue
        try:
            election_date = date.fromisoformat(election.get("electionDay", ""))
            if cutoff <= election_date <= max_date:
                future.append(election)
        except ValueError:
            continue  # Skip invalid dates
    
    # Sort by date (closest first)
    future.sort(key=lambda x: date.fromisoformat(x.get("electionDay", "9999-12-31")))
    return future


def save_election_data(elections: list[dict], voter_info: dict, output_dir: Optional[str] = None, cli_command: Optional[str] = None) -> Path:
    """Save election data to a timestamped output directory."""
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"output/{timestamp}"
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save elections list
    elections_file = output_path / "elections.json"
    with open(elections_file, "w") as f:
        json.dump(elections, f, indent=2)
    
    # Save detailed voter info
    voter_info_file = output_path / "voter_info.json"
    with open(voter_info_file, "w") as f:
        json.dump(voter_info, f, indent=2)
    
    # Create metadata.json
    today = date.today()
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "generated_at_human": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "days_since_generated": 0,
        "cli_command": cli_command or "uv run python src/civic_agent/api.py",
        "upcoming_elections": []
    }
    
    # Build upcoming elections list with days_until
    for election in elections:
        try:
            election_date = date.fromisoformat(election.get("electionDay", ""))
            days_until = (election_date - today).days
            if days_until >= 0:
                metadata["upcoming_elections"].append({
                    "name": election.get("name", "Unknown"),
                    "date": election.get("electionDay", ""),
                    "id": election.get("id", ""),
                    "days_until": days_until
                })
        except ValueError:
            continue
    
    # Sort by days_until
    metadata["upcoming_elections"].sort(key=lambda x: x["days_until"])
    
    # Set next_election (closest)
    if metadata["upcoming_elections"]:
        metadata["next_election"] = metadata["upcoming_elections"][0]
    
    metadata_file = output_path / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Create a summary markdown file for the OpenCode agent to read
    summary_file = output_path / "election_summary.md"
    with open(summary_file, "w") as f:
        f.write(f"# Election Data Summary\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        
        if metadata.get("next_election"):
            next_e = metadata["next_election"]
            f.write(f"**NEXT ELECTION: {next_e['name']}** on {next_e['date']} ({next_e['days_until']} days away)\n\n")
        
        f.write(f"## Upcoming Elections (next {len(metadata['upcoming_elections'])})\n\n")
        for e in metadata["upcoming_elections"]:
            f.write(f"- **{e['name']}**\n")
            f.write(f"  - Date: {e['date']} ({e['days_until']} days away)\n")
            f.write(f"  - ID: {e['id']}\n\n")
        
        if voter_info.get("contests"):
            f.write(f"## Contests on Ballot\n\n")
            for contest in voter_info["contests"]:
                f.write(f"- {contest.get('office', contest.get('type', 'Unknown'))}\n")
    
    return output_path


def cleanup_old_directories(keep: int = 100):
    """Remove oldest timestamped directories, keeping only the `keep` most recent."""
    output_base = Path("output")
    if not output_base.exists():
        return
    
    # Find all timestamped directories
    dirs = []
    for d in output_base.iterdir():
        if d.is_dir() and len(d.name) == 15 and d.name[8] == "_":
            try:
                # Parse: 20260521_123230 -> 2026-05-21 12:32:30
                name = d.name
                year = int(name[0:4])
                month = int(name[4:6])
                day = int(name[6:8])
                hour = int(name[9:11])
                minute = int(name[11:13])
                second = int(name[13:15])
                dt = datetime(year, month, day, hour, minute, second)
                dirs.append((dt, d))
            except (ValueError, IndexError):
                continue
    
    # Sort by timestamp (newest first)
    dirs.sort(key=lambda x: x[0], reverse=True)
    
    # Remove directories beyond `keep`
    removed = 0
    for i, (dt, d) in enumerate(dirs):
        if i >= keep:
            import shutil
            shutil.rmtree(d)
            removed += 1
    
    if removed > 0:
        print(f"Cleaned up {removed} old timestamped directories (kept newest {keep})")


def main():
    """Main entry point for CLI usage."""
    args = parse_args()
    
    try:
        address, api_key = load_env()
        
        print(f"Fetching elections for address: {address}")
        print(f"Looking {args.days_ahead} days ahead...")
        
        elections = get_elections(api_key)
        
        if not elections:
            print("No elections found from API.")
            return
        
        print(f"API returned {len(elections)} total election(s)")
        
        # Filter to future elections within days_ahead
        future_elections = filter_future_elections(elections, args.days_ahead)
        
        if not future_elections:
            print(f"No elections found within {args.days_ahead} days.")
            return
        
        print(f"Found {len(future_elections)} upcoming election(s) within {args.days_ahead} days")
        
        # Determine target election
        if args.election_id:
            # User specified a specific election
            target_election = None
            for e in future_elections + elections:  # Check both future and all
                if str(e.get("id")) == str(args.election_id):
                    target_election = e
                    break
            if not target_election:
                raise ValueError(f"Election ID {args.election_id} not found")
        else:
            # Auto-detect: find election for user's state
            state = address.split(",")[-1].strip()[:2] if "," in address else None
            target_election = None
            
            for election in future_elections:
                ocd_id = election.get("ocdDivisionId", "")
                if state and f"state:{state.lower()}" in ocd_id:
                    target_election = election
                    break
            
            if not target_election and future_elections:
                target_election = future_elections[0]  # Closest election
        
        print(f"Fetching voter info for: {target_election['name']}")
        voter_info = get_voter_info(api_key, address, target_election["id"])
        
        # Build CLI command for metadata
        cli_parts = ["uv", "run", "python", "src/civic_agent/api.py"]
        if args.election_id:
            cli_parts.extend(["--election-id", args.election_id])
        if args.days_ahead != 90:
            cli_parts.extend(["--days-ahead", str(args.days_ahead)])
        cli_command = " ".join(cli_parts)
        
        output_path = save_election_data(future_elections, voter_info, cli_command=cli_command)
        
        # Cleanup old directories
        cleanup_old_directories(args.keep_dirs)
        
        print(f"Election data saved to: {output_path}")
        print(f"Next election: {target_election['name']} on {target_election['electionDay']}")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please copy .env.example to .env and fill in your values.")
    except RuntimeError as e:
        print(f"API error: {e}")


if __name__ == "__main__":
    main()
