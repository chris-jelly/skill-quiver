## REMOVED Requirements

### Requirement: System validates SKILL.md frontmatter
**Reason**: Validation is removed from quiv entirely. Skills are validated by their upstream authors and by `npx skills` at install time. The curation tool does not need to duplicate this responsibility.
**Migration**: Use `npx skills add --list <repo>` to verify skill structure. Rely on upstream CI for validation.

### Requirement: System validates skill name format
**Reason**: Removed along with the validation capability.
**Migration**: Name format is enforced by upstream skill authors and the `npx skills` CLI.

### Requirement: System detects name/directory mismatch
**Reason**: Removed along with the validation capability.
**Migration**: No replacement needed. Upstream repos own their skill naming.

### Requirement: System supports batch validation
**Reason**: Removed along with the validation capability.
**Migration**: No replacement needed.

### Requirement: System reports validation errors clearly
**Reason**: Removed along with the validation capability.
**Migration**: No replacement needed.
