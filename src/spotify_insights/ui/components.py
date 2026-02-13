"""Shared Rich renderables used by both static and interactive UI."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def section_panel(title: str, subtitle: str | None = None) -> Panel:
    """Create a consistently styled section header panel."""
    return Panel(
        Text(title, style="bold white"),
        subtitle=subtitle,
        border_style="bright_cyan",
        expand=True,
        padding=(0, 1),
    )


def stat_table(stats: list[tuple[str, str]], title: str | None = None) -> Table:
    """Create a key-value statistics table."""
    table = Table(
        show_header=False,
        expand=True,
        title=title,
        title_style="bold",
        border_style="dim",
        pad_edge=False,
        show_edge=False,
    )
    table.add_column("Metric", style="cyan", ratio=2)
    table.add_column("Value", style="white", ratio=3)

    for key, value in stats:
        table.add_row(key, value)

    return table


def ranked_table(
    rows: list[dict],
    columns: list[tuple[str, str]],
    title: str | None = None,
) -> Table:
    """Create a numbered ranking table.

    Args:
        rows: List of dicts with values for each column key.
        columns: List of (key, header_label) tuples defining columns.
        title: Optional table title.
    """
    table = Table(
        title=title,
        title_style="bold",
        border_style="dim",
        show_lines=False,
        expand=True,
    )
    table.add_column("#", style="dim", width=4, justify="right")
    for key, label in columns:
        if key in ("name", "track", "album", "artist"):
            table.add_column(label, style="white", ratio=3, no_wrap=True, overflow="ellipsis")
        else:
            table.add_column(label, style="bright_white", justify="right")

    for i, row in enumerate(rows, 1):
        values = [str(i)]
        for key, _ in columns:
            values.append(str(row.get(key, "")))
        table.add_row(*values)

    return table


def bar_chart(
    items: list[tuple[str, float]],
    title: str | None = None,
    max_width: int = 40,
    color: str = "bright_cyan",
) -> Table:
    """Create a horizontal bar chart using Rich Table."""
    if not items:
        return Table()

    max_val = max(v for _, v in items)

    table = Table(
        show_header=False,
        expand=True,
        title=title,
        title_style="bold",
        border_style="dim",
        pad_edge=False,
        show_edge=False,
    )
    table.add_column("Label", style="cyan", width=12)
    table.add_column("Bar", ratio=3)
    table.add_column("Value", style="white", justify="right", width=12)

    for label, value in items:
        bar_len = int((value / max_val) * max_width) if max_val > 0 else 0
        bar = Text("█" * bar_len, style=color)
        table.add_row(label, bar, f"{value:.1f}")

    return table
