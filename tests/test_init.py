"""Tests for repository initialization."""

from pathlib import Path

import pytest

from skill_quiver.errors import InitError
from skill_quiver.init import SKILLS_KDL_TEMPLATE, init_repo


class TestInitRepo:
    def test_successful_repo_init(self, tmp_path: Path) -> None:
        """Init creates skills.kdl, skills/, skills/.gitkeep; does not create .gitignore."""
        result = init_repo(tmp_path)
        assert result == tmp_path
        assert (tmp_path / "skills.kdl").is_file()
        assert (tmp_path / "skills").is_dir()
        assert (tmp_path / "skills" / ".gitkeep").is_file()
        assert not (tmp_path / ".gitignore").exists()

    def test_skills_kdl_content(self, tmp_path: Path) -> None:
        """skills.kdl matches the template with commented example."""
        init_repo(tmp_path)
        content = (tmp_path / "skills.kdl").read_text(encoding="utf-8")
        assert content == SKILLS_KDL_TEMPLATE
        assert "// source {" in content
        assert 'name "community-skills"' in content

    def test_already_initialized_error(self, tmp_path: Path) -> None:
        """Raises InitError when skills.kdl already exists."""
        (tmp_path / "skills.kdl").write_text("existing", encoding="utf-8")
        with pytest.raises(InitError, match="Already initialized"):
            init_repo(tmp_path)

    def test_dir_with_nonexistent_directory(self, tmp_path: Path) -> None:
        """--dir creates non-existent directory and initializes inside."""
        new_dir = tmp_path / "new-project"
        assert not new_dir.exists()
        new_dir.mkdir()
        result = init_repo(new_dir)
        assert result == new_dir
        assert (new_dir / "skills.kdl").is_file()
        assert (new_dir / "skills").is_dir()
