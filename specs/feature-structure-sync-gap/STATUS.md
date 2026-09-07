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

---

# Cycle 7 (spurt 6) -- #250 Defect 4 micro-spurt: PASS, gate pending

**Result: D4-T1 / D4-T2 / D4-T3 / D4-T5 complete; D4-T4 was already done at
cycle 7 group 1. Checkpoint D4 is NOT yet closed -- it closes on the cycle-8
verification gate.**

- **D4-T1** `_normalize_ws_tag` + `_resolve_ws_handle`, both module-level per
  C-D4-7 (`_resolve_ws_handle` at `flexicon/code/BaseOperations.py:333`,
  independently confirmed by the lead), plus a one-line change to
  `_apply_props_loop`'s resolution step and a shared `_ws_resolve_cache`.
  Committed `269b6a7` -- **by the OTHER session, see the incident below.**
- **D4-T2** offline suite + resolution-site ratchet: 21 passed.
- **D4-T3** live on `target_sandbox`, `run_mode: live` on BOTH sides.
  Unfixed: 2 FAILED (the drop, measured not assumed). Fixed: 2 PASSED.
  D4-c SKIPPED on both sides -- see the ruling below.
  Evidence: `specs/250-writingsystem-activation/evidence/live-D4-T3.md`.
- **D4-T5** CHANGELOG entry, committed `8c679ed` (also the other session).
- Offline delta +21 passed, 0 change in failures, agreeing across 5 runs.
- Fence held: zero commits touched `PhonemeOperations.py`,
  `ExampleOperations.py` or `WritingSystemOperations.py` (lead-verified).

## LEAD RULING -- the D4-c live skip is ACCEPTED, with an amendment

`test_d4c_separator_divergent_resolves` was SKIPPED (loudly, on both the
unfixed and fixed sides) because `target_sandbox`'s only two active writing
systems are `en` and `etu` -- **neither contains a `-` or `_` to flip**, so a
separator-divergent spelling cannot be constructed from real project state.

**Ruled ACCEPTABLE. The gate does not need to close it live.** Reasoning:

1. D4-a, D4-b and D4-c reach the LCM through **one** call site --
   `_resolve_ws_handle(target_ws_by_id, tgt_ws_id, _index_cache=...)`. There
   is no case/separator branching below it. The three variants differ **only**
   in what `_normalize_ws_tag` folds, a pure two-operation string transform.
2. The LCM-facing half of that path is proven live **twice** (D4-a and D4-b,
   drop and save). The residue unique to D4-c is `str.replace("_", "-")` --
   pure Python, with no LCM behaviour that could distinguish a hyphen fold
   from a case fold.
3. D4-c is covered offline **against the real `_apply_props_loop`**, not a
   mock -- which is the form spec 250 D4-T2 itself prescribes ("run against
   `_apply_props_loop` directly with fabricated dicts").
4. Closing it live would require either hunting for a differently-shaped
   project or fabricating a separator-bearing writing system -- both excluded
   by spec section 6.4's "no special project state" design, and it would cost
   a full serialised live cycle to test a string method.

**The amendment is the load-bearing half of this ruling.** Acceptance
criterion 1 is FROZEN and reads "D4-a, D4-b and D4-c all resolve ... proven
live". Leaving that text standing next to a skipped D4-c is precisely the
silent-partial-coverage shape this work exists to eliminate. Criterion 1 is
therefore amended in `specs/250-writingsystem-activation/spec.md` to state the
live/offline split explicitly. **No artifact -- evidence file, CHANGELOG, or
the D4-T6 comment -- may describe D4-c as live-verified.** The gate checks this.

**Falsifiability residue, named:** if `_apply_props_loop` ever grows a second
resolution call site, or if a project with a separator-bearing `ws.Id` becomes
available, D4-c's live gap reopens and must be closed then.

## LEAD RULING -- `missing live_phase marker` is a real defect, fixed in cycle 8

`tests/live_status.json` lists all three new live tests under
`uncategorized_live_tests` as `missing live_phase marker`. They are invisible
to the repo's live-coverage accounting (`tests/LIVE_COVERAGE.md`,
`tests/LIVE_STATUS.md`). This is a telemetry defect, not a correctness one, but
it is exactly the kind of silent gap this feature exists to close. Folded into
cycle 8 as **D4-T7**, done by the agent already holding the live token and
re-verified in the same window -- splitting it would cost a whole serialised
live cycle for three decorator lines. It runs AFTER the gate's own measurements,
so it cannot muddy them.

## INCIDENT -- duplicate dispatch: two sessions ran the SAME dispatch plan

**This is a protocol defect, not an agent error, and it is now the crew's
governing concurrency lesson.**

A second Claude Code session (`flexicon-cd`) independently executed **this
lead's own cycle-7 dispatch plan** at the same time as this session, and
implemented D4-T1/T2/T5 concurrently. Duplicated commits now on `main`:
`269b6a7` (D4-T1), `8c679ed` (D4-T5), `4287114` (their report), alongside this
session's `302d266`, `1705e10`, `312c5c3`. The two fixes were byte-identical so
nothing was lost -- but that was luck, not design.

**ROOT CAUSE: `.crew-handoff.json` + `STATUS.md` are a shared work queue with
no claim mechanism.** Both sessions read `next_entry` and both executed it.
Nothing in the handoff protocol as written prevents this.

Two further hazards surfaced inside the incident:

- **A shared-file restore can destroy another session's uncommitted edit.**
  This session's D4-T3 required swapping `BaseOperations.py` between its
  pre-fix and post-fix blobs to measure both sides; the other session's
  in-progress, never-staged D4-T1 edit vanished from the working tree between
  two of its own bash calls, with no dangling git object anywhere. The
  no-`git add` rule protects the COMMITTER; **nothing protected the HOLDER.**
  Any measurement requiring an unfixed/fixed swap must use a private
  `git worktree` or sandbox copy, never the shared tree.
- **`269b6a7` is a RECONSTRUCTION, not a recovered blob.** Having lost its
  edit, the other session's agent re-typed the fix from diff text in its own
  conversation and committed immediately. Root cause of the vanish was never
  confirmed.

### The convergence argument is REJECTED as possibly circular (binding)

The reassurance on offer is that the committed blob
(`a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db`) is byte-identical to this
session's separately-authored fix. Two independent authorings converging
byte-for-byte would be strong evidence -- **but `git commit --only -- <path>`
reads WORKING-TREE content regardless of staging**, and this session's own
authored fix was sitting in the working tree during that window. So either
(i) two authorings genuinely converged, or (ii) the commit simply read this
session's copy, in which case there is ONE authoring counted twice and the
convergence corroborates nothing. **Neither session can distinguish (i) from
(ii).** Both agents hedged identically in their own reports.

**Therefore: `269b6a7` is treated as UNREVIEWED THIRD-PARTY CODE. Its
falsifiability evidence must come from a MUTATION TEST, not from provenance.**
The cycle-8 gate verifies it from scratch against C-D4-1..C-D4-7 and is
forbidden from citing byte-identical convergence as corroboration.

## PROTOCOL, NOW IN FORCE -- take the lock, do not read `next_entry`

**Every spurt in either session now BEGINS by acquiring locks via the `lockout`
skill, not by reading `next_entry`.**

```
python ~/.claude/skills/lockout/lockout.py acquire <paths> \
    --team <team> --session <session-id> --purpose "..." --ttl 60 --json
```

**On conflict: STOP and report. Never wait-loop.** This session currently holds,
under team `flexicon-19`, session `5b6c151f-877a-48a8-ba39-be2a3de5abdd`:
`flexicon/code/BaseOperations.py`,
`specs/feature-structure-sync-gap/{.crew-handoff.json, STATUS.md, spec.md}`,
`specs/250-writingsystem-activation/spec.md`.

**The binding constraint is the LIVE PYTEST TOKEN, not the file locks.** Only
one agent may run `FLEXLIBS_REQUIRE_LIVE=1` against the shared FLEx projects at
a time. Agreed split: **this session owns the live chain** (cycle-8 D4 gate,
then T6/T7/T8 closing #251/#252, then T9 closing #253); **`flexicon-cd` owns
non-live work** (T16/T17 docs, and DRAFTING -- not filing -- an issue for the
two resolution sites D4 does not reach). **Do not plan T16/T17 here.**

**`CLAUDE.md` is FROZEN until the gate returns** -- `flexicon-cd`'s T16 edits
it and has agreed to defer. No agent may edit it, and no task may depend on it
changing.

## Committing: the AMENDED rule (the blanket "never `git add`" was wrong)

**The earlier blanket "NEVER `git add`" rule is WITHDRAWN -- it was impossible
to follow.** Independently verified by both sessions (git 2.32.0.windows.1):
`git commit --only -- <path>` **fails outright on an untracked file** with
`error: pathspec ... did not match any file(s) known to git`, and
`git commit --include` reports `nothing added to commit but untracked files
present`. `--only` can only restrict a commit to paths git already knows about.
Every new report, evidence file and test file is untracked at commit time, so
the blanket rule forbade the majority of what agents legitimately do.

**BINDING PROCEDURE:**

- **MODIFYING a tracked file** -- commit straight from the working tree, no
  staging at any point:
  ```
  git commit --only -F <msgfile> -- <exact path>
  ```
- **CREATING a new file** -- `git add` is unavoidable, so minimise the window.
  Do the add and the commit in a **single shell invocation**, and verify the
  index is empty on both sides:
  ```
  git status --porcelain    # index must be empty
  git add -- <exact path> && git commit --only -F <msgfile> -- <exact path>
  git status --porcelain    # index must be empty again
  ```
  Keeping `--only` pins the commit to that one path, so even if a third crew
  stages something inside the window it cannot ride along. This collapses the
  exposure to microseconds rather than eliminating it -- the best available, and
  strictly better than the bare `git add` ... later ... bare `git commit`
  pattern that actually bit us twice.
- **STILL ABSOLUTELY FORBIDDEN:** `git add -A`, `git add .`, `git add -u`,
  `git commit -a`, and any `git add` that is not immediately followed by its own
  scoped commit in the same invocation.

### Documented alternative -- private index (NOT the default)

There is a zero-exposure variant, verified working in a scratch repo by this
session (another crew's staged `A other.txt` survived untouched throughout):

```
TMPIDX=$(mktemp)
GIT_INDEX_FILE=$TMPIDX git read-tree HEAD
GIT_INDEX_FILE=$TMPIDX git add -- <exact path>
GIT_INDEX_FILE=$TMPIDX git commit -F <msgfile>
rm -f $TMPIDX
git update-index --add -- <exact path>    # MANDATORY reconcile
```

**It is deliberately NOT the default, because its failure mode is worse than
the one it prevents.** If an agent omits the final reconcile, the shared index
shows the new file as a staged **DELETION** against the new HEAD, and anyone
running `git commit -a` commits that deletion -- losing the file outright,
versus the microsecond sweep risk of the standard procedure. Use it only where
an agent is explicitly instructed to and the reconcile is spelled out.

## Baseline correction (prevents a false regression call)

In the pinned `tests/operations tests/contract` subset the expected red set is
**2 failures, not 3**: the two foreign
`test_transaction_rollback.py::TestPhase2JoinOrOpen` failures, messages
unchanged. `test_flexlibs2_alias_ratchet.py` is red **in its own file**, outside
this subset. The NaturalClass
`test_apply_raises_on_type_mismatch_segments_target` failure does **not**
surface in this subset at all.

## Known non-discrepancy (do not report as a gap)

`evidence/live-D4-T3-predictions.md` was never authored; the predictions live
in the committed `evidence/live-D4-T3.md` under `[PREDICTION]` headings, which
is sufficient and satisfies the commit-before-run precedent. Do not grep for
the separate filename and report it missing.

## Inputs from `flexicon-cd`, whose lane is now FINISHED

Commits `4fc2b6bd` (T17) and `b3735f81` (the draft-only issue). They have
released all their locks and now hold only `CLAUDE.md`, still deferred.
**T16/T17 are done and are not this session's work.**

### A non-site the ratchet correctly excludes -- do not re-derive it

`flexicon/code/Grammar/PhonemeOperations.py:1336`
(`all_ws = {ws.Id: ws.Handle ...}`) **looks** like a fourth resolution site and
is not one. It is a `GetSyncableProperties` **READ** path feeding
`__ReadMultiString`: it enumerates **source** writing systems and resolves no
target. It is one of the 13 protected map-build sites, correctly excluded from
the frozen three-site set. `flexicon-cd` checked this rather than assuming it.
**The three-site frozen set is confirmed correct.** Recorded here so no future
sweep spends a cycle re-deriving it.

### Partial-write hazard for whoever closes resolution site 2 (NOT cycle-8 work)

In `flexicon/code/Lexicon/ExampleOperations.py`'s `TranslationsOC` loop,
`new_trans` is created via `ICmTranslationFactory` and
`item.TranslationsOC.Add(new_trans)` runs **before** per-writing-system
resolution. Routing that loop through `_resolve_ws_handle` introduces an
`FP_ParameterError` that can fire **mid-loop**, potentially leaving an
`ICmTranslation` owned by the example with **zero alts set**.

**Whether the surrounding transaction rolls that back needs VERIFYING, not
assuming.** This is a constraint on the future follow-up that closes resolution
sites 2 and 3 -- recorded now so it is not discovered the hard way. Not
scheduled in cycle 8.

### Open question for spec 233's owner -- NOT resolved by this campaign

`specs/233-basetype-cast-sweep/spec.md` said "All 16 CONFIRMED sites fixed";
T17's three appended `SegmentsRC` rows make it 19. `flexicon-cd` added the 3 to
the criteria as the consistent default but **explicitly did not decide it** --
it is spec 233's owner's call. Two knock-on facts they flagged:

- the new "19 CONFIRMED" now **collides numerically** with a pre-existing
  "19 NEEDS RUNTIME" count in the same document;
- they left the sweep-total arithmetic (`16+19+9+20=64`) on the original 16 so
  it still reconciles.

**This campaign does not resolve it and no agent here should.** Route to spec
233's owner.

---

# Cycle 8 (spurt 7) -- the D4 verification GATE: **PASS on every leg**

**CHECKPOINT D4 IS CLOSED.** The `#250` Defect-4 micro-spurt is finished and
the live chain returns to this feature's own task list at **T6**.

Two reports, both committed:

- `specs/250-writingsystem-activation/reviews/cycle8-archivist-269b6a7-audit.md`
- `specs/250-writingsystem-activation/reviews/cycle8-verification-D4-gate.md`

## What the gate actually proved (mutation, not provenance)

| Leg | Result |
|---|---|
| 1. `269b6a7` re-audited from git objects only | **PASS on all seven clauses** C-D4-1..C-D4-7. 0 FAIL, 0 CONCERN. `--stat` = one file (`BaseOperations.py`, 114+/1-), so acceptance criterion 6's auto-reject trigger never fires. |
| 1. M-D4-1 / M-D4-2 / M-D4-3 | **PASS-KILLED** (14/21, 3-failed, 2-failed respectively). Every restore verified `git hash-object`-equal to `git rev-parse HEAD:<path>`. |
| 2. M-T14a-2 / M-T14a-3 | **PASS-KILLED**, live. |
| 3. Ratchet probe (4th resolution site) | **PASS-KILLED, tracked + hash-verified.** The failure message named `Shared/string_utils.py` as the 4th site, exactly as predicted. Restored via `git show HEAD:<path>`, not `checkout`. |
| 4. Offline delta | **PASS.** `2 failed, 371 passed, 504 deselected`, run twice, identical both times, and the 2 failures are exactly the pinned foreign pair. |
| 5. Live re-run as-committed | **PASS.** `2 passed, 1 skipped`, `run_mode: live`. |
| 6. Artifact scan for false "D4-c live-verified" claims | **PASS, zero hits.** |
| 7. D4-T7 `live_phase` markers | **PASS** (`c76c399`). `uncategorized_live_tests` no longer lists the three tests. |

**No mutation stayed NOT-KILLED.** That is the whole basis for closing D4.

## Consequence 1 -- **Checkpoint 2c HOLDS. It does NOT reopen.**

Cycle 6 closed 2c on a *structural re-derivation* of T14a tests 2 and 3, and
named that as weaker-than-mutation residue rather than hiding it. Cycle 8 paid
that debt: M-T14a-2 (slot routing forced to `rows[0]`) and M-T14a-3 (the
no-slot branch picking `rows[0]` instead of raising) **each killed their test,
live**. T14a's coverage is genuine and non-tautological. The residue recorded
in cycle-6 ruling 2 is discharged; nothing about 2c is now carried on
structural argument alone.

## Consequence 2 -- the possibly-circular convergence argument stays REJECTED

The archivist was told to consider and rule on it, and did: `git commit --only`
reads working-tree content regardless of staging, so byte-identical convergence
between the two sessions and read-the-other-copy are indistinguishable from the
repo alone. It is cited in the audit **only** to explain why it corroborates
nothing. All seven PASSes settle from the blob text plus mutation kills.

## Consequence 3 (BINDING, all future work) -- **worktree isolation is the DEFAULT for mutation testing**

Cycle 7's hazard (rule 4) said "use a private worktree **or** sandbox copy" and
read as a preference. It is now a **requirement**, and it is the direct answer
to the holder-side hazard that destroyed an in-flight edit in cycle 7:

> **Any agent that mutates a tracked file in order to measure a before/after --
> mutation testing, ratchet probes, bisects, "does this test actually fail" --
> MUST do it in a disposable `git worktree add <tmpdir> HEAD`. The shared
> working tree is never mutated, not even with an intended restore.**

Cycle 8 did exactly this and it worked: all of legs 1-4 ran in the worktree;
gitignored `tests/fixtures/*.fwbackup` were copied in read-only so
`target_sandbox` still worked; and the shared tree was touched **only** for
leg 7's 3-line metadata patch (`c76c399`) and the report (`16692ef`). Every
dispatch prompt from here on states this as a rule, not a suggestion.

A `git hash-object`-verified restore is still required **inside** the
worktree -- it proves the mutation was undone. It is not a substitute for the
worktree; cycle 7 proved a correct restore can still clobber a concurrent
writer.

## Consequence 4 -- the amended git rule is now standing crew record

Restated so no future prompt has to re-derive it:

- **Modify a tracked file:** `git commit --only -F <msgfile> -- <exact path>`.
  No staging at any point.
- **Create a new file:** ONE invocation of
  `git add -- <exact path> && git commit --only -F <msgfile> -- <exact path>`,
  with the index verified empty immediately before and immediately after.
- **Absolutely forbidden, always:** `git add -A`, `git add .`, `git add -u`,
  `git commit -a`.

## Filed since cycle 7 -- **flexicon#266 and #267**, both user-approved

The cycle-7 draft is filed as two issues, correctly split rather than lumped:

- **`#266`** -- `Grammar/PhonemeOperations.__ApplyBasicIPASymbol`. The genuine
  one-line C-D4-7 substitution: route the lookup through `_resolve_ws_handle`.
- **`#267`** -- `Lexicon/ExampleOperations`' `TranslationsOC` loop. Scoped as a
  **CORRECTNESS change, not a substitution**, because the `ICmTranslation` is
  created and attached **before** any writing system resolves; a naive one-line
  swap leaves an **orphaned translation with zero alts** when the ambiguity
  error fires mid-loop. `#267` therefore carries a regression-test requirement
  for that orphan.

Both issues record the ratchet consequence explicitly: **closing a resolution
site turns the three-site ratchet red BY DESIGN. Update the frozen set in the
same commit. Never disable the test.**

The D4-T6 draft now cites `#266`/`#267` instead of restating them longhand
(`18d6310`). **The D4-T6 comment on `#250` is still UNPOSTED** -- posting needs
the user's approval and no agent may post it.

## Also landed

- `a67890e` -- corrected `spec.md` section 7's false "`flexlibs2/` does not
  exist" premise. It **does** exist, as the inbound-only shim removed at
  v5.0.0, and the error **understated** the finding: `#240`'s ratchet forbids
  any internal reference, so the stale `CLAUDE.md` was instructing agents to
  write exactly what that ratchet rejects.
- **T16 (`9e0f9710`) and T17 (`4fc2b6bd`) are DONE**, by `flexicon-cd`.

## Concurrency: **`flexicon-cd` has STOOD DOWN**

It has released all locks, will not plan cycles, and will not touch campaign
state. **This session holds the lead role and the live-pytest token outright.**
The work-split clause is retained as history, not as a live constraint. The
one-live-token-holder-at-a-time rule survives on its own merits.

## Still not this campaign's problem

Spec 233's `16 -> 19 CONFIRMED` definition-of-done. Flagged for spec 233's
owner. No agent here resolves it.

## Next pickup -- **cycle 9 = T6, `MSAOperations`, closes `flexicon#251`**

New `GetSyncableProperties` / `ApplySyncableProperties` on
`flexicon/code/Lexicon/MSAOperations.py`, `ClassName`-discriminated + cast, all
four C1 rows (`MoStemMsa.MsFeaturesOA`, `MoInflAffMsa.InflFeatsOA`,
`MoDerivAffMsa.FromMsFeaturesOA`/`ToMsFeaturesOA`).

**The `#251` trap, which has now burned three prior attempts:** `hasattr` is
False for **0 true / 2088 false** live MSAs through the base-interface view,
because pythonnet resolves attributes against the **STATIC wrapper type**, not
the runtime object. **A `hasattr`-gated fix is 100% dead code.** Discriminate on
`.ClassName` and cast (`IMoStemMsa(obj)` etc.); a wrong cast raises `TypeError`
loudly, which is acceptable and must not be swallowed.

**Next checkpoint: Checkpoint 3a = T6 implemented + live-verified + gated.**
T7/T8 stay closed behind it.

---

# Cycle 8 addendum -- two lead rulings made after the cycle-9 dispatch

## RULING -- the D4-T6 comment on `#250`: **POST.** Not held.

The user delegated this decision to `/lex-lead` ("let the /lex-lead team
decide"). It is therefore ruled, not escalated. **Post the body of
`specs/250-writingsystem-activation/reviews/cycle8-D4-T6-comment-draft.md`
verbatim as a comment on flexicon#250. Do NOT close #250. Do NOT edit its body,
title or labels.** That is the entire authorisation.

**Why post.** The draft's own stated precondition was the cycle-8 gate returning
PASS, and it did, on every leg. The decisive argument is disclosure, not
tidiness: the asymmetry is in `main` **today** and is undisclosed. A phoneme
synced across a case- or separator-divergent writing system now saves its `Name`
and `Description` alts and **still silently drops its `BasicIPASymbol` alt** --
one object, one sync call, two outcomes, no warning either way. Anyone syncing
right now is exposed and cannot learn it from the issue. A campaign whose entire
purpose is eliminating silent partial coverage does not get to sit on a silent
partial-coverage disclosure because a later comment would be neater.

**The hold argument, answered rather than waved off.** "T6-T9 will change what
#250's neighbourhood looks like" is true of the feature area and false of this
comment: T6-T9 are feature-structure sync work on MSA/POS/Allomorph/Phoneme;
they touch neither WS-resolution site (`#266`/`#267`) nor Defects 1-3. Nothing in
the comment is at risk of being invalidated, so the "post now plus a correction
later" scenario does not arise. A follow-up when `#266`/`#267` close is an
ordinary additive comment, not a correction. And the real alternative to posting
now is not "post later" -- it is "the information stays in a repo file no issue
reader will ever find".

**Facts re-verified before authorising** (a public comment is hard to retract,
so none of it was taken on trust):

- `#250`, `#266`, `#267` all exist, all OPEN, titles matching the draft's
  descriptions.
- The three-site frozen set is confirmed by cycle 8's tracked, hash-verified
  ratchet probe, whose failure message named the 4th site exactly as predicted.
- The asymmetry is confirmed **from the shipped source**, not inferred.
  `PhonemeOperations.ApplySyncableProperties` carries the comment "BasicIPASymbol
  and Features need dedicated handling; everything else (Name, Description, and
  any future plain scalars) goes through the base loop", and
  `__ApplyBasicIPASymbol` then builds its own `{ws.Id: ws.Handle}` map and runs
  its own resolution loop.
- Gate leg 6 found zero artifacts claiming D4-c is live-verified; the comment
  does not claim it either.

The draft file's header was updated in the same commit, because leaving a file
that says "NOT POSTED / needs the user's approval" next to a posted comment is
exactly the artifact-contradicts-the-world defect leg 6 went looking for.

## FLAG FOR THE CYCLE-10 GATE -- the `clr.GetClrType` alarm, and what checking it actually turned up

The flag raised was: Pyright shows **`clr.GetClrType` at `~:1170`** of
`flexicon/code/Lexicon/MSAOperations.py`, and since T6's entire premise is *how*
MSA subtype discrimination is done, a CLR-type-identity approach could satisfy
the cycle-9 prompt's "zero hasattr gates, prove it with a grep" while still not
being the frozen C1/R2 `.ClassName`-plus-cast pattern. CLR type identity is the
same family of hazard as the original trap -- static-versus-runtime type -- so it
could work for factory-fresh concrete objects and fail for objects arriving via
`GetAll()` / `Find()` / `Object()`. That was a sound thing to flag.

**T6 had already landed and committed by the time this reached the lead** (HEAD
`a60cc83`), so reading the shipped line cost nothing and no agent was
interrupted. Three findings, and they do not all point the same way.

**Finding 1 -- the GetClrType alarm does NOT survive inspection. Downgrade it.**
`:1170` is inside `__CreateAndAttach`, and it reads
`ServiceLocator.GetService(clr.GetClrType(factory_interface))`. That is the
service-locator idiom -- pythonnet's `GetService` overload needs the
`System.Type` form of the interface -- and it performs **no type discrimination
whatsoever**. It is also **pre-existing**: it sits at the identical `:1165`/`:1170`
in T6's parent. It surfaced now only because T6 added ~330 lines above it and
Pyright re-reported a shifted line. Not a fourth variant of the trap.

**Finding 2 -- the actual discrimination is CORRECT, and is the frozen pattern.**
`__ResolveMsa` at `:1149-1158` reads `getattr(obj, "ClassName", None)` and looks
it up in a `{ClassName: interface}` dict, casting only on a hit and returning the
object **unchanged** on a miss. The Get/Apply dispatchers at `:898` and `:992`
likewise branch on `msa.ClassName`. The docstring at `:891` states "Zero
`hasattr` gates on any feature-struct property: dispatch is entirely
`.ClassName`-driven". The out-of-table path returns rather than raising, which is
ruling R2 satisfied. **The gate still confirms this rather than taking the lead's
read for it** -- specifically that `__ResolveMsa` is the *only* discrimination
path the new methods use, and it must be settled **by mutation with a live
base-interface MSA** (`GetAll()` / `Find()` / `Object()`), not by reading. The
0-true/2088-false measurement is exactly why reading is not enough here.

**Finding 3 -- NEW, and the genuinely interesting one. Pre-existing `hasattr`
gates on LCM properties survive at `:545`, `:550`, `:555`**, inside
`ChangeAffixVariant`: `hasattr(deriv_src, "FromInflectionClassRA")`,
`"ToInflectionClassRA")`, `"StratumRA")`. These are **not** feature-struct
properties, so they are outside T6's scope and outside the cycle-9 prompt's
grep -- which is precisely how they survived. But they are `hasattr` probes
against LCM properties on an MSA, which is the **#251 trap's own shape**. If
`deriv_src` there is ever base-interface-viewed, all three are silently False and
those branches are dead code that quietly drops data. **Cycle 10 must determine
whether `deriv_src` is base-interface-viewed at that point and report; it must
NOT fix it inline** -- that is a separate defect with its own blast radius, and
folding it into T6's gate would repeat the scope creep this campaign keeps
ruling against.

**Two smaller Pyright findings in the same file, for the gate:**

- `:1155` passes `Any | None` where a `str` key is expected. (Note this is inside
  the `.ClassName` dict lookup -- benign as written, since `.get(None)` simply
  misses, but the type should be narrowed.)
- `FP_ReadOnlyError` and `FP_NullParameterError` are imported but unused at
  `:60-61`. An unused `FP_ReadOnlyError` deserves a second look rather than a
  reflexive delete: the project rule is that write operations check
  `writeEnabled` first, so an unused import may be the symptom of a **missing
  write guard** rather than dead code. Decide which, then act.

---

# Cycles 9-10 (spurt 8) -- T6 lands, gate PASSES. **Checkpoint 3a is CLOSED.**

T6 is DONE and gated. `MSAOperations` now has
`GetSyncableProperties`/`ApplySyncableProperties`, `ClassName`-discriminated and
cast, covering all four in-scope C1 MSA rows. Six commits: `04b50407`
(production), `941a29eb` (.pyi), `23227b64` (tests), `f7ab3a69` (CHANGELOG),
`e356670e` + `e022a783` (live evidence). Gate artifacts committed at `f062a460`.

- Implementer report: `reviews/cycle9-programmer-T6.md` (now carries a LEAD
  CORRECTION block appended at the end)
- Gate report: `reviews/cycle10-verification-T6-gate.md` -- **GATE: PASS**
- Gate evidence: `evidence/live-cycle10-T6-gate.md`

## The central #251 question is ANSWERED YES

This is the finding that matters, and it is the one three prior attempts got
wrong. The discrimination **holds against genuine base-interface views**: three
live tests call `sandbox.Object(hvo)` -- a bare `ICmObject` obtained via
`ServiceLocator.GetObject` -- before `GetSyncableProperties`, and all three
round-trip. Entry paths are genuine re-fetches, never the factory handle held at
write time. **#251's trap is not repeated.** T6 is substantively correct and
nothing about it is reverted.

Also verified clean: the offline suite is substantially falsifiable (9 of 21 go
red under forced dispatch, so it is not decorative); R3 holds
(`_MSA_PROP_BY_CLASS_AND_SLOT` is test-only, never referenced from `flexicon/`);
the comparator reproduces at 392 passed / 2 failed / 510 deselected across two
independent runs with the pinned foreign pair unchanged; `run_mode: live`
throughout; every mutation ran in a disposable worktree with hash-verified
reverts and the shared tree untouched.

## RULING on the P0 -- the dead C2 cast: **KEEP it, TEST it, and correct the claim.**

The gate mutated `__GetMsaObject`'s ClassName cast away entirely and **all six
live tests stayed green**, including the one built to prove C2. NOT-KILLED.
`_ResolveFeatureStrucOwner` re-derives `.ClassName` and re-casts independently,
so the eager cast cannot change an observable outcome on any path this module
currently exercises.

**Do NOT delete it.** Three reasons:

1. **C2 is a family-wide clause**, not a local optimisation: "every
   `__Get<X>Object` resolver in this feature's blast radius must cast before
   returning." Deleting MSA's compliance because a second layer currently
   compensates would make `MSAOperations` the one class in the family that
   violates C2.
2. It is one refactor from load-bearing. The moment any code reads a
   subtype-only member directly rather than through `_ResolveFeatureStrucOwner`,
   the cast is what stands between us and #251's exact failure mode.
3. The defect here was never the cast. **The defect was the claim.** Removing
   working defensive code to resolve a documentation error is the wrong lever.

**But unexercised code must not stay unexercised** -- that is how it rots or gets
deleted by a future reader with less context. T6b adds a DIRECT,
mutation-resistant test on `__GetMsaObject` for both the HVO(int) and GUID(str)
paths, and that test must be verified to DIE when the cast is removed.

**Credit where it is due:** `__GetMsaObject`'s own docstring already says this
module "avoids that specific failure mode by routing all subtype access through
`_ResolveFeatureStrucOwner` (which casts internally regardless)" and justifies
the eager cast on symmetry with the sibling C2 fix sites. The evidence file was
equally candid. **The code and the evidence were honest; the summary was not.**
The caveat was dropped exactly once, at the report layer, and became
"Live-proven". That is the cheapest failure mode in this whole campaign to
repeat, and it is why the correction is appended to the report itself rather
than quietly noted here.

## RULING on the tautological clauses: **non-blocking, but they do NOT ride quietly.**

Four claims are narrower than written -- C7-offline (mocks the thing it tests),
C6-presence-gate (fixture Guid is truthy, so presence and truthiness coincide),
R2-live (structurally undecidable), and the zero-`hasattr` AST test (inspects
neither function where discrimination actually lives). Each is recorded in the
LEAD CORRECTION appended to `reviews/cycle9-programmer-T6.md`.

They do not block Checkpoint 3a: in every case the clause **is** enforced, just
by a different test than the report credited (C7 by the live test, C6 and R2 by
the static AST tests). No contract is actually unenforced.

**But they are fixed BEFORE T7, not after.** T7 (`POSOperations`) and T8
(`AllomorphOperations`) will copy T6's test patterns -- that is the point of
having a template. Letting three decorative patterns replicate into two more
modules and sweeping them later is precisely the trade spec section 6.3 rejected
when it sequenced #250 Defect 4 *before* T6 rather than after T8. Same argument,
same answer. **T6b runs first.**

## Leg 7 resolved -- and the flag was over-weighted

The `ChangeAffixVariant` `hasattr` gates at `:545`/`:550`/`:555` are **not** a
trap repeat. `deriv_src` at `:541` is already `concrete_src = IMoDerivAffMsa(msa)`
from `:526`, so those gates run against a concrete cast; confirmed live, all
three return `True` on a real `MoDerivAffMsa`. Redundant, not data-dropping. **No
follow-up issue is warranted and none should be filed.** Recorded so nobody
re-derives it. The main session flagged it and then reported its own flag as
over-weighted once the gate settled it -- that self-correction is the behaviour
this crew wants, and it cost one cheap leg to buy certainty.

## #250 -- the D4-T6 comment is POSTED

Posted verbatim per the lead ruling, at
`issues/250#issuecomment-5576611010`. **#250 confirmed still OPEN**; body, title
and labels untouched; nothing else on GitHub changed.

## #251 is NOT closed on GitHub, deliberately

It is fixed on the merits and closeable, but closure waits on T6b so the closing
comment can state accurate coverage rather than restate the withdrawn C2 claim.
Closure also needs its **own** user authorisation -- the delegation the user gave
for the #250 comment was specific to that comment and does not generalise to
closing issues.

## Next pickup -- **T6b, then T7**

`next_checkpoint` = Checkpoint 3b = T6b landed and gated. T7/T8 stay closed
behind it. T6b is small, test-only, and needs the live token for item 1's
mutation check.
