# Original Author Review -- issues #318-321 (nonexistent-member mutations)

## RECOMMENDATION

**Q1 -- Narrow the inner except?** YES. Catch only the specific LCM/COM
condition that legitimately means "this item can't be removed right now"
(if none exists, catch nothing and let the whole block raise);
`AttributeError`/`TypeError` must propagate. Precedent: `FLExInit.py:91-98`
(#249) narrows a blanket `except Exception` to `except
System.InvalidOperationException as e: if "already been initialized" not
in e.Message: raise` -- a programmer/environment error is never allowed to
hide behind a message check for one known-benign condition. `OwningList`
raising `AttributeError` is exactly the "not that exact benign case" class
#249 says must propagate.

**Q2 -- Raise when duplicates were found but none removed?** YES, and also
raise (don't silently return 0) when duplicates were found and the try
block around the whole detection dies. "0 removed because there were 0
duplicates" and "0 removed because every removal attempt failed" are
observably different states (`len(sig_map[sig]) > 1` was true) and must not
collapse to the same silent return. Precedent: #291 turned exactly this
collapse -- a real failure being indistinguishable from a real pass --
into the defect; the fix's stated principle is that the thing under test
(here: "duplicates were removed") must be able to fail loud when it didn't
happen.

**Q3 -- Return removed_count / a result object instead of None?** NO, not
as the primary fix. The only caller of `__DeduplicatePronunciationsInEntry`
/ `__DeduplicateAllomorphsInEntry` / `__DeduplicateExamplesInSense` is
`MergeObject()` itself (`LexEntryOperations.py:3010-3014`,
`LexSenseOperations.py:3775`), and `MergeObject()`'s own documented
contract returns nothing (see its docstring example at
`LexEntryOperations.py:2961-2974`: no captured return value). Plumbing a
count out of three private `__`-prefixed helpers into a public method that
has never returned one is a signature change nobody asked for and no
caller can act on. If per-item counts are wanted later, log them (they
already are, at `logger.info` on success) -- don't invent a return-value
contract to carry information that raising already communicates.

**Q4 -- Is `logger.warning` the right level?** NO. "The operation I
advertised did not happen" is an error, and for the genuinely-unexpected
member-name case it should never reach logging at all -- it should raise
per Q1. Precedent: the 4.8.0 changelog's own stated theme is "every
remaining legitimate drop is now unconditionally logged rather than
silent" paired with converting silent no-ops into raises wherever the
no-op was not itself legitimate (`LexiconSetComplexFormType` /
`LexiconGetComplexFormType`, #280). `logger.warning` is acceptable only
for the narrowed, genuinely-benign per-item case surviving from Q1 (e.g. an
LCM-side "can't delete, still referenced" condition) -- never for the
outer catch-all that currently exists at
`LexEntryOperations.py:3146`/`3217` and
`LexSenseOperations.py:3893`.

**Q5 -- Does raising break compatibility, and is that allowed here?** YES,
raising is allowed, and it should ship as a **minor** version bump, not
`v5.0.0`. Direct precedent, verbatim from `CHANGELOG.md` 4.8.0 preamble:
"Neither removes a signature or changes the meaning of a default a caller
passes explicitly, so this ships as a minor bump per the precedent set by
4.4.0, 4.6.0 and 4.7.0." The `LexiconSetComplexFormType`/`Get` entry is the
closest match: "a call that previously failed silently now either succeeds
or raises." This case is one tier louder because dedup runs inside
`MergeObject(auto_deduplicate=True)`, which is `True` by default -- so the
new exception can surface on a call site that never mentioned
deduplication. That is acceptable and matches #317's framing (silent data
corruption is the worse failure mode) but must be called out explicitly in
the CHANGELOG as `BREAKING (behavioural)` exactly like the 4.8.0 entries,
including a one-line workaround (`auto_deduplicate=False` to opt out while
migrating).

## Exception shape

Add to `exceptions.py`, alongside `FP_TransactionError`:

```python
class FP_DeduplicationError(FP_RuntimeError):
    """Raised when duplicate items were detected but could not all be removed."""
    def __init__(self, item_kind, entry_hvo, found, removed, cause=None):
        message = (
            f"Deduplication of {item_kind} in entry (HVO: {entry_hvo}) found "
            f"{found} duplicate(s) but removed only {removed}"
            + (f": {cause}" if cause else ".")
        )
        super().__init__(message)
```

Raised from each of the three helpers in place of the current
`logger.warning` catch-alls, once the inner except is narrowed per Q1.

---
**Reviewed By:** Original Author Agent
