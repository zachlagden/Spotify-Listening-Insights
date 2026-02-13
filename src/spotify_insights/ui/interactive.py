"""Textual TUI app with sidebar navigation for exploring analysis results."""

from __future__ import annotations

from io import StringIO

import pandas as pd
from rich.console import Console
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Footer, Header, ListItem, ListView, Static

from spotify_insights.models import AnalysisResults
from spotify_insights.ui.components import bar_chart, ranked_table, stat_table

SECTIONS = [
    ("overview", "Overview"),
    ("artists", "Artists"),
    ("tracks", "Tracks"),
    ("albums", "Albums"),
    ("temporal", "Temporal"),
    ("advanced", "Advanced"),
    ("export", "Export"),
]


def _render_to_str(renderable) -> str:
    """Render a Rich renderable to a plain string for Textual."""
    buf = StringIO()
    temp_console = Console(file=buf, force_terminal=True, width=100)
    temp_console.print(renderable)
    return buf.getvalue()


class SectionContent(Static):
    """Displays the content for a selected section."""


class InsightsTUI(App):
    """Textual app for exploring Spotify listening insights."""

    CSS = """
    #sidebar {
        width: 20;
        dock: left;
        background: $surface;
        border-right: tall $primary;
        padding: 1;
    }

    #sidebar ListView {
        height: 100%;
    }

    #content {
        padding: 1 2;
    }

    SectionContent {
        padding: 0;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("1", "select_section(0)", "Overview", show=False),
        Binding("2", "select_section(1)", "Artists", show=False),
        Binding("3", "select_section(2)", "Tracks", show=False),
        Binding("4", "select_section(3)", "Albums", show=False),
        Binding("5", "select_section(4)", "Temporal", show=False),
        Binding("6", "select_section(5)", "Advanced", show=False),
        Binding("7", "select_section(6)", "Export", show=False),
    ]

    def __init__(
        self,
        results: AnalysisResults,
        df: pd.DataFrame | None = None,
    ) -> None:
        super().__init__()
        self.results = results
        self.df = df
        self.title = "Spotify Listening Insights"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with ScrollableContainer(id="sidebar"):
                yield ListView(
                    *[ListItem(Static(label), id=key) for key, label in SECTIONS],
                    id="section-list",
                )
            with ScrollableContainer(id="content"):
                yield SectionContent(self._get_section_content("overview"))
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        section_key = event.item.id or "overview"
        content = self.query_one(SectionContent)
        content.update(self._get_section_content(section_key))

    def action_select_section(self, index: int) -> None:
        if 0 <= index < len(SECTIONS):
            key = SECTIONS[index][0]
            content = self.query_one(SectionContent)
            content.update(self._get_section_content(key))
            # Also highlight in sidebar
            lv = self.query_one("#section-list", ListView)
            lv.index = index

    def _get_section_content(self, key: str) -> str:
        if key == "overview":
            return self._render_overview()
        elif key == "artists":
            return self._render_artists()
        elif key == "tracks":
            return self._render_tracks()
        elif key == "albums":
            return self._render_albums()
        elif key == "temporal":
            return self._render_temporal()
        elif key == "advanced":
            return self._render_advanced()
        elif key == "export":
            return self._render_export()
        return "Unknown section"

    def _render_overview(self) -> str:
        o = self.results.overall
        table = stat_table(
            [
                ("Period", f"{o.date_range} ({o.days_covered:,} days)"),
                (
                    "Total listening time",
                    f"{o.total_hours:,.1f} hours ({o.total_hours / 24:.1f} days)",
                ),
                ("Daily average", f"{o.daily_avg_minutes:.1f} minutes"),
                ("Total tracks played", f"{o.total_plays:,}"),
                ("Unique tracks", f"{o.unique_tracks:,}"),
                ("Unique artists", f"{o.unique_artists:,}"),
                ("Unique albums", f"{o.unique_albums:,}"),
                ("Active days", f"{o.active_days} ({o.active_days_pct}%)"),
                ("Weekend/weekday ratio", f"{o.weekend_weekday_ratio}"),
                ("Night listening", f"{o.night_listening_pct}%"),
            ],
            title="Overall Statistics",
        )
        return _render_to_str(table)

    def _render_artists(self) -> str:
        rows = []
        for a in self.results.top_artists:
            rows.append(
                {
                    "name": a.name,
                    "hours": f"{a.total_hours}h",
                    "plays": f"{a.total_plays:,}",
                    "tracks": str(a.unique_tracks),
                    "albums": str(a.unique_albums),
                }
            )
        table = ranked_table(
            rows,
            [
                ("name", "Artist"),
                ("hours", "Hours"),
                ("plays", "Plays"),
                ("tracks", "Tracks"),
                ("albums", "Albums"),
            ],
            title="Top Artists",
        )
        return _render_to_str(table)

    def _render_tracks(self) -> str:
        rows = []
        for t in self.results.top_tracks:
            rows.append(
                {
                    "track": t.name,
                    "artist": t.artist,
                    "hours": f"{t.total_hours}h",
                    "plays": f"{t.total_plays:,}",
                }
            )
        table = ranked_table(
            rows,
            [
                ("track", "Track"),
                ("artist", "Artist"),
                ("hours", "Hours"),
                ("plays", "Plays"),
            ],
            title="Top Tracks",
        )
        return _render_to_str(table)

    def _render_albums(self) -> str:
        rows = []
        for a in self.results.top_albums:
            rows.append(
                {
                    "album": a.name,
                    "artist": a.artist,
                    "hours": f"{a.total_hours}h",
                    "tracks": str(a.unique_tracks),
                    "plays": f"{a.total_plays:,}",
                }
            )
        table = ranked_table(
            rows,
            [
                ("album", "Album"),
                ("artist", "Artist"),
                ("hours", "Hours"),
                ("tracks", "Tracks"),
                ("plays", "Plays"),
            ],
            title="Top Albums",
        )
        return _render_to_str(table)

    def _render_temporal(self) -> str:
        t = self.results.temporal
        parts = []

        if t.time_of_day:
            chart = bar_chart(
                [(label, hours) for label, hours, _ in t.time_of_day],
                title="Time of Day (hours)",
            )
            parts.append(_render_to_str(chart))

        if t.day_of_week:
            chart = bar_chart(
                [(day, hours) for day, hours, _, _ in t.day_of_week],
                title="Day of Week (hours)",
                color="bright_green",
            )
            parts.append(_render_to_str(chart))

        if t.seasonal:
            chart = bar_chart(
                [(s, hours) for s, hours, _, _ in t.seasonal],
                title="Seasonal (hours)",
                color="bright_yellow",
            )
            parts.append(_render_to_str(chart))

        return "\n".join(parts) if parts else "No temporal data"

    def _render_advanced(self) -> str:
        m = self.results.advanced
        table = stat_table(
            [
                ("Daily consistency", f"{m.consistency_pct}%"),
                ("Avg daily artists", f"{m.avg_daily_artists}"),
                ("Heavy listening days", f"{m.heavy_listening_days} ({m.heavy_listening_pct}%)"),
                ("Light listening days", f"{m.light_listening_days} ({m.light_listening_pct}%)"),
                ("Repeated tracks (10+)", f"{m.heavily_repeated_tracks:,}"),
                ("Longest streak", m.longest_streak_info),
                ("Current streak", f"{m.current_streak} days"),
                ("Primary time", f"{m.primary_time} ({m.primary_time_pct}%)"),
                ("Avg daily listening", f"{m.avg_daily_minutes} min"),
                ("Most active day", f"{m.most_active_day} ({m.most_active_day_minutes} min)"),
                ("Most active month", f"{m.most_active_month} ({m.most_active_month_hours}h)"),
            ],
            title="Advanced Metrics",
        )
        return _render_to_str(table)

    def _render_export(self) -> str:
        lines = [
            "Export Options",
            "",
            "Run from the command line to export:",
            "",
            "  spotify-insights -d <dir> --output export --export-format json",
            "  spotify-insights -d <dir> --output export --export-format csv",
            "",
            "This will save your full history and analysis summary.",
        ]
        return "\n".join(lines)


def run_tui(results: AnalysisResults, df: pd.DataFrame | None = None) -> None:
    """Launch the interactive TUI."""
    app = InsightsTUI(results, df)
    app.run()
