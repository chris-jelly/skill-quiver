"""Provenance tracking via .source.kdl files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import kdl
from pydantic import BaseModel

from skill_quiver.errors import SyncError

PROVENANCE_FILENAME = ".source.kdl"


class Provenance(BaseModel):
    """Provenance information for a fetched skill."""

    repo: str
    path: str
    ref: str
    sha: str
    license: str | None = None
    fetched: datetime


def write_provenance(skill_dir: Path, provenance: Provenance) -> None:
    """Write provenance information to .source.kdl.

    Args:
        skill_dir: Path to the skill directory.
        provenance: Provenance data to write.
    """
    doc = kdl.Document()
    node = kdl.Node(name="source")
    node.props["repo"] = provenance.repo
    node.props["path"] = provenance.path
    node.props["ref"] = provenance.ref
    node.props["sha"] = provenance.sha
    if provenance.license is not None:
        node.props["license"] = provenance.license
    node.props["fetched"] = provenance.fetched.isoformat()
    doc.nodes.append(node)

    out_path = skill_dir / PROVENANCE_FILENAME
    out_path.write_text(str(doc) + "\n", encoding="utf-8")


def read_provenance(skill_dir: Path) -> Provenance | None:
    """Read provenance information from .source.kdl.

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        Provenance object, or None if file doesn't exist.

    Raises:
        SyncError: If the file exists but cannot be parsed.
    """
    source_file = skill_dir / PROVENANCE_FILENAME
    if not source_file.is_file():
        return None

    try:
        content = source_file.read_text(encoding="utf-8")
        doc = kdl.parse(content)
    except Exception as e:
        raise SyncError(f"Cannot parse {source_file}: {e}") from e

    for node in doc.nodes:
        if node.name == "source":
            props: dict[str, object] = {}
            for key, value in node.props.items():
                props[key] = value
            # Parse fetched as datetime
            if "fetched" in props and isinstance(props["fetched"], str):
                props["fetched"] = datetime.fromisoformat(props["fetched"])
            try:
                return Provenance.model_validate(props)
            except Exception as e:
                raise SyncError(f"Invalid provenance data in {source_file}: {e}") from e

    return None
