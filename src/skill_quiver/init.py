"""Repository initialization: set up a new skill-quiver project."""

from pathlib import Path

from skill_quiver.errors import InitError

SKILLS_KDL_TEMPLATE = """\
// Add sources to fetch skills from.
// Example:
//
// source {
//     name "community-skills"
//     repo "https://github.com/org/ai-skills"
//     path "skills"
//     ref "main"
//     license "MIT"
//     skill "code-reviewer"
//     skill "readme-writer"
// }
"""

GITIGNORE_MARKER = "# quiv - provenance tracking files are machine-generated"
GITIGNORE_ENTRIES = f"""\
{GITIGNORE_MARKER}
skills/**/.source.kdl
"""


def _configure_gitignore(target: Path) -> bool:
    """Create or append quiv entries to .gitignore.

    Returns True if .gitignore was created or modified, False if entries
    were already present.
    """
    gitignore = target / ".gitignore"

    if gitignore.is_file():
        existing = gitignore.read_text(encoding="utf-8")
        if GITIGNORE_MARKER in existing:
            return False
        # Append with a leading newline if file doesn't end with one
        separator = "" if existing.endswith("\n") else "\n"
        gitignore.write_text(existing + separator + GITIGNORE_ENTRIES, encoding="utf-8")
    else:
        gitignore.write_text(GITIGNORE_ENTRIES, encoding="utf-8")

    return True


def init_repo(target: Path) -> Path:
    """Initialize a skill-quiver project directory.

    Creates skills.kdl, skills/ directory with .gitkeep, and configures
    .gitignore with quiv-specific entries.

    Args:
        target: Directory to initialize. Must exist.

    Returns:
        Path to the initialized directory.

    Raises:
        InitError: If skills.kdl already exists in the target directory.
    """
    manifest = target / "skills.kdl"
    if manifest.is_file():
        raise InitError("Already initialized (skills.kdl exists)")

    # Create skills.kdl
    manifest.write_text(SKILLS_KDL_TEMPLATE, encoding="utf-8")

    # Create skills/ directory with .gitkeep
    skills_dir = target / "skills"
    skills_dir.mkdir(exist_ok=True)
    (skills_dir / ".gitkeep").touch()

    # Configure .gitignore
    _configure_gitignore(target)

    # Print summary
    created = [
        "skills.kdl",
        "skills/",
        "skills/.gitkeep",
        ".gitignore",
    ]
    print(f"Initialized skill-quiver project at {target}")
    for item in created:
        print(f"  {item}")

    return target
