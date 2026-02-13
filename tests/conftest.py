"""Shared fixtures for tests — sample DataFrames mimicking real Spotify data."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest


def _make_entry(
    ts: str,
    track: str = "Test Track",
    artist: str = "Test Artist",
    album: str = "Test Album",
    ms_played: int = 200_000,
    uri: str = "spotify:track:abc123",
) -> dict:
    return {
        "ts": ts,
        "master_metadata_track_name": track,
        "master_metadata_album_artist_name": artist,
        "master_metadata_album_album_name": album,
        "ms_played": ms_played,
        "spotify_track_uri": uri,
        "platform": "Linux",
        "conn_country": "US",
        "reason_start": "trackdone",
        "reason_end": "trackdone",
        "shuffle": False,
        "skipped": False,
        "offline": False,
        "incognito_mode": False,
    }


@pytest.fixture
def sample_entries() -> list[dict]:
    """A small list of raw history entries."""
    return [
        _make_entry(
            "2024-01-15T10:00:00Z", "Song A", "Artist 1", "Album X", 180_000, "spotify:track:a1"
        ),
        _make_entry(
            "2024-01-15T10:05:00Z", "Song B", "Artist 1", "Album X", 240_000, "spotify:track:b1"
        ),
        _make_entry(
            "2024-01-16T14:00:00Z", "Song C", "Artist 2", "Album Y", 300_000, "spotify:track:c1"
        ),
        _make_entry(
            "2024-01-16T14:10:00Z", "Song A", "Artist 1", "Album X", 180_000, "spotify:track:a1"
        ),
        _make_entry(
            "2024-01-17T22:00:00Z", "Song D", "Artist 3", "Album Z", 150_000, "spotify:track:d1"
        ),
        _make_entry(
            "2024-01-18T08:30:00Z", "Song A", "Artist 1", "Album X", 180_000, "spotify:track:a1"
        ),
        _make_entry(
            "2024-01-19T16:00:00Z", "Song B", "Artist 1", "Album X", 240_000, "spotify:track:b1"
        ),
        _make_entry(
            "2024-01-20T20:00:00Z", "Song E", "Artist 2", "Album Y", 260_000, "spotify:track:e1"
        ),
        _make_entry(
            "2024-01-21T09:00:00Z", "Song F", "Artist 4", "Album W", 190_000, "spotify:track:f1"
        ),
        _make_entry(
            "2024-01-22T11:00:00Z", "Song A", "Artist 1", "Album X", 180_000, "spotify:track:a1"
        ),
    ]


@pytest.fixture
def sample_entries_with_dupes(sample_entries: list[dict]) -> list[dict]:
    """Entries with intentional duplicates."""
    return sample_entries + [sample_entries[0], sample_entries[2]]


@pytest.fixture
def sample_json_file(sample_entries: list[dict], tmp_path: Path) -> Path:
    """Write sample entries to a temp JSON file and return the path."""
    fp = tmp_path / "streaming_history_0.json"
    fp.write_text(json.dumps(sample_entries))
    return fp


@pytest.fixture
def sample_json_dir(sample_entries: list[dict], tmp_path: Path) -> Path:
    """Create a temp directory with two JSON files."""
    f1 = tmp_path / "streaming_history_0.json"
    f2 = tmp_path / "streaming_history_1.json"
    f1.write_text(json.dumps(sample_entries[:5]))
    f2.write_text(json.dumps(sample_entries[5:]))
    return tmp_path


@pytest.fixture
def processed_df(sample_entries: list[dict]) -> pd.DataFrame:
    """A fully processed DataFrame ready for analysis."""
    from spotify_insights.models import ProcessingStats
    from spotify_insights.processor import process_pipeline

    df, _ = process_pipeline(sample_entries, ProcessingStats())
    return df
