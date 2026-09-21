# QC Review - Cycle 1

**Feature:** 338-publication-defaults (PR #344)
**Recommendation:** PASS (with one P2 follow-up)

## Findings

- **P2 - Clone loses source publications (LexEntryOperations.py:397, :419-420).**
  `Clone()` builds its new entry via `self.Create()`, which now seeds
  `DoNotPublishInRC` with every publication. The subsequent copy of
  `source_entry.DoNotPublishInRC` therefore only restores the source's
  *excluded* set, so a clone of an entry that was *published* in some
  publication is now excluded from it. Pre-fix clone inherited the source's
  exclusion set and stayed published elsewhere by default. Acceptable for
  issue #338's goal (create = opt-in), but should be documented as a behavior
  change for callers who clone published entries.

## Questions answered

1. **Recursion** - PASS. `Publications.GetAll()` (recursive=True) walks
   `SubPossibilitiesOS` depth-first; `DoNotPublishInRC` is a
   `CmReferenceCollection` over `ICmPossibility`, so top-level and
   sub-publications both add cleanly. Matches existing usage at
   ExampleOperations.py:1656 and LexEntryOperations.py:2335.
2. **Clone regression** - See P2 above. Not a data-loss bug; intentional
   create-opt-in semantics. Recommend a docstring note.
3. **Transaction / None safety** - PASS. All 5 call sites are inside
   `_TransactionCM`. Helper guards on None item, missing `DoNotPublishInRC`,
   missing `Publications`, and missing `GetAll`, so it is a safe no-op on an
   unopened or partially-initialized project. Blank-sense `Add()` precedes
   the helper at LexEntryOperations.py:242-243.
4. **Semantic consistency** - PASS. The in-place `if publication not in
   item.DoNotPublishInRC: ...Add()` mirrors the established publication
   exclusion pattern.
5. **Test quality** - PASS. All 6 paths round-trip through the LCM
   (`Find()` / gloss / example-text re-read) rather than asserting on the
   just-returned object; use `target_sandbox`, `requires_live_project`,
   `TEST_issue338_` prefixes, and `finally:` cleanup. Skips when the sandbox
   has no publications.

## Verification status

See `evidence/live-338-verification.md`: 6/6 passed against a live LCM
(`FLEXLIBS_REQUIRE_LIVE=1`, `run_mode: live`).