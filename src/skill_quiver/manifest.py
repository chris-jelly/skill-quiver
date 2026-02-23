"""KDL manifest parsing and Pydantic models for skills.kdl."""

from __future__ import annotations

import re
from pathlib import Path

import kdl
from pydantic import BaseModel, HttpUrl, field_validator

from skill_quiver.errors import ManifestError

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _validate_kebab_case(name: str) -> str:
    """Validate a kebab-case name."""
    if not NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid name '{name}': must be lowercase alphanumeric with single hyphens, "
            "no leading/trailing hyphens, no consecutive hyphens"
        )
    if len(name) > 64:
        raise ValueError(f"Invalid name '{name}': must be 64 characters or fewer")
    return name


class Source(BaseModel):
    """A single source definition from skills.kdl."""

    name: str
    repo: HttpUrl
    path: str = "."
    ref: str = "main"
    license: str | None = None
    attribution: str | None = None
    skills: list[str]

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _validate_kebab_case(v)

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: list[str]) -> list[str]:
        if len(v) < 1:
            raise ValueError("At least one skill must be specified")
        for skill_name in v:
            _validate_kebab_case(skill_name)
        return v


class Manifest(BaseModel):
    """Parsed skills.kdl manifest."""

    sources: list[Source]
    root: Path


def parse_manifest(path: Path) -> Manifest:
    """Parse a skills.kdl manifest file.

    Args:
        path: Path to the skills.kdl file.

    Returns:
        Parsed Manifest object.

    Raises:
        ManifestError: If the file cannot be parsed or validated.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ManifestError(f"Cannot read manifest: {e}") from e

    try:
        doc = kdl.parse(content)
    except Exception as e:
        raise ManifestError(f"Invalid KDL syntax in {path}: {e}") from e

    sources: list[Source] = []
    for node in doc.nodes:
        if node.name != "source":
            continue

        props: dict[str, object] = {}
        skills: list[str] = []

        # Extract properties from node props (key=value syntax)
        for key, value in node.props.items():
            props[key] = value

        # Extract from child nodes (key "value" syntax in KDL)
        for child in node.nodes:
            if child.name == "skill":
                if child.args:
                    skills.append(str(child.args[0]))
            elif child.args:
                # Single-argument child node: treat as key-value pair
                props[child.name] = child.args[0]

        props["skills"] = skills

        try:
            source = Source.model_validate(props)
        except Exception as e:
            source_name = props.get("name", "<unnamed>")
            raise ManifestError(f"Invalid source '{source_name}' in {path}: {e}") from e

        sources.append(source)

    return Manifest(sources=sources, root=path.parent)
