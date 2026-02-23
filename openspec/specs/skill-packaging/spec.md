## ADDED Requirements

### Requirement: System creates distributable zip archives
The system SHALL create zip archives from skill directories for distribution.

#### Scenario: Zip archive created successfully
- **WHEN** user runs `quiv package <skill-name>`
- **THEN** a zip file is created containing the skill directory contents

#### Scenario: SKILL.md existence checked
- **WHEN** attempting to package a directory without SKILL.md
- **THEN** the system displays an error and exits without creating archive

### Requirement: System includes skill contents in archive
The system SHALL include all skill files and subdirectories in the archive.

#### Scenario: All files included
- **WHEN** a skill is packaged
- **THEN** the archive contains SKILL.md, all files in scripts/, references/, assets/

#### Scenario: Hidden files excluded
- **WHEN** a skill is packaged
- **THEN** hidden files (starting with .) are excluded from the archive

### Requirement: System supports custom output path
The system SHALL support specifying a custom output path for the zip archive.

#### Scenario: Custom output path used
- **WHEN** user runs `quiv package <skill-name> --output /path/to/output.zip`
- **THEN** the archive is created at the specified path

#### Scenario: Default output path used
- **WHEN** user runs `quiv package <skill-name>` without output flag
- **THEN** the archive is created as `<skill-name>.zip` in current directory

### Requirement: System validates skill before packaging
The system SHALL validate the skill structure before creating the archive.

#### Scenario: Invalid skill rejected
- **WHEN** attempting to package an invalid skill structure
- **THEN** the system displays validation errors and exits

#### Scenario: Valid skill accepted
- **WHEN** the skill passes validation
- **THEN** the system proceeds with packaging

### Requirement: System reports packaging results
The system SHALL provide feedback about the packaging operation.

#### Scenario: Success message displayed
- **WHEN** packaging completes successfully
- **THEN** the system displays the path to the created archive and file count/size

#### Scenario: Errors displayed on failure
- **WHEN** packaging fails
- **THEN** the system displays specific error messages explaining the failure
