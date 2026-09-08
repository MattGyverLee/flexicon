# Cycle 14 -- CHECKPOINT 4 VERIFICATION GATE on T7 (#252): LEAD PREDICTIONS

**Committed BEFORE any cycle-14 gate run, per `prediction_commitment_rule`
(BINDING from cycle 13, from cycle12-lead-ruling-2).**

Author: /lex-lead, cycle 14 dispatch. Date: 2026-09-07.
Parent commit at authoring time: `5fd1521`.
Subjects under test: `4e9d152` (production) + `4b746a0` (tests), pre-T7
comparison point `1d88aa4`, report commit `c26a017`.

A prediction that exists only inside a dispatch prompt is NOT pre-committed
and cannot be adjudicated afterwards. These ten are. Each is falsifiable.
The gate MUST report each as HELD or FALSIFIED. **A FALSIFIED prediction is a
useful result, not a failure** -- record it with its measurement and proceed.

Where a prediction is marked BLOCKING, falsification means Checkpoint 4 does
NOT close this cycle.

---

## [PREDICTION] G1 -- M1's asymmetric split reproduces EXACTLY (BLOCKING)

Re-running M1 (remove the `ClassName == "PartOfSpeech"` cast from
`POSOperations.__ResolveObject`) from scratch in a fresh disposable worktree
at `4b746a0` will reproduce cycle 13's split exactly:

- **KILLED:** `test_hvo_path_casts_to_concrete_pos` (direct cast lock, with
  `AttributeError` on `DefaultFeaturesOA`) and
  `test_hvo_entry_path_captures_name` (with the P1 observation
  `assert 'Name' in {}`), plus the offline cast-shape test.
- **SURVIVED:** both feature-struct slot round-trips
  (`Default`, `InherFeatVal`), `test_apply_raises_on_unresolved_feature_guid`,
  and `test_ambiguous_owner_without_slot_raises`.

Confidence: high -- this is a re-run of a reported measurement, not a new
inference.

**Falsifier, and it OUTRANKS T7 ENTIRELY:** if either feature-struct
round-trip DIES under M1, then `_ResolveFeatureStrucOwner` is NOT the
compensating cast layer that cycle 10 concluded it was
(`cycle10-CENTRAL-251-QUESTION-ANSWERED-YES`, and the P5 validation built on
it). In that case the gate STOPS the checkpoint work, reports that finding
FIRST and in full, and Checkpoint 4 stays open regardless of every other
leg's colour.

Second falsifier: if everything stays GREEN under M1, the cast is dead code
here as it was in T6 and the `t6b_rulings.P0_dead_c2_cast_RULING` applies
again.

## [PREDICTION] G2 -- M2-M5 each reproduce their reported kills, survivals included (BLOCKING)

Each of M2 (presence gate -> truthiness), M3 (`on_unresolved` raise -> skip),
M4 (ambiguous-no-slot picks `rows[0]`, in shared `BaseOperations.py`) and M5
(InherFeatVal calls forced to `slot="Default"`) will kill the tests named in
`reviews/cycle13-programmer.md` section 3, and M2's two DISCLOSED survivals
(guid-only-truthy, neither-present) will survive again for the reason given
-- truthy fixtures cannot separate presence from truthiness.

**Falsifier:** any reported kill fails to kill. That would mean the claim was
reasoned rather than run, or is environment-dependent -- the exact process
defect `cycle12-lead-ruling-3` was adopted to prevent. Checkpoint 4 does not
close.

## [PREDICTION] G2a -- M4's disclosed co-kill is REAL

`reviews/cycle13-programmer.md` discloses but did not run one claim: that
under M4, T14a's `test_ambiguous_owner_without_slot_raises_through_makefeatstruc`
(`tests/operations/test_makefeatstruc_c3_live.py`) would also die, because M4
edits shared `BaseOperations.py`. PREDICTED: it dies.

**Falsifier:** it survives M4 -- which would mean T14a test 3 does not
actually depend on the raise branch, and `checkpoint_2c` would need
re-examination. Non-blocking on T7 either way, but it must be RUN, not
reasoned: it is a one-line mutation already staged in the same worktree.

## [PREDICTION] G3 -- P2's live half: the POS-touching pre-existing live set is NON-EMPTY, and its delta is ZERO (BLOCKING)

The gate enumerates, by grep at `c26a017`, every pre-existing
`requires_live_project` test that reaches `POSOperations` (directly or via
`project.POS`), EXCLUDING the new `test_issue252_pos_feature_sync.py`.

PREDICTED: the set is **non-empty** and includes at least
`tests/operations/test_pos_operations.py`, `tests/operations/test_pos_catalog.py`,
`tests/operations/test_set_pos_msa_dispatch.py` and
`tests/operations/test_owner_cast_pattern.py`.

PREDICTED: run at `1d88aa4` (pre-T7) and at `c26a017`, same shell, both with
`FLEXLIBS_REQUIRE_LIVE=1` and `run_mode: live`, the pass/fail result is
**identical** -- zero flips in either direction.

**Falsifier and its two branches:**
- The set comes back EMPTY. Then leg 2 is unclosable by this route and a
  green run proves nothing (an empty set is not evidence). The gate must
  instead close P2's live half with a TRACKED probe file that enters a
  representative subset of the other `__ResolveObject` call sites BY HVO at
  both commits and compares. Say which route was taken.
- Any test FLIPS. Then P2 is FALSIFIED on its live half and Checkpoint 4 does
  not close on the strength of the offline half alone.

## [PREDICTION] G3a -- if a flip occurs, its DIRECTION is diagnostic

PREDICTED: any flip will be RED -> GREEN (a method that previously dropped
data on the HVO path now captures it), because the cast strictly ADDS
attributes to the object the other call sites receive.

**Falsifier, and it is a P0 if it fires:** a GREEN -> RED flip. That means a
pre-existing `POSOperations` method duck-types on the *absence* of an
`IPartOfSpeech` attribute, so the cast is not strictly widening and T7
introduced a real regression at one of the sites it never tested.

## [PREDICTION] G4 -- the "15 call sites" figure is WRONG by one (non-blocking, bookkeeping)

`reviews/cycle13-programmer.md` section 5 and
`.crew-handoff.json checkpoint_4.residual_named` both state
`__ResolveObject` has **15** call sites. PREDICTED: grep at `c26a017` finds
**16** `self.__ResolveObject(` invocations -- fourteen pre-existing (lines
273, 401, 439, 474, 511, 555, 617, 673, 674, 711, 751, 792, 841, 913) plus
two new ones inside the T7 sync methods (near 1216 and 1305).

**Falsifier:** exactly 15. Either way this is bookkeeping only and blocks
nothing -- but the residual's DENOMINATOR must be stated correctly, because
"14 other call sites" is the size of the risk P2's live half exists to
bound. Report the exact enumerated list.

## [PREDICTION] G5 -- P1 re-derives at `1d88aa4` in TRACKED form

A tracked probe run inside the worktree at `1d88aa4`, calling
`POSOperations.GetSyncableProperties(<hvo of a real POS>)`, returns a dict
**missing all four** of `Name`, `Abbreviation`, `Description`,
`CatalogSourceId` -- predicted literally `{}`. The same call at `c26a017`
returns all four.

The deleted STEP 0 probe file must NOT be cited as the proof
(`cycle13` lead adjudication: credit M1, and now this leg).

**Falsifier:** any of the four is present at `1d88aa4`. Then P1's mechanism
differs from the stated one, and the "#252 has two halves" framing must be
corrected BEFORE the closure comment is drafted.

## [PREDICTION] G6 -- comparator lands on the NEW baseline

Pinned subset `tests/operations tests/contract -m "not requires_live_project"
-p no:cacheprovider` at `c26a017`: **2 failed / 416 passed / 518 deselected**,
red set exactly the two foreign
`test_transaction_rollback.py::TestPhase2JoinOrOpen` failures.

**Falsifier:** a third failure (a real regression), or 396/392 (a gate reading
a stale baseline -- see `cycle12-comparator-BASELINE-MOVED`). Report a DELTA
measured in the gate's own shell, never a bare absolute.

## [PREDICTION] G7 -- the live file re-runs clean as committed

`test_issue252_pos_feature_sync.py` at `c26a017`: 6 passed / 20 deselected,
`tests/live_status.json` shows `"run_mode": "live"` and
`"uncategorized_live_tests": []`.

**Falsifier:** anything other than 6 passed, `run_mode: mock`, or any of the
six appearing under `uncategorized_live_tests` (the D4-T7 telemetry defect
recurring).

## [PREDICTION] G8 -- closing conditions 1-8 and 10 re-derive to MET (BLOCKING)

Independently re-derived from source, git and the offline suite -- NOT read
back from `STATUS.md`'s verdicts -- conditions 1, 2, 3, 4, 5, 6, 7, 8 and 10
all come back MET, with condition 5's known truthiness residual disclosed
and unchanged from T6b.

**Falsifier:** any one returns NOT MET. Checkpoint 4 does not close.

## [PREDICTION] G9 -- the Pyright diagnostics are PRE-EXISTING, not T7's

PREDICTED: `git show 4e9d152 -- flexicon/code/Grammar/POSOperations.py`
touches **no line below ~1100**, so the diagnostics at lines 206/208/241/372
(tuple attribute access, override parameter-name mismatch) predate T7; and
the `super().ApplySyncableProperties` diagnostic has an identical shape at
`MSAOperations.py:1001`, which T6 already carried through a PASSED gate.

**Falsifier:** the diff touches lines below 1100, or the diagnostic SET
differs between `1d88aa4` and `c26a017` beyond the new region. Then T7 added
type noise and it is a P2 to record, not to fix in this cycle.

## [PREDICTION] G10 -- the `CompareTo` side effect is REAL and is P2's honest soft spot

`reviews/cycle13-programmer.md` section 6 discloses that `CompareTo` output
CHANGED as a side effect: two POS with identical feature specs but
independently-created structs now report a difference on the `<key>Guid`
key, where previously the keys did not exist to compare.

PREDICTED: this is genuinely new observable behaviour for any caller
comparing two POS, it is pinned only by the new file's own
`TestPOSSyncCompareToStructGuidPinning`, and P2's committed falsifier ("any
test OUTSIDE the new T7 file changes result") does NOT technically fire on it
because the change is confined to keys the new file introduced.

PREDICTED FURTHER: `3eff177`'s CHANGELOG entry does NOT disclose it.

**Falsifier:** the CHANGELOG does disclose it (then nothing to record), or a
test outside the new file does move on it (then P2 is falsified through this
route instead of through leg 2). Non-blocking on Checkpoint 4 either way, but
if the CHANGELOG omission holds, the gate records it as a P2 and the #252
closure draft must name the behaviour change explicitly -- a caller reading
"closes #252" should not discover it from a diff.
