# STATUS -- lcm-member-truth-sweep

**Last updated:** 2026-09-18 (end of spurt 1)
**Status:** in_progress -- 1 of 8 checkpoints complete
**Baseline:** `598f41e` (v4.8.0)
**Issues:** #302, #261, #283, #259, #303, #309

## What landed this spurt (checkpoint 1: ground truth + spec)

Cycle 1 was investigation only -- **no production file was modified**
(`git status --porcelain` clean of `flexicon/` edits). Three specialists ran
in parallel and all three returned.

- **Live reflection sweep** (`run_mode: live`, Sena 3 + pure
  `clr.GetClrType`) settled all six issues' member surfaces.
  -> `reviews/cycle1-verification.md`, `evidence/live-cycle1-reflection.md`
- **9 reflection ratchet tests** added, all passing live.
  -> `tests/operations/test_lcm_member_truth_sweep.py`
- **Domain ruling** on the `OverlayOperations` rewrite: drop the
  `PossibilityItemOperations` base, re-root on `ILangProject.OverlaysOC`,
  delete 10 dead methods with a migration table, split over 3 spurts.
  -> `reviews/cycle1-domain.md`
- **Blast-radius + sibling catalogues**: 62 executable production sites
  across the six issues; 25 ranked sibling candidates, 22 of them
  high-confidence silent data loss. -> `reviews/cycle1-explore.md`
- **Spec and task list written**, with 14 binding rulings (C1-C14) and 4
  open questions (Q1-Q4). -> `spec.md`, `tasks.md`

### Headline findings

- **#259 is a navigation fix, not a rename.** `IWfiMorphBundle` has no such
  member at all; the value lives one hop away at
  `IMoStemMsa.InflectionClassRA`. Of 1932 real Sena 3 bundles, 94 have a
  null `MsaRA` and 1144 of the 1838 non-null ones carry a non-stem MSA that
  **raises** on unguarded access. The type narrowing is load-bearing.
- **#283 drops data today.** A seeded live probe showed the duplicate's
  contexts `None` after `Duplicate(deep=True)` -- the code implements
  neither reference nor clone semantics, just silent loss.
- **#261's real blast radius is 38 public methods**, not the one the issue
  names, and a bare `except` mislabels the cause in all 38.
- **Two existing tests are compromised.**
  `test_datanotebook_duplicate.py` never imports the production module and
  would pass no matter what `Duplicate()` does (C4: delete and rewrite).
  `test_260_environment_resolver_gate.py:311-317` deliberately asserts the
  bug and will go red on the #283 fix (C8: invert in the same commit).

### Rulings made this spurt (full text in `spec.md` section 3)

- **C1** #302 adopts `self.project.lp.ResearchNotebookOA.RecordsOC` (the
  existing house idiom) over `repos.Singleton.RecordsOC` (which would be a
  brand-new pattern -- `.Singleton` appears zero times in `flexicon/`).
  Gated on the T2.1 live probe; flips if `ResearchNotebookOA` can be null.
- **C13** Catalogue 2's 22 siblings stay **out of scope for behaviour
  change** -- but with a named owner and date, not a vague "later": the
  catalogue is copied to a durable file (T2.6), a ready-to-file proposal
  batch is drafted at the end of checkpoint 2 (T2.7), and rows already in
  scope get live absence-ratchets at zero marginal cost (T2.5).
- **C14** Future dispatches must respect each specialist's toolset:
  `lex-domain`, `Explore`, `lex-qc`, `lex-author`, `lex-README` and
  `lex-synthesis` are read-only and cannot write their own report files.

## Next pickup (checkpoint 2)

**#302 + #261 in `flexicon/code/Notebook/DataNotebookOperations.py`** --
four executable lines across two issues in one file.

Start with **T2.1**: the live probe that gates C1 (is
`lp.ResearchNotebookOA` non-null on both Target and Sena 3, and is it the
same object as `repos.Singleton`?). If that probe fails, flip C1 to the
`Singleton` form **before** writing any fix.

Then T2.2 (the three `RecordsOC` sites), T2.3 (the resolver plus removing
the `except` mask), T2.4 (delete and rewrite the non-test), T2.5-T2.7 (the
C13 catalogue hand-off), T2.8 (live evidence), T2.9 (commit and push).

## Nothing is blocked

No `needs_human` gate is open. The one that will open is T2.7/T8.4: issue
filing for Catalogue 2 requires the user's approval and cannot be done by
the crew.
