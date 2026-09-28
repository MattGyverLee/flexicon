# Cycle 1 - Original Author Review: guid-preserving Create() for Agent/Reversal ops

Score: 8/10 | Status: CONCERNS (design questions, not code defects)

Note: this report was produced by lex-author, which has no Write tool; the
main session persisted it verbatim to this path.

## 1. Proposed signatures

- `AgentOperations.Create(self, name, wsHandle=None, guid=None)` -- identical
  shape to `WordformOperations.Create`. `guid` appended last,
  positional-with-default, not keyword-only. No BC break.
- `ReversalIndexOperations.Create(self, name, writing_system, guid=None)` --
  `writing_system` stays required/positional (it has no default today, unlike
  `wsHandle` elsewhere); `guid` appended after it, default `None`. No BC break.
- `ReversalIndexEntryOperations.Create(self, index_or_hvo, form, sense=None,
  wsHandle=None, guid=None)` -- `guid` appended after the existing `wsHandle`
  default, mirroring how `TextOperations.Create` appended `guid` (then
  `contents_guid`) after its existing optional params. No BC break.

None should be keyword-only -- every one of the 8 existing callers
(`WordformOperations`, `TextOperations`, `ParagraphOperations`,
`WfiGlossOperations`, etc.) leaves `guid` as an ordinary trailing default
param, never `*`-gated. Deviating here would be an inconsistency, not an
improvement.

## 2. ReversalIndexOperations duplicate-WS behavior with guid=

Still raise `FP_ParameterError`. The WS-uniqueness check happens *before*
`_CreateWithGuid` is ever called -- it is a business-rule validation (decision
D5's validate-then-mutate), unrelated to `_CreateWithGuid`'s own fallback,
which only concerns a **GUID** already existing in the project, not a duplicate
writing system. The precedent already documents the right escape hatch:
"callers that must not silently lose identity should check for an existing
object first (Find/Get* helpers)." Reproducing/round-tripping code should call
`FindByWritingSystem` first and skip creation if found -- that is the caller's
job, not a new implicit upsert-and-return-existing behavior invented for this
feature. No precedent anywhere in the 8 callers does silent-return-existing;
do not add it now.

## 3. ReversalIndexEntry: form-identity vs guid-identity

Recommend: accept it, but keep `guid` a *transport-only* field, not a second
identity key. Critically, `ReversalIndexEntryOperations.Create` **already has
no dedup-by-form logic** -- like `WordformOperations.Create` ("Does not check
if wordform already exists -- use Find() or Exists() first"), it always creates
unconditionally; the docstring/callers dedup by form themselves before calling.
So adding `guid=` changes nothing about identity resolution inside `Create()`
-- it is a pure passthrough exactly like the Wordform case. Do not add any
guid-based lookup/merge logic to `Create()` itself; that would be new
complexity nobody asked for and contradicts "simple is better than complex."

## 4. CmAgent: is guid= meaningful?

Weaker case than the other two, but not zero. `AgentOperations.Duplicate()`
currently documents "a new copy with a new GUID" as the intended behavior --
i.e. today identity is fully derived/discardable, and nothing in this file
currently cares about GUID stability. That said, the repo has a
`flexlibs2/sync/` engine, and cross-project reproduction of `ICmAgent`
(preserving which agent evaluated an analysis) is a plausible
round-trip/merge scenario, same rationale as the 8 existing callers.

Recommendation: add `guid=None` to `AgentOperations.Create` for consistency
with the established pattern -- it is free (defaults preserve old behavior) and
matches "unify operations across types" from the API philosophy -- but do not
touch `Duplicate()`'s semantics; that method's "always a new GUID" contract is
a different, intentional, and correct decision that should not be revisited
here.

## 5. Silent fallback-to-new-identity

Keep it, unchanged, for all three. This is the one part of the design that must
not fragment: the whole feature (#236) is entitled "consistent with how
flexicon already does this," and the fallback-with-warning is the load-bearing
part of that consistency contract. Making these three call sites special-cased
to raise loudly would produce three different Create() failure contracts across
11 total callers for no stated reason, contradicting both "backward
compatibility is sacred" and "explicit over implicit" (callers who need loud
failure already have the documented Find-first pattern).

## Overall

Would I have done it this way? Yes.

Recommendation: APPROVE the three signatures as specified above, with the
guidance in points 2-5 folded into each docstring (especially: guid does NOT
change existing-object validation, and Create() still performs zero dedup by
design).

Reviewed By: Original Author Agent (lex-author), cycle 1

## Files read (read-only)

- `flexicon\code\BaseOperations.py` (`_CreateWithGuid`, ~1884-1962)
- `flexicon\code\TextsWords\WordformOperations.py` (Create, ~129-179)
- `flexicon\code\TextsWords\TextOperations.py` (Create, ~109-182)
- `flexicon\code\TextsWords\ParagraphOperations.py` (Create, ~127-168)
- `flexicon\code\TextsWords\WfiGlossOperations.py` (Create, ~187-209)
- `flexicon\code\Lists\AgentOperations.py` (Create/Duplicate, ~114-232)
- `flexicon\code\Reversal\ReversalIndexOperations.py` (Create, ~110-177)
- `flexicon\code\Reversal\ReversalIndexEntryOperations.py` (Create, ~130-200)
