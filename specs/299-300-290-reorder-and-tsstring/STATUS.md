# STATUS — 299/300/290 reorder-and-TsString

**Last updated:** 2026-09-10 (end of spurt 1, cycle 5)
**Status:** BLOCKED on a human decision — code complete, all quality gates green,
but the working tree is shared with another agent and cannot be committed as-is.

## What landed this spurt (cycles 1-5)

All three fixes are implemented, live-LCM verified, and reviewed. They are
**uncommitted** in the working tree.

- **#299** — `TextOperations._GetSequence` deleted (its target
  `project.lp.Texts` is `TextsOC`, an unordered owning collection with no
  indexer/`.MoveTo`; the inherited `BaseOperations` `NotImplementedError` is
  the honest behavior, matching the `LexEntryOperations` no-override
  precedent). `ParagraphOperations._GetSequence` corrected to
  `parent.ContentsOA.ParagraphsOS`; `SegmentOperations._GetSequence`
  corrected to `parent.SegmentsOS` (was `AnalysesRS`, which has its own
  dedicated #215 API).
- **#300** — `WfiMorphBundleOperations._GetSequence` corrected from the
  nonexistent `parent.MorphsOS` to `parent.MorphBundlesOS`.
- **#290** — `ConstChartRowOperations` Get/SetLabel and Get/SetNotes now
  treat `IConstChartRow.Label`/`.Notes` as bare `ITsString` via the house
  `_MakeTsString`/`_ReadTsString` adapters, not as `IMultiString`
  (CLAUDE.md Category 8). The now-inert `ws=` parameter on the getters is
  flagged in-docstring as an open API question, deliberately not changed.

Quality gates: live-LCM verification PASS (`run_mode: live`, pre/post values
re-queried from the LCM); QC 90/100; domain rulings recorded and one
cycle-1 citation error self-corrected in cycle 5. The cycle-3 QC
**Pattern-Audit Gate** is now cleared by the cycle-4 sweeps plus the
cycle-5 snapshot adjudication of all 15 sibling findings.

## Next pickup (blocker first)

1. **Resolve the shared-tree contamination** (needs the user). Another agent
   is running a docstring-example ratchet campaign in this same working
   tree (its test landed as `2cc53d2`; its ~16 files of docstring fixes are
   still uncommitted). Two of our five source files —
   `TextOperations.py` and `WfiMorphBundleOperations.py` — contain that
   agent's hunks interleaved with ours, so no path-scoped commit of those
   files is safe. Either wait for that agent to commit its campaign, or get
   explicit approval to hunk-split.
2. Split `evidence/commit-message-draft.md` (currently one combined message)
   into the agreed five commit messages.
3. Execute the five commits. **COMMIT ONLY — do not push** (shared tree).

## Outstanding, non-blocking

- 11 HIGH + 4 MED sibling sites adjudicated as follow-up work; none fixed
  here. See `evidence/cycle4-snapshot-adjudication.md`.
- This spec dir has no `spec.md`; the work was issue-driven (#299/#300/#290).
