# Cycle 2 - Programmer report: guid-preserving Create() (#236)

Implemented exactly per the APPROVED cycle-1 reviews; no design changes.

## Files changed

- `flexicon/code/Lists/AgentOperations.py:115-181` — `Create()` signature and
  body; `factory.Create()` → `self._CreateWithGuid(factory, guid, "ICmAgent")`
  at line ~173. `Duplicate()` untouched.
- `flexicon/code/Reversal/ReversalIndexOperations.py:111-194` — `Create()`
  signature and body; `factory.Create()` →
  `self._CreateWithGuid(factory, guid, "IReversalIndex")` at line ~185. The
  `FindByWritingSystem` duplicate-WS check (now ~178-180) stays before any
  mutation and before `_CreateWithGuid`, unchanged in position/behaviour.
- `flexicon/code/Reversal/ReversalIndexEntryOperations.py:131-215` —
  `Create()` signature and body; `factory.Create()` →
  `self._CreateWithGuid(factory, guid, "IReversalIndexEntry")` at line ~208;
  `index.EntriesOC.Add(new_entry)` kept immediately after.
- `tests/operations/test_guid_create_agent_reversals_live.py` (new) — live
  coverage, all 3 types.
- `specs/236-guid-create-agent-reversals/evidence/live-cycle2-guid-create.md`
  (new).

## Final signatures

```python
AgentOperations.Create(self, name, wsHandle=None, guid=None)
ReversalIndexOperations.Create(self, name, writing_system, guid=None)
ReversalIndexEntryOperations.Create(self, index_or_hvo, form, sense=None, wsHandle=None, guid=None)
```

All trailing positional-with-default, not keyword-only, matching all 8
existing `_CreateWithGuid` callers.

## Live run

`run_mode: "live"` (`tests/live_status.json`).
`test_guid_create_agent_reversals_live.py -m requires_live_project`:
**14 passed, 1 skipped**. The skip is
`ReversalIndex::test_create_duplicate_guid_falls_back_without_raising` —
Target currently has only 1 free analysis WS (`en`) without a reversal
index, but that test needs 2 (each index needs its own WS). Reported per
brief rather than deleting an existing index. Offline regression
(`tests/operations -m "not requires_live_project"`): 294 passed, 1
pre-existing failure (`test_lexsense_operations.py`, `FileNotFoundError`
against a sibling repo path) — reproduced identically with `git stash`
applied, confirming it predates this change.

Pre/post GUID read-back (via `FLExProject.Object(guid)`, not the returned
handle) confirmed for all three types; duplicate-GUID fallback observed live
for `ICmAgent` with the actual warning log captured. Full detail in the
evidence file.

## Deviations

1. `ReversalIndexEntryOperations` live tests pass `wsHandle=` explicitly to
   `Create()` rather than relying on the index to resolve its own writing
   system. Root cause: `ReversalIndexOperations.Create()` stores
   `str(writing_system)` verbatim — when a caller passes an int handle (the
   pattern shown in that method's own docstring example), the string stored
   is the stringified int, not an ICU tag, so
   `ReversalIndexEntryOperations.Create()`'s `WSHandle(index.WritingSystem)`
   fallback fails to resolve and raises `ArgumentNullException` deep in
   `TsStringUtils.MakeString`. This is a **pre-existing bug unrelated to
   #236's guid= addition** (reproduces identically with `guid=None`) and is
   out of this task's scope; not fixed here. Flagged for a follow-up issue.
2. Evidence-gathering used a standalone ad-hoc script (not committed) rather
   than pytest `-s` output, to get clean pre/post GUID values including the
   live fallback warning text; the pytest suite itself is the authoritative
   pass/fail record.
