# STATUS -- feature-structure-sync-gap

Repo: flexicon (main). Issues: flexicon#251, #252, #256, and **#253 (folded in)**.

## Where things stand (as of 2026-09-07, spurt 2 / cycle 3 end)

**Checkpoint 2a reached: T1-T3 landed, verification-gated PASS, committed.**
Checkpoints were re-cut in cycle 3: **2a = T1-T3** (additive helpers, zero
runtime delta) and **2b = T4-T5** (re-point NC/Phoneme onto the shared helper +
`MakeFeatStruc` generalization). Next spurt targets **Checkpoint 2b**.

> **State-reconciliation note (lead, spurt 3 entry).** This file and
> `.crew-handoff.json` were left describing spurt 1 / cycle 1 while cycles 2 and
> 3 had in fact landed and committed. Corrected here from the committed
> evidence. `spec.md`'s T2/T3 checkboxes were likewise unticked and are now
> ticked. **Cause: two spurts ended without the lead's handoff-write step.** The
> loop's memory is these three files plus git; when they drift, the next spurt
> re-plans work that is already done. Do not end a spurt without updating them.

## What landed in spurt 2 (cycles 2-3)

- **T1 DONE** (commit `1790fcc`) -- `lcm_casting._interface_cache` gained the
  **12 registrable** feature-struct owner entries (corrected from 13:
  `IPosFeatures` does not exist and is hardcoded to `None`, the
  `IPhReduplicationRule` precedent). Full `cast_to_concrete`/`_GetTypedOwner`
  caller-delta table produced. Gate PASS (`reviews/cycle2-verification-T1.md`):
  offline 1277 -> 1277 identical; live only status change is the new T1 test
  FAIL->PASS. Anti-trap audit confirmed the test casts a re-fetched bare
  `project.Object(hvo)`, not a factory-fresh object.
- **T2 + T3 DONE** (commit `cfc86af`) -- `BaseOperations._ResolveFeatureStrucOwner`,
  `_GetFeatureStruc` (recursive C4 serializer), `_ResolveFsByGuid`. The C1 table
  lives in exactly ONE place: `Shared/lcm_constants.py::FEATURE_STRUC_OWNER_TABLE`.
  Purely additive -- all 7 named Operations files byte-unchanged. Gate PASS
  (`reviews/cycle3-verification-T2-T3.md`): offline 1277 -> 1290, live new-file
  16 passed, zero-delta set 9 passed identical both sides. Verification ran a
  **mutation test** (deleted the cast) and 12/16 live tests failed, proving the
  suite exercises real code rather than a tautology.
- **Contract amended in cycle 3** -- new **C4a** (`_ApplyFeatureStruc` must
  accept BOTH the C4 recursive dict and the shipped legacy flat list) and
  **C4b** (NC/Phoneme *capture* stays legacy; migration is the new task **T9b**).
  Two concurrent wire formats is the accepted interim state.
- **Open measurement closed:** Ngoreme live shows NC complex=0/closed=76 and
  Phoneme complex=0/closed=779 -- **zero nesting across 855 specs**. This
  confirms the code comments' closed-only assumption and **lowers T9b's
  priority** relative to MSA's 99.7%-nested finding.
- **Known pre-existing failure, NOT ours:**
  `test_apply_raises_on_type_mismatch_segments_target` fails identically before
  and after every change so far (`AttributeError: 'ICmObject' object has no
  attribute 'Name'`, `NaturalClassOperations.py:1270`). It is a C2/HVO-cast
  symptom and should fall out of **T10**; do not re-diagnose it as a regression.

## What landed in spurt 1 (cycle 1)

- **Live ground truth captured** (`run_mode: "live"`, 8/8 passed, Ngoreme FLEx
  read-only + disposable `target_sandbox`; the real Target was never opened and
  both `.fwdata` mtimes predate the run). Evidence:
  `evidence/live-cycle1-probe.md`. Harness:
  `tests/operations/test_issue251_252_256_feature_struct_probe.py`.
- **The three diagnoses are NOT the same bug**, and the probe measured the
  difference:
  - **#251 (MSA)** is the classic pythonnet trap -- `hasattr` is False for
    **0 True / 2088 False** live MSAs via the base-interface view. A
    `hasattr`-gated fix would be 100% dead code (the f424f99 / 3abf6b5 mistake,
    for the third time).
  - **#252 (POS)** is a **pure coverage gap** -- `POSOperations.GetAll()`
    already casts, so `hasattr` is True 26/26. Nothing is being cast wrong;
    the two properties are simply never emitted.
  - **#256 (`MakeFeatStruc`)** is neither -- it fails even for a *concrete*
    MSA because `owner.FeaturesOA` is the **wrong property name** for every MSA
    type. Not a casting bug at all.
  A single copy-paste fix across all three would be wrong in two directions.
- **Nesting is the majority shape, not an edge case:** 799 nested vs 21 flat of
  820 non-null structs. The observed Bantu shape has a **null outer `TypeRA`
  and a non-null inner one**, so `TypeRA` handling is per-level.
- **8 uncaptured feature-struct owners found beyond the filed issues** (MSA x4,
  POS x2, `IMoAffixAllomorph.MsEnvFeaturesOA`, `IWfiAnalysis.MsFeaturesOA`).
  `"Allomorph"` and `"POS"` are both live sync object types
  (`flexicon/sync/engine.py:441`/`:445`), so that data loss **ships today**.
- **The root enabler was identified:** `lcm_casting._interface_cache` contains
  **no** feature-structure owner class, which is why `cast_to_concrete` returns
  those objects unchanged and why the #133 fix at
  `InflectionFeatureOperations.py:493` still silently does nothing.
- **Contract frozen** in `spec.md` (C1-C8) with the five lead rulings:
  - **#253 is IN** -- both specialists converged, and Explore's Deliverable 4
    proved the two `__ApplyFeatures` bodies differ on exactly four *parameters*,
    which met the stated flip condition. Split into a behaviour-preserving
    refactor (T4) and a **separately committed** policy flip (T9) with a
    BREAKING (behavioural) `### Changed` CHANGELOG entry, next minor -- the
    #254 precedent. `on_unresolved="skip"` survives as an explicit opt-in.
  - **Newly-found P0s:** `MsEnvFeaturesOA`, `PhonemeOperations.py:1431`
    (truthiness gate) and `:1351` (HVO-path omission) all join **this** feature
    -- the last two must land together or neither is testable. `IWfiAnalysis`,
    `FeatureDisjunctionsOC`, annotation/ScrNote `FeaturesOA`,
    `EtymologyOperations:548` and the `_apply_props_loop` dict hazard are OUT
    as new issues (filing needs the user's approval). NC's `SegmentsRC` gates
    are appended to `specs/233-basetype-cast-sweep/spec.md` instead of
    double-filed.
  - **`_interface_cache` is fixed here and is Task 1**, with a mandatory
    caller-delta enumeration because adding entries changes `cast_to_concrete`
    behaviour for existing callers.
  - **Surface: recursive dict, tuple overload rejected.** The flat
    list-of-tuples is a hard back-compat requirement -- 5 internal call sites
    and 4 shipped tests pass it.
  - **Nested read-side traversal was upgraded to P0** and pulled in: capture
    without it would drop the majority shape and make writes asymmetric with
    reads.

## Lead corrections to the specialist reports

- lex-domain's owner table marked only `IMoDerivAffMsa` as ambiguous.
  **`IPartOfSpeech` is equally ambiguous** (`DefaultFeaturesOA` *and*
  `InherFeatValOA`) and now carries `slot="Default"`/`"InherFeatVal"` in the
  frozen table.
- The sweep marked `IFsComplexValue.ValueOA` **UNCONFIRMED** because
  `liblcm_baseline.json` has no entry for the type; the live probe observed it
  directly. **Ruled CONFIRMED** -- live evidence outranks a stale snapshot, and
  the snapshot gap is logged as a P2 tooling follow-up.
- Reporter's MSA stem count (1949) corrected to **1951**.

## Next pickup

`spec.md` section 5, **Checkpoint 2b**, and the same one-task-at-a-time
discipline that worked for T1:

1. **T4 ALONE** -- extract `BaseOperations._ApplyFeatureStruc` (C5/C6/C7 +
   **C4a** dual wire shape) and re-point NC (`on_unresolved="raise"`) and
   Phoneme (`"skip"`) at it. **Zero RUNTIME delta.** The E5 hazard is the whole
   difficulty: `tests/operations/test_natural_class_feature_sync.py:77-160`
   holds `inspect.getsource` shape assertions against
   `_NaturalClassOperations__ApplyFeatures`, one of which does
   `src.index("feat_obj = self.__ResolveByGuid")` and raises `ValueError` the
   moment that literal moves. They must be **migrated 1:1** onto
   `BaseOperations._ApplyFeatureStruc` and enumerated assertion-by-assertion in
   the T4 report. Deleting or weakening any one is a QC rejection.
2. **T5** -- one generalized `MakeFeatStruc` (C3); Infl and Phon become
   call-throughs. Closes **#256**.

## Sequencing ruling on #250 (lead, spurt 3)

**#250 does NOT run in parallel.** It gets its own spec + spurt once this
feature reaches `feature_complete`. Full rationale in the spurt-3 lead ruling;
the four binding reasons:

1. **Shared strictening site.** #250's Defect 3 is the silent `continue` at
   `BaseOperations.py:360-364` -- the *same* line C6 exists to route around.
   C6's anti-regression test must be in place across T6/T7/T8 **before** #250
   makes that drop loud, or a forgotten `pop` will surface as a misattributed
   writing-system error instead of the missing-feature-struct error it is.
2. **Shared write path under live evidence.** #250 changes what
   `target_ws_by_id` (`BaseOperations.py:1306-1308`) is built from and how it is
   keyed. That dict feeds **every** `ApplySyncableProperties` in the repo,
   including the five new ones T6-T8 add. Mutating it mid-feature would
   invalidate FS live evidence already captured under the old semantics.
3. **Live Target contention.** Both need `FLEXLIBS_REQUIRE_LIVE=1` against the
   single Target/`target_sandbox`.
4. **#250 is not a bug fix, it is a contract decision.** `Exists`'s docstring
   and body disagree; fixing either side is defensible and they have opposite
   blast radii. That needs its own freeze cycle.

Carry forward into #250's spec when it opens: **Defect 4 (case-normalization
divergence, `en-US` vs `en-us`) is NOT latent** -- it fires today with no
special project state -- and is separable from latent Defects 1-3.

## Process notes

- `Explore` and `lex-domain` have **no `Write` tool**. Cycle-1 reports were
  persisted by the main session on their behalf. Until those roles get write
  access to `specs/<feature>/reviews/`, **route report-writing through a
  write-capable agent** (`lex-programmer`, `lex-archivist`, `lex-doc`,
  `lex-logscan`) or the path-relay discipline breaks.
- `CLAUDE.md` is stale: it says `flexlibs2/code/`; the package is
  `flexicon/code/`. Fixed as T16 (docs-only).
- Cycle 3 disclosed an incident: a misdirected `git checkout --` briefly
  discarded uncommitted `BaseOperations.py`, recovered byte-exact from a
  dangling stash blob. **Commit before stash-based baselining.**
