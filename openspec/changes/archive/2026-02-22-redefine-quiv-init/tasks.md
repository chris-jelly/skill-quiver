## 1. Rewrite init module

- [x] 1.1 Replace `SKILL_MD_TEMPLATE` and `SUBDIRECTORIES` constants with `SKILLS_KDL_TEMPLATE` and `GITIGNORE_ENTRIES` constants
- [x] 1.2 Remove `init_skill()` function and `validate_name` import
- [x] 1.3 Implement `init_repo(target: Path) -> Path` that creates `skills.kdl`, `skills/.gitkeep`, and configures `.gitignore`
- [x] 1.4 Implement `.gitignore` append logic: create if missing, append if exists, skip if quiv entries already present (detect via `# quiv -` marker)
- [x] 1.5 Add "Already initialized (skills.kdl exists)" error when `skills.kdl` is present
- [x] 1.6 Print summary of created files on success

## 2. Update CLI

- [x] 2.1 Remove `skill_name` positional argument and `--output` flag from init subparser
- [x] 2.2 Update init help text from "Scaffold a new skill" to "Initialize a skill-quiver project"
- [x] 2.3 Update `_handle_init` to create `--dir` directory if it doesn't exist, then call `init_repo(target=work_dir)`

## 3. Rewrite tests

- [x] 3.1 Remove all existing `test_init.py` tests for skill scaffolding
- [x] 3.2 Add test: successful repo init creates `skills.kdl`, `skills/`, `skills/.gitkeep`, `.gitignore`
- [x] 3.3 Add test: `skills.kdl` content matches template with commented example
- [x] 3.4 Add test: already-initialized directory raises `InitError` with correct message
- [x] 3.5 Add test: `.gitignore` created when none exists
- [x] 3.6 Add test: `.gitignore` appended when it already exists (preserves existing content)
- [x] 3.7 Add test: `.gitignore` not duplicated when quiv entries already present
- [x] 3.8 Add test: `--dir` with non-existent directory creates it and initializes inside

## 4. Update module docstring

- [x] 4.1 Update `init.py` module docstring from skill scaffolding to repo initialization

## 5. Update README

- [x] 5.1 Update Quick Start to show `quiv init` as first step
- [x] 5.2 Rewrite `quiv init` command docs (remove SKILL arg, describe new behavior)
- [x] 5.3 Update project structure description for init.py
