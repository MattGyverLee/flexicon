# Cycle-17 Checkpoint 5 gate -- LEAD PREDICTIONS (committed before any run)

Author: lex-lead, cycle 17. HEAD at authoring: e7f1048.
Rule: prediction_commitment_rule (BINDING from cycle 13). Each prediction
carries an explicit falsifier. An empty falsifier set is NOT a pass
(standing_rule_empty_falsifier_set_is_not_a_pass).

## [PREDICTION] G1 -- LEG 1, P4's unmeasured HVO axis
A new live test that passes a GENUINE Python int (an existing
MoAffixAllomorph's `.Hvo`, asserted `isinstance(hvo, int)`) into a COVERED
site -- primary site `GetForm` (AllomorphOperations.py:813), which is
read-only and therefore safe on target_sandbox -- will PASS at HEAD, and
will go RED under mutation M-G1 (delete the two ClassName cast branches at
AllomorphOperations.py:1364-1369 so `__GetAllomorphObject` returns `obj`
unchanged) with an AttributeError or failed assertion naming the
concrete-only member. Basis: cycle-16's P1 measured
`hasattr(bare_object, "Form") -> False` on a bare `sandbox.Object(hvo)` view
of a real MoAffixAllomorph, so `Form` is itself concrete-only through the
HVO entry path.
FALSIFIER: the test stays GREEN under M-G1. If that happens, the gate must
try a second covered site (Delete :310, Duplicate :373, SetForm :858) before
concluding, and if no covered site can be made to go red, P4's HVO half is
FALSIFIED-AS-UNTESTABLE and the cast needs a different justification --
report that verdict, do not soften it.

## [PREDICTION] G2 -- LEG 2, the surviving hasattr gates
For a live LCM object whose ClassName is NEITHER "MoStemAllomorph" NOR
"MoAffixAllomorph", `Allomorphs.GetSyncableProperties(hvo)` will NOT raise:
`__GetAllomorphObject` returns the object unchanged (R16-4(ii), never-raising
by design), the three gates at :570/:579/:584 all evaluate False, and the
return value is exactly `{'Form': {}, 'MorphTypeRA': None}` -- i.e. the T8
defect-i silent-drop shape reproduces verbatim on the unrecognised-ClassName
path. The `allomorph.ClassName == "MoAffixAllomorph"` check at :594 is
reached and evaluates False, so no feature key is emitted and the resolver is
never entered.
FALSIFIER: it raises instead of dropping (then R16-4(ii)'s never-raising
characterisation is wrong and condition 3 must be re-ruled), OR the returned
dict differs from `{'Form': {}, 'MorphTypeRA': None}` (then the gate reports
the actual dict verbatim and the lead re-rules).

## [PREDICTION] G2b -- LEG 2's allowlist test shape
AllomorphOperations.py contains SEVEN `hasattr` calls, not three: :358 and
:368 (Delete, first arg `owner`), :460 and :466 (Duplicate, first arg
`parent`), plus the three subtype gates at :570/:579/:584 (first arg
`allomorph`). Therefore an allowlist test asserting "exactly 3 hasattr calls
in the file" is WRONG and would fail for the wrong reason. The correct test
scopes by FIRST-ARGUMENT IDENTITY: exactly three `hasattr` calls in this file
take the resolved `allomorph` as their first argument, and their second
arguments are exactly the string literals "Form", "IsAbstract",
"MorphTypeRA".
FALSIFIER: the AST walk finds a count other than 7 total or other than 3
`allomorph`-scoped, or a second-argument set differing from those three
literals. Report the actual numbers.

## [PREDICTION] G3 -- LEG 3, independent reproduction
Re-run from scratch in a FRESH disposable worktree, M-T8-1 (remove the cast)
reproduces the cycle-16 ASYMMETRIC split: the direct-cast test
(TestT8LiveDirectCast) and the HVO-entry test (TestT8LiveHasattrTrap) DIE,
while the feature-struct round-trip (TestT8LiveRoundTrip) SURVIVES via the
`_ResolveFeatureStrucOwner` compensating layer. M-T8-2 (delete the
`ClassName == "MoAffixAllomorph"` guard at :594) turns the live stem test
(TestT8LiveStemAllomorphNoFeatureKeys) RED with an FP_ParameterError naming
MoStemAllomorph.
FALSIFIER: any predicted-dead test survives, any predicted-survivor dies, or
M-T8-2's failure does not name MoStemAllomorph. A NOT-KILLED mutation is a P0
and reopens Checkpoint 5.

## [PREDICTION] G4 -- LEG 4, the moved baseline
`python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider`
at HEAD e7f1048 yields 2 failed / 437 passed / 524 deselected, with the red
set exactly the two foreign tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen
failures. After this gate's own new OFFLINE tests land, `passed` rises by
EXACTLY the number of new offline tests added and `failed` stays 2.
FALSIFIER: a third failure, a different red set, or a passed-delta not equal
to the count of new offline tests. 416/2/518 is RETIRED and must not be cited.

## [PREDICTION] G5 -- LEG 5, evidence durability (lead predicts PARTIAL)
evidence/live-T8.md corroborates live_status.json at :17 (`"run_mode": "live"`)
and :61 (`"run_mode": "live"`, `"run_timestamp": "2026-09-08T04:08:50Z"`).
The lead predicts these are KEY-LEVEL QUOTES, not a verbatim dump of the
live_status.json block, so condition 8 is met in SUBSTANCE (run_mode live is
durably recorded in-cycle, with a timestamp, committed at bd98c6b) but only
PARTIALLY against the literal "quotes it VERBATIM" wording of the cycle-15
ephemerality rule. Verdict predicted: PASS-WITH-QUALIFIER, not clean PASS.
FALSIFIER (two-sided): if a full verbatim live_status.json block IS present,
the verdict is a clean PASS and this prediction is falsified in the
conservative direction; if run_mode/timestamp are NOT actually quoted, or the
quote postdates cycle 16, condition 8 FAILS outright.

---

# POST-HOC ERRATUM (lead, cycle-17 adjudication -- appended, nothing above rewritten)

The predictions above are preserved VERBATIM as committed at `8691c65`. This
erratum is appended below them so the audit trail stays intact; do not edit the
prediction text itself.

## ERRATUM 1 -- G3's test-name mapping was wrong in one place (two symptoms)

G3's text names the M-T8-1 dead set as `{TestT8LiveDirectCast,
TestT8LiveHasattrTrap}` and names `TestT8LiveRoundTrip` as the survivor. Both
halves of that mapping are wrong, from a single authoring error: the lead
believed the HVO-entry test lived in `TestT8LiveHasattrTrap`, when it actually
lives in `TestT8LiveRoundTrip`. Corrected mapping, against the inventory as it
stood at `e7f1048` (i.e. before this prediction was committed):

| G3's semantic label | Class named in G3 | Test that actually carries it | M-T8-1 outcome |
|---|---|---|---|
| "the direct-cast test" | `TestT8LiveDirectCast` | `::test_hvo_path_casts_to_concrete_affix_allomorph` | DIES (as predicted) |
| "the HVO-entry test" | `TestT8LiveHasattrTrap` (WRONG) | `TestT8LiveRoundTrip::test_hvo_entry_path_captures_form` (:933) | DIES (as predicted, different class) |
| "the feature-struct round-trip" | `TestT8LiveRoundTrip` (imprecise -- that class holds 3 tests, only 1 is the round-trip) | `TestT8LiveRoundTrip::test_ms_env_features_capture_apply_roundtrip` (:894) | SURVIVES (as predicted) |

Read literally, the error produced TWO breaches of G3's falsifier, not one:
(i) a predicted-dead test survived (`TestT8LiveHasattrTrap`); and
(ii) a member of a predicted-survivor class died
(`TestT8LiveRoundTrip::test_hvo_entry_path_captures_form`). The cycle-17 gate
report disclosed only (i). Both are recorded here.

## ERRATUM 2 -- `TestT8LiveHasattrTrap` CANNOT die under M-T8-1. Do not read its green as suspicious.

`TestT8LiveHasattrTrap::test_bare_moaffixallomorph_hasattr_all_four_false` calls
only `sandbox.Object(allo.Hvo)` and asserts `hasattr` is False for four members
on that BARE object. It never calls `__GetAllomorphObject`. M-T8-1 makes
`__GetAllomorphObject` return its argument unchanged; it does not change what a
bare `ICmObject` view is. The assertions therefore remain true by construction.
Predicting this test's death was not merely mislabeled -- it was IMPOSSIBLE.
Its survival is correct and structurally necessary, not a resilience finding
and not a regression.

## Why this is a labeling defect and NOT a post-hoc falsifier substitution

The discriminating question: could the corrected mapping have been derived from
G3's own semantic labels plus the test inventory AT PREDICTION TIME, with no
reference to the outcome? Yes, and it is forced:

- `test_hvo_entry_path_captures_form` is the only test in the file named for the
  HVO entry path, and its docstring says so outright ("GetSyncableProperties(hvo)
  must capture Form on the HVO entry path").
- `test_ms_env_features_capture_apply_roundtrip` is the only feature-struct
  round trip in the file.
- Every test involved PRE-EXISTED this prediction. `8691c65` is a child of
  `e7f1048` and a strict ancestor of all four cycle-17 measurement commits
  (`44c67eb`, `14dce75`, `a962728`, `12d44cb`) -- verified from the DAG. No test
  was written, renamed or re-marked in cycle 17 to satisfy a falsifier.

A genuine post-hoc substitution has a signature this episode does not have: the
semantically-named test SURVIVES and the gate goes shopping among the reds for a
replacement claim. Here the semantically-named HVO-entry test is precisely the
one that died, and the semantically-named round-trip is precisely the one that
survived. The asymmetric split was confirmed on the exact axes predicted.

`standing_rule_empty_falsifier_set_is_not_a_pass` does NOT bite. That rule
targets a no-change measurement whose falsifier set is empty on the affected
axis. G3 is not a no-change measurement: M-T8-1 produced three real kills (2
live + 1 offline collateral), M-T8-2 produced one naming `MoStemAllomorph`
exactly, and three named survivors DO traverse `__GetAllomorphObject` indirectly
and could have flipped. The falsifier set was non-empty and load-bearing in both
directions. The clause that carries the reopening consequence -- "a NOT-KILLED
mutation is a P0 and reopens Checkpoint 5" -- did not fire: every mutation
applied in cycle 17 was killed by at least one test.

## ERRATUM 3 -- G4's "six T8 commits" premise

The cycle-17 gate prompt and STATUS.md described range `09fcbf8..e7f1048` as
"six commits". `git rev-list --count 09fcbf8..e7f1048` = **8**
(`cf2fdfe`, `df37e35`, `016a97a`, `bd98c6b`, `191556f`, `6484d81`, `fdd8694`,
`e7f1048`). `cf2fdfe` IS chronologically first, so the provenance claim that
rested on the ordering holds. Prose-accuracy defect only; no prediction's truth
value changes.
