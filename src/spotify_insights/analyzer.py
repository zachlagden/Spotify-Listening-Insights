"""All statistics computation. Each function returns typed dataclasses."""

from __future__ import annotations

import pandas as pd

from spotify_insights.models import (
    AdvancedMetrics,
    AlbumStat,
    AnalysisResults,
    ArtistStat,
    OverallStats,
    TemporalPatterns,
    TrackStat,
)


def analyze_overall(df: pd.DataFrame) -> OverallStats:
    """Compute high-level listening statistics."""
    date_range = f"{df['ts'].min():%Y-%m-%d} to {df['ts'].max():%Y-%m-%d}"
    days_covered = (df["ts"].max() - df["ts"].min()).days + 1
    total_hours = df["duration_hours"].sum()
    active_days = df["day"].nunique()

    weekend_hours = df[df["is_weekend"]]["duration_hours"].sum()
    weekday_hours = df[~df["is_weekend"]]["duration_hours"].sum()
    wk_ratio = weekend_hours / weekday_hours if weekday_hours > 0 else 0.0

    night_count = len(df[df["time_of_day"] == "Night"])
    night_pct = (night_count / len(df) * 100) if len(df) > 0 else 0.0

    return OverallStats(
        date_range=date_range,
        days_covered=days_covered,
        total_hours=round(total_hours, 1),
        daily_avg_minutes=round(total_hours * 60 / days_covered, 1) if days_covered > 0 else 0.0,
        total_plays=len(df),
        unique_tracks=df["master_metadata_track_name"].nunique(),
        unique_artists=df["master_metadata_album_artist_name"].nunique(),
        unique_albums=df["master_metadata_album_album_name"].nunique(),
        active_days=active_days,
        active_days_pct=round((active_days / days_covered) * 100, 1) if days_covered > 0 else 0.0,
        weekend_weekday_ratio=round(wk_ratio, 2),
        night_listening_pct=round(night_pct, 1),
    )


def analyze_artists(df: pd.DataFrame, top_n: int = 15) -> list[ArtistStat]:
    """Compute per-artist statistics, returning the top N."""
    artist_stats = (
        df.groupby("master_metadata_album_artist_name", observed=False)
        .agg(
            {
                "ms_played": ["sum", "mean", "count"],
                "master_metadata_track_name": ["count", "nunique"],
                "master_metadata_album_album_name": "nunique",
                "is_weekend": "mean",
                "ts": ["min", "max"],
            }
        )
        .sort_values(("ms_played", "sum"), ascending=False)
    )

    results: list[ArtistStat] = []
    for artist, data in artist_stats.head(top_n).iterrows():
        hours = data[("ms_played", "sum")] / (1000 * 60 * 60)
        avg_min = data[("ms_played", "mean")] / (1000 * 60)
        total_plays = data[("master_metadata_track_name", "count")]
        unique_tracks = data[("master_metadata_track_name", "nunique")]
        unique_albums = data[("master_metadata_album_album_name", "nunique")]
        first = data[("ts", "min")]
        last = data[("ts", "max")]

        results.append(
            ArtistStat(
                name=str(artist),
                total_hours=round(hours, 1),
                avg_play_minutes=round(avg_min, 1),
                total_plays=int(total_plays),
                unique_tracks=int(unique_tracks),
                unique_albums=int(unique_albums),
                plays_per_track=round(total_plays / unique_tracks, 1) if unique_tracks else 0.0,
                weekend_pct=round(data[("is_weekend", "mean")] * 100, 1),
                first_played=f"{first:%Y-%m-%d}",
                last_played=f"{last:%Y-%m-%d}",
                active_days=(last - first).days,
            )
        )

    return results


def analyze_tracks(df: pd.DataFrame, top_n: int = 15) -> list[TrackStat]:
    """Compute per-track statistics, returning the top N."""
    track_stats = (
        df.groupby(
            [
                "master_metadata_track_name",
                "master_metadata_album_artist_name",
                "master_metadata_album_album_name",
            ],
            observed=False,
        )
        .agg(
            {
                "ms_played": ["sum", "count", "mean"],
                "ts": ["min", "max"],
                "is_weekend": "mean",
                "time_of_day": lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "Various",
            }
        )
        .sort_values(("ms_played", "sum"), ascending=False)
    )

    results: list[TrackStat] = []
    for (track, artist, album), data in track_stats.head(top_n).iterrows():
        if pd.isna(track) or pd.isna(artist) or pd.isna(album):
            continue

        hours = data[("ms_played", "sum")] / (1000 * 60 * 60)
        plays = data[("ms_played", "count")]
        avg_sec = data[("ms_played", "mean")] / 1000
        first = data[("ts", "min")]
        last = data[("ts", "max")]

        results.append(
            TrackStat(
                name=str(track),
                artist=str(artist),
                album=str(album),
                total_hours=round(hours, 1),
                total_plays=int(plays),
                avg_duration_seconds=round(avg_sec, 1),
                weekend_pct=round(data[("is_weekend", "mean")] * 100, 1),
                most_common_time=str(data[("time_of_day", "<lambda>")]),
                first_played=f"{first:%Y-%m-%d}",
                last_played=f"{last:%Y-%m-%d}",
                days_span=(last - first).days,
            )
        )

    return results


def analyze_albums(df: pd.DataFrame, top_n: int = 10) -> list[AlbumStat]:
    """Compute per-album statistics, returning the top N."""
    basic_stats = df.groupby(
        [
            "master_metadata_album_album_name",
            "master_metadata_album_artist_name",
        ],
        observed=False,
    ).agg(
        {
            "ms_played": ["sum", "mean", "count"],
            "master_metadata_track_name": ["count", "nunique"],
            "ts": ["min", "max"],
            "is_weekend": "mean",
        }
    )

    time_modes = df.groupby(
        [
            "master_metadata_album_album_name",
            "master_metadata_album_artist_name",
        ],
        observed=False,
    )["time_of_day"].agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "Various")

    album_stats = pd.concat([basic_stats, time_modes], axis=1)
    album_stats.sort_values(("ms_played", "sum"), ascending=False, inplace=True)

    results: list[AlbumStat] = []
    for (album, artist), data in album_stats.head(top_n).iterrows():
        if pd.isna(album) or pd.isna(artist):
            continue

        hours = data[("ms_played", "sum")] / (1000 * 60 * 60)
        avg_min = data[("ms_played", "mean")] / (1000 * 60)
        total_plays = data[("master_metadata_track_name", "count")]
        unique_tracks = data[("master_metadata_track_name", "nunique")]
        first = data[("ts", "min")]
        last = data[("ts", "max")]

        results.append(
            AlbumStat(
                name=str(album),
                artist=str(artist),
                total_hours=round(hours, 1),
                avg_play_minutes=round(avg_min, 1),
                total_plays=int(total_plays),
                unique_tracks=int(unique_tracks),
                plays_per_track=round(total_plays / unique_tracks, 1) if unique_tracks else 0.0,
                weekend_pct=round(data[("is_weekend", "mean")] * 100, 1),
                most_common_time=str(data["time_of_day"]),
                first_played=f"{first:%Y-%m-%d}",
                last_played=f"{last:%Y-%m-%d}",
                days_in_rotation=(last - first).days,
            )
        )

    return results


def analyze_temporal(df: pd.DataFrame) -> TemporalPatterns:
    """Compute temporal listening distributions."""
    # Time of day
    time_dist = df.groupby("time_of_day", observed=False)["duration_hours"].sum()
    total_hours = time_dist.sum()
    time_of_day = [
        (str(period), round(hours, 1), round((hours / total_hours) * 100, 1))
        for period, hours in time_dist.items()
    ]

    # Day of week
    dow_stats = (
        df.groupby("day_of_week", observed=False)
        .agg(
            {
                "duration_hours": "sum",
                "master_metadata_track_name": "count",
                "master_metadata_album_artist_name": "nunique",
            }
        )
        .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    )
    day_of_week = [
        (
            str(day),
            round(stats["duration_hours"], 1),
            int(stats["master_metadata_track_name"]),
            int(stats["master_metadata_album_artist_name"]),
        )
        for day, stats in dow_stats.iterrows()
    ]

    # Monthly
    monthly_stats = df.groupby(["year", "month"], observed=False).agg(
        {
            "duration_hours": "sum",
            "master_metadata_track_name": "count",
            "master_metadata_album_artist_name": "nunique",
        }
    )
    monthly = [
        (
            f"{pd.Timestamp(year=year, month=month, day=1):%B %Y}",
            round(stats["duration_hours"], 1),
            int(stats["master_metadata_track_name"]),
            int(stats["master_metadata_album_artist_name"]),
        )
        for (year, month), stats in monthly_stats.iterrows()
    ]

    # Seasonal
    season_stats = df.groupby("season", observed=False).agg(
        {
            "duration_hours": "sum",
            "master_metadata_track_name": "count",
            "master_metadata_album_artist_name": "nunique",
        }
    )
    seasonal = [
        (
            str(season),
            round(stats["duration_hours"], 1),
            int(stats["master_metadata_track_name"]),
            int(stats["master_metadata_album_artist_name"]),
        )
        for season, stats in season_stats.iterrows()
    ]

    return TemporalPatterns(
        time_of_day=time_of_day,
        day_of_week=day_of_week,
        monthly=monthly,
        seasonal=seasonal,
    )


def analyze_advanced(df: pd.DataFrame) -> AdvancedMetrics:
    """Compute advanced listening metrics."""
    daily_listening = df.groupby(df["ts"].dt.date)["duration_minutes"].sum()
    active_days = daily_listening[daily_listening > 0]
    total_days = len(daily_listening)

    consistency = (len(active_days) / total_days) * 100 if total_days > 0 else 0.0

    unique_artists_per_day = df.groupby(df["ts"].dt.date)[
        "master_metadata_album_artist_name"
    ].nunique()

    mean_listening = active_days.mean()
    std_listening = active_days.std()
    heavy = active_days[active_days > mean_listening + std_listening]
    light = active_days[active_days < mean_listening - std_listening]

    track_counts = df["master_metadata_track_name"].value_counts()
    heavily_repeated = int(track_counts[track_counts >= 10].count())

    daily_variety = df.groupby(df["ts"].dt.date)["master_metadata_track_name"].nunique().mean()

    # Listening streaks
    daily_bool = daily_listening > 0
    dates = sorted(daily_bool.index)

    max_streak = 0
    current_streak_count = 0
    max_streak_end = None

    for date in dates:
        if daily_bool[date]:
            current_streak_count += 1
            if current_streak_count > max_streak:
                max_streak = current_streak_count
                max_streak_end = date
        else:
            current_streak_count = 0

    current_streak = 0
    for date in reversed(dates):
        if daily_bool[date]:
            current_streak += 1
        else:
            break

    if max_streak_end:
        max_streak_start = max_streak_end - pd.Timedelta(days=max_streak - 1)
        streak_info = (
            f"{max_streak} days ({max_streak_start:%Y-%m-%d} to {max_streak_end:%Y-%m-%d})"
        )
    else:
        streak_info = f"{max_streak} days"

    # Time preferences
    time_prefs = df.groupby("time_of_day", observed=False).size()
    primary_time = str(time_prefs.idxmax())
    primary_time_pct = (time_prefs.max() / len(df)) * 100 if len(df) > 0 else 0.0

    # Monthly trends
    monthly_listening = df.groupby(["year", "month"])["duration_hours"].sum()
    most_active_idx = monthly_listening.idxmax()
    most_active_month = f"{most_active_idx[1]}/{most_active_idx[0]}"

    return AdvancedMetrics(
        consistency_pct=round(consistency, 1),
        avg_daily_artists=round(unique_artists_per_day.mean(), 1),
        heavy_listening_days=len(heavy),
        heavy_listening_pct=round(len(heavy) / len(active_days) * 100, 1)
        if len(active_days)
        else 0.0,
        light_listening_days=len(light),
        light_listening_pct=round(len(light) / len(active_days) * 100, 1)
        if len(active_days)
        else 0.0,
        heavily_repeated_tracks=heavily_repeated,
        daily_track_variety=round(daily_variety, 1),
        longest_streak=max_streak,
        longest_streak_info=streak_info,
        current_streak=current_streak,
        primary_time=primary_time,
        primary_time_pct=round(primary_time_pct, 1),
        avg_daily_minutes=round(active_days.mean(), 1),
        median_daily_minutes=round(active_days.median(), 1),
        most_active_day=f"{active_days.idxmax():%Y-%m-%d}",
        most_active_day_minutes=round(active_days.max(), 1),
        daily_std_minutes=round(active_days.std(), 1),
        most_active_month=most_active_month,
        most_active_month_hours=round(monthly_listening.max(), 1),
        avg_monthly_hours=round(monthly_listening.mean(), 1),
        monthly_std_hours=round(monthly_listening.std(), 1),
    )


def analyze_all(df: pd.DataFrame) -> AnalysisResults:
    """Run all analysis and return a complete AnalysisResults."""
    return AnalysisResults(
        overall=analyze_overall(df),
        top_artists=analyze_artists(df),
        top_tracks=analyze_tracks(df),
        top_albums=analyze_albums(df),
        temporal=analyze_temporal(df),
        advanced=analyze_advanced(df),
    )
