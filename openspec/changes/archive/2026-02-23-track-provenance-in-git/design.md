## Context

Currently, `.source.kdl` provenance files are gitignored by `quiv init`. This means that when skill directories are committed and pushed, the pinned SHA, origin URL, and license information for each skill is lost. The `THIRD_PARTY_LICENSES` file exists but only lists source-level info without indicating which skills fall under each license.

The codebase is small and well-structured:
- `src/skill_quiver/init.py` has a `GITIGNORE_ENTRIES` constant with the `.source.kdl` exclusion
- `src/skill_quiver/sync.py` has `generate_license_file()` which iterates `manifest.sources` but doesn't use `source.skills`
- `src/skill_quiver/provenance.py` handles `.source.kdl` read/write (unchanged by this work)

## Goals / Non-Goals

**Goals:**
- Make `.source.kdl` files committed to git alongside skills, so provenance is version-controlled
- Add per-source skill lists to `THIRD_PARTY_LICENSES` so license-to-skill mapping is visible in one file

**Non-Goals:**
- Changing the `.source.kdl` format or content
- Changing provenance read/write logic
- Providing a migration tool for existing repos (users can manually remove the gitignore line)
- Changing `THIRD_PARTY_LICENSES` to a different file format

## Decisions

### 1. Remove `.source.kdl` from gitignore template entirely

**Decision**: Remove the `skills/**/.source.kdl` line and the marker comment from `GITIGNORE_ENTRIES` in `init.py`. The constant becomes empty, so `_configure_gitignore` should be removed and `init_repo` should stop calling it.

**Alternatives considered**:
- Keep gitignore but add a separate `quiv unignore` command: Overcomplicated for a one-line change.
- Make it configurable (ignore or not): Premature flexibility. Provenance in git is strictly better for auditability.

**Rationale**: The original design gitignored `.source.kdl` because it was considered machine-generated noise. But `skills/` itself is machine-generated and committed. Provenance is the most important metadata about vendored skills and should be reviewable in PRs.

### 2. Skill list format in THIRD_PARTY_LICENSES

**Decision**: Add a `Skills:` line followed by indented bullet items (`  - skill-name`) after the existing fields in each source section.

```
## community-skills
URL: https://github.com/org/ai-skills
License: MIT
Skills:
  - code-reviewer
  - readme-writer
```

**Alternatives considered**:
- Comma-separated on one line (`Skills: a, b, c`): Gets unwieldy with many skills.
- Markdown table: Heavier than needed for a list.
- Using a markdown library: The output is simple string concatenation of validated kebab-case names; no escaping needed.

**Rationale**: Bullet list is readable at any length and trivial to generate with f-strings. Skills are sorted alphabetically for consistency.

### 3. Init cleanup: remove gitignore configuration entirely

**Decision**: Since the only gitignore entry was `.source.kdl`, removing it leaves `GITIGNORE_ENTRIES` empty. Rather than keep dead code, remove `GITIGNORE_ENTRIES`, `GITIGNORE_MARKER`, `_configure_gitignore()`, and the gitignore-related steps from `init_repo()`. The init summary output should no longer mention `.gitignore`.

**Rationale**: Dead code is confusing. If future gitignore needs arise, the function can be reintroduced.

## Risks / Trade-offs

- **Larger diffs on sync**: Every `quiv sync` that updates a skill will now show `.source.kdl` changes in git diff. This is intentional and desirable (SHA changes become reviewable), but could surprise users used to clean diffs. → Acceptable; this is the point of the change.
- **Existing repos**: Repos initialized before this change will still have `.source.kdl` in their `.gitignore`. Users must manually remove the line. → Document in release notes. No automated migration needed for a single-line gitignore edit.
