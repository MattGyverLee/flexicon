# STATUS — 254-getmorphtype-allomorph

Repo: flexicon (main). Issue: flexicon#254.

## Where things stand (as of 2026-09-06, spurt 1 / cycle 1 end)

**Checkpoint reached: contract frozen + live ground truth captured.**
No code under `flexicon/code/` has been modified yet. Implementation is the
next spurt.

## What landed this spurt

- **Live ground truth captured** (`run_mode: "live"`, Sena 3 via disposable
  `sena3_sandbox`, 2 passed). `bundle.MorphRA` is always an `IMoForm`
  (`MoStemAllomorph` 697 / `MoAffixAllomorph` 1142), `None` on ~4.8% of 1932
  sampled bundles. The real morph type sits at `MorphRA.MorphTypeRA`, whose
  `Name` must be read via `BestAnalysisAlternative.Text` —
  `get_String(anal_ws)` returned empty for every sample.
  Evidence: `evidence/live-cycle1-probe.md`.
- **The decisive finding:** `SetMorphType(bundle, <IMoMorphType>)` is a
  **hard crash**, not silent corruption — `TypeError: ... MoMorphType value
  cannot be converted to SIL.LCModel.IMoForm`, raised before any mutation
  reaches the LCM. The non-`None` write path has therefore **never once
  succeeded**, so retiring it breaks no working caller and leaves no corrupt
  data in the wild.
- **Write-side twin found** (not in the filed issue): `SetMorphType` at
  `WfiMorphBundleOperations.py:877` assigns into the same wrong field. Must be
  fixed with the getter — a getter-only fix leaves the setter writing an
  `IMoMorphType` into an `IMoForm` slot.
- **Sweep closed the scope question:** 111 files, four passes — the
  `GetMorphType`/`SetMorphType` pair is the whole population of this shape.
  The issue's own sweep hint resolves **negative** (`AllomorphOperations:871`
  and `LexEntryOperations:1443` are already correct).
- **Contract frozen** in `spec.md` (C1-C6), including the two calls that were
  open going into synthesis:
  - `SetMorphType(bundle, None)` — the one path that ever worked — is
    **retired too**, not preserved. It nulled `MorphRA`, i.e. cleared the
    *allomorph* while the docstring claimed it cleared the *type*; the
    identical capability lands on `SetMorph(bundle, None)`. Rationale in
    spec.md C2.
  - **Semver sign-off resolved,** not escalated: ships as BREAKING
    (behavioural) under `### Changed` in `[Unreleased]`, next minor (4.6.0),
    no deprecation window — matching the `OpenProject(undoable=)` default flip
    and #232 precedents. Only `GetMorphType`'s return-type flip has real
    back-compat surface.
- **Docstring rewrite folded into the fix, not deferred** (user addendum): the
  shipped `SetMorphType` Example (L845-849) tells callers to pass an
  `IMoMorphType` pulled from `MorphTypesOA.PossibilitiesOS`, so the published
  documentation *is* the crash vector. `Args:`/`Notes:`/`See Also:` all lie in
  mutually-consistent ways, which is why a set-then-get round-trip
  self-confirms.

## Next pickup

Implement C1-C5 in `flexicon/code/TextsWords/WfiMorphBundleOperations.py`,
then live-verify on the **Target** via the disposable `target_sandbox` fixture
(write path, nothing leaks, no `restore_target.py` needed — so no destructive
live write and no human gate). Fold in the one-call `InflClassRA` reflection
probe while the session is open; if it confirms the field is absent on
`IWfiMorphBundle`, **file a separate issue** rather than extending this diff.

Uncommitted at spurt end: `tests/operations/test_issue254_morphra_probe.py`
(the cycle-1 probe) plus this spec dir.
