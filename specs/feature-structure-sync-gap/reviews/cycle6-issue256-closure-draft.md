# Cycle 6 -- Draft closure comment for flexicon#256 (DRAFT ONLY, not posted)

**Status of issue at time of drafting:** OPEN (confirmed via `gh issue view 256`,
read-only, 2026-09-07). No mutating gh command (`close`/`comment`/`edit`) was run.

**Issue's own three asks (quoted from `gh issue view 256`):**
1. "Resolve the owning property per type (`InflFeatsOA` / `MsFeaturesOA` /
   `FeaturesOA`) instead of hard-coding `FeaturesOA`."
2. "Support nested specs, e.g. `("noun agreement", [(feat, val), ...])`."
3. "Add `CopyFeatStruc(src_fs, target_owner)` -- copying an existing structure
   is the common real operation and is currently ~25 lines of raw LCM."

---

## Proposed GitHub comment (verbatim, ready to post if approved)

```
Fixed in commit 6643b483. BaseOperations now has one generalized
_MakeFeatStruc; InflectionFeatureOperations.MakeFeatStruc and
PhonFeatureOperations.MakeFeatStruc are both 1-line call-throughs to it.

**Ask 1 -- per-type owner resolution.** Owner resolution now routes through
a ClassName-keyed table (Shared/lcm_constants.py::FEATURE_STRUC_OWNER_TABLE),
so an MSA resolves to MsFeaturesOA/InflFeatsOA rather than the hardcoded
FeaturesOA (which doesn't exist on any MSA type). This was never a casting
bug -- it failed even against a concrete MSA, because the property name
itself was wrong. Verified live: MakeFeatStruc([], owner=stem) on a real
MoStemMsa flips from `FP_ParameterError: owner has no FeaturesOA property`
to returning a real IFsFeatStruc. Reproduced independently by both the
implementer and the verification gate.

**Ask 2 -- nested feature structures: structurally solved, but note the
operand form.** Nesting now works via a recursive dict, keyed by HVO or
GUID rather than by name:

    specs = {agreement_feat.Hvo: {number_feat.Hvo: sg_val.Hvo}}
    InflectionFeatures.MakeFeatStruc(specs, owner=stem_msa)

Verification ran a live two-level round-trip on a real MoStemMsa, re-read
from a FRESH object handle rather than the original reference -- values
matched at both levels. The legacy flat list of (feature, value) tuples is
kept indefinitely (5 internal call sites + shipped tests depend on it); a
dict value nests, a scalar value doesn't.

To be straight about the gap: this issue's example was written with names
(`("noun agreement", [(feat, val), ...])`). Nesting is solved; passing the
operands as bare NAME strings is not -- see the limitation below. The Bantu
two-level shape from the report is expressible today, but you resolve the
IFsFeatDefn/IFsSymFeatVal objects (or their HVOs) yourself first.

**Ask 3 -- CopyFeatStruc(src_fs, target_owner): DEFERRED, NOT DECLINED.**
Already designed and frozen as contract C8:
CopyFeatStruc(self, src_fs, target_owner, slot=None, overwrite=False).
overwrite=False raises rather than silently replacing an existing struct.
There is deliberately no merge mode -- there's no unambiguous domain rule
for a conflicting (feature, value) pair, and that judgment belongs to the
linguist, not a silently-invented policy. Scheduled as task T12 of this
same feature; not started yet, but on the list.

**One honest limitation:** operands accept an IFsFeatDefn/IFsSymFeatVal
object, an HVO int, or a GUID string -- not a plain name. Name-string
resolution was never implemented in either pre-fix version (confirmed by
reading both at their true parent commit); it's recorded as a candidate
follow-up rather than something this fix removed.

**Verification:** live, run_mode: live, against a real FLEx project, with a
falsifiability mutation test (forcing the resolved property name bogus took
the live subset from 1 to 8 failures; reverted, hash-verified
byte-identical restore). Evidence:
specs/feature-structure-sync-gap/evidence/live-T5.md and
specs/feature-structure-sync-gap/evidence/live-cycle5-verification-t5.md
(sections 5 and 8 for the closure-specific checks).

Closing as resolved for asks 1 and 2; ask 3 tracked as T12, not closed by
this fix.
```

(Word count of the comment body above: ~360 words.)

---

## Proposed action (would run ONLY on explicit user approval)

```
gh issue close 256 --repo MattGyverLee/flexicon --comment "<comment text above>"
```

or, if the user prefers to keep the issue open until T12 ships:

```
gh issue comment 256 --repo MattGyverLee/flexicon --body "<comment text above>"
```

Neither command has been run. This file is a draft for the user/lead to
review and edit before any gh mutation happens.

## Confirmation

- Only read-only command executed: `gh issue view 256` (twice: once for
  status/labels/comments, once for full body text).
- No `gh issue close`, `gh issue comment`, `gh issue edit`, or any other
  mutating command was run.
- `git status --porcelain` after writing this file showed only this new
  file as untracked; nothing else was created or modified.
