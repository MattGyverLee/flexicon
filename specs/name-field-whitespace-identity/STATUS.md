# STATUS -- name-field-whitespace-identity

**Campaign:** `tier1-silent-data-loss`, spun-out sub-item **2a** (between
queue item 2, `242-paragraph-whitespace`, and queue item 3,
`feature-structure-sync-gap`) -- **`active`**.
**Last updated:** 2026-09-07, Checkpoint 1 (spec + live probe) DONE, cycle 1.
**Status:** Spec + probe delivered. Contract items C1-C8 FROZEN. No
behaviour change under `flexicon/code/` has landed from this feature yet.

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
