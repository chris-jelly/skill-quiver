"""Tests for skill initialization."""

from __future__ import annotations

from pathlib import Path

import pytest

from skill_quiver.errors import InitError
from skill_quiver.init import init_skill


class TestInitSkill:
    def test_successful_scaffold(self, tmp_path: Path) -> None:
        result = init_skill("my-skill", root=tmp_path)
        assert result.is_dir()
        assert (result / "SKILL.md").is_file()
        assert (result / "scripts").is_dir()
        assert (result / "references").is_dir()
        assert (result / "assets").is_dir()
        assert (result / "scripts" / ".gitkeep").is_file()

    def test_skill_md_content(self, tmp_path: Path) -> None:
        result = init_skill("test-skill", root=tmp_path)
        content = (result / "SKILL.md").read_text(encoding="utf-8")
        assert "name: test-skill" in content
        assert "description:" in content

    def test_existing_directory_error(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        with pytest.raises(InitError, match="already exists"):
            init_skill("my-skill", root=tmp_path)

    def test_invalid_name_rejection(self, tmp_path: Path) -> None:
        with pytest.raises(InitError, match="Invalid skill name"):
            init_skill("Invalid Name", root=tmp_path)

    def test_custom_output_path(self, tmp_path: Path) -> None:
        custom = tmp_path / "custom" / "output"
        custom.mkdir(parents=True)
        result = init_skill("my-skill", output=custom)
        assert result == custom / "my-skill"
        assert result.is_dir()

    def test_parent_directory_creation(self, tmp_path: Path) -> None:
        """Root skills/ dir doesn't exist yet -- should be created."""
        result = init_skill("my-skill", root=tmp_path)
        assert result.is_dir()
        assert (tmp_path / "skills").is_dir()
