# Cycle 3 -- Archivist spec edits

**File touched:** `specs/feature-structure-sync-gap/spec.md` only.

## Sections edited
- **Section 3 / D3** -- corrected "13 entries" to 12 registrable
  `_interface_cache` names + `PosFeatures` hardcoded to `None` (E1); T1 marked
  `[x]` DONE, commit `1790fcc0`; stated C1 is UNAMENDED. Added the E2 finding
  (only `PhNCFeatures`/`PhPhoneme` have `FeaturesOA`; confirms C1) plus the
  unlocked `FeatureStructureDelete` clear-path side effect.
- **New D3a** -- scope statement (E3): T6 unchanged; T11 changes twice
  (drop `PosFeatures`, add E2 regression test).
- **Section 4** -- header retitled `C1-C8, C4a-C4b`; **new C4a** (accept both
  wire shapes) and **new C4b** (capture stays legacy for NC/Phoneme; T9b is
  the migration task) inserted between C4 and C5 (E4).
- **Section 5** -- header gained re-cut checkpoints (2a = T1-T3, 2b = T4-T5);
  T1 marked done with corrected entry count; T3 got the E5 `__ResolveByGuid`
  corollary; T4 got the E5 `inspect.getsource` hazard/ruling; new **T9b**
  inserted after T9; T11 updated with the two E3 changes.

## Rulings that did not apply cleanly
None. All five (E1-E5) slotted into existing structure without contradicting
surrounding text; D3's original "Entries to add" list and mandatory-guard
paragraph needed direct correction (kept guard text unchanged, only the count
and list corrected) rather than append-only, since leaving the wrong 13-name
list in place would have been actively misleading.

No other files touched. No GitHub issue filed.
