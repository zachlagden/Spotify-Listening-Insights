"""Rich static output renderer — prints the full report from pre-computed AnalysisResults."""

from __future__ import annotations

from rich.console import Console

from spotify_insights.models import AnalysisResults
from spotify_insights.ui.components import bar_chart, ranked_table, section_panel, stat_table


def render_report(results: AnalysisResults, console: Console | None = None) -> None:
    """Render the complete analysis report to the terminal."""
    if console is None:
        console = Console()

    _render_overall(results, console)
    _render_artists(results, console)
    _render_tracks(results, console)
    _render_albums(results, console)
    _render_temporal(results, console)
    _render_advanced(results, console)


def _render_overall(results: AnalysisResults, console: Console) -> None:
    o = results.overall
    console.print()
    console.print(section_panel("Overall Statistics"))

    stats = [
        ("Period", f"{o.date_range} ({o.days_covered:,} days)"),
        ("Total listening time", f"{o.total_hours:,.1f} hours ({o.total_hours / 24:.1f} days)"),
        ("Daily average", f"{o.daily_avg_minutes:.1f} minutes"),
        ("Total tracks played", f"{o.total_plays:,}"),
        ("Unique tracks", f"{o.unique_tracks:,}"),
        ("Unique artists", f"{o.unique_artists:,}"),
        ("Unique albums", f"{o.unique_albums:,}"),
        ("Active listening days", f"{o.active_days} ({o.active_days_pct}% of period)"),
        ("Weekend/weekday ratio", f"{o.weekend_weekday_ratio}"),
        ("Night listening", f"{o.night_listening_pct}% of plays"),
    ]
    console.print(stat_table(stats))


def _render_artists(results: AnalysisResults, console: Console) -> None:
    if not results.top_artists:
        return

    console.print()
    console.print(section_panel("Top Artists", subtitle="by listening time"))

    rows = []
    for a in results.top_artists:
        rows.append(
            {
                "name": a.name,
                "hours": f"{a.total_hours}h",
                "plays": f"{a.total_plays:,}",
                "tracks": str(a.unique_tracks),
                "albums": str(a.unique_albums),
                "span": f"{a.active_days}d",
            }
        )

    console.print(
        ranked_table(
            rows,
            [
                ("name", "Artist"),
                ("hours", "Hours"),
                ("plays", "Plays"),
                ("tracks", "Tracks"),
                ("albums", "Albums"),
                ("span", "Active"),
            ],
        )
    )

    # Detailed breakdown for top 5
    for a in results.top_artists[:5]:
        detail = stat_table(
            [
                ("Total time", f"{a.total_hours} hours"),
                ("Avg play duration", f"{a.avg_play_minutes} min"),
                ("Tracks", f"{a.unique_tracks} unique across {a.unique_albums} albums"),
                ("Plays", f"{a.total_plays:,} total ({a.plays_per_track} per track)"),
                ("Weekend listening", f"{a.weekend_pct}%"),
                ("First played", a.first_played),
                ("Last played", a.last_played),
                ("Active period", f"{a.active_days} days"),
            ],
            title=a.name,
        )
        console.print()
        console.print(detail)


def _render_tracks(results: AnalysisResults, console: Console) -> None:
    if not results.top_tracks:
        return

    console.print()
    console.print(section_panel("Top Tracks", subtitle="by listening time"))

    rows = []
    for t in results.top_tracks:
        rows.append(
            {
                "track": t.name,
                "artist": t.artist,
                "hours": f"{t.total_hours}h",
                "plays": f"{t.total_plays:,}",
                "time": t.most_common_time,
            }
        )

    console.print(
        ranked_table(
            rows,
            [
                ("track", "Track"),
                ("artist", "Artist"),
                ("hours", "Hours"),
                ("plays", "Plays"),
                ("time", "Peak Time"),
            ],
        )
    )

    # Detailed breakdown for top 5
    for t in results.top_tracks[:5]:
        detail = stat_table(
            [
                ("Artist", t.artist),
                ("Album", t.album),
                ("Listening time", f"{t.total_hours} hours"),
                ("Total plays", f"{t.total_plays:,}"),
                ("Avg duration", f"{t.avg_duration_seconds}s"),
                ("Weekend plays", f"{t.weekend_pct}%"),
                ("Most common time", t.most_common_time),
                ("First played", t.first_played),
                ("Last played", t.last_played),
                ("Days span", f"{t.days_span}"),
            ],
            title=t.name,
        )
        console.print()
        console.print(detail)


def _render_albums(results: AnalysisResults, console: Console) -> None:
    if not results.top_albums:
        return

    console.print()
    console.print(section_panel("Top Albums", subtitle="by listening time"))

    rows = []
    for a in results.top_albums:
        rows.append(
            {
                "album": a.name,
                "artist": a.artist,
                "hours": f"{a.total_hours}h",
                "tracks": str(a.unique_tracks),
                "plays": f"{a.total_plays:,}",
            }
        )

    console.print(
        ranked_table(
            rows,
            [
                ("album", "Album"),
                ("artist", "Artist"),
                ("hours", "Hours"),
                ("tracks", "Tracks"),
                ("plays", "Plays"),
            ],
        )
    )


def _render_temporal(results: AnalysisResults, console: Console) -> None:
    t = results.temporal

    console.print()
    console.print(section_panel("Temporal Patterns"))

    # Time of day bar chart
    if t.time_of_day:
        chart = bar_chart(
            [(label, hours) for label, hours, _ in t.time_of_day],
            title="Time of Day (hours)",
        )
        console.print(chart)

    # Day of week bar chart
    if t.day_of_week:
        console.print()
        chart = bar_chart(
            [(day, hours) for day, hours, _, _ in t.day_of_week],
            title="Day of Week (hours)",
            color="bright_green",
        )
        console.print(chart)

    # Seasonal
    if t.seasonal:
        console.print()
        chart = bar_chart(
            [(season, hours) for season, hours, _, _ in t.seasonal],
            title="Seasonal (hours)",
            color="bright_yellow",
        )
        console.print(chart)


def _render_advanced(results: AnalysisResults, console: Console) -> None:
    m = results.advanced

    console.print()
    console.print(section_panel("Advanced Metrics"))

    habits = [
        ("Daily consistency", f"{m.consistency_pct}% of days have activity"),
        ("Avg daily artists", f"{m.avg_daily_artists}"),
        (
            "Heavy listening days",
            f"{m.heavy_listening_days} ({m.heavy_listening_pct}% of active days)",
        ),
        (
            "Light listening days",
            f"{m.light_listening_days} ({m.light_listening_pct}% of active days)",
        ),
        ("Repeated tracks (10+)", f"{m.heavily_repeated_tracks:,} tracks"),
        ("Daily track variety", f"{m.daily_track_variety} unique tracks"),
        ("Longest streak", m.longest_streak_info),
        ("Current streak", f"{m.current_streak} days"),
        ("Primary listening time", f"{m.primary_time} ({m.primary_time_pct}% of plays)"),
    ]
    console.print(stat_table(habits, title="Listening Habits"))

    console.print()
    daily_stats = [
        ("Average listening", f"{m.avg_daily_minutes} minutes"),
        ("Median listening", f"{m.median_daily_minutes} minutes"),
        ("Most active day", f"{m.most_active_day} ({m.most_active_day_minutes} min)"),
        ("Standard deviation", f"{m.daily_std_minutes} minutes"),
    ]
    console.print(stat_table(daily_stats, title="Daily Statistics"))

    console.print()
    monthly_stats = [
        ("Most active month", f"{m.most_active_month} ({m.most_active_month_hours}h)"),
        ("Avg monthly listening", f"{m.avg_monthly_hours}h"),
        ("Monthly variation", f"{m.monthly_std_hours}h std deviation"),
    ]
    console.print(stat_table(monthly_stats, title="Monthly Trends"))
