# Issue #294 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/294-pos-default-features from origin/main

## RULING (binding)

Issue #294 asks for a public read/write surface for the two
`IPartOfSpeech` feature structures that sync already handles internally
(`DefaultFeaturesOA`, `InherFeatValOA`). Q5 in
`specs/276-gramcat-collection/evidence/domain-ruling.md` settles direction:
expose direct access to the owned properties; do not invent category
expansion semantics.

**Correct behaviour (issue #294 scope):**

1. **GetDefaultFeatures / GetInherFeatVal** -- Resolve the POS via
   `__ResolveObject`, then `_ResolveFeatureStrucOwner(pos, slot=...)`.
   When the owning property is `None`, return `None`. Otherwise return the
   C4 recursive dict from `_GetFeatureStruc(struct)` (same shape as
   `GetSyncableProperties` emits under `DefaultFeatures` / `InherFeatVal`).
2. **SetDefaultFeatures / SetInherFeatVal** -- Write-enabled; open a
   transaction; call `_ApplyFeatureStruc(..., on_unresolved="raise")` with
   the same slot/key pairing as `ApplySyncableProperties`. Accept an
   optional `struct_guid` for identity-preserving updates.

**Out of scope:** Name-string operands (#265), GramCat delegation (#276),
or changes to the sync capture/apply key names.

## Pattern audit

Single chokepoint: `POSOperations.py`. No sibling Operations classes share
this two-slot PartOfSpeech table row.

## Verification plan

- Offline: source ratchets + AST checks in
  `tests/operations/test_issue294_pos_default_features.py`; extend
  `test_issue252_pos_feature_sync.py` parity only if needed.
- Live: optional round-trip on a POS with populated default features when
  LCM is available (`requires_live_project`).
