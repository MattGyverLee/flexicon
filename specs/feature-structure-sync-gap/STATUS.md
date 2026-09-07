# STATUS -- feature-structure-sync-gap

Repo: flexicon (main). Issues: flexicon#251, #252, #256, and **#253 (folded in)**.

## Where things stand (as of 2026-09-07, spurt 3 / cycle 4 end)

**T4 landed and gated PASS. Checkpoint 2b is HALF closed -- T5 remains.**
Next spurt is **T5 alone**, and only then does the #250 Defect 4 window open.

### Cycle-4 lead rulings (three)

**Ruling 1 -- Checkpoint 2b is T4 AND T5; T4's gate did not close it.**
Cycle 4's PASS was T4's *task* gate. `spec.md` (re-cut in cycle 3) defines
Checkpoint 2b as T4-T5. This matters because
`specs/250-writingsystem-activation/spec.md` section 6.3 condition 3 makes the
Defect 4 micro-spurt conditional on "Checkpoint 2b's gate has cleared and is
committed, so `BaseOperations.py` has no uncommitted FS work in it" -- and T5
puts the single generalized `MakeFeatStruc` into exactly that file. So the
window is **queued, not open**: T5 first, Defect 4 second, T6 third. Both the
letter and the stated purpose of that condition point the same way, and cycle 3
already came within one `git checkout --` of losing an uncommitted
`BaseOperations.py`. Serialising costs one spurt and removes the whole class of
risk.

**Ruling 2 -- the SLDR crash does NOT block cycle 5, and the fix is NOT the
answer to it. The answer is procedural, costs nothing, and is adopted now.**

The reported crash is real: `tests/conftest.py:135` calls `Sldr.Initialize(True)`
unguarded while the production path it bootstraps
(`flexicon/code/FLExInit.py:66-71`) wraps the identical call in `try/except` +
warning. Pre-existing identically at `a26d39c`, orthogonal to T4.

**But it is not the main cause of the divergence, and I nearly mis-ruled it.**
There is a THIRD measurement of the same offline suite at effectively the same
commit, from the other crew's `reviews/cycle2-baseline.md`:

| Who | Result |
|---|---|
| T4 implementer (disposable worktree) | 1494 -> **1495 passed**, 0 failed, 627 deselected |
| Cycle-4 gate | **225 passed, 1273 errors** |
| Other crew, committed HEAD | **1292 passed, 3 failed, 498 deselected, 0 errors** |

**Two of three were clean**, so "the suite is broken" is the wrong conclusion.
And `deselected` of 627 vs 498 proves the three runs did not even *collect the
same set* -- no `conftest.py` guard could have made those numbers agree. The
dominant variable is an **unpinned invocation** (rootdir, `-m` filter, worktree
vs clone, stale `__pycache__`, whether SLDR was already initialised in that
shell); SLDR order-dependence sits underneath it.

Consequences:

- **Cycle 5 is unblocked immediately** by adopting **spec.md section 5.1**
  (new): *measure a DELTA between your own two runs in the same shell; an
  absolute offline pass count is not evidence.* Zero cost, no code, no waiting.
  The other crew derived the same rule independently against this repo --
  convergent, which is the strongest kind of confirmation available here.
- **T18 (the conftest guard) is DEFERRED and does NOT gate T5.**
  `tests/conftest.py` is a **shared harness neither crew owns**; the other crew
  is measuring deltas against it and their protocol tells them to **STOP and
  report** if a fourth failure appears. Perturbing their baseline to tidy ours
  is not a trade we get to make unilaterally. It lands when only one crew is
  active, or via a coordinated `needs_human` window.
- **`flexicon#264` is FILED** (user-approved):
  https://github.com/MattGyverLee/flexicon/issues/264 -- "Unguarded
  `Sldr.Initialize` in `tests/conftest.py` makes the offline suite
  order-dependent, invalidating before/after test-count comparisons". T18 is
  that issue. **Add to it:** the marker asymmetry is **11 unmarked modules**,
  not one -- all of `flexicon/sync/tests/` except `test_duplicate_operations.py`,
  plus `flexicon/tests/test_FLExInit.py` and `test_FLExProject.py`; only **2**
  modules in those two trees set `pytestmark`.
- **This is also why `#264` is not a prerequisite for T5.** The bare offline
  command collects those 11 live-requiring modules, so the count is invalid on
  its own terms; the conftest guard alone would not repair it (marker hygiene is
  `#264`'s separate suggested-fix item 2). **T5's comparator is frozen in
  spec.md section 5.1** -- live subset both sides (primary), a pinned offline
  subset measured as a delta (secondary), a determinism check that reports
  `FAIL: unfalsifiable` rather than a bare count, and a **mutation test**, which
  is what actually makes a zero-delta claim falsifiable. The offline count never
  was the falsifier; cycles 3 and 4 both proved the mutation test is.

**Ruling 3 -- the `flexlibs2` -> `flexicon` rename did NOT invalidate spec.md's
line numbers; no refresh pass is needed, and symbol/literal anchoring stays the
standing discipline.** Measured, not assumed: `git show ec54432 --numstat` on
the five files this feature touches is `14/14`, `1/1`, `1/1`, `1/1`, `1/1` --
pure line-for-line import-string substitution, **zero net line-count change**.
The files moved directories; nothing inside them shifted. spec.md's paths were
already `flexicon/...` (its only four `flexlibs2` mentions are T16's own
description of the CLAUDE.md staleness).

The drift that *does* exist is **T4's own**, and it is small: Phoneme `:1431` is
still the `if features:` truthiness gate, `__ApplyBasicIPASymbol`'s WS map moved
to `:1441`. T4 removed `__ResolveByGuid` from both files, so anything below it
shifted up. **Standing rule (already frozen as `specs/250-writingsystem-activation/spec.md`
section 6.1): anchor on symbols and literals, confirm each anchor is unique in
the file before editing, and report the line numbers actually found.** That is
sufficient; a refresh pass would burn a cycle re-deriving numbers that the next
task invalidates again.

**Beware the stale duplicate tree:** `build/lib/flexicon/...` is an untracked
build artifact containing a full second copy of the package. It pollutes every
repo-wide `grep`. Search `flexicon/` explicitly, never bare `.`.

## What landed in spurt 3 (cycle 4)

- **T4 DONE** (`4aca74a` production, `61e0f87` live tests, `e17cd7d` evidence).
  `BaseOperations._ApplyFeatureStruc` + `_ApplyFeatureStrucSpecMap` extracted;
  NC re-pointed (`on_unresolved="raise"`), Phoneme re-pointed (`"skip"`); both
  private `__ResolveByGuid` twins de-duplicated onto T3's `_ResolveFsByGuid`;
  Phoneme's dead `fill_gaps` removed. New live file
  `tests/operations/test_apply_feature_struc.py` (7 tests) covers **both** C4a
  wire shapes including one level of nesting -- the first live proof of the
  nested recursion.
- **Gate PASS** (`reviews/cycle4-verification-T4.md`). Zero runtime delta
  measured directly on both sides (34 passed / 1 known failure, identical at
  `a26d39c` and HEAD). E5: 6 assertions re-enumerated independently at the
  parent commit and confirmed migrated 1:1 -- zero deleted, zero weakened. **Two**
  mutation tests (legacy raise-branch; nested-recursion `TypeRA`) each produced
  real failures, then restored `git hash-object`-identical to the committed blob.
- **`monkeypatch` finding worth carrying:** `SIL.LCModel` is a pythonnet CLR
  namespace and **rejects `setattr` outright** (`AttributeError: type does not
  support setting attributes`). Patching the real module is not merely awkward,
  it is impossible. This is why T4 added the three one-line `_CastFs*` seams on
  `BaseOperations` (a plain Python class), matching the pre-existing
  `_TransactionCM`/`_CreateWithGuid` monkeypatch technique. Any future
  fake-object test of LCM-casting code living in `BaseOperations` needs the same
  shape -- do not rediscover this by trial and error.
- **Contract snapshot discipline held:** a wholesale `expected_contract.json`
  regen pulled in ~50 lines of unrelated accumulated drift and was **reverted**
  in favour of a hand-added single entry (`IFsComplexValueFactory`).
  Regenerating wholesale launders unrelated changes into the commit; do not
  do it.
- **Concurrent work on `main`:** the `flexlibs2` -> `flexicon` rename (`ec54432`,
  merged `3d357d8`) and a separate `name-field-whitespace-identity` feature
  (`a3fc8e3`, `361feef`) landed during cycle 4. HEAD is no longer this feature's
  own tip; always re-baseline from `git log`, never from a remembered SHA.

## Where things stood (spurt 2 / cycle 3 end)

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

**T5 alone, one task, one spurt** -- the discipline that worked for T1 and T4.

1. **Adopt spec.md section 5.1 before the first edit** -- record the offline
   counts in the shell you will re-run in, quote the exact command, and report
   only **your own delta**. T18 is deferred and is NOT a prerequisite; do not
   touch `tests/conftest.py` this spurt.
2. **T5** -- one generalized `MakeFeatStruc` (C3); Infl
   (`InflectionFeatureOperations.py:970`) and Phon
   (`PhonFeatureOperations.py:553`) become call-throughs; recursive dict +
   flat-list alias + `slot=`. Closes **#256**.

   **The load-bearing insight, from cycle 1's live probe: #256 is NOT a casting
   bug.** `MakeFeatStruc` fails even for a *concrete* MSA because
   `owner.FeaturesOA` is the **wrong property name** for every MSA type. The fix
   is to route owner resolution through T2's `_ResolveFeatureStrucOwner` /
   `Shared/lcm_constants.py::FEATURE_STRUC_OWNER_TABLE`. Adding a cast or a
   `hasattr` gate would be the `f424f99` / `3abf6b5` mistake for the fourth
   time and is a QC rejection.

   **No E5-class hazard here** (verified cycle 4): no `inspect.getsource`
   assertion anywhere in `tests/` targets `MakeFeatStruc`. The real hazard is
   plain back-compat -- 4 production call sites
   (`NaturalClassOperations.py:463/:867/:1034`, `PhonemeOperations.py:1886`) plus
   `PhonFeatureOperations.py:106`'s docstring example, and 4 test files
   (`test_phonemes.py`, `test_phon_features.py`, `test_feature_struc_resolver.py`,
   `test_issue251_252_256_feature_struct_probe.py`). Enumerate the behavioural
   delta between the two existing implementations **before** merging them, the
   way Explore's Deliverable 4 did for `__ApplyFeatures` -- two bodies that look
   like twins are how #253 got its four-parameter divergence.
3. **Then, and only then,** the #250 Defect 4 micro-spurt (see
   `queued_micro_spurts` in `.crew-handoff.json`), then T6.

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

## Concurrency: a second crew shares this working tree (BINDING)

Their protocol is `specs/name-field-whitespace-identity/CONCURRENCY.md`, written
by the main session and confirmed by the project owner as expected. It names
**us** as "the other crew". Read it as reciprocal.

- **Ours (they will not touch):** `flexicon/code/BaseOperations.py`,
  `flexicon/code/Grammar/*`, `specs/feature-structure-sync-gap/`,
  `specs/250-writingsystem-activation/`. They fenced `BaseOperations.py` off for
  themselves on design grounds *before* the concurrency; the concurrency makes it
  absolute.
- **Theirs -- DO NOT TOUCH, DO NOT STAGE, DO NOT REVERT:**
  `flexicon/code/TextsWords/ParagraphOperations.py`,
  `flexicon/code/TextsWords/SegmentOperations.py`,
  `flexicon/code/TextsWords/DiscourseOperations.py`,
  `tests/operations/test_issue242_whitespace_probe.py`,
  `tests/operations/test_name_field_identity_probe.py`,
  `specs/name-field-whitespace-identity/`, `specs/242-paragraph-whitespace/`,
  `specs/tier1-silent-data-loss/`.
- **Shared, owned by neither:** `tests/conftest.py`. This is why T18 is deferred.
- **Staging rule, never relaxed:** always `git add <explicit paths>`. **Never**
  `git add -A`, `git add .`, `git add -u`, or `git commit -a` -- all four would
  sweep their in-flight work into our commit. Run `git status --porcelain` before
  committing and confirm every staged path is one you authored.
- **Never** `git checkout`, `git restore`, `git stash`, or `git reset` a path you
  did not author. Their uncommitted work is unrecoverable if discarded -- and
  cycle 3 already lost (and barely recovered) an uncommitted `BaseOperations.py`
  to exactly this.
- `specs/duplicate-signature-harmonisation/` (untracked) is orphaned evidence
  from already-merged issue #246. It belongs to neither crew. Leave it.
- If you need one of their files: **stop and report `needs_human`.** Do not edit
  it, do not copy code out of it, do not wait for them.

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
