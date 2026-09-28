# Domain/API-Design Review: Issue #542 (affix slot readers)

**Status:** CONDITIONAL

**1. Return-type change (AffixSlot vs raw IMoInflAffixSlot).** Breaking only in the narrow pythonnet sense: `IMoInflAffixSlot(returned_obj)` round-trips via `LCMObjectWrapper`/`_UnwrapLcm`, but external scripts doing `isinstance`/type checks or `ClassName` equality on the return value see a different Python type. This matches the accepted pattern for every other wrapper. No hard migration entry is needed for behaviour, but a one-line migration-guide note ("GetAffixSlots/*_slots now return AffixSlot wrappers; `.Name`/`.Optional`/`.Hvo` still work") is warranted for FlexTools script authors. **Follow-up acceptable**, before the next tagged release.

**2. CreateAffixSlot should return AffixSlot.** Yes -- a real gap against Rule 3 (unify). `CreateAffixSlot` returns raw `IMoInflAffixSlot` while the readers return `AffixSlot`, so the two halves of the same feature give different object shapes. Small, low-risk change. **Must fix in this PR.**

**3. GetAffixesInSlot returning IMoInflAffMsa.** Matches the LCM model (slots are filled by MSAs) and the #543 vocabulary, so it is defensible as the primitive. It does not match how users think ("which affixes/entries go here"), and forces raw owner navigation. A sense/entry-level convenience (e.g. `GetAffixEntriesInSlot` or an `as_senses` option) is missing. **Follow-up acceptable**; file the issue now.

**4. "Optional" semantics vs the Templates UI.** Matches. Optional slots are shown in parentheses; `IsSlotOptional` reads the same `MoInflAffixSlot.Optional` boolean, and new slots default to obligatory as in FLEx. No change.

**5. Home of the slot methods.** POSOperations is right: slots are owned by `IPartOfSpeech.AffixSlotsOC`, and `AffixTemplate.*_slots` already expose `AffixSlot` wrappers whose docstrings point back to POSOperations. One source of truth reachable two ways. Any future MorphRuleOperations slot convenience should delegate to POSOperations. No change.

## Recommendations Summary
- Must fix in this PR: (2) CreateAffixSlot returns AffixSlot.
- Follow-up acceptable: (1) migration-guide note; (3) sense/entry-level convenience alongside GetAffixesInSlot.
- No action: (4), (5).

Note (recorded by main session): the lex-domain agent had no write tool; this file condenses its hand-back without changing its verdicts.

---
**Reviewed By:** Domain Expert Agent
