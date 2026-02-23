## ADDED Requirements

### Requirement: System parses KDL manifest files
The system SHALL parse KDL format manifest files named `skills.kdl` that define external skill sources.

#### Scenario: Valid KDL file parses successfully
- **WHEN** a well-formed `skills.kdl` file exists in the working directory
- **THEN** the system parses it without errors and extracts structured source data

#### Scenario: Invalid KDL syntax shows error
- **WHEN** a `skills.kdl` file contains invalid KDL syntax
- **THEN** the system displays a parse error with line number and context

### Requirement: System validates required manifest fields
The system SHALL validate that all required fields are present in each source definition.

#### Scenario: Missing required field shows validation error
- **WHEN** a source definition lacks a required field (e.g., `name`, `repo`, `source`)
- **THEN** the system displays a validation error identifying the missing field

#### Scenario: Complete source definition validates successfully
- **WHEN** all required fields are present in a source definition
- **THEN** the system accepts the definition for further processing

### Requirement: System extracts structured source data
The system SHALL extract source definitions into a structured format for use by other commands.

#### Scenario: Multiple sources extracted
- **WHEN** the manifest contains multiple `source` blocks
- **THEN** the system extracts each as a separate structured object with all properties

#### Scenario: Source properties parsed correctly
- **WHEN** a source has properties like `name`, `repo`, `source`, `license`, `filter`
- **THEN** each property is correctly typed and accessible in the structured data

### Requirement: System supports optional manifest fields
The system SHALL handle optional fields gracefully, using sensible defaults when not provided.

#### Scenario: Optional license field defaults to null
- **WHEN** a source definition lacks a `license` field
- **THEN** the system treats the license as unspecified

#### Scenario: Optional filter field defaults to include all
- **WHEN** a source definition lacks a `filter` field
- **THEN** the system includes all skills from the source

### Requirement: System validates source name format
The system SHALL validate that source names follow kebab-case naming conventions.

#### Scenario: Invalid source name shows error
- **WHEN** a source name contains spaces, uppercase letters, or special characters
- **THEN** the system displays a validation error with the expected format

#### Scenario: Valid kebab-case name accepted
- **WHEN** a source name uses only lowercase alphanumeric characters and single hyphens
- **THEN** the system accepts the name as valid
