## ADDED Requirements

### Requirement: Sync fetch downloads from GitHub API
The system SHALL download skill sources from GitHub repositories using the GitHub API tarball endpoint.

#### Scenario: GitHub source fetched via API
- **WHEN** user runs `quiv sync fetch` with a GitHub source defined in manifest
- **THEN** the system downloads the tarball via GitHub API

#### Scenario: GitHub API respects auth token
- **WHEN** `GITHUB_TOKEN` environment variable is set
- **THEN** the system uses it for authenticated API requests to avoid rate limits

### Requirement: Sync fetch falls back to git sparse checkout
The system SHALL fall back to git sparse checkout for non-GitHub hosts.

#### Scenario: Non-GitHub source uses sparse checkout
- **WHEN** user runs `quiv sync fetch` with a non-GitHub git source
- **THEN** the system performs a sparse checkout of only the required paths

#### Scenario: Sparse checkout minimizes data transfer
- **WHEN** a source has a path filter specified
- **THEN** the system only fetches files matching the filter pattern

### Requirement: Sync fetch supports skip-if-up-to-date
The system SHALL skip fetching sources that are already at the latest pinned SHA.

#### Scenario: Up-to-date source skipped
- **WHEN** a source has a `.source.kdl` with matching SHA and upstream hasn't changed
- **THEN** the system skips the fetch and reports "up to date"

#### Scenario: Out-of-date source fetched
- **WHEN** upstream SHA differs from local `.source.kdl`
- **THEN** the system fetches the new version

### Requirement: Sync fetch supports source filtering
The system SHALL support filtering which skills to fetch within a source.

#### Scenario: Filter applies to source fetch
- **WHEN** a source definition includes a `filter` property
- **THEN** only skills matching the filter are fetched

#### Scenario: No filter fetches all
- **WHEN** a source definition lacks a `filter` property
- **THEN** all skills from the source are fetched

### Requirement: Sync diff compares local vs upstream
The system SHALL compare local skills against upstream versions and report differences.

#### Scenario: Diff shows version differences
- **WHEN** user runs `quiv sync diff`
- **THEN** the system displays which skills have upstream changes

#### Scenario: Diff with latest mode ignores pins
- **WHEN** user runs `quiv sync diff --latest`
- **THEN** the system compares against latest upstream regardless of pinned SHA

### Requirement: Sync update applies upstream changes
The system SHALL update local skills to match upstream versions with conflict detection.

#### Scenario: Update applies changes
- **WHEN** user runs `quiv sync update`
- **THEN** the system updates local skills to match upstream

#### Scenario: Update detects local modifications
- **WHEN** local skills have uncommitted changes
- **THEN** the system warns about potential conflicts

#### Scenario: Force update ignores local changes
- **WHEN** user runs `quiv sync update --force`
- **THEN** the system overwrites local changes without warning

#### Scenario: Per-skill targeting supported
- **WHEN** user runs `quiv sync update <skill-name>`
- **THEN** only that specific skill is updated
