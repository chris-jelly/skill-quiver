"""Tests for manifest parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from skill_quiver.errors import ManifestError
from skill_quiver.manifest import Source, parse_manifest


class TestParseManifest:
    def test_valid_manifest(self, sample_manifest: Path) -> None:
        manifest = parse_manifest(sample_manifest)
        assert len(manifest.sources) == 1
        source = manifest.sources[0]
        assert source.name == "test-source"
        assert "github.com/example/repo" in str(source.repo)
        assert source.path == "skills"
        assert source.ref == "main"
        assert source.license == "MIT"
        assert source.skills == ["my-skill", "another-skill"]
        assert manifest.root == sample_manifest.parent

    def test_multiple_sources(self, tmp_path: Path) -> None:
        from tests.conftest import MULTI_SOURCE_KDL

        manifest_path = tmp_path / "skills.kdl"
        manifest_path.write_text(MULTI_SOURCE_KDL, encoding="utf-8")
        manifest = parse_manifest(manifest_path)
        assert len(manifest.sources) == 2
        assert manifest.sources[0].name == "alpha-source"
        assert manifest.sources[1].name == "beta-source"
        assert manifest.sources[1].ref == "v2"

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(ManifestError, match="Cannot read manifest"):
            parse_manifest(tmp_path / "nonexistent.kdl")

    def test_invalid_kdl_syntax(self, tmp_path: Path) -> None:
        bad_kdl = tmp_path / "skills.kdl"
        bad_kdl.write_text("{{{ not valid kdl", encoding="utf-8")
        with pytest.raises(ManifestError, match="Invalid KDL syntax"):
            parse_manifest(bad_kdl)

    def test_missing_required_fields(self, tmp_path: Path) -> None:
        """Source without name should fail validation."""
        kdl_content = """\
source {
    repo "https://github.com/example/repo"
    skill "my-skill"
}
"""
        manifest_path = tmp_path / "skills.kdl"
        manifest_path.write_text(kdl_content, encoding="utf-8")
        with pytest.raises(ManifestError, match="Invalid source"):
            parse_manifest(manifest_path)

    def test_invalid_source_name(self, tmp_path: Path) -> None:
        kdl_content = """\
source {
    name "Invalid Name"
    repo "https://github.com/example/repo"
    skill "my-skill"
}
"""
        manifest_path = tmp_path / "skills.kdl"
        manifest_path.write_text(kdl_content, encoding="utf-8")
        with pytest.raises(ManifestError, match="Invalid source"):
            parse_manifest(manifest_path)

    def test_optional_fields_defaults(self, tmp_path: Path) -> None:
        kdl_content = """\
source {
    name "minimal-source"
    repo "https://github.com/example/repo"
    skill "my-skill"
}
"""
        manifest_path = tmp_path / "skills.kdl"
        manifest_path.write_text(kdl_content, encoding="utf-8")
        manifest = parse_manifest(manifest_path)
        source = manifest.sources[0]
        assert source.path == "."
        assert source.ref == "main"
        assert source.license is None
        assert source.attribution is None

    def test_empty_manifest(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "skills.kdl"
        manifest_path.write_text("// empty manifest\n", encoding="utf-8")
        manifest = parse_manifest(manifest_path)
        assert manifest.sources == []


class TestSourceModel:
    def test_valid_source(self) -> None:
        source = Source(
            name="my-source",
            repo="https://github.com/example/repo",  # type: ignore[arg-type]
            skills=["skill-a", "skill-b"],
        )
        assert source.name == "my-source"

    def test_invalid_name_uppercase(self) -> None:
        with pytest.raises(Exception):
            Source(
                name="MySource",
                repo="https://github.com/example/repo",  # type: ignore[arg-type]
                skills=["skill-a"],
            )

    def test_invalid_name_consecutive_hyphens(self) -> None:
        with pytest.raises(Exception):
            Source(
                name="my--source",
                repo="https://github.com/example/repo",  # type: ignore[arg-type]
                skills=["skill-a"],
            )

    def test_empty_skills_list(self) -> None:
        with pytest.raises(Exception):
            Source(
                name="my-source",
                repo="https://github.com/example/repo",  # type: ignore[arg-type]
                skills=[],
            )
