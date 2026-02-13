"""Tests for the analyzer module."""

from __future__ import annotations

import pandas as pd

from spotify_insights.analyzer import (
    analyze_advanced,
    analyze_albums,
    analyze_all,
    analyze_artists,
    analyze_overall,
    analyze_temporal,
    analyze_tracks,
)
from spotify_insights.models import (
    AdvancedMetrics,
    AlbumStat,
    AnalysisResults,
    ArtistStat,
    OverallStats,
    TemporalPatterns,
    TrackStat,
)


class TestAnalyzeOverall:
    def test_returns_overall_stats(self, processed_df: pd.DataFrame) -> None:
        result = analyze_overall(processed_df)
        assert isinstance(result, OverallStats)
        assert result.total_plays == 10
        assert result.unique_tracks == 6
        assert result.unique_artists == 4
        assert result.unique_albums == 4
        assert result.total_hours > 0
        assert result.days_covered > 0

    def test_active_days_calculated(self, processed_df: pd.DataFrame) -> None:
        result = analyze_overall(processed_df)
        assert result.active_days > 0
        assert 0 < result.active_days_pct <= 100


class TestAnalyzeArtists:
    def test_returns_list_of_artist_stats(self, processed_df: pd.DataFrame) -> None:
        result = analyze_artists(processed_df)
        assert isinstance(result, list)
        assert all(isinstance(a, ArtistStat) for a in result)
        assert len(result) == 4  # 4 unique artists in sample data

    def test_sorted_by_hours(self, processed_df: pd.DataFrame) -> None:
        result = analyze_artists(processed_df)
        hours = [a.total_hours for a in result]
        assert hours == sorted(hours, reverse=True)

    def test_artist_fields_populated(self, processed_df: pd.DataFrame) -> None:
        result = analyze_artists(processed_df)
        top = result[0]
        assert top.name != ""
        assert top.total_plays > 0
        assert top.unique_tracks > 0
        assert top.first_played != ""


class TestAnalyzeTracks:
    def test_returns_list_of_track_stats(self, processed_df: pd.DataFrame) -> None:
        result = analyze_tracks(processed_df)
        assert isinstance(result, list)
        assert all(isinstance(t, TrackStat) for t in result)

    def test_track_fields_populated(self, processed_df: pd.DataFrame) -> None:
        result = analyze_tracks(processed_df)
        top = result[0]
        assert top.name != ""
        assert top.artist != ""
        assert top.album != ""
        assert top.total_plays > 0


class TestAnalyzeAlbums:
    def test_returns_list_of_album_stats(self, processed_df: pd.DataFrame) -> None:
        result = analyze_albums(processed_df)
        assert isinstance(result, list)
        assert all(isinstance(a, AlbumStat) for a in result)

    def test_album_fields_populated(self, processed_df: pd.DataFrame) -> None:
        result = analyze_albums(processed_df)
        top = result[0]
        assert top.name != ""
        assert top.artist != ""
        assert top.total_plays > 0


class TestAnalyzeTemporal:
    def test_returns_temporal_patterns(self, processed_df: pd.DataFrame) -> None:
        result = analyze_temporal(processed_df)
        assert isinstance(result, TemporalPatterns)
        assert len(result.time_of_day) == 4
        assert len(result.day_of_week) == 7
        assert len(result.seasonal) > 0


class TestAnalyzeAdvanced:
    def test_returns_advanced_metrics(self, processed_df: pd.DataFrame) -> None:
        result = analyze_advanced(processed_df)
        assert isinstance(result, AdvancedMetrics)
        assert result.consistency_pct > 0
        assert result.longest_streak > 0
        assert result.primary_time != ""


class TestAnalyzeAll:
    def test_returns_complete_results(self, processed_df: pd.DataFrame) -> None:
        result = analyze_all(processed_df)
        assert isinstance(result, AnalysisResults)
        assert isinstance(result.overall, OverallStats)
        assert len(result.top_artists) > 0
        assert len(result.top_tracks) > 0
        assert len(result.top_albums) > 0
        assert isinstance(result.temporal, TemporalPatterns)
        assert isinstance(result.advanced, AdvancedMetrics)
