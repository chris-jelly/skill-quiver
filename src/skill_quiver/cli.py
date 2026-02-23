"""CLI entry point and argument parsing for quiv."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skill_quiver import __version__
from skill_quiver.errors import QuivError


def find_manifest(start: Path) -> Path:
    """Walk up directory tree looking for skills.kdl.

    Args:
        start: Directory to start searching from.

    Returns:
        Path to the skills.kdl file.

    Raises:
        QuivError: If no skills.kdl is found.
    """
    current = start.resolve()
    while True:
        candidate = current / "skills.kdl"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    raise QuivError(
        f"No skills.kdl found in {start} or any parent directory. "
        "Run 'quiv init' to create one."
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="quiv",
        description="Manage curated skill collections",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Working directory (default: current directory)",
        metavar="DIR",
    )

    subparsers = parser.add_subparsers(dest="command", title="commands")

    # --- sync command group ---
    sync_parser = subparsers.add_parser("sync", help="Sync skills from upstream")
    sync_sub = sync_parser.add_subparsers(dest="sync_command", title="sync commands")

    # sync fetch
    sync_sub.add_parser("fetch", help="Fetch skills from upstream sources")

    # sync diff
    diff_parser = sync_sub.add_parser("diff", help="Show differences with upstream")
    diff_parser.add_argument(
        "--latest",
        action="store_true",
        help="Compare against latest upstream regardless of pinned SHA",
    )

    # sync update
    update_parser = sync_sub.add_parser(
        "update", help="Update local skills from upstream"
    )
    update_parser.add_argument(
        "skill_name",
        nargs="?",
        default=None,
        help="Specific skill to update (default: all)",
        metavar="SKILL",
    )
    update_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite local changes without warning",
    )

    # --- validate command ---
    validate_parser = subparsers.add_parser(
        "validate", help="Validate skill structure and naming"
    )
    validate_parser.add_argument(
        "skill_name",
        nargs="?",
        default=None,
        help="Specific skill to validate (default: all)",
        metavar="SKILL",
    )

    # --- init command ---
    init_parser = subparsers.add_parser("init", help="Scaffold a new skill")
    init_parser.add_argument(
        "skill_name",
        help="Name for the new skill (kebab-case)",
        metavar="SKILL",
    )
    init_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: skills/<skill-name> under manifest root)",
        metavar="PATH",
    )

    # --- package command ---
    package_parser = subparsers.add_parser(
        "package", help="Package a skill as a zip archive"
    )
    package_parser.add_argument(
        "skill_name",
        help="Skill to package",
        metavar="SKILL",
    )
    package_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for zip file (default: <skill-name>.zip)",
        metavar="PATH",
    )

    return parser


def _resolve_dir(args: argparse.Namespace) -> Path:
    """Resolve the working directory from --dir flag or CWD."""
    if args.dir is not None:
        d = Path(args.dir)
        if not d.is_dir():
            raise QuivError(f"Directory does not exist: {d}")
        return d.resolve()
    return Path.cwd()


def _handle_sync(args: argparse.Namespace, work_dir: Path) -> None:
    """Dispatch sync subcommands."""
    from skill_quiver.manifest import parse_manifest
    from skill_quiver.sync import sync_diff, sync_fetch, sync_update

    if not args.sync_command:
        raise QuivError("No sync subcommand provided. Use: fetch, diff, or update")

    manifest_path = find_manifest(work_dir)
    manifest = parse_manifest(manifest_path)

    match args.sync_command:
        case "fetch":
            sync_fetch(manifest)
        case "diff":
            sync_diff(manifest, latest=args.latest)
        case "update":
            sync_update(
                manifest,
                skill_name=args.skill_name,
                force=args.force,
            )


def _handle_validate(args: argparse.Namespace, work_dir: Path) -> None:
    """Dispatch validate command."""
    from skill_quiver.validate import validate_all

    manifest_path = find_manifest(work_dir)
    root = manifest_path.parent
    results = validate_all(root, skill_name=args.skill_name)

    has_errors = False
    for skill_name, errors in sorted(results.items()):
        if errors:
            has_errors = True
            print(f"{skill_name}:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
        else:
            print(f"{skill_name}: ok")

    if has_errors:
        raise QuivError("Validation failed", exit_code=2)


def _handle_init(args: argparse.Namespace, work_dir: Path) -> None:
    """Dispatch init command."""
    from skill_quiver.init import init_skill

    init_skill(name=args.skill_name, output=args.output, root=work_dir)


def _handle_package(args: argparse.Namespace, work_dir: Path) -> None:
    """Dispatch package command."""
    from skill_quiver.package import package_skill

    manifest_path = find_manifest(work_dir)
    root = manifest_path.parent
    skill_dir = root / "skills" / args.skill_name
    package_skill(skill_dir=skill_dir, output=args.output)


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the quiv CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    try:
        work_dir = _resolve_dir(args)

        match args.command:
            case "sync":
                _handle_sync(args, work_dir)
            case "validate":
                _handle_validate(args, work_dir)
            case "init":
                _handle_init(args, work_dir)
            case "package":
                _handle_package(args, work_dir)

    except QuivError as e:
        print(f"error: {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)
