# Verification Report -- lcm-member-truth-sweep cycle 1

**Verdict:** [PASS] (reflection + read-path ground-truth sweep; no production
fix was authored or claimed in this task -- this establishes the facts a
future fix must be built against)
**Live run:** yes | **run_mode:** live
**Evidence:** specs/lcm-member-truth-sweep/evidence/live-cycle1-reflection.md
**Project:** Sena 3 (sena3_sandbox, tempdir copy) for Parts 1(d)/2(c)/2(d);
pure clr.GetClrType reflection (no project needed) for Parts 1(a)/1(b)/1(c)/
2(a)/3(a)/3(b)

## Scope note

This task was explicitly a reflection + read-path ground-truth task, not a
fix. "Did this change do what it claims" therefore maps to: did the
reflection sweep actually reach live SIL.LCModel / a live LCM cache and
produce machine-checked evidence for every claim requested, rather than
guessed or copied-from-code-comments evidence. It did.

## Claim vs. observed

| Claim (from the briefing) | Observed live | Status |
|---|---|---|
| #259: dump full IWfiMorphBundle surface | 7 properties dumped verbatim; InflClassRA absent | [PASS] |
| #259: check IMoStemMsa / IMoInflAffMsa / MsaRA base / InflTypeRA target | All 4 surfaces dumped; IMoStemMsa.InflectionClassRA found; IMoInflAffMsa and the IMoMorphSynAnalysis base have no such member; ILexEntryInflType confirmed a distinct concept (no overlap) | [PASS] |
| #259: clear verdict (i)/(ii)/(iii) with evidence | Verdict (ii) -- navigate MsaRA to IMoStemMsa.InflectionClassRA -- stated with the full surface dumps as evidence | [PASS] |
| #259: confirm live whether MsaRA navigation is safe when null/wrong subtype | Sampled 1932 real Sena 3 bundles: 94 null MsaRA, 1144/1838 non-null are non-stem subtypes that raise AttributeError on .InflectionClassRA when accessed unguarded | [PASS] |
| #283: confirm IPhEnvironment context member names/types | LeftContextRA/RightContextRA confirmed (IPhPhonContext); LeftContextOA/RightContextOA confirmed absent | [PASS] |
| #283: state correct Duplicate semantics under RA, and deep=True's meaning | Reference-assignment is correct; deep=True has no remaining meaning for the context fields once names are fixed (documented as an anti-pattern flag risk per CLAUDE.md) | [PASS] |
| #283: Sena 3 pre-state count of environments with populated contexts | 0/44 -- recorded verbatim | [PASS] |
| #283: seed in sena3_sandbox only, exercise both sides, read back HVOs from BOTH source and duplicate, state reference vs clone | Seeded (TEST_283_seed_env, 2 IPhSimpleContextSeg objects); re-read by HVO: source both populated (152223/152224), duplicate both None -- observed finding is that current Duplicate code implements NEITHER semantics (silent drop, same defect class as #259), not that it clones | [PASS] |
| #302: confirm IRnResearchNbkRepository surface is Singleton (+Count claim) | Singleton confirmed as the sole property this reflection surfaced; the "Count" half of the issue's claim is flagged unconfirmed/needs-recheck against the generic IRepository\<T\> base, not silently accepted | [PASS] (with caveat noted, not swept under) |
| #302: confirm IRnResearchNbk.RecordsOC exists | Confirmed present on the Singleton's type | [PASS] |
| #261: name the exact service-locator path + file:line precedent | project.Object(hvo) -> ServiceLocator.GetObject(...); precedent cited at flexicon/code/Grammar/EnvironmentOperations.py:714 | [PASS] |

## #259 verdict (headline)

**(ii) -- navigation through MsaRA**, specifically
`bundle.MsaRA -> cast_to_concrete(...) -> (only if IMoStemMsa) .InflectionClassRA`.
Not (i): no member of any name for this concept exists on `IWfiMorphBundle`
itself (full 7-property surface dump has no candidate). Not (iii): the
field genuinely exists in the model (`IMoStemMsa.InflectionClassRA`), it
is just one hop away via `MsaRA`, not declared on the bundle. The
navigation is NOT safe unguarded: live sampling over 1932 real bundles
found 94 with null `MsaRA` and 1144 with a non-stem MSA subtype that
raises `AttributeError` (not `None`) on `.InflectionClassRA` when
accessed on the concretely-cast object without an `isinstance` check --
so the fix needs both a None-check and a concrete-type narrowing, not a
bare rename.

## #283 reference-vs-clone observation (headline)

The seeded live probe shows current `Duplicate` code does **neither**
reference nor clone semantics -- it silently drops both contexts on
every call, because it writes to `LeftContextOA`/`RightContextOA`, names
that do not exist on `IPhEnvironment` (real names are
`LeftContextRA`/`RightContextRA`, confirmed by `clr.GetClrType`). Source
environment's contexts were confirmed non-null after seeding
(hvo=152223/152224); the duplicate's were confirmed `None` after a fresh
re-fetch by HVO. Once the property names are corrected, the analytically
correct semantics under Reference Atomic is a plain reference assignment
(`duplicate.LeftContextRA = source.LeftContextRA`), not a deep clone --
`deep=True` has no remaining meaning for this field.

## Mock suite (regression, supplementary)

Not run this cycle -- this task made no production code change (pure
reflection/read-path plus one restored sandbox seed), so there is nothing
new for the mock suite to regress-test. The mock suite remains
appropriate to run once an actual #259/#283/#302/#261 fix is authored in
a later cycle.

## Blockers

None. Target/Sena 3 fixtures were both available; FieldWorks 9 was
installed and reachable; `sena3_sandbox` opened normally.

## Test artifact

`tests/operations/test_lcm_member_truth_sweep.py` -- 9 tests, all pass
live (`run_mode: live`, confirmed via `tests/live_status.json`). No
production code was modified. The only write performed was the
explicitly authorized Part 2(d) seeding into `sena3_sandbox` (a tempdir
copy), fully restored in a `finally:` block.

## Recommendation

APPROVE for handoff to the next spurt: the #259 fix should implement
`MsaRA` navigation with a None-check + `cast_to_concrete`/`isinstance`
narrowing to `IMoStemMsa` (not a bare rename); the #283 fix should
correct the property names to `LeftContextRA`/`RightContextRA` and
implement reference-assignment semantics in `Duplicate` (reconsidering
whether `deep` should remain a parameter at all for this field, per
CLAUDE.md's no-op-flag anti-pattern); #302's `repos.RecordsOC` ->
`repos.Singleton.RecordsOC` rewrite is confirmed safe to proceed, with a
follow-up recheck of the "Count" half of that issue's claim; #261's fix
should route `DataNotebookOperations.py:182/187` through
`self.project.Object(hvo)` instead of the raw `LcmCache.GetObject(hvo)`,
following the `EnvironmentOperations.py:714` precedent.
