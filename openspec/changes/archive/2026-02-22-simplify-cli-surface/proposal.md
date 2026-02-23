## Why

The CLI command surface doesn't match the tool's purpose. `quiv` exists to declaratively
assemble a curated skill collection from disparate git repos — `skills.kdl` declares
desired state, and the tool makes `skills/` match it. But the current API (`sync fetch`,
`sync diff`, `sync update`, `validate`, `package`) exposes a multi-step manual workflow
instead of a single declarative operation. `sync` reads as a verb but acts as a namespace.
`validate` and `package` serve no clear consumer in the actual workflow (skills are
validated upstream, and the git repo itself is the distribution format for `npx skills`).

## What Changes

- **BREAKING**: Remove `quiv sync fetch`, `quiv sync diff`, `quiv sync update` sub-command hierarchy
- **BREAKING**: Remove `quiv validate` command entirely
- **BREAKING**: Remove `quiv package` command entirely
- Introduce `quiv sync` as a top-level verb that resolves `skills.kdl` and makes `skills/` match it
- Add `quiv sync --dry-run` flag to show what would change without writing anything
- Treat `skills/` as a build output owned by `quiv` — no local edit protection, no `--force` flags
- `quiv sync` is incremental (skips skills whose provenance SHA matches upstream) but always overwrites stale skills without warning
- Retain `quiv init` unchanged

## Capabilities

### New Capabilities

_(None — this is a simplification, not a new capability. The sync engine already does the work; we're collapsing the interface to it.)_

### Modified Capabilities

- `cli-framework`: Command dispatch changes — remove `sync` sub-command routing, `validate` dispatch, and `package` dispatch. `sync` becomes a direct top-level command with `--dry-run` flag.
- `sync-engine`: Collapse fetch/diff/update into a single `sync` operation. Remove local edit protection. Add dry-run mode that reports what would change without downloading. Remove per-skill targeting from update (always sync everything).
- `skill-validation`: **Remove entirely** — validation is not part of the tool's responsibility.
- `skill-packaging`: **Remove entirely** — the git repo is the distribution format.

## Impact

- **CLI**: All existing `quiv sync fetch/diff/update`, `quiv validate`, and `quiv package` invocations break
- **Code**: `validate.py` and `package.py` can be deleted. `cli.py` simplifies significantly (no sub-parser for sync). `sync.py` merges fetch+update logic and adds dry-run path.
- **Specs**: `skill-validation` and `skill-packaging` specs should be archived. `sync-engine` and `cli-framework` specs need delta updates.
- **Tests**: Tests for validate, package, and the three-command sync workflow need to be rewritten or removed
- **Dependencies**: No new dependencies. `errors.py` can drop `ValidationError` and `PackageError`.
