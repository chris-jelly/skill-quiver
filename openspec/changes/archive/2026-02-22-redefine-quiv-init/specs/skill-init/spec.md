## REMOVED Requirements

### Requirement: System scaffolds skill directory
**Reason**: `quiv` manages collections of upstream skills, not skill authoring. Skill scaffolding does not align with the tool's purpose.
**Migration**: Use `quiv init` to initialize a skill-quiver repository instead. Individual skill directories are created by `quiv sync fetch` from upstream sources.

### Requirement: System creates template SKILL.md
**Reason**: Skill authoring is not a supported workflow. Skills are fetched from upstream repos.
**Migration**: No replacement needed. SKILL.md files come from upstream skill repositories.

### Requirement: System creates standard subdirectories
**Reason**: The scripts/, references/, and assets/ subdirectories were part of skill scaffolding which is being removed.
**Migration**: No replacement needed. Subdirectory structure comes from upstream skill repositories.

### Requirement: System validates skill name on init
**Reason**: The init command no longer takes a skill name. It initializes a repository, not a skill.
**Migration**: Name validation remains in other commands that accept skill names (e.g., validate, sync update).

### Requirement: System supports custom output path
**Reason**: The --output flag is removed since init no longer creates skill directories at arbitrary paths.
**Migration**: Use `--dir` to initialize a repository in a different directory.
