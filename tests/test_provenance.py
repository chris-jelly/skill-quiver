"""Tests for provenance tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from skill_quiver.errors import SyncError
from skill_quiver.provenance import Provenance, read_provenance, write_provenance


class TestProvenanceRoundTrip:
    def test_write_and_read(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()

        prov = Provenance(
            repo="https://github.com/example/repo",
            path="skills",
            ref="main",
            sha="abc123def456",
            license="MIT",
            fetched=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )

        write_provenance(skill_dir, prov)

        # Verify file was created
        source_file = skill_dir / ".source.kdl"
        assert source_file.is_file()

        # Read back
        result = read_provenance(skill_dir)
        assert result is not None
        assert result.repo == "https://github.com/example/repo"
        assert result.path == "skills"
        assert result.ref == "main"
        assert result.sha == "abc123def456"
        assert result.license == "MIT"
        assert result.fetched.year == 2025

    def test_write_without_license(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()

        prov = Provenance(
            repo="https://github.com/example/repo",
            path=".",
            ref="v2",
            sha="deadbeef",
            license=None,
            fetched=datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        )

        write_provenance(skill_dir, prov)
        result = read_provenance(skill_dir)
        assert result is not None
        assert result.license is None


class TestReadProvenance:
    def test_missing_file(self, tmp_path: Path) -> None:
        result = read_provenance(tmp_path)
        assert result is None

    def test_invalid_kdl_content(self, tmp_path: Path) -> None:
        source_file = tmp_path / ".source.kdl"
        source_file.write_text("{{{ invalid", encoding="utf-8")
        with pytest.raises(SyncError, match="Cannot parse"):
            read_provenance(tmp_path)


class TestProvenanceModel:
    def test_required_fields(self) -> None:
        prov = Provenance(
            repo="https://example.com",
            path=".",
            ref="main",
            sha="abc123",
            fetched=datetime.now(timezone.utc),
        )
        assert prov.license is None

    def test_all_fields(self) -> None:
        prov = Provenance(
            repo="https://example.com",
            path="skills",
            ref="v1",
            sha="abc123",
            license="MIT",
            fetched=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        assert prov.license == "MIT"
