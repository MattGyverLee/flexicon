# Cycle 14 -- Draft closure comment for flexicon#252 (DRAFT ONLY, not posted)

**Status of issue at time of drafting:** OPEN, ZERO comments (confirmed via
`gh issue view 252 --json state,comments`, read-only, 2026-09-07). No
mutating gh command (`close`/`comment`/`edit`) was run, and none will be run
by this task. `4e9d152`'s commit trailer "closes #252" did NOT auto-close
it -- that commit landed direct-to-main with no PR, so GitHub never saw the
closing keyword in a merge context.

**Closure requires the user's own authorisation, exactly as #251's did.**
This file is a draft for the user/lead to review and edit. Nothing in this
task takes any GitHub action.

**Readiness:** READY. No P0 was found by the cycle-14 verification gate or
by this audit's independent re-derivation (`reviews/cycle14-archivist.md`).
One P2 exists (CompareTo/CHANGELOG omission) and is named explicitly below,
per the gate's recommendation.

---

## Proposed GitHub comment (verbatim, ready to post if approved)

```
Fixed in commit 4e9d152 (tests: 4b746a0). Independently gated PASS at
cycle 14 (specs/feature-structure-sync-gap/reviews/cycle14-verification.md).

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

**One disclosed side effect, not covered by this fix and not something we
consider a defect:** `CompareTo`'s behaviour changes as a side effect of the
two new key-pairs now existing at all. Two POS with identical feature
specs but independently-created structs (different struct GUIDs) now report
a difference on the `<key>Guid` key, where before neither key existed to
compare. This is pinned by a dedicated test
(`TestPOSSyncCompareToStructGuidPinning`) but was NOT mentioned in the
CHANGELOG entry for this fix -- flagging it here so a reader relying on
"closes #252" is not surprised by it later. A candidate follow-up (compare
serialized spec content rather than struct identity) is noted but not
filed as its own issue.

**Explicitly NOT covered by this fix:**
- The CompareTo struct-GUID behaviour change above -- disclosed, not fixed.
- Two writing-system resolution sites this campaign does not reach, already
  filed separately as #266 and #267.

**Verification:** live, `run_mode: live`, against a real FLEx project, with
five characterizing mutations run from scratch in a disposable worktree
(each restored and hash-verified), a live enumeration of the ~16 other
call sites this cast also touches (89 passed/1 skipped, identical on both
sides of the fix, zero regressions), and the tracked HVO-path probe above.
Full detail: specs/feature-structure-sync-gap/reviews/cycle14-verification.md
and specs/feature-structure-sync-gap/evidence/live-cycle14-gate.md.

Closing as resolved.
```

(Word count of the comment body above: ~490 words.)

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
  --json state,comments,title` (confirms OPEN, zero comments).
- No `gh issue close`, `gh issue comment`, `gh issue edit`, or any other
  mutating command was run.
- `git status --porcelain` before and after writing this file showed only
  the five known pre-existing foreign noise items, plus this new file (and
  the audit report) as untracked additions from this task.