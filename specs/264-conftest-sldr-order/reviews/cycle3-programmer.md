# Cycle 3 -- Programmer report (issue #264)

## Diff summary

### Edit 1 (the blocker) -- `flexicon/tests/test_FLExProject.py`
Added `@pytest.mark.requires_live_project` to `test_AllProjectNames`
(now at line ~28-33), with a 3-line comment above it matching the voice
of the two existing sibling comments (`test_OpenProject` at ~36-42,
`test_ReadLexicon` at ~55-60): it explains that `AllProjectNames()`
reads the FieldWorks projects directory via
`FwDirectoryFinder.ProjectsDirectory` and therefore needs a real
FieldWorks install, and cites issue #264. No other lines in the file
were touched.

```python
    # AllProjectNames() reads the FieldWorks projects directory via
    # FwDirectoryFinder.ProjectsDirectory, which needs a real FieldWorks
    # install (see the offline-selector rationale above). issue #264.
    @pytest.mark.requires_live_project
    def test_AllProjectNames(self):
        """Test that AllProjectNames returns a list."""
        self.assertIsInstance(AllProjectNames(), list)
```

### Edit 2 (the P2) -- `tests/test_264_sldr_single_init_path.py`
Added a "Known limitation" paragraph to the module-level `#`-style
header block (this file uses the project's comment-header convention
in place of a triple-quoted module docstring; there was no `"""..."""`
module docstring to edit). Inserted between the existing "Modeled on
..." paragraph and the "Platform:" line. Plain ASCII, no emoji. Content:

- `_has_requires_live_project_marker` (lines 226-243, unchanged) checks
  for the marker at FILE level -- a module-level `pytestmark` or a
  decorator on any function/class in the file -- not per test function,
  so a file whose siblings carry the marker passes even if one
  individual live-touching test in it does not.
- `_calls_live_project_api` (lines 186-197, unchanged) recognizes only
  calls named `OpenProject` or `FLExInitialize`, so other live-state
  entry points such as `AllProjectNames` (which reads
  `FwDirectoryFinder.ProjectsDirectory`) are not detected.
- Both are noted explicitly as tracked follow-ups, not fixed here.

No logic in the ratchet (lines 26-onward) was touched; the recognized
call-name set and `_ALLOWED_PATHS` are untouched, as instructed.

`tests/contract/expected_contract.json` was not touched.

## Commands run

### 1. `python -m pytest flexicon/tests/test_FLExProject.py -m "not requires_live_project" -q`
```
3 deselected in 0.91s
```
(Exit code 5 -- "no tests collected" -- because this file contains
exactly 3 tests and all 3 now correctly carry
`requires_live_project`, so the offline selector deselects the whole
file. This is the expected/correct post-fix state, not a failure: the
blocker was `test_AllProjectNames` running unmarked and crashing under
`-m "not requires_live_project"`; now nothing in this file runs
offline at all.)

### 2. `python -m pytest tests/test_264_sldr_single_init_path.py -q`
```
..                                                                       [100%]
[OK] Wrote D:\Github\_Projects\_LEX\flexicon\tests\test_results.json (2 tests recorded)

2 passed in 2.91s
```

### 3. `python -m pytest -m "not requires_live_project" -q`
```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1779 passed, 737 deselected, 12 warnings in 17.31s
```

## Pass/fail line

PASS -- 0 failed. Full offline selector: 1779 passed, 737 deselected
(matches the expected ~1779 passed / ~737 deselected). The
previously-failing `test_AllProjectNames` no longer runs offline; the
#264 ratchet test passes 2/2; no other test was touched or regressed.
No commit was made per instructions.
