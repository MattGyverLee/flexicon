# Live evidence -- #352 ScrDraft face (Description scalar + factory)

**Date:** 2026-09-21
**Projects:** Tlachichilco Tepehua-NT orthography (has Scripture; found by
scanning installed `.fwdata` for `<Scripture`). Read path opens read-only;
write path creates one `TEST_352` draft with finally-cleanup and a
zero-residue assertion. Target has no Scripture (`TranslatedScriptureOA`
is None) so it cannot host this verification.
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_352_scrdraft_live.py -m requires_live_project -q
```

## Pre-fix live facts

- Real draft: `Description` pytype=`str` (`'Last Standard Format Import'`),
  `hasattr(get_String)`=False -- scalar String (snapshot 20171 confirmed).
- `IScrDraftFactory` exposes no no-arg `Create()` (TypeError); live stack
  shows `ScrDraftFactory.Create(String description)` -- the String is the
  description, and the factory parents the draft into `ArchivedDraftsOC`
  itself. The old `factory.Create()` + `set_String` + manual Add never
  worked (triple-broken Create).
- `FLExProject` had no `ScrDrafts` accessor at all (the ops class was
  orphaned); wired following the house lazy-import pattern + `.pyi` stub.
- Housekeeping finding: committing a per-operation UnitOfWork headless
  crashes in `SendPropChangedNotifications` (no ISynchronizeInvoke), so
  the writable fixture opens with `undoable=False` like the house
  fixtures (session envelope commits).

## Fix (`flexicon/code/Scripture/ScrDraftOperations.py`, `FLExProject.py`)

- `Create`: `factory.Create(description)` + HVO-membership-guarded Add +
  direct scalar `Description` assignment. The `type` label param stays
  accepted-but-unapplied (ScrDraftType enum not exposed via pythonnet;
  documented).
- `Find`/`GetDescription`/`SetDescription`: direct scalar read/assign,
  no WS dimension. Dead `ITsString`/`TsStringUtils` imports removed.

## Post-fix values read back from the LCM

- Real draft reads back verbatim; `Find` hits/misses correctly.
- `Create("TEST_352 draft")` -> read-back equals; `SetDescription`
  relabels; `Delete` removes; draft HVO set identical before/after
  (zero residue).

## Pass/fail

**PASS.** `2 passed` on the command above, live run_mode.
Related suite `test_flexproject_discoverability.py`: 12 passed.
