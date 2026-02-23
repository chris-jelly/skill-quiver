## ADDED Requirements

### Requirement: System tracks third-party licenses
The system SHALL generate and maintain a THIRD_PARTY_LICENSES file aggregating license information from all skill sources.

#### Scenario: License file generated after fetch
- **WHEN** user runs `quiv sync fetch` successfully
- **THEN** a THIRD_PARTY_LICENSES file is created/updated in the working directory

#### Scenario: License information aggregated
- **WHEN** multiple sources have different licenses
- **THEN** the THIRD_PARTY_LICENSES file lists all licenses with source attribution

### Requirement: System extracts license from manifest
The system SHALL use license information specified in the skills.kdl manifest.

#### Scenario: Source license extracted
- **WHEN** a source has a `license` property in manifest
- **THEN** that license is included in THIRD_PARTY_LICENSES

#### Scenario: Missing license noted
- **WHEN** a source lacks a license property
- **THEN** the system notes "License not specified" for that source

### Requirement: System formats license file consistently
The system SHALL format the THIRD_PARTY_LICENSES file in a consistent, readable manner.

#### Scenario: Per-source section format
- **WHEN** the license file is generated
- **THEN** each source has a clearly separated section with name, URL, and license

#### Scenario: Chronological ordering
- **WHEN** sources are listed
- **THEN** they are ordered by source name alphabetically

### Requirement: System cleans up when sources removed
The system SHALL update THIRD_PARTY_LICENSES when sources are removed from the manifest.

#### Scenario: Removed source deleted from licenses
- **WHEN** a source is removed from skills.kdl and sync is run
- **THEN** that source is no longer listed in THIRD_PARTY_LICENSES

#### Scenario: Empty manifest removes license file
- **WHEN** all sources are removed from skills.kdl
- **THEN** the THIRD_PARTY_LICENSES file is removed

### Requirement: System handles license file conflicts
The system SHALL handle cases where THIRD_PARTY_LICENSES cannot be written.

#### Scenario: Permission error shown
- **WHEN** the system cannot write to THIRD_PARTY_LICENSES due to permissions
- **THEN** an appropriate error message is displayed

#### Scenario: Read-only file handled
- **WHEN** THIRD_PARTY_LICENSES exists but is read-only
- **THEN** the system attempts to make it writable or reports the conflict
