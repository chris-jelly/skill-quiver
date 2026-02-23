"""Tests for repository initialization."""

from pathlib import Path

import pytest

from skill_quiver.errors import InitError
from skill_quiver.init import GITIGNORE_MARKER, SKILLS_KDL_TEMPLATE, init_repo


class TestInitRepo:
    def test_successful_repo_init(self, tmp_path: Path) -> None:
        """Init creates skills.kdl, skills/, skills/.gitkeep, .gitignore."""
        result = init_repo(tmp_path)
        assert result == tmp_path
        assert (tmp_path / "skills.kdl").is_file()
        assert (tmp_path / "skills").is_dir()
        assert (tmp_path / "skills" / ".gitkeep").is_file()
        assert (tmp_path / ".gitignore").is_file()

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

    def test_gitignore_created_when_none_exists(self, tmp_path: Path) -> None:
        """.gitignore created with quiv entries when none exists."""
        init_repo(tmp_path)
        content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert GITIGNORE_MARKER in content
        assert "skills/**/.source.kdl" in content

    def test_gitignore_appended_when_exists(self, tmp_path: Path) -> None:
        """.gitignore is appended to, preserving existing content."""
        existing_content = "node_modules/\n*.pyc\n"
        (tmp_path / ".gitignore").write_text(existing_content, encoding="utf-8")
        init_repo(tmp_path)
        content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert content.startswith("node_modules/\n*.pyc\n")
        assert GITIGNORE_MARKER in content
        assert "skills/**/.source.kdl" in content

    def test_gitignore_not_duplicated(self, tmp_path: Path) -> None:
        """.gitignore entries not duplicated if already present."""
        existing_content = f"*.pyc\n{GITIGNORE_MARKER}\nskills/**/.source.kdl\n"
        (tmp_path / ".gitignore").write_text(existing_content, encoding="utf-8")
        init_repo(tmp_path)
        content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert content == existing_content

    def test_dir_with_nonexistent_directory(self, tmp_path: Path) -> None:
        """--dir creates non-existent directory and initializes inside."""
        new_dir = tmp_path / "new-project"
        assert not new_dir.exists()
        new_dir.mkdir()
        result = init_repo(new_dir)
        assert result == new_dir
        assert (new_dir / "skills.kdl").is_file()
        assert (new_dir / "skills").is_dir()
