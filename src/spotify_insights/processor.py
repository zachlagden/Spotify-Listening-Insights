"""Data processing: deduplication, timestamp enrichment, DataFrame preparation."""

from __future__ import annotations

import pandas as pd

from spotify_insights.models import ProcessingStats


def build_dataframe(all_history: list[dict]) -> pd.DataFrame:
    """Convert raw history list to a DataFrame."""
    return pd.DataFrame(all_history)


def deduplicate(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove duplicate entries based on timestamp, URI, and ms_played.

    Returns:
        Tuple of (deduplicated DataFrame, number of duplicates removed)
    """
    initial = len(df)
    df = df.drop_duplicates(subset=["ts", "spotify_track_uri", "ms_played"])
    return df, initial - len(df)


def enrich_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived time columns to the DataFrame."""
    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"]).dt.tz_convert("UTC")
    ts_naive = df["ts"].dt.tz_localize(None)

    # Duration columns
    df["duration_hours"] = df["ms_played"] / (1000 * 60 * 60)
    df["duration_minutes"] = df["ms_played"] / (1000 * 60)

    # Time-based columns
    df["year"] = df["ts"].dt.year
    df["month"] = df["ts"].dt.month
    df["hour"] = df["ts"].dt.hour
    df["day_of_week"] = df["ts"].dt.day_name()
    df["week_number"] = df["ts"].dt.isocalendar().week
    df["is_weekend"] = df["ts"].dt.dayofweek.isin([5, 6])

    # Time of day categories
    df["time_of_day"] = pd.cut(
        df["hour"],
        bins=[0, 6, 12, 18, 24],
        labels=["Night", "Morning", "Afternoon", "Evening"],
    )

    # Additional time periods
    df["month_year"] = ts_naive.dt.to_period("M")
    df["day"] = ts_naive.dt.date
    df["quarter"] = df["ts"].dt.quarter
    df["season"] = pd.cut(
        df["month"],
        bins=[0, 3, 6, 9, 12],
        labels=["Winter", "Spring", "Summer", "Fall"],
    )

    return df


def merge_api_data(df: pd.DataFrame, recent_plays: list[dict]) -> pd.DataFrame:
    """Merge API-fetched plays into the main DataFrame."""
    if not recent_plays:
        return df

    recent_df = pd.DataFrame(recent_plays)
    recent_df["ts"] = pd.to_datetime(recent_df["ts"]).dt.tz_convert("UTC")

    df = pd.concat([df, recent_df], ignore_index=True)
    df = df.drop_duplicates(subset=["ts", "spotify_track_uri", "ms_played"])
    return df


def process_pipeline(
    all_history: list[dict],
    proc_stats: ProcessingStats,
) -> tuple[pd.DataFrame, ProcessingStats]:
    """Run the full processing pipeline: build, deduplicate, enrich.

    Returns:
        Tuple of (processed DataFrame, updated ProcessingStats)
    """
    df = build_dataframe(all_history)
    df, dupes = deduplicate(df)
    proc_stats.duplicates_removed = dupes

    df = enrich_timestamps(df)

    proc_stats.final_entries = len(df)
    proc_stats.date_start = f"{df['ts'].min():%Y-%m-%d}"
    proc_stats.date_end = f"{df['ts'].max():%Y-%m-%d}"
    proc_stats.unique_artists = df["master_metadata_album_artist_name"].nunique()
    proc_stats.unique_tracks = df["master_metadata_track_name"].nunique()
    proc_stats.unique_albums = df["master_metadata_album_album_name"].nunique()

    return df, proc_stats
