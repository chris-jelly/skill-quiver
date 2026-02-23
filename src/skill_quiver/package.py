"""Skill packaging: create distributable zip archives."""

from __future__ import annotations

import zipfile
from pathlib import Path

from skill_quiver.errors import PackageError


def package_skill(skill_dir: Path, output: Path | None = None) -> Path:
    """Package a skill directory as a zip archive.

    Args:
        skill_dir: Path to the skill directory.
        output: Custom output path for the zip file.

    Returns:
        Path to the created zip archive.

    Raises:
        PackageError: If skill is invalid or packaging fails.
    """
    # Validate skill exists
    if not skill_dir.is_dir():
        raise PackageError(f"Skill directory not found: {skill_dir}")

    # Check SKILL.md exists
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise PackageError(f"Missing SKILL.md in {skill_dir}")

    # Run validation
    from skill_quiver.validate import validate_skill

    errors = validate_skill(skill_dir)
    if errors:
        raise PackageError(
            f"Validation failed for '{skill_dir.name}': {'; '.join(errors)}"
        )

    # Determine output path
    skill_name = skill_dir.name
    if output is not None:
        zip_path = output
    else:
        zip_path = Path.cwd() / f"{skill_name}.zip"

    # Collect files (exclude hidden files)
    files_to_package: list[Path] = []
    for file_path in sorted(skill_dir.rglob("*")):
        if file_path.is_file():
            # Skip hidden files (any path component starting with .)
            relative = file_path.relative_to(skill_dir)
            if any(part.startswith(".") for part in relative.parts):
                continue
            files_to_package.append(file_path)

    # Create zip
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in files_to_package:
                arcname = file_path.relative_to(skill_dir.parent)
                zf.write(file_path, arcname)
    except OSError as e:
        raise PackageError(f"Failed to create archive: {e}") from e

    # Report results
    archive_size = zip_path.stat().st_size
    file_count = len(files_to_package)
    _format_size = _human_size(archive_size)
    print(f"Packaged '{skill_name}': {file_count} files, {_format_size}")
    print(f"Archive: {zip_path}")

    return zip_path


def _human_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} {unit}"
        size_bytes /= 1024  # type: ignore[assignment]
    return f"{size_bytes:.1f} TB"
