# cycle1-programmer.md -- issue #260 half two, __GetEnvironmentObject

## Status: BLOCKED on lead ruling -- cast NOT applied

## Reflection result (STEP 1) and shape chosen

Live reflection against `target_sandbox` (see
`evidence/live-T1-reflection.md`):

- `clr.GetClrType(IPhEnvironment).Assembly.GetTypes()` filtered by
  `IsAssignableFrom` finds exactly ONE implementing type in the whole
  `SIL.LCModel` assembly: `SIL.LCModel.DomainImpl.PhEnvironment`.
- A real environment created via `EnvironmentOperations.Create`
  reports `ClassName == "PhEnvironment"`, both on the live object and
  on a bare `sandbox.Object(hvo)` re-fetch.
- `hasattr(bare, "StringRepresentation")` and `hasattr(bare, "Name")`
  are both `False` on the bare view -- P3's trap holds.

**P1 HELD.** IPhEnvironment has no concrete subtype hierarchy (unlike
`IMoForm`'s `MoStemAllomorph`/`MoAffixAllomorph` split). The shape
chosen (per the lead's stated expectation given P1 HELD) would be a
guarded, never-raising, ONE-branch `ClassName` check merging the
int/object branches -- not the sibling's two-branch dance (nothing to
discriminate between) and not an unconditional `IPhEnvironment(obj)`
(would newly raise on non-environment inputs the permissive resolver
returns unchanged today). This shape is recorded but **not applied**
-- see below.

## RED-before-GREEN (STEP 2) -- P2 FALSIFIED, no fix applied

Wrote `tests/operations/test_260_env_resolver_hvo_gate.py`, covering
both mutating callers (`AddPhoneEnv`, `RemovePhoneEnv`) via a genuine
Python `int` HVO, with the same `isinstance(hvo, int)` trap and P3
bare-view assertion as the T8 gate, and fresh-refetch discipline for
the post-write check.

Ran against **unmodified** `__GetEnvironmentObject` (confirmed via
`git diff --stat` showing no prior change to
`AllomorphOperations.py`):

```
2 passed, 19 warnings in 4.13s
```

Both `AddPhoneEnv(allomorph, env_hvo_int)` and
`RemovePhoneEnv(allomorph, env_hvo_int)` **succeeded** on the
uncast baseline, and the fresh re-fetch confirmed the write persisted
correctly in both directions. Full command, verbatim
`tests/live_status.json` (`run_mode: "live"`), and the CLR-argument-
binding-vs-Python-attribute-access explanation are in
`evidence/live-T2-p2-falsification.md`.

**P2 FALSIFIED.** `PhoneEnvRC.Add`/`.Remove` bind a bare `ICmObject`
argument successfully -- the CLR resolves the method argument against
the object's actual runtime type (which does implement
`IPhEnvironment`), unlike direct Python attribute access (pythonnet's
static wrapper type gate, the T8 axis), which is what actually broke
for `Form`/`MsEnvFeaturesOA` on the sibling resolver.

Per `standing_rule_empty_falsifier_set_is_not_a_pass` and the prompt's
explicit "IF P2 IS FALSIFIED" branch: **this cast has no behavioral
falsifier at its two call sites.** Reported as exactly that --
**contract/docstring fix; behavioral axis UNMEASURED** -- and stopped
per instruction. No alternate call site was sought, no synthetic
assertion was added to manufacture a RED, and this green run is NOT
reported as evidence the cast was behaviorally needed. **The cast was
deliberately not applied to `AllomorphOperations.py`.** Flagging for a
lead ruling on whether a contract-only (docstring-truth /
defense-in-depth) fix should still land given zero measured behavioral
effect at both known call sites.

## STEP 3 (live verification) -- performed for the RED leg only

The mandated live invocation was run (see command/output above and in
`evidence/live-T2-p2-falsification.md`). Since the fix was not
applied, there is no GREEN leg to report; STEP 3 was scoped by the
prompt's per-prediction requirement, and P2's own falsification is
itself the STEP 3 result for this spurt.

## Per-prediction adjudication

- **P1: HELD.** IPhEnvironment has no concrete subtypes;
  `ClassName == "PhEnvironment"` confirmed live.
- **P2: FALSIFIED.** Pre-fix baseline is GREEN, not RED, at both call
  sites (see mechanism above).
- **P3: HELD.** `hasattr(bare, "StringRepresentation")` is `False` on
  the bare view, confirmed in both the reflection probe and the gate
  test.
- **P4: UNMEASURED** (not HELD, not FALSIFIED) -- the cast this
  prediction is about was never applied, per the P2-falsification
  branch. Cannot be adjudicated until the lead rules on whether to
  land a contract-only fix.
- **P5: HELD.** Offline suite: `439 passed, 2 failed, 528 deselected`
  (526 + N, N=2 new live-marked tests, exactly as pre-committed), red
  set exactly the two foreign `TestPhase2JoinOrOpen` failures. Run
  twice (before and after the IMoForm commit) with identical results.

## IMoForm ruling outcome

Removed. Verified genuinely unused by AST (`ast.Name` walk finds zero
usages of `IMoForm` outside the import statement) and by pyflakes
(`'SIL.LCModel.IMoForm' imported but unused`). Confirmed no re-export:
grepped the whole tree for `from ...AllomorphOperations import
IMoForm` and for any `AllomorphOperations import` site -- every caller
(including `flexicon/__init__.py:169`) imports only the
`AllomorphOperations` class itself, never `IMoForm`. Landed as a
separate commit. (Noted, but left untouched and out of scope: pyflakes
also flags `ILexEntry` as unused on this same file, and `IPhEnvironment`
would become used again if/when the resolver fix lands -- neither was
authorized for this spurt.)

## Commit SHAs, in order

1. `c1055b1` -- `docs(260-environment-resolver-cast): spec + tasks + committed predictions` (spec.md, tasks.md, predictions.md; committed before any live run, per STEP 0).
2. `beaf70d` -- `test(260-environment-resolver-cast): live gate + reflection, P2 FALSIFIED` (test file, live-T1-reflection.md, live-T2-p2-falsification.md).
3. `254d0ae` -- `chore(AllomorphOperations): drop unused IMoForm import` (STEP 5, separate commit).

No fix commit exists for `__GetEnvironmentObject` itself -- that is
the blocker.

## Offline regression numbers

`python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider`
→ `439 passed, 2 failed, 528 deselected` (both before and after the
IMoForm commit). Failing set: exactly
`tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::
test_rollback_flag_set_true_on_exception` and `::test_depth_restored_
on_exception` -- the pre-existing, unrelated foreign failures named in
the baseline. No new offline failures introduced.

## Blocker -- needs lead ruling

P2, the load-bearing behavioral prediction for this spurt, is
falsified: neither `AddPhoneEnv` nor `RemovePhoneEnv` is affected by
the missing cast in `__GetEnvironmentObject`, because both pass the
resolver's return value straight into a strongly-typed .NET reference-
collection method (CLR runtime-type dispatch), never touching a
subtype-only Python attribute the way the T8 sibling defect's callers
did. The three-birds convergence claimed in `spec.md` (this cast
closes #260 part 2 and satisfies #268's zero-live-coverage condition
for `AddPhoneEnv`/`RemovePhoneEnv`) is UNCHANGED as a live-coverage
claim -- the new gate test does add real coverage for both methods --
but it is NOT evidence that a cast was behaviorally required, and I
have not applied one. Needs a ruling on: (a) land the contract-only
cast anyway for docstring-truth/defense-in-depth, or (b) close this
half of #260 as "no behavioral defect found; docstring overpromises a
cast the call sites don't need" without a code change to
`__GetEnvironmentObject`.
