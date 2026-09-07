# STATUS -- feature-structure-sync-gap

Repo: flexicon (main). Issues: flexicon#251, #252, #256, and **#253 (folded in)**.

## Where things stand (as of 2026-09-07, spurt 5 / cycle 6 end)

**CHECKPOINT 2c IS CLOSED.** T14a landed (`b3ba083b`) --
`tests/operations/test_makefeatstruc_c3_live.py`, three
`requires_live_project` tests on `target_sandbox`, `run_mode: live`, 3/3
passed, evidence `evidence/live-T14a.md`. The C3/C4 errata landed
(`6b54059`, five `spec.md` edits). flexicon**#265 is FILED** and open
(user-approved) for the name-operand policy gap. The #256 closure comment is
**drafted and corrected but NOT posted** -- it stays with the user.

**The #250 Defect 4 micro-spurt is DISPATCHED as cycle 7.** All three of
`specs/250-writingsystem-activation/spec.md` section 6.3's conditions were
re-checked at close and all three hold (see ruling 3).

### Cycle-6 lead rulings (five)

**Ruling 1 -- Checkpoint 2c closes WITHOUT a separate live verification cycle,
and here is the falsifiable reason.**

Cycle 5's plan called for a narrow gate whose one question was falsifiability:
"a promoted probe that passes against mutated code is worthless coverage."
That question is answered, but only partly by the implementer, so the lead
answered the rest directly instead of spending a live cycle on it:

- **Structural risk absent.** T14a is test-only. `b3ba083b` is three files
  (`test_makefeatstruc_c3_live.py`, the evidence file, the report) with **zero
  diff to `flexicon/code/BaseOperations.py`** and `tests/conftest.py`
  untouched -- independently confirmed by the main session. The failure mode a
  verification gate exists to catch (a production behaviour change riding along
  unnoticed) has no surface here.
- **Test 1 has a mutation kill.** `__NormalizeFeatStrucLevel`'s recursion was
  disabled; the nested round-trip failed, the other two correctly stayed green,
  and `BaseOperations.py` was restored `git hash-object`-identical (never via
  `git checkout`).
- **Tests 2 and 3 have NO mutation kill.** The lead read the test source rather
  than taking the report's word, and re-derived their non-tautology
  structurally: test 2 applies `slot="From"` and `slot="To"` to **one**
  `MoDerivAffMsa` (the same `deriv_hvo`, two fresh `sandbox.Object()` lookups),
  then asserts both slots are non-`None`, that `FromMsFeaturesOA.Hvo !=
  ToMsFeaturesOA.Hvo`, **and** that each slot carries its own distinct value
  (sg vs pl). If `slot=` were ignored, either one property stays `None` or the
  two Hvos are equal -- the test cannot pass vacuously. Test 3 asserts the raise
  message contains **both** `"MoDerivAffMsa"` and `"slot"` and then re-fetches
  to assert neither slot got a partial attach, so a raise from an unrelated
  cause does not satisfy it.
- **Residue, named not hidden.** Structural re-derivation is weaker evidence
  than a mutation kill. It is not dropped, it is **rescheduled**: see ruling 2.

**Ruling 2 -- the two missing mutation kills are FOLDED INTO the Defect-4 gate,
not given their own cycle.**

Only one agent runs live pytest in this tree at a time, so a standalone T14a
gate would cost a full serialised cycle. The Defect-4 verification gate is
already holding the live-pytest token, already mutating and hash-restoring
`flexicon/code/BaseOperations.py`, and already running `target_sandbox`. Adding
two one-line mutations there is close to free:

- **M-T14a-2:** break `slot=` routing in `_ResolveFeatureStrucOwner` (force it
  to return the first table row regardless of `slot`). Expect
  `test_slot_disambiguates_from_and_to_through_makefeatstruc` to FAIL.
- **M-T14a-3:** make the ambiguous-`ClassName`-no-`slot` branch pick a row
  instead of raising -- i.e. mutate the C1 "never guessed" rule itself. Expect
  `test_ambiguous_owner_without_slot_raises_through_makefeatstruc` to FAIL.

If either mutation leaves its test GREEN, that test is tautological, T14a is
**not** actually done, and Checkpoint 2c reopens as a defect regardless of the
Defect-4 result. Restore via a scratchpad backup + `git hash-object` compare,
never `git checkout` (concurrency rule).

**Ruling 3 -- Defect 4's three dispatch conditions re-checked at close; all
hold.**

1. *Lookup-only.* Contract `C-D4-2` is frozen and the fence lists exactly two
   permitted symbols. Unchanged.
2. *`target_sandbox`, not the in-place Target.* Frozen in section 6.4; carried
   into the cycle-7 prompts verbatim.
3. *`BaseOperations.py` holds no uncommitted FS work.* Re-verified at close:
   T14a was test-only by design and `b3ba083b` shows zero diff to that file;
   `git status --porcelain` is clean for it.

Anchors re-confirmed **unique** in `flexicon/code/BaseOperations.py` at
`b3ba083b`, by the lead, before dispatch (spec 6.1 requires this and forbids
trusting the line numbers):

| Anchor | Found at | Spec said | Unique? |
|---|---|---|---|
| `def _apply_props_loop(` | `:319` | `:319` | yes |
| `tgt_handle = target_ws_by_id.get(tgt_ws_id)` | `:360` | `~:354-364` | yes (count 1) |
| `# Target lacks this WS; skip silently.` | `:362` | -- | yes |
| `ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()` | `:1307` | `:1306-1308` | yes in this file |

**No drift.** T5 added ~276 lines to `BaseOperations.py` but all of it landed
*after* `:1307`, so the Defect-4 target region is where the frozen contract said
it would be. The contract does **not** need re-freezing. Implementers still
re-confirm the anchors themselves before editing.

**Ruling 4 -- `__ResolveFeatStrucOperand`'s twin `_obj` branches are a NOTE, not
a task, and the note has a named trigger.**

`flexicon/code/BaseOperations.py` `__ResolveFeatStrucOperand` (`~:2656-2661`,
new in T5 `6643b483`) has two branches that both `return raw._obj`:

```python
if hasattr(raw, "_obj") and not hasattr(raw, "Hvo"):
    return raw._obj
if hasattr(raw, "_obj") and hasattr(raw._obj, "Hvo"):
    return raw._obj
return raw
```

They are collapsible to one condition, and there is an uncovered case: a wrapper
having **both** `_obj` and `Hvo` whose `raw._obj` lacks `Hvo` falls through and
returns the **wrapper**. Ruling: **NOTE.**

- It is not a silent-corruption defect. The returned value is assigned to
  `cv.FeatureRA` / `cv.ValueRA`; a Python wrapper handed to a CLR property
  setter raises. The uncovered path **fails loud**, which is the behaviour C1
  requires anyway.
- Fixing it now would mean opening `BaseOperations.py` for a cosmetic change at
  exactly the moment Defect 4's condition 3 requires that file to be quiet. The
  cost of touching it now strictly exceeds the benefit.
- **Trigger:** fold the collapse into **T12** (`CopyFeatStruc`), the next task
  that legitimately edits this file's feature-struct code -- as a one-line rider
  **plus** a test pinning the uncovered case (wrapper has `_obj` and `Hvo`,
  inner `_obj` lacks `Hvo`), so the collapse is proven behaviour-preserving
  rather than assumed.
- Pyright's `_obj`-on-`bool` complaint at that site is a **false positive** (it
  does not narrow through `hasattr`). Recorded so nobody re-derives it.

**Ruling 5 -- the crew routing table now tracks WRITE and COMMIT separately.
This is a real process defect and it cost cycle 6 a manual rescue.**

`lex-doc` has `Write` but **no `Bash`**, so it physically cannot run
`git commit`; its cycle-6 report correctly reported "BLOCKED / NOT DONE" for the
commit step and the main session had to commit `6b54059` on its behalf. The old
mental model was one column ("who can persist"). Write and commit are different
capabilities. Verified from the agent definitions, 2026-09-07:

| Agent | Read/Grep/Glob | Edit | Write | Bash | Can CREATE a file | Can COMMIT |
|---|---|---|---|---|---|---|
| `lex-programmer` | yes | yes | yes | yes | yes | **yes** |
| `lex-logscan` | yes | yes | yes | yes | yes | **yes** |
| `lex-verification` | yes | -- | -- | yes | **only via Bash heredoc** | **yes** |
| `lex-archivist` | yes | yes | -- | yes | **only via Bash heredoc** (`Edit` cannot create) | **yes** |
| `lex-doc` | yes | yes | yes | -- | yes | **NO -- someone else must commit** |
| `lex-simplify` | yes | yes | -- | -- | no (`Edit` cannot create) | no |
| `lex-qc` | yes | -- | -- | -- | no | no |
| `lex-domain` | yes (+WebFetch) | -- | -- | -- | no | no |
| `lex-synthesis` | yes | -- | -- | -- | no | no |
| `lex-author` | yes | -- | -- | -- | no | no |

Binding consequences for every future dispatch plan:

1. **Bash-only roles must be told to write their report with a heredoc.**
   `lex-archivist` has `Edit` but no `Write`, and `Edit` cannot create a file
   that does not exist -- so "just Edit it" silently fails for a new report.
2. **If `lex-doc` is dispatched, the plan must name who commits its output** --
   in the same response, not discovered afterwards.
3. **Read-only roles (`lex-qc`, `lex-domain`, `lex-synthesis`, `lex-author`)
   cannot persist anything at all.** This is the same finding cycle 1 recorded
   for `Explore`/`lex-domain`; it is now a table rather than a paragraph so it
   stops being rediscovered.

### Cycle-6 items NOT closed (deliberately)

- **#256 closure -- PENDING THE USER.** Draft at
  `reviews/cycle6-issue256-closure-draft.md`, **not posted**, and it may stay
  open. The main session corrected a substantive error in it first: the draft
  illustrated nesting with **name** keys (`{"noun agreement": {...}}`) while
  four lines later stating names are not accepted operands -- that example would
  have **raised** if the reporter pasted it. It now shows the shape that works
  (`{agreement_feat.Hvo: {number_feat.Hvo: sg_val.Hvo}}`) plus an explicit
  paragraph that nesting is solved **but not with the name-based operands**
  #256's own example used. Lead note: this means **#256's ask 2 is answered
  structurally, not in the form the reporter asked for**, and #265 is where the
  requested form lives. Whoever posts it must not let that read as a full grant.
- **T14a mutation kills for tests 2 and 3** -- rescheduled into the Defect-4
  gate (ruling 2), not dropped.

## Next pickup

**Spurt 6 = the #250 Defect 4 micro-spurt, ALONE. Then T6.**

Contract: `specs/250-writingsystem-activation/spec.md` (FROZEN at `a26d39c`;
Defect 4 only -- Defects 1-3 stay queued behind this feature reaching
`feature_complete`).

- **Cycle 7, group 1 (read-only, no pytest):** D4-T4 -- re-verify the section-3
  13-site inventory by grep, pinned to a named commit, and settle finding F2
  (does `PhonemeOperations`' apply path self-resolve and therefore NOT inherit
  the fix?). **Report only; edit nothing.**
- **Cycle 7, group 2 (holds the live-pytest token):** D4-T1 (the lookup-only
  normalized fallback), D4-T2 (offline tests), D4-T3 (live on
  `target_sandbox`, predictions committed BEFORE the run, unfixed side measured
  first), D4-T5 (CHANGELOG).
- **Cycle 8:** the Defect-4 verification gate, **plus** the two folded T14a
  mutations M-T14a-2 / M-T14a-3 (ruling 2), plus the D4-T6 #250 comment
  DRAFTED, not posted.
- **Checkpoint D4** closes when the fix is committed, gated PASS, and both
  folded mutations killed their tests.
- If lookup-only proves infeasible -> **STOP, `needs_human`.** Do not expand to
  the 13 build sites (C-D4-2).

## Where things stood (as of 2026-09-07, spurt 4 / cycle 5 end)

**CHECKPOINT 2b IS CLOSED.** T5 landed (`6643b483`) and its verification gate is
**PASS** (`reviews/cycle5-verification-T5.md`). One generalized
`BaseOperations._MakeFeatStruc` now backs both `InflectionFeatureOperations`
and `PhonFeatureOperations`, routing owner resolution through the C1 table
instead of the dead `hasattr(..., "FeaturesOA")` gate. Offline delta 0; live
subset unchanged except the #256 probe flip; mutation test 1 -> 8 failed with a
hash-verified clean restore. The gate re-derived the true parent itself
(`7bc6d01c`, NOT `HEAD~1`) and independently confirmed `6643b483` contains only
its own five files despite a concurrent git-index collision.

**The #250 Defect 4 micro-spurt window is now OPEN.**

### Cycle-5 lead rulings (four)

**Ruling 1 -- the T5 coverage gap does NOT block #256, but it is closed NEXT,
before anything else, as T14a.**

The gate proved the recursive-dict shape and `slot=` work live, but had to write
its **own** probes to do it -- and those probes lived in a disposable worktree
that has since been removed. **The coverage that proves T5's new public surface
works currently exists nowhere except as prose in an evidence file.** The
behaviour is verified (two independent parties, live, falsifiable); the
*regression protection* is not. That is precisely the "1467 passing tests didn't
catch it" shape from the #222 family that started this feature -- with the one
difference that we have named it rather than discovered it later.

So: **#256 closes on the evidence** (verification asks whether the code works,
and it demonstrably does), **and T14a lands immediately** so the protection is
real. T14a is deliberately test-only -- it adds NO production code, so it does
not re-open `BaseOperations.py`, which keeps the #250 spec's section 6.3
condition 3 satisfied for the Defect-4 spurt that follows it.

**T14 is split:** **T14a** (promote the gate's probes -- nested recursive-dict
round-trip, `slot="From"/"To"` on a live `MoDerivAffMsa`, ambiguous-owner error
path) runs now; **T14b** (empty-but-present struct, per-level `TypeGuid` and
GUID preservation, unknown-`ClassName` raise) stays at its original place late
in the task list.

**Ruling 2 -- C3's "a name" operand claim is WRONG; the contract text is
amended, no new task is added to this feature.**

The gate confirmed independently what the implementer disclosed: `__ResolveFeature`'s
non-int branch was a pure passthrough in **both** pre-T5 twins. Name resolution
was never implemented, is not a T5 regression, and no shipped test ever
exercised it. Between "amend the contract" and "add a task", **amend**:
resolving a bare name means choosing a `Find`-style lookup, a scope, an
ambiguity policy across feature systems, and a case/writing-system rule -- four
decisions with no obvious default. Guessing them is exactly the silent guess the
C1 resolver exists to forbid, and inventing a policy under a frozen contract at
the tail of a feature is how scope creep gets laundered as bug-fixing.

C3's operand list is corrected to what ships (`IFsFeatDefn`/`IFsSymFeatVal`
objects or wrappers, HVO ints, GUID strings) with a dated errata note recording
that the "a name" text was never backed by an implementation. C4's
"user-facing surface is name-tolerant / wire format is GUID-only" contrast is
corrected in the same pass so the spec stops asserting a distinction that does
not exist. **Name-operand support is recorded in section 7 as a candidate
follow-up issue** -- it needs its own freeze cycle, the way #250 did. Filing it
needs the user's approval and is NOT done unilaterally.

**Ruling 3 -- #256 closes, on two halves, with `CopyFeatStruc` explicitly
DEFERRED-not-declined.**

Both halves the issue actually asked for are confirmed live by two independent
parties: (i) owner resolution per type -- `MsFeaturesOA` for MSAs, via the C1
resolver, not the impossible hardcoded `FeaturesOA` (item 7's live
`FP_ParameterError` -> `IFsFeatStruc` flip, plus the gate's own `MoStemMsa`
round-trip re-fetched from a fresh object); (ii) nested feature structures
expressible -- the gate's two-level recursive-dict round-trip, re-read from a
fresh `IMoStemMsa`. The issue's third suggestion, `CopyFeatStruc(src_fs,
target_owner)`, is **in scope for this feature but out of scope for this
closure**: it is already frozen as **C8** and scheduled as **T12**, with
`overwrite=False` raising by default and no merge mode. The closing comment must
say so explicitly, so the closure is not misread as a decline. **Closing is
proposed, not executed -- issue closure needs the user's approval** (the same
rule as #250's D4-T6 and #264's filing).

**Ruling 4 -- Defect 4 runs BEFORE T6, and it gets its own spurt.**

All three of `specs/250-writingsystem-activation/spec.md` section 6.3's
dispatch conditions now hold: (1) the fix is frozen lookup-only (C-D4-2),
touching none of the 13 map-build sites; (2) live verification is frozen to
`target_sandbox`, not the in-place Target; (3) Checkpoint 2b's gate has cleared
and is **committed**, so `BaseOperations.py` holds no uncommitted FS work. The
substantive reason is unchanged and decisive: **T6-T8 add five new sync
implementations whose multistring alts inherit the fix for free if it lands
first, versus five fresh instances of a known bug to sweep later.**

It does **not** share this spurt with T14a. Defect 4 has its own six-task list
and its own gate, and both it and T14a need `FLEXLIBS_REQUIRE_LIVE=1` live runs.
**Only one agent runs live pytest at a time in this tree** -- #264 is literally
about global init order-dependence, and cycle 5's own incident showed a live run
leaving residue in a shared in-place project. Serialising is cheap; two
concurrent live sessions is an unforced error.

### Cycle-5 corrections carried forward

- **#264's figure is CORRECTED: 3, not 11.** Of the 13 modules in
  `flexicon/sync/tests/` and `flexicon/tests/`, 11 are unmarked, but only
  **three actually call `FLExInitialize`** (`test_base_operations.py`,
  `test_FLExInit.py`, `test_FLExProject.py`). The other 8 call no init and look
  genuinely offline-safe. **Blanket-marking those trees would wrongly delete
  real offline coverage** -- #264's suggested-fix item 2 must target the three,
  not the eleven. The issue has been amended upstream; use 3 from here on.
- **Two Pyright diagnostics in T5-touched files are PRE-EXISTING and benign** --
  `InflectionFeatureOperations.py:415` (empty-generator idiom, from `588a8591`)
  and `PhonFeatureOperations.py:658` (heterogeneous-dict typing gap, from
  `e1603c7f`, on the capture side C4b freezes). No action. Recorded so nobody
  re-derives them.
- **A concurrent git-index collision occurred during T5** and was caught on both
  sides: the implementer detected and unstaged the foreign paths, and the gate
  independently confirmed `6643b483` contains only its own five files with
  `tests/conftest.py` byte-untouched. The other crew is still active in this
  tree. The explicit-path staging rule is what made this recoverable -- it is
  not a formality.
- **Live-fixture hazard, disclosed twice in cycle 5:** `writable_project` opens
  the real, shared Sena 3 **in place**, not a sandbox, so a failing live
  assertion leaves residue -- and residue can make a later clean run report wrong
  numbers even with the source hash-verified identical. Both agents hit this;
  both cleared it with `python scripts/restore_sena3.py`. Prefer
  `target_sandbox` for anything that writes.

## Next pickup (spurt 5 -- SUPERSEDED; T14a is DONE, Checkpoint 2c CLOSED)

**Spurt 5 = T14a + the two docs/record items, then a narrow gate. Nothing else.**

1. **T14a (live, `target_sandbox`)** -- promote the gate's deleted probes into a
   shipped test file. Reconstruct from
   `evidence/live-cycle5-verification-t5.md` section 5; the original file
   (`test_verify_t5_c3_gate.py`) is **gone** with its worktree, do not hunt for
   it. Test-only: no production code, do not re-open `BaseOperations.py`.
2. **C3/C4 errata + #264 figure correction + T14 split** (docs-only, `spec.md`).
3. **#256 closure comment DRAFTED, not posted** -- routed to the user for
   approval.
4. **Gate** -- narrow, and the question that matters is falsifiability: a
   promoted probe that passes against mutated code is worthless coverage.
5. **Then the #250 Defect 4 micro-spurt**
   (`specs/250-writingsystem-activation/spec.md`), **then T6.**

## Where things stood (spurt 3 / cycle 4 end)

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

## Next pickup (spurt 3 -- SUPERSEDED; T5 is DONE)

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
