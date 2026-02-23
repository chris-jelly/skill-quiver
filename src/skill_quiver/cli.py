"""CLI entry point and argument parsing for quiv."""

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

    # --- sync command ---
    sync_parser = subparsers.add_parser(
        "sync", help="Resolve manifest and sync skills from upstream"
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files",
    )

    # --- init command ---
    subparsers.add_parser("init", help="Initialize a skill-quiver project")

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
    """Dispatch sync command."""
    from skill_quiver.manifest import parse_manifest
    from skill_quiver.sync import sync

    manifest_path = find_manifest(work_dir)
    manifest = parse_manifest(manifest_path)
    sync(manifest, dry_run=args.dry_run)


def _handle_init(args: argparse.Namespace, work_dir: Path) -> None:
    """Dispatch init command."""
    from skill_quiver.init import init_repo

    # Create --dir directory if it doesn't exist (init-only behavior)
    if args.dir is not None and not Path(args.dir).is_dir():
        Path(args.dir).mkdir(parents=True, exist_ok=True)
        work_dir = Path(args.dir).resolve()

    init_repo(target=work_dir)


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
            case "init":
                _handle_init(args, work_dir)

    except QuivError as e:
        print(f"error: {e.message}", file=sys.stderr)
        sys.exit(e.exit_code)
