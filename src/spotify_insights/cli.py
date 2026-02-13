"""Click-based CLI argument parsing and main orchestration."""

from __future__ import annotations

import sys

import click
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from spotify_insights import __version__
from spotify_insights.analyzer import (
    analyze_advanced,
    analyze_albums,
    analyze_artists,
    analyze_overall,
    analyze_temporal,
    analyze_tracks,
)
from spotify_insights.exporter import export_analysis_json, export_history_csv, export_history_json
from spotify_insights.loader import (
    connect_to_spotify,
    discover_files,
    fetch_recent_plays,
    load_all_files,
    load_env_credentials,
)
from spotify_insights.models import AnalysisResults
from spotify_insights.processor import enrich_timestamps, merge_api_data, process_pipeline
from spotify_insights.ui.components import section_panel
from spotify_insights.ui.static import render_report
from spotify_insights.utils import format_size

console = Console()


@click.command()
@click.option(
    "-d",
    "--directory",
    type=click.Path(exists=True, file_okay=False),
    help="Path to directory containing Spotify JSON data files.",
)
@click.option(
    "-o",
    "--output",
    type=click.Choice(["static", "export"]),
    default=None,
    help="Output mode. If not set, you will be prompted.",
)
@click.option(
    "--export-format",
    type=click.Choice(["json", "csv"]),
    default="json",
    help="Export format (used with --output export).",
)
@click.option(
    "--no-api",
    is_flag=True,
    default=False,
    help="Skip Spotify API integration entirely.",
)
@click.version_option(version=__version__, prog_name="spotify-insights")
def main(
    directory: str | None,
    output: str | None,
    export_format: str,
    no_api: bool,
) -> None:
    """Analyze your Spotify listening history with rich terminal output."""
    console.print()
    console.print(
        Panel(
            Text("Spotify Listening Insights", style="bold bright_cyan", justify="center"),
            subtitle=f"v{__version__}",
            border_style="bright_cyan",
        )
    )
    console.print()

    # --- Directory selection ---
    if directory is None:
        directory = Prompt.ask(
            "[cyan]Enter the directory containing your Spotify JSON files[/]",
            default=".",
            console=console,
        )

    try:
        file_paths = discover_files(directory)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/]")
        sys.exit(1)

    # Show discovered files
    file_table = Table(
        title="Discovered Files",
        border_style="dim",
        show_lines=False,
    )
    file_table.add_column("#", style="dim", width=4, justify="right")
    file_table.add_column("File", style="white")
    file_table.add_column("Size", style="cyan", justify="right")
    for i, fp in enumerate(file_paths, 1):
        file_table.add_row(str(i), fp.name, format_size(fp.stat().st_size))
    console.print(file_table)
    console.print()

    # --- Load data ---
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        all_history, file_stats, proc_stats = load_all_files(file_paths, progress)

    console.print(
        f"  Loaded [bold]{proc_stats.total_entries:,}[/] entries from "
        f"[bold]{proc_stats.files_processed}[/] files"
    )
    console.print()

    # --- Process data ---
    with console.status("[bold cyan]Processing data..."):
        df, proc_stats = process_pipeline(all_history, proc_stats)

    if proc_stats.duplicates_removed > 0:
        console.print(f"  Removed [bold]{proc_stats.duplicates_removed:,}[/] duplicates")

    # --- Spotify API gap filling ---
    if not no_api:
        client_id, client_secret = load_env_credentials()
        if client_id and client_secret:
            last_ts = df["ts"].max()
            gap_days = (pd.Timestamp.now(tz="UTC") - last_ts).days
            if gap_days > 0:
                console.print(f"  [yellow]Gap detected:[/] last entry is {gap_days} days ago")
                fill = Prompt.ask(
                    "  Fill gap from Spotify API?",
                    choices=["y", "n"],
                    default="n",
                    console=console,
                )
                if fill == "y":
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TaskProgressColumn(),
                        console=console,
                    ) as progress:
                        sp = connect_to_spotify(client_id, client_secret)
                        if sp:
                            recent = fetch_recent_plays(sp, last_ts, progress)
                            if recent:
                                df = merge_api_data(df, recent)
                                df = enrich_timestamps(df)
                                proc_stats.api_entries_added = len(recent)
                                console.print(f"  Added [bold]{len(recent):,}[/] plays from API")
                        else:
                            console.print("  [red]Could not connect to Spotify API[/]")

    # --- Processing summary ---

    console.print()
    console.print(section_panel("Processing Summary"))
    summary_table = Table(show_header=False, expand=True, border_style="dim", show_edge=False)
    summary_table.add_column("Metric", style="cyan", ratio=2)
    summary_table.add_column("Value", style="white", ratio=3)
    summary_table.add_row("Files processed", str(proc_stats.files_processed))
    summary_table.add_row("Total entries", f"{proc_stats.total_entries:,}")
    summary_table.add_row("Duplicates removed", f"{proc_stats.duplicates_removed:,}")
    summary_table.add_row("Final entries", f"{proc_stats.final_entries:,}")
    summary_table.add_row("Date range", f"{proc_stats.date_start} to {proc_stats.date_end}")
    summary_table.add_row("Unique artists", f"{proc_stats.unique_artists:,}")
    summary_table.add_row("Unique tracks", f"{proc_stats.unique_tracks:,}")
    summary_table.add_row("Unique albums", f"{proc_stats.unique_albums:,}")
    if proc_stats.api_entries_added > 0:
        summary_table.add_row("API entries added", f"{proc_stats.api_entries_added:,}")
    console.print(summary_table)
    console.print()

    # --- Analysis ---
    with console.status("[bold cyan]Analyzing listening history...") as status:
        results = AnalysisResults()

        status.update("[bold cyan]Analyzing overall statistics...")
        results.overall = analyze_overall(df)

        status.update("[bold cyan]Analyzing artists...")
        results.top_artists = analyze_artists(df)

        status.update("[bold cyan]Analyzing tracks...")
        results.top_tracks = analyze_tracks(df)

        status.update("[bold cyan]Analyzing albums...")
        results.top_albums = analyze_albums(df)

        status.update("[bold cyan]Analyzing temporal patterns...")
        results.temporal = analyze_temporal(df)

        status.update("[bold cyan]Computing advanced metrics...")
        results.advanced = analyze_advanced(df)

    console.print("[green]Analysis complete.[/]")
    console.print()

    # --- Output mode ---
    if output is None:
        output = Prompt.ask(
            "[cyan]How would you like to view results?[/]",
            choices=["static", "export"],
            default="static",
            console=console,
        )

    if output == "static":
        render_report(results, console)
    elif output == "export":
        if export_format == "csv":
            msg = export_history_csv(df)
        else:
            msg = export_history_json(df)
        console.print(f"[green]{msg}[/]")

        analysis_msg = export_analysis_json(results)
        console.print(f"[green]{analysis_msg}[/]")

    console.print()
    console.print("[dim]Thank you for using Spotify Listening Insights.[/]")
