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

## Cycle 2 (open)

- [ ] T2: `EnvironmentOperations.__ResolveObject` (Grammar/, :648-659)
      -- **the real defect**. Uncast, 9 call sites, 5 of which do direct
      Python attribute access (`env.Name`, `env.StringRepresentation`)
      and 2 of which are `hasattr`-gated (`LeftContextOA`,
      `RightContextOA` -> silent `None`). Zero test coverage of any
      kind. RED-first live gate required.
- [ ] T3: `AllomorphOperations.__GetEnvironmentObject` -- land the
      guarded contract-conformance cast (int/object branches merged),
      docstring stating what is actually guaranteed plus an explicit
      note that no behavioural falsifier exists at the current call
      sites. Must NOT be presented as a verified bug fix.
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
