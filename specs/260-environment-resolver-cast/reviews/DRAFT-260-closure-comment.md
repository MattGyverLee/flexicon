# DRAFT closure comment for flexicon#260 -- FOR USER REVIEW, NOT POSTED

**Status: DRAFT. No GitHub action has been taken.** Nothing below has been
posted, and #260 has not been labelled or closed. Closure routes through the
main session and the user.

**CYCLE-2 UPDATE (2026-09-08): T2 and T3 have now landed, and P9 has been
verified live** (`specs/260-environment-resolver-cast/evidence/
live-T3-p9-p10.md`, `run_mode: "live"`). Part 2 below has been rewritten to
match. **Still do not post without explicit user sign-off** -- posting to
GitHub is a main-session/user action, not something this cycle performs
itself. Two things changed since the draft was first written that the user
should be aware of before approving posting:

1. The flexicon#268 coverage claim (see Part 2 and the reviewer notes) is
   now TRUE for both halves of the call (allomorph-HVO and
   environment-HVO), not just the environment half -- P10 measured
   `hasattr(bare_allo, "PhoneEnvRC") == False` live, so two new tests were
   added exercising the allomorph itself as a genuine int HVO.
2. A NEW, separate, pre-existing bug was discovered while building this
   cycle's P7 fixture: `EnvironmentOperations.GetLeftContextPattern` /
   `GetRightContextPattern` / `Duplicate`'s deep-copy block all read a
   property name (`LeftContextOA`/`RightContextOA`) that does not exist
   anywhere in the LCM API for `IPhEnvironment` -- confirmed live via .NET
   reflection, which lists only `LeftContextRA`/`RightContextRA`. This is
   NOT part of #260 and is NOT fixed by this cycle's cast; see the new
   "Part 3" section below, added so it is not lost. Recommend filing a new
   issue for it separately -- do not fold it into #260's closure.

---

## Proposed comment body

### Part 1 -- `__GetAllomorphObject` (the reported crash): FIXED and gated

The `AttributeError: 'ICmObject' object has no attribute 'Form'` in the issue
body is fixed. `Lexicon/AllomorphOperations.py __GetAllomorphObject` now
resolves and then casts by `ClassName` to the concrete allomorph interface
(`IMoStemAllomorph` / `IMoAffixAllomorph`) before returning, on **both** the
`int`-HVO branch and the already-an-object branch. The object branch matters:
the reported failure came from an object input
(`obj = project.Object(guid); allomorphs.GetForm(obj)`), so an int-only cast
would have left the reported defect live.

- Fix: commit `df37e35` (landed as task T8 of the feature-structure-sync-gap
  spurt).
- Live gate: `tests/operations/test_t8_hvo_path_gate.py`, which passes a
  **genuine Python `int`** HVO (asserted `isinstance(hvo, int)` before the
  call) so the cast is exercised non-vacuously; an already-typed object would
  exercise it vacuously and prove nothing. Adjudicated at cycle 17.
- The resolver is deliberately **permissive**: an unrecognised `ClassName` is
  returned unchanged rather than raising, because 11 other call sites depend
  on this shared resolver never raising.

The workaround shown in the issue body (callers hand-writing `IMoForm(obj)`)
is no longer needed.

### Part 2 -- the requested `__GetEnvironmentObject` sibling sweep: investigated, **no behavioural defect found**

The issue asked for `__GetEnvironmentObject` to be swept in the same pass, on
the explicit basis that it was *"not directly observed failing this window, but
structurally the same defect."* We took that seriously and tested it directly
rather than assuming the structure implied the bug. It does not.

**Measured live against unmodified source** (`target_sandbox`,
`FLEXLIBS_REQUIRE_LIVE=1`, `tests/live_status.json` `run_mode: "live"`): both
callers of the uncast resolver -- `AddPhoneEnv` and `RemovePhoneEnv` --
**SUCCEED** with a genuine `int` HVO, and a fresh re-fetch from the LCM
confirms the write persisted in both directions. The pre-fix baseline was
**green, not red**.

**Why the structural similarity does not carry.** An uncast resolver is only a
*behavioural* defect where a caller performs **Python attribute access** on the
resolved object. pythonnet's Python-side wrapper exposes only the members
declared on the static interface it was built against (`ICmObject`), so
`env.Name` raises and `hasattr(env, "LeftContextOA")` silently answers
`False`. That is the axis Part 1 failed on (`.Form`).

Passing that same bare wrapper as an **argument to a strongly-typed .NET
method** is a different path: the CLR binds the argument on the object's
*runtime* type, which does implement `IPhEnvironment`. Both of
`__GetEnvironmentObject`'s callers do only that
(`allomorph.PhoneEnvRC.Add/.Remove`, an
`ILcmReferenceCollection[IPhEnvironment]`). Hence a real contract mismatch
with **zero behavioural consequence at either call site**.

Two supporting measurements from the same live run:

- `IPhEnvironment` has exactly **one** implementing type in the whole
  `SIL.LCModel` assembly (`SIL.LCModel.DomainImpl.PhEnvironment`), so there is
  no subtype hierarchy to discriminate here -- unlike `IMoForm`'s stem/affix
  split in Part 1.
- The attribute-access trap itself is real for `PhEnvironment`:
  `hasattr(bare, "StringRepresentation")` and `hasattr(bare, "Name")` are both
  `False` on a bare `project.Object(hvo)` view. The trap exists; these two
  callers just never step in it.

**Disposition.** A guarded, never-raising contract-conformance cast HAS BEEN
LANDED (cycle 2, commit `ef3bd4ef`) in `__GetEnvironmentObject` so that its
docstring's `Returns: IPhEnvironment` is true on every entry path, and so
that it matches its immediate neighbour in the same file. This is recorded
as **contract conformance, not a bug fix** -- it has no measured behavioural
effect and we are not claiming one. The two callers are now covered by a
live regression fence (`tests/operations/test_260_env_resolver_hvo_gate.py`),
which was green before the cast and STAYED green after it, re-verified LIVE
(P9 HELD, `evidence/live-T3-p9-p10.md`) -- including the identity hazard
that casting mints a new pythonnet wrapper, which could in principle have
broken `RemovePhoneEnv`'s `if env in allomorph.PhoneEnvRC` membership test.
It did not. That file's header records explicitly what it does and does not
prove.

### What this investigation turned up, and has now fixed: the real `IPhEnvironment` defect was one file over

`Grammar/EnvironmentOperations.py:648`, `__ResolveObject`, was the **same
uncast shape for the same interface** -- and unlike `AllomorphOperations`,
its callers do exactly the thing that breaks. **This has now been fixed**
(cycle 2, commit `79d8dc34`), live-verified RED-then-GREEN:

- `GetName` (:258) reads `env.Name.get_String(...)`; `SetName` (:304) writes
  it -- FIXED, P6 GREEN.
- `GetStringRepresentation` (:365) reads `env.StringRepresentation.Text`;
  `SetStringRepresentation` (:428) writes it -- FIXED, P6 GREEN.
- `GetSyncableProperties` (:700) does `getattr(env, prop_name)` over
  `Name` / `Description` / `StringRepresentation` -- FIXED, P6b GREEN. This
  is the one that mattered most: it sits on the cross-project sync path.

Nine call sites total, zero test coverage before this cycle; five of the
nine are now live-gated and fixed
(`tests/operations/test_260_environment_resolver_gate.py`).

**`GetLeftContextPattern` / `GetRightContextPattern` are NOT fixed by this
cast, and the cast does not touch their defect at all.** See Part 3 below --
a separate, more fundamental bug was discovered investigating them. The
silent-`None` pair remains the worst of the set: no exception, no
traceback, nothing for log triage to ever find -- which is why it survived
while the loud `AttributeError` twin in this
issue was reported within a day. It is now tracked as its own bug -- see
Part 3 -- rather than being folded into this cast fix, which does not
touch it.

### Part 3 -- discovered investigating `GetLeftContextPattern`: a separate, pre-existing bug (recommend a NEW issue, not part of #260)

Building a live fixture for `GetLeftContextPattern` surfaced something the
"missing cast" framing did not predict: **`LeftContextOA` / `RightContextOA`
do not exist anywhere in the LCM API for `IPhEnvironment`.** Confirmed live
via .NET reflection
(`clr.GetClrType(IPhEnvironment).GetProperties()`): both the interface and
its sole concrete implementation (`PhEnvironment`) declare only
`LeftContextRA` / `RightContextRA` (**Reference** Atomic). Attempting to
read the nonexistent name off a freshly-cast object raises
`AttributeError: 'IPhEnvironment' object has no attribute 'LeftContextOA'.
Did you mean: 'LeftContextRA'?` -- pythonnet's own suggestion names the fix.

`GetLeftContextPattern`, `GetRightContextPattern`, and `Duplicate`'s
deep-copy block all read the wrong name, so they return `None` / copy
nothing for **every** environment, cast or not -- the cast landed in this
cycle changes nothing here, because there is nothing for a cast to reach;
the property being read simply is not real. (The reason an already-typed
object briefly appeared to "hold" a value assigned to `.LeftContextOA` in
an early version of this cycle's fixture is a pythonnet quirk, not a real
read: assigning an attribute name that is not a genuine CLR member on an
un-narrowed wrapper silently creates a dynamic Python instance attribute
that vanishes on any fresh wrapper of the same object.)

This is a genuine, live-reproducible bug, but it is a **different bug
shape** than #260 (wrong property name, not a missing cast) and is
**out of scope for this cast-only task**. Recommend filing it as its own
new issue, with `tests/operations/test_260_environment_resolver_gate.py::
TestP7DiscoveredWrongPropertyName` as the live anchor. Do not fold it into
#260's closure.

### Note for future sweepers

This issue is a clean worked example of a distinction that matters for the
whole missing-cast defect family: **"uncast resolver" is a contract mismatch,
and only some contract mismatches are bugs.** The discriminator is not whether
the resolver casts, and not whether it validates its input -- it is whether any
caller performs Python attribute access (or `hasattr`) on the resolved object
for a member that is not on `ICmObject`. Same interface, same resolver shape,
one harmless instance and one severe instance, in adjacent files. Counting
uncast resolvers therefore over-counts defects, so sweep scoping has to be done
on the caller-usage axis.

Related: the `DataNotebookOperations.__GetRecordObject` twin named in the issue
body is tracked as flexicon#261 (a different bug shape -- wrong lookup API, not
a missing cast). A broader caller-usage re-triage of the remaining uncast
resolvers is scheduled separately; no sweep issues are being filed until that
re-triage is done, precisely because of the over-counting problem above.

---

## Reviewer notes (not part of the comment)

- Evidence: `specs/260-environment-resolver-cast/evidence/live-T1-reflection.md`,
  `.../live-T2-p2-falsification.md` (cycle 1), and
  `.../live-T2-red-p6-p6b-p7.md`, `.../live-T2-green-p6-p6b-p8.md`,
  `.../live-T3-p9-p10.md` (cycle 2).
- Adjudication: `specs/260-environment-resolver-cast/STATUS.md` (cycle-1
  ruling) and `reviews/cycle2-programmer.md` (cycle-2 adjudication of
  P6/P6b/P7/P8/P9/P10/P11).
- Prediction ledger: `specs/260-environment-resolver-cast/predictions.md`
  (cycle 1: P1 HELD, **P2 FALSIFIED**, P3 HELD, P4 UNMEASURED, P5 HELD;
  cycle 2: P6 HELD, P6b HELD, **P7 FALSIFIED** -- the cast does not fix
  `GetLeftContextPattern`, a different bug does that (Part 3) -- P8
  partially held (LeftContext leg excluded), P9 HELD, P10 HELD, P11 to be
  confirmed by the offline run).
- `spec.md` contains one inherited error, corrected above and left in place as
  the historical record: it transferred Part 1's "the observed failure came from
  an OBJECT input, so merge the branches" reasoning onto the *environment* half,
  where no failure was ever observed. The branch-merge argument is sound for
  Part 1 (and T8 did merge them); it was never evidence about Part 2.
- The "three-birds convergence" in `spec.md` is now fully realised: the gate
  test provides real, NON-VACUOUS coverage for `AddPhoneEnv` and
  `RemovePhoneEnv` on BOTH the allomorph-HVO and environment-HVO paths
  (flexicon#268's set) -- P10 measured `hasattr(bare_allo, "PhoneEnvRC") ==
  False` live, so `TestHvoPathBothIntCastAddPhoneEnv` /
  `...Remove...` were added rather than withdrawing the claim. It remains
  true that this coverage is not evidence a cast was behaviourally required
  at these two call sites (it wasn't -- P2 stays falsified); it is evidence
  the coverage gap flexicon#268 named is closed.
- Recommended issue action, now that T2/T3 have landed and P9 is verified
  live: **close #260** (both halves: the `AllomorphOperations` contract fix
  and the `EnvironmentOperations` behavioural fix). Two follow-on issues,
  NEITHER folded into #260:
  1. The Class-A caller-usage re-triage (STATUS.md; unaffected by this
     cycle, scheduled separately).
  2. NEW -- the `LeftContextOA`/`RightContextOA` wrong-property-name bug in
     `EnvironmentOperations.GetLeftContextPattern` / `GetRightContextPattern`
     / `Duplicate` (Part 3 above). This is NOT the same defect as #260 (wrong
     name, not a missing cast) and needs its own issue so it is searchable on
     its own terms, same reasoning as keeping the original silent-`None`
     defect out of #260 when it was still (mis-)attributed to the cast.
