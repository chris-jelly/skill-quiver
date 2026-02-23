"""Sync engine: resolve manifest and make skills/ match it."""

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


def sync(manifest: Manifest, dry_run: bool = False) -> None:
    """Resolve manifest and make skills/ match it.

    For each source in the manifest, resolves the upstream SHA, compares
    with local provenance, and re-extracts any stale skills. Treats
    skills/ as a build output — stale skills are deleted and replaced
    unconditionally.

    Args:
        manifest: Parsed manifest with sources.
        dry_run: If True, report what would change without writing files.
    """
    skills_dir = manifest.root / "skills"

    if not dry_run:
        skills_dir.mkdir(exist_ok=True)

    with _make_client() as client:
        for source in manifest.sources:
            if _is_github(source):
                sha = resolve_sha(client, source)
            else:
                sha = source.ref

            # Check which skills are stale
            stale_skills: list[str] = []
            for skill_name in source.skills:
                skill_dir = skills_dir / skill_name
                prov = read_provenance(skill_dir)
                if prov is None or prov.sha != sha:
                    stale_skills.append(skill_name)

            if not stale_skills:
                print(f"{source.name}: up to date")
                continue

            if dry_run:
                # Report what would change
                local_sha = "none"
                for skill_name in stale_skills:
                    prov = read_provenance(skills_dir / skill_name)
                    if prov is not None:
                        local_sha = prov.sha[:8]
                        break
                print(
                    f"{source.name}: {local_sha} -> {sha[:8]} "
                    f"({len(stale_skills)} skills)"
                )
                continue

            # Delete stale skill directories before fetching
            for skill_name in stale_skills:
                skill_dir = skills_dir / skill_name
                if skill_dir.exists():
                    shutil.rmtree(skill_dir)

            # Fetch
            print(f"Syncing {source.name}...")
            if _is_github(source):
                extracted = fetch_github_tarball(client, source, sha, skills_dir)
            else:
                extracted = fetch_git_sparse(source, skills_dir)

            # Write provenance
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
                print(f"  {skill_dir.name}")

    if not dry_run:
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
        section_lines.append("Skills:")
        for skill_name in sorted(source.skills):
            section_lines.append(f"  - {skill_name}")
        sections.append("\n".join(section_lines))

    content = "# Third-Party Licenses\n\n" + "\n\n".join(sections) + "\n"

    try:
        license_path.write_text(content, encoding="utf-8")
    except OSError as e:
        raise SyncError(f"Cannot write license file: {e}") from e
