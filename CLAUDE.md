# CLAUDE.md

This file provides context to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

Spotify Listening Insights is a Python CLI tool that analyzes Spotify privacy data exports and generates rich terminal listening statistics, with an optional interactive TUI mode.

## Tech Stack

- **Language**: Python 3.10+
- **CLI**: Click
- **Terminal UI**: Rich (static output) + Textual (interactive TUI)
- **Data**: pandas, numpy
- **Spotify API**: spotipy
- **Testing**: pytest
- **Linting**: ruff

## Project Structure

```
src/spotify_insights/
  __init__.py       — Package metadata, __version__
  __main__.py       — Entry point (python -m spotify_insights)
  cli.py            — Click CLI argument parsing
  loader.py         — JSON file discovery/loading + Spotify API fetch
  processor.py      — Deduplication, timestamp enrichment, DataFrame prep
  analyzer.py       — All statistics computation, returns typed dataclasses
  models.py         — Dataclasses for all analysis results
  exporter.py       — Export to JSON/CSV
  utils.py          — format_duration, format_size helpers
  ui/
    static.py       — Rich static output (tables, panels, bars)
    interactive.py  — Textual TUI app
    components.py   — Shared Rich renderables
tests/
  conftest.py       — Shared fixtures (sample DataFrames, mock data)
  test_loader.py
  test_processor.py
  test_analyzer.py
```

## Development

### Setup

```bash
git clone https://github.com/zachlagden/Spotify-Listening-Insights.git
cd Spotify-Listening-Insights
pip install -e ".[dev]"
```

### Running

```bash
spotify-insights --help
spotify-insights -d /path/to/spotify/data
python -m spotify_insights -d /path/to/spotify/data
```

### Testing

```bash
pytest
```

### Linting

```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

## Common Patterns

- All analysis results are typed dataclasses in `models.py`
- Analysis functions in `analyzer.py` return dataclass instances, never print
- All terminal output goes through Rich renderables in `ui/`
- The pipeline is: load -> process -> analyze -> render (compute-first, no pauses)

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `SPOTIFY_CLIENT_ID` | Spotify API client ID (optional, for gap filling) |
| `SPOTIFY_CLIENT_SECRET` | Spotify API client secret (optional, for gap filling) |

## Notes

- Data processing uses UTC timestamps throughout
- The `--no-api` flag skips all Spotify API integration
- Export supports both JSON and CSV formats
