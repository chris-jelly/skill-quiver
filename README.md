# skill-quiver

CLI tool for managing curated collections of AI agent skills from git repositories.

`quiv` reads a declarative `skills.kdl` manifest, fetches skills from upstream repos,
tracks provenance, validates structure, and packages skills for distribution.
It handles the curation side -- fetching and organizing skills.
Agent-side installation is delegated to `npx skills`.

## Installation

Requires Python >= 3.13.

```bash
uv tool install skill-quiver
```

Or for development:

```bash
git clone https://github.com/your-org/skill-quiver.git
cd skill-quiver
uv venv && uv pip install -e .
```

## Quick start

1. Initialize a skill-quiver project:

```bash
quiv init
```

This creates `skills.kdl`, `skills/`, and configures `.gitignore`.

2. Edit `skills.kdl` to add your sources:

```kdl
source {
    name "community-skills"
    repo "https://github.com/org/ai-skills"
    path "skills"
    ref "main"
    license "MIT"
    skill "code-reviewer"
    skill "readme-writer"
}
```

3. Fetch the skills:

```bash
quiv sync fetch
```

This downloads the declared skills into `./skills/`, writes `.source.kdl` provenance
files, and generates a `THIRD_PARTY_LICENSES` file.

4. Validate your skills:

```bash
quiv validate
```

## Commands

### `quiv sync fetch`

Downloads skills from all sources in the manifest. Skips sources already at the
latest SHA. Uses the GitHub API tarball endpoint for GitHub repos, falls back to
`git sparse-checkout` for other hosts.

Set `GITHUB_TOKEN` in your environment to avoid API rate limits.

### `quiv sync diff [--latest]`

Compares local skills against upstream. Shows added, removed, and changed files
as unified diffs. Pass `--latest` to compare against the latest upstream commit
regardless of the pinned SHA.

### `quiv sync update [SKILL] [--force]`

Updates local skills to match upstream. Detects local modifications and warns
before overwriting. Use `--force` to skip the check. Pass a skill name to update
a single skill.

### `quiv validate [SKILL]`

Checks skill directories for valid structure:
- SKILL.md exists with valid YAML frontmatter (`name`, `description`)
- Directory name matches the frontmatter `name` field
- Names follow kebab-case format (lowercase alphanumeric, single hyphens, 1-64 chars)

Pass a skill name to validate a single skill, or omit to validate all.

### `quiv init`

Initializes a new skill-quiver project in the current directory:
- `skills.kdl` with a commented example source block
- `skills/` directory with `.gitkeep`
- `.gitignore` entries for provenance tracking files

```bash
quiv init
# Creates skills.kdl, skills/, .gitignore
```

Use `--dir PATH` to initialize in a different directory (creates it if needed).
Errors if `skills.kdl` already exists.

### `quiv package <SKILL>`

Creates a zip archive of a skill directory. Validates the skill first, excludes
hidden files (`.` prefix), and reports file count and archive size.

```bash
quiv package my-skill
# Creates my-skill.zip in the current directory
```

Use `--output PATH` to write the archive elsewhere.

### Global flags

- `--dir DIR` -- operate in a different directory instead of CWD
- `--version` -- print version and exit

## Manifest format

The manifest file `skills.kdl` uses [KDL](https://kdl.dev) syntax. Each `source`
block declares a git repository and the skills to fetch from it.

```kdl
source {
    name "my-source"          // required, kebab-case identifier
    repo "https://github.com/org/repo"  // required, git repo URL
    path "skills"             // optional, subdirectory in repo (default: ".")
    ref "main"                // optional, git ref to pin to (default: "main")
    license "MIT"             // optional, license identifier
    attribution "Org Name"    // optional, attribution text
    skill "skill-one"         // at least one required
    skill "skill-two"
}
```

Multiple `source` blocks are supported for pulling skills from different repositories.

## Provenance

Each fetched skill gets a `.source.kdl` file tracking its origin:

```kdl
source repo="https://github.com/org/repo" path="skills" ref="main" sha="abc123..." fetched="2025-01-15T12:00:00+00:00"
```

This file is used for skip-if-up-to-date detection on subsequent fetches and for
auditing where a skill came from.

## Development

```bash
uv venv
uv pip install -e .
uv pip install pytest respx ruff
```

Run tests:

```bash
pytest
```

Lint and format:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Project structure

```
src/skill_quiver/
  __init__.py       # Version
  cli.py            # argparse setup, command dispatch
  manifest.py       # skills.kdl parsing, Pydantic models
  sync.py           # Fetch, diff, update, license tracking
  validate.py       # SKILL.md and name validation
  init.py           # Repository initialization
  package.py        # Zip packaging
  provenance.py     # .source.kdl read/write
  errors.py         # Exception hierarchy
```

## License

MIT -- see [LICENSE](LICENSE).
