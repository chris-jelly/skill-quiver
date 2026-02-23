"""Skill validation: name format, SKILL.md frontmatter, directory structure."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, field_validator

from skill_quiver.manifest import NAME_PATTERN

NAME_MAX_LENGTH = 64


class SkillFrontmatter(BaseModel):
    """Expected YAML frontmatter fields in SKILL.md."""

    name: str
    description: str

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        if not NAME_PATTERN.match(v):
            raise ValueError(
                f"Invalid skill name '{v}': must be lowercase alphanumeric "
                "with single hyphens"
            )
        if len(v) > NAME_MAX_LENGTH:
            raise ValueError(
                f"Invalid skill name '{v}': must be {NAME_MAX_LENGTH} characters or fewer"
            )
        return v


def validate_name(name: str) -> list[str]:
    """Validate a skill name against naming conventions.

    Args:
        name: The skill name to validate.

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []

    if not name:
        errors.append("Skill name must not be empty")
        return errors

    if len(name) > NAME_MAX_LENGTH:
        errors.append(f"Skill name '{name}' exceeds {NAME_MAX_LENGTH} characters")

    if not NAME_PATTERN.match(name):
        specifics: list[str] = []
        if re.search(r"[A-Z]", name):
            specifics.append("contains uppercase letters")
        if " " in name:
            specifics.append("contains spaces")
        if "--" in name:
            specifics.append("contains consecutive hyphens")
        if name.startswith("-") or name.endswith("-"):
            specifics.append("starts or ends with a hyphen")
        if not re.match(r"^[a-z0-9-]+$", name):
            specifics.append("contains invalid characters")

        detail = "; ".join(specifics) if specifics else "invalid format"
        errors.append(
            f"Invalid skill name '{name}': {detail}. "
            "Must be lowercase alphanumeric with single hyphens."
        )

    return errors


def validate_frontmatter(skill_dir: Path) -> list[str]:
    """Validate SKILL.md frontmatter in a skill directory.

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.is_file():
        errors.append(f"Missing SKILL.md in {skill_dir.name}")
        return errors

    try:
        content = skill_md.read_text(encoding="utf-8")
    except OSError as e:
        errors.append(f"Cannot read SKILL.md: {e}")
        return errors

    # Extract YAML frontmatter
    if not content.startswith("---"):
        errors.append(f"Missing YAML frontmatter in {skill_dir.name}/SKILL.md")
        return errors

    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append(f"Malformed YAML frontmatter in {skill_dir.name}/SKILL.md")
        return errors

    frontmatter_text = parts[1].strip()
    if not frontmatter_text:
        errors.append(f"Empty YAML frontmatter in {skill_dir.name}/SKILL.md")
        return errors

    # Parse YAML frontmatter (simple key: value parsing)
    import yaml

    try:
        data = yaml.safe_load(frontmatter_text)
    except Exception as e:
        errors.append(f"Invalid YAML frontmatter in {skill_dir.name}/SKILL.md: {e}")
        return errors

    if not isinstance(data, dict):
        errors.append(
            f"YAML frontmatter must be a mapping in {skill_dir.name}/SKILL.md"
        )
        return errors

    # Validate with Pydantic model
    try:
        SkillFrontmatter.model_validate(data)
    except Exception as e:
        errors.append(f"Invalid frontmatter in {skill_dir.name}/SKILL.md: {e}")

    return errors


def validate_skill(skill_dir: Path) -> list[str]:
    """Validate a single skill directory.

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        List of error messages (empty if valid).
    """
    errors: list[str] = []

    # Validate directory name
    errors.extend(validate_name(skill_dir.name))

    # Validate frontmatter
    fm_errors = validate_frontmatter(skill_dir)
    errors.extend(fm_errors)

    # Check name/directory mismatch (only if frontmatter parsed successfully)
    if not fm_errors:
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        if len(parts) >= 3:
            import yaml

            data = yaml.safe_load(parts[1].strip())
            if isinstance(data, dict) and "name" in data:
                fm_name = data["name"]
                if fm_name != skill_dir.name:
                    errors.append(
                        f"Name mismatch: frontmatter name '{fm_name}' "
                        f"does not match directory name '{skill_dir.name}'"
                    )

    return errors


def validate_all(root: Path, skill_name: str | None = None) -> dict[str, list[str]]:
    """Validate all skills in a directory or a specific skill.

    Args:
        root: Root directory containing the skills/ subdirectory.
        skill_name: Optional specific skill to validate.

    Returns:
        Dict mapping skill names to their error lists.
    """
    skills_dir = root / "skills"
    results: dict[str, list[str]] = {}

    if skill_name:
        skill_dir = skills_dir / skill_name
        if not skill_dir.is_dir():
            results[skill_name] = [f"Skill directory not found: {skill_dir}"]
        else:
            results[skill_name] = validate_skill(skill_dir)
    else:
        if not skills_dir.is_dir():
            return results
        for entry in sorted(skills_dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith("."):
                results[entry.name] = validate_skill(entry)

    return results
