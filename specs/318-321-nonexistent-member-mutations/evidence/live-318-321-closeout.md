# Live verification -- #318/#319/#320/#321 closeout

**Date:** 2026-09-20
**Baseline:** `aadb86a` (main, after rebase onto `f909721`)
**run_mode:** `live` (confirmed in `tests/live_status.json` after every run below)
**Fixture:** `target_sandbox` -- a tempdir copy of the Target `.fwbackup`.
The registered Target and Sena 3 projects were never opened for writing.
**FieldWorks:** 9 (`C:\Program Files\SIL\FieldWorks 9`)

This run was requested to justify closing #318-#321. It did not: it
found that **#318's fix did not work**, for two further reasons in the
same bug class as #318 itself. Both are fixed here, and #318 is verified
live for the first time.

---

## 1. What the re-run was checking

`specs/318-321-nonexistent-member-mutations/reviews/cycle3-rulings-applied.md`
recorded 29 live failures across `test_natural_classes`,
`test_phon_features`, `test_phon_rules`, `test_phonemes` and a
duplicate-operations module, attributing them to a concurrently-edited
working tree. That attribution was doubtful, because every one of those
is a `Duplicate()` path and `Duplicate()` runs through the
`clone_properties()` predicate that #321 narrowed.

**The attribution was right, the count was wrong.** Re-running those
modules live gives **1 failure, not 29**:
`test_natural_classes.py::TestNaturalClassSync::test_apply_raises_on_type_mismatch_segments_target`
(`AttributeError: 'ICmObject' object has no attribute 'Name'` at
`NaturalClassOperations.py:1270`).

That failure is **pre-existing and unrelated to #321**, established by
A/B: reverting `flexicon/code/lcm_casting.py` to its pre-#321 state
(`git checkout f909721 -- flexicon/code/lcm_casting.py`) and re-running
the single test reproduces it identically. It is an uncast-resolver
defect of the #275/#284 family, not a regression from this work.

All `Duplicate()` live suites pass with #321 in place: 12 passed across
`test_lexentry_duplicate`, `test_datanotebook_duplicate`,
`test_discourse_duplicate`, `test_note_duplicate`,
`test_wfi_analysis_duplicate`, `test_phoneme_duplicate_fix`.

## 2. #318 was still completely broken -- two further nonexistent members

#318 repaired the *removal* call (`dupe.OwningList.Remove()` ->
`entry.PronunciationsOS.Remove()`). It did not repair *detection*, which
sits upstream of it and never produced a single duplicate candidate. Two
separate defects, both the same shape as #318 -- a member that does not
exist, swallowed by a broad `except Exception: continue`:

### 2a. `cache.WritingSystemManager.AllWritingSystems` does not exist

Five sites built their signature maps by iterating
`self.project.project.WritingSystemManager.AllWritingSystems`
(`LexEntryOperations.py:3111, 3195`; `LexSenseOperations.py:3677, 3685,
3837`). Live probe:

    AttributeError: 'LcmCache' object has no attribute 'WritingSystemManager'
    AttributeError: 'WritingSystemManager' object has no attribute 'AllWritingSystems'

Two errors stacked: the manager hangs off `ServiceLocator`, not the
cache, and the enumeration member is on `ServiceLocator.WritingSystems`.
The correct chain is `ServiceLocator.WritingSystems.AllWritingSystems`,
as `WritingSystemOperations.GetAll()` already used.

Every iteration therefore raised into the enclosing
`except Exception: logger.debug(...); continue`, so `sig_map` stayed
empty, `found_count` stayed 0, and dedup returned silently having
examined nothing -- for every entry, every sense, every caller.

### 2b. `ILexExampleSentence.Reference` is an ITsString, not a multi-string

`__GetExampleSignature` computed
`ITsString(example.Reference.get_String(0)).Text`. Live probe:

    Reference type: ITsString
    get_String(0) RAISED AttributeError: 'ITsString' object has no attribute 'get_String'

`Reference` is a plain `ITsString` and has no `get_String(ws)`; only
`Example` is a multi-string. The `AttributeError` was caught by the
method's own `except Exception: return None`, so **every** example
produced a `None` signature and example dedup never found a duplicate.

This is CLAUDE.md "Category 8: same-name fields with different LCM
types" -- two members on the same object, one multi-string and one not,
accessed as though both were multi-strings.

### 2c. Why review did not catch it

`tests/operations/test_issue318_dedup_owninglist.py` wired its mock as
`project.project.WritingSystemManager.AllWritingSystems`. Since
`project.project` is a bare `Mock()`, that nonexistent path
auto-vivified and the mock suite passed green **against production code
that raised on every real database**. The mock encoded the bug. It now
mirrors the real member chain, with a comment saying why that matters.

## 3. #319 -- strict xfail fired, as designed

The six live tests in
`tests/operations/test_issue319_participants_researchers_live.py` were
marked `xfail(strict=True)`, blocked by the `DataNotebookOperations`
defects of #261/#302 (`LcmCache.GetObject`, `repos.RecordsOC` on the
service object). Those were fixed upstream by `994f2ee`, so the markers
XPASSed and failed the suite -- exactly the behaviour they were written
to produce. Markers removed; the stale module note is corrected.

## 4. Commands and results

    $env:FLEXLIBS_REQUIRE_LIVE = "1"

    python -m pytest tests/operations/test_issue318_dedup_owninglist_live.py -m requires_live_project -q
      -> 5 passed, 1 skipped

    python -m pytest tests/operations/test_issue319_participants_researchers_live.py -m requires_live_project -q
      -> 6 passed

    python -m pytest tests/operations/test_natural_classes.py tests/operations/test_phon_features.py \
        tests/operations/test_phon_rules.py tests/operations/test_phonemes.py -m requires_live_project -q
      -> 1 failed, 58 passed, 1 skipped   (the 1 is pre-existing, see section 1)

    python -m pytest <6 Duplicate modules> -m requires_live_project -q
      -> 12 passed, 24 deselected

    python -m pytest <11 modules, live sweep> -m requires_live_project -q
      -> 27 passed, 1 skipped, 3 errors   (errors = missing Sena 3 fixture, see below)

    python -m pytest -m "not requires_live_project" <7 mock modules> -q
      -> 104 passed, 4 deselected

`tests/live_status.json` reported `"run_mode": "live"` for every run.

### Pre-state / post-state read back from the LCM

For the pronunciation, allomorph and example cases, the post-state is
re-queried through
`cast_to_concrete(ServiceLocator.GetObject(survivor.Hvo))` after the
merge rather than read from the pre-merge Python handle. Confirmed
post-state: exactly one item bearing the duplicated form/text survives
(two before the fix); the master and the distinct sibling both survive
by Hvo; the removed duplicate has `IsValidObject == False` and
re-resolving its Hvo raises, so it was genuinely deleted rather than
orphaned.

### A test-design correction worth recording

The first version of the live test asserted `before - after > 0` on the
owning sequence. That is the wrong signal: LibLCM's own
`survivor.MergeObject(victim)` **appends the victim's lexeme form to
`AlternateFormsOS` while collapsing the duplicate**, so the net length
is unchanged (3 -> 3) even on a fully successful dedup, and the
assertion reads as the pre-fix silent no-op. The tests now assert on how
many items carry the duplicated form -- one when dedup ran, two when it
did not.

## 5. Not covered

- **`tests/fixtures/` has no `Sena 3*.fwbackup` on this machine**, so
  every `sena3_sandbox` test errors under `FLEXLIBS_REQUIRE_LIVE=1`.
  That is the fail-loud rule working, not a regression: 14 errors in
  `test_lcm_member_truth_sweep.py` and 3 in
  `test_overlay_operations.py::TestGetPossItemsLive`. #320's own live
  evidence comes from the earlier cycle's
  `evidence/live-cycle2-business-rules.md` instead.
- `FP_DeduplicationError`'s partial-failure branch has no live test. With
  no inner `try/except` around `.Remove()`, a live `.Remove()` either
  raises or succeeds; making it return normally while leaving the item
  in place requires monkeypatching the owning sequence, which does not
  belong in a live-verification file. The mock suite covers the branch.

## 6. Verdict

**PASS** for #318, #319, #321. #320 passes on mock plus the earlier
cycle's live evidence; its remaining live module needs the Sena 3
fixture restored.

#318 is only now actually fixed. Had these issues been closed on the
previous run's evidence, deduplication would have shipped as a silent
no-op for the second time -- which is the defect #318 was filed about.
