"""Sync engine: fetch, diff, and update skills from upstream sources."""

from __future__ import annotations

import difflib
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

from skill_quiver.errors import SyncError
from skill_quiver.manifest import Manifest, Source
from skill_quiver.provenance import Provenance, read_provenance, write_provenance


def _make_client() -> httpx.Client:
    """Create an httpx client with optional GitHub token auth."""
    headers: dict[str, str] = {
        "Accept": "application/vnd.github.v3+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return httpx.Client(
        headers=headers,
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=True,
    )


def _is_github(source: Source) -> bool:
    """Check if a source is hosted on GitHub."""
    parsed = urlparse(str(source.repo))
    return parsed.hostname in ("github.com", "www.github.com")


def _parse_github_repo(source: Source) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL."""
    parsed = urlparse(str(source.repo))
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        raise SyncError(f"Invalid GitHub repo URL: {source.repo}")
    return parts[0], parts[1].removesuffix(".git")


def resolve_sha(client: httpx.Client, source: Source) -> str:
    """Get the latest commit SHA for a source via GitHub API.

    Args:
        client: httpx client instance.
        source: Source to resolve.

    Returns:
        The commit SHA string.

    Raises:
        SyncError: If the API call fails.
    """
    owner, repo = _parse_github_repo(source)
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{source.ref}"

    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise SyncError(
            f"Failed to resolve SHA for {source.name}: HTTP {e.response.status_code}"
        ) from e
    except httpx.HTTPError as e:
        raise SyncError(f"Failed to resolve SHA for {source.name}: {e}") from e

    data = response.json()
    return data["sha"]


def fetch_github_tarball(
    client: httpx.Client,
    source: Source,
    sha: str,
    dest: Path,
) -> list[Path]:
    """Download and extract a GitHub tarball for specific skills.

    Args:
        client: httpx client instance.
        source: Source definition.
        sha: Commit SHA to fetch.
        dest: Destination directory for extracted skills.

    Returns:
        List of paths to extracted skill directories.

    Raises:
        SyncError: If download or extraction fails.
    """
    owner, repo = _parse_github_repo(source)
    url = f"https://api.github.com/repos/{owner}/{repo}/tarball/{sha}"

    try:
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            with client.stream("GET", url) as response:
                response.raise_for_status()
                for chunk in response.iter_bytes(chunk_size=8192):
                    tmp.write(chunk)
    except httpx.HTTPError as e:
        raise SyncError(f"Failed to download tarball for {source.name}: {e}") from e

    extracted_skills: list[Path] = []
    try:
        with tarfile.open(tmp_path, "r:gz") as tar:
            # Find the top-level directory in the tarball
            members = tar.getmembers()
            if not members:
                raise SyncError(f"Empty tarball for {source.name}")

            top_dir = members[0].name.split("/")[0]
            source_path = source.path.strip("/")

            for skill_name in source.skills:
                # Build the path within the tarball
                if source_path and source_path != ".":
                    skill_prefix = f"{top_dir}/{source_path}/{skill_name}/"
                else:
                    skill_prefix = f"{top_dir}/{skill_name}/"

                # Extract matching members
                skill_dest = dest / skill_name
                skill_dest.mkdir(parents=True, exist_ok=True)

                for member in members:
                    if member.name.startswith(skill_prefix) and not member.isdir():
                        # Calculate relative path within the skill
                        rel_path = member.name[len(skill_prefix) :]
                        if not rel_path:
                            continue

                        out_file = skill_dest / rel_path
                        out_file.parent.mkdir(parents=True, exist_ok=True)

                        extracted = tar.extractfile(member)
                        if extracted is not None:
                            out_file.write_bytes(extracted.read())

                if any(skill_dest.iterdir()):
                    extracted_skills.append(skill_dest)
    except tarfile.TarError as e:
        raise SyncError(f"Failed to extract tarball for {source.name}: {e}") from e
    finally:
        tmp_path.unlink(missing_ok=True)

    return extracted_skills


def fetch_git_sparse(source: Source, dest: Path) -> list[Path]:
    """Fetch skills via git sparse checkout (fallback for non-GitHub hosts).

    Args:
        source: Source definition.
        dest: Destination directory for cloned skills.

    Returns:
        List of paths to extracted skill directories.

    Raises:
        SyncError: If git is unavailable or clone fails.
    """
    # Check git availability
    git_path = shutil.which("git")
    if git_path is None:
        raise SyncError(
            "git is not installed. Required for non-GitHub sources. "
            "Install git or use GitHub-hosted sources."
        )

    source_path = source.path.strip("/")

    # Build sparse checkout paths
    sparse_paths: list[str] = []
    for skill_name in source.skills:
        if source_path and source_path != ".":
            sparse_paths.append(f"{source_path}/{skill_name}")
        else:
            sparse_paths.append(skill_name)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        try:
            # Initialize sparse checkout
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--filter=blob:none",
                    "--sparse",
                    "--branch",
                    source.ref,
                    str(source.repo),
                    str(tmp / "repo"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            repo_dir = tmp / "repo"

            subprocess.run(
                ["git", "sparse-checkout", "set"] + sparse_paths,
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise SyncError(
                f"Git sparse checkout failed for {source.name}: {e.stderr}"
            ) from e

        # Copy skills to destination
        extracted_skills: list[Path] = []
        for skill_name in source.skills:
            if source_path and source_path != ".":
                src_skill = repo_dir / source_path / skill_name
            else:
                src_skill = repo_dir / skill_name

            if src_skill.is_dir():
                skill_dest = dest / skill_name
                if skill_dest.exists():
                    shutil.rmtree(skill_dest)
                shutil.copytree(src_skill, skill_dest)
                extracted_skills.append(skill_dest)

    return extracted_skills


def sync_fetch(manifest: Manifest) -> None:
    """Fetch all skills from manifest sources.

    Args:
        manifest: Parsed manifest with sources.
    """
    skills_dir = manifest.root / "skills"
    skills_dir.mkdir(exist_ok=True)

    with _make_client() as client:
        for source in manifest.sources:
            print(f"Fetching source: {source.name}")

            if _is_github(source):
                # Resolve SHA
                sha = resolve_sha(client, source)

                # Check if up-to-date
                all_up_to_date = True
                for skill_name in source.skills:
                    skill_dir = skills_dir / skill_name
                    prov = read_provenance(skill_dir)
                    if prov is None or prov.sha != sha:
                        all_up_to_date = False
                        break

                if all_up_to_date:
                    print(f"  {source.name}: up to date (SHA {sha[:8]})")
                    continue

                # Fetch tarball
                extracted = fetch_github_tarball(client, source, sha, skills_dir)
            else:
                # Non-GitHub: use git sparse checkout
                sha = source.ref  # Can't easily resolve SHA without GitHub API
                extracted = fetch_git_sparse(source, skills_dir)

            # Write provenance for each extracted skill
            now = datetime.now(timezone.utc)
            for skill_dir in extracted:
                prov = Provenance(
                    repo=str(source.repo),
                    path=source.path,
                    ref=source.ref,
                    sha=sha,
                    license=source.license,
                    fetched=now,
                )
                write_provenance(skill_dir, prov)
                print(f"  Fetched: {skill_dir.name}")

        # Generate license file after all fetches
        generate_license_file(manifest, manifest.root)


def sync_diff(manifest: Manifest, latest: bool = False) -> None:
    """Compare local skills against upstream versions.

    Args:
        manifest: Parsed manifest with sources.
        latest: If True, compare against latest upstream regardless of pinned SHA.
    """
    skills_dir = manifest.root / "skills"
    has_diff = False

    with _make_client() as client:
        for source in manifest.sources:
            if not _is_github(source):
                print(f"  {source.name}: diff not supported for non-GitHub sources")
                continue

            # Get upstream SHA
            upstream_sha = resolve_sha(client, source)

            for skill_name in source.skills:
                skill_dir = skills_dir / skill_name
                prov = read_provenance(skill_dir)

                if prov is None:
                    print(f"  {skill_name}: not yet fetched")
                    has_diff = True
                    continue

                if not latest and prov.sha == upstream_sha:
                    continue

                # Fetch upstream to temp and diff
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp = Path(tmp_dir)
                    fetch_github_tarball(client, source, upstream_sha, tmp)

                    upstream_skill = tmp / skill_name
                    if not upstream_skill.is_dir():
                        print(f"  {skill_name}: not found upstream")
                        continue

                    # Compare files
                    _diff_directories(skill_dir, upstream_skill, skill_name)
                    has_diff = True

    if not has_diff:
        print("All skills are up to date.")


def _diff_directories(local: Path, upstream: Path, skill_name: str) -> None:
    """Print unified diff between two directories."""
    local_files = {
        f.relative_to(local): f
        for f in sorted(local.rglob("*"))
        if f.is_file()
        and not any(p.startswith(".") for p in f.relative_to(local).parts)
    }
    upstream_files = {
        f.relative_to(upstream): f
        for f in sorted(upstream.rglob("*"))
        if f.is_file()
        and not any(p.startswith(".") for p in f.relative_to(upstream).parts)
    }

    all_paths = sorted(set(local_files) | set(upstream_files))

    for rel_path in all_paths:
        local_file = local_files.get(rel_path)
        upstream_file = upstream_files.get(rel_path)

        if local_file and not upstream_file:
            print(f"  {skill_name}/{rel_path}: removed upstream")
        elif not local_file and upstream_file:
            print(f"  {skill_name}/{rel_path}: added upstream")
        elif local_file and upstream_file:
            try:
                local_lines = local_file.read_text(encoding="utf-8").splitlines(
                    keepends=True
                )
                upstream_lines = upstream_file.read_text(encoding="utf-8").splitlines(
                    keepends=True
                )
            except UnicodeDecodeError:
                # Binary file
                if local_file.read_bytes() != upstream_file.read_bytes():
                    print(f"  {skill_name}/{rel_path}: binary files differ")
                continue

            diff = list(
                difflib.unified_diff(
                    local_lines,
                    upstream_lines,
                    fromfile=f"local/{skill_name}/{rel_path}",
                    tofile=f"upstream/{skill_name}/{rel_path}",
                )
            )
            if diff:
                for line in diff:
                    print(line, end="")
                print()


def sync_update(
    manifest: Manifest,
    skill_name: str | None = None,
    force: bool = False,
) -> None:
    """Update local skills from upstream.

    Args:
        manifest: Parsed manifest with sources.
        skill_name: Optional specific skill to update.
        force: If True, overwrite local changes without warning.
    """
    skills_dir = manifest.root / "skills"

    with _make_client() as client:
        for source in manifest.sources:
            # Filter to specific skill if requested
            skills_to_update = source.skills
            if skill_name:
                if skill_name not in source.skills:
                    continue
                skills_to_update = [skill_name]

            if _is_github(source):
                sha = resolve_sha(client, source)
            else:
                sha = source.ref

            for sname in skills_to_update:
                skill_dir = skills_dir / sname
                prov = read_provenance(skill_dir)

                if prov and prov.sha == sha:
                    print(f"  {sname}: already up to date")
                    continue

                # Check for local modifications
                if not force and skill_dir.is_dir() and prov:
                    print(f"  {sname}: has local state, use --force to overwrite")
                    continue

                # Fetch and replace
                print(f"  Updating: {sname}")
                if _is_github(source):
                    if skill_dir.exists():
                        shutil.rmtree(skill_dir)
                    fetch_github_tarball(client, source, sha, skills_dir)
                else:
                    fetch_git_sparse(source, skills_dir)

                # Write provenance
                now = datetime.now(timezone.utc)
                new_prov = Provenance(
                    repo=str(source.repo),
                    path=source.path,
                    ref=source.ref,
                    sha=sha,
                    license=source.license,
                    fetched=now,
                )
                write_provenance(skill_dir, new_prov)
                print(f"  Updated: {sname}")

        # Regenerate license file
        generate_license_file(manifest, manifest.root)


def generate_license_file(manifest: Manifest, root: Path) -> None:
    """Generate THIRD_PARTY_LICENSES file from manifest sources.

    Args:
        manifest: Parsed manifest with sources.
        root: Root directory for the license file.
    """
    license_path = root / "THIRD_PARTY_LICENSES"

    if not manifest.sources:
        # Remove file if no sources
        if license_path.exists():
            license_path.unlink()
        return

    sections: list[str] = []
    for source in sorted(manifest.sources, key=lambda s: s.name):
        section_lines = [
            f"## {source.name}",
            f"URL: {source.repo}",
        ]
        if source.license:
            section_lines.append(f"License: {source.license}")
        else:
            section_lines.append("License: Not specified")
        if source.attribution:
            section_lines.append(f"Attribution: {source.attribution}")
        sections.append("\n".join(section_lines))

    content = "# Third-Party Licenses\n\n" + "\n\n".join(sections) + "\n"

    try:
        license_path.write_text(content, encoding="utf-8")
    except OSError as e:
        raise SyncError(f"Cannot write license file: {e}") from e
