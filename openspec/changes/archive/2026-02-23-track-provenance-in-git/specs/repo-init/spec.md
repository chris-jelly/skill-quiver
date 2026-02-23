## REMOVED Requirements

### Requirement: System configures gitignore
**Reason**: The only gitignore entry was `skills/**/.source.kdl` to exclude provenance files. Now that provenance files are version-controlled, there are no quiv-specific gitignore entries needed.
**Migration**: Users with existing repos should manually remove the `skills/**/.source.kdl` line and the `# quiv - provenance tracking files are machine-generated` marker from their `.gitignore`.
