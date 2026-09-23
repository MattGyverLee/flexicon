<!-- Provenance: main session wrote this file because lex-domain cannot write files. Content is the lex-domain hand-back verbatim. -->

**Verdict: fail.** Two mismatches on `0672b0b`.

**1. `optional=True` does not match the FLEx default.** A new affix slot is obligatory. `MakeInflAffixSlotChooserCommand` sets `Optional` from the chooser flag, and `SimpleListChooser` reads the XML `optional` attribute with default `false`. The template menu is two links, "Add an obligatory slot" (`false`) and "Add an optional slot" (`true`). An unset LCM Boolean is false, and the template table draws parentheses only when `Optional` is true. `CreateAffixSlot(pos, name)` therefore stores an optional slot where FLEx would store an obligatory one. The default should be `optional=False`.

**2. Same-owner HVO is the wrong rule.** `AddSlotToTemplate` requires `slot.Owner.Hvo == template.Owner.Hvo`. Slots live on a category so templates can share them. `AllAffixSlots` is that category's `AffixSlots` plus the owner's `AllAffixSlots`, walking up (`vAllAffixSlots` in `MasterFieldWorksModel`). A subcategory template may use a slot owned by a parent or higher category, and the chooser can create that slot on the top category (`GetHvoOfHighestPOS`). A parent template uses only its own slots and ancestor-owned slots. Equality rejects the legal ancestor case along with the illegal descendant case.

**3. Sides and index 0 match storage.** `prefix`, `suffix`, `proclitic`, and `enclitic` are the four reference sequences. Index `0` is the first stored element (`Insert`); `Count` appends. The LTR template table draws `PrefixSlots` and `SuffixSlots` in stored order, prefixes left of STEM and suffixes right, so index 0 is the left end of that side: outermost prefix, stem-adjacent suffix.

**4. The split is right.** `CreateAffixSlot` writes `AffixSlotsOC`, the analysis-WS name, and `Optional`. FLEx's create command does the same. Placement stays on `AddSlotToTemplate`. `IMoInflAffMsa.SlotsRC` (#258) stays a separate write.
