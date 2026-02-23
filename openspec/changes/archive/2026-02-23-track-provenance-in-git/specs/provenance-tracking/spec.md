## ADDED Requirements

### Requirement: Provenance files are version-controlled
The system SHALL NOT exclude `.source.kdl` files from version control. Provenance files are committed alongside skill directories as the per-skill source of truth.

#### Scenario: Source files appear in git
- **WHEN** user runs `quiv sync` and commits the results
- **THEN** `.source.kdl` files are included in the commit alongside skill files

#### Scenario: Provenance changes visible in diffs
- **WHEN** a skill is updated to a new SHA via `quiv sync`
- **THEN** the `.source.kdl` change appears in the git diff for review
