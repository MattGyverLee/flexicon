# TASKS -- name-field-whitespace-identity

Derived from `spec.md` sections 0-5 (C1-C8, FROZEN). Issues: Q-242A, Q-242B
(`specs/tier1-silent-data-loss/QUEUE.md`, sub-item 2a). Campaign:
`tier1-silent-data-loss`.

**AUTHORISED BY THE OWNER, 2026-09-07.** No behaviour change under
`flexicon/code/` has been made by this feature yet. `spec.md` C1-C8 are
frozen; every code task below implements C4 (comparison-symmetry fix) and
C7 (Q-242B fix shape) exactly as ruled, with C8's anti-regression pin as
the acceptance gate.

**MERGED FILE, 2026-09-08.** A second crew wrote this same `tasks.md`
independently on `origin/main` (PR #282) with its own checkpoint set, all
marked BLOCKED/unstarted. It is preserved verbatim in **Appendix B** below;
`spec.md` Appendix A explains why its "not started" status reflected its
branch rather than `main`. The checkpoints in THIS file are the accurate
record of what landed. Cite the other crew's items as
**"NF-n (spec.md Appendix B)"**.

---

## READ FIRST -- binding on every task

1. **`specs/name-field-whitespace-identity/CONCURRENCY.md` is binding.** A
   second, owner-confirmed crew is committing in this same clone right
   now. Never stage a path you did not author (explicit `git add <path>`
   only -- never `-A`, `.`, `-u`, or `commit -a`). Never revert, restore,
   stash, or reset a path you did not author. Treat
   `flexicon/code/BaseOperations.py`,
   `flexicon/code/Grammar/NaturalClassOperations.py`,
   `flexicon/code/Grammar/PhonemeOperations.py`,
   `tests/operations/test_natural_class_feature_sync.py`,
   `specs/feature-structure-sync-gap/`, and
   `specs/250-writingsystem-activation/` as **theirs** -- do not open them
   to edit, do not cite their contents as this feature's state.
2. **The DELTA rule REPLACES the old fixed offline-baseline gate while the
   other crew is active.** `specs/242-paragraph-whitespace/tasks.md`'s
   "offline baseline is 1292 passed" absolute is **VOID** for the
   duration of this feature -- do not chase it, do not "restore" it, do
   not report deviation from it as a regression you caused. Instead:
   - Run `python -m pytest tests -m "not requires_live_project" -q`
     **immediately before your first edit** in each task and record the
     counts.
   - Make your change.
   - Run it again and record the counts.
   - **Report both raw numbers and the delta.** Expected delta for a
     correct change: `passed` unchanged or up by exactly the offline
     tests you added; `deselected` up by exactly the `requires_live_project`
     tests you added.
   - If a test fails in a file you did **not** touch and it is on
     `CONCURRENCY.md`'s known-foreign list (`test_natural_class_feature_sync.py`
     collection errors; `test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies`;
     `test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_no_new_unbracketed_mutations`),
     name it as foreign and move on. If it fails in a file you did not
     touch and is **NOT** on that list, STOP and report -- that one may
     genuinely be yours.
3. **Fixtures:** `target_sandbox` / `target_sandbox_path` ONLY. Never the
   real Target, never any `scripts/restore_*.py` run.
4. **Live verification is REQUIRED** for anything touching an Operations
   class, a factory call, a property setter, or the write path (CLAUDE.md).
   Mock-only is `FAIL: unverified`, never a clean result.
5. **Derive live counts with `--collect-only`, never trust a filename.**
   `python -m pytest <file> --collect-only -q -m requires_live_project`
   and paste the count into the evidence file. **"no tests collected" is
   a ZERO, never a pass.**
6. **Never run bare `pytest`** or `pytest --ignore=tests/contract` --
   neither applies an `-m` filter, so both execute the ~322
   `requires_live_project` tests in place against real projects. Always:
   ```
   $env:FLEXLIBS_REQUIRE_LIVE = "1"
   python -m pytest tests/operations/test_name_field_identity_probe.py -m requires_live_project -q -s
   ```
7. **The C28 forward rule:** a stated prediction is committed BEFORE the
   measuring run, not edited after -- write PREDICTIONS, commit, run the
   live command, then fill in RESULTS in a second commit.
8. **Evidence or it did not happen.** Each task writes
   `specs/name-field-whitespace-identity/evidence/live-<task>.md` with the
   exact command, the `run_mode` value from `tests/live_status.json`, the
   offline-suite DELTA (item 2 above), and pre/post values **re-read from
   the LCM** after the write.
9. **No GitHub issues filed from inside this feature.** The
   `CheckOperations._GetCheckList()` bug (`spec.md` section 3) and Q-242C
   are recorded, not filed.
10. **No emoji in console output** (Windows). Use `[OK]` / `[FAIL]` /
    `[WARN]`.
11. **Extend, do not duplicate:**
    `tests/operations/test_name_field_identity_probe.py` already exists
    from cycle 1 (8 live tests, PN1-PN8, per
    `evidence/live-probe-cycle1.md`). Every task below extends this file
    in place rather than creating a parallel probe file, unless a task's
    own scope genuinely needs a dedicated file (state why, if so).
12. **`CheckOperations._GetCheckList()` dependency (`spec.md` section 3):**
    every live task touching `CheckOperations.py` must reuse the same
    test-instance-only `_GetCheckList` monkeypatch pattern
    (`_seed_valid_check_list()` in the cycle-1 probe file) to reach
    `CreateCheckType`'s own name-handling logic. This is a live-verification
    workaround only -- do not fix the underlying bug, do not remove the
    workaround once a task lands.
13. **C1-C8 are FROZEN.** Do not implement C4's fix with any variation
    (a shared helper, a `normalize_match_key` change, a per-family
    exception to symmetric stripping) without citing and overturning the
    relevant contract item by number. If an implementer concludes
    `Shared/string_utils.py` or `BaseOperations.py` must change: **STOP,
    `needs_human`** (C4).
14. **C9** (`spec.md`) is the CheckOperations live-verification workaround
    BOUNDARY -- only a test-instance-only `_GetCheckList`-alone monkeypatch
    returning a real LCM `ICmPossibilityList` is authorised; see `spec.md`
    C9 for the full NOT-authorised list.
15. **C10** (`spec.md`) requires a `## WHAT WAS NOT EXERCISED` section in
    every evidence file from cycle 3 onward, and records the Q-242B
    severity correction (also reachable by an ordinary whitespace-only
    `str`, not just non-`str`).
16. **C11** (`spec.md`) governs per-site fix SHAPE (Shape A vs Shape B,
    chosen by the site's own upstream guard) and the three-site
    whitespace-only carve-out recorded as Q-242D.

---

## Checkpoint 1 -- Spec + live probe (THIS SPURT)

**DONE, 2026-09-07.** Delivered:

- [x] `spec.md` -- contract items C1-C8 (transcribed, FROZEN), the
      authority/provenance record (section 0), the problem statement, the
      recorded-not-ruled `_GetCheckList` bug, the contradiction check, and
      open questions.
- [x] `tasks.md` (this file).
- [x] `STATUS.md`.
- [x] `.crew-handoff.json`.
- [x] `tests/operations/test_name_field_identity_probe.py` -- 8/8 live
      tests passing (PN1-PN8), `run_mode: live`,
      `target_sandbox`/`target_sandbox_path` fixtures only. Delivered by
      `/lex-programmer` in cycle 1.
- [x] Two cycle-1 reviews on file: `reviews/cycle1-programmer.md`,
      `reviews/cycle1-domain.md`.
- [x] `evidence/live-probe-cycle1.md` -- predictions committed before the
      measuring run (`bdbce02`), results filled in after, `run_mode: live`,
      8/8 passing.
- [x] `CONCURRENCY.md` -- the binding protocol for the shared working tree.

**Checkpoint:** spec + probe on file. `flexicon/` shows unrelated
modifications from the concurrent crew (see `CONCURRENCY.md`); this
feature's own diff to `flexicon/` remains empty. **No code task below may
begin without following the READ FIRST rules above, especially item 1
(concurrency) and item 2 (the DELTA rule).**

---

## Checkpoint 2 -- Implement the direct fix, one task per family (**DONE, 4 of 4 -- 8/8 sites landed, cycle 4**)

Sequenced so the comparison-symmetry fix (C4) and the persist fix land
TOGETHER per family -- never a persist fix without its comparison fix,
since that is the C2 duplicate-explosion hazard. Order: Discourse first
(no comparison, smallest, lowest risk), then Text, then Anthropology, then
Check (which also carries the distinct Q-242B task).

### [x] T1 -- `DiscourseOperations` (LIVE) -- **DONE, cycle 2** (`3eac4a0`). `SetChartName` fully live-verified; `CreateChart`'s persist half is `FAIL: unverified`, blocked by two pre-existing unrelated defects, recorded as **Q-DISC1**.

Persist fix only, no comparison exists.

**Sites:** `flexicon/code/TextsWords/DiscourseOperations.py:327`
(`CreateChart`) and `:482` (`SetChartName`).

**Scope:** persist the caller's original, unstripped name (C4's binding
shape: validate on a throwaway `.strip()`'d copy via the existing
`_ValidateStringNotEmpty` call at `CreateChart`, and whatever the
equivalent guard is at `SetChartName`; persist the original argument, not
the stripped local). Per C3's explicit per-family carve-out, `Discourse`
has **no** comparison method to touch -- do not add one, do not invent a
dedup check where none exists today.

**Anti-regression pin (C8, Discourse-scoped):** since there is no dedup
check, only the persist half of C8 applies here -- `CreateChart(<name with
trailing space>)` persists byte-identical, re-read from the LCM after the
write. (The "raises already exists" half is inapplicable per `spec.md`
C8's family-specific note.)

Live gate per READ FIRST items 3-7. Evidence:
`evidence/live-t1-discourse-fix.md`.

### [x] T2 -- `TextOperations` (LIVE) -- **DONE, cycle 2** (`6ff3e5e` / `db95230` / `da580cd`). Fully green; both C8 halves live-confirmed. `SetName` took Shape B per C11(a).

Persist fix AND comparison-symmetry fix, together.

**Sites:** `flexicon/code/TextsWords/TextOperations.py:152` (`Create`),
`:608` (`SetName`) for persist; `:458/:461/:464` (`Exists`) for
comparison symmetry.

**Scope:**
- Persist: `Create`/`SetName` persist the caller's original argument, not
  the stripped local (C4).
- Comparison: at `Exists`, strip INLINE at both the needle key (`:461`)
  and the haystack key (`:464`) per C4's exact shape:
  ```
  target = normalize_match_key(name, casefold=...).strip()
  ... normalize_match_key(candidate, casefold=...).strip() == target
  ```
  Do not touch `normalize_match_key` itself or add a shared helper (C4).

**Anti-regression pin (C8, full):** `Texts.Create(<name with trailing
space>)` twice -> the second call RAISES "already exists", AND the first
text's stored `Name` re-reads BYTE-IDENTICAL (including the trailing
space) from the LCM after the write.

**Extend** `test_name_field_identity_probe.py`'s PN2/PN8 to assert the
fixed behaviour (flip from "duplicate succeeds" to "duplicate raises";
flip the haystack-blindness assertions), keeping the pre-fix behaviour
documented in a comment for historical record (same pattern as
`242-paragraph-whitespace/tasks.md` T1). Live gate per READ FIRST items
3-7. Evidence: `evidence/live-t2-text-fix.md`.

### [x] T3 -- `AnthropologyOperations` (LIVE) -- **DONE, cycle 3** (`7bc6d01` / `ab638aa` / `7409ad6`). Fully green; all six predictions MATCHED live; 15/15, `run_mode: live`; offline delta `+0/+0/+0`; both C8 halves confirmed. Q-242D measured at PN15, not fixed.

Persist fix AND comparison-symmetry fix, together.

**Sites:** `flexicon/code/Notebook/AnthropologyOperations.py:265`
(`Create`), `:374` (`CreateSubitem`) for persist; `:558/:562/:565`
(`Find`, reached via `Exists` at `:507-510`) for comparison symmetry.

**Scope:** same shape as T2 -- persist the caller's original at both
writer sites; strip inline at both sides of `Find`'s comparison per C4.
**Observation, not a task (spec.md C5):** `CreateSubitem` has no dedup
check at all, unlike `Create` -- do **not** add one while fixing its
persist behaviour. Both persist sites are Shape B per C11(a) --
throwaway non-reassigning `.strip()`, not plain deletion.

**Anti-regression pin (C8, full, `Create` only -- `CreateSubitem` has no
dedup check per the observation above):**
`Anthropology.Create(<name with trailing space>)` twice -> the second
RAISES "already exists", AND the stored value re-reads BYTE-IDENTICAL.

**Extend** `test_name_field_identity_probe.py`'s PN3 to assert the fixed
behaviour. Live gate per READ FIRST items 3-7. Evidence:
`evidence/live-t3-anthropology-fix.md`.

### [x] T4 -- `CheckOperations` (LIVE) -- **DONE, cycle 4** (`2d8bfc5` / `0ab9c60` / `cbbb55e` / `f5291e9`+`785d5ee`). Q-242A and Q-242B landed TOGETHER at the same three expressions in ONE commit per C6, with TWO evidence files. C7's exact shape at all three sites; `FindCheckType` strips both sides. 20/20 live, `run_mode: live`, collect count 20; all nine predictions MATCHED; offline delta `+0/+0/+5`; both C8 halves green. BREAKING: `FindCheckType` now RAISES instead of coercing and returning `None`.

**Sites:** `flexicon/code/System/CheckOperations.py:196`
(`CreateCheckType`), `:341/:344/:350` (`FindCheckType`), `:432`
(`SetName`).

**Why landed as one task, not two sequential edits (spec.md C6):**
`CheckOperations.py:196` is simultaneously a Q-242A site (needs the
persist fix) and the Q-242B site (needs C7's fix shape). Editing it once
for Q-242A and again later for Q-242B is the "two features editing one
expression in sequence" overhead C6 explicitly rules out. This task
produces **one commit** implementing both, but tracks them with
**separate evidence, severity labels, and CHANGELOG entries** per C6.

**Q-242A part (comparison symmetry + persist), per C4/C5:**
- `FindCheckType` (`:341/:344/:350`): strip inline at both the needle key
  and the haystack key, identical shape to T2/T3.
- `CreateCheckType` (`:196`) and `SetName` (`:432`): persist the caller's
  original argument, not a stripped local.

**Q-242B part (silent-empty-name fix), per C7 exactly:**
- Replace `name = name.strip() if isinstance(name, str) else ""` at
  **all three** line numbers (`:196`, `:341`, `:432`) with a call to the
  already-shipped `BaseOperations._ValidateStringNotEmpty` (`:2491`) --
  **calling** it, not editing it, with **no reassignment of `name`**.
- **KEEP** the existing leading `_ValidateParam(name, "name")` call at
  each site (C7a) -- do not drop it, even though
  `_ValidateStringNotEmpty(None)`'s `if text is None` branch is dead code.
  Record that dead branch as an **observation only**; do not fix it here.
- **Do NOT** harmonise the `AttributeError` sites elsewhere in the
  codebase (`TextOperations.SetName`,
  `AnthropologyOperations.Create`/`CreateSubitem`) -- that is Q-242C, out
  of scope (C7b).
- Whitespace-only input (`"   "`) raises `FP_ParameterError`, on both the
  `str` and non-`str` branches, per lex-domain's Q6 (transcribed in
  `spec.md` C7).

**Live-verification dependency (spec.md section 3):** `CreateCheckType`
is unreachable through the public API without the
`_GetCheckList`/`_GetOrCreateCheckList` `AttributeError` bug getting in
the way first. **Reuse** the cycle-1 probe's
`_seed_valid_check_list()` monkeypatch pattern in this task's live test(s)
-- do not fix `_GetCheckList` itself (out of scope, unrelated bug,
`spec.md` section 3). C9 governs the `_GetCheckList` workaround boundary;
C10(a) requires the `## WHAT WAS NOT EXERCISED` section in BOTH evidence
files.

**Anti-regression pins:**
- **C8 (Q-242A half, full):** `CreateCheckType(<name with trailing
  space>)` twice -> the second RAISES "already exists" (via
  `FindCheckType`'s now-symmetric comparison), AND the stored value
  re-reads BYTE-IDENTICAL.
- **Q-242B pin (new, not in `spec.md` C8 but required by C7):**
  `CreateCheckType(<non-str payload>)` and `CreateCheckType("   ")` both
  now RAISE (`TypeError` for the non-str payload via
  `_ValidateStringNotEmpty`, `FP_ParameterError` for the whitespace-only
  string per lex-domain Q6) instead of silently persisting an empty name.
  Re-read the check-list contents after each attempted call to confirm
  **no** check type was created.

**Extend** `test_name_field_identity_probe.py`'s PN4 (comparison), PN5/PN6
(Q-242B) to assert the fixed behaviour. Live gate per READ FIRST items
3-7, plus item 12 (the `_GetCheckList` workaround). Evidence:
**two files**, per C6's separate-evidence requirement:
`evidence/live-t4a-check-q242a-fix.md` (comparison + persist) and
`evidence/live-t4b-check-q242b-fix.md` (silent-empty-name fix).

---

## Checkpoint 3 -- Docs (dispatch to `/lex-doc`)

### [ ] T5 -- CHANGELOG + docstring updates, per C6's separate-entries requirement -- **THE LAST TASK; the whole next spurt**

Not authored by the Archivist (Archivist/Doc-Agent division of labour) --
dispatched to `/lex-doc`, whose returned patches are staged and committed
by the Archivist.

- **Q-242A entry** (Text/Anthropology/Check comparison symmetry + persist
  fix across `TextOperations`, `AnthropologyOperations`,
  `DiscourseOperations`, `CheckOperations`): classify following #242's own
  precedent (`### Changed` with a `**BREAKING (behavioural): ...**` lead,
  per `242-paragraph-whitespace/spec.md` C9's `CHANGELOG.md:15/63/431`
  convention) unless `/lex-doc` finds a reason to diverge -- if so, that
  is `/lex-doc`'s call to make and record, not pre-decided here.
- **Q-242B entry** (`CheckOperations`'s silent-empty-name fix): **separate
  entry**, per C6, at a severity reflecting that this is TOTAL payload
  loss corrected into a loud exception, not merely restored whitespace --
  `/lex-doc`'s call on exact classification.
- **Docstring `Note:`** on each of the eight touched methods'
  `Args` sections documenting the new whitespace-preserving /
  whitespace-symmetric-comparison / loud-on-non-str-and-whitespace-only
  behaviour, matching #242's own T3 precedent.
- **Do not** author CHANGELOG prose directly as the Archivist -- if
  tempted, dispatch `/lex-doc` instead, per the Archivist/Doc-Agent
  division of labour.
- Must disclose Q-242D as a known remaining gap, and must record
  `CreateChart`'s `FAIL: unverified` persist pin (Q-DISC1) rather than
  claiming 8/8 verified.

Docs-only, no live-verification requirement.

**Added at the cycle-4 close by `/lex-lead` (binding on the T5 spurt):**

- **`/lex-doc` has NO shell tool.** It cannot run `pytest` or `git`. It edits
  files and returns a report path; **the main session performs every shell
  action**, including the AMENDMENT 2 commit bracket and the commit itself.
  Never ask `/lex-doc` to verify or commit -- refusing is the correct answer.
- **The docstring scope is ELEVEN methods**, not eight (the "eight sites" count
  is persist sites; the comparison-symmetry methods are additional):
  `DiscourseOperations.CreateChart`, `.SetChartName`; `TextOperations.Create`,
  `.Exists`, `.SetName`; `AnthropologyOperations.Create`, `.CreateSubitem`,
  `.Find`; `CheckOperations.CreateCheckType`, `.FindCheckType`, `.SetName`.
  **`AnthropologyOperations.Exists` was deliberately NOT touched** -- do not
  document it as changed.
- **`FindCheckType`'s docstring needs a RESOLUTION, not an append.** Its
  `Raises:` section already promises `FP_NullParameterError: If name is None or
  empty` -- a promise the pre-fix code never kept -- while its `Notes:` say
  `- Returns None if not found (doesn't raise exception)`. Post-fix the real
  behaviour is `TypeError` for non-`str` and **`FP_ParameterError`** (not
  `FP_NullParameterError`) for whitespace-only. Both statements must end up
  true and mutually consistent.
- **Blast radius of that break is EXTERNAL callers only** (`/lex-lead`
  verified): the only internal call site in `flexicon/` is
  `CheckOperations.py:199`, inside `CreateCheckType`, which validates `name`
  immediately beforehand.
- **`CHANGELOG.md` anchors** (advisory, re-derive): `[Unreleased]` at `:12`,
  `### Changed` at `:14`, the #242 whitespace precedent entry at `:95`,
  `### Fixed` at `:138`.
- **Also outstanding in this spurt:** transcribe **C12** and **C13** (ruled at
  the cycle-4 close, recorded in `STATUS.md`) verbatim into `spec.md`.

---

## Standing note for every task above

`git status --porcelain` must be checked before every `git add`, **and AGAIN
immediately before every `git commit`, and `git show --stat HEAD` immediately
after it** -- see `CONCURRENCY.md` **AMENDMENT 2**, binding from T4 onward. The
pre-`add` check ALONE is not sufficient: in cycle 3 the other crew's `git add`
landed in the window between T3's pre-`add` check and T3's commit, and five of
their files were swept in. Only paths this feature's own tasks authored may be
staged. Given
`CONCURRENCY.md`'s live situation, expect `flexicon/code/BaseOperations.py`,
`flexicon/code/Grammar/NaturalClassOperations.py`, and
`flexicon/code/Grammar/PhonemeOperations.py` to show as modified at any
given moment -- these are never staged by this feature's commits.

---

## Appendix B -- the parallel task list from `origin/main` (`dd5422f`, PR #282), verbatim

Reproduced exactly as written, heading levels demoted one step to nest under
this appendix. Its checkpoints are numbered independently of the ones above
and are NOT this feature's work plan; the plan above is. Kept for the audit
trail and because `specs/tier1-silent-data-loss/QUEUE.md` points at it.


Derived from `spec.md` NF1-NF11 (all FROZEN, 2026-09-08).
Origin: Q-242A in `specs/tier1-silent-data-loss/QUEUE.md`.

**Checkpoint 1 (the ruling) is DONE. Checkpoints 2-4 are BLOCKED on
`specs/242-paragraph-whitespace/spec.md` C18** -- the environment cannot
execute the live tests OR the offline suite, so nothing below can be
verified, and per CLAUDE.md an unverified write-path change is
`FAIL: unverified`, never a clean result. Do not start Checkpoint 2 until
C18 is resolved.

---

### Checkpoint 1 -- Rule the dedup-identity question (DONE, 2026-09-08)

- [x] T1 -- Census every `normalize_match_key` comparison site; classify
      asymmetric / symmetric. Result: 40 pairs, 10 asymmetric, 0 casefold
      divergence (`spec.md` NF1).
- [x] T2 -- Establish whether the identity defect is caused by fixing the
      strip, or pre-existing. Result: **pre-existing, and reachable
      through this library's own public API** in both halves --
      duplicate-explosion (4 sites) and unreachable-object (5 sites).
      This refuted the premise of the question as filed (`spec.md` NF2).
- [x] T3 -- Rule the question. `"Genesis "` IS `"Genesis"` for identity;
      case unchanged per-site (`spec.md` NF3). Store verbatim, compare
      normalized (`spec.md` NF4).
- [x] T4 -- Rule the fix locus and scope (`spec.md` NF5, NF6), including
      the four binding conditions after the impact assessment found a
      counter-example.
- [x] T5 -- Record hazards H1-H8, provenance, the C8 citation defect, and
      the adjudicated inter-pass disagreements (`spec.md` NF7, NF9, NF10,
      NF11).

**Q-242A is UNBLOCKED by this checkpoint.** Its stated blocker was this
ruling.

---

### Checkpoint 2 -- The matcher (BLOCKED on C18)

Order matters: the probe must measure the defect BEFORE the fix lands, per
the C28 forward rule.

- [ ] T1 -- Write `tests/operations/test_name_field_identity_probe.py`.
      **It does not exist** -- `evidence/live-probe-cycle1.md` names it but
      it was never written or committed (`spec.md` NF8). Predictions
      PN1-PN8 are already committed (`bdbce02`), so do NOT edit them; the
      harness must be built to measure them as written.
- [ ] T2 -- Run the probe against the UNFIXED code. Confirm or refute
      PN1-PN8 and the NF2 halves empirically. **A refuted prediction is a
      successful cycle** -- the evidence file's refutation clause binds.
      Fill in its RESULTS section in a second commit.
- [ ] T3 -- Add unit cases to `tests/test_normalize_match_key.py` for
      `" x "`, `"   "` and `" *** "`. **None exist today in either
      direction** (`spec.md` NF7 H7), so the suite currently cannot catch
      this change failing. These land WITH the change, not after.
- [ ] T4 -- `normalize_match_key`: `text = normalize_text(text).strip(" \t\r\n")`,
      placed AFTER the null-marker check (NF5 condition 1, NF7 H4) and
      using the restricted character set (NF5 condition 2, NF7 H5).
- [ ] T5 -- Fence `ScrDraftOperations.Find` off the shared helper (NF5
      condition 3, NF7 H2). Containment is not equality. Comment it so a
      future reader does not "tidy" it back.
- [ ] T6 -- Drop the now-redundant needle-only `.strip()` at all **10**
      bucket-A sites. **Use both greps** -- 7 are inline
      (`normalize_match_key(name.strip(), ...)`) and 3 are reassignment-style
      (`name = name.strip()` first); an inline-only pattern match silently
      misses three (`spec.md` NF11 item 3).
- [ ] T7 -- Add needle guards at the unguarded sites so a whitespace-only
      needle cannot degenerate into the promiscuous `""` key (NF5
      condition 4, NF7 H6): `PhonemeOperations.py:462` and `:929`,
      `PhonologicalRuleOperations.py:332`, `POSOperations.py:343`,
      `DataNotebookOperations.py:479`.
- [ ] T8 -- Re-run the probe. The NF2 halves must now be fixed: uniqueness
      guards fire, created objects are findable.

### Checkpoint 3 -- The 8 filed writer sites (BLOCKED on C18)

- [ ] T1 -- Apply #242 C8's binding shape at all 8 Q-242A sites:
      `x = v if isinstance(v, str) else str(v)`; guard on `x.strip()`;
      persist the ORIGINAL `v`. Sites: `CheckOperations.py:196`/`:432`,
      `TextOperations.py:152`/`:608`, `DiscourseOperations.py:327`/`:482`,
      `AnthropologyOperations.py:265`/`:374`.
- [ ] T2 -- Do NOT touch the coercion defect at `CheckOperations.py:196`/
      `:341`/`:432` -- that is **Q-242B**, ruled out of scope by NF6 and
      deliberately triaged at higher severity. This feature edits those
      FILES without fixing that DEFECT; keep the two apart in the diff and
      the commit message.
- [ ] T3 -- Live-verify: pre-state and post-state read back from the LCM by
      re-querying after the write. `target_sandbox` / `target_sandbox_path`
      ONLY. Per #242 C16, paste `run_mode` AND `run_timestamp` verbatim
      into the evidence file -- `tests/live_status.json` is gitignored and
      does not survive the run.

### Checkpoint 4 -- Docs (BLOCKED on C18)

- [ ] T1 -- CHANGELOG. Two distinct entries, not one:
      a **`### Fixed`** entry for the matcher asymmetry and the two NF2
      halves (**pre-existing**, per NF2/NF9 -- classified like #242's C12),
      and a **`### Changed`** entry with a `**BREAKING (behavioural): ...**`
      lead for the 8 writer sites (per #242 C9's convention, which now has
      four instances at `CHANGELOG.md:15`, `:63`, `:95`, `:500`).
- [ ] T2 -- Document the equality-vs-containment split in
      `normalize_match_key`'s docstring, so the fence is discoverable from
      the helper rather than only from this spec.
- [ ] T3 -- Docstring notes at the 8 writer sites, matching #242 C14's
      binding text.

### Open, NOT this feature's to close

- [ ] **C18** (`specs/242-paragraph-whitespace/spec.md`) -- restore a
      3.8-3.13 interpreter with `pythonnet >=3.0.3,<3.1`, or rule on
      relaxing the pin. `needs_human`. **Everything above is blocked on
      this.**
- [ ] **NF7 H1** -- `strip_display_marker`'s ordering defect
      (`morph_type_utils.py:108-109`): a `" -suffix"` needle keeps its `-`
      marker. Pre-existing, NOT fixed by this feature (the marker strip
      runs first, at the call site). Needs its own ruling.
- [ ] **NF10** -- #242 C8 cites a "CLAUDE.md-named caller-managed-flag
      anti-pattern" that does not appear in `CLAUDE.md`. For #242's owner:
      locate the rule, write it down, or restate C8's ground as the
      82-vs-12 argument alone.
- [ ] **NF1's case-sensitivity inconsistency** -- 21 sites
      case-insensitive, 19 case-sensitive. Newly documented, ruled out of
      scope by NF3, and deliberately NOT filed as a defect: each site is
      internally consistent, so this is a consistency question. Do not cite
      NF3 as precedent for harmonising it.
- [ ] **Q-242B**, **Q-242C** -- remain in
      `specs/tier1-silent-data-loss/QUEUE.md`, untouched by NF6.

### Hard constraints

- `target_sandbox` / `target_sandbox_path` ONLY. Never the real Target,
  never `scripts/restore_*.py`.
- Never bare `pytest` -- it collects and EXECUTES ~322
  `requires_live_project` tests in-place against real projects. Offline is
  `python -m pytest tests -m "not requires_live_project" -q`.
- Derive every live count with `--collect-only`. "No tests collected" is a
  ZERO, never a pass.
- The C28 forward rule: predictions are committed BEFORE the measuring run.
  PN1-PN8 are already committed at `bdbce02` -- do not edit them to match
  what you measure.
- NF1-NF11 are FROZEN. Do not implement NF5 with any variation -- no bare
  `.strip()`, no placement before the null-marker check, no unfenced
  `ScrDraftOperations.Find` -- without citing and overturning the item by
  number.
- This spec does not edit `specs/tier1-silent-data-loss/QUEUE.md` or its
  `.crew-handoff.json`; campaign-level files belong to the main session.
