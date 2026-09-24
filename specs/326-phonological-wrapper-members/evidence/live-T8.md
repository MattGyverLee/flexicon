# Live T8 Verification -- Issue #326: Phonological Wrapper Members (Final Tree)

**Task:** lex-verification, REQUIRED live LCM verification of the final tree
(T5 implement + T6 simplify). Worktree `C:/Github/flexicon-326`, branch
`fix/326-phonological-wrapper-members`. No production code changed. No
commit made. Two new evidence-only test files added (see below); no writes
performed against any project.

## Exact commands run

### 1. Offline suite (gate for non-write-path work)

```powershell
cd C:/Github/flexicon-326
python -m pytest -m "not requires_live_project" -q
```

**Result:** `5 failed, 2043 passed, 896 deselected, 17 warnings in 10.35s`

Full output: `specs/326-phonological-wrapper-members/evidence/T8-offline-output.txt`

The 5 failures are pre-existing and unrelated to #326 (identical to T5's and
T6's reported failures -- re-confirmed independently here, same test IDs):

1. `tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies`
2. `tests/contract/test_lcm_contract.py::TestLiveRegressionCheck::test_no_regressions_from_baseline`
3. `tests/operations/test_issue266_phoneme_ws_resolution.py::TestApplyBasicIPASymbolSharedIndexCache::test_fresh_index_cache_per_apply_call`
4. `tests/operations/test_issue267_translations_ws_resolution.py::TestTranslationsOCSharedIndexCache::test_fresh_index_cache_per_apply_call`
5. `tests/write_path_transactions/test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_no_new_unbracketed_mutations`

No new offline failures introduced by T5/T6 vs. the pre-existing baseline.

### 2. Live suite: T5's programmer smoke test (required invocation, re-run independently)

```powershell
cd C:/Github/flexicon-326
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_phonological_wrappers_live.py -m requires_live_project -q -s
```

**Result:** `3 passed in 23.69s`

Full output: `specs/326-phonological-wrapper-members/evidence/T8-live-output.txt`

### 3. Live suite: T8's own independent re-query (additional evidence, not a substitute for #2)

> [NOTE] 2026-09-23: `tests/operations/test_issue326_t8_verification_live.py`
> was T8 scratch and was intentionally never committed
> (`reviews/T11-archivist.md:55`, `reviews/T8-verification.md:25,55`), so the
> command below cannot be re-run from the repo. To re-verify #326, run the
> committed file from step 2, `tests/operations/test_phonological_wrappers_live.py`
> (context links + metathesis parts read back via the wrappers). It passed
> live on 2026-09-23 (3/3, `run_mode: live`); see
> `specs/issue-289-headless-progress/evidence/live-import-regression.md`.

```powershell
cd C:/Github/flexicon-326
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue326_t8_verification_live.py -m requires_live_project -q -s
```

**Result:** `2 passed in 23.66s`

Full output: `specs/326-phonological-wrapper-members/evidence/T8-requery-output.txt`

New file added: `tests/operations/test_issue326_t8_verification_live.py`
(evidence-only, `requires_live_project`, opens installed projects
`writeEnabled=False`, no factory calls, no `UndoableOperation`; not part of
production behaviour and not committed).

## LIVE GATE

`tests/live_status.json`, checked after the final run above:

```json
"run_mode": "live",
"run_timestamp": "2026-09-22T21:45:50Z",
"by_class": {
  "PhonologicalRuleOperations": {
    "read": { "status": "pass", "last_verified": "2026-09-22" }
  }
}
```

`run_mode == "live"` -- confirmed, not `"mock"`. FLEx initialized fully
(`FieldWorks 9.3.11.2703`, `SIL.LCModel` loaded, `FLExInitialize()`
completed, "Loaded 60/60 operations classes") for both live runs.

## Fixture note (Sena 3 unavailable)

Per T1's independent finding (`live-T1-reflection.md`): Sena 3's `.fwdata`
fails to open (`File is not a valid FieldWorks project file.` --
`XMLBackendProvider.ReadInSurrogate`), independent of this task; a
same-sized `.bak` sits alongside it. `sena3_sandbox` was not usable for the
same reason. Verification below therefore uses `target_sandbox` (proves the
session reaches a real, write-enabled LCM cache) plus **read-only** installed
FLEx projects for the actual assertions, per the task's explicit fallback
instruction ("if Sena 3 fixture is missing, say so and verify against Target
sandbox + read-only installed projects"). No writes were made to any
installed project. No `TEST_`-prefixed objects were created (no writes were
needed for a read-back verification).

## Pre-state (cite T1 -- old/invented properties)

From `live-T1-reflection.md`, confirmed by live CLR reflection and live
instance reads *before* T5's fix existed:

- `IPhSimpleContextSeg.SegmentRA` -- **does not exist**: `hasattr()` ->
  `False`; unguarded read raises
  `AttributeError: 'IPhSimpleContextSeg' object has no attribute 'SegmentRA'`.
- `IPhSimpleContextNC.NaturalClassRA` -- **does not exist**: `hasattr()` ->
  `False`; unguarded read raises
  `AttributeError: 'IPhSimpleContextNC' object has no attribute 'NaturalClassRA'`.
- `IPhMetathesisRule.LeftPartOfMetathesisOS` / `RightPartOfMetathesisOS` --
  **do not exist** on any of 4 live `PhMetathesisRule` instances checked
  (`has_LeftPartOfMetathesisOS` / `has_RightPartOfMetathesisOS` both `False`
  on all four).
- Net effect on the pre-fix wrapper code: `PhonologicalContext.segment`,
  `PhonologicalContext.natural_class`, and
  `PhonologicalRule.has_metathesis_parts`/`metathesis_parts` read these
  nonexistent members and (depending on guard style) either raised or
  degraded to `None`/empty collections on every live rule -- i.e. dead on
  arrival against this LCM build.

## Post-state -- RE-QUERIED from the LCM after read (not the value passed in)

Since this is a pure read-back verification (no write path), "re-querying"
means: call the wrapper property, take the live object it returns, and read
a *further* field off that returned object independently -- proving the
wrapper actually resolved a real link, not merely that it didn't crash.

### `PhonologicalContext.segment` / `.natural_class` (via `FeatureStructureRA`)

From T5's smoke test (`live-programmer-context-links.json`):

- `seg_class_name`: `"PhPhoneme"`
- `nc_class_name`: `"PhNCSegments"`

From T8's own independent re-query (`live-T8-context-link-names.json`,
project `Aweti`), reading `.Name` off the returned live objects via
`best_analysis_text()` (proper `IMultiUnicode` extraction, matching T1's
methodology):

- `seg_class_name`: `"PhPhoneme"`, `seg_name`: `""` (this particular live
  phoneme in `Aweti` has no Name text set -- a real data condition of that
  project, not a wrapper defect; the `ClassName` still confirms
  `FeatureStructureRA` resolved to a genuine `IPhPhoneme`, and `hasattr`
  raised no exception)
- `nc_class_name`: `"PhNCSegments"`, `nc_name`: `"C:A"` (a real,
  non-empty natural-class name read back from the live LCM)

Both `seg_found`/`nc_found` are `True`, and both come from a live object
returned by the wrapper, not a value supplied by the test -- the test never
constructs or passes in a phoneme/natural-class object.

### `PhonologicalRule.metathesis_parts` (via `StrucDescOS` + switch indices)

From T5's smoke test (`live-programmer-metathesis.json`, `left_count: 1`,
`right_count: 1`, `left_switch: [0,1]`, `right_switch: [1,2]`).

From T8's own independent re-query
(`live-T8-metathesis-part-contents.json`, project
`Tlachichilco Tepehua-NT Noparse`, which matches the four-row table in T1's
reflection exactly for `LeftSwitchIndex/Limit` and `RightSwitchIndex/Limit`):

```json
{
  "left_switch": [0, 1],
  "right_switch": [1, 2],
  "left_part_class_types": ["PhSimpleContextSeg"],
  "right_part_class_types": ["PhSimpleContextSeg"],
  "left_part_context_names": [""],
  "right_part_context_names": [""]
}
```

The sliced parts are re-wrapped `PhonologicalContext` objects of a genuine
concrete type (`PhSimpleContextSeg`), independently re-queried for
`class_type` and `Name` -- proving `metathesis_parts` actually slices real
`StrucDescOS` elements at the switch-index boundaries reported by the live
`IPhMetathesisRule` concrete object, rather than returning empty
placeholders. (The empty `Name` text is again a property of this project's
data, not of the wrapper; T1's reflection on the same project family found
no separate Name text set on these particular `PhSimpleContextSeg` slices
either -- consistent, not contradictory.)

## Pass/fail line

**PASS: live-verified.** `run_mode == "live"` for both the required T5
programmer smoke test and T8's independent re-query (not `"mock"`); the
offline suite shows no new failures beyond the 5 pre-existing ones (matches
T5 and T6 exactly); pre-state (T1) confirms the old `SegmentRA` /
`NaturalClassRA` / `LeftPartOfMetathesisOS` / `RightPartOfMetathesisOS`
members do not exist on live LCM instances; post-state confirms the new
`FeatureStructureRA`-based and `StrucDescOS`-slice-based implementations
resolve to real, independently re-queryable live objects
(`PhPhoneme`/`PhNCSegments` class names, a non-empty natural-class name
`"C:A"`, and correctly-typed `PhSimpleContextSeg` metathesis-part slices) on
real installed FLEx projects, with the Sena 3 gap explicitly disclosed and
covered by the sanctioned fallback (Target sandbox + read-only installed
projects). No writes were made to any project.
