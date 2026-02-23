"""Tests for skill validation."""

from pathlib import Path


from skill_quiver.validate import (
    validate_all,
    validate_frontmatter,
    validate_name,
    validate_skill,
)


class TestValidateName:
    def test_valid_names(self) -> None:
        assert validate_name("my-skill") == []
        assert validate_name("a") == []
        assert validate_name("skill-123") == []
        assert validate_name("a-b-c") == []

    def test_empty_name(self) -> None:
        errors = validate_name("")
        assert len(errors) > 0
        assert "empty" in errors[0].lower()

    def test_uppercase(self) -> None:
        errors = validate_name("MySkill")
        assert len(errors) > 0
        assert "uppercase" in errors[0].lower()

    def test_spaces(self) -> None:
        errors = validate_name("my skill")
        assert len(errors) > 0
        assert "spaces" in errors[0].lower()

    def test_consecutive_hyphens(self) -> None:
        errors = validate_name("my--skill")
        assert len(errors) > 0
        assert "consecutive" in errors[0].lower()

    def test_leading_hyphen(self) -> None:
        errors = validate_name("-skill")
        assert len(errors) > 0

    def test_trailing_hyphen(self) -> None:
        errors = validate_name("skill-")
        assert len(errors) > 0

    def test_too_long(self) -> None:
        errors = validate_name("a" * 65)
        assert len(errors) > 0
        assert "64" in errors[0] or "exceed" in errors[0].lower()

    def test_max_length_ok(self) -> None:
        assert validate_name("a" * 64) == []


class TestValidateFrontmatter:
    def test_valid_frontmatter(self, sample_skill_dir: Path) -> None:
        errors = validate_frontmatter(sample_skill_dir)
        assert errors == []

    def test_missing_skill_md(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        errors = validate_frontmatter(skill_dir)
        assert len(errors) > 0
        assert "Missing SKILL.md" in errors[0]

    def test_no_frontmatter(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# No frontmatter\n", encoding="utf-8")
        errors = validate_frontmatter(skill_dir)
        assert len(errors) > 0
        assert "Missing YAML frontmatter" in errors[0]

    def test_empty_frontmatter(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\n---\n# Content\n", encoding="utf-8")
        errors = validate_frontmatter(skill_dir)
        assert len(errors) > 0

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n: invalid: yaml:\n---\n", encoding="utf-8"
        )
        errors = validate_frontmatter(skill_dir)
        assert len(errors) > 0


class TestValidateSkill:
    def test_valid_skill(self, sample_skill_dir: Path) -> None:
        errors = validate_skill(sample_skill_dir)
        assert errors == []

    def test_name_directory_mismatch(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "wrong-name"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: actual-name\ndescription: test\n---\n# Content\n",
            encoding="utf-8",
        )
        errors = validate_skill(skill_dir)
        assert any("mismatch" in e.lower() for e in errors)


class TestValidateAll:
    def test_validate_all_skills(self, sample_root: Path) -> None:
        results = validate_all(sample_root)
        assert "my-skill" in results
        assert results["my-skill"] == []

    def test_validate_specific_skill(self, sample_root: Path) -> None:
        results = validate_all(sample_root, skill_name="my-skill")
        assert "my-skill" in results

    def test_validate_nonexistent_skill(self, sample_root: Path) -> None:
        results = validate_all(sample_root, skill_name="nonexistent")
        assert "nonexistent" in results
        assert len(results["nonexistent"]) > 0

    def test_no_skills_directory(self, tmp_path: Path) -> None:
        (tmp_path / "skills.kdl").touch()
        results = validate_all(tmp_path)
        assert results == {}

    def test_batch_validation(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"

        # Valid skill
        valid = skills_dir / "valid-skill"
        valid.mkdir(parents=True)
        (valid / "SKILL.md").write_text(
            "---\nname: valid-skill\ndescription: test\n---\n# Content\n",
            encoding="utf-8",
        )

        # Invalid skill (no SKILL.md)
        invalid = skills_dir / "invalid-skill"
        invalid.mkdir()

        results = validate_all(tmp_path)
        assert results["valid-skill"] == []
        assert len(results["invalid-skill"]) > 0
