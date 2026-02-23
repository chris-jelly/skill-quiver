## 1. Delete removed modules and error classes

- [x] 1.1 Delete `src/skill_quiver/validate.py`
- [x] 1.2 Delete `src/skill_quiver/package.py`
- [x] 1.3 Remove `ValidationError` and `PackageError` from `src/skill_quiver/errors.py`

## 2. Rewrite sync engine

- [x] 2.1 Replace `sync_fetch`, `sync_diff`, `sync_update` with a single `sync(manifest, dry_run=False)` function in `src/skill_quiver/sync.py`
- [x] 2.2 Implement dry-run path: resolve upstream SHAs, compare with provenance, report what would change without downloading
- [x] 2.3 Remove local edit protection — stale skills are deleted and re-extracted unconditionally
- [x] 2.4 Remove `_diff_directories` and all file-level diff logic
- [x] 2.5 Remove per-skill targeting (the `skill_name` parameter on update)

## 3. Simplify CLI parser and dispatch

- [x] 3.1 Remove `sync` sub-parser nesting (fetch/diff/update) from `_build_parser` in `src/skill_quiver/cli.py`
- [x] 3.2 Add `--dry-run` flag directly to the `sync` sub-command
- [x] 3.3 Remove `validate` and `package` sub-commands from `_build_parser`
- [x] 3.4 Remove `_handle_validate` and `_handle_package` functions
- [x] 3.5 Simplify `_handle_sync` to call `sync()` directly instead of dispatching to sub-commands

## 4. Update tests

- [x] 4.1 Delete `tests/test_validate.py`
- [x] 4.2 Delete `tests/test_package.py`
- [x] 4.3 Rewrite `tests/test_sync.py` to test the unified `sync()` function, including dry-run mode
- [x] 4.4 Update `tests/test_cli.py` to reflect the new command surface (no sub-commands under sync, no validate/package)

## 5. Update documentation

- [x] 5.1 Rewrite `README.md` to reflect the simplified CLI: `quiv init`, `quiv sync`, `quiv sync --dry-run`
- [x] 5.2 Update `skill-quiver-spec.md` to remove references to validate, package, and the sync sub-command hierarchy

## 6. Verify

- [x] 6.1 Run full test suite and confirm all tests pass
- [x] 6.2 Run `ruff check src/ tests/` and `ruff format src/ tests/`
