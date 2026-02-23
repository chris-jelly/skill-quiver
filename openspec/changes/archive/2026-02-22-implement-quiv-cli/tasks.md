## 1. Project Setup

- [x] 1.1 Create `pyproject.toml` with package metadata, Python >= 3.13 requirement, dependencies (`kdl-py`, `pydantic`, `httpx`), dev dependencies (`pytest`, `respx`, `ruff`), and `[project.scripts]` entry point `quiv = "skill_quiver.cli:main"`
- [x] 1.2 Create `src/skill_quiver/__init__.py` with `__version__` string
- [x] 1.3 Create `src/skill_quiver/errors.py` with `QuivError` base exception (message, exit_code), `ManifestError`, `SyncError`, `ValidationError`, `PackageError`, `InitError` subclasses
- [x] 1.4 Verify project installs with `uv pip install -e .` and `quiv --version` runs

## 2. CLI Framework

- [x] 2.1 Create `src/skill_quiver/cli.py` with `argparse` top-level parser: `--version`, `--dir` global flag, subcommand registration for `sync`, `validate`, `init`, `package`
- [x] 2.2 Implement `sync` subcommand group with `fetch`, `diff`, `update` sub-parsers (flags: `--latest` for diff, `--force` and optional skill name for update)
- [x] 2.3 Implement `validate` subcommand parser with optional `<skill-name>` positional arg
- [x] 2.4 Implement `init` subcommand parser with required `<skill-name>` and optional `--output` flag
- [x] 2.5 Implement `package` subcommand parser with required `<skill-name>` and optional `--output` flag
- [x] 2.6 Implement `main()` entry point with `QuivError` catch-all, stderr output, exit code handling
- [x] 2.7 Implement `find_manifest(start: Path) -> Path` helper that walks up directory tree looking for `skills.kdl`
- [x] 2.8 Write `tests/test_cli.py` with end-to-end tests: `--help`, `--version`, unknown command error, `--dir` with valid/invalid paths, missing manifest error

## 3. Manifest Parsing

- [x] 3.1 Create `src/skill_quiver/manifest.py` with Pydantic `Source` model: name (validated kebab-case pattern), repo (`HttpUrl`), path (default `"."`), ref (default `"main"`), license (optional), attribution (optional), skills (`list[str]`, min_length=1 with name format validator)
- [x] 3.2 Create `Manifest` model: `sources: list[Source]`, `root: Path`
- [x] 3.3 Implement `parse_manifest(path: Path) -> Manifest` function: read file, `kdl.parse()`, traverse `source` nodes, extract properties into dicts, `Source.model_validate()` each, return `Manifest`
- [x] 3.4 Implement error handling: `ManifestError` for invalid KDL syntax with line context, missing required fields, invalid source names
- [x] 3.5 Write `tests/test_manifest.py` with fixtures for valid/invalid KDL files, missing fields, invalid names, multiple sources, optional field defaults

## 4. Provenance Tracking

- [x] 4.1 Create `src/skill_quiver/provenance.py` with Pydantic `Provenance` model: repo (`str`), path (`str`), ref (`str`), sha (`str`), license (`str | None`), fetched (`datetime`)
- [x] 4.2 Implement `write_provenance(skill_dir: Path, provenance: Provenance)` using `kdl` document builder and `kdl.dump()` to write `.source.kdl`
- [x] 4.3 Implement `read_provenance(skill_dir: Path) -> Provenance | None` using `kdl.parse()` and `Provenance.model_validate()`; return `None` if file missing
- [x] 4.4 Write `tests/test_provenance.py` with round-trip read/write tests, missing file handling, invalid KDL content

## 5. Sync Engine

- [x] 5.1 Create `src/skill_quiver/sync.py` with shared `httpx.Client` factory that reads `GITHUB_TOKEN` from env and configures auth header
- [x] 5.2 Implement `resolve_sha(client, source) -> str` to get latest commit SHA via GitHub API (`GET /repos/{owner}/{repo}/commits/{ref}`)
- [x] 5.3 Implement `fetch_github_tarball(client, source, sha, dest) -> list[Path]`: download tarball via streaming `GET /repos/{owner}/{repo}/tarball/{ref}`, extract with `tarfile`, filter to declared skill directories
- [x] 5.4 Implement `fetch_git_sparse(source, dest) -> list[Path]`: `subprocess.run` git sparse checkout fallback for non-GitHub hosts, check `git` availability
- [x] 5.5 Implement `sync_fetch(manifest: Manifest)`: iterate sources, detect GitHub vs non-GitHub by hostname, skip if up-to-date (compare provenance SHA), fetch, write provenance, update license file
- [x] 5.6 Implement `sync_diff(manifest: Manifest, latest: bool)`: compare local skill files vs upstream using `difflib.unified_diff`, report added/removed/changed per skill
- [x] 5.7 Implement `sync_update(manifest: Manifest, skill_name: str | None, force: bool)`: detect local modifications, apply upstream changes, respect `--force`, support per-skill targeting
- [x] 5.8 Write `tests/test_sync.py` with `respx` mocked HTTP fixtures: fetch happy path, skip-if-up-to-date, GitHub auth, sparse checkout fallback, diff output, update conflict detection

## 6. Skill Validation

- [x] 6.1 Create `src/skill_quiver/validate.py` with `validate_name(name: str) -> list[str]` checking: lowercase alphanumeric + single hyphens, 1-64 chars, no consecutive hyphens, no leading/trailing hyphens
- [x] 6.2 Implement `validate_frontmatter(skill_dir: Path) -> list[str]`: read SKILL.md, extract YAML frontmatter, parse with `SkillFrontmatter` Pydantic model, collect errors
- [x] 6.3 Implement `validate_skill(skill_dir: Path) -> list[str]`: run name validation, frontmatter validation, name/directory mismatch check, return all errors
- [x] 6.4 Implement `validate_all(root: Path, skill_name: str | None) -> dict[str, list[str]]`: discover skill directories, validate each (or single if name given), return results keyed by skill name
- [x] 6.5 Write `tests/test_validate.py` with fixtures: valid skill, missing SKILL.md, invalid frontmatter, invalid names (uppercase, spaces, consecutive hyphens, too long), name/directory mismatch, batch validation

## 7. Skill Init

- [x] 7.1 Create `src/skill_quiver/init.py` with `init_skill(name: str, output: Path | None, root: Path)`: validate name, resolve output path, check directory doesn't exist, create directory
- [x] 7.2 Implement template SKILL.md generation with pre-filled name and placeholder frontmatter fields (name, description, triggers)
- [x] 7.3 Create standard subdirectories: `scripts/`, `references/`, `assets/` with `.gitkeep` files
- [x] 7.4 Write `tests/test_init.py` with tests: successful scaffold, existing directory error, invalid name rejection, custom output path, parent directory creation

## 8. Skill Packaging

- [x] 8.1 Create `src/skill_quiver/package.py` with `package_skill(skill_dir: Path, output: Path | None)`: validate skill exists and has SKILL.md, run validation
- [x] 8.2 Implement zip creation: walk skill directory, exclude hidden files (`.` prefix), write to zip with `zipfile`, default output `<skill-name>.zip` in CWD
- [x] 8.3 Implement result reporting: file count, archive size, output path
- [x] 8.4 Write `tests/test_package.py` with tests: successful packaging, missing SKILL.md error, hidden file exclusion, custom output path, validation failure

## 9. License Tracking

- [x] 9.1 Add `generate_license_file(manifest: Manifest, root: Path)` to `src/skill_quiver/sync.py` (or a dedicated helper): iterate sources alphabetically, format per-source sections with name/URL/license
- [x] 9.2 Handle missing license (note "License not specified"), handle empty manifest (remove file)
- [x] 9.3 Integrate license file generation into `sync_fetch` flow (called after successful fetch)
- [x] 9.4 Write tests for license file: generation, alphabetical ordering, missing licenses, cleanup on empty manifest

## 10. Integration and Polish

- [x] 10.1 Create `tests/conftest.py` with shared fixtures: sample `skills.kdl` manifest, sample skill directories with valid SKILL.md, tmp_path wrappers
- [x] 10.2 Wire all command handlers in `cli.py` to their respective module functions (sync -> sync.py, validate -> validate.py, init -> init.py, package -> package.py)
- [x] 10.3 Run full test suite with `pytest`, fix any failures
- [x] 10.4 Run `ruff check` and `ruff format` on all source files, fix any issues
