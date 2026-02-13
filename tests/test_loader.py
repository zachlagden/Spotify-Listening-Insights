"""Tests for the loader module."""

from __future__ import annotations

from pathlib import Path

import pytest

from spotify_insights.loader import discover_files, load_all_files, load_file


class TestDiscoverFiles:
    def test_discovers_json_files(self, sample_json_dir: Path) -> None:
        files = discover_files(str(sample_json_dir))
        assert len(files) == 2
        assert all(f.suffix == ".json" for f in files)

    def test_raises_on_missing_dir(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            discover_files(str(tmp_path / "nonexistent"))

    def test_raises_on_empty_dir(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="No JSON files found"):
            discover_files(str(tmp_path))


class TestLoadFile:
    def test_loads_entries(self, sample_json_file: Path) -> None:
        data, stats = load_file(sample_json_file)
        assert len(data) == 10
        assert stats["entries"] == 10
        assert stats["earliest_entry"] is not None
        assert stats["latest_entry"] is not None

    def test_collects_unique_tracks(self, sample_json_file: Path) -> None:
        _, stats = load_file(sample_json_file)
        # Songs A-F = 6 unique tracks
        assert len(stats["unique_tracks"]) == 6

    def test_collects_unique_artists(self, sample_json_file: Path) -> None:
        _, stats = load_file(sample_json_file)
        # Artists 1-4 = 4 unique artists
        assert len(stats["unique_artists"]) == 4


class TestLoadAllFiles:
    def test_loads_all_from_directory(self, sample_json_dir: Path) -> None:
        files = discover_files(str(sample_json_dir))
        all_history, file_stats, proc_stats = load_all_files(files)
        assert len(all_history) == 10
        assert proc_stats.files_processed == 2
        assert proc_stats.total_entries == 10
        assert len(file_stats) == 2
