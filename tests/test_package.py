"""Tests for skill packaging."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from skill_quiver.errors import PackageError
from skill_quiver.package import package_skill


def _create_valid_skill(parent: Path, name: str = "my-skill") -> Path:
    """Helper to create a valid skill directory for packaging tests."""
    skill_dir = parent / "skills" / name
    skill_dir.mkdir(parents=True)

    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test\n---\n# {name}\nContent\n",
        encoding="utf-8",
    )
    scripts = skill_dir / "scripts"
    scripts.mkdir()
    (scripts / "helper.sh").write_text("#!/bin/bash\necho hello\n", encoding="utf-8")

    # Hidden file (should be excluded)
    (skill_dir / ".source.kdl").write_text("source {}", encoding="utf-8")

    return skill_dir


class TestPackageSkill:
    def test_successful_packaging(self, tmp_path: Path) -> None:
        skill_dir = _create_valid_skill(tmp_path)
        output = tmp_path / "output.zip"
        result = package_skill(skill_dir, output=output)
        assert result == output
        assert output.is_file()

        # Verify zip contents
        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            assert any("SKILL.md" in n for n in names)
            assert any("helper.sh" in n for n in names)

    def test_missing_skill_dir(self, tmp_path: Path) -> None:
        with pytest.raises(PackageError, match="not found"):
            package_skill(tmp_path / "nonexistent")

    def test_missing_skill_md(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "skills" / "no-md"
        skill_dir.mkdir(parents=True)
        with pytest.raises(PackageError, match="Missing SKILL.md"):
            package_skill(skill_dir)

    def test_hidden_file_exclusion(self, tmp_path: Path) -> None:
        skill_dir = _create_valid_skill(tmp_path)
        output = tmp_path / "output.zip"
        package_skill(skill_dir, output=output)

        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            assert not any(".source.kdl" in n for n in names)

    def test_custom_output_path(self, tmp_path: Path) -> None:
        skill_dir = _create_valid_skill(tmp_path)
        custom_output = tmp_path / "custom" / "archive.zip"
        custom_output.parent.mkdir(parents=True)
        result = package_skill(skill_dir, output=custom_output)
        assert result == custom_output
        assert custom_output.is_file()

    def test_default_output_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        skill_dir = _create_valid_skill(tmp_path)
        monkeypatch.chdir(tmp_path)
        result = package_skill(skill_dir)
        assert result.name == "my-skill.zip"
