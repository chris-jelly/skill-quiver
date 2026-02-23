## ADDED Requirements

### Requirement: System validates SKILL.md frontmatter
The system SHALL validate that SKILL.md files have proper frontmatter structure.

#### Scenario: Valid frontmatter passes
- **WHEN** a SKILL.md has valid YAML frontmatter with required fields
- **THEN** validation succeeds

#### Scenario: Missing frontmatter shows error
- **WHEN** a SKILL.md lacks frontmatter entirely
- **THEN** validation fails with error indicating missing frontmatter

#### Scenario: Invalid YAML frontmatter shows error
- **WHEN** a SKILL.md has malformed YAML frontmatter
- **THEN** validation fails with YAML parse error

### Requirement: System validates skill name format
The system SHALL validate that skill names follow lowercase alphanumeric format with single hyphens.

#### Scenario: Valid name passes
- **WHEN** a skill name is 1-64 characters of lowercase alphanumeric with single hyphens
- **THEN** validation succeeds

#### Scenario: Uppercase letters rejected
- **WHEN** a skill name contains uppercase letters
- **THEN** validation fails with naming convention error

#### Scenario: Spaces rejected
- **WHEN** a skill name contains spaces
- **THEN** validation fails with naming convention error

#### Scenario: Consecutive hyphens rejected
- **WHEN** a skill name contains consecutive hyphens
- **THEN** validation fails with naming convention error

#### Scenario: Empty name rejected
- **WHEN** a skill name is empty or missing
- **THEN** validation fails with error

#### Scenario: Too long name rejected
- **WHEN** a skill name exceeds 64 characters
- **THEN** validation fails with length error

### Requirement: System detects name/directory mismatch
The system SHALL validate that the skill name in frontmatter matches the directory name.

#### Scenario: Mismatch detected
- **WHEN** the frontmatter name differs from the containing directory name
- **THEN** validation warns about the mismatch

#### Scenario: Exact match passes
- **WHEN** frontmatter name exactly matches directory name
- **THEN** validation succeeds without warnings

### Requirement: System supports batch validation
The system SHALL validate multiple skills in a single command.

#### Scenario: All skills validated
- **WHEN** user runs `quiv validate` in a directory with multiple skills
- **THEN** all skills are validated and results are reported

#### Scenario: Individual skill validation
- **WHEN** user runs `quiv validate <skill-name>`
- **THEN** only that skill is validated

### Requirement: System reports validation errors clearly
The system SHALL provide clear error messages for validation failures.

#### Scenario: Errors show location
- **WHEN** validation fails
- **THEN** the error message includes the file path and line/column if applicable

#### Scenario: Multiple errors shown
- **WHEN** multiple validation errors exist
- **THEN** all errors are displayed with context for each
