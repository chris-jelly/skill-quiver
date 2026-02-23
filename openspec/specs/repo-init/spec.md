## ADDED Requirements

### Requirement: System creates manifest file
The system SHALL create a `skills.kdl` file with a commented example source block when initializing a repository.

#### Scenario: Manifest created in target directory
- **WHEN** user runs `quiv init`
- **THEN** a `skills.kdl` file is created in the working directory containing a commented example source block

#### Scenario: Manifest created with --dir flag
- **WHEN** user runs `quiv init --dir <path>`
- **THEN** a `skills.kdl` file is created in the specified directory

### Requirement: System creates skills directory
The system SHALL create a `skills/` directory with a `.gitkeep` file when initializing a repository.

#### Scenario: Skills directory created
- **WHEN** user runs `quiv init`
- **THEN** a `skills/` directory is created with a `.gitkeep` file inside it

### Requirement: System rejects already-initialized directory
The system SHALL error when `skills.kdl` already exists in the target directory.

#### Scenario: Already initialized error
- **WHEN** user runs `quiv init` in a directory that already contains `skills.kdl`
- **THEN** the system displays "Already initialized (skills.kdl exists)" and exits with an error

### Requirement: System creates target directory for --dir
The system SHALL create the target directory if it does not exist when `--dir` is specified with `init`.

#### Scenario: Non-existent --dir directory created
- **WHEN** user runs `quiv init --dir new-project` and `new-project/` does not exist
- **THEN** the system creates `new-project/` and initializes the repository inside it

### Requirement: Init takes no positional arguments
The `quiv init` command SHALL accept no positional arguments. It operates on the current working directory or the directory specified by `--dir`.

#### Scenario: No arguments required
- **WHEN** user runs `quiv init` with no arguments
- **THEN** the system initializes the repository in the current working directory

#### Scenario: Positional argument rejected
- **WHEN** user runs `quiv init some-name`
- **THEN** the CLI parser rejects the command with a usage error

### Requirement: System prints summary of created files
The system SHALL print a summary of what was created after successful initialization.

#### Scenario: Creation summary displayed
- **WHEN** initialization completes successfully
- **THEN** the system prints the list of files and directories that were created
