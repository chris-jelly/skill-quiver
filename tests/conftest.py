"""Shared test fixtures for skill-quiver tests."""

from __future__ import annotations

from pathlib import Path

import pytest

VALID_SKILL_MD = """\
---
name: my-skill
description: A test skill
triggers: test trigger
---

# my-skill

Test skill content.
"""

VALID_KDL_MANIFEST = """\
source {
    name "test-source"
    repo "https://github.com/example/repo"
    path "skills"
    ref "main"
    license "MIT"
    skill "my-skill"
    skill "another-skill"
}
"""

MULTI_SOURCE_KDL = """\
source {
    name "alpha-source"
    repo "https://github.com/alpha/repo"
    path "."
    license "Apache-2.0"
    skill "skill-a"
}

source {
    name "beta-source"
    repo "https://github.com/beta/repo"
    path "skills"
    ref "v2"
    skill "skill-b"
    skill "skill-c"
}
"""


@pytest.fixture
def sample_manifest(tmp_path: Path) -> Path:
    """Create a sample skills.kdl manifest file."""
    manifest_path = tmp_path / "skills.kdl"
    manifest_path.write_text(VALID_KDL_MANIFEST, encoding="utf-8")
    return manifest_path


@pytest.fixture
def sample_skill_dir(tmp_path: Path) -> Path:
    """Create a sample valid skill directory."""
    skills_dir = tmp_path / "skills" / "my-skill"
    skills_dir.mkdir(parents=True)

    skill_md = skills_dir / "SKILL.md"
    skill_md.write_text(VALID_SKILL_MD, encoding="utf-8")

    for subdir in ("scripts", "references", "assets"):
        (skills_dir / subdir).mkdir()
        (skills_dir / subdir / ".gitkeep").touch()

    return skills_dir


@pytest.fixture
def sample_root(tmp_path: Path, sample_manifest: Path, sample_skill_dir: Path) -> Path:
    """Create a full sample project root with manifest and skill."""
    return tmp_path
