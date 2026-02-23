## Context

`quiv init` currently calls `init_skill()` which scaffolds a single skill directory with SKILL.md and subdirectories. The CLI requires a positional `SKILL` argument and accepts `--output`. This behavior doesn't match the tool's purpose — `quiv` manages collections of upstream skills, not skill authoring.

The `init.py` module is self-contained (no external dependencies beyond `validate_name`), and the CLI handler is a thin wrapper. The change is localized to 3 files: `init.py`, `cli.py`, and `test_init.py`.

## Goals / Non-Goals

**Goals:**
- Replace skill scaffolding with repo initialization (create `skills.kdl`, `skills/`, `.gitignore` entries)
- Simplify the `init` CLI to take no arguments (operates on CWD or `--dir`)
- Provide a clear "already initialized" error when `skills.kdl` exists
- Handle `.gitignore` gracefully — append if it exists, create if it doesn't, skip if entries already present

**Non-Goals:**
- Interactive prompts or wizards during init
- Creating a sample source or fetching skills as part of init
- Supporting `--force` to overwrite an existing `skills.kdl`
- Modifying `_resolve_dir` behavior — the existing `--dir` flag works as-is

## Decisions

### 1. Replace `init_skill()` with `init_repo()` entirely

**Decision**: Remove `init_skill` and all skill-scaffolding code. Replace with a single `init_repo(target: Path) -> Path` function.

**Rationale**: The old behavior is completely superseded. Keeping both would be confusing since the tool doesn't support skill authoring. A clean replacement is simpler than deprecation given this is a pre-1.0 tool.

**Alternatives considered**:
- *Deprecate `init_skill` and add `init_repo` alongside it*: Unnecessary complexity for a pre-1.0 tool with no known external consumers of the Python API.

### 2. Append to `.gitignore` rather than overwrite

**Decision**: If `.gitignore` exists, read it and append quiv entries only if they're not already present. If it doesn't exist, create it with just the quiv entries.

**Rationale**: Users may have existing `.gitignore` files. Overwriting would destroy their configuration. Appending is the standard pattern (used by `git init`, `cargo init`, etc.).

**Alternatives considered**:
- *Overwrite .gitignore*: Destructive, unacceptable.
- *Never touch .gitignore, just tell user what to add*: Extra manual step that most users will forget.

### 3. `--dir` creates the target directory if it doesn't exist

**Decision**: Modify `_resolve_dir` to create the directory when used with `init` (currently it errors if the directory doesn't exist).

**Rationale**: `quiv init --dir new-project` is a natural workflow for starting a new project. Requiring `mkdir` first is unnecessary friction. Other init commands (`git init`, `npm init`) create the directory.

**Implementation**: Rather than changing `_resolve_dir` globally, handle this in `_handle_init` before resolving: if `args.dir` is set and doesn't exist, create it. This keeps the existing "dir must exist" behavior for all other commands.

**Alternatives considered**:
- *Change `_resolve_dir` to always create*: Would mask errors for non-init commands where a missing directory likely means a typo.

### 4. Keep `validate_name` import out of `init_repo`

**Decision**: `init_repo` won't validate a name since it doesn't take one. Remove the dependency on `validate_name`.

**Rationale**: The function now only needs a target path. No name validation is needed.

### 5. Template content as module-level constants

**Decision**: Keep `SKILLS_KDL_TEMPLATE` and `GITIGNORE_ENTRIES` as module-level string constants in `init.py`, matching the existing pattern used by `SKILL_MD_TEMPLATE`.

**Rationale**: Consistent with existing code style. Templates are small enough that external files aren't warranted.

## Risks / Trade-offs

- **Breaking change for existing users** → Acceptable for pre-1.0 tool. No known automation depends on `quiv init <name>`. Document in changelog.
- **`.gitignore` append logic could duplicate entries if file has unusual formatting** → Mitigate by checking for the exact quiv comment marker line (`# quiv -`) before appending.
- **`_resolve_dir` special-casing for init adds a code smell** → Small scope, well-documented. Can revisit if more commands need directory creation.
