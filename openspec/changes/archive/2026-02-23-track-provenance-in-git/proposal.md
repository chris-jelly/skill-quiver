## Why

Provenance files (`.source.kdl`) are gitignored, so when skills are committed to a repo, the pinned SHA, origin, and license information is lost. The `THIRD_PARTY_LICENSES` file also doesn't list which skills belong to each source, making it impossible to know which license covers a given skill directory without re-running `quiv sync` and inspecting the local-only provenance files.

## What Changes

- Stop gitignoring `.source.kdl` files so provenance is tracked in version control alongside skills
- Update the `quiv init` gitignore template to remove the `.source.kdl` exclusion
- Add a `Skills:` section to each source entry in `THIRD_PARTY_LICENSES`, listing the skills covered by that source's license
- Update `generate_license_file` to include skill names as a bullet list per source

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `provenance-tracking`: `.source.kdl` files are no longer gitignored; they are committed alongside skill directories as the per-skill source of truth for origin, version, and license
- `license-tracking`: `THIRD_PARTY_LICENSES` now includes a skills list per source, showing which skills fall under each license

## Impact

- `src/skill_quiver/init.py`: Gitignore template changes (remove `.source.kdl` exclusion)
- `src/skill_quiver/sync.py`: `generate_license_file` updated to include skill names
- Tests for both init and license generation will need updating
- Existing users who run `quiv init` on a new project will get the updated gitignore; existing projects will need to manually un-ignore `.source.kdl` files
