# STATUS -- name-field-whitespace-identity

**Campaign:** `tier1-silent-data-loss`, spun-out sub-item **2a** (between
queue item 2, `242-paragraph-whitespace`, and queue item 3,
`feature-structure-sync-gap`) -- **`active`**.
**Last updated:** 2026-09-07, **end of cycle 6 -- SUB-ITEM 2a COMPLETE**.
Checkpoint 1 DONE; **Checkpoint 2 DONE -- 8 of 8 sites landed** (T1, T2, T3,
T4); **Checkpoint 3 DONE** (T5 docs, plus the cycle-6 micro-fix). **No tasks
remain. `/lex-lead` APPROVED at cycle 6 and emitted `FEATURE COMPLETE` for
sub-item 2a only -- the `tier1-silent-data-loss` campaign remains OPEN with
items 3 and 4 unauthorised.**
**Status:** Contract items **C1-C13 FROZEN** -- C12 and C13 were ruled by
`/lex-lead` at the cycle-4 close and are recorded in the "Cycle 4 close"
section below; their verbatim transcription into `spec.md` is PENDING and
rides with the T5 spurt. Behaviour change has landed under `flexicon/code/`
from this feature in **four** files: `TextsWords/DiscourseOperations.py` (T1),
`TextsWords/TextOperations.py` (T2), `Notebook/AnthropologyOperations.py` (T3),
`System/CheckOperations.py` (T4). See the "Cycle 4 close" section at the FOOT
of this file for the authoritative next pickup; every earlier "Next pickup" and
the "Cycle 3 close" section are superseded.

> **A SECOND CREW is committing in this same clone right now** (confirmed
> by the project owner as theirs and expected). See `CONCURRENCY.md` --
> binding on every future spurt. `flexicon/code/BaseOperations.py`,
> `flexicon/code/Grammar/NaturalClassOperations.py`, and
> `flexicon/code/Grammar/PhonemeOperations.py` show as modified in
> `git status` at the time of this pass -- **none of that is this
> feature's work**; do not stage it, do not attribute it here, do not
> revert or restore it.

---

## What landed at Checkpoint 1 (this spurt)

- **`spec.md`** -- authority/provenance record (section 0: `/lex-lead`
  ruled C1-C8, the owner then placed the identity question (C3) under
  `/lex-domain`'s authority, `/lex-domain` independently re-tested and
  ACCEPTED option (i)); the problem statement (Q-242A/Q-242B); eight
  frozen contract items (C1-C8): the needle-only-strip mechanism (C1), the
  persist-only-fix-produces-duplicates correction to #242 C10 (C2), the
  whitespace-insensitive-dedup ruling with lex-domain's independent
  grounds (C3), the fix shape and shared-code fence (C4), the four-file
  scope (C5), the Q-242A/Q-242B bundling rationale (C6), the Q-242B fix
  shape and the Q-242C boundary (C7), and the anti-regression pin (C8); a
  recorded-not-ruled section on the unrelated `_GetCheckList` bug; a
  contradiction check (none found); and open questions (none left open in
  scope).
- **`tasks.md`** -- a READ FIRST section carrying forward #242's standing
  gates plus `CONCURRENCY.md`'s DELTA rule (replacing the VOID fixed
  offline baseline); Checkpoint 1 (this spurt, DONE); Checkpoint 2 (T1
  Discourse, T2 Text, T3 Anthropology, T4 Check -- Q-242A and Q-242B
  landed together at the same expressions per C6, tracked with separate
  evidence); Checkpoint 3 (T5, docs dispatch to `/lex-doc`).
- **`STATUS.md`** (this file).
- **`.crew-handoff.json`**.
- **`CONCURRENCY.md`** -- already on file, written by the main session,
  read and treated as binding by this pass.
- **Live probe** -- `tests/operations/test_name_field_identity_probe.py`,
  8/8 passing (PN1-PN8), `run_mode: live`,
  `target_sandbox`/`target_sandbox_path` fixtures only, real Target
  untouched, no `scripts/restore_*.py` run. Predictions committed
  (`bdbce02`) before the measuring run -- the C28 forward rule. Offline
  baseline at cycle-1 time: **1292 passed, 491 deselected** (deselected
  rose 483 -> 491, exactly +8 for the new live tests) -- this absolute is
  now **VOID** per `CONCURRENCY.md`'s DELTA rule for any future spurt.
- **Reviews on file** -- `reviews/cycle1-programmer.md`,
  `reviews/cycle1-domain.md`.
- **Evidence on file** -- `evidence/live-probe-cycle1.md`.

## Headline findings (see `spec.md` for full detail and citations)

1. **The C1-C8 ruling's premise is CONFIRMED, not refuted.** `Exists`/
   `Find`/`FindCheckType` all strip only the search needle, never the
   stored haystack -- live-confirmed at all three families (PN2/PN3/PN4).
2. **`Create()`'s own duplicate guard inherits this blind spot.** A
   layer-B-written name carrying a trailing space is invisible to
   `Exists()`, so `Create()` mints a second object a human would call by
   the same name (PN8, binding claim MATCHED). One non-binding sub-detail
   -- the second record's stored name was not byte-identical to the first
   under CURRENT, pre-fix code -- was flagged before the run as an
   artifact of testing against unfixed persist behaviour, not a
   contradiction of C2.
3. **`CheckOperations.CreateCheckType` silently converts both a non-str
   payload and a whitespace-only string into a persisted empty name with
   no exception** (Q-242B, PN5/PN6 both MATCHED), via
   `name = name.strip() if isinstance(name, str) else ""` plus a
   None-only `_ValidateParam`.
4. **`/lex-domain` independently re-tested and ACCEPTED `/lex-lead`'s
   option (i)** -- whitespace-insensitive comparison, raw-byte
   persistence -- on independent FLEx-domain grounds: the uniqueness
   guard at all three families is a flexicon invention, not a FLEx/LCM
   invariant (FLEx's own Texts & Words organizer enforces zero title
   uniqueness).
5. **An unrelated, unplanned bug was found and NOT fixed:**
   `CheckOperations._GetCheckList()` is a hardcoded stub whose
   fallback path calls a nonexistent `ServiceLocator.GetInstance(...)`
   (should be `.GetService(...)`), making `CreateCheckType()` raise
   `AttributeError` on every call against a live LCM. Worked around at
   the test-instance level only (zero `flexicon/` lines changed);
   recorded in `spec.md` section 3 as a live-verification dependency for
   every future task touching `CheckOperations.py`.

## Contradictions found and preserved

**None.** All binding predictions (PN1-PN4, PN7, PN8's binding claim)
MATCHED. The one non-binding MISS (PN8's byte-identity sub-detail) is
folded into `spec.md` C2 as a measurement-artifact correction, not a
contradiction. `/lex-domain`'s ruling independently re-derived C3's
answer and agrees with `/lex-lead`'s option (i) in substance -- see
`spec.md` section 0 for the full authority/provenance record.

## Next pickup

**Checkpoint 2** (`tasks.md` T1-T4): implement the direct fix, one task
per family, in order Discourse -> Text -> Anthropology -> Check, each
landing its persist fix and comparison-symmetry fix (where applicable)
together. **T4 also lands the distinct Q-242B fix at the same
expressions as T4's Q-242A half**, per `spec.md` C6, tracked with
separate evidence/severity/CHANGELOG entries. Then **Checkpoint 3** (T5,
docs dispatch to `/lex-doc`).

## Hard constraints for any future spurt on this feature

- **Read `CONCURRENCY.md` before every spurt.** Never stage, revert, or
  restore a path you did not author. Explicit `git add <path>` only.
- **The DELTA rule replaces the fixed offline baseline** for the duration
  of the concurrency situation -- measure before/after your own edits
  only; treat `CONCURRENCY.md`'s named foreign failures as foreign.
- `target_sandbox` / `target_sandbox_path` fixtures ONLY -- never the real
  Target, never any `scripts/restore_*.py` run.
- Derive every live count with `--collect-only -q -m requires_live_project`.
  "No tests collected" is a ZERO, never a pass. Never bare `pytest`.
- The C28 forward rule: commit predictions BEFORE the measuring run.
- `tests/operations/test_name_field_identity_probe.py` already exists --
  EXTEND it per-task, do not duplicate it, unless a task's scope
  genuinely needs a dedicated file.
- No GitHub issues filed from inside this feature. The `_GetCheckList`
  bug and Q-242C stay recorded-not-filed.
- C1-C8 are FROZEN. Do not implement C4's fix with any variation (a
  shared helper, editing `normalize_match_key`, a per-family exception)
  without citing and overturning the relevant contract item by number. If
  `Shared/string_utils.py` or `BaseOperations.py` must change: STOP,
  `needs_human`.
- Do not touch `specs/feature-structure-sync-gap/` or
  `specs/250-writingsystem-activation/` from inside this feature.
- Do not edit `specs/tier1-silent-data-loss/.crew-handoff.json` from
  inside this feature -- that campaign-level file is the main session's
  to maintain.

---

## Cycle 2-3

- **T1 landed** (`DiscourseOperations`): `SetChartName` fully live-verified
  (persist byte-identical, re-read from the LCM). `CreateChart`'s persist
  half is `FAIL: unverified`, blocked by two independent pre-existing
  defects unrelated to this feature's edit -- recorded as **Q-DISC1**.
- **T2 landed fully green** (`TextOperations`): both C8 halves (second
  `Create()` call raises "already exists"; first record re-reads
  byte-identical) confirmed live.
- The baseline re-derivation and the `CONCURRENCY.md` amendment landed at
  `67114c8`.
- **C9, C10, C11 frozen** in `spec.md`: C9 is the `_GetCheckList`
  live-verification workaround boundary governing T4; C10 mandates the
  `## WHAT WAS NOT EXERCISED` disclosure section (retro-fitted to
  `evidence/live-t1-discourse-fix.md` and `evidence/live-t2-text-fix.md`)
  and records the Q-242B severity correction (also reachable by an
  ordinary whitespace-only `str`); C11 governs per-site fix SHAPE
  (Shape A vs Shape B) and records the three-site whitespace-only
  carve-out.
- **Q-CHK1, Q-DISC1, and Q-242D recorded** in
  `specs/tier1-silent-data-loss/QUEUE.md`'s "Awaiting user approval"
  section, all UNAUTHORISED pending user approval.

---

## Cycle 3 close -- Checkpoint 2 is 6/8 sites landed (AUTHORITATIVE next pickup)

**Spurt 3 ended here by design.** T4 was deliberately NOT chained into this
spurt; it is the entire next spurt.

### What landed in cycle 3

- **T3 landed fully green** (`Notebook/AnthropologyOperations.py`, commits
  `7bc6d01` predictions / `ab638aa` code+test / `7409ad6` results). Four sites
  re-confirmed by symbol lookup before editing: `Create`, `CreateSubitem`
  (Shape B per C11(a) -- throwaway non-reassigning `.strip()`, duplicate
  trailing `_ValidateParam` deleted per C11(b)), `Find` (inline strip on BOTH
  sides, `casefold=False` and the early-return short-circuit unchanged), and
  `Exists` (untouched, deliberately).
- **All six T3 predictions MATCHED live.** `15 passed`, `run_mode: live`,
  collect count 15 (11 existing + PN12-PN15). Offline delta `+0/+0/+0`; the
  same three known-foreign failures by name and message, no fourth at any
  point.
- **C8 pin green on BOTH halves** at Anthropology: the second
  `Create('TEST_NF_Anth ')` RAISES `FP_ParameterError: ... already exists`, and
  the first item re-reads byte-identical `'TEST_NF_Anth '` from the LCM after
  the rejected attempt (genuine re-query, not an echo of the input).
- **Q-242D measured, not fixed** (PN15): `Create("   ")` now persists the
  literal three-space string (was `''` pre-fix), raising nothing. Disclosed,
  per C11(c); T5 must carry it as a known remaining gap.
- **Archivist scribe pass** (`bdf98cc`): C9/C10/C11 transcribed verbatim into
  `spec.md`; Q-CHK1/Q-DISC1/Q-242D appended to the campaign QUEUE.md's
  "Awaiting user approval"; the C10(b) Q-242B correction appended beneath the
  preserved-verbatim row; tasks.md READ FIRST items 14-16; CONCURRENCY.md line
  numbers re-derived; `## WHAT WAS NOT EXERCISED` retro-fitted into the T1 and
  T2 evidence files per C10(a). **Zero transcription deviations.**

### Concurrency incident -- occurred, corrected, and the rule is now stronger

T3's first predictions commit swept in five of the other crew's files because
their `git add` landed **between** T3's pre-`add` `git status` check and T3's
own commit. T3 self-caught it via `git show --stat HEAD` and corrected with
`git reset --soft HEAD~1` + index-only `git reset HEAD -- <foreign paths>`
(zero working-tree bytes touched), then re-committed clean.

`/lex-lead` independently audited the final history and **confirms it is
clean**: `7bc6d01` contains only the evidence file, and the other crew's work
landed separately as their own commit `6643b48`. No cross-contamination
survived into HEAD.

**`CONCURRENCY.md` now carries AMENDMENT 2 as a binding rule from T4 onward:**
re-run `git status --porcelain` immediately BEFORE `git commit` (not only
before `git add`), and verify with `git show --stat HEAD` immediately AFTER.
The pre-`add` check alone is structurally unable to catch this race.

### Independently verified by /lex-lead this cycle

`normalize_match_key` returns `""` for `None` / empty / `***` inputs, so the
haystack-side `.strip()` T3 added to `Find` -- applied to a value derived from
`ITsString(...).Text`, which CAN be `None` -- cannot raise on an item with no
name. The same reasoning clears T2's landed `Exists`. **No latent crash at
either site.**

### Line numbers drifted a THIRD time -- re-derive again before T4

Measured at HEAD immediately before this handoff: `_ValidateStringNotEmpty` is
`BaseOperations.py:3191` (CONCURRENCY.md's own re-derivation earlier the SAME
DAY said `:3182`); `_ValidateParam` is `:3023` (was recorded `:3014`);
`_ValidateParamNotEmpty` is `:3085`. The other crew's `6643b48` moved them
again. **Cite by symbol, never by a line number you did not derive yourself in
the current session.**

The three `CheckOperations.py` sites, by contrast, were confirmed UNCHANGED at
HEAD and still carry the coercion verbatim:
`name = name.strip() if isinstance(name, str) else ""` at **`:196`**
(`CreateCheckType`, def at `:146`), **`:341`** (`FindCheckType`, def at `:300`),
and **`:432`** (`SetName`, def at `:397`).

### Next pickup -- Checkpoint 2, T4 (`CheckOperations`), then Checkpoint 3, T5

**T4 is the whole next spurt.** It is the hardest of the four: it lands Q-242A
AND Q-242B in ONE commit at the SAME expressions (C6), it is the only task
gated behind the `_GetCheckList` workaround (C9), and it is the only task whose
target sites are governed by C7's explicit fix shape rather than C11's Shape
A/B choice. Do not bundle T5 into it.

---

## Cycle 4 close -- Checkpoint 2 is DONE, 8/8 sites landed (AUTHORITATIVE next pickup)

**Spurt 4 ended here by design.** T5 was deliberately NOT chained on after T4;
it is the entire next spurt, and it is the last one.

### What landed in cycle 4

- **T4 landed** (`flexicon/code/System/CheckOperations.py`), commits `2d8bfc5`
  (predictions, C28) / `0ab9c60` (code + tests) / `cbbb55e` (results) /
  `f5291e9` + `785d5ee` (report). Q-242A and Q-242B landed in ONE commit at the
  SAME three expressions per C6, tracked with TWO evidence files.
- **C7's exact shape at all three sites**: the coercing rebind
  `name = name.strip() if isinstance(name, str) else ""` and the duplicate
  trailing `_ValidateParam` were replaced by
  `self._ValidateStringNotEmpty(name, "name")` with **no reassignment of
  `name`**; the LEADING `_ValidateParam` was kept per C7(a).
  `FindCheckType` additionally strips **both** the needle key and the haystack
  key inline, `casefold=True` unchanged.
- **20/20 live, `run_mode: live`, collect count 20** (15 prior + PN16-PN20).
  All nine predictions (T4A-P1..P4, T4B-P1..P5) matched exactly. Offline delta
  **`+0/+0/+5`**; the same three known-foreign failures with unchanged
  messages, no fourth. C8 pin green on both halves at `CreateCheckType`.
- **No line-number drift this cycle** -- all five re-derived figures matched
  the cycle-3-close values.

### Independently verified by /lex-lead this cycle (not taken on report)

- `git show 0ab9c60 -- flexicon/code/System/CheckOperations.py` is exactly
  C7's shape at exactly three sites and touches nothing else. The true code-file
  numstat is **`+5 / -8`** (13 lines touched), not the `+13/-13` quoted in the
  cycle-4 relay -- a relay mis-statement only; the diff shape is correct.
- The test-file deletions in `0ab9c60` (`+509 / -63`) are **only** the pre-fix
  assertions inside PN4/PN5/PN6, correctly flipped to assert the fixed
  behaviour with the pre-fix behaviour preserved in each docstring. **No
  existing pin was weakened or removed.** The file now holds exactly 20
  `test_` functions, matching the collect count.
- **`git stash list` and the stash reflog are both EMPTY** -- T4's
  stash/measure/pop left no residue and no foreign working-tree change is
  sitting in a stash.
- **Blast radius of the `FindCheckType` breaking change is external callers
  only.** The single internal call site is `CheckOperations.py:199`, inside
  `CreateCheckType`, which validates `name` immediately beforehand. No other
  module in `flexicon/` calls `FindCheckType`.
- The existing `FindCheckType` docstring is **internally inconsistent** and T5
  must resolve it, not merely append to it: its `Raises:` section already
  promises `FP_NullParameterError: If name is None or empty` (a promise the
  pre-fix code never kept), while its `Notes:` say
  `- Returns None if not found (doesn't raise exception)`. Post-fix the method
  raises `TypeError` for non-`str` and `FP_ParameterError` (**not**
  `FP_NullParameterError`) for whitespace-only.

### Lead rulings at the cycle-4 close

- **C12 (FROZEN, transcription into `spec.md` pending -- rides with T5).**
  `CONCURRENCY.md` AMENDMENT 2 is **retained and vindicated**. On T4's 4th
  commit the pre-`commit` status re-check caught five of the other crew's
  `specs/feature-structure-sync-gap/` files already staged in the shared index,
  landed there after T4's own `git add`. T4 cleared them with an index-only
  `git reset HEAD -- <paths>` (zero working-tree bytes), re-confirmed, then
  committed; `f5291e9` is confirmed to contain exactly one file. The amendment
  caught, at its intended catch point, the exact failure that motivated it.
  **Recommendation (main session's call, not this feature's):** copy AMENDMENT
  2 verbatim into `specs/tier1-silent-data-loss/.crew-handoff.json`'s
  hard_rules so campaign items 3 and 4 inherit it. That file is the main
  session's to maintain and must NOT be edited from inside this feature.
- **C13 (FROZEN, transcription into `spec.md` pending -- rides with T5).**
  T4's self-disclosed order slip -- the code edit preceded the "before" offline
  baseline, against STEP 4 -- is **accepted, and the `+0/+0/+5` delta stands as
  measured; no re-derivation is ordered.** Grounds: (a) T4 corrected by
  stashing its own edit, measuring the true pre-edit tree at the same HEAD, then
  popping, which yields a genuine before/after pair rather than a
  reconstruction; (b) the C28 predict-before-measure guarantee is intact --
  `2d8bfc5` landed before the measuring run; (c) the delta is independently
  corroborated by the collect count moving 15 -> 20, exactly the `+5` claimed;
  (d) `git stash list` is empty, so the pop was complete. **Forward rule:** the
  stash/measure/pop recovery is ALLOWED in this clone, but ONLY with an
  explicit pathspec (`git stash push -- <your own path>`); a bare `git stash`
  would sweep the other crew's uncommitted work and is FORBIDDEN, alongside
  `git reset --hard`.

### Recorded, not fixed

- `_ValidateStringNotEmpty`'s own `None` branch is dead code at all three
  `CheckOperations` sites, because the leading `_ValidateParam` (kept per C7a)
  catches `None` first. Observation only.
- `Q-242D` is unchanged: whitespace-only input still persists literal
  whitespace at the three Shape-B sites. T5 MUST disclose it.
- `Q-DISC1` is unchanged: `DiscourseOperations.CreateChart`'s persist half
  remains **`FAIL: unverified`** -- inspection-correct but unreachable through
  its own public API. T5 MUST record this rather than claim 8/8 verified.

### Unrelated working-tree observation (NOT this feature's, do not act)

`git status --porcelain` at this handoff shows `.claude/ralph-loop.local.md`
as **deleted (unstaged)**, plus a modified
`specs/feature-structure-sync-gap/spec.md` and two untracked paths. None of
that is this feature's work; per `CONCURRENCY.md` it must not be staged,
restored, or reverted from inside this feature. Flagged to the main session
only because a missing `.claude/ralph-loop.local.md` may matter to the loop
harness.

### Next pickup -- Checkpoint 3, T5 (docs), the LAST spurt

**T5 is docs-only; there is no live-verification requirement.** Full brief in
`.crew-handoff.json` -> `next_entry`. In outline:

1. **`/lex-doc` authors the patches directly** (it edits files; it has **no
   shell tool** and therefore cannot run `pytest` or `git` -- it must not be
   asked to verify or commit, and must not be blamed for refusing to).
2. **Two separate `CHANGELOG.md` entries** under `[Unreleased]`, per C6 -- one
   for Q-242A, one for Q-242B, following the #242 precedent already in the file
   at `CHANGELOG.md:95` (a `### Changed` item led by
   `**BREAKING (behavioural): ...**`). Divergence is `/lex-doc`'s call to make
   and record.
3. **Docstring updates on the 11 touched methods** across the four files.
4. **Mandatory disclosures**: Q-242D as a known remaining gap; Q-DISC1 /
   `CreateChart` as `FAIL: unverified`; the `FindCheckType` behavioural break.
5. **The main session performs every shell action** -- the AMENDMENT 2 commit
   bracket and the commit itself. `/lex-doc` returns a report path plus a
   2-line summary and nothing else.
6. Optionally an archivist pass to transcribe **C12 and C13** into `spec.md`
   verbatim; that transcription is outstanding either way.

---

## Cycles 5-6 close -- APPROVED, sub-item 2a COMPLETE (AUTHORITATIVE final state)

**`/lex-lead` verdict: APPROVED.** All quality gates green, no P0 or P1 open.
`FEATURE COMPLETE` was emitted for **sub-item 2a only**; the campaign promise
`TIER1 COMPLETE` is NOT satisfied and was NOT emitted.

### What landed

- **T5** (`90cfce7`, six files): two separate `[Unreleased]` `### Changed`
  entries per C6, both led `**BREAKING (behavioural):**`; docstring Notes on
  all 11 touched methods; `AnthropologyOperations.Exists` correctly NOT
  documented as changed; `FindCheckType`'s self-contradictory docstring
  RESOLVED (not appended to), with the correction narrated so the diff stays
  legible; the same false `Raises` shape additionally caught and corrected at
  `CreateCheckType` and `SetName` -- sites the dispatch brief had not named.
  Q-242D and Q-DISC1 disclosed in both CHANGELOG and docstrings; **8/8 was
  never claimed**; no GitHub issues filed.
- **C12 / C13 / AMENDMENT 3** transcribed verbatim (`ab494d4`).
- **Cycle-6 micro-fix** (`5c161e1`, four files): the three proven-false
  `Raises` blocks at `AnthropologyOperations.Create`, `.CreateSubitem`, and
  `TextOperations.SetName` corrected to describe today's actual behaviour --
  `None` raises `FP_NullParameterError`; **empty OR whitespace-only** is NOT
  rejected and persists literally (Q-242D named, Q-242C named as owner);
  non-`str` raises `AttributeError` from the throwaway `.strip()`, annotated
  "retained per C7(b); not a deliberate type check". `parent_item` /
  `text_or_hvo` halves untouched, as scoped. **C12(f)** appended verbatim.
  `spec.md`'s own stale header corrected on the main session's initiative --
  RATIFIED (see below).

### Verified by /lex-lead at closure (not taken on report)

- **`90cfce7` and `5c161e1` between them changed ZERO executable lines.** Every
  removed line across all four Operations files is a docstring line; both sets
  were listed and read in full. The offline invariant (`passed` unchanged at
  1292, same three known-foreign failures, no fourth) therefore holds **by
  construction**, and a re-run was explicitly declined as proving nothing.
- **No HTML entity artefact** survived into `spec.md`, `CONCURRENCY.md`,
  `CHANGELOG.md`, or either Operations file, across two transcription rounds.
- **C12(f) is verbatim** as ruled, placed after C12(e) with C13 still following.
- The three corrected `Raises` blocks say exactly what was specified, including
  the widened "empty **or** whitespace-only" scope.

### The one defect found at closure -- a citation error, carried not blocked

`spec.md`'s corrected header attributes T1 (`DiscourseOperations`) to
"**`ab638aa`-adjacent**". `ab638aa` is **T3's** commit
(`fix(anthropology-operations)`). **T1's actual commit is `3eac4a0`**
(`fix(discourse-operations): T1 -- persist caller's original name bytes, not
the stripped local`), verified at closure. T2 (`db95230`), T3 (`ab638aa`) and
T4 (`0ab9c60`) are all cited correctly.

Ruled **P3, clerical** -- it does not touch a gate and does not delay the
close, but it MUST be repaired in the already-scheduled campaign-closure
commit. Exact replacement, one line:

    `flexicon/code/TextsWords/DiscourseOperations.py` (T1, `3eac4a0`),

### Judgement calls ruled at closure

- **The `spec.md` header correction: RATIFIED.** A status header that
  contradicts the record is a C27 defect, and the fix is squarely in-scope for
  a closing commit -- it is a state summary, not a contract item, and nothing
  in it decides anything. Marking it as a correction rather than silently
  rewriting is the right instinct and is precisely how contract-adjacent prose
  should be amended: staleness made legible, not erased. Correct call, correct
  execution, one wrong hash.
- **`docs/MANIFEST.md` absence: RATIFIED as flagged-not-fixed.** Declining to
  bootstrap a repo-wide artefact from a narrowly-dispatched task is right.
  Carried to campaign level as an observation.
- **Cycle 5's "declined to fix three docstrings" call: OVERTURNED IN PART at
  cycle 5, discharged at cycle 6.** The scope instinct was sound; the stated
  reasoning ("correcting docs without code creates a new mismatch in the
  opposite direction") was not, and is REJECTED as precedent -- documenting
  today's behaviour removes a mismatch, it cannot create one. Recorded so no
  future agent cites it.

### Outstanding, all UNAUTHORISED and all owned above this feature

`Q-CHK1`, `Q-DISC1`, `Q-242C`, `Q-242D`. **Q-242C now has TWO dependents** --
Q-242D, and the three `Raises` blocks corrected at cycle 6, which will need
re-correcting if and when Q-242C adds the rejection. Sequence Q-242C ahead of
both.

### Known limitation shipped, deliberately and on the record

`DiscourseOperations.CreateChart`'s persist half is **`FAIL: unverified`**
(Q-DISC1): inspection-correct, unreachable through its own public API, blocked
by two pre-existing unrelated defects. **This feature never claimed 8/8
verified**, in STATUS.md, in `spec.md`, or in the CHANGELOG.

### Next pickup

**None for this feature.** Remaining work is campaign-level and belongs to the
main session -- see `.crew-handoff.json` -> `next_entry`.
