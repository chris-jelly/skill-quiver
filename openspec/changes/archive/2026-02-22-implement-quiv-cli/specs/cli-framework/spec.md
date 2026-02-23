## ADDED Requirements

### Requirement: CLI provides entry point command
The system SHALL provide a `quiv` command-line entry point that is discoverable and executable after package installation.

#### Scenario: Entry point is available after installation
- **WHEN** user installs the package via pipx or pip
- **THEN** the `quiv` command is available in the system PATH

#### Scenario: Entry point shows help with no arguments
- **WHEN** user runs `quiv` without any arguments
- **THEN** the system displays help text showing available commands

### Requirement: CLI supports version flag
The system SHALL display the current version when the `--version` flag is provided.

#### Scenario: Version flag displays version
- **WHEN** user runs `quiv --version`
- **THEN** the system outputs the installed version number

### Requirement: CLI supports directory override
The system SHALL support a `--dir` flag to specify a working directory other than the current working directory.

#### Scenario: Directory override changes working directory
- **WHEN** user runs `quiv --dir /path/to/skills <command>`
- **THEN** the system operates in `/path/to/skills` instead of CWD

#### Scenario: Missing directory shows error
- **WHEN** user provides a non-existent directory path with `--dir`
- **THEN** the system displays an error message and exits with non-zero code

### Requirement: CLI discovers manifest in CWD
The system SHALL discover `skills.kdl` manifest files in the current working directory by default.

#### Scenario: Manifest discovered in current directory
- **WHEN** user runs a `quiv` command from a directory containing `skills.kdl`
- **THEN** the system uses that manifest file for operations

#### Scenario: Missing manifest shows helpful error
- **WHEN** user runs a command requiring a manifest and no `skills.kdl` exists
- **THEN** the system displays an error message suggesting to run `quiv init`

### Requirement: CLI provides command dispatch
The system SHALL dispatch to appropriate command handlers based on the provided subcommand.

#### Scenario: Unknown command shows error
- **WHEN** user runs `quiv unknowncommand`
- **THEN** the system displays an error message listing available commands

#### Scenario: Command-specific help is available
- **WHEN** user runs `quiv <command> --help`
- **THEN** the system displays help specific to that command including available flags and arguments
