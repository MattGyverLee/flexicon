# tasks

## Cycle 1 (complete)

- [x] T1: `__GetEnvironmentObject` investigated + live-gated -- **cast NOT applied**
  - [x] LCM reflection recorded (evidence/live-T1-reflection.md)
  - [x] RED test committed before any fix (test file + evidence)
  - [x] **P2 FALSIFIED live** -- pre-fix baseline is GREEN at both call
        sites. `PhoneEnvRC.Add`/`.Remove` bind a bare `ICmObject` because
        the CLR resolves the argument on the object's runtime type. The
        T8 axis (pythonnet static-wrapper gate on Python *attribute*
        access) is not reached here.
  - [x] Live verification against target_sandbox (`run_mode: live`)
  - [x] Offline regression run, P5 adjudicated (439/2/528)
  - [x] IMoForm unused-import ruling -- removed (254d0ae)
- [x] T1a: Class A/B/C/D inventory of object-resolution helpers (archivist)

### Cycle 1 lead adjudication

P1 HELD, P2 FALSIFIED (real, non-vacuous -- verified independently),
P3 HELD, P4 UNMEASURED, P5 HELD.

Ruling: the falsification kills the claim "this cast fixes a bug" at
AllomorphOperations' two call sites. It does **not** kill "this resolver
violates its documented contract", and it does not clear `IPhEnvironment`
as an interface -- the genuine behavioural defect is one file over, in
`EnvironmentOperations.__ResolveObject`.

Ruling on the gate test (`test_260_env_resolver_hvo_gate.py`): it
**STAYS**, re-labelled as a regression fence rather than a cast gate.
The cycle-16/17 rule (never pin a defect green as expected behaviour)
does not bite: there is no defect at these two call sites to pin. What
the test pins is a genuinely correct behaviour -- int-HVO write-through
on `AddPhoneEnv`/`RemovePhoneEnv`, fresh-refetch verified -- for two
methods that had zero live coverage. Deleting it would discard the only
artifact that makes the falsification reproducible.

- [x] T1b: gate-test header corrected in place (lead, docs-only). The
      header asserted P2 as fact ("per P2 that reference-collection call
      does not bind to a bare ICmObject") -- the exact false-marker
      hazard flagged in STATUS.md, in the file most likely to be cited
      as evidence. Replaced with a CYCLE-1 CORRECTION block and an
      explicit PROVES / DOES NOT PROVE section, and the two inline
      assertion messages re-worded off "the cast under test" onto "the
      HVO entry path under test". Comment-only; `ast.parse` clean,
      collect-only still reports exactly 2 tests (P5's N=2 intact).
- [x] T1c: #260 closure comment drafted for USER review at
      `reviews/DRAFT-260-closure-comment.md`. NOT posted; no GitHub
      action taken. Marked do-not-post until T3 lands.

## Cycle 2 (open)

- [ ] T2: `EnvironmentOperations.__ResolveObject` (Grammar/, :648-659)
      -- **the real defect**. Uncast, 9 call sites (lead-verified by
      grep: :214, :255, :298, :362, :422, :478, :534, :589, :688).
      Direct Python attribute access at :258 `env.Name.get_String`,
      :304 `env.Name.set_String`, :365 `env.StringRepresentation.Text`,
      :428 `env.StringRepresentation =`, and -- **third site, found by
      the lead this cycle, not in the cycle-1 report** -- :700
      `getattr(env, prop_name)` looping over `Name` / `Description` /
      `StringRepresentation` inside `GetSyncableProperties`.
      `hasattr`-gated silent-`None` at :481 `LeftContextOA` and :537
      `RightContextOA`. Zero test coverage of any kind. RED-first live
      gate required (P6, P6b, P7, P8).
- [ ] T3: `AllomorphOperations.__GetEnvironmentObject` -- land the
      guarded contract-conformance cast (int/object branches merged),
      docstring stating what is actually guaranteed plus an explicit
      note that no behavioural falsifier exists at the current call
      sites. Must NOT be presented as a verified bug fix.
      **P1 makes the shape trivial**: exactly one implementing type, so
      a `ClassName == "PhEnvironment"` guard then `IPhEnvironment(obj)`,
      never raising, one branch covering both inputs.
      **Identity hazard -- do not skip.** `RemovePhoneEnv` does
      `if env in allomorph.PhoneEnvRC` before `.Remove(env)`. Casting
      mints a new pythonnet wrapper over the same CLR object, so the
      `in` test and `.Remove` now depend on .NET equality of a
      re-wrapped object. That is precisely why P9 exists and why it must
      be re-run **LIVE**, not merely offline: an offline pass cannot see
      a `PhoneEnvRC` membership change. If either gate test flips, the
      cast comes straight back out and cycle 1's falsification is
      re-opened.
- [ ] T4: strengthen `test_260_env_resolver_hvo_gate.py` to exercise the
      *allomorph* HVO path non-vacuously (measure
      `hasattr(bare_allo, "PhoneEnvRC")` first, then branch) so the
      flexicon#268 coverage claim is either made true or withdrawn.
- [ ] T5: correct the false docstring claim in
      `Lexicon/MSAOperations.py` (~:1126) that
      `__GetNaturalClassObject`/`__GetPhonemeObject` are "C2 fix sites".
      They are uncast. A false "already fixed" marker is a landmine for
      the next sweeper.

## Deferred to a later spurt (ruled, not scheduled here)

- Class-A re-triage on the **caller-usage** axis (see STATUS.md). Must
  run before ANY sweep issue is filed.
