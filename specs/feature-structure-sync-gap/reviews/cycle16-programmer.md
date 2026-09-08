# Cycle 16 -- Programmer report: T8 (AllomorphOperations MsEnvFeaturesOA sync)

T8, spec.md:655. Unfiled P0 -- no GitHub issue exists; filing one remains an
outstanding USER decision. No GitHub action of any kind was taken.

## Commits (this cycle, in order)

1. `cf2fdfed` -- predictions committed verbatim, before any run.
2. `df37e35a` -- production: `flexicon/code/Lexicon/AllomorphOperations.py`.
3. `016a97a4` -- tests: `tests/operations/test_t8_allomorph_feature_sync.py`
   (21 offline + 6 live, `live_phase` markers on all 6).
4. `bd98c6b3` -- live evidence:
   `specs/feature-structure-sync-gap/evidence/live-T8.md`.
5. `191556f2` -- `CHANGELOG.md` disclosure.

Line anchors re-confirmed at edit time (drifted slightly from the dispatch's
:514/:523/:528 due to inserted doc comments): the three pre-existing
`hasattr` gates now sit at :516/:525/:530 pre-edit (renumbered again after
the new docstrings landed); `__GetAllomorphObject` was at :1102-1114
pre-edit.

## Production shape

- `GetSyncableProperties` now resolves `item` through `__GetAllomorphObject`
  first (fixes defect i: it previously used `item` raw). Adds
  `if allomorph.ClassName == "MoAffixAllomorph": self.__CaptureFeatureStrucProp(...)`
  -- positive dispatch, no `else`, no explicit `MoStemAllomorph` guard.
- New `ApplySyncableProperties` override (AllomorphOperations had none
  before): pops `MsEnvFeatures`/`MsEnvFeaturesGuid` before `super()`,
  applies via the same positive dispatch, `on_unresolved="raise"`.
- `__GetAllomorphObject` (defect ii, 11 call sites) now casts to
  `IMoStemAllomorph`/`IMoAffixAllomorph` by `ClassName`, never raises on a
  miss. `slot=None` throughout (R16-1: one C1 row, no ambiguity).

## Prediction adjudication

**P1 -- HELD.** Bare `sandbox.Object(hvo)` measured live: `hasattr` False
for `Form`/`IsAbstract`/`MorphTypeRA`/`MsEnvFeaturesOA` (committed as a
durable test, `TestT8LiveHasattrTrap`, never deleted -- avoids the cycle-13
provenance loss). Pre-fix `GetSyncableProperties(hvo)` measured directly
against parent commit `09fcbf8` in a disposable worktree:
`{'Form': {}, 'MorphTypeRA': None}` -- exact match to the prediction.

**P2 -- HELD.** Unmutated: a real live `MoStemAllomorph`'s capture emits
neither `MsEnvFeatures` nor `MsEnvFeaturesGuid` and does not raise
(`TestT8LiveStemAllomorphNoFeatureKeys`). Mutation **M-T8-2** (delete the
`ClassName == "MoAffixAllomorph"` guard in `GetSyncableProperties`, resolver
called unconditionally): the same live test FAILED with
`FP_ParameterError: _ResolveFeatureStrucOwner: ClassName 'MoStemAllomorph'
is not a recognized feature-structure owner...` -- exact match. Two offline
tests (`test_capture_stem_allomorph_returns_no_feature_keys_and_never_calls_resolver`,
`test_capture_unknown_class_name_returns_no_feature_keys_and_never_calls_resolver`)
also died under the same mutation. Restore hash-verified:
`6a0c6e94fdba934b38fdeea1bdf01a9eb8a0ab7d`.

**P3 -- HELD.** Static AST test
`test_no_non_none_slot_literal_anywhere_in_feature_struct_calls` confirms no
`slot="..."` literal other than `None` in `GetSyncableProperties`/
`ApplySyncableProperties`/the two private feature helpers. No slot-
disambiguation test exists (correctly -- N/A per R16-1).

**P4 -- HELD, measured at both commits (`09fcbf8` and `016a97a4`), never
reasoned.** Wide offline comparator (`tests/operations tests/contract -m
"not requires_live_project"`) in a disposable worktree: BEFORE `2 failed,
416 passed, 518 deselected`; AFTER `2 failed, 437 passed, 524 deselected`
-- delta is exactly +21/+6 (the new T8 tests), same 2 foreign
`TestPhase2JoinOrOpen` failures both times. Matches the documented
comparator baseline exactly (416/2, red set of 2, not 3). Narrow LIVE
comparator over the archivist-confirmed 9-file wide-instrument set
(`test_allomorphs_live.py`, `test_lexicon_brackets_live.py`,
`test_owner_cast_pattern.py` -- the other 6 files in the grep-derived floor
carry no `requires_live_project` marker per
`reviews/cycle16-archivist-callsites.md`): BEFORE and AFTER both
`31 passed, 24 deselected, 2 xfailed`; sorted per-test PASSED/XFAIL lists
diffed byte-for-byte -- zero flips. Noted, not hidden: 7 of `Allomorphs`'
11 call sites have zero pre-existing live coverage at all (per the
archivist), so the C2 widening at those 7 sites is untested by this
comparator (vacuously non-flipping).

**P5 -- HELD.** Mutation **M-T8-1** (remove the cast in
`__GetAllomorphObject`, unconditional `return obj`): live tests
`TestT8LiveDirectCast::test_hvo_path_casts_to_concrete_affix_allomorph`
and `TestT8LiveRoundTrip::test_hvo_entry_path_captures_form` FAILED; the
`MsEnvFeaturesOA` round-trip, C7-raise, and stem-no-raise live tests all
SURVIVED (compensating layer: `_ResolveFeatureStrucOwner` casts
internally). Exact predicted split. Restore hash-verified:
`6a0c6e94fdba934b38fdeea1bdf01a9eb8a0ab7d` (matches
`git rev-parse HEAD:flexicon/code/Lexicon/AllomorphOperations.py`).

All five predictions HELD; none falsified. Nothing required a
`needs_human` escalation.

## Mechanics compliance

Disposable worktree (`git worktree add`/`remove --force`) used for both
mutations and the before/after comparator checkouts; the shared tree was
never mutated (confirmed clean `git status --porcelain` before/after).
Restores hash-verified via `git hash-object`, never `git checkout` in the
shared tree. Fixtures copied read-only into the worktree. All five commits
used `git commit --only -F <msgfile> -- <path>` (new files: single
`git add -- <path> && git commit --only ...` invocation), index verified
empty via `git status --porcelain` before and after each. The five noise
items (`.claude/ralph-loop.local.md` deletion, `.vscode/`, two
`.spec-context.json` files, `specs/duplicate-signature-harmonisation/`) and
the parallel archivist's `reviews/cycle16-archivist-callsites.md` were never
staged.

`tests/live_status.json` quoted verbatim into `evidence/live-T8.md`
(`run_mode: live`, timestamp `2026-09-08T04:08:50Z`) in the same cycle.

## Not done / deferred

`CompareTo`'s struct-GUID-pinning behaviour-change disclosure (T7's
companion test/CHANGELOG pattern) was not replicated for Allomorphs --
out of the explicit R16 scope; flagged here as a candidate cycle-17 note,
not filed.
