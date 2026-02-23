## MODIFIED Requirements

### Requirement: CLI provides command dispatch
The system SHALL dispatch to appropriate command handlers based on the provided subcommand. The available commands SHALL be `init` and `sync`.

#### Scenario: Unknown command shows error
- **WHEN** user runs `quiv unknowncommand`
- **THEN** the system displays an error message listing available commands

#### Scenario: Command-specific help is available
- **WHEN** user runs `quiv <command> --help`
- **THEN** the system displays help specific to that command including available flags and arguments

## REMOVED Requirements

### Requirement: CLI dispatches validate command
**Reason**: The `validate` command is removed. Skill validation is the responsibility of upstream repos and `npx skills` at install time, not the curation tool.
**Migration**: Remove `quiv validate` from any scripts or workflows. Use `npx skills` for install-time validation.

### Requirement: CLI dispatches package command
**Reason**: The `package` command is removed. The git repository itself is the distribution format — `npx skills add <repo>` consumes it directly. Zip archives have no consumer in the workflow.
**Migration**: Remove `quiv package` from any scripts or workflows. Point `npx skills add` at the repo directly.
