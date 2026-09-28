# T7 (POSOperations feature-struct sync, flexicon#252) -- LEAD PREDICTIONS

**Committed BEFORE any T7 run, per `prediction_commitment_rule`
(BINDING from cycle 13, from cycle12-lead-ruling-2).**

Author: /lex-lead, cycle 13 dispatch. Date: 2026-09-07.
Parent commit at authoring time: `7e0fdf2`.

A prediction that exists only inside a dispatch prompt is NOT pre-committed
and cannot be adjudicated afterwards. These five are. Each is falsifiable and
each MUST be reported as HELD or FALSIFIED in the cycle-13 programmer report
and re-checked by the Checkpoint 4 gate. A FALSIFIED prediction is a useful
result, not a failure -- record it and proceed.

---

## [PREDICTION] P1 -- the #252 entry-path hole is REAL and wider than the filed issue

`POSOperations.__ResolveObject` (`flexicon/code/Grammar/POSOperations.py:1107`)
returns `self.project.Object(pos_or_hvo)` with **no cast**. `GetSyncableProperties`
(`:1149`) calls it, then gates every capture on `hasattr(pos, prop_name)`
(`:1159`) and `hasattr(pos, "CatalogSourceId")` (`:1170`).

PREDICTED: calling `POSOperations.GetSyncableProperties(<hvo of a real POS>)`
on a live project TODAY returns a dict **missing all four** of `Name`,
`Abbreviation`, `Description`, `CatalogSourceId` -- i.e. `{}` or near-`{}` --
because a bare `ICmObject` from `project.Object()` answers `hasattr` False for
all of them.

COROLLARY PREDICTED: cycle 1's item-3 conclusion -- "`POSOperations.GetAll()`
already performs the correct cast, so `hasattr` works correctly on **every
object `GetSyncableProperties` will ever receive**"
(`evidence/live-cycle1-probe.md:88-91`) -- is **entry-path-conditional and
therefore wrong**. It is true for the `GetAll()` path and false for the HVO
path. #252 is then not a *pure* coverage gap: it is a coverage gap **plus** a
silent-drop bug on the HVO entry path.

Confidence: high. Falsifier: the four keys come back populated from an HVO.

## [PREDICTION] P2 -- the C2 cast is a strictly widening change

PREDICTED: adding a `ClassName`-discriminated cast to `IPartOfSpeech` inside
`__ResolveObject` (cast on `ClassName == "PartOfSpeech"`, return the object
UNCHANGED on any miss -- the `__ResolveMsa` shape) makes P1's four keys appear
and changes nothing else across the other 15 `__ResolveObject` call sites,
because those sites already receive concrete objects from `GetAll()`/`Find()`
or pass non-POS objects straight through.

Falsifier: any offline or live test outside the new T7 file changes result.

## [PREDICTION] P3 -- the live round-trip must CREATE its struct

PREDICTED: both `DefaultFeaturesOA` and `InherFeatValOA` exist on
`IPartOfSpeech` with declared CLR type `SIL.LCModel.IFsFeatStruc`
(cycle-1 item 3 measured this: `hasattr` 26/26 True, both), and **no** POS in
the sandbox carries a non-null struct (cycle-1 measured non-null 0/26 for
both). So the live test cannot find a populated POS to read; it MUST create
the struct on a `TEST_`-prefixed POS via the apply path first.

Falsifier: either property absent from `IPartOfSpeech` (which would invalidate
a frozen `FEATURE_STRUC_OWNER_TABLE` row and is a STOP), or a non-null struct
found in the sandbox.

## [PREDICTION] P4 -- slot ambiguity raises, it does not guess

PREDICTED: `_ResolveFeatureStrucOwner(pos)` with **no** `slot=` raises
`FP_ParameterError` whose message names both `PartOfSpeech` and `slot`,
because `FEATURE_STRUC_OWNER_TABLE["PartOfSpeech"]` has two rows
(`Shared/lcm_constants.py:127-130`) -- the same behaviour T14a test 3 pinned
for `MoDerivAffMsa`.

Falsifier: it returns a row instead of raising, or the message omits either
term.

## [PREDICTION] P5 -- POS's cast mutation KILLS, where MSA's did NOT

This is the distinguishing prediction of cycle 13, and it is deliberately the
opposite of the cycle-10 result.

At cycle 10, removing `__GetMsaObject`'s cast left all six live MSA tests GREEN
(NOT-KILLED) because `_ResolveFeatureStrucOwner` re-derives `ClassName` and
re-casts independently -- a second compensating layer.

PREDICTED for POS: removing the new `__ResolveObject` cast will
(a) kill the new **direct** cast test, and
(b) **also** kill at least one **behavioural** live test -- specifically the
HVO-entry capture test asserting `Name` comes back -- because the four
multistring/string props have **no** compensating second layer; only the two
feature-struct keys do.

PREDICTED SPLIT, stated explicitly so a partial result is still adjudicable:
under cast removal the two feature-struct keys are expected to SURVIVE (they
route through `_ResolveFeatureStrucOwner`, which casts internally) while the
four multistring props are expected to DROP.

Falsifier: everything stays green (then the cast is dead code here too, and the
T6b `P0_dead_c2_cast_RULING` applies again), or the feature keys also drop
(then `_ResolveFeatureStrucOwner` is not the compensating layer cycle 10
concluded it was, and that finding outranks this task).
