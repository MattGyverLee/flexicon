# Live T1 Reflection -- Issue #326: Phonological Wrapper Members

**Task:** lex-verification, live READ-ONLY reflection pass. No code changes made.
No project was opened writeEnabled=True; no writes occurred anywhere.

**Worktree:** `C:/Github/flexicon-326`, branch `fix/326-phonological-wrapper-members`.

## Exact commands run

```powershell
cd C:/Github/flexicon-326
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue326_phonological_reflection_live.py -m requires_live_project -q -s
```

A temporary, read-only-only verification test was added at
`tests/operations/test_issue326_phonological_reflection_live.py` (opens every
project with `writeEnabled=False`, no `UndoableOperation`, no factory calls)
purely to drive the live reflection through the standard `flex_plugin.py`
session fixture and produce a machine-checkable `run_mode` gate. It writes
its raw findings to
`specs/326-phonological-wrapper-members/evidence/raw-reflection-data.json`.

## LIVE GATE

`tests/live_status.json` (checked immediately after the run above):

```json
"run_mode": "live",
"by_class": {
  "PhonologicalRuleOperations": {
    "read": { "status": "pass", "last_verified": "2026-09-22" }
  }
}
```

`run_mode == "live"` -- confirmed. FLEx initialized fully (FieldWorks 9.3.11.2703,
`SIL.LCModel` loaded, `FLExInitialize()` completed) and the test ran against real
`.fwdata` projects, not mocks. Test result: **1 passed**.

## Scope of the scan

Reads are unrestricted (CLAUDE.md), so the test opened **89 installed
projects** read-only in a single pass (see full list in
`raw-reflection-data.json:read_candidates`), scanning `PhonologicalDataOA.PhonRulesOS`
and `PhonologicalDataOA.EnvironmentsOS[*].{Left,Right}ContextOA` in each.
30 of them had at least one phonological rule. **`Sena 3` failed to open**
(`File is not a valid FieldWorks project file.` at
`XMLBackendProvider.ReadInSurrogate`) -- its `.fwdata` appears corrupted
independently of this task (a same-sized `.bak` sits alongside it, dated
2026-09-20). This is an environmental finding, not something this read-only
task attempted to fix (fixing it would require a write/restore, out of scope
here). Per the issue's own fallback instruction, other projects were used
instead and were sufficient to answer every question below.

## Finding 1 -- IPhSimpleContextSeg / IPhSimpleContextNC real link member

**Confirmed: `FeatureStructureRA` is the real link property on both types.
`SegmentRA` and `NaturalClassRA` do not exist on either concrete interface** --
`hasattr()` returns `False` for both, on live pythonnet-wrapped instances, and
an unguarded direct read raises `AttributeError`.

### IPhSimpleContextSeg (live instance, project `Test`, guid `1d8d6124-241a-49d8-802b-64fa055db4b9`)

- `has_FeatureStructureRA` = `True`, `has_SegmentRA` = `False`, `has_NaturalClassRA` = `False`
- Unguarded `concrete.SegmentRA` (as shown in the wrapper's own docstring examples,
  `phonological_context.py` lines ~411 and ~540) raises:
  `AttributeError: 'IPhSimpleContextSeg' object has no attribute 'SegmentRA'`
- `FeatureStructureRA` sample value: runtime type `IPhPhoneme`, `ClassName` =
  `"PhPhoneme"`, `Name` = `"a"` (a real phoneme in the project's phoneme inventory)

### IPhSimpleContextNC (live instance, project `IndonesianHC-Complete`, guid `f0c782ee-3c28-45fb-b64e-15833c65b12d`)

- `has_FeatureStructureRA` = `True`, `has_SegmentRA` = `False`, `has_NaturalClassRA` = `False`
- Unguarded `concrete.NaturalClassRA` raises:
  `AttributeError: 'IPhSimpleContextNC' object has no attribute 'NaturalClassRA'`
- `FeatureStructureRA` sample value: runtime type `IPhNaturalClass`, `ClassName` =
  `"PhNCFeatures"` (a concrete `IPhNaturalClass` subtype -- LCM's natural classes
  branch into `PhNCSegments` and `PhNCFeatures`), `Name` =
  `'Created automatically for rule "***"'`
- Explicit cast check: `IPhNaturalClass(fsra) is not None` -> `True` --
  **confirms `FeatureStructureRA` really does point at the natural class
  (`IPhNaturalClass`), not at a bare feature structure (`IFsFeatStruc`)**, despite
  the property's name.

### Type-level member lists (CLR reflection on the loaded `SIL.LCModel` assembly, not instance-dependent)

`IPhSimpleContextSeg` properties/methods (58 members) include `FeatureStructureRA`,
`Rule`, `Name`, `Guid`, `ClassName`, `Description`, `DeletionTextTSS`, `SortKey*` --
**no `Segment`, `SegmentRA`, or `Phoneme*` member exists.**

`IPhSimpleContextNC` properties/methods (58 members) include `FeatureStructureRA`,
`PlusConstrRS`, `MinusConstrRS`, `Rule`, `Name`, `Guid`, `ClassName` --
**no `NaturalClass`, `NaturalClassRA`, or `NC*` member exists.**

(Full sorted member arrays for both are in `raw-reflection-data.json:type_level_members`.)

## Finding 2 -- IPhMetathesisRule real member set

**Confirmed: `LeftPartOfMetathesisOS` / `RightPartOfMetathesisOS` do not exist.**
The real API is `StrucDescOS` (shared with every `PhSegmentRule`) plus a set of
integer switch/environment/middle index-and-limit fields, exactly as the issue
suspected.

Four live `PhMetathesisRule` instances were found and reflected (`has_LeftPartOfMetathesisOS`
and `has_RightPartOfMetathesisOS` were `False` on all four):

| project | guid | StrucDescOS.Count | LeftSwitchIndex/Limit | RightSwitchIndex/Limit | MiddleIndex/Limit | LeftEnvIndex/Limit | RightEnvIndex/Limit | IsMiddleWithLeftSwitch |
|---|---|---|---|---|---|---|---|---|
| arz-flex | 9eeb39f4-99b1-4631-bd2c-444359754dba | 0 | -1 / 0 | -1 / 0 | -1 / 0 | -1 / 0 | -1 / 0 | False |
| Tlachichilco Tepehua-NT Noparse | 0b282f4f-1b1d-4246-a999-a8a592bccc6e | 2 | 0 / 1 | 1 / 2 | -1 / 1 | -1 / 0 | -1 / 2 | False |
| Tlachichilco Tepehua-NT orthography | 0b282f4f-1b1d-4246-a999-a8a592bccc6e | 4 | 2 / 3 | 3 / 4 | -1 / 3 | 1 / 2 | -1 / 4 | False |
| Tlachichilco Tepehua-Speedtest | 0b282f4f-1b1d-4246-a999-a8a592bccc6e | 2 | 0 / 1 | 1 / 2 | -1 / 1 | -1 / 0 | -1 / 2 | False |

Full `IPhMetathesisRule` member list (CLR type reflection, 121 members) --
notable properties: `StrucDescOS`, `StrucChange`, `GetStrucChangeIndex`,
`GetStrucChangeIndices`, `SetStrucChangeIndices`, `UpdateStrucChange`,
`LeftSwitchIndex`, `LeftSwitchLimit`, `RightSwitchIndex`, `RightSwitchLimit`,
`LeftEnvIndex`, `LeftEnvLimit`, `RightEnvIndex`, `RightEnvLimit`, `MiddleIndex`,
`MiddleLimit`, `IsMiddleWithLeftSwitch`, `InitialStratumRA`, `FinalStratumRA`,
`Direction`, `Disabled`, `Name`, `Description`, `OrderNumber`. **No
`LeftPartOfMetathesisOS` / `RightPartOfMetathesisOS` / `*PartOfMetathesis*`
member exists anywhere in this list.** (Full array in
`raw-reflection-data.json:type_level_members.IPhMetathesisRule`; this matches
`tests/contract/snapshots/liblcm_baseline.json`'s independently-captured
CLR-reflection baseline for the same interface, corroborating the result.)

## Finding 3 -- Complete ClassName set observed across live PhonRulesOS

Across the 30 projects that had rules (335 rules total):

```
PhRegularRule:     331
PhMetathesisRule:     4
```

**No other `ClassName` value was ever observed.** In particular,
`PhReduplicationRule` never appeared as a live `ClassName`.

## Finding 4 -- Reduplication rule class: does not exist, refuted nowhere

Two independent checks, both negative:

1. `from SIL.LCModel import IPhReduplicationRule` -> `ImportError` (the symbol
   does not exist in the loaded `SIL.LCModel` assembly at all).
2. Scanning `ClassName` across all 335 live rules in 30 projects: zero instances
   of `PhReduplicationRule`.

**Verdict: `lcm_casting.py` lines 122-141 and 1064-1071's claim -- "LCM has no
PhReduplicationRule class; `PhSegmentRule` only branches into `PhRegularRule`
and `PhMetathesisRule`" -- is CONFIRMED, not refuted**, for this LCM build
(FieldWorks 9.3.11.2703). This is consistent with the complete `ClassName` set
in Finding 3 and with `docs/USAGE_PHONOLOGICAL_RULES.md`'s example output
(`PhReduplicationRule: 2 (17%)`) and `phonological_rule.py`'s
`has_redup_parts`/`redup_parts`/`as_reduplication_rule` API being aspirational
documentation/API surface with no live backing -- i.e. currently dead code
paths, matching the `LeftPartOfMetathesisOS`/`RightPartOfMetathesisOS` finding
in shape (guarded `hasattr` reads that can never be true against this LCM
version).

## Pass/fail line

**PASS: live-verified.** `run_mode == "live"` (see LIVE GATE above); all four
questions in the task were answered from live LCM data (three from live
instances with sample values, one -- `IPhMetathesisRule`'s field set -- from
four live instances plus a cross-check against the existing
`tests/contract/snapshots/liblcm_baseline.json` CLR-reflection baseline, which
agrees exactly). No code was changed. No project was written to.

## Raw data

Full machine-readable output (all `projects_scanned` entries, complete member
arrays, complete metathesis samples, complete context samples):
`specs/326-phonological-wrapper-members/evidence/raw-reflection-data.json`

Full pytest output: `specs/326-phonological-wrapper-members/evidence/pytest-run-output.txt`
