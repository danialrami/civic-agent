"""
Tests for the Google Civic API client.
"""

from datetime import date, timedelta
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from civic_agent.api import load_env, save_election_data


def test_load_env_missing_values(monkeypatch):
    """Test that load_env raises errors when env vars are not set."""
    monkeypatch.delenv("CIVIC_ADDRESS", raising=False)
    monkeypatch.delenv("GOOGLE_CIVIC_API_KEY", raising=False)
    
    # Mock load_dotenv in civic_agent.api to avoid reading the real .env file
    with patch("civic_agent.api.load_dotenv"):
        with pytest.raises(ValueError):
            load_env()


def test_save_election_data(tmp_path):
    """Test that election data is saved correctly to timestamped directory."""
    elections = [
        {"id": "1234", "name": "Primary Election", "electionDay": "2026-05-26"}
    ]
    voter_info = {"contests": [{"office": "U.S. Senate"}]}
    
    output_dir = str(tmp_path / "test_output")
    result_path = save_election_data(elections, voter_info, output_dir)
    
    # Check that files were created
    assert (result_path / "elections.json").exists()
    assert (result_path / "voter_info.json").exists()
    assert (result_path / "election_summary.md").exists()
    
    # Check content
    with open(result_path / "elections.json", "r") as f:
        saved_elections = json.load(f)
    assert saved_elections == elections


def test_save_election_data_creates_summary(tmp_path):
    """Test that the summary markdown file contains expected content."""
    future_date = (date.today() + timedelta(days=14)).isoformat()
    elections = [
        {"id": "1234", "name": "Primary Election", "electionDay": future_date}
    ]
    voter_info = {"contests": [{"office": "U.S. Senate"}]}
    
    output_dir = str(tmp_path / "test_output")
    result_path = save_election_data(elections, voter_info, output_dir)
    
    with open(result_path / "election_summary.md", "r") as f:
        content = f.read()
    
    assert "Election Data Summary" in content
    assert "Primary Election" in content
    assert future_date in content
