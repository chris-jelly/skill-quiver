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


def init_repo(target: Path) -> Path:
    """Initialize a skill-quiver project directory.

    Creates skills.kdl and skills/ directory with .gitkeep.

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

    # Print summary
    created = [
        "skills.kdl",
        "skills/",
        "skills/.gitkeep",
    ]
    print(f"Initialized skill-quiver project at {target}")
    for item in created:
        print(f"  {item}")

    return target
