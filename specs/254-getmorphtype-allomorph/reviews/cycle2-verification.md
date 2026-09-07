# Cycle 2 -- Live verification report, issue #254

**Overall verdict: PASS**

**Live run:** yes | **run_mode:** live
**Evidence:** specs/254-getmorphtype-allomorph/evidence/live-cycle2-fix.md
**Project:** Sena 3 (sena3_sandbox, tempdir copy)
**Test file added:** tests/operations/test_issue254_live_cycle2.py (8 live
tests, all `requires_live_project`, all `live_phase`-tagged)

## Claim vs. observed

| Claim | Observed live | Status |
|---|---|---|
| C1: bare `bundle.MorphRA.MorphTypeRA` resolves, no cast needed | bare and `IMoForm(...)` cast returned identical `Hvo`; both = `root` for a stem sample | PASS |
| C1: `GetMorphType` returns `IMoMorphType` with correct names | prefix/suffix/root all confirmed, `ClassName=MoMorphType`, matches cycle-1 distribution | PASS |
| C1: `MorphRA is None` -> `None` + warning naming Hvo | `caplog` captured the warning verbatim, named Hvo=139620 | PASS |
| C1: `MorphRA` set, `MorphTypeRA is None` -> silent `None` | Constructed the state (LCM auto-infers a default type on Add -- had to clear it explicitly in a follow-up transaction); confirmed `None`, zero warning records | PASS |
| C2: `SetMorphType` raises `FP_ParameterError` unconditionally, both forms, identical message read-only vs. write-enabled, no transaction, `MorphRA` unchanged | all 4 combinations raised byte-identical message; `UndoableActionCount` and `MorphRA.Hvo` unchanged | PASS |
| C3: `GetMorph` returns `IMoForm`, silent `None` | confirmed both branches, no warning on `None` | PASS |
| C4: `SetMorph` round-trips, clears via `None`, rejects real `IMoMorphType` with `FP_ParameterError` naming `ClassName` | all three confirmed via re-fetch from a *fresh* `project.Object()` call, not the in-memory reference; rejected call caused no mutation | PASS |
| Out-of-scope: does `InflClassRA` exist on live `IWfiMorphBundle`? | **No** -- `hasattr` False, direct access raises `AttributeError` | Answered, not fixed |

## No code change made

Both conditions that would have licensed an edit were false:
- Item 1: bare `morph.MorphTypeRA` resolved correctly live -- the shipped
  code's preferred path is correct; the cast-fallback comment (L850-856)
  is now dead documentation but harmless, left as shipped.
- Item 7: `isinstance(morph, IMoForm)` correctly rejected a real
  `IMoMorphType` object and raised our `FP_ParameterError` (not a
  pythonnet `TypeError`) with no modification needed.

`WfiMorphBundleOperations.py` is unmodified from the programmer's cycle-2
diff. No production code was touched by this verification.

## One live-only discovery, not a defect

Item 4 required constructing a bundle with a linked-but-typeless
allomorph. Sena 3 has none naturally (matches cycle-1: all 1839
non-`None` `MorphRA` samples carried a type). On constructing a fresh
`MoStemAllomorph` and adding it to `entry.AlternateFormsOS`, LCM
auto-inferred a default `MorphTypeRA` (`"root"`) as a commit-time side
effect -- the object was not actually typeless immediately after
creation. This is LCM behavior unrelated to #254 and required no code
change; the test clears the field explicitly in a follow-up transaction
to reach the state the contract describes. Noting it here since it cost
verification time and could surprise a future test author who assumes a
freshly-created `IMoForm` starts with `MorphTypeRA is None`.

## Mock suite (regression, supplementary)

Command: `python -m pytest -m "not requires_live_project" -q`
Result: 1480 passed, 0 failed (5 subtests passed)
Pre-existing failures (not caused by this change): none

## Blockers

None.

## Recommendation

APPROVE
