"""Tests for the CLI framework."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from skill_quiver import __version__
from skill_quiver.cli import find_manifest, main


class TestVersion:
    def test_version_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert __version__ in captured.out

    def test_version_via_subprocess(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "skill_quiver", "--version"],
            capture_output=True,
            text=True,
        )
        assert __version__ in result.stdout


class TestHelp:
    def test_no_args_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        main([])
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "commands" in captured.out.lower()

    def test_help_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "sync" in captured.out
        assert "validate" in captured.out
        assert "init" in captured.out
        assert "package" in captured.out

    def test_sync_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["sync", "--help"])
        assert exc_info.value.code == 0


class TestDirFlag:
    def test_valid_dir(self, tmp_path: Path) -> None:
        """--dir with a valid directory should not error on its own."""
        # Will fail because no manifest, but should not fail on dir check
        with pytest.raises(SystemExit):
            main(["--dir", str(tmp_path), "validate"])

    def test_invalid_dir(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--dir", "/nonexistent/path", "validate"])
        assert exc_info.value.code != 0


class TestFindManifest:
    def test_manifest_in_current_dir(self, tmp_path: Path) -> None:
        manifest = tmp_path / "skills.kdl"
        manifest.touch()
        result = find_manifest(tmp_path)
        assert result == manifest

    def test_manifest_in_parent(self, tmp_path: Path) -> None:
        manifest = tmp_path / "skills.kdl"
        manifest.touch()
        sub = tmp_path / "sub" / "dir"
        sub.mkdir(parents=True)
        result = find_manifest(sub)
        assert result == manifest

    def test_no_manifest(self, tmp_path: Path) -> None:
        from skill_quiver.errors import QuivError

        with pytest.raises(QuivError, match="No skills.kdl found"):
            find_manifest(tmp_path)


class TestUnknownCommand:
    def test_unknown_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["unknowncommand"])
        assert exc_info.value.code != 0
