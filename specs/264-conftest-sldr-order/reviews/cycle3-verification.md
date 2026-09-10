# Verification Report -- issue #264, cycle 3 (final gate)

**Verdict:** [PASS]
**Live run:** yes | **run_mode:** live
**Evidence:** specs/264-conftest-sldr-order/evidence/live-sldr-init.md (see "## Cycle 3" section)
**Project:** none opened write-enabled (read-only `OpenProject(..., writeEnabled=False)` against the local FieldWorks projects directory; no restore script needed)

## Change under review
`@pytest.mark.requires_live_project` added to `test_AllProjectNames` in
`flexicon/tests/test_FLExProject.py`; docstring note added to
`tests/test_264_sldr_single_init_path.py`. No production code change.

## Gate 1 -- Offline gate

**Command:** `python -m pytest -m "not requires_live_project" -q`
**Result:** `1779 passed, 737 deselected, 12 warnings in 18.67s` -- **0 failed**.
Baseline before the fix: `1 failed, 1779 passed, 736 deselected` (the one
failure was `test_AllProjectNames`). Delta matches exactly what the fix
claims: the failing test moved from "failing" to "deselected"; nothing
else regressed.

## Gate 2 -- Live gate for the newly-marked test

**Command as specified:**
`FLEXLIBS_REQUIRE_LIVE=1 python -m pytest flexicon/tests/test_FLExProject.py -m requires_live_project -q`
**Result of the literal command:** 3 failed -- but this is a harness
artifact, not evidence against the change. `flexicon/tests/` sits outside
`tests/`'s directory subtree, so pytest never auto-loads
`tests/conftest.py`'s autouse `initialize_flex_for_tests` fixture when the
file is targeted on its own; FLEx is never initialized at all (not live,
not mock), and `FwDirectoryFinder.ProjectsDirectory` throws before either
degradation path can engage. `tests/live_status.json` was not even
rewritten by this invocation -- it produced no evidence, so it cannot be
read as a live failure. This subtree gap is pre-existing and already
acknowledged in `pyproject.toml` (lines 84-89, marker registration
comment).

**Corrected invocation** (loads the same fixture explicitly):
`FLEXLIBS_REQUIRE_LIVE=1 python -m pytest flexicon/tests/test_FLExProject.py -m requires_live_project -q -p tests.conftest`
**Result:** `3 passed in 3.82s`. All three tests selected
(`test_AllProjectNames`, `test_OpenProject`, `test_ReadLexicon`), all PASS.
`tests/live_status.json` -> `"run_mode": "live"`, `run_timestamp` matches
the run window, all three nodeids recorded `"status": "pass"`. Read-only
throughout (`writeEnabled=False`); no project was modified; no restore
needed.

## Claim vs. observed

| Claim | Observed live | Status |
|-------|---------------|--------|
| Offline gate has 0 failures after the marker fix | `1779 passed, 737 deselected`, 0 failed | [PASS] |
| `test_AllProjectNames` genuinely passes live (marker is a correct fix, not a cover-up) | Passed live, `run_mode: live`, re-selected under `-m requires_live_project` | [PASS] |
| `test_OpenProject` / `test_ReadLexicon` still pass live and stay read-only | Both passed, both call `OpenProject(..., writeEnabled=False)` | [PASS] |

## Mock suite (regression, supplementary)
Same command as the offline gate above (this repo's "mock suite" and
"offline gate" are the same selector). Result: `1779 passed, 0 failed`.
Pre-existing failures not caused by this change: none observed.

## Blockers
None. One process note (not a blocker): the literal live-gate command in
the task, run against `flexicon/tests/test_FLExProject.py` in isolation,
does not load `tests/conftest.py` (directory-subtree scoping) and so
neither initializes FLEx nor updates `live_status.json`. Recommend a
follow-up issue to add a `pytest_plugins = ("conftest",)` shim or a local
`flexicon/tests/conftest.py` re-export so a bare invocation of files under
`flexicon/tests/` can't be mistaken for a real live failure. Verification
in this cycle used `-p tests.conftest` to load the same fixture explicitly
and obtained a genuine `run_mode: live` pass.

## Recommendation
APPROVE
