# Cycle 2 - Independent live re-verification

Note: produced by lex-verification (Read/Grep/Glob/Bash, no Write tool); the
main session persisted it verbatim to this path.

## VERDICT: PASS

**run_mode:** `live` -- confirmed as the literal value in
`tests/live_status.json`, timestamp 2026-08-17T20:48:17Z, matching this
agent's own re-run (not merely read from the programmer's evidence file).

**Live suite (re-run independently):** `14 passed, 1 skipped` -- matches the
programmer's claim exactly. The skip is the documented
`ReversalIndex::test_create_duplicate_guid_falls_back_without_raising`, which
needs 2 free analysis writing systems while the Target sandbox has only 1. It
is not a hidden failure.

**Regression (re-run independently):** `1 failed, 294 passed` -- matches the
claim. The failure is
`test_lexsense_operations.py::TestGetComplexFormsNotSubentries::test_uses_kclassid_not_type_for_ownerofclass`
(FileNotFoundError against a sibling repo path), untouched by this diff --
confirmed no changed file in `git status --short` relates to LexSense.

**Re-query check:** confirmed via Grep on the test file that
`_reread_by_guid(project, guid)` (line 40) calls `project.Object(guid_str)` --
a fresh LCM lookup by GUID string, independent of the object handle `Create()`
returned. All three type tests assert
`str(reread.Guid).lower() == requested.lower()` against this fresh fetch, not
against the input. No self-referential assertion found.

**Signatures, verified directly in source rather than from the report:**

- `AgentOperations.Create(self, name, wsHandle=None, guid=None)`
- `ReversalIndexOperations.Create(self, name, writing_system, guid=None)`
- `ReversalIndexEntryOperations.Create(self, index_or_hvo, form, sense=None, wsHandle=None, guid=None)`

All trailing positional-with-default -- old positional call sites unaffected.

**Duplicate() untouched:** `git diff HEAD -- flexicon/code/Lists/AgentOperations.py`
shows a single hunk, entirely inside `Create()` (signature, docstring, and
`factory.Create()` -> `self._CreateWithGuid(...)`). No `Duplicate` hunk
present.

## Discrepancies

None found between the programmer's claim and what was independently
reproduced.

Note for whoever finalizes: the changes are currently uncommitted working-tree
modifications, not yet in a commit. That is not a verification defect, just a
state fact.

## Files

- `specs\236-guid-create-agent-reversals\evidence\live-cycle2-guid-create.md`
- `tests\operations\test_guid_create_agent_reversals_live.py`
- `tests\live_status.json`

Verified By: lex-verification, cycle 2
