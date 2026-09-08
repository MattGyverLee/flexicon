# Cycle 3 — Programmer report (#285 final P1)

## Edit (docs/FLEXTOOLSMCP_WRITE_CONTRACT.md:313-317, one bullet)

**Before:**
```
- `FLExProject.OpenProject(self, projectName, writeEnabled=False,
  undoable=False, ui=None)` (`FLExProject.py:164`), passing `ui` straight
  through to `FLExLCM.OpenProject(projectName, ui)`. `ui=None` (the default,
  unchanged for backward compatibility) still constructs `FwLcmUI` — verified
  by monkeypatch test and by the verification agent reading `FLExLCM.py:98-99`.
```

**After (13 lines appended, nothing deleted):** same four lines kept
verbatim, followed by:
```
  **SUPERSEDED (issue #285, 2026-09-08): both claims in this bullet are
  historical, not current.** `ui=None` now resolves to a bare
  `HeadlessLcmUI()` — `FLExLCM.py:98-99` reads `ui = HeadlessLcmUI()`, not
  `FwLcmUI(...)`; the historical `FwLcmUI` path is reachable only by passing
  `ui=FwLcmUI(None, ThreadHelper())` explicitly. The monkeypatch test cited
  above was inverted and renamed
  (`tests/test_headless_lcm_ui.py::TestOpenProjectDefaultUi::
  test_flexlcm_openproject_defaults_to_headlesslcmui`) and now asserts the
  opposite of what this bullet says. Likewise the `undoable=False` shown in
  the signature above is the *4.3.0* default quoted at the time this bullet
  was written; the real default has been `undoable=True` since 4.4.0 (see
  "DEF" in the task table below). See the CHANGELOG `[Unreleased]` #285 entry
  for the current behaviour of both.
```
Follows the `4526245` convention: stale text kept + marked historical, not
rewritten. Section's other `FwLcmUI`/`ui=None` mentions checked (grep) — line
246's `ui-injection` row was already fixed in `4526245`; no other stale claim
found in the rest of the file.

## Out-of-scope confirmation
`git diff --stat`: `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md | 13 +++++++` only
(one file changed, 13 insertions, 0 deletions). Grep confirms
`specs/write-path-transactions/{spec.md:426, tasks.md:14,20,
reviews/cycle1-programmer-trackA.md:42}` still read the original
"constructs FwLcmUI" wording — untouched. `build/` untouched.

## Suite
`python -m pytest -m "not requires_live_project" -q`:
**1728 passed, 0 failed, 693 deselected**, 8 warnings, 5 subtests passed —
matches the expected/pre-change tallies exactly.

## Commit
`b61aa8ad434671e9933aa5e82ab36bca9b77788d` on `fix/285-headless-ui-default`
(verified via `git branch --show-current` before committing).
