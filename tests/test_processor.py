"""Tests for the processor module."""

from __future__ import annotations

import pandas as pd

from spotify_insights.models import ProcessingStats
from spotify_insights.processor import (
    build_dataframe,
    deduplicate,
    enrich_timestamps,
    process_pipeline,
)


class TestBuildDataframe:
    def test_creates_dataframe(self, sample_entries: list[dict]) -> None:
        df = build_dataframe(sample_entries)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert "ts" in df.columns
        assert "ms_played" in df.columns


class TestDeduplicate:
    def test_removes_duplicates(self, sample_entries_with_dupes: list[dict]) -> None:
        df = build_dataframe(sample_entries_with_dupes)
        deduped, removed = deduplicate(df)
        assert removed == 2
        assert len(deduped) == 10

    def test_no_dupes_means_zero_removed(self, sample_entries: list[dict]) -> None:
        df = build_dataframe(sample_entries)
        deduped, removed = deduplicate(df)
        assert removed == 0
        assert len(deduped) == 10


class TestEnrichTimestamps:
    def test_adds_derived_columns(self, sample_entries: list[dict]) -> None:
        df = build_dataframe(sample_entries)
        df, _ = deduplicate(df)
        df = enrich_timestamps(df)

        expected_cols = [
            "duration_hours",
            "duration_minutes",
            "year",
            "month",
            "hour",
            "day_of_week",
            "is_weekend",
            "time_of_day",
            "day",
            "quarter",
            "season",
        ]
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_timestamps_are_utc(self, sample_entries: list[dict]) -> None:
        df = build_dataframe(sample_entries)
        df, _ = deduplicate(df)
        df = enrich_timestamps(df)
        assert str(df["ts"].dt.tz) == "UTC"


class TestProcessPipeline:
    def test_full_pipeline(self, sample_entries_with_dupes: list[dict]) -> None:
        stats = ProcessingStats()
        df, stats = process_pipeline(sample_entries_with_dupes, stats)

        assert stats.duplicates_removed == 2
        assert stats.final_entries == 10
        assert stats.unique_artists > 0
        assert stats.unique_tracks > 0
        assert "duration_hours" in df.columns
