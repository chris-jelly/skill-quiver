# skill-quiver

CLI tool for managing curated collections of AI agent skills from git repositories.

`quiv` reads a declarative `skills.kdl` manifest, fetches skills from upstream repos,
and tracks provenance. It handles the curation side: assembling skills from disparate
sources into a single repo. Agent-side installation is left to your preferred tool or
workflow.

## Why skill-quiver?

AI agent skills live in git repos scattered across GitHub. Tools like
[`npx skills`](https://github.com/vercel-labs/skills) make it easy to install a
single skill, but they're imperative. There's no way to declare "these are the
skills I want" and reproduce that set on a fresh machine.

`quiv` fills that gap. It's the declarative curation layer:

- **Reproducible**: Your `skills.kdl` manifest captures your entire skill set
  in one file. Commit it alongside the synced `skills/` directory to track how
  your skills change over time.
- **Attribution-preserving**: Skills are other people's work. `quiv` tracks
  where every skill came from (`.source.kdl`) and generates a
  `THIRD_PARTY_LICENSES` file automatically.
- **Composable**: `quiv` handles curation and provenance. Installation to agent
  directories is a separate step, handled by whatever tool or process you prefer
  (e.g., `npx skills`).

Think of it as git submodules done right, scoped specifically to AI skills:
declarative, with subdirectory extraction and provenance tracking built in.

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

3. Sync the skills:

```bash
quiv sync
```

This downloads the declared skills into `./skills/`, writes `.source.kdl` provenance
files, and generates a `THIRD_PARTY_LICENSES` file.

4. Install to your agents using your preferred tool or process. For example,
   with [`npx skills`](https://github.com/vercel-labs/skills):

```bash
npx skills add ./
```

## How it works

```
skills.kdl          quiv sync          skills/              install
(manifest)    --->   (build)    --->   (output)     --->    (your tool)
```

You declare which skills you want from which repos in `skills.kdl`. `quiv sync` makes
`skills/` match that declaration. The `skills/` directory is a build output that `quiv`
owns completely. Commit it to your repo and use whatever tool you like to install
skills to your agents.

## Commands

### `quiv sync`

Resolves all sources in the manifest and makes `skills/` match. Sync is incremental and skips
skills whose provenance SHA already matches upstream. Stale skills are deleted and
re-extracted unconditionally.

Set `GITHUB_TOKEN` in your environment to avoid API rate limits.

```bash
quiv sync
```

### `quiv sync --dry-run`

Shows what would change without downloading or writing files. Resolves upstream SHAs
and compares against local provenance.

```bash
quiv sync --dry-run
# community-skills: a1b2c3d -> f4e5d6a (2 skills)
# bob-toolkit: up to date
```

### `quiv init`

Initializes a new skill-quiver project in the current directory:
- `skills.kdl` with a commented example source block
- `skills/` directory with `.gitkeep`
- `.gitignore` entries for provenance tracking files

```bash
quiv init
```

Use `--dir PATH` to initialize in a different directory (creates it if needed).
Errors if `skills.kdl` already exists.

### Global flags

- `--dir DIR`: operate in a different directory instead of CWD
- `--version`: print version and exit

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

This file is used for skip-if-up-to-date detection on subsequent syncs and for
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
  sync.py           # Sync engine, license tracking
  init.py           # Repository initialization
  provenance.py     # .source.kdl read/write
  errors.py         # Exception hierarchy
```

## License

MIT. See [LICENSE](LICENSE).
