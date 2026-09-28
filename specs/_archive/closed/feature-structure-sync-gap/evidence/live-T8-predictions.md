# T8 (AllomorphOperations feature-struct sync, unfiled P0) -- PRE-COMMITTED PREDICTIONS

**Committed BEFORE any live run, per `prediction_commitment_rule`
(BINDING from cycle 13, from cycle12-lead-ruling-2).** T8 is an UNFILED P0
-- no GitHub issue exists and filing one is an outstanding USER decision.
Reference this task as "T8, spec.md:655" everywhere, never an issue number.

Author: cycle-16 programmer dispatch (verbatim copy, not reworded).
Parent commit at authoring time: `09fcbf8` (HEAD, main).

A prediction that exists only inside a dispatch prompt is NOT pre-committed
and cannot be adjudicated afterwards. These five are copied verbatim from
the dispatch prompt below. Each is falsifiable and each is reported as
HELD or FALSIFIED in the cycle-16 programmer report.

---

[PREDICTION P1] For a MoAffixAllomorph fetched as `sandbox.Object(hvo)` with
NO cast, hasattr(obj,"Form"), hasattr(obj,"IsAbstract"),
hasattr(obj,"MorphTypeRA") and hasattr(obj,"MsEnvFeaturesOA") are ALL FALSE.
Consequently the CURRENT GetSyncableProperties(hvo) returns exactly
{"Form": {}, "MorphTypeRA": None} -- a silent drop with no raise.
FALSIFIER: any of those four hasattr readings returning True on a genuinely
uncast object, or the current code raising instead of returning that dict.

[PREDICTION P2] With the positive `if class_name == "MoAffixAllomorph"`
dispatch, GetSyncableProperties on a REAL LIVE MoStemAllomorph emits NEITHER
"MsEnvFeatures" nor "MsEnvFeaturesGuid" and does NOT raise; and under
mutation M-T8-2 (delete the ClassName condition so the resolver runs
unconditionally) that same test FAILS with FP_ParameterError naming
"MoStemAllomorph". FALSIFIER: the test staying GREEN under M-T8-2 (it would
then be decorative and R2-shaped, and condition 2 is UNMET), or the
unmutated code raising on MoStemAllomorph.

[PREDICTION P3] No T8 production line passes a non-None `slot=` for the
allomorph family and no T8 test asserts slot disambiguation.
FALSIFIER: a slot= string literal other than None in T8's feature-struct calls.

[PREDICTION P4] Adding the ClassName-discriminated cast to
__GetAllomorphObject changes NO result in any pre-existing live test,
because the 11 other call sites immediately dereference concrete
IMoForm/IMoAffixAllomorph members that would ALREADY have failed loudly on a
bare ICmObject -- so the HVO path was already broken-or-unused there and
widening cannot regress it. FALSIFIER: any pre-existing live test in the
9-file wide-instrument set flipping in EITHER direction between HEAD 09fcbf8
and the T8 commit. This must be MEASURED at both commits, not reasoned; if
you cannot measure both sides, say so explicitly and it becomes a cycle-17
gate leg.

[PREDICTION P5] Mutation M-T8-1 (remove the cast from __GetAllomorphObject)
KILLS the direct-cast test and the HVO-entry-path capture test, while the
MsEnvFeaturesOA round-trip test SURVIVES, because _ResolveFeatureStrucOwner
casts internally and acts as the compensating layer (the cycle-10 finding).
FALSIFIER: the round-trip dying too (no compensating layer), or the
direct-cast test surviving (dead-cast recurrence -- T6b's KEEP-and-TEST
remedy was not actually pre-applied).
