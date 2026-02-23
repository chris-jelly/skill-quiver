## Context

The current CLI exposes five commands (`sync fetch`, `sync diff`, `sync update`, `validate`,
`package`) that model a multi-step manual workflow. The tool's actual purpose is simpler:
read a declarative manifest and make `skills/` match it. This change collapses the interface
to `quiv sync` (with `--dry-run`) and `quiv init`, deleting `validate` and `package` entirely.

The sync engine already contains all the core logic (resolve SHAs, download tarballs, sparse
checkout fallback, provenance tracking, license generation). The change is primarily a
restructuring of how that logic is composed and exposed, not a rewrite.

## Goals / Non-Goals

**Goals:**

- Single top-level `quiv sync` command that resolves manifest and makes `skills/` match it
- `--dry-run` flag that reports what would change without downloading or writing
- `skills/` treated as a build output — always overwritten when stale, no local edit protection
- Incremental by default — skip skills whose provenance SHA matches upstream
- Simpler CLI parser — no sub-command nesting under `sync`
- Remove `validate.py`, `package.py`, and their test suites
- Remove `ValidationError` and `PackageError` from the error hierarchy

**Non-Goals:**

- Rewriting the fetch/download logic (tarball, sparse checkout) — it works, we're recomposing it
- Changing the manifest format (`skills.kdl`)
- Changing provenance tracking (`.source.kdl`)
- Changing license generation behavior
- Adding interactive prompts or confirmation steps

## Decisions

### 1. Merge fetch + update into a single `sync` function

**Choice:** A single `sync(manifest, dry_run=False)` function replaces `sync_fetch`,
`sync_diff`, and `sync_update`.

**Rationale:** The fetch/update split existed to protect local edits — `fetch` downloaded
state, `update` applied it with safety checks. Since `skills/` is now a build output, the
safety layer is unnecessary. The operation is: resolve each source's SHA, compare with
provenance, and for anything stale, delete and re-extract.

**Alternative considered:** Keep `sync_fetch` and `sync_update` as internal functions called
sequentially by the public `sync` function. Rejected because there's no intermediate state
worth preserving — fetch-then-update is a single atomic operation per source.

### 2. Dry-run resolves SHAs but does not download tarballs

**Choice:** `--dry-run` makes API calls to resolve upstream SHAs and compares them against
local provenance, then reports what would change. It does not download tarballs or write files.

**Rationale:** SHA resolution is cheap (one API call per source). Downloading tarballs is
expensive and unnecessary for a "what would change?" check. This replaces `sync diff`
for the common case. Users who want a file-level diff can run `quiv sync` and then `git diff`.

**Output format for dry-run:**
```
$ quiv sync --dry-run
community-skills: a1b2c3d → f4e5d6a (2 skills)
bob-toolkit: up to date
```

### 3. Remove `_diff_directories` entirely

**Choice:** Delete the file-level diff logic.

**Rationale:** `skills/` is a git-tracked build output. After `quiv sync`, `git diff` shows
exactly what changed, with better formatting than our custom differ. The `_diff_directories`
function duplicates what git does and adds ~50 lines of code to maintain.

### 4. Remove sub-parser nesting in argparse

**Choice:** `sync` becomes a direct sub-command with `--dry-run` as its only flag, at the
same level as `init`. No nested sub-parsers.

**Before:**
```python
sync_parser = subparsers.add_parser("sync")
sync_sub = sync_parser.add_subparsers(dest="sync_command")
sync_sub.add_parser("fetch")
# ... etc
```

**After:**
```python
sync_parser = subparsers.add_parser("sync")
sync_parser.add_argument("--dry-run", action="store_true")
```

The `_handle_sync` function no longer dispatches to sub-commands — it calls `sync()` directly.

### 5. Delete modules and error classes, don't deprecate

**Choice:** Remove `validate.py`, `package.py`, `ValidationError`, and `PackageError` outright.

**Rationale:** This is a pre-1.0 tool with no published consumers. No deprecation period needed.
Clean deletion is simpler and avoids dead code.

### 6. Stale skill replacement strategy

**Choice:** When a skill is stale (provenance SHA differs from upstream), delete the entire
skill directory with `shutil.rmtree` and re-extract from the tarball. Don't attempt
incremental file patching.

**Rationale:** This matches the "build output" mental model. It's simpler, avoids
file-level merge conflicts, and guarantees the local state matches upstream exactly.
The current `sync_update` already does this (behind `--force`); we just remove the guard.

## Risks / Trade-offs

- **[Breaking change for all existing users]** → Pre-1.0 tool, unlikely to have external
  users yet. README and spec updates will document the new interface.

- **[Loss of file-level diff]** → Users lose `quiv sync diff` output. Mitigated by `git diff`
  after sync, which is strictly better (syntax highlighting, paging, etc.).

- **[Dry-run requires network access]** → SHA resolution hits the GitHub API even in dry-run
  mode. Acceptable because the whole point is checking upstream state. Could add offline
  provenance-only reporting later if needed.

- **[No per-skill targeting]** → `sync update <skill>` goes away. `quiv sync` always
  processes all sources. Acceptable because the operation is incremental (skips up-to-date
  skills) so the cost of "sync everything" is low. If a single-skill sync is needed later,
  it can be added as `quiv sync --source <name>`.
