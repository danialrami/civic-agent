"""
Google Civic Information API client for retrieving election data.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def load_env() -> tuple[str, str]:
    """Load address and API key from .env file."""
    from dotenv import load_dotenv
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
    
    body = {"address": address}
    if election_id:
        body["electionId"] = election_id
    
    try:
        result = service.elections().voterInfoQuery(body=body).execute()
        return result
    except HttpError as e:
        raise RuntimeError(f"Failed to fetch voter info: {e}")


def save_election_data(elections: list[dict], voter_info: dict, output_dir: Optional[str] = None) -> Path:
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
    
    # Create a summary markdown file for the OpenCode agent to read
    summary_file = output_path / "election_summary.md"
    with open(summary_file, "w") as f:
        f.write(f"# Election Data Summary\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write(f"## Elections\n\n")
        for election in elections:
            f.write(f"- **{election.get('name', 'Unknown')}**\n")
            f.write(f"  - Date: {election.get('electionDay', 'N/A')}\n")
            f.write(f"  - ID: {election.get('id', 'N/A')}\n\n")
        
        if voter_info.get("contests"):
            f.write(f"## Contests on Ballot\n\n")
            for contest in voter_info["contests"]:
                f.write(f"- {contest.get('office', contest.get('type', 'Unknown'))}\n")
    
    return output_path


def main():
    """Main entry point for CLI usage."""
    try:
        address, api_key = load_env()
        
        print(f"Fetching elections for address: {address}")
        elections = get_elections(api_key)
        
        if not elections:
            print("No upcoming elections found.")
            return
        
        print(f"Found {len(elections)} election(s)")
        
        # Get voter info for the first upcoming election
        # TODO: User may want to specify which election or get all
        first_election = elections[0]
        voter_info = get_voter_info(api_key, address, first_election["id"])
        
        output_path = save_election_data(elections, voter_info)
        print(f"Election data saved to: {output_path}")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please copy .env.example to .env and fill in your values.")
    except RuntimeError as e:
        print(f"API error: {e}")


if __name__ == "__main__":
    main()
