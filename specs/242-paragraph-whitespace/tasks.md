# TASKS -- 242-paragraph-whitespace

Derived from `spec.md` sections 2-4 (C1-C11, R1-R3 [DISCHARGED], Q1-Q3).
Issue: #242. Campaign: `tier1-silent-data-loss`, queue item 2 of 4.

**R1/R2/R3 and the coercion question are now RULED (`spec.md` C8-C11,
2026-09-07). NO BEHAVIOUR CHANGE UNDER `flexicon/code/` HAS BEEN MADE YET**
-- `git diff --stat -- flexicon/` is empty and independently re-confirmed
(`evidence/live-probe-cycle1.md`) as of this pass. Checkpoint 3's code
tasks (T1/T2) are now UNBLOCKED and may proceed with C8's exact fix shape;
this mirrors `243-closeproject-save-guard/tasks.md`'s discipline of gating
implementation tasks behind a named ruling rather than letting an
implementer guess.

**Extend, do not duplicate:**
`tests/operations/test_issue242_whitespace_probe.py` already exists from
Checkpoint 1 (5 live tests passing against the UNFIXED code -- `test_p1`
through `test_p5`, per `evidence/live-probe-cycle1.md`). Every task below
that needs a regression test EXTENDS this file in place; it does not create
a parallel probe file.

**Standing gates for every future task (carried from the campaign
QUEUE.md "Hard rules" and `243-closeproject-save-guard`'s own hard-won
rules -- do not relitigate any of these):**

1. **Fixtures:** `target_sandbox` / `target_sandbox_path` ONLY. Never the
   real Target, never any `scripts/restore_*.py` run. If a task genuinely
   needs the real Target, stop with `status: needs_human` rather than
   running it.
2. **Live verification is REQUIRED** for anything touching an Operations
   class, a factory call, a property setter, or the write path (CLAUDE.md).
   Mock-only is `FAIL: unverified`, never a clean result.
3. **Derive live counts with `--collect-only`, never trust a filename.**
   `python -m pytest <file> --collect-only -q -m requires_live_project` and
   paste the count into the evidence file. **"no tests collected" is a
   ZERO, never a pass** -- `243-closeproject-save-guard`'s T2 spurt found a
   "live suite" named by filename that collected 0 tests; do not repeat
   that mistake here.
4. **Never run bare `pytest`** or `pytest --ignore=tests/contract` --
   neither applies an `-m` filter, so both execute the ~322
   `requires_live_project` tests in place against real projects. Always:
   ```
   $env:FLEXLIBS_REQUIRE_LIVE = "1"
   python -m pytest tests/operations/test_issue242_whitespace_probe.py -m requires_live_project -q -s
   ```
5. **Offline baseline is 1292 passed as of `b0e3d14`** (the commit this
   feature's cycle-1 probe landed against, per
   `reviews/cycle1-programmer.md`). Every future task re-confirms this
   count is unchanged (plus exactly the new live-marked tests it adds,
   which land in `deselected`, not `passed`, when run offline).
6. **The C28 forward rule (named in `243-closeproject-save-guard/spec.md`):
   a stated prediction is committed BEFORE the measuring run, not edited
   after.** Any new probe extension follows the same discipline used in
   `evidence/live-probe-cycle1.md`: write PREDICTIONS, commit, then run the
   live command, then fill in RESULTS in a second commit.
7. **Evidence or it did not happen.** Each task writes
   `specs/242-paragraph-whitespace/evidence/live-<task>.md` with the exact
   command, the `run_mode` value from `tests/live_status.json`, and
   pre/post values **re-read from the LCM** after the write (not asserted
   on the value passed in).
8. **No GitHub issues filed from inside this feature.** Anything needing
   the user's approval (R3's 8 sites, Q3's `CheckOperations.py` variant)
   goes to `specs/tier1-silent-data-loss/QUEUE.md` "Awaiting user
   approval," which already carries four asks from campaign item 1 plus one
   ungated cleanup -- do not disturb, reword or reorder that section.

---

## Checkpoint 1 -- Spec + live probe (THIS SPURT)

**DONE, 2026-09-07.** Delivered:

- [x] `spec.md` -- contract items C1-C7 (frozen findings of fact), R1-R3
      (recommendations awaiting a `/lex-lead` ruling), Q1-Q3 (open
      questions), and a contradiction-check section.
- [x] `tasks.md` (this file).
- [x] `STATUS.md`.
- [x] `.crew-handoff.json`.
- [x] `tests/operations/test_issue242_whitespace_probe.py` -- 5/5 live
      tests passing against the UNFIXED code, `run_mode: live`,
      `target_sandbox`/`target_sandbox_path` fixtures only. Already existed
      going into this pass (delivered by `/lex-programmer` in the same
      cycle as this Archivist pass); not modified by this pass.
- [x] Three cycle-1 reviews on file: `reviews/cycle1-programmer.md`,
      `reviews/cycle1-explore.md`, `reviews/cycle1-domain.md`.
- [x] `evidence/live-probe-cycle1.md` -- predictions committed before the
      measuring run (`b28c8640`), results added after (`558654e`),
      `run_mode: live`, 5/5 passing.

**Checkpoint:** spec + probe on file, matching the campaign QUEUE.md entry
condition for this item ("Checkpoint 1 = spec + a live probe that measures
what is actually stripped ... and whether any caller depends on the
stripping"). `git diff --stat -- flexicon/` empty, re-confirmed. **No task
below this line may be started until `/lex-lead` rules on R1/R2/R3.**

---

## Checkpoint 2 -- CP-RULING: `/lex-lead` decides fix shape, CHANGELOG classification, and the 8-sites scope (UNSTARTED)

Not a code task. `/lex-lead` reads `spec.md` sections 2-4 and rules on:

- [x] **R1 ruling -- DONE, 2026-09-07 (`spec.md` C8).** Direct fix (a)
      ACCEPTED; `preserve_whitespace=` kwarg (b) REJECTED as the
      CLAUDE.md caller-managed-flag anti-pattern. Binding shape:
      `x = v if isinstance(v, str) else str(v)` then
      `if not x.strip(): raise`, with the ORIGINAL `v` persisted. The
      non-str branch is not stripped at any of the four sites (deletes
      `SegmentOperations.py:595`'s `str(text).strip()`).
- [x] **R2 ruling -- DONE, 2026-09-07 (`spec.md` C9).** CHANGELOG entry is
      `### Changed` with a `**BREAKING (behavioural): ...**` lead. This
      OVERTURNS cycle-1 domain's Q4 no-BREAKING-prefix recommendation --
      `CHANGELOG.md:431` (`OpenProject(..., undoable=...)`) applies the
      same label to a pure silent-default flip with no signature break, so
      "no signature/exception-type change means no BREAKING prefix" does
      not hold against the repo's own convention. `CHANGELOG.md:15` and
      `:63` are the other two `BREAKING` hits. The actual CHANGELOG prose
      is still `/lex-doc`'s to author, per the Archivist/Doc-Agent
      division of labour -- this ruling fixes only the classification.
- [x] **R3 ruling -- DONE, 2026-09-07 (`spec.md` C10).** The 8 newly-found
      sibling sites are routed to
      `specs/tier1-silent-data-loss/QUEUE.md` "Awaiting user approval"
      (Q-242A) -- NOT folded into this feature, NOT spun into a follow-on
      feature. Rationale: the 4 filed sites write CONTENT fields where
      domain's Q2 structural-whitespace argument holds; the 8 new sites
      write NAME fields where it does not, and three of the four new
      families feed the stripped value into a uniqueness check
      (`CheckOperations.py:196->200`, `TextOperations.py:152->155`,
      `AnthropologyOperations.py:265->269`) that the 4 filed sites have no
      equivalent of. Q3 (`CheckOperations.py`'s third, higher-severity
      variant) is filed SEPARATELY as Q-242B, deliberately not bundled
      with Q-242A so it is not triaged at whitespace severity. A fourth,
      previously-unasked question -- str()-coercion harmonisation across
      the codebase -- was also ruled: OUT of scope for this feature
      (`spec.md` C11), queued as Q-242C.

**Checkpoint:** `spec.md` C8-C11 record R1, R2, R3 and the coercion
ruling. `tasks.md` Checkpoint 3 below is rewritten to match C8's exact
fix shape; Checkpoint 5 (the 8 sibling sites) is DELETED rather than left
as dead scope, since C10 routed those sites out of this feature entirely.
Update `STATUS.md` / `.crew-handoff.json`, commit, stop.

---

## Checkpoint 3 -- Implement the direct fix at the four named sites (UNSTARTED, ruling landed per `spec.md` C8)

Scope now matches C8's ruling exactly, not the provisional R1 recommendation
it discharges. Binding shape at all four sites (C1's table):

```python
x = v if isinstance(v, str) else str(v)
if not x.strip():
    raise FP_ParameterError(...)
...
MakeString(v, ...)   # the ORIGINAL, unstripped value is what gets persisted
```

The non-str branch is NOT stripped at any of the four sites -- this
deletes `SegmentOperations.py:595`'s `str(text).strip()` (C6 item 2),
bringing `AppendSentence` into line with the three `ParagraphOperations.py`
sites' existing non-str behaviour. This is the full extent of the
coercion-asymmetry work authorised here -- C11 rules the broader
str()-coercion-vs-reject question OUT of scope; do not widen T1/T2 into
that question.

- [x] **T1** (LIVE) `flexicon/code/TextsWords/ParagraphOperations.py`,
      three sites (`Create`, `SetText`, `InsertAt`, per `spec.md` C1's
      table): validate emptiness on a throwaway `.strip()`'d copy, persist
      the caller's original `content` per C8's binding shape above (the
      non-str branch was already unstripped here -- C6 item 1 -- so this is
      unchanged for these three sites; C8 confirms rather than modifies
      their non-str behaviour). EXTEND
      `test_p1`/`test_p3`/`test_p4`/`test_p5` in
      `tests/operations/test_issue242_whitespace_probe.py` to flip their
      assertions from "stripped" to "preserved" against the patched code,
      keeping the unfixed-code behaviour documented in a comment for
      historical record (same pattern as
      `243-closeproject-save-guard/tasks.md` T4). **Deliverable, explicit:**
      measure and record the `AppendSentence` terminator interaction:
      appending `"foo"` then `"bar"` via two `AppendSentence` calls, with
      the fix applied, is **PREDICTED to produce a baseline of
      `"foo . bar"`** (terminator `". "` per C5, line 614, plus C8's
      now-preserved caller whitespace). State this predicted string in the
      probe extension BEFORE running it (C28 forward rule), then record
      the measured string alongside it. `/lex-lead` rules on this specific
      measurement in cycle 3 -- do not treat a predicted/measured mismatch
      as a task failure; report it as a finding. Live gate per the
      boilerplate above. Evidence: `evidence/live-t1-paragraph-fix.md`.
      **DONE, cycle 2 (`evidence/live-t1-t2-fix.md`).** P6/P7 CONFIRMED, no
      exceptions. P8 CONFIRMED the predicted `'foo . bar'` anomaly is real
      (reported, not fixed this cycle, per the ruling) -- see T5 below,
      where cycle 3 fixes it.
- [x] **T2** (LIVE) `flexicon/code/TextsWords/SegmentOperations.py:595`
      (`AppendSentence`): same shape as T1, applying C8's binding shape --
      DELETE the `.strip()` from the non-str branch
      (`str(text).strip()` -> `str(text)`), per C8's explicit instruction
      that this site's non-str asymmetry (C6 item 2) is resolved, not
      preserved. EXTEND `test_p2` in the same probe file. **Deliverable,
      explicit:** T2 shares T1's AppendSentence terminator-measurement
      deliverable above -- this is the site under test, so T1 and T2
      report the SAME measurement, not two independent ones; do not
      duplicate the live run. Live gate per the boilerplate. Evidence:
      `evidence/live-t2-segment-fix.md`. **DONE, cycle 2
      (`evidence/live-t1-t2-fix.md`, same commits as T1 --
      `be42aaf`/`066bab0`).**
- [x] **T3** (docs-only, per C9's ruling) Add the one-line `Note:` to each
      of the four docstrings' `Args` section (C1's four sites), documenting
      that whitespace is now preserved. Dispatch to `/lex-doc` per the
      Archivist/Doc-Agent division of labour; the Archivist does not author
      docstring prose. Docs-only, no live-verification requirement. **DONE,
      cycle 2 (`reviews/cycle2-doc.md`).**
- [x] **T4** (docs-only, per C9's ruling) `CHANGELOG.md` entry under
      `### Changed` with a `**BREAKING (behavioural): ...**` lead (C9),
      cross-referencing #242. Dispatch to `/lex-doc`; stage and commit its
      returned patch. Docs-only, no live-verification requirement. **DONE,
      cycle 2 (`reviews/cycle2-doc.md`)** -- landed with a "Known
      interaction, not yet resolved" sub-paragraph documenting the P8
      anomaly as unfixed; **that sub-paragraph is DELETED, not amended, by
      T6 below**, per C12's classification (PRE-EXISTING and NEWLY
      VISIBLE, not an open caveat).
- [x] **T5** (Checkpoint 3; LIVE; distinct from Checkpoint 4's T5 below)
      the AppendSentence join-boundary fix, per `/lex-lead`'s cycle-3
      ruling C12: anchor the terminator at the last non-whitespace
      character and reuse the caller's existing trailing whitespace as the
      separator, deleting nothing at the join boundary (the four-case
      algorithm is recorded in full at `spec.md` C12). **DONE, cycle 3**
      -- `flexicon/code/TextsWords/SegmentOperations.py`'s
      `AppendSentence` `current_length > 0` branch only;
      `ParagraphOperations.py` not touched by this task.
      `reviews/cycle3-programmer.md`; evidence
      `evidence/live-t5-joinfix.md`: 9 prediction rows, all `MATCH`, 0
      MISS, `run_mode: live`, `target_sandbox`/`target_sandbox_path`
      only. C12.4 inertness proof (the four `trail == 0` rows,
      byte-for-byte identical to cycle 2's post-T1/T2 behaviour) held.
      Commits: `a580f7b` (predictions), `608200c2` (results + code +
      tests, C28 forward rule).
- [x] **T6** (docs-only, per C12's ruling) `CHANGELOG.md`/docstring
      follow-up for the C12 fix: a standalone `### Fixed` entry (not
      folded into T4's `### Changed` entry), and deletion of T4's "Known
      interaction, not yet resolved" sub-paragraph, per C12's
      pre-existing/newly-visible classification. Dispatched to `/lex-doc`,
      running in parallel with this Archivist pass; not authored here.
- [x] **T7** (this record) -- record `/lex-lead`'s cycle-3 rulings (C12,
      C13) as frozen contract items in `spec.md`, and close out this
      checkpoint's bookkeeping. Archivist pass, cycle 3.

**Checkpoint 3 CLOSED, cycle 3, 2026-09-07.** T1-T7 all DONE. T1/T2
live-verified with the flipped probe assertions green and the
AppendSentence terminator measurement recorded (predicted-then-measured,
C28 forward rule); the measured anomaly (P8) was ruled on and fixed by T5
per C12, not left open. T3/T4 landed via `/lex-doc` in cycle 2; T6 (the
C12-driven doc follow-up) is in flight via `/lex-doc` in parallel with
this pass. Offline suite at **1292 passed, 483 deselected**
(cycle-2 baseline was 482; +1 explained by `test_p8b`, not absorbed).
Update `STATUS.md` / `.crew-handoff.json`, commit, stop.

---

## Checkpoint 4 -- CLOSED -- DECLINED (C13), 2026-09-07

**Was:** "Corpus-shaped reproduction of the owner's 41/86 figure
(UNSTARTED, OPTIONAL, per Q2)." Only scheduled if a ruling decided Q2
needed answering before this feature could honestly claim to fix the
owner's filed report, not just the mechanism.

**Ruling, `/lex-lead`, cycle 3 (`spec.md` C13): DECLINED, not deferred.**
This is a deliberate choice not to make this measurement, recorded here
so the record shows the choice was made -- not left dangling. Left
in place (not deleted) for that reason, unlike Checkpoint 5's dead scope
below, which was routed elsewhere entirely.

**Rationale (see `spec.md` C13 for the full record):** the owner's
44/104-paragraph and 41/86-segment field figures were diagnostic; the
underlying mechanism is already proven directly at unit level by P6 (8
payloads, byte-for-byte, all four writers, the layer-B bypass, and
in-memory/on-disk agreement -- `evidence/live-t1-t2-fix.md`). Reproducing
the owner's exact corpus number would re-prove a known mechanism at
higher cost (building/sourcing a populated corpus) and lower resolution
(an aggregate count vs. P6's payload-by-payload, writer-by-writer
isolation). **Explicit negative claim: THIS FEATURE DOES NOT CLAIM TO
HAVE REPRODUCED THE OWNER'S 41/86 FIGURE.**

- [x] ~~**T5** (LIVE, optional) Build or reuse a populated multi-paragraph,
      multi-segment corpus in a sandbox, reproduce it through the fixed
      writers, and re-measure the identical/differing counts the owner's
      issue reports (60/44 paragraphs, 45/41 segments -- `spec.md` C2).
      Evidence: `evidence/live-t5-corpus-reproduction.md`.~~ **DECLINED,
      not run.** (Note: this Checkpoint-4 T5 is a distinct item from
      Checkpoint 3's T5 above, the AppendSentence join-boundary fix --
      the numbering collision is between two different checkpoints, not a
      duplicate task.)

**Q2 is DISCHARGED** by this ruling -- see `spec.md` section 4.

---

**Checkpoint 5 (the 8 sibling sites) is DELETED, 2026-09-07.** `spec.md`
C10 routed those 8 sites to `specs/tier1-silent-data-loss/QUEUE.md`
"Awaiting user approval" (Q-242A) rather than folding them into this
feature, so there is no scope left for a checkpoint here -- see C10 for
the full rationale. Do not re-add this checkpoint without a new ruling
overturning C10 by number.
