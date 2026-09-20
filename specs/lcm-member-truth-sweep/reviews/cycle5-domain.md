# Domain Expert Ruling: #259 SetInflectionClass / Q2 (binding C11)

**Campaign:** lcm-member-truth-sweep, cycle 5 (checkpoint 4)
**Issue:** #259
**Date:** 2026-09-18
**Status:** RULING DELIVERED -- `DECISION: warn`. Domain-rulable; no escalation needed.

> Provenance note: produced by the `lex-domain` subagent, which has no
> Write/Edit tools in its agent definition. Persisted to this path verbatim
> by the main session on its behalf. Content is unmodified.

RULING: #259 SetInflectionClass (checkpoint 4, Q2)

**A. FLEx-native semantics: YES, the fan-out is correct FLEx behaviour.**
`MoStemMsa` is owned by the `ILexEntry` (`MorphoSyntaxAnalysesOC`) and is
what a `LexSense.MorphoSyntaxAnalysisRA` points to as "Grammatical Info."
`WfiMorphBundle.MsaRA` is a pure reference into that *same* MSA object,
set precisely so an interlinear analysis stays tied to the lexicon entry's
grammatical description. In the FLEx UI, editing Inflection Class on a
sense's Grammatical Info Details is a lexicon-level edit to the MSA, and
every analysis referencing it reads the new value immediately -- that is
the whole point of sharing by reference rather than by copy: one
grammatical description, many usages, kept in sync. So the 267x fan-out is
correct domain behaviour wearing a misleading Python signature. The defect
is `SetInflectionClass(bundle, infl_class)` implying per-bundle scope when
the true grain is per-lexeme/per-MSA.

**B. DECISION: warn.**

1. Fix the crash: mirror `GetInflectionClass`'s navigation --
   `bundle.MsaRA` -> null/ClassName check -> narrow to `IMoStemMsa` via
   `cast_to_concrete` -> set `.InflectionClassRA`. Do NOT write
   `bundle.InflClassRA`.
2. If `MsaRA` is null (94 bundles) or not a `MoStemMsa` (1144 bundles:
   1109 `MoInflAffMsa`, 32 `MoDerivAffMsa`, 3 `MoUnclassifiedAffixMsa`),
   raise `FP_ParameterError` -- there is no writable target, and silently
   no-op'ing would violate CLAUDE.md rule #5 (correctness must be
   unconditional, not opt-in). Message: `"Cannot set inflection class:
   bundle's MSA is <null | ClassName=X>; only MoStemMsa carries
   InflectionClassRA."` For `MoDerivAffMsa`, note in the message/docstring
   that it has `From/ToInflectionClassRA` instead -- a different pair of
   properties this method deliberately does not touch (matches
   `get_inflection_class_from_msa`'s existing note) -- without implying a
   new setter must be built.
3. The warning uses the **print-style precedent from `MergeObject` /
   `validate_merge_compatibility`**, not `warnings.warn` -- that is the
   established in-repo idiom for "legitimate but consequential" writes.
   Text: something like `"NOTE: inflection class is stored on the shared
   MSA, not the bundle; this change will be visible to every other morph
   bundle and sense referencing the same MSA."`
4. **Do NOT report an exact fan-out count per call.** `RemoveOrphaned`'s
   own docstring frames its one-pass `AllInstances()` scan as the cost
   model for a *project-wide bulk operation*; `SetInflectionClass` is a
   per-object setter that can legitimately run in a loop over hundreds of
   bundles, turning an O(n) scan into O(n^2) (~1.3M comparisons for a full
   694-bundle sweep). Keep the warning qualitative only. If a caller wants
   the precise count, they can compute it themselves (or a future
   opt-in/bulk helper could return it) -- that is not this fix's job.

Accept (silent) is out per verification's own call. Redirect is not
viable: there is no MSA-level inflection-class setter, and creating one is
new API surface, which C13 places out of scope for this campaign. Refuse
would block a write that Part A establishes is legitimate FLEx behaviour,
permanently, with no alternative path -- worse than warning.

**C. Remit check: I can rule this; no escalation needed.** This resolves
by combining settled FLEx domain semantics (Part A, which is squarely
domain expertise) with an already-established in-repo convention (the
`MergeObject` warn idiom, CLAUDE.md rule #6) and does not require new
public API surface, so it doesn't trip C13's human-filing gate. Nothing
here is a values/business tradeoff needing the user's judgment.

Files read: flexicon/code/TextsWords/WfiMorphBundleOperations.py:1290-1370,
flexicon/code/lcm_casting.py:730-822, flexicon/code/Lexicon/MSAOperations.py
(RemoveOrphaned ~65-819), specs/lcm-member-truth-sweep/spec.md:180-280,
flexicon/code/exceptions.py (FP_ParameterError confirmed present).
