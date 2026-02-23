## Why

The `ai-skills` repository contains several Python scripts (~1,400 lines total) for managing curated skill collections -- fetching skills from git repos, validating them, tracking provenance, and packaging them for distribution. These scripts are tightly coupled to a single repo and lack a proper CLI interface, making them unusable outside that context. Extracting them into a standalone CLI tool (`quiv`) enables any user to manage their own skill collections with a declarative manifest, proper provenance tracking, and composable tooling alongside `npx skills` for agent installation.

## What Changes

- **New Python CLI package**: `skill-quiver` with `quiv` entry point, installable via `pipx`
- **New manifest format**: `skills.kdl` declarative file defining external skill sources, parsed with `kdl-py`
- **New sync engine**: `quiv sync fetch|diff|update` commands for downloading, comparing, and updating skills from upstream git repositories (GitHub API tarball + git sparse checkout fallback)
- **New provenance system**: `.source.kdl` files tracking origin, pinned SHA, license, and fetch timestamp for each skill
- **New validation command**: `quiv validate` checks SKILL.md frontmatter structure and naming conventions
- **New init command**: `quiv init` scaffolds skill directories with templates
- **New package command**: `quiv package` creates distributable zip archives
- **New license tracking**: Auto-generated `THIRD_PARTY_LICENSES` file from manifest sources
- **CWD-based operation**: All commands operate relative to the working directory with optional `--dir` override
- **Installation delegation**: Agent directory installation is explicitly NOT implemented; users are directed to `npx skills`

## Capabilities

### New Capabilities

- `cli-framework`: Python package structure, entry point (`quiv`), argument parsing, command dispatch, `--dir` override, `--help`, `--version`, and CWD-based manifest discovery
- `manifest-parsing`: `skills.kdl` format definition, KDL parsing with `kdl-py`, validation of required/optional fields, structured source data extraction
- `sync-engine`: `quiv sync fetch` (GitHub API tarball + git sparse checkout fallback, skip-if-up-to-date, source filtering, auth), `quiv sync diff` (local vs upstream comparison, `--latest` mode), `quiv sync update` (local modification detection, `--force`, per-skill targeting)
- `provenance-tracking`: `.source.kdl` file format, write-on-fetch, read-for-skip-detection, SHA comparison against upstream
- `skill-validation`: SKILL.md frontmatter validation, name format rules (lowercase alphanumeric, single hyphens, 1-64 chars), name/directory mismatch detection, batch validation
- `skill-init`: Directory scaffolding with template SKILL.md, standard subdirectories (`scripts/`, `references/`, `assets/`), name validation, custom output path
- `skill-packaging`: Zip archive creation from skill directories, custom output path, SKILL.md existence check
- `license-tracking`: `THIRD_PARTY_LICENSES` file generation/update after fetch, per-source license and attribution aggregation, cleanup when no sources exist

### Modified Capabilities

(none -- this is a greenfield project with no existing specs)

## Impact

- **New repository structure**: `src/skill_quiver/` package with 7 modules (`cli.py`, `manifest.py`, `sync.py`, `validate.py`, `package.py`, `init.py`, `provenance.py`), `pyproject.toml`, tests
- **Dependencies**: Python >= 3.13, `kdl-py` (KDL parsing), `pydantic` (data modeling/validation), `httpx` (HTTP client)
- **External integration**: Relies on GitHub API for tarball downloads (optional `GITHUB_TOKEN` auth), falls back to `git` CLI for non-GitHub hosts
- **User workflow**: Users create a `skills.kdl` manifest, run `quiv sync fetch` to pull skills, then use `npx skills add ./skills/` separately for agent installation
