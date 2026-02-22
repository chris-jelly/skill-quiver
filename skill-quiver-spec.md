# skill-quiver Specification

> Bootstrap spec for the `skill-quiver` project. Drop this into the new repo's
> `openspec/specs/skill-quiver/spec.md` to kick off a change.

## Context

This CLI tool (command: `quiv`) is extracted from the `ai-skills` repository's
`scripts/` directory. It manages **curated skill collections** -- declarative
manifests that pull skills from external git repositories, track provenance,
and prepare them for installation.

Installation to agent directories (opencode, claude-code, cursor, etc.) is
delegated to the `vercel-labs/skills` CLI (`npx skills`), which supports 37+
agents. `quiv` focuses on the **curation layer** that `npx skills` does not
provide: declarative manifests, upstream syncing, diffing, provenance tracking,
validation, and packaging.

### Design Principles

- **CWD-based operation**: `quiv` operates on whatever directory it's run in, like `git`. No hardcoded repo paths.
- **Declarative over imperative**: A `skills.kdl` manifest declares desired state; commands converge toward it.
- **Composable**: Works alongside `npx skills` rather than replacing it. Each tool does what it's good at.
- **Multi-repo aware**: A user may have multiple skill repos (personal, work, team). The CLI should not assume a single global collection.

### Dependencies

- **Runtime**: Python >= 3.12, `kdl-py` (KDL parser)
- **External tool (optional)**: `npx skills` from `vercel-labs/skills` for agent directory installation. `quiv` should document this dependency but not require it at runtime.

### Origin

Extracted from: https://github.com/<owner>/ai-skills/tree/main/scripts/
- `skill_sync.py` (894 lines) -> `quiv sync`
- `validate_skill.py` (114 lines) -> `quiv validate`
- `package_skill.py` (43 lines) -> `quiv package`
- `init_skill.py` (66 lines) -> `quiv init`
- `skill_install.py` (346 lines) -> **dropped** (delegated to `npx skills`)

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
│       ├── sync.py           # fetch, diff, update commands
│       ├── validate.py       # SKILL.md validation
│       ├── package.py        # Zip packaging
│       ├── init.py           # Skill scaffolding
│       └── provenance.py     # .source.kdl read/write
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
- **WHEN** they run `quiv sync fetch`
- **THEN** `quiv` reads `skills.kdl` from the current directory and writes fetched skills to `skills/` in the current directory

#### Scenario: No manifest found
- **GIVEN** the user is in a directory with no `skills.kdl` (and no parent has one)
- **WHEN** they run `quiv sync fetch`
- **THEN** `quiv` exits with an error: "No skills.kdl found in current directory or any parent"

#### Scenario: Explicit path override
- **WHEN** a user runs `quiv --dir /path/to/repo sync fetch`
- **THEN** `quiv` operates on `/path/to/repo` instead of CWD

### Requirement: Manifest format (skills.kdl)

The CLI SHALL define and own the `skills.kdl` format. The format uses KDL syntax and declares external skill sources, with optional install filters.

```kdl
source "<name>" {
    repo "<git-url>"             // Required: git repository URL (GitHub HTTPS, SSH, or any git URL)
    path "<subdir>"              // Optional: subdirectory within repo (default: root)
    ref "<branch|tag|sha>"       // Optional: git ref to pin (default: "main")
    license "<spdx-id>"         // Required: SPDX license identifier
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

### Requirement: Sync fetch downloads skills from declared sources

The `quiv sync fetch` command SHALL download skills from sources declared in `skills.kdl` into the local `skills/` directory. For GitHub repositories, it SHALL use the GitHub API (tarball download). For other git hosts, it SHALL fall back to shallow clone with sparse checkout.

#### Scenario: Fetch from GitHub source
- **GIVEN** a source pointing to a GitHub repo with `ref "main"`
- **WHEN** the user runs `quiv sync fetch`
- **THEN** `quiv` resolves the ref to a SHA, downloads the tarball, extracts declared skills to `skills/`, and writes provenance files

#### Scenario: Fetch skips up-to-date skills
- **GIVEN** a skill already exists locally with a `.source.kdl` matching the upstream SHA
- **WHEN** the user runs `quiv sync fetch`
- **THEN** that skill is skipped with a message "up-to-date"

#### Scenario: Fetch from non-GitHub source
- **GIVEN** a source pointing to a GitLab or self-hosted repo
- **WHEN** the user runs `quiv sync fetch`
- **THEN** `quiv` falls back to `git clone --depth 1 --sparse` to fetch the skills

#### Scenario: Fetch specific source only
- **WHEN** the user runs `quiv sync fetch --source <name>`
- **THEN** only that source is fetched; other sources are left untouched

#### Scenario: GitHub token authentication
- **GIVEN** the `GITHUB_TOKEN` environment variable is set
- **WHEN** `quiv` makes GitHub API requests
- **THEN** it includes the token in the Authorization header

### Requirement: Provenance tracking via .source.kdl

Each fetched skill SHALL contain a `.source.kdl` file recording its origin, pinned SHA, license, and fetch timestamp.

```kdl
source {
    repo "https://github.com/owner/repo"
    path "skills"
    ref "main"
    sha "abc123..."
    license "MIT"
    fetched "2026-02-22T12:00:00Z"
}
```

#### Scenario: Provenance written on fetch
- **WHEN** a skill is fetched from upstream
- **THEN** a `.source.kdl` file is written to the skill directory with repo, path, ref, SHA, license, and UTC timestamp

#### Scenario: Provenance read for skip detection
- **WHEN** `quiv sync fetch` checks if a skill needs updating
- **THEN** it reads the existing `.source.kdl` and compares the SHA against the upstream resolved SHA

### Requirement: Sync diff compares local skills against upstream

The `quiv sync diff` command SHALL compare locally-fetched skills against their upstream versions, showing differences.

#### Scenario: Diff a specific skill
- **WHEN** the user runs `quiv sync diff <skill-name>`
- **THEN** `quiv` fetches the upstream version to a temp directory and runs a recursive diff, excluding `.source.kdl`

#### Scenario: Diff all fetched skills
- **WHEN** the user runs `quiv sync diff` with no skill name
- **THEN** `quiv` diffs all skills that have a `.source.kdl` provenance file

#### Scenario: Diff against latest upstream
- **WHEN** the user runs `quiv sync diff --latest`
- **THEN** `quiv` compares against the upstream default branch HEAD, not the pinned ref

#### Scenario: Local-only skill skipped
- **GIVEN** a skill directory exists without a `.source.kdl` file
- **WHEN** the user runs `quiv sync diff`
- **THEN** that skill is skipped with a message "local-only"

### Requirement: Sync update pulls latest upstream versions

The `quiv sync update` command SHALL update fetched skills to the latest upstream version, with safety checks for local modifications.

#### Scenario: Update detects local modifications
- **GIVEN** a skill has been modified locally (differs from its pinned upstream version)
- **WHEN** the user runs `quiv sync update`
- **THEN** that skill is skipped with a warning showing the diff, suggesting `--force`

#### Scenario: Force update overwrites local changes
- **WHEN** the user runs `quiv sync update --force`
- **THEN** local modifications are overwritten with the upstream version

#### Scenario: Update already at latest
- **GIVEN** a skill's pinned SHA matches the current upstream SHA
- **WHEN** the user runs `quiv sync update`
- **THEN** that skill is reported as "already at latest"

#### Scenario: Update specific skill
- **WHEN** the user runs `quiv sync update --skill <name>`
- **THEN** only that skill is updated

### Requirement: Third-party license tracking

The `quiv sync fetch` command SHALL generate a `THIRD_PARTY_LICENSES` file in the repo root, listing license and attribution information for all external sources.

#### Scenario: Licenses file generated after fetch
- **WHEN** `quiv sync fetch` completes
- **THEN** a `THIRD_PARTY_LICENSES` file is written (or updated) listing each source's repo, license, attribution, and skills

#### Scenario: No external sources
- **GIVEN** `skills.kdl` has no source blocks
- **WHEN** `quiv sync fetch` runs
- **THEN** the `THIRD_PARTY_LICENSES` file is removed if it exists

### Requirement: Validate checks SKILL.md correctness

The `quiv validate` command SHALL validate a skill's SKILL.md file for correct frontmatter structure and naming conventions.

#### Scenario: Valid skill passes
- **GIVEN** a skill directory with a conforming SKILL.md
- **WHEN** the user runs `quiv validate skills/my-skill`
- **THEN** `quiv` prints "Valid" with the skill's name and description

#### Scenario: Missing frontmatter
- **GIVEN** a SKILL.md that does not start with `---` YAML frontmatter
- **WHEN** the user runs `quiv validate`
- **THEN** `quiv` exits with an error about missing frontmatter

#### Scenario: Name/directory mismatch
- **GIVEN** a SKILL.md where the `name` field does not match the directory name
- **WHEN** the user runs `quiv validate`
- **THEN** `quiv` exits with an error identifying the mismatch

#### Scenario: Name format validation
- **WHEN** the `name` field contains uppercase letters, spaces, or consecutive hyphens
- **THEN** `quiv` exits with an error describing the naming rules (lowercase alphanumeric with single hyphen separators, 1-64 chars)

#### Scenario: Validate all skills in directory
- **WHEN** the user runs `quiv validate` with no path argument
- **THEN** `quiv` validates all skill directories under `skills/`

### Requirement: Init scaffolds a new skill directory

The `quiv init` command SHALL create a new skill directory with a template SKILL.md and standard subdirectories.

#### Scenario: Create new skill
- **WHEN** the user runs `quiv init my-new-skill --description "Does something useful"`
- **THEN** `quiv` creates `skills/my-new-skill/` with:
  - `SKILL.md` (template with frontmatter populated)
  - `scripts/` directory
  - `references/` directory
  - `assets/` directory

#### Scenario: Skill already exists
- **GIVEN** `skills/my-skill/` already exists
- **WHEN** the user runs `quiv init my-skill`
- **THEN** `quiv` exits with an error: skill already exists

#### Scenario: Invalid name rejected
- **WHEN** the user runs `quiv init "My Skill!"` 
- **THEN** `quiv` exits with an error about invalid name format

#### Scenario: Custom output path
- **WHEN** the user runs `quiv init my-skill --path ./custom-dir`
- **THEN** the skill is created under `custom-dir/my-skill/` instead of `skills/my-skill/`

### Requirement: Package creates distributable archive

The `quiv package` command SHALL create a zip archive of a skill directory for distribution.

#### Scenario: Package a skill
- **WHEN** the user runs `quiv package skills/my-skill`
- **THEN** `quiv` creates `my-skill-skill.zip` containing all files from the skill directory

#### Scenario: Custom output path
- **WHEN** the user runs `quiv package skills/my-skill -o my-skill.zip`
- **THEN** the archive is written to the specified path

#### Scenario: Missing SKILL.md
- **GIVEN** the target directory does not contain a SKILL.md
- **WHEN** the user runs `quiv package`
- **THEN** `quiv` exits with an error

### Requirement: Installation delegates to npx skills

The CLI SHALL NOT implement agent directory installation directly. Instead, documentation and help text SHALL guide users to use `npx skills` for the installation step.

#### Scenario: Help text mentions npx skills
- **WHEN** the user runs `quiv --help`
- **THEN** the help output includes a note about using `npx skills add ./skills/` for installing to agent directories

#### Scenario: Convenience wrapper (future consideration)
- The CLI MAY in a future version provide a `quiv install` command that shells out to `npx skills add ./skills/ [args]`, but this is NOT required for the initial version.

---

## Non-Requirements (Explicit Exclusions)

- **Agent directory management**: Handled by `npx skills`. No platform registry, no symlink/copy logic.
- **Skill discovery/search**: Handled by `npx skills find` and skills.sh.
- **Multi-repo config file**: Future enhancement. V1 operates on a single directory at a time.
- **PyPI publishing**: The CLI should be installable from git (`pipx install git+...`). PyPI publishing is a separate concern.
- **Interactive prompts**: All commands are non-interactive. No TUI, no selection menus.

---

## CLI Summary

```
quiv sync fetch [--source <name>]         Fetch skills from declared sources
quiv sync diff [<skill>] [--latest]       Compare local vs upstream
quiv sync update [--skill <name>] [--force]  Update to latest upstream

quiv validate [<path>]                    Validate SKILL.md files
quiv init <name> [--description <desc>] [--path <dir>]  Scaffold new skill
quiv package <path> [-o <output>]         Create distributable zip

quiv --dir <path>                         Override working directory
quiv --help                               Show help
quiv --version                            Show version
```
