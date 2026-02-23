## 1. Remove gitignore configuration from init

- [x] 1.1 Remove `GITIGNORE_MARKER` and `GITIGNORE_ENTRIES` constants from `src/skill_quiver/init.py`
- [x] 1.2 Remove `_configure_gitignore()` function from `src/skill_quiver/init.py`
- [x] 1.3 Remove `_configure_gitignore(target)` call from `init_repo()`
- [x] 1.4 Update `init_repo()` docstring to no longer mention `.gitignore`
- [x] 1.5 Remove `.gitignore` from the `created` summary list in `init_repo()`
- [x] 1.6 Update tests in `tests/test_init.py`: remove `test_gitignore_created_when_none_exists`, `test_gitignore_appended_when_exists`, `test_gitignore_not_duplicated`
- [x] 1.7 Update `test_successful_repo_init` to assert `.gitignore` is NOT created
- [x] 1.8 Remove `GITIGNORE_MARKER` from the import in `tests/test_init.py`

## 2. Add skills list to THIRD_PARTY_LICENSES

- [x] 2.1 Update `generate_license_file()` in `src/skill_quiver/sync.py` to append a `Skills:` heading and indented bullet list (`  - skill-name`) for each source, with skills sorted alphabetically
- [x] 2.2 Update `test_generation` in `tests/test_sync.py` to assert skills appear in the license file output (the `_make_source` helper already provides `skills: ["my-skill"]`)
- [x] 2.3 Add test for multiple skills listed per source: create a source with several skills and assert they appear as indented bullets in alphabetical order
- [x] 2.4 Update `test_alphabetical_ordering` if needed to verify skills appear within each source section

## 3. Verify

- [x] 3.1 Run full test suite and confirm all tests pass
