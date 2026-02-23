"""Skill scaffolding: create new skill directories with templates."""

from __future__ import annotations

from pathlib import Path

from skill_quiver.errors import InitError
from skill_quiver.validate import validate_name

SKILL_MD_TEMPLATE = """\
---
name: {name}
description: TODO - describe what this skill does
triggers: TODO - list trigger phrases
---

# {name}

TODO - write skill instructions here.
"""

SUBDIRECTORIES = ["scripts", "references", "assets"]


def init_skill(
    name: str,
    output: Path | None = None,
    root: Path | None = None,
) -> Path:
    """Scaffold a new skill directory.

    Args:
        name: Name for the new skill (must be valid kebab-case).
        output: Custom output path. If None, uses skills/<name> under root.
        root: Root directory (used when output is None).

    Returns:
        Path to the created skill directory.

    Raises:
        InitError: If the name is invalid or directory already exists.
    """
    # Validate name
    errors = validate_name(name)
    if errors:
        raise InitError(f"Invalid skill name: {'; '.join(errors)}")

    # Resolve output path
    if output is not None:
        skill_dir = output / name
    elif root is not None:
        skill_dir = root / "skills" / name
    else:
        skill_dir = Path.cwd() / "skills" / name

    # Check if directory already exists
    if skill_dir.exists():
        raise InitError(f"Directory already exists: {skill_dir}")

    # Create directory structure
    skill_dir.mkdir(parents=True, exist_ok=False)

    # Write template SKILL.md
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(SKILL_MD_TEMPLATE.format(name=name), encoding="utf-8")

    # Create standard subdirectories with .gitkeep
    for subdir_name in SUBDIRECTORIES:
        subdir = skill_dir / subdir_name
        subdir.mkdir()
        gitkeep = subdir / ".gitkeep"
        gitkeep.touch()

    print(f"Created skill '{name}' at {skill_dir}")
    return skill_dir
