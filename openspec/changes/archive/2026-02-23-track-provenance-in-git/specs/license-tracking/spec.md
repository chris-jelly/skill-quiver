## MODIFIED Requirements

### Requirement: System formats license file consistently
The system SHALL format the THIRD_PARTY_LICENSES file in a consistent, readable manner.

#### Scenario: Per-source section format
- **WHEN** the license file is generated
- **THEN** each source has a clearly separated section with name, URL, license, and skills list

#### Scenario: Chronological ordering
- **WHEN** sources are listed
- **THEN** they are ordered by source name alphabetically

#### Scenario: Skills listed per source
- **WHEN** a source has skills declared in the manifest
- **THEN** the source section includes a "Skills:" heading followed by each skill name as an indented bullet item, sorted alphabetically
