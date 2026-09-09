# Archivist Report -- Pre-flight audit for archival close of #270

**Date:** 2026-09-09
**Repo:** MattGyverLee/flexicon (gh default set explicitly; upstream remote
avoided)
**Action:** Read-only audit. No code changes, no issue edits made.

## Check 1 -- GramCatOperations.GetAll (deferred to #276)

- Source unchanged: `flexicon/code/Grammar/GramCatOperations.py` lines
  119-125 still does bare `yield cat` in `walk()`, guarded by
  `hasattr(cat, "SubPossibilitiesOS")`, no cast added.
- Pinning tests present and unmodified:
  `tests/operations/test_collection_cast_pattern.py:836-882`,
  `TestGramCatGetAllRecursionClaim`, asserting `IFsFeatStrucType` has no
  `SubPossibilitiesOS` against the checked-in LCM baseline.
- Issue #276 ("GramCatOperations walks MsFeatureSystemOA.TypesOC:
  recursion is unreachable...") is **OPEN** and owns this. **Deferral
  holds.**

## Check 2 -- FLExProject possibility helpers (deferred to #279)

Line numbers cited in #279 (`:4173`, `:4184`) have shifted with unrelated
edits but the helpers and their behavior are unchanged:

- Was `:4173` -> now `ListFieldPossibilities` (def line 4202, `return
  pList.PossibilitiesOS` at line 4219) -- still returns the live
  collection, no cast.
- Was `:4184` -> now `ListFieldLookup` (def line 4221, `return
  pList.FindPossibilityByName(...)` at line 4230) -- still returns the
  base-typed `ICmPossibility`, no cast.

Issue #279 is **OPEN** and its description matches current source.
Nothing in merged #270 work touched these lines. **Deferral holds.**

## Check 3 -- scope hygiene

| Issue | State | Title |
|---|---|---|
| #269 | CLOSED | `__ResolveObject` never casts: GetHeadword raises on any ICmObject... |
| #270 | OPEN | Collection getters return uncast ICmObject: Pattern A sweep covered .Owner but never collections |
| #276 | OPEN | GramCatOperations walks MsFeatureSystemOA.TypesOC: recursion unreachable... |
| #277 | OPEN | Two getters return [] unconditionally: OverlayOperations.GetPossItems / EnvironmentOperations._GetSequence |
| #278 | OPEN | Live verification blocked: no Sena 3 .fwbackup fixture, 23 tests error, #270 Tiers 3/4 unverified |
| #279 | OPEN | #270 remainder: 4 unregistered cast-registry interfaces + FLExProject possibility-helper API decision |

#276/#277/#279 are each self-contained follow-ups (data-model decision,
dead getters, registry+API decision) that #270's stated scope does not
require to close. #278 (Sena 3 fixture gap) is the one item that directly
gates whether #270's Tier 3/4 claims are *verified* -- flag this to the
user before closing, since #270's evidence file is
`live-269-270-272.md`, not the `live-270-tier34.md` path named in the
task brief (that file does not exist in the repo; confirm which is
authoritative before posting any close comment).

## Draft archival close comment for #270 (NOT POSTED)

> Live verification for the collection-cast sweep in this issue is
> recorded in
> `specs/269-272-casting-and-factory-seam/evidence/live-269-270-272.md`.
> Two items originally scoped here were deliberately deferred rather than
> folded in:
>
> - The `GramCatOperations.GetAll` recursion question is a data-model
>   decision, not a casting defect -- tracked separately in #276, with an
>   offline pin in `test_collection_cast_pattern.py`
>   (`TestGramCatGetAllRecursionClaim`).
> - Two getters that read nonexistent properties, and four cast-registry
>   interfaces plus the `FLExProject` possibility-helper API decision, are
>   tracked separately in #277 and #279 respectively.
>
> Those three remain open follow-ups and are out of scope for this issue.

