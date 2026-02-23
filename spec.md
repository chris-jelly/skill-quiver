# Redefine `quiv init` as repo initialization

## Problem

`quiv init` currently scaffolds a single skill directory (creates `SKILL.md`, `scripts/`, `references/`, `assets/`). This doesn't match what the tool actually does. `quiv` manages a *collection* of skills fetched from upstream git repos -- users aren't authoring individual skills here, they're curating which upstream skills to track.

The natural meaning of `quiv init` is "set up a new skill-quiver project" -- create the manifest and directory structure needed to start managing a collection.

## Current behavior

```bash
quiv init my-skill
# Creates skills/my-skill/SKILL.md, scripts/, references/, assets/
```

## Proposed behavior

```bash
quiv init
# Creates skills.kdl, skills/, .gitignore in the current directory
```

### What `quiv init` should do

1. Check that `skills.kdl` doesn't already exist in the target directory (error if it does)
2. Create `skills.kdl` with a commented example source block
3. Create `skills/` directory with a `.gitkeep`
4. Create or append to `.gitignore` with quiv-specific entries (`.source.kdl` files, etc.)
5. Print what was created

### Template `skills.kdl`

```kdl
// Add sources to fetch skills from.
// Example:
//
// source {
//     name "community-skills"
//     repo "https://github.com/org/ai-skills"
//     path "skills"
//     ref "main"
//     license "MIT"
//     skill "code-reviewer"
//     skill "readme-writer"
// }
```

### `.gitignore` entries

```
# quiv - provenance tracking files are machine-generated
skills/**/.source.kdl
```

### CLI changes

- Remove the required `<skill-name>` positional argument
- Remove the `--output` flag
- `quiv init` takes no arguments (operates on CWD or `--dir`)

### Error cases

- `skills.kdl` already exists: error with message "Already initialized (skills.kdl exists)"
- Target directory doesn't exist: create it (when using `--dir`)

## Affected files

- `src/skill_quiver/init.py` -- rewrite `init_skill()` -> `init_repo()`
- `src/skill_quiver/cli.py` -- update init parser and handler (remove skill_name arg, remove --output)
- `tests/test_init.py` -- rewrite tests for new behavior
- `README.md` -- update init section

## What to remove

The old skill-scaffolding behavior (template SKILL.md, scripts/references/assets subdirs) should be removed entirely. Users don't author skills with this tool -- they fetch them from upstream.
