GATE: PASS

# Cycle 4 verification gate -- T4

**Evidence:** specs/feature-structure-sync-gap/evidence/live-cycle4-verification-t4.md
**Baseline used:** a26d39c (T4's true parent -- confirmed via git graph:
4aca74a's sole parent, pre-dating the ec54432 rename that merged in via
3d357d8). Comparison points stated explicitly: a26d39c (pre-T4), 4aca74a
(T4 production diff, still pre-rename in this line), e17cd7d (final HEAD,
post-rename-merge, post T4 test commits). All three measured directly,
not asserted.

## Part 1 -- both sides measured
Live subset (3 named files): 34 passed/14 deselected/1 failed IDENTICAL
at a26d39c and at HEAD (4th file test_apply_feature_struc.py adds exactly
+7 passed at HEAD, 41 total). run_mode: live confirmed every run.

Full bare offline command (python -m pytest -m "not requires_live_project"
-q) crashes IDENTICALLY on both sides in this environment (225
passed/1270 errors at a26d39c vs 225 passed/1273 errors at HEAD, delta
fully explained by +15 newly-collected requires_live_project tests from
concurrent/new files). Root-caused to a pre-existing bug: conftest.py's
autouse fixture calls unguarded Sldr.Initialize(True) while
FLExInit.FLExInitialize() wraps the same call in try/except; whichever
legacy test module inits SLDR first (several exist under flexicon/tests,
flexicon/sync/tests, tests/contract) makes conftest's raise. Confirmed
present at a26d39c, i.e. before any T4 commit -- orthogonal to T4,
not a regression it introduced. This is a genuine discrepancy from the
implementer's reported "1495 passed / 3 failed" (which did not reproduce
here) but does not change the verdict for the reason above -- full
detail in the evidence file.

## Part 2 -- zero-delta audit
Confirmed via git diff a26d39c..4aca74a on both Operations files:
PhonemeOperations.py:1351 and :1431 byte-identical, untouched; Phoneme's
on_unresolved="skip" default preserved at the call-through; NC's
on_unresolved="raise" and struct_guid=features_guid preserved. Neither
NC's nor Phoneme's GetSyncableProperties (capture side) touched -- both
still emit the legacy flat list (C4b holds). Exactly ONE copy of the C1
table repo-wide (Shared/lcm_constants.py::FEATURE_STRUC_OWNER_TABLE).

## Part 3 -- E5 assertion migration
Independently enumerated the pre-T4 file at a26d39c: 6 individual assert
statements (spec's own convention groups them into "5" since 2 share one
test method) targeting _NaturalClassOperations__ApplyFeatures. All 6
found migrated 1:1 onto BaseOperations._ApplyFeatureStruc via a new
_base_method_source helper, same literal substrings except the two the
task itself mandated renaming (__ResolveByGuid -> _ResolveFsByGuid per
T3 de-dup; nc_name -> label per C5's frozen signature, with NC's actual
rendered error text unchanged). Zero deleted, zero weakened. Full table
in the evidence file.

## Part 4 -- anti-tautology mutation tests
Mutation 1 (legacy raise-mode: raise -> continue on unresolved
FeatureGuid): live subset went from 1 failed to 3 failed (2 new real
failures). Mutation 2 (nested recursion: struct.TypeRA = type_obj ->
pass): the dedicated nested-recursion test failed (1 failed, 6 passed).
Both mutations restored from a saved pre-mutation copy and hash-verified
identical to the committed blob (git hash-object ==
1bc956bbb629f217f9bd8051d47f5af9dbbdb568 == git rev-parse
HEAD:flexicon/code/BaseOperations.py), confirmed both times. Live subset
re-run clean after each restore.

## Part 5 -- C4a dual-shape check
Read _ApplyFeatureStruc/_ApplyFeatureStrucSpecMap directly:
isinstance(spec_dict, dict) branches cleanly to legacy-list vs C4-dict
handling. Legacy shape has its own dedicated live test class
(TestApplyFeatureStrucLegacyListLive, 4 tests); C4 dict shape (flat and
one level nested) has its own dedicated live test class
(TestApplyFeatureStrucC4DictLive, 3 tests). Both shapes are genuinely
exercised by tests, not merely present in code.

## Part 6 -- opportunistic (report only)
Confirmed YES: PhonemeOperations.__ApplyBasicIPASymbol (current location
PhonemeOperations.py:1440-1442) builds its own
{ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()} map
rather than delegating to _apply_props_loop, so it will not inherit a
fix queued as issue #250 Defect 4. Confirmed untouched by T4's diff. Not
changed, per instruction.

## Recommendation
APPROVE. T4's zero-runtime-delta claim holds under independent live and
code-level re-measurement; the E5 migration is verified 1:1; the mutation
tests prove the new/relocated code paths are load-bearing, not
tautological. One process note for the lead: the offline full-suite
count could not be reproduced in this session due to a pre-existing,
order-dependent SLDR-double-init crash (present at a26d39c too, so not a
T4 regression) -- worth a follow-up ticket, not a blocker for this gate.
