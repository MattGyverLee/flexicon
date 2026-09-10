# Cycle 2 QC Review -- Issue #264

**Verdict:** Confirmed clean. The conftest.py fix, markers, and ratchet are sound
and well-scoped. One P1 gap identified; no P0s.

Note: this agent had no Write/Bash tool available in its session, so this file
was transcribed by the coordinator from the agent's direct report rather than
written by the QC agent itself. Content is verbatim from that report.

## P0

None.

## P1

1. `flexicon/tests/test_FLExProject.py:28-30` -- `test_AllProjectNames` is
   unmarked but touches live `FwDirectoryFinder` state (per cycle-2's own
   finding). `tests/test_264_sldr_single_init_path.py:194-197`'s
   `_calls_live_project_api()` only recognizes `OpenProject`/`FLExInitialize`
   call names, so this call site is structurally invisible to the ratchet, and
   `_has_requires_live_project_marker` (`tests/test_264_sldr_single_init_path.py:226-243`)
   checks file-level marker presence, not per-function -- the file passes only
   because its two sibling methods carry the marker. This is exactly the #264
   bug class, left as an acknowledged gap rather than closed. Either mark
   `test_AllProjectNames` too, or file a tracked follow-up for the ratchet's
   per-function granularity limitation so it doesn't give false confidence on
   files with mixed marked/unmarked tests.

2. Cannot verify cycle-2's "environmental, pre-existing" characterization of
   the `test_AllProjectNames` `FwDirectoryFinder.ProjectsDirectory` failure by
   execution (no Bash/exec tool this session). Static evidence is consistent
   with it being pre-existing/out-of-scope (cycle1-audit.md never flagged this
   call site either), but this is not a confirmed live re-run.

## P2

- Same root cause as P1.1: document the file-level-vs-per-function
  marker-check limitation in `tests/test_264_sldr_single_init_path.py`'s
  module docstring for future maintainers.

## Everything else reviewed clean

- `tests/conftest.py:114-150` preserves `FwRegistryHelper.Initialize()` ->
  `FwUtils.InitializeIcu()` ordering, the #35 faulthandler disable/enable
  try/finally pair is intact, the unused `Sldr` import is fully gone (only
  comment references remain, confirmed via grep).
- The AST ratchet in `tests/test_264_sldr_single_init_path.py:70-99` correctly
  matches only executable `Call` nodes (verified against comments at
  conftest.py:134-142, which don't trigger it) and cycle-2's allowlist entries
  (`tests/test_264_sldr_single_init_path.py:150-171`) each carry a specific,
  checkable reason.
- Marker placement is correct: `test_pattern_writing_systems_enumeration.py:116-117`
  uses a class-level decorator (static scanner at lines 1-102 stays
  collectable), `flexicon/tests/test_FLExInit.py:20` and
  `flexicon/tests/test_FLExProject.py:39,53` correctly cite #264.
- No `flexlibs2` references outside the sanctioned prose comparisons already
  covered by the ratchet's own allowlist (`tests/test_flexlibs2_alias_ratchet.py:221-222`).
- CHANGELOG.md and docs (`API_ISSUES_CATEGORIZED.md:892-907`,
  `EXCEPTION_HANDLING.md:680-689`) entries match house style and
  cross-reference correctly.
- `tests/contract/snapshots/expected_contract.json` untouched by this diff, as
  instructed.
