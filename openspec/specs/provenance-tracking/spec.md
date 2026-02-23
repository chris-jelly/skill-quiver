## ADDED Requirements

### Requirement: System writes provenance on fetch
The system SHALL write `.source.kdl` files to track provenance information when fetching skills.

#### Scenario: Source file created on fetch
- **WHEN** user runs `quiv sync fetch` successfully
- **THEN** the system creates `.source.kdl` file for each fetched skill

#### Scenario: Source file contains origin
- **WHEN** a `.source.kdl` file is written
- **THEN** it contains the origin repository URL

#### Scenario: Source file contains pinned SHA
- **WHEN** a `.source.kdl` file is written
- **THEN** it contains the exact git SHA that was fetched

#### Scenario: Source file contains license
- **WHEN** a `.source.kdl` file is written
- **THEN** it contains the license identifier from the manifest if provided

#### Scenario: Source file contains timestamp
- **WHEN** a `.source.kdl` file is written
- **THEN** it contains the fetch timestamp in ISO 8601 format

### Requirement: System reads provenance for skip detection
The system SHALL read `.source.kdl` files to determine if a skill needs updating.

#### Scenario: SHA comparison for updates
- **WHEN** checking if update is needed
- **THEN** the system reads local `.source.kdl` SHA and compares with upstream

#### Scenario: Missing source file triggers full fetch
- **WHEN** a skill lacks a `.source.kdl` file
- **THEN** the system treats it as needing a full fetch

### Requirement: Provenance file uses KDL format
The system SHALL use KDL format for `.source.kdl` files for consistency with manifest.

#### Scenario: Valid KDL structure
- **WHEN** a `.source.kdl` file is written
- **THEN** it is valid KDL that can be parsed by the system

### Requirement: Provenance supports multiple sources
The system SHALL track provenance for skills from multiple different sources.

#### Scenario: Different sources tracked separately
- **WHEN** skills are fetched from multiple git repositories
- **THEN** each skill has its own `.source.kdl` with correct origin information

### Requirement: Provenance files are version-controlled
The system SHALL NOT exclude `.source.kdl` files from version control. Provenance files are committed alongside skill directories as the per-skill source of truth.

#### Scenario: Source files appear in git
- **WHEN** user runs `quiv sync` and commits the results
- **THEN** `.source.kdl` files are included in the commit alongside skill files

#### Scenario: Provenance changes visible in diffs
- **WHEN** a skill is updated to a new SHA via `quiv sync`
- **THEN** the `.source.kdl` change appears in the git diff for review
