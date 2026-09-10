# Cycle 1 - Programmer report: issue #264

## Files changed

- `tests/conftest.py:114-135` - removed `from SIL.WritingSystems import Sldr`
  (now unused) and the bare `Sldr.Initialize(True)` call. Left a comment
  citing #264 stating SLDR init is owned solely by `FLExInitialize()`'s
  `IsInitialized`-guarded path. Kept the `FwRegistryHelper.Initialize()` /
  `FwUtils.InitializeIcu()` block and its faulthandler disable/enable pair
  (#35) untouched; ICU-before-init ordering preserved.
- `flexicon/sync/tests/test_base_operations.py:1-19` - added `import pytest`
  and `pytestmark = pytest.mark.requires_live_project`, with a comment
  mirroring `test_duplicate_operations.py:31-38`, citing #264.
- `tests/test_264_sldr_single_init_path.py` (new) - regression test, two
  classes: (1) AST ratchet asserting no executable `Sldr.Initialize(...)`
  call exists outside `flexicon/code/FLExInit.py` (modeled on
  `test_flexlibs2_alias_ratchet.py`, immune to the string appearing in
  comments/docstrings); (2) asserts every `flexicon/sync/tests/test_*.py`
  module calling `OpenProject(` carries the `requires_live_project` marker.
- `tests/test_flexlibs2_alias_ratchet.py` - added the new test file to
  `_PY_PROSE_ALLOWED`; its docstring names `test_flexlibs2_alias_ratchet.py`
  by filename as the pattern it models, which the flexlibs2 ratchet itself
  flagged.
- `CHANGELOG.md` - new `[Unreleased] / Fixed` entry, house style matching
  the #249 entry.
- `docs/API_ISSUES_CATEGORIZED.md` - added a "Corollary" subsection under
  Category 12 stating there is exactly one `Sldr.Initialize()` call site.
- `docs/EXCEPTION_HANDLING.md` - added a matching short note after the
  #179/#249 "`.ldml.bad`" section, cross-referencing both the doc corollary
  and the new ratchet test.

## Item 3 decision (no new helper)

**Decision: no new guard/idempotence helper.** `FLExInitialize()` already
is the single guarded SLDR-init path (the #249 fix). Adding a second helper
"for symmetry" would only create a second seam that has to be kept in sync
with the first -- exactly the class of bug #264 itself is. The corollary is
recorded as documentation (API_ISSUES_CATEGORIZED.md, EXCEPTION_HANDLING.md)
plus a static ratchet, not new production code. If a future caller needs
guarded init outside `FLExInit.py`, the correct move is to call
`FLExInitialize()`, not to duplicate its guard.

## Verification

Command: `python -m pytest -m "not requires_live_project" -q`
Result after fix: **1784 passed, 732 deselected**, 0 failed.

Pre-fix check (stashed only `tests/conftest.py` and
`flexicon/sync/tests/test_base_operations.py`, ran the new file alone):
both new test classes in `tests/test_264_sldr_single_init_path.py` FAILED
as expected (`Sldr.Initialize` found at the old `tests/conftest.py:135`;
`test_base_operations.py` missing the marker). Stash was popped immediately
after, tree confirmed clean via `git status --short` before/after.

## Not done / out of scope

- `flexicon/tests/test_FLExProject.py` also calls `OpenProject()` with no
  `requires_live_project` marker at all (no marker of any kind, not even a
  wrong one). This is outside `flexicon/sync/tests/`, was not named in the
  issue or in Task 2/4's instructions (which scope explicitly to "sync test
  modules"), and fixing it would risk masking a currently-passing offline
  run if that file depends on the session fixture in ways I have not
  audited. Flagging for a follow-up issue rather than silently expanding
  scope.
- Working tree left dirty per instructions; no commit made.
