# Cycle 4 — Domain Expert Review (getall-contract-flexicon)

> Written by main session on behalf of lex-domain (read-only, no Write tool). Verbatim.

**Verdict: PASS overall (1 recommendation on item 3, not a blocker)**

**1. Container-type taxonomy (loop/len/index/re-iterate) — PASS.** The right behavioral contract from a FLEx-user perspective: script authors from FLExTools/IronPython routinely write `len(entries)` for progress and `entries[0]` for spot-checks — patterns that silently break on a raw C# `IEnumerable` or one-shot generator. Unifying `EnumerableWrapper`/`list`/`SmartCollection` under one guarantee correctly reflects that users care only about "can I treat this like a normal Python sequence."

**2. SmartCollection docstrings naming the wrapper class (Allomorph, PhonologicalRule, CompoundRule, AffixTemplate) — PASS.** Correct domain-facing choice. Users interact with the Python wrapper objects (`.filter()`/`.by_type()`, Pythonic attributes), not the raw LCM interface. Naming the LCM interface would mislead users into expecting `.hvo`/`.ClassName` C# access.

**3. Base `GetAll` annotation `-> Iterator[Any]` — RECOMMEND: defer to .pyi work, but flag now.** The misleading annotation lives ONLY in `BaseOperations.pyi` (blanket `*args/**kwargs -> Iterator[Any]` on essentially every method, not GetAll-specific) — there is NO such annotation in runtime `BaseOperations.py` (no real base `GetAll`; each subclass defines its own). Since the stubs are wrong on both parameter signatures AND return types, a partial return-type-only fix would leave stubs inaccurate and create false trust. Defer to the dedicated `.pyi` reconciliation cycle — but that cycle must not be indefinitely delayed: IDE-autocomplete users today get worse guidance than the docstrings now provide. Technical debt, not mere housekeeping.

**4. GetSegmentsWithType NotImplementedError vs silent None — PASS.** Correct: segment-level `FreeTranslation`/`LiteralTranslation` have no typed link to a translation-type possibility in LCM (unlike text-level). Returning None/empty would falsely imply "no segments use this type" when the real answer is "impossible at this level." MediaOperations folder-walk-vs-repository caveat is accurate: repository enumeration is broader than walking `MediaOC`/`PicturesOC`, correctly including orphaned/pronunciation/external-link `ICmFile`.

**Summary:** Container taxonomy and wrapper-naming are domain-correct; GetSegmentsWithType/MediaOperations semantics check out against real LCM. Only open item is the `.pyi` `Iterator[Any]` annotation — confirmed stub-only (no runtime mismatch), reasonably deferred, but should not be indefinitely delayed.
