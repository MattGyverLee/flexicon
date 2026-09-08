# DRAFT closure comment for flexicon#260 -- FOR USER REVIEW, NOT POSTED

**Status: DRAFT. No GitHub action has been taken.** Nothing below has been
posted, and #260 has not been labelled or closed. Closure routes through the
main session and the user.

**Do not post yet.** The "Part 2" section below asserts that the
contract-conformance cast has landed. It has NOT -- that is cycle-2 task T3.
Post only after T3 lands and P9 (the two existing gate tests stay green and
unchanged) is verified live. If T3's outcome differs, rewrite Part 2 first.

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

**Disposition.** A guarded, never-raising contract-conformance cast has been
landed in `__GetEnvironmentObject` so that its docstring's
`Returns: IPhEnvironment` is true on every entry path, and so that it matches
its immediate neighbour in the same file. This is recorded as **contract
conformance, not a bug fix** -- it has no measured behavioural effect and we
are not claiming one. The two callers are now covered by a live regression
fence (`tests/operations/test_260_env_resolver_hvo_gate.py`), which was green
before the cast and is required to stay green after it; that file's header
records explicitly what it does and does not prove.

### What this investigation did turn up: the real `IPhEnvironment` defect is one file over

`Grammar/EnvironmentOperations.py:648`, `__ResolveObject`, is the **same uncast
shape for the same interface** -- and unlike `AllomorphOperations`, its callers
do exactly the thing that breaks:

- `GetName` (:258) reads `env.Name.get_String(...)`; `SetName` (:304) writes it
- `GetStringRepresentation` (:365) reads `env.StringRepresentation.Text`;
  `SetStringRepresentation` (:428) writes it
- `GetSyncableProperties` (:688) does `getattr(env, prop_name)` over
  `Name` / `Description` / `StringRepresentation`
- `GetLeftContext` (:481) and `GetRightContext` (:537) are `hasattr`-gated and
  therefore **silently return `None`** instead of raising

Nine call sites, zero test coverage of any kind. The silent-`None` pair is the
worst of the set: no exception, no traceback, nothing for log triage to ever
find -- which is why it survived while the loud `AttributeError` twin in this
issue was reported within a day. It is being fixed RED-first with a live gate.

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

- Evidence: `specs/260-environment-resolver-cast/evidence/live-T1-reflection.md`
  and `.../live-T2-p2-falsification.md`.
- Adjudication: `specs/260-environment-resolver-cast/STATUS.md`, cycle-1 ruling.
- Prediction ledger: `specs/260-environment-resolver-cast/predictions.md`
  (P1 HELD, **P2 FALSIFIED**, P3 HELD, P4 UNMEASURED, P5 HELD).
- `spec.md` contains one inherited error, corrected above and left in place as
  the historical record: it transferred Part 1's "the observed failure came from
  an OBJECT input, so merge the branches" reasoning onto the *environment* half,
  where no failure was ever observed. The branch-merge argument is sound for
  Part 1 (and T8 did merge them); it was never evidence about Part 2.
- The "three-birds convergence" in `spec.md` survives only in its
  live-coverage sense: the new gate does add real coverage for `AddPhoneEnv`
  and `RemovePhoneEnv` (flexicon#268's set). It is not evidence that a cast was
  behaviourally required. Whether that coverage is non-vacuous on the
  *allomorph* HVO path is still unmeasured -- see prediction P10 (task T4). If
  P10 measures `hasattr(bare_allo, "PhoneEnvRC") == True`, the #268 claim must
  be **withdrawn**, not patched, and this comment's coverage sentence edited
  before posting.
- Recommended issue action once T3 lands: **close #260**. Do NOT fold the
  `EnvironmentOperations.__ResolveObject` defect into this issue -- it needs its
  own issue so its silent-`None` variant is searchable on its own terms.
