# TASKS -- name-field-whitespace-identity

Derived from `spec.md` sections 0-5 (C1-C8, FROZEN). Issues: Q-242A, Q-242B
(`specs/tier1-silent-data-loss/QUEUE.md`, sub-item 2a). Campaign:
`tier1-silent-data-loss`.

**AUTHORISED BY THE OWNER, 2026-09-07.** No behaviour change under
`flexicon/code/` has been made by this feature yet. `spec.md` C1-C8 are
frozen; every code task below implements C4 (comparison-symmetry fix) and
C7 (Q-242B fix shape) exactly as ruled, with C8's anti-regression pin as
the acceptance gate.

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

## Checkpoint 2 -- Implement the direct fix, one task per family (UNSTARTED)

Sequenced so the comparison-symmetry fix (C4) and the persist fix land
TOGETHER per family -- never a persist fix without its comparison fix,
since that is the C2 duplicate-explosion hazard. Order: Discourse first
(no comparison, smallest, lowest risk), then Text, then Anthropology, then
Check (which also carries the distinct Q-242B task).

### T1 -- `DiscourseOperations` (LIVE): persist fix only, no comparison exists

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

### T2 -- `TextOperations` (LIVE): persist fix AND comparison-symmetry fix, together

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

### T3 -- `AnthropologyOperations` (LIVE): persist fix AND comparison-symmetry fix, together

**Sites:** `flexicon/code/Notebook/AnthropologyOperations.py:265`
(`Create`), `:374` (`CreateSubitem`) for persist; `:558/:562/:565`
(`Find`, reached via `Exists` at `:507-510`) for comparison symmetry.

**Scope:** same shape as T2 -- persist the caller's original at both
writer sites; strip inline at both sides of `Find`'s comparison per C4.
**Observation, not a task (spec.md C5):** `CreateSubitem` has no dedup
check at all, unlike `Create` -- do **not** add one while fixing its
persist behaviour.

**Anti-regression pin (C8, full, `Create` only -- `CreateSubitem` has no
dedup check per the observation above):**
`Anthropology.Create(<name with trailing space>)` twice -> the second
RAISES "already exists", AND the stored value re-reads BYTE-IDENTICAL.

**Extend** `test_name_field_identity_probe.py`'s PN3 to assert the fixed
behaviour. Live gate per READ FIRST items 3-7. Evidence:
`evidence/live-t3-anthropology-fix.md`.

### T4 -- `CheckOperations` (LIVE): Q-242A comparison-symmetry + persist fix, AND the distinct Q-242B fix, landed TOGETHER at the same expressions

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
`spec.md` section 3).

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

### T5 -- CHANGELOG + docstring updates, per C6's separate-entries requirement

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

Docs-only, no live-verification requirement.

---

## Standing note for every task above

`git status --porcelain` must be checked before every `git add`, and only
paths this feature's own tasks authored may be staged. Given
`CONCURRENCY.md`'s live situation, expect `flexicon/code/BaseOperations.py`,
`flexicon/code/Grammar/NaturalClassOperations.py`, and
`flexicon/code/Grammar/PhonemeOperations.py` to show as modified at any
given moment -- these are never staged by this feature's commits.
