## MODIFIED Requirements

### Requirement: Sync fetch downloads from GitHub API
The system SHALL download skill sources from GitHub repositories using the GitHub API tarball endpoint when `quiv sync` is run.

#### Scenario: GitHub source fetched via API
- **WHEN** user runs `quiv sync` with a GitHub source defined in manifest
- **THEN** the system downloads the tarball via GitHub API

#### Scenario: GitHub API respects auth token
- **WHEN** `GITHUB_TOKEN` environment variable is set
- **THEN** the system uses it for authenticated API requests to avoid rate limits

### Requirement: Sync fetch falls back to git sparse checkout
The system SHALL fall back to git sparse checkout for non-GitHub hosts when `quiv sync` is run.

#### Scenario: Non-GitHub source uses sparse checkout
- **WHEN** user runs `quiv sync` with a non-GitHub git source
- **THEN** the system performs a sparse checkout of only the required paths

#### Scenario: Sparse checkout minimizes data transfer
- **WHEN** a source has a path filter specified
- **THEN** the system only fetches files matching the filter pattern

### Requirement: Sync fetch supports skip-if-up-to-date
The system SHALL skip fetching sources that are already at the latest upstream SHA, using local provenance for comparison.

#### Scenario: Up-to-date source skipped
- **WHEN** a source has a `.source.kdl` with SHA matching the current upstream SHA
- **THEN** the system skips the fetch and reports "up to date"

#### Scenario: Out-of-date source fetched
- **WHEN** upstream SHA differs from local `.source.kdl`
- **THEN** the system fetches the new version

### Requirement: Sync overwrites stale skills unconditionally
The system SHALL treat `skills/` as a build output. When a skill is stale, the system SHALL delete the local skill directory and re-extract from upstream without warning or confirmation.

#### Scenario: Stale skill replaced without warning
- **WHEN** a skill's provenance SHA differs from upstream
- **THEN** the system deletes the local skill directory and re-extracts from upstream

#### Scenario: Local edits are not protected
- **WHEN** a user has manually edited files in a skill directory
- **AND** the skill's provenance SHA differs from upstream
- **THEN** the system overwrites the local edits without warning

### Requirement: Sync supports dry-run mode
The system SHALL support a `--dry-run` flag that resolves upstream SHAs and reports what would change without downloading tarballs or writing files.

#### Scenario: Dry-run reports pending changes
- **WHEN** user runs `quiv sync --dry-run`
- **AND** some sources have upstream changes
- **THEN** the system reports which sources would be updated with old and new SHAs

#### Scenario: Dry-run reports up-to-date state
- **WHEN** user runs `quiv sync --dry-run`
- **AND** all sources are up to date
- **THEN** the system reports all skills are up to date

#### Scenario: Dry-run does not write files
- **WHEN** user runs `quiv sync --dry-run`
- **THEN** no files in `skills/` are created, modified, or deleted

## REMOVED Requirements

### Requirement: Sync diff compares local vs upstream
**Reason**: File-level diff is removed. Since `skills/` is a git-tracked build output, `git diff` after `quiv sync` provides strictly better output (syntax highlighting, paging). The `--dry-run` flag replaces the "what's changed?" use case at the SHA level.
**Migration**: Use `quiv sync --dry-run` to check for upstream changes, then `quiv sync && git diff` for file-level details.

### Requirement: Sync update applies upstream changes
**Reason**: The separate `update` command is removed. `quiv sync` now performs the full resolve-and-apply operation in a single step. Local edit protection (`--force`) is removed because `skills/` is a build output.
**Migration**: Replace `quiv sync update` with `quiv sync`. Replace `quiv sync update --force` with `quiv sync` (force is now the only behavior).

### Requirement: Sync fetch supports source filtering
**Reason**: Per-skill targeting via `filter` is removed. `quiv sync` always processes all sources and all skills declared in the manifest. The operation is incremental (skips up-to-date skills) so the cost is low.
**Migration**: Remove `filter` usage. To exclude skills, remove them from `skills.kdl`.
