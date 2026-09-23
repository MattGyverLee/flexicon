<!-- Provenance: main session wrote this file because lex-domain cannot write files. Content is the lex-domain hand-back verbatim. -->

**Verdict: pass.** Both cycle-2 failures are corrected on `6abff1c`. Sides, index 0, and the create-then-place split are unchanged.

**1. Obligatory default.** `CreateAffixSlot(pos, name, optional=False)` writes `slot.Optional` after `AffixSlotsOC.Add` on the POS it is given. `__ResolveObject` only casts to `IPartOfSpeech`. It does not climb to the highest POS. Omitting `optional` stores `False` (obligatory). `optional=True` is still assigned through.

**2. AllAffixSlots membership.** `AddSlotToTemplate` no longer compares owner HVOs. It accepts the slot only when its HVO is in the template owner's `AllAffixSlots` (`__AllAffixSlotHvos`). That property is the category's own slots plus ancestor slots. A descendant-owned slot is absent, so it is rejected and the side is not written. A missing owner, or an owner whose `ClassName` is not `PartOfSpeech`, leaves the visible set unset and raises `FP_ParameterError` before `Add` or `Insert`. There is no same-owner fallback if `AllAffixSlots` is absent.

**Claimed read-backs** in `specs/255-affix-slot/evidence/live-cycle3.md` (programmer claim; this review did not open a project): HVO 10444 `Optional` false; child prefix contains 10444; parent `AllAffixSlots` is 10444 only; adding 10446 raises and the parent prefix stays empty. Those outcomes match the two rules above.
