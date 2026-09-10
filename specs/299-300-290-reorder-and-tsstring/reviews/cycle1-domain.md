# Domain Expert Review — Issue #299 `_GetSequence` design question

**Date:** 2026-09-10
**Score:** N/A (design ruling, not a scored implementation)
**Status:** RULING — implement as specified below

**Evidence base:** Read `TextOperations.py`, `ParagraphOperations.py`, `SegmentOperations.py` in full; `BaseOperations.py` (Sort/MoveUp/MoveDown/MoveToIndex at 693/799/896/982, `_GetSequence` contract at 1598, `_GetObject` at 1641, `_GetTypedOwner` at 1677); `_GetSequence` overrides in `EnvironmentOperations.py`, `InflectionFeatureOperations.py`, `AllomorphOperations.py`, `possibility_item_base.py`; confirmed `LexEntryOperations.py` has no `_GetSequence` override and no `__ResolveObject`; confirmed `project.lp.Texts` is a renamed `TextsOC` (owning **collection**, no order/`.MoveTo`) per `TextOperations.Create()`'s own comment (line 170-172); GitHub issue #299 fetched via WebFetch.

---

## Q1: Does the issue's fix correctly make TextOperations and ParagraphOperations identical?

**RULING: No.** This is a bug in the issue's own proposed fix. `TextOperations` must not implement `_GetSequence` at all.

`project.lp.Texts` (the sequence `TextOperations.Create()` actually operates on — see its comment "`TextsOC` ... renamed ... to `Texts`") is an owning **collection**, not an owning **sequence**. `Sort()`/`MoveUp()`/`MoveDown()`/`MoveToIndex()` in `BaseOperations` require `sequence[i]` indexer and `.MoveTo()`, neither of which an OC-family type supports. `TextOperations`'s own entity (`IText`, per its `Create`/`GetAll`) therefore has **no** orderable child sequence of its own kind to reorder — exactly the situation `LexEntryOperations.py` already exists to model: it defines no `_GetSequence` override at all, and top-level unordered entries correctly get `BaseOperations`'s built-in `NotImplementedError` when someone tries to `Sort()`/`MoveUp()` them. `ParagraphOperations`, by contrast, genuinely owns paragraph-reordering: its `Create(text_or_hvo, ...)` and `GetAll(text_or_hvo)` operate on paragraphs keyed by the owning text, exactly the shape `_GetSequence` needs (parent owns a sequence of the entities this class manages). Applying the issue's literal fix to `TextOperations` duplicates `ParagraphOperations`'s responsibility in a class whose own docstring ("for text paragraphs") already reveals this was the original mistake, not a coincidence.

**Code:** Delete the `_GetSequence` override in `TextOperations.py` (lines 66-68) entirely. Do not replace it with anything — `BaseOperations._GetSequence`'s default `NotImplementedError("TextOperations must implement _GetSequence() ...")` becomes the correct, honest behavior for `project.Texts.Sort()`/`MoveUp()`/etc.

## Q2: What parent type must each `_GetSequence` accept?

**RULING: Exactly one type per class, matching that class's own `Create()`/`GetAll()` contract — fail loudly (bare `AttributeError`) on anything else. No normalization, no `parent_is_text=`-style flag.**

House convention, confirmed by three independent examples: `EnvironmentOperations._GetSequence` (`parent.EnvironmentsOS`, parent = `IPhPhonData`, one hop) explicitly documents that its predecessor bug was copy-pasting a *different* class's legitimately-multi-hop chain (`InflectionFeatureOperations._GetSequence` → `parent.FeaturesOA.PossibilitiesOS`, parent = whatever type that class's own `Create`/`GetAll` require) onto a parent type that never had that intervening object. The pattern is: the chain is fixed per-class to match that class's already-established parent-type contract, never conditional on the argument's runtime shape. None of `TextOperations`/`ParagraphOperations`/`SegmentOperations` route through a shared `__ResolveObject`; each has its own private resolver (`__GetTextObject`, `__GetParagraphObject`, `__GetSegmentObject`) used only inside that class's own CRUD methods — but critically, `BaseOperations.Sort/MoveUp/MoveDown/MoveToIndex` call the *generic* `self._GetObject(parent_or_hvo)` (int-or-passthrough, no casting) before invoking `_GetSequence`, so `_GetSequence` is the only place doing type-specific access and must match whatever type the sibling CRUD methods already promise callers.

- `ParagraphOperations._GetSequence`: parent = **`IText`** (same as `Create(text_or_hvo,...)`, `GetAll(text_or_hvo)`, `InsertAt(text_or_hvo,...)`, all of which resolve via `__GetTextObject`). Although `IStText` owns `ParagraphsOS` one hop closer, no other method in this class accepts `IStText`; adding it only here would be an inconsistent one-off, not a fix.
- `SegmentOperations._GetSequence`: parent = **`IStTxtPara`** (same as `GetAll(paragraph_or_hvo)`, `AppendSentence(paragraph_or_hvo,...)`, resolved via `__GetParagraphObject`).

## Q3: Segments or Analyses?

**RULING: SEGMENTS. The current docstring ("segment analyses (reference sequence)") is wrong and must be corrected.**

`SegmentOperations.GetAll(paragraph_or_hvo)` yields `ISegment` objects; `AppendSentence`/`Delete`/`SplitSegment`/`MergeSegments` all create/manage `ISegment` objects in `SegmentsOS`. That is this class's entity, matching the house convention (class X manages entity X; `_GetSequence` reorders the sequence-of-X owned by parent). `AnalysesRS` reordering is a **separate, already-solved** problem: `SetAnalysis`, `ReplaceAnalysis`, `InsertAnalysis`, `AppendAnalysis`, `RemoveAnalysis` (lines 740-938, added for issue #215) already give `AnalysesRS` its own dedicated, purpose-built API. No second method is warranted — repurposing the generic `Sort`/`MoveUp`/`MoveToIndex` for `AnalysesRS` would duplicate and potentially conflict with that existing, more carefully-reasoned API for a reference sequence of polymorphic analysis tokens.

**Code:** `return parent.SegmentsOS`, and rewrite the docstring at `SegmentOperations.py:110` from "segment analyses (reference sequence)" to "a paragraph's segments (parent is IStTxtPara)".

## Q4: CLAUDE.md rule #5 conflict

**RULING: A `parent_is_text=`/similar kwarg would violate rule #5 and must not be added.** Rule #5 forbids a flag whose `False`/default branch preserves broken or inconsistent behavior while making correctness the caller's opt-in problem. Here the fix is unconditional per class (Q2's single fixed chain), so no flag is needed or permitted. The only place a "does this parent look like an IText or an IStText" branch might tempt an implementer is exactly the case rule #5's own worked example targets — do not add it; instead enforce the single documented parent type and let a wrong-type call fail with a bare `AttributeError`, which is itself informative (mirrors `EnvironmentOperations`'s and `InflectionFeatureOperations`'s existing precedent of zero caller-facing normalization knobs).

---

## Exact code for the implementer

```python
# TextOperations.py: DELETE lines 66-68 (the _GetSequence override).
# No replacement -- BaseOperations._GetSequence's own NotImplementedError
# is the correct behavior (Texts is an unordered owning collection; see
# LexEntryOperations.py for the existing precedent of no override).

# ParagraphOperations.py:59-61
def _GetSequence(self, parent):
    """Specify which sequence to reorder: a text's paragraphs.

    ``parent`` must be an IText -- the same type Create()/GetAll()/
    InsertAt() already require via __GetTextObject(). IStText is not
    accepted here even though it owns ParagraphsOS directly, because no
    sibling method on this class accepts it either.
    """
    return parent.ContentsOA.ParagraphsOS

# SegmentOperations.py:109-111
def _GetSequence(self, parent):
    """Specify which sequence to reorder: a paragraph's segments.

    ``parent`` must be an IStTxtPara -- the same type GetAll()/
    AppendSentence() already require via __GetParagraphObject().
    AnalysesRS has its own dedicated API (SetAnalysis/ReplaceAnalysis/
    InsertAnalysis/AppendAnalysis/RemoveAnalysis, issue #215) and must
    not be targeted by Sort/MoveUp/MoveDown/MoveToIndex.
    """
    return parent.SegmentsOS
```

---

## CORRECTION (cycle 5, 2026-09-10)

Q2's characterization of `InflectionFeatureOperations._GetSequence` →
`parent.FeaturesOA.PossibilitiesOS` as a "legitimately-multi-hop chain" is
**WRONG**. The freshly-regenerated LCM contract baseline
(`tests/contract/snapshots/liblcm_baseline.json`, liblcm 11.0.0.0,
generated 2026-09-08T15:18:18Z) confirms `IFsFeatStruc` — the type
`FeaturesOA` resolves to — has **no `PossibilitiesOS`** at all. Its real
child collection is `FeatureSpecsOC`, an unordered `ObjectCollection`. Full
adjudication and the reproduction command are recorded in
`specs/299-300-290-reorder-and-tsstring/evidence/cycle4-snapshot-adjudication.md`.

Three points, stated explicitly:

**(a) This does NOT change the Q2 ruling.** The ruling — exactly one
parent type per class, matching that class's own `Create()`/`GetAll()`
contract, fail loudly on anything else, no normalization flag — rests
independently on `EnvironmentOperations` (the one-hop, correctly-typed
sibling), the `LexEntryOperations` no-override precedent, and CLAUDE.md
rule #5. `InflectionFeatureOperations` was cited only as an illustrative
contrast case for "a chain some other class's parent type legitimately
needs"; it was never load-bearing for the ruling itself.

**(b) This does NOT affect the shipped code.** `ParagraphOperations`'s own
chain, `parent.ContentsOA.ParagraphsOS`, is separately and independently
snapshot-confirmed: `IText.ContentsOA` exists and `IText` has no
`ParagraphsOS` of its own, while `IStText.ParagraphsOS` (the collection one
hop past `ContentsOA`) is confirmed present. Nothing in this correction
touches `TextOperations`, `ParagraphOperations`, or `SegmentOperations`.

**(c) The finding STRENGTHENS the ruling.** `InflectionFeatureOperations`'s
own `_GetSequence` is itself now a confirmed cycle4 HIGH sibling finding
(`reviews/cycle4-sweep-getsequence.md`, `InflectionFeatureOperations.py:145`)
— exactly the copy-pasted, unverified multi-hop chain that this Q2 ruling's
"fail loudly, match your own class's contract, no cross-class copying"
rule exists to prevent. That a chain cited here as the illustrative
"legitimate" contrast case turned out on live reflection to be broken is
direct evidence for, not against, treating multi-hop `_GetSequence` chains
as high-risk and requiring per-class verification rather than reuse.
