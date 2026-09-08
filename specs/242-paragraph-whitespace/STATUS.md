# STATUS -- 242-paragraph-whitespace (flexicon#242)

**Campaign:** `tier1-silent-data-loss`, queue item 2 of 4 -- **`done`**
(the campaign record set item 2 `status: done` and `active_index: null` at
cycle 4; see `specs/tier1-silent-data-loss/QUEUE.md`). This file previously
read `active`, which was stale.
**Last updated:** 2026-09-08, cycle 5 (five-verifier independent gate).
**Status:** Checkpoints 1-3 DONE. Checkpoint 4 DECLINED (not deferred).
Checkpoint 6 (the cycle-5 gate) CLOSED on substance with two items OPEN.
`/lex-lead` has ruled on R1, R2, R3, the coercion question, the
AppendSentence join-boundary defect, and the Checkpoint-4/Q2 corpus
question -- see `spec.md` C8-C13. Behaviour change under `flexicon/code/`
HAS landed: the four named sites' direct fix (C8, cycle 2, commits
`be42aaf`/`066bab0`), the AppendSentence join-boundary fix (C12, cycle 3,
commits `a580f7b`/`608200c`), and the docstring/CHANGELOG work (C14, cycle
4, commit `ed428f7`).

**THE VERIFICATION GATE HAS RUN -- TWICE, BOTH GREEN.** This file
previously said the feature was "pending only the cycle-3 independent
verification gate." That was stale on two counts: the cycle-3 gate had
already returned `GATE: GREEN` (`reviews/cycle3-verification.md`), and the
campaign record had already recorded `feature_complete APPROVED by
lex-lead` at cycle 4. A second, independent five-verifier gate ran at cycle
5 and also returned green on substance
(`reviews/cycle5-verification-swarm.md`).

**Two items remain OPEN, neither of them evidence against the fix and
neither introduced by it** -- `spec.md` C18 (the test environment is
broken: Python 3.14.5 only, outside `requires-python`, so the offline
baseline is currently unreproducible; `needs_human`) and `spec.md` C16 (the
`run_mode: live` claims rest on a gitignored artifact that was never
committed; BLOCKED BY C18).

> **THE CAMPAIGN IS NOT COMPLETE.** This is queue item 2 of 4. Item 1
> (`243-closeproject-save-guard`, #243) is `done`. Items 3
> (`feature-structure-sync-gap`, #251/#252/#253/#256) and 4
> (`250-writingsystem-activation`, #250) are `queued`, untouched.

---

## What landed at Checkpoint 1 (this spurt)

- **`spec.md`** -- problem statement (from the GitHub issue #242 body,
  fetched verbatim via `gh issue view 242`); seven frozen contract items
  (C1-C7): the four sites' dual line-numbering (issue-time vs HEAD), the
  owner's field evidence (60/44 paragraphs, 45/41 segments) and the #239
  `guid=` irony, what the live probe measured and did not, the null-marker
  ruling (discharged with negative evidence), the `AppendSentence`
  internal-inconsistency finding, the str()-coercion three-way asymmetry,
  and the sibling-sweep result (12 bug-shape sites vs 82/390 correct-shape
  sites); three recommendations explicitly marked NOT frozen and awaiting
  a `/lex-lead` ruling (R1 fix shape, R2 breaking-change classification, R3
  the 8 new sites' scope); three open questions (Q1-Q3); and a
  contradiction-check section recording that no two cycle-1 reports were
  found to conflict.
- **`tasks.md`** -- Checkpoint 1 (this spurt, DONE), Checkpoint 2
  (CP-RULING, unstarted, not a code task), Checkpoint 3 (the direct-fix
  implementation, unstarted, blocked on Checkpoint 2), Checkpoint 4 (the
  optional corpus-shaped reproduction, unstarted), Checkpoint 5 (the 8
  sibling sites, scope deliberately left unwritten pending Checkpoint 2's
  R3 ruling).
- **`STATUS.md`** (this file).
- **`.crew-handoff.json`**.
- **Live probe** -- `tests/operations/test_issue242_whitespace_probe.py`,
  5/5 passing (`test_p1` through `test_p5`), `run_mode: live`,
  `target_sandbox`/`target_sandbox_path` fixtures only, real Target
  untouched, no `scripts/restore_*.py` run. Predictions committed
  (`b28c8640`) before the measuring run, results added after (`558654e`) --
  the C28 forward rule. Offline baseline **1292 passed** as of `b0e3d14`
  (unchanged from before this feature's probe landed; deselected rose
  475 -> 480, exactly +5 for the new live tests).
- **Reviews on file** -- `reviews/cycle1-programmer.md`,
  `reviews/cycle1-explore.md`, `reviews/cycle1-domain.md`.
- **Evidence on file** -- `evidence/live-probe-cycle1.md`.

## Headline findings (see `spec.md` for full detail and citations)

1. **The fix is real, not cosmetic.** A raw `MakeString` write (bypassing
   this library) preserves every payload byte-for-byte, including the
   padded null marker. The loss measured at the four shipped writers is
   caused entirely by this library's own `.strip()` calls (`spec.md` C3(i)).
2. **The null-marker path is not load-bearing here.** Zero matches for
   `normalize_text`/`FLEX_NULL_MARKER`/`string_utils` in either
   `ParagraphOperations.py` or `SegmentOperations.py`; the read paths never
   normalize; `Contents`/`BaselineText` are plain `ITsString`, not the
   `IMultiString` type the null-marker mechanism applies to (`spec.md` C4).
3. **Trailing whitespace is structural in FLEx paragraph data, not
   corruption.** `AppendSentence` itself inserts `". "` (period plus a
   trailing space) as its own sentence terminator, then strips equivalent
   trailing whitespace from the next call's input -- the file is internally
   inconsistent, and the fix is faithful reproduction of valid structure,
   not data cleanup (`spec.md` C5).
4. **A third, worse variant of the same bug shape exists at
   `CheckOperations.py:196/341/432`** -- a non-`str` input silently becomes
   an empty string that passes validation and gets persisted with no
   exception (`spec.md` C6, item 3).
5. **The four named sites are outliers, not the house style.** 82 sibling
   writer sites (390 counting all writers that persist the caller's
   original unmodified) already use the "validate on a throwaway, persist
   the original" shape; only 12 sites (the 4 known plus 8 newly found) share
   the bug shape (`spec.md` C7).

## Rulings landed at Checkpoint 2 (this spurt)

- **R1 -- fix shape -- RULED, `spec.md` C8.** Direct fix ACCEPTED;
  `preserve_whitespace=` kwarg REJECTED as the CLAUDE.md caller-managed-flag
  anti-pattern. Binding shape: `x = v if isinstance(v, str) else str(v)`
  then `if not x.strip(): raise`, with the ORIGINAL `v` persisted. The
  non-str branch is not stripped at any of the four sites -- this deletes
  `SegmentOperations.py:595`'s `str(text).strip()`.
- **R2 -- breaking-change / CHANGELOG classification -- RULED (and
  OVERTURNED), `spec.md` C9.** CHANGELOG entry is `### Changed` with a
  `**BREAKING (behavioural): ...**` lead -- this OVERTURNS cycle-1
  domain's no-BREAKING-prefix recommendation, on file evidence:
  `CHANGELOG.md:431` applies the same label to `OpenProject(...,
  undoable=...)`, a pure silent-default flip with no signature break.
  `CHANGELOG.md:15` and `:63` are the convention's other two instances.
- **R3 -- scope of the 8 newly-found sibling sites -- RULED, `spec.md`
  C10.** Routed to `specs/tier1-silent-data-loss/QUEUE.md` "Awaiting user
  approval" as **Q-242A**, NOT folded into this feature. Rationale: the 4
  filed sites write CONTENT fields where domain's structural-whitespace
  argument holds; the 8 new sites write NAME fields where it does not, and
  three of the four new families feed the stripped value into a
  uniqueness check the 4 filed sites have no equivalent of. Q3
  (`CheckOperations.py`'s worse, non-str-input variant) is filed
  separately and more severely as **Q-242B**, deliberately not bundled
  with Q-242A. A fourth question, str()-coercion harmonisation, was also
  ruled OUT of scope (`spec.md` C11) and queued as **Q-242C**.

## Rulings landed at cycle 3

- **C12 -- AppendSentence join-boundary ruling.** Invariant: "AppendSentence
  may INSERT at the join boundary. It may never DELETE at the join
  boundary." Three options considered: the cycle-1 rstrip-anchor candidate
  (REJECTED -- discards the caller's trailing space, violating the
  invariant) and a document-only option (REJECTED -- leaves the defect
  unfixed indefinitely); the ACCEPTED shape anchors the terminator at the
  last non-whitespace character and reuses the caller's existing trailing
  whitespace as the separator, deleting nothing. Needs no exception to
  #242's no-strip principle (`rstrip()` computes an index only; never
  written). Four-case algorithm and the C12.4 inertness proof (provably
  inert whenever `trail == 0`, i.e. every input reachable before #242) are
  recorded in full at `spec.md` C12. Classification: PRE-EXISTING and
  NEWLY VISIBLE, not introduced by the whitespace fix -- standalone
  `### Fixed` CHANGELOG entry; the cycle-2 "Known interaction, not yet
  resolved" sub-paragraph is DELETED, not amended. Verified live,
  9/9 prediction rows MATCH, `evidence/live-t5-joinfix.md`.
- **C13 -- Checkpoint 4 / Q2 ruling: DECLINED, not deferred.** The owner's
  44/104 and 41/86 field figures were diagnostic; the mechanism is already
  proven directly at unit level by P6. Explicit negative claim: **WE DO
  NOT CLAIM TO HAVE REPRODUCED THE OWNER'S 41/86 FIGURE.** Q2 DISCHARGED.

## Contradictions found and preserved

**None.** The three cycle-1 reports (programmer, explore, domain), the
evidence file, and this pass's independent re-verification of the live
source at HEAD were checked against each other; no two assert incompatible
facts. One apparent numbering mismatch (Explore's "persist" line numbers
vs. this pass's `Contents =` assignment lines) is a difference in
convention, not a contradiction, and both are shown together in `spec.md`
C1 so neither reading is lost. See `spec.md` section 5 for the full check.

## Cycle 5 (2026-09-08) -- second independent gate, five verifiers

`reviews/cycle5-verification-swarm.md`. Five adversarial verifiers, no
numbers taken from prior reports: code conformance PASS, docs PASS, live
evidence FAIL, regression FAIL, scope discipline FAIL. **All three FAILs
were record or environment, none was substance.**

- **Substance re-verified from scratch.** C8's shape at all four sites;
  C12's four-case algorithm; C10's 8 sibling sites untouched and still
  bug-shaped. C12's no-strip guarantee was upgraded from observed to
  **structural**: `raw.rstrip()` occurs once inside `len(...)`, so its
  string result is never bound and is unreachable, and every
  `ReplaceTsString(n, n, ...)` is zero-width -- deletion at the join
  boundary is not expressible in the code.
- **Five record repairs landed** -- C14 written (it had been cited in
  `ed428f7` and at campaign level but never written into `spec.md`), C15
  narrowing C12's inertness citation, C17 recording line-number drift,
  `tasks.md`'s four stale/false statements corrected, and
  `AppendSentence`'s docstring summary fixed where it still stated the
  pre-C12 rule as current.
- **Two items OPEN** -- C18 (environment, `needs_human`) and C16 (live
  evidence durability, blocked by C18).
- **One item for a human to check** -- `066bab0`'s body carries `closes
  #242`, against the campaign record's "files and closes nothing."
  `gh issue view 242` could not resolve the issue from the cycle-5
  session, so the issue's actual state is UNVERIFIED.
- **Not remediated, recorded only** -- `ed428f7` breached two no-touch
  constraints (it edited the campaign handoff and the queue's item-3/item-4
  notes from inside a `docs(242)` commit). Bookkeeping only, no work
  started on items 3 or 4, and not repairable without rewriting history.

## Next pickup

**All checkpoints are DONE, DECLINED or CLOSED, and the verification gate
has run twice, both green.** There is **no remaining implementation, test
or verification work inside this feature.**

What remains is not this feature's to close:

1. **C18 -- the test environment is broken.** `needs_human`. Python 3.14.5
   is the only interpreter; `requires-python` is `>=3.8,<3.14` and
   `pythonnet` is pinned `<3.1` with no 3.14 wheel, so `import clr` fails
   and the offline suite cannot execute. **The 1292/483 baseline is
   currently neither confirmed nor refuted.**
2. **C16 -- the live-evidence durability gap.** Blocked by C18.
3. **N7 -- confirm #242's state on GitHub** and reopen if the `closes
   #242` keyword closed it unintentionally.

`feature_complete` was APPROVED at campaign level at cycle 4; this file
does not set it and never did. Checkpoint 5 (the 8 sibling sites) remains
DELETED -- C10 routed that scope to the campaign QUEUE.md, not to this
feature. Note that Q-242A's subject is now under active investigation at
`specs/name-field-whitespace-identity/` while `QUEUE.md` still reads "No
work happens on this until the user rules" -- outside this feature's
boundary, but the campaign record should be reconciled.

## Hard constraints for any future spurt on this feature

- `target_sandbox` / `target_sandbox_path` fixtures ONLY -- never the real
  Target, never any `scripts/restore_*.py` run.
- Derive every live count with `--collect-only -q -m requires_live_project`
  and paste it into the evidence file. "No tests collected" is a ZERO,
  never a pass.
- Offline baseline is **1292 passed** as of `b0e3d14`. Never bare `pytest`.
  **As of 2026-09-08 this baseline cannot be reproduced at all** -- see
  `spec.md` C18. Do not treat a failing offline run as a #242 regression
  until the interpreter is restored; check `python --version` against
  `requires-python` FIRST.
- The C28 forward rule: a stated prediction is committed BEFORE the
  measuring run.
- `tests/operations/test_issue242_whitespace_probe.py` already exists --
  EXTEND it, do not duplicate it.
- No GitHub issues filed from inside this feature. R3's 8 sites (Q-242A),
  Q3's `CheckOperations.py` variant (Q-242B), and the coercion question
  (Q-242C) are now appended to
  `specs/tier1-silent-data-loss/QUEUE.md` "Awaiting user approval" -- do
  not disturb, reword or reorder the entries that preceded them.
- Do not touch `specs/feature-structure-sync-gap/` or campaign queue items
  3 and 4 from inside this feature.
