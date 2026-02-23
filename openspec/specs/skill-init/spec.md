## ADDED Requirements

### Requirement: System scaffolds skill directory
The system SHALL create skill directory structure with template content when initializing a new skill.

#### Scenario: Skill directory created
- **WHEN** user runs `quiv init <skill-name>`
- **THEN** a new directory is created with the skill name

#### Scenario: Directory already exists shows error
- **WHEN** user tries to init a skill in an existing directory
- **THEN** the system displays an error and exits

### Requirement: System creates template SKILL.md
The system SHALL create a SKILL.md file with template frontmatter when scaffolding.

#### Scenario: SKILL.md created with template
- **WHEN** a skill is initialized
- **THEN** a SKILL.md file is created with template frontmatter including name field pre-filled

#### Scenario: Template includes required fields
- **WHEN** a template SKILL.md is created
- **THEN** it includes all required frontmatter fields with placeholder values

### Requirement: System creates standard subdirectories
The system SHALL create standard subdirectories when scaffolding a skill.

#### Scenario: Scripts directory created
- **WHEN** a skill is initialized
- **THEN** a `scripts/` subdirectory is created

#### Scenario: References directory created
- **WHEN** a skill is initialized
- **THEN** a `references/` subdirectory is created

#### Scenario: Assets directory created
- **WHEN** a skill is initialized
- **THEN** an `assets/` subdirectory is created

### Requirement: System validates skill name on init
The system SHALL validate the skill name before creating the directory.

#### Scenario: Invalid name rejected
- **WHEN** user provides an invalid skill name to init
- **THEN** the system displays validation error and exits without creating files

#### Scenario: Valid name accepted
- **WHEN** user provides a valid skill name
- **THEN** the system proceeds with initialization

### Requirement: System supports custom output path
The system SHALL support specifying a custom output path for the new skill.

#### Scenario: Custom path used
- **WHEN** user provides `--output /custom/path` flag
- **THEN** the skill is created at the specified path instead of CWD

#### Scenario: Custom path parent directories created
- **WHEN** the custom output path includes non-existent parent directories
- **THEN** the system creates all necessary parent directories
