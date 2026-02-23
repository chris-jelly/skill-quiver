## Context

The `skill-quiver` repo is currently empty (no source code). We are building the `quiv` CLI from scratch, extracting and restructuring logic from ~1,400 lines of scripts in the `ai-skills` repository. The original scripts use `argparse`, raw `urllib` calls to GitHub API, `subprocess` for git operations, and a custom KDL parser wrapper. The new CLI must be a proper installable Python package that operates on any directory containing a `skills.kdl` manifest.

Key constraints:
- Python >= 3.13 (modern syntax: `match`, `type` aliases, `tomllib`, improved error messages)
- Runtime dependencies: `kdl-py` (KDL parsing), `pydantic` (data modeling/validation), `httpx` (HTTP client)
- Must work without network access for local-only commands (`validate`, `init`, `package`)
- Must handle both GitHub (API tarball) and non-GitHub (git sparse checkout) repos
- All commands are non-interactive

## Goals / Non-Goals

**Goals:**
- Installable CLI package with `quiv` entry point via `pyproject.toml` `[project.scripts]`
- Clean module boundaries matching the 7-module structure from the spec
- CWD-based manifest discovery (search upward like git)
- Robust error handling with clear user-facing messages
- Testable architecture (IO at the edges, logic in the core)

**Non-Goals:**
- Agent directory installation (delegated to `npx skills`)
- Plugin system or extensibility hooks
- Async/concurrent fetching (sequential is fine for v1)
- Rich TUI output (plain text with minimal formatting)
- PyPI publishing infrastructure

## Decisions

### 1. CLI framework: `argparse` (stdlib) over Click/Typer

**Decision**: Use `argparse` from the standard library.

**Rationale**: The CLI has a simple command structure (`sync fetch|diff|update`, `validate`, `init`, `package`) with straightforward flags. `argparse` handles subcommands natively, adds zero dependencies, and the original scripts already use it. Click/Typer would add a dependency for no meaningful benefit at this complexity level.

**Alternatives considered**:
- **Click**: More ergonomic decorators but adds a dependency. The nested `sync` subcommand group is easily handled by `argparse` sub-parsers.
- **Typer**: Type-hint-based, but pulls in Click + typing-extensions. Overkill for 6 commands.

### 2. Module structure: flat package under `src/skill_quiver/`

**Decision**: Use the `src` layout with a flat module structure:

```
src/skill_quiver/
├── __init__.py       # Version string
├── cli.py            # argparse setup, command dispatch
├── manifest.py       # skills.kdl parsing → Pydantic models
├── sync.py           # fetch, diff, update logic
├── validate.py       # SKILL.md validation
├── package.py        # Zip packaging
├── init.py           # Skill scaffolding
└── provenance.py     # .source.kdl read/write
```

**Rationale**: The `src` layout prevents accidental imports of the local package during development. Flat structure is appropriate -- each module maps to a distinct command or concern with minimal cross-module dependencies.

### 3. Data modeling: Pydantic `BaseModel` for manifest, provenance, and validation

**Decision**: Use Pydantic v2 `BaseModel` for all structured data types.

**Rationale**: The project has significant validation logic -- manifest fields, skill name formats, SKILL.md frontmatter structure -- that Pydantic handles declaratively. Field-level validators (`Field(pattern=..., min_length=..., max_length=...)`) replace manual regex checks and error message construction. `model_validate()` transforms raw dicts (from KDL parsing or YAML frontmatter) into validated models with clear error messages for free. Serialization via `model_dump()` simplifies provenance file writing.

**Key models**:
- `Source(BaseModel)`: name, repo (`HttpUrl`), path (default `"."`), ref (default `"main"`), license, attribution (optional), skills (`list[str]`, `min_length=1`) with `@field_validator` for skill name format
- `Provenance(BaseModel)`: repo, path, ref, sha, license, fetched (`datetime`)
- `SkillFrontmatter(BaseModel)`: name (`Field(pattern=r'^[a-z0-9]+(-[a-z0-9]+)*$', max_length=64)`), description, and other frontmatter fields -- used by `validate` command
- `Manifest(BaseModel)`: list of sources, root directory path

**Alternatives considered**:
- **dataclasses**: Lighter weight but requires writing all validation logic manually. For a project with 3+ models that all need field validation, Pydantic pays for itself in reduced boilerplate and better error messages.
- **attrs**: Similar to dataclasses with validators, but Pydantic's `model_validate(dict)` pattern is a better fit for parsing KDL nodes and YAML frontmatter into structured data.

### 4. Manifest discovery: walk-up search from CWD

**Decision**: Starting from CWD (or `--dir`), search for `skills.kdl` in the current directory, then each parent, stopping at filesystem root.

**Rationale**: Mirrors git's `.git` discovery. Users can run `quiv` from any subdirectory of their skill repo. The discovered directory becomes the "root" for all relative operations (`skills/` output, `THIRD_PARTY_LICENSES` location).

**Implementation**: A `find_manifest(start: Path) -> Path` function that walks up `start.resolve().parents`. Commands that don't need a manifest (`init` with `--path`, `validate` with explicit path) skip discovery.

### 5. HTTP client: `httpx` for GitHub API and tarball downloads

**Decision**: Use `httpx` with a shared `httpx.Client` for all HTTP operations (GitHub API calls and tarball downloads).

**Rationale**: The GitHub tarball endpoint (`GET /repos/{owner}/{repo}/tarball/{ref}`) returns a 302 redirect to an S3 URL. `httpx` follows redirects automatically, while `urllib` requires manual redirect handling. Additional benefits:
- **Streaming downloads**: `client.stream("GET", url)` with chunked iteration for large tarballs, avoiding loading entire archives into memory
- **Connection pooling**: `httpx.Client()` reuses connections across multiple API calls within a single `sync fetch` run
- **Timeout control**: First-class `Timeout` object instead of `socket.setdefaulttimeout`
- **Testing**: `httpx.MockTransport` or the `respx` library provide clean request mocking, far simpler than patching `urllib.request.urlopen`
- **JSON handling**: `response.json()` and `response.raise_for_status()` reduce boilerplate
- **Async option**: `httpx.AsyncClient` is available if we add concurrent fetching later

**Auth**: Read `GITHUB_TOKEN` from environment, configure on client: `httpx.Client(headers={"Authorization": f"Bearer {token}"})`. Unauthenticated requests work but are rate-limited.

**Tarball extraction**: Download via `client.stream()`, pipe to `tarfile.open(fileobj=...)` for extraction. Extract only declared skill directories from the archive.

**Fallback**: For non-GitHub URLs (detected by hostname not matching `github.com`), shell out to `git clone --depth 1 --sparse-checkout` via `subprocess.run`.

**Alternatives considered**:
- **urllib.request**: Zero dependencies but requires manual redirect handling, manual chunked reads, manual JSON parsing, and awkward mocking. The original scripts used it, but it's the weakest part of their implementation.
- **requests**: Mature but `httpx` has a nearly identical API with better async support and more active development.

### 6. KDL parsing: `kdl-py` with manual node traversal

**Decision**: Use `kdl-py` (`kdl.parse()`) and manually traverse the document tree to extract `source` blocks and their children.

**Rationale**: `kdl-py` is the only maintained Python KDL parser. The parsing pipeline is: `kdl.parse()` → traverse nodes → build dicts → `Source.model_validate(dict)` (Pydantic). This gives us `kdl-py` for syntax and Pydantic for semantic validation, with clear error messages at both levels.

**Writing .source.kdl**: Use `Provenance.model_dump()` to get a dict, then build the KDL tree with `kdl-py`'s document builder and `kdl.dump()` to serialize. This keeps provenance files machine-readable and consistent.

### 7. Error handling: exceptions with structured exit codes

**Decision**: Define a `QuivError` base exception with a `message` and `exit_code`. Each module raises specific subclasses (`ManifestError`, `SyncError`, `ValidationError`). The CLI dispatcher in `cli.py` catches `QuivError` at the top level, prints the message to stderr, and exits with the code.

**Rationale**: Keeps business logic free of `sys.exit()` calls. Makes testing straightforward (assert exception type and message). Users get clean error messages without tracebacks.

**Exit codes**:
- 0: Success
- 1: General error (manifest not found, invalid arguments)
- 2: Validation failure (invalid SKILL.md, missing fields)

### 8. Diff implementation: `difflib` (stdlib)

**Decision**: Use `difflib.unified_diff` for comparing local vs upstream skill files.

**Rationale**: Stdlib, no dependency. Output format is familiar (unified diff). For recursive directory comparison, walk both trees with `pathlib`, compare file-by-file, and report added/removed/changed files.

**Alternative considered**: Shelling out to `diff -r`. Works but adds a platform dependency and is harder to test.

### 9. Testing strategy: `pytest` with filesystem fixtures

**Decision**: Use `pytest` with `tmp_path` fixtures for all file-system-dependent tests. Use `respx` or `httpx.MockTransport` for network tests.

**Rationale**: `pytest` is the standard. `tmp_path` provides isolated directories per test. `respx` provides declarative HTTP mocking for `httpx` that's cleaner than patching `urlopen`. Network mocking keeps tests fast and deterministic.

**Test structure**:
```
tests/
├── test_cli.py          # End-to-end CLI invocation tests
├── test_manifest.py     # KDL parsing and validation
├── test_sync.py         # Fetch, diff, update (mocked network)
├── test_validate.py     # SKILL.md validation
├── test_package.py      # Zip creation
├── test_init.py         # Scaffolding
├── test_provenance.py   # .source.kdl read/write
└── conftest.py          # Shared fixtures (sample manifests, skill dirs)
```

## Risks / Trade-offs

**[`kdl-py` maturity]** → `kdl-py` is a relatively niche library. If it has bugs or breaks on edge cases, we have no fallback KDL parser for Python. Mitigation: pin the version, keep manifest format simple, add thorough parsing tests. Could fall back to a regex-based parser for the simple subset we use, but only if necessary.

**[GitHub API rate limits]** → Unauthenticated API calls are limited to 60/hour. A manifest with many sources could hit this during initial fetch. Mitigation: document `GITHUB_TOKEN` setup prominently. Skip-if-up-to-date logic reduces repeat calls. Consider caching resolved SHAs.

**[`git` CLI dependency for non-GitHub hosts]** → The sparse checkout fallback requires `git` to be installed. Mitigation: this only affects non-GitHub sources, which are the minority use case. Check for `git` at command time and give a clear error if missing.

**[No concurrent fetching]** → Sequential fetching is slower for many sources. Mitigation: acceptable for v1. The skip-if-up-to-date optimization handles the common case (re-running fetch). Concurrent fetching can be added later with `concurrent.futures`.

**[Tarball extraction filtering]** → Extracting specific directories from a full-repo tarball downloads more data than needed. Mitigation: GitHub tarballs are compressed and typically small. Sparse checkout is the alternative but requires `git`. Tarball is simpler and works without git installed.
