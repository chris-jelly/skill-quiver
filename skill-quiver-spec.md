# skill-quiver Specification

> Bootstrap spec for the `skill-quiver` project.

## Context

This CLI tool (command: `quiv`) manages **curated skill collections** -- declarative
manifests that pull skills from external git repositories, track provenance,
and prepare them for installation.

Installation to agent directories (opencode, claude-code, cursor, etc.) is
delegated to the `vercel-labs/skills` CLI (`npx skills`), which supports 37+
agents. `quiv` focuses on the **curation layer** that `npx skills` does not
provide: declarative manifests, upstream syncing, and provenance tracking.

### Design Principles

- **CWD-based operation**: `quiv` operates on whatever directory it's run in, like `git`. No hardcoded repo paths.
- **Declarative over imperative**: A `skills.kdl` manifest declares desired state; `quiv sync` converges toward it.
- **Build output**: `skills/` is owned by `quiv` -- it is derived from the manifest and overwritten on each sync.
- **Composable**: Works alongside `npx skills` rather than replacing it. Each tool does what it's good at.
- **Multi-repo aware**: A user may have multiple skill repos (personal, work, team). The CLI should not assume a single global collection.

### Dependencies

- **Runtime**: Python >= 3.13, `kdl-py` (KDL parser)
- **External tool (optional)**: `npx skills` from `vercel-labs/skills` for agent directory installation. `quiv` should document this dependency but not require it at runtime.

---

## Requirements

### Requirement: Project structure follows standard Python CLI packaging

The project SHALL be structured as an installable Python package with a CLI entry point.

```
skill-quiver/
├── pyproject.toml            # Package metadata, [project.scripts] entry point
├── src/
│   └── skill_quiver/
│       ├── __init__.py
│       ├── cli.py            # Argument parsing and command dispatch
│       ├── manifest.py       # skills.kdl parsing and validation
│       ├── sync.py           # Sync engine, license tracking
│       ├── init.py           # Repository initialization
│       ├── provenance.py     # .source.kdl read/write
│       └── errors.py         # Exception hierarchy
├── tests/
├── README.md
└── LICENSE
```

#### Scenario: CLI is installable via pipx
- **GIVEN** the project is published or available as a git repo
- **WHEN** a user runs `pipx install skill-quiver` or `pipx install git+https://github.com/<owner>/skill-quiver.git`
- **THEN** the `quiv` command is available on their PATH

#### Scenario: Entry point invokes CLI
- **WHEN** a user runs `quiv --help`
- **THEN** they see a help message listing all available subcommands

### Requirement: CWD-based operation with manifest discovery

All commands SHALL operate relative to the current working directory. The CLI SHALL locate `skills.kdl` by searching the current directory (and optionally parent directories, like git does).

#### Scenario: Manifest found in current directory
- **GIVEN** the user is in a directory containing `skills.kdl`
- **WHEN** they run `quiv sync`
- **THEN** `quiv` reads `skills.kdl` from the current directory and writes fetched skills to `skills/` in the current directory

#### Scenario: No manifest found
- **GIVEN** the user is in a directory with no `skills.kdl` (and no parent has one)
- **WHEN** they run `quiv sync`
- **THEN** `quiv` exits with an error: "No skills.kdl found in current directory or any parent"

#### Scenario: Explicit path override
- **WHEN** a user runs `quiv --dir /path/to/repo sync`
- **THEN** `quiv` operates on `/path/to/repo` instead of CWD

### Requirement: Manifest format (skills.kdl)

The CLI SHALL define and own the `skills.kdl` format. The format uses KDL syntax and declares external skill sources.

```kdl
source "<name>" {
    repo "<git-url>"             // Required: git repository URL (GitHub HTTPS, SSH, or any git URL)
    path "<subdir>"              // Optional: subdirectory within repo (default: root)
    ref "<branch|tag|sha>"       // Optional: git ref to pin (default: "main")
    license "<spdx-id>"         // Optional: SPDX license identifier
    attribution "<text>"         // Optional: attribution text
    skill "<skill-name>"         // Required: at least one; repeatable
}
```

#### Scenario: Valid manifest parses successfully
- **GIVEN** a `skills.kdl` with one or more valid `source` blocks
- **WHEN** `quiv` parses the manifest
- **THEN** it returns structured source data with all fields populated (defaults applied for optional fields)

#### Scenario: Missing required field
- **GIVEN** a `skills.kdl` where a source block is missing `repo`
- **WHEN** `quiv` parses the manifest
- **THEN** it exits with an error identifying the source name and the missing field

#### Scenario: Source with no skills
- **GIVEN** a `skills.kdl` where a source block has no `skill` entries
- **WHEN** `quiv` parses the manifest
- **THEN** it exits with an error: source must declare at least one skill

### Requirement: Sync resolves manifest and makes skills/ match it

The `quiv sync` command SHALL resolve all sources in the manifest and make `skills/` match. For GitHub repositories, it SHALL use the GitHub API (tarball download). For other git hosts, it SHALL fall back to shallow clone with sparse checkout. Stale skills are deleted and re-extracted unconditionally.

#### Scenario: Sync from GitHub source
- **GIVEN** a source pointing to a GitHub repo with `ref "main"`
- **WHEN** the user runs `quiv sync`
- **THEN** `quiv` resolves the ref to a SHA, downloads the tarball, extracts declared skills to `skills/`, and writes provenance files

#### Scenario: Sync skips up-to-date skills
- **GIVEN** a skill already exists locally with a `.source.kdl` matching the upstream SHA
- **WHEN** the user runs `quiv sync`
- **THEN** that skill is skipped with a message "up to date"

#### Scenario: Sync from non-GitHub source
- **GIVEN** a source pointing to a GitLab or self-hosted repo
- **WHEN** the user runs `quiv sync`
- **THEN** `quiv` falls back to `git clone --depth 1 --sparse` to fetch the skills

#### Scenario: Stale skills overwritten unconditionally
- **GIVEN** a skill has been modified locally and its provenance SHA differs from upstream
- **WHEN** the user runs `quiv sync`
- **THEN** the local skill directory is deleted and re-extracted from upstream without warning

#### Scenario: GitHub token authentication
- **GIVEN** the `GITHUB_TOKEN` environment variable is set
- **WHEN** `quiv` makes GitHub API requests
- **THEN** it includes the token in the Authorization header

### Requirement: Sync supports dry-run mode

The `quiv sync --dry-run` flag SHALL resolve upstream SHAs and report what would change without downloading tarballs or writing files.

#### Scenario: Dry-run reports pending changes
- **WHEN** the user runs `quiv sync --dry-run` and some sources have upstream changes
- **THEN** `quiv` reports which sources would be updated with old and new SHAs

#### Scenario: Dry-run does not write files
- **WHEN** the user runs `quiv sync --dry-run`
- **THEN** no files in `skills/` are created, modified, or deleted

### Requirement: Provenance tracking via .source.kdl

Each fetched skill SHALL contain a `.source.kdl` file recording its origin, pinned SHA, license, and fetch timestamp.

```kdl
source repo="https://github.com/owner/repo" path="skills" ref="main" sha="abc123..." fetched="2026-02-22T12:00:00Z"
```

#### Scenario: Provenance written on sync
- **WHEN** a skill is synced from upstream
- **THEN** a `.source.kdl` file is written to the skill directory with repo, path, ref, SHA, license, and UTC timestamp

#### Scenario: Provenance read for skip detection
- **WHEN** `quiv sync` checks if a skill needs updating
- **THEN** it reads the existing `.source.kdl` and compares the SHA against the upstream resolved SHA

### Requirement: Third-party license tracking

The `quiv sync` command SHALL generate a `THIRD_PARTY_LICENSES` file in the repo root, listing license and attribution information for all external sources.

#### Scenario: Licenses file generated after sync
- **WHEN** `quiv sync` completes
- **THEN** a `THIRD_PARTY_LICENSES` file is written (or updated) listing each source's repo, license, and attribution

#### Scenario: No external sources
- **GIVEN** `skills.kdl` has no source blocks
- **WHEN** `quiv sync` runs
- **THEN** the `THIRD_PARTY_LICENSES` file is removed if it exists

### Requirement: Init scaffolds a new project

The `quiv init` command SHALL initialize a new skill-quiver project in the current directory.

#### Scenario: Create new project
- **WHEN** the user runs `quiv init`
- **THEN** `quiv` creates `skills.kdl`, `skills/` with `.gitkeep`, and `.gitignore` entries

#### Scenario: Already initialized
- **GIVEN** `skills.kdl` already exists in the directory
- **WHEN** the user runs `quiv init`
- **THEN** `quiv` exits with an error

#### Scenario: Custom directory
- **WHEN** the user runs `quiv init --dir /path/to/dir`
- **THEN** the project is initialized in the specified directory (created if needed)

### Requirement: Installation delegates to npx skills

The CLI SHALL NOT implement agent directory installation directly. Instead, documentation and help text SHALL guide users to use `npx skills` for the installation step.

#### Scenario: Help text mentions npx skills
- **WHEN** the user runs `quiv --help`
- **THEN** the help output includes a note about using `npx skills add ./` for installing to agent directories

---

## Non-Requirements (Explicit Exclusions)

- **Agent directory management**: Handled by `npx skills`. No platform registry, no symlink/copy logic.
- **Skill discovery/search**: Handled by `npx skills find` and skills.sh.
- **Skill validation**: Handled by upstream repos and `npx skills` at install time.
- **Skill packaging**: The git repo is the distribution format.
- **Multi-repo config file**: Future enhancement. V1 operates on a single directory at a time.
- **PyPI publishing**: The CLI should be installable from git (`pipx install git+...`). PyPI publishing is a separate concern.
- **Interactive prompts**: All commands are non-interactive. No TUI, no selection menus.

---

## CLI Summary

```
quiv sync [--dry-run]                     Resolve manifest and sync skills
quiv init                                 Initialize a skill-quiver project

quiv --dir <path>                         Override working directory
quiv --help                               Show help
quiv --version                            Show version
```
