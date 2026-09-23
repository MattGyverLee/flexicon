<!-- Provenance: main session wrote this file because lex-qc cannot write files. Content is the lex-qc hand-back verbatim. -->

**QC 0672b0b..6abff1c — 98/100**

**P0:** none. **P1:** none. **P2:** none.

**`__ResolveObject` (`MorphRuleOperations.py:1107`).** The `IPartOfSpeech` cast runs only when `ClassName == "PartOfSpeech"`. Callers: `GetAllAffixTemplatesForPOS:271`, `CreateAffixTemplate:412`, `AddSlotToTemplate` template `:484`, slot `:485`, owner `:489`, `Delete:557`, `GetName:606`, `SetName:641`, `GetDescription:673`, `SetDescription:704`, `GetStratum:741`, `SetStratum:776`, `IsDisabled:815`, `SetDisabled:850`, `Duplicate:912`, `GetSyncableProperties:1016`.

Compound rules are unchanged. `CreateCompoundRule` does not use this resolver. Compound `ClassName` values are `MoEndoCompound` and `MoExoCompound`, so the cast does not run on get, set, duplicate, or delete.

Template objects are unchanged. `MoInflAffixTemplate` and `MoInflAffixSlot` skip the cast, so the object added to a side sequence is the one passed in. The cast does fire for a POS argument to `GetAllAffixTemplatesForPOS` and `CreateAffixTemplate`, and for the template owner at `:489`. A bare `ICmObject` or HVO becomes `IPartOfSpeech`, which is what makes `AffixTemplatesOS` and `AllAffixSlots` visible. An already-typed POS is re-wrapped and those members stay available.

Delete is unchanged. `:557` resolves the rule, not the owner. Template delete still loads the owner with `_GetObject` at `:571`.

**`__AllAffixSlotHvos` (`:1123`).** Acceptable, not a P2. The inner import is cached after the first call. `GetClrType` runs once per `AddSlotToTemplate`, then the method reads `pos.AllAffixSlots`. A missing property returns `None`, and `AddSlotToTemplate` raises `FP_ParameterError` before the write. The module already imports `IPartOfSpeech` at `:45`; the inner alias is redundant style. Two points off for that, not a defect.

**`CreateAffixSlot` (`POSOperations.py:871`).** Default `optional=False` remains. `AffixSlotsOC.Add` at `:919` still runs before `Name.set_String` (`:922`) and `Optional` (`:924`).

**Tests.** Offline coverage: omitted optional (`test_issue255_affix_slot.py:215`), ancestor accept (`:274`), descendant reject (`:285`). The live test reads `Optional` from a slot re-fetched by HVO (`test_issue255_affix_slot_live.py:256`) and both sides through `_template_on` (`:35`), which walks the owner’s `AffixTemplatesOS`. Those asserts are not on the object just returned.

No `flexlibs2` string in the delta. Pattern-audit skip is accepted for this correction.
