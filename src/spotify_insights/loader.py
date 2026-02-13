"""JSON file discovery, loading, and Spotify API integration."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import spotipy
from dotenv import load_dotenv
from rich.progress import Progress
from spotipy.oauth2 import SpotifyOAuth

from spotify_insights.models import ProcessingStats
from spotify_insights.utils import format_size


def discover_files(directory: str) -> list[Path]:
    """Find all JSON files in the given directory."""
    dir_path = Path(directory).resolve()
    if not dir_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    files = sorted(dir_path.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files found in {dir_path}")
    return files


def load_file(file_path: str | Path) -> tuple[list[dict], dict]:
    """Load a single JSON history file and collect basic stats."""
    file_path = Path(file_path)
    stats = {
        "file_size": os.path.getsize(file_path),
        "entries": 0,
        "earliest_entry": None,
        "latest_entry": None,
        "unique_tracks": set(),
        "unique_artists": set(),
    }

    with open(file_path, "rb") as f:
        data = json.load(f)

    stats["entries"] = len(data)

    min_ts = float("inf")
    max_ts = float("-inf")

    for entry in data:
        ts = int(datetime.fromisoformat(entry["ts"].replace("Z", "+00:00")).timestamp())
        if ts < min_ts:
            min_ts = ts
        if ts > max_ts:
            max_ts = ts

        if track := entry.get("master_metadata_track_name"):
            stats["unique_tracks"].add(track)
        if artist := entry.get("master_metadata_album_artist_name"):
            stats["unique_artists"].add(artist)

    if data:
        stats["earliest_entry"] = datetime.fromtimestamp(min_ts)
        stats["latest_entry"] = datetime.fromtimestamp(max_ts)

    return data, stats


def load_all_files(
    file_paths: list[Path],
    progress: Progress | None = None,
) -> tuple[list[dict], list[dict], ProcessingStats]:
    """Load all history files and return combined data with stats.

    Returns:
        Tuple of (all_history, file_stats_list, processing_stats)
    """
    all_history: list[dict] = []
    file_stats: list[dict] = []
    proc_stats = ProcessingStats()

    task = None
    if progress:
        task = progress.add_task("Loading files...", total=len(file_paths))

    for fp in file_paths:
        data, stats = load_file(fp)
        all_history.extend(data)
        file_stats.append(
            {
                "name": fp.name,
                "size": format_size(stats["file_size"]),
                "entries": stats["entries"],
                "date_range": (
                    f"{stats['earliest_entry']:%Y-%m-%d} to {stats['latest_entry']:%Y-%m-%d}"
                    if stats["earliest_entry"]
                    else "N/A"
                ),
                "unique_tracks": len(stats["unique_tracks"]),
                "unique_artists": len(stats["unique_artists"]),
            }
        )
        proc_stats.files_processed += 1
        proc_stats.total_entries += stats["entries"]

        if progress and task is not None:
            progress.update(task, advance=1)

    return all_history, file_stats, proc_stats


def connect_to_spotify(client_id: str, client_secret: str) -> spotipy.Spotify | None:
    """Initialize connection to the Spotify API."""
    try:
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://localhost:8888/callback",
            scope="user-read-recently-played",
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        sp.current_user()
        return sp
    except Exception:
        return None


def fetch_recent_plays(
    sp: spotipy.Spotify,
    last_timestamp: pd.Timestamp,
    progress: Progress | None = None,
) -> list[dict]:
    """Fetch plays from the Spotify API since last_timestamp."""
    if last_timestamp.tz is None:
        last_timestamp = last_timestamp.tz_localize("UTC")

    current_time = pd.Timestamp.now(tz="UTC")
    after_timestamp = int(last_timestamp.timestamp() * 1000)
    current_timestamp = int(current_time.timestamp() * 1000)
    initial_gap = current_timestamp - after_timestamp

    all_plays: list[dict] = []
    task = None
    if progress:
        task = progress.add_task("Fetching recent plays...", total=100)

    while after_timestamp < current_timestamp:
        try:
            results = sp.current_user_recently_played(limit=50, after=after_timestamp)

            if not results["items"]:
                break

            earliest_ts = None
            for item in results["items"]:
                play = {
                    "ts": item["played_at"],
                    "master_metadata_track_name": item["track"]["name"],
                    "master_metadata_album_artist_name": item["track"]["artists"][0]["name"],
                    "master_metadata_album_album_name": item["track"]["album"]["name"],
                    "spotify_track_uri": item["track"]["uri"],
                    "ms_played": item["track"]["duration_ms"],
                }
                all_plays.append(play)

                ts = pd.to_datetime(item["played_at"]).tz_convert("UTC")
                if earliest_ts is None or ts < earliest_ts:
                    earliest_ts = ts

            if earliest_ts:
                after_timestamp = int(earliest_ts.timestamp() * 1000)
                pct = min(
                    ((after_timestamp - int(last_timestamp.timestamp() * 1000)) / initial_gap)
                    * 100,
                    100,
                )
                if progress and task is not None:
                    progress.update(task, completed=int(pct))

        except Exception:
            break

    if progress and task is not None:
        progress.update(task, completed=100)

    return all_plays


def load_env_credentials() -> tuple[str | None, str | None]:
    """Load Spotify API credentials from environment."""
    if os.path.exists(".env"):
        load_dotenv(override=True)
    return os.getenv("SPOTIFY_CLIENT_ID"), os.getenv("SPOTIFY_CLIENT_SECRET")
