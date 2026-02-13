"""Dataclasses for all analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProcessingStats:
    """Statistics about the data loading/processing phase."""

    files_processed: int = 0
    total_entries: int = 0
    duplicates_removed: int = 0
    api_entries_added: int = 0
    final_entries: int = 0
    date_start: str = ""
    date_end: str = ""
    unique_artists: int = 0
    unique_tracks: int = 0
    unique_albums: int = 0


@dataclass
class OverallStats:
    """High-level listening statistics."""

    date_range: str = ""
    days_covered: int = 0
    total_hours: float = 0.0
    daily_avg_minutes: float = 0.0
    total_plays: int = 0
    unique_tracks: int = 0
    unique_artists: int = 0
    unique_albums: int = 0
    active_days: int = 0
    active_days_pct: float = 0.0
    weekend_weekday_ratio: float = 0.0
    night_listening_pct: float = 0.0


@dataclass
class ArtistStat:
    """Statistics for a single artist."""

    name: str = ""
    total_hours: float = 0.0
    avg_play_minutes: float = 0.0
    total_plays: int = 0
    unique_tracks: int = 0
    unique_albums: int = 0
    plays_per_track: float = 0.0
    weekend_pct: float = 0.0
    first_played: str = ""
    last_played: str = ""
    active_days: int = 0


@dataclass
class TrackStat:
    """Statistics for a single track."""

    name: str = ""
    artist: str = ""
    album: str = ""
    total_hours: float = 0.0
    total_plays: int = 0
    avg_duration_seconds: float = 0.0
    weekend_pct: float = 0.0
    most_common_time: str = ""
    first_played: str = ""
    last_played: str = ""
    days_span: int = 0


@dataclass
class AlbumStat:
    """Statistics for a single album."""

    name: str = ""
    artist: str = ""
    total_hours: float = 0.0
    avg_play_minutes: float = 0.0
    total_plays: int = 0
    unique_tracks: int = 0
    plays_per_track: float = 0.0
    weekend_pct: float = 0.0
    most_common_time: str = ""
    first_played: str = ""
    last_played: str = ""
    days_in_rotation: int = 0


@dataclass
class TemporalPatterns:
    """Temporal listening distribution data."""

    time_of_day: list[tuple[str, float, float]] = field(default_factory=list)
    day_of_week: list[tuple[str, float, int, int]] = field(default_factory=list)
    monthly: list[tuple[str, float, int, int]] = field(default_factory=list)
    seasonal: list[tuple[str, float, int, int]] = field(default_factory=list)


@dataclass
class AdvancedMetrics:
    """Advanced listening habit metrics."""

    consistency_pct: float = 0.0
    avg_daily_artists: float = 0.0
    heavy_listening_days: int = 0
    heavy_listening_pct: float = 0.0
    light_listening_days: int = 0
    light_listening_pct: float = 0.0
    heavily_repeated_tracks: int = 0
    daily_track_variety: float = 0.0
    longest_streak: int = 0
    longest_streak_info: str = ""
    current_streak: int = 0
    primary_time: str = ""
    primary_time_pct: float = 0.0
    avg_daily_minutes: float = 0.0
    median_daily_minutes: float = 0.0
    most_active_day: str = ""
    most_active_day_minutes: float = 0.0
    daily_std_minutes: float = 0.0
    most_active_month: str = ""
    most_active_month_hours: float = 0.0
    avg_monthly_hours: float = 0.0
    monthly_std_hours: float = 0.0


@dataclass
class AnalysisResults:
    """Container for all analysis results."""

    overall: OverallStats = field(default_factory=OverallStats)
    top_artists: list[ArtistStat] = field(default_factory=list)
    top_tracks: list[TrackStat] = field(default_factory=list)
    top_albums: list[AlbumStat] = field(default_factory=list)
    temporal: TemporalPatterns = field(default_factory=TemporalPatterns)
    advanced: AdvancedMetrics = field(default_factory=AdvancedMetrics)
