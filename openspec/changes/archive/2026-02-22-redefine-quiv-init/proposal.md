## Why

`quiv init` currently scaffolds a single skill directory (SKILL.md, scripts/, references/, assets/), but users don't author skills with this tool — they curate collections of upstream skills fetched from git repos. The natural meaning of `quiv init` is "set up a new skill-quiver project," not "create a skill template." This mismatch confuses new users and doesn't align with the tool's actual purpose.

## What Changes

- **BREAKING**: Remove the `SKILL` positional argument and `--output` flag from `quiv init`
- **BREAKING**: Remove skill-scaffolding behavior entirely (no more SKILL.md template, scripts/references/assets subdirs)
- `quiv init` now initializes a repository: creates `skills.kdl` (with commented example), `skills/` directory (with `.gitkeep`), and appends quiv-specific entries to `.gitignore`
- Error if `skills.kdl` already exists ("Already initialized")
- Support `--dir` flag to initialize in a different directory (creating it if needed)

## Capabilities

### New Capabilities

- `repo-init`: Initializing a skill-quiver project directory with manifest, skills directory, and gitignore configuration

### Modified Capabilities

- `skill-init`: The entire skill-scaffolding capability is being removed and replaced by repo initialization. The `init` command no longer creates individual skill directories.

## Impact

- `src/skill_quiver/init.py` — rewrite `init_skill()` to `init_repo()` with new behavior
- `src/skill_quiver/cli.py` — update init subparser (remove `skill_name` arg, remove `--output`, update handler)
- `tests/test_init.py` — rewrite all 6 tests for new repo-initialization behavior
- CLI interface is a breaking change for any scripts or docs referencing `quiv init <name>`
