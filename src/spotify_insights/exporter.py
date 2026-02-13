"""Export analysis data to JSON and CSV formats."""

from __future__ import annotations

import csv
import json
import os

import pandas as pd

from spotify_insights.models import AnalysisResults
from spotify_insights.utils import format_size

# Columns from the original Spotify export format
_ORIGINAL_COLUMNS = [
    "ts",
    "spotify_track_uri",
    "ms_played",
    "master_metadata_track_name",
    "master_metadata_album_artist_name",
    "master_metadata_album_album_name",
    "platform",
    "conn_country",
    "ip_addr_decrypted",
    "user_agent_decrypted",
    "episode_name",
    "episode_show_name",
    "spotify_episode_uri",
    "reason_start",
    "reason_end",
    "shuffle",
    "skipped",
    "offline",
    "offline_timestamp",
    "incognito_mode",
]


def export_history_json(df: pd.DataFrame, output_path: str = "history_full.json") -> str:
    """Export the processed history to a JSON file in original Spotify format.

    Returns:
        Summary string with entry count and file size.
    """
    export_columns = [col for col in _ORIGINAL_COLUMNS if col in df.columns]
    unique_entries = df[export_columns].drop_duplicates(
        subset=["ts", "spotify_track_uri", "ms_played"]
    )

    export_data = unique_entries.to_dict("records")

    for entry in export_data:
        if isinstance(entry["ts"], pd.Timestamp):
            entry["ts"] = entry["ts"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        for col in _ORIGINAL_COLUMNS:
            if col not in entry:
                entry[col] = None

    # Deduplicate and sort
    seen: set[tuple] = set()
    deduplicated: list[dict] = []
    for entry in export_data:
        key = (entry["ts"], entry.get("spotify_track_uri"), entry.get("ms_played"))
        if key not in seen:
            seen.add(key)
            deduplicated.append(entry)

    deduplicated.sort(key=lambda x: x["ts"])

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(deduplicated, f, ensure_ascii=False, indent=2)

    size = os.path.getsize(output_path)
    return f"Exported {len(deduplicated):,} entries to {output_path} ({format_size(size)})"


def export_history_csv(df: pd.DataFrame, output_path: str = "history_full.csv") -> str:
    """Export the processed history to a CSV file.

    Returns:
        Summary string with entry count and file size.
    """
    export_columns = [col for col in _ORIGINAL_COLUMNS if col in df.columns]
    unique_entries = df[export_columns].drop_duplicates(
        subset=["ts", "spotify_track_uri", "ms_played"]
    )
    unique_entries = unique_entries.sort_values("ts")
    unique_entries.to_csv(output_path, index=False, quoting=csv.QUOTE_NONNUMERIC)

    size = os.path.getsize(output_path)
    return f"Exported {len(unique_entries):,} entries to {output_path} ({format_size(size)})"


def export_analysis_json(results: AnalysisResults, output_path: str = "analysis.json") -> str:
    """Export the analysis results summary to JSON.

    Returns:
        Summary string.
    """
    from dataclasses import asdict

    data = asdict(results)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    size = os.path.getsize(output_path)
    return f"Exported analysis to {output_path} ({format_size(size)})"
