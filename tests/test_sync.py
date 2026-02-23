"""Tests for the sync engine."""

from __future__ import annotations

import io
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from skill_quiver.errors import SyncError
from skill_quiver.manifest import Manifest, Source
from skill_quiver.provenance import Provenance, write_provenance
from skill_quiver.sync import (
    _is_github,
    _make_client,
    _parse_github_repo,
    generate_license_file,
    resolve_sha,
    sync_fetch,
)


def _make_source(**kwargs: object) -> Source:
    """Helper to create a Source with defaults."""
    defaults = {
        "name": "test-source",
        "repo": "https://github.com/example/repo",
        "path": "skills",
        "ref": "main",
        "skills": ["my-skill"],
    }
    defaults.update(kwargs)
    return Source.model_validate(defaults)


def _make_tarball(files: dict[str, str], top_dir: str = "example-repo-abc123") -> bytes:
    """Create a tarball in-memory with the given files."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path, content in files.items():
            full_path = f"{top_dir}/{path}"
            info = tarfile.TarInfo(name=full_path)
            data = content.encode("utf-8")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    buf.seek(0)
    return buf.read()


class TestIsGithub:
    def test_github_url(self) -> None:
        source = _make_source(repo="https://github.com/example/repo")
        assert _is_github(source) is True

    def test_non_github_url(self) -> None:
        source = _make_source(repo="https://gitlab.com/example/repo")
        assert _is_github(source) is False


class TestParseGithubRepo:
    def test_standard_url(self) -> None:
        source = _make_source(repo="https://github.com/owner/repo")
        owner, repo = _parse_github_repo(source)
        assert owner == "owner"
        assert repo == "repo"

    def test_url_with_git_suffix(self) -> None:
        source = _make_source(repo="https://github.com/owner/repo.git")
        owner, repo = _parse_github_repo(source)
        assert owner == "owner"
        assert repo == "repo"


class TestResolveSha:
    @respx.mock
    def test_resolve_sha_success(self) -> None:
        source = _make_source()
        sha = "abc123def456789"

        respx.get("https://api.github.com/repos/example/repo/commits/main").mock(
            return_value=httpx.Response(200, json={"sha": sha})
        )

        with _make_client() as client:
            result = resolve_sha(client, source)
        assert result == sha

    @respx.mock
    def test_resolve_sha_not_found(self) -> None:
        source = _make_source()

        respx.get("https://api.github.com/repos/example/repo/commits/main").mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )

        with _make_client() as client:
            with pytest.raises(SyncError, match="HTTP 404"):
                resolve_sha(client, source)


class TestSyncFetch:
    @respx.mock
    def test_fetch_happy_path(self, tmp_path: Path) -> None:
        source = _make_source(path="skills")
        manifest = Manifest(sources=[source], root=tmp_path)
        sha = "abc123"

        # Mock resolve SHA
        respx.get("https://api.github.com/repos/example/repo/commits/main").mock(
            return_value=httpx.Response(200, json={"sha": sha})
        )

        # Mock tarball download
        tarball = _make_tarball(
            {
                "skills/my-skill/SKILL.md": "---\nname: my-skill\n---\n# Content",
            }
        )
        respx.get(f"https://api.github.com/repos/example/repo/tarball/{sha}").mock(
            return_value=httpx.Response(200, content=tarball)
        )

        sync_fetch(manifest)

        skill_dir = tmp_path / "skills" / "my-skill"
        assert skill_dir.is_dir()
        assert (skill_dir / "SKILL.md").is_file()
        assert (skill_dir / ".source.kdl").is_file()

    @respx.mock
    def test_skip_if_up_to_date(self, tmp_path: Path) -> None:
        source = _make_source(path="skills")
        manifest = Manifest(sources=[source], root=tmp_path)
        sha = "abc123"

        # Pre-create skill with matching provenance
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        prov = Provenance(
            repo="https://github.com/example/repo/",
            path="skills",
            ref="main",
            sha=sha,
            fetched=datetime.now(timezone.utc),
        )
        write_provenance(skill_dir, prov)

        # Mock resolve SHA
        respx.get("https://api.github.com/repos/example/repo/commits/main").mock(
            return_value=httpx.Response(200, json={"sha": sha})
        )

        # Tarball should NOT be requested
        sync_fetch(manifest)

        # Verify no tarball request was made
        assert len(respx.calls) == 1  # Only the SHA resolve call

    @respx.mock
    def test_github_auth_header(self) -> None:
        """Test that GITHUB_TOKEN is included in requests."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
            client = _make_client()
            assert "Bearer test-token" in client.headers.get("authorization", "")
            client.close()


class TestGenerateLicenseFile:
    def test_generation(self, tmp_path: Path) -> None:
        sources = [
            _make_source(name="beta-source", license="MIT"),
            _make_source(name="alpha-source", license="Apache-2.0"),
        ]
        manifest = Manifest(sources=sources, root=tmp_path)

        generate_license_file(manifest, tmp_path)

        license_path = tmp_path / "THIRD_PARTY_LICENSES"
        assert license_path.is_file()
        content = license_path.read_text(encoding="utf-8")
        assert "alpha-source" in content
        assert "beta-source" in content
        # Alphabetical ordering
        assert content.index("alpha-source") < content.index("beta-source")

    def test_missing_license(self, tmp_path: Path) -> None:
        sources = [_make_source(name="no-license", license=None)]
        manifest = Manifest(sources=sources, root=tmp_path)

        generate_license_file(manifest, tmp_path)

        content = (tmp_path / "THIRD_PARTY_LICENSES").read_text(encoding="utf-8")
        assert "Not specified" in content

    def test_empty_manifest_removes_file(self, tmp_path: Path) -> None:
        # Pre-create license file
        license_path = tmp_path / "THIRD_PARTY_LICENSES"
        license_path.write_text("old content", encoding="utf-8")

        manifest = Manifest(sources=[], root=tmp_path)
        generate_license_file(manifest, tmp_path)

        assert not license_path.exists()

    def test_alphabetical_ordering(self, tmp_path: Path) -> None:
        sources = [
            _make_source(name="zeta-src", license="MIT"),
            _make_source(name="alpha-src", license="BSD"),
            _make_source(name="mid-src", license="ISC"),
        ]
        manifest = Manifest(sources=sources, root=tmp_path)

        generate_license_file(manifest, tmp_path)

        content = (tmp_path / "THIRD_PARTY_LICENSES").read_text(encoding="utf-8")
        positions = [
            content.index(s.name) for s in sorted(sources, key=lambda s: s.name)
        ]
        assert positions == sorted(positions)
