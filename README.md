# Spotify Listening Insights

[![Release](https://img.shields.io/github/v/release/zachlagden/Spotify-Listening-Insights?style=flat-square)](https://github.com/zachlagden/Spotify-Listening-Insights/releases)
[![License](https://img.shields.io/github/license/zachlagden/Spotify-Listening-Insights?style=flat-square)](LICENCE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://python.org)
[![CI](https://img.shields.io/github/actions/workflow/status/zachlagden/Spotify-Listening-Insights/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/zachlagden/Spotify-Listening-Insights/actions)
[![Stars](https://img.shields.io/github/stars/zachlagden/Spotify-Listening-Insights?style=flat-square)](https://github.com/zachlagden/Spotify-Listening-Insights/stargazers)

Analyze your Spotify listening history with rich terminal output. Processes your Spotify privacy data export and generates detailed statistics about your listening habits, favourite artists, tracks, albums, and temporal patterns.

| Feature | Description |
|---------|-------------|
| Rich terminal output | Polished tables, panels, and bar charts using Rich |
| Interactive TUI | Browse sections with keyboard navigation using Textual |
| Pre-computed analysis | All stats computed upfront — no pauses between sections |
| Spotify API integration | Fill gaps in your data with recent plays from the API |
| Export | Save your full history and analysis to JSON or CSV |
| Multi-platform binaries | Download and run without installing Python |

## Quick Start

### Option 1: Download Binary

Download the latest binary for your platform from [Releases](https://github.com/zachlagden/Spotify-Listening-Insights/releases):

| Platform | Binary |
|----------|--------|
| Linux x86_64 | `spotify-insights-linux-x86_64` |
| macOS x86_64 | `spotify-insights-macos-x86_64` |
| macOS Apple Silicon | `spotify-insights-macos-aarch64` |
| Windows x86_64 | `spotify-insights-windows-x86_64.exe` |

```bash
# Linux/macOS
chmod +x spotify-insights-*
./spotify-insights-linux-x86_64 -d /path/to/spotify-data

# Windows
spotify-insights-windows-x86_64.exe -d C:\path\to\spotify-data
```

### Option 2: Install from Source

```bash
git clone https://github.com/zachlagden/Spotify-Listening-Insights.git
cd Spotify-Listening-Insights
pip install -e .
```

```bash
spotify-insights -d /path/to/spotify-data
# or
python -m spotify_insights -d /path/to/spotify-data
```

## How to Get Your Spotify Data

1. Go to your [Spotify Account Privacy Settings](https://www.spotify.com/account/privacy/)
2. Scroll down and request **Extended streaming history**
3. Wait for the email from Spotify (can take up to 30 days)
4. Download and extract the ZIP — you will get a folder with JSON files
5. Point `spotify-insights` at that folder

## Usage

```
spotify-insights [OPTIONS]

Options:
  -d, --directory PATH     Path to directory containing Spotify JSON files
  -o, --output [static|interactive|export]
                           Output mode (default: prompted)
  --export-format [json|csv]
                           Export format (default: json)
  --no-api                 Skip Spotify API integration
  --version                Show version
  --help                   Show this message
```

### Output Modes

- **static** — Print the full report to the terminal with Rich formatting
- **interactive** — Open a TUI where you can browse sections with arrow keys
- **export** — Save your full history and analysis summary to JSON or CSV

## Optional: Spotify API Setup

To fill gaps between your data export and now, you can connect to the Spotify API:

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/create)
2. Create a new application
3. Set the redirect URI to `http://localhost:8888/callback`
4. Create a `.env` file in your working directory:

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

## Development

```bash
pip install -e ".[dev]"
ruff check src/ tests/
ruff format --check src/ tests/
pytest
```

## Privacy

- All data is processed locally on your machine
- No data is sent to external servers
- API credentials are stored locally in `.env` and never committed

## License

[MIT](LICENCE) -- Zachariah Michael Lagden
