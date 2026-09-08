# Draft closure comment for flexicon#252 (DRAFT ONLY, not posted)

**Drafted** cycle 14; **corrected** cycle 15 (call-site coverage over-claim
fixed; CompareTo/CHANGELOG line updated now that `9d00826` has landed).

**Status of issue at time of drafting:** OPEN, ZERO comments (confirmed via
`gh issue view 252 --json state,comments`, read-only, 2026-09-07). No
mutating gh command (`close`/`comment`/`edit`) was run, and none will be run
by this task. `4e9d152`'s commit trailer "closes #252" did NOT auto-close
it -- that commit landed direct-to-main with no PR, so GitHub never saw the
closing keyword in a merge context.

**Closure requires the user's own authorisation, exactly as #251's did.**
This file is a draft for the user/lead to review and edit. Nothing in this
task takes any GitHub action.

**Readiness:** READY. No P0 was found by the cycle-14 verification gate, by
the cycle-14 archivist re-derivation, or by the cycle-15 LEG 2b close-out.
The one P2 the cycle-14 draft carried (the CompareTo change being absent
from the CHANGELOG) was FIXED at `9d00826`, and the text below is updated
accordingly.

## Cycle-15 correction log

Two things in the cycle-14 version of this draft were wrong and are fixed
here:

1. **Over-claim on call-site coverage.** The old text read "a live
   enumeration of the ~16 other call sites this cast also touches (89
   passed/1 skipped ...)", which reads as though all 16 sites were
   exercised live. They were not. The cycle-14 verification report's own
   wording was "many, though not exhaustively every one", and the draft
   dropped that qualifier. The Verification section below now states the
   actual per-site coverage: 5 live at both commits, 2 live at HEAD only,
   9 not live at either.
2. **Stale CHANGELOG claim.** The old text said the CompareTo side effect
   "was NOT mentioned in the CHANGELOG". It is now disclosed there
   (`9d00826`).

Everything else the cycle-14 draft got right is preserved: both halves of
the fix, the correction of our own earlier cycle-1 finding, and the
explicit NOT-covered section citing #266/#267.

---

## Proposed GitHub comment (verbatim, ready to post if approved)

```
Fixed in commit 4e9d152 (tests: 4b746a0). Independently gated PASS at
cycle 14 (specs/feature-structure-sync-gap/reviews/cycle14-verification.md),
with the write-path residual closed at cycle 15
(specs/feature-structure-sync-gap/evidence/live-cycle15-leg2b.md).

**This fix has two halves, and the second is wider than what this issue
asked for.**

**Half 1 -- the feature-struct coverage gap this issue actually reported.**
`PartOfSpeech` has two feature-struct-owning properties in the frozen C1
table (`DefaultFeaturesOA`, slot "Default"; `InherFeatValOA`, slot
"InherFeatVal"). Neither was ever captured or applied by
`GetSyncableProperties`/`ApplySyncableProperties`, so a synced POS carried a
correct Name/Abbreviation/Description/CatalogSourceId but a permanently
null feature structure. Both properties are now captured and applied,
routed through the existing shared resolver/capture/apply helpers (no new,
independent copy of the owner table), with the slot passed explicitly at
every call site -- `PartOfSpeech`, unlike `MoStemMsa`, is ambiguous between
its two rows, and the ambiguous-without-slot path raises rather than
guessing.

**Half 2 -- an independent, pre-existing bug this issue did not name, on
the HVO entry path.** `POSOperations.__ResolveObject` returned a bare,
uncast `ICmObject` whenever `GetSyncableProperties`/`ApplySyncableProperties`
was called with an HVO integer instead of an already-typed object (the
shape `GetAll()` yields). Because every capture in that method was
`hasattr`-gated, this silently dropped `Name`/`Abbreviation`/`Description`/
`CatalogSourceId` too -- not just the two new feature-struct properties.
Live-measured before and after the fix, independently re-derived at cycle
14 with a tracked probe against the same pre-existing POS at both commits:
0 of 4 keys present before, all 4 present after
(specs/feature-structure-sync-gap/evidence/live-cycle14-gate.md, LEG 3).

**This corrects an earlier finding of ours.** An early pass on this issue
concluded "#252 is a pure coverage gap ... hasattr works correctly on every
object GetSyncableProperties will ever receive." That statement was true
only for the `GetAll()` entry path and false for the HVO entry path -- the
26-of-26-true measurement it was based on was itself taken on
`GetAll()`-sourced objects, which is exactly why the HVO-path bug did not
show up in it. #252 was a coverage gap plus an independent silent-drop bug,
not a pure coverage gap.

**One disclosed side effect, not something we consider a defect:**
`CompareTo`'s behaviour changes as a side effect of the two new key-pairs
now existing at all. Two POS with identical feature specs but
independently-created structs (different struct GUIDs) now report a
difference on the `<key>Guid` key, where before neither key existed to
compare. This is pinned by a dedicated test
(`TestPOSSyncCompareToStructGuidPinning`) and is disclosed in the CHANGELOG
entry for this fix (commit 9d00826). A candidate follow-up -- comparing
serialized spec content rather than struct identity -- is noted but not
filed as its own issue.

**Explicitly NOT covered by this fix:**
- The CompareTo struct-GUID behaviour change above -- disclosed, not fixed.
- Two writing-system resolution sites this campaign does not reach, already
  filed separately as #266 and #267.
- Nine of the sixteen `__ResolveObject` call sites in `POSOperations` are
  not exercised by any live test, at either commit -- see the precise
  breakdown under Verification. Seven of those nine have no automated
  coverage of any kind. That is a pre-existing test-coverage gap, not
  something this fix introduces, but it bounds how much this fix's
  regression evidence can claim.

**Verification:** live, `run_mode: live`, against a real FLEx project, with
five characterizing mutations run from scratch in a disposable worktree
(each restored and hash-verified), plus the tracked HVO-path probe above.

Coverage of the call sites this cast touches is PARTIAL, and worth stating
precisely rather than in aggregate. `__ResolveObject` has 16 call sites in
`POSOperations`:

- **5 sites live-verified at BOTH the pre-fix and post-fix commits**
  (`Delete`, `GetName`, `SetName`, `GetAbbreviation`, `SetAbbreviation`) --
  the POS write path, via `TestPOSBrackets` against a sandboxed copy of the
  project: 4 passed / 4 passed, `run_mode: live` on both sides, zero flips
  in either direction.
- **2 sites live at the post-fix commit only** (`GetSyncableProperties`,
  `ApplySyncableProperties`) -- these are the fix itself, and cannot exist
  at the pre-fix commit.
- **9 sites not exercised live at either commit.** Two
  (`GetSubcategories`, `GetEntryCount`) have mock-only unit coverage; seven
  (`AddSubcategory`, `RemoveSubcategory` -- two sites --
  `GetCatalogSourceId`, `GetInflectionClasses`, `GetAffixSlots`,
  `Duplicate`) have no test coverage of any kind.

Separately, a broad live regression run over 90 collected items in 15
POS-touching test files was identical on both sides of the fix (89 passed /
1 skipped, zero regressions). A further 55 live items in those same files
were deliberately NOT run: six of the fifteen files write in-place to a
real named FieldWorks project, and doubling that exposure was judged a
worse trade than naming the gap here.

Full detail: specs/feature-structure-sync-gap/reviews/cycle14-verification.md,
specs/feature-structure-sync-gap/evidence/live-cycle14-gate.md, and
specs/feature-structure-sync-gap/evidence/live-cycle15-leg2b.md.

Closing as resolved.
```

---

## Proposed action (would run ONLY on explicit user approval)

```
gh issue close 252 --repo MattGyverLee/flexicon --comment "<comment text above>"
```

or, if the user prefers to keep the issue open a while longer:

```
gh issue comment 252 --repo MattGyverLee/flexicon --body "<comment text above>"
```

Neither command has been run. This file is a draft for the user/lead to
review and edit before any gh mutation happens.

## Confirmation

- Only read-only command executed against GitHub: `gh issue view 252
  --json state,comments,title` (confirms OPEN, zero comments), at cycle 14.
  Cycle 15 ran NO gh command at all, read-only or otherwise.
- No `gh issue close`, `gh issue comment`, `gh issue edit`, or any other
  mutating command was run.
- The five known pre-existing foreign noise items were never staged.
