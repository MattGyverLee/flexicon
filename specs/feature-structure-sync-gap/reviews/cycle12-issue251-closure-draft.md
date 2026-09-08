# DRAFT -- closing comment for GitHub issue flexicon#251

Status: DRAFT ONLY. Not posted to GitHub. #251 remains OPEN. Posting/
closing requires explicit user authorization, which has not been given.

---

## #251 status: fix delivered, independently gated PASS

**What was asked:** MSAOperations needed to gain feature-struct sync
(GetSyncableProperties / ApplySyncableProperties) across the four C1 MSA
subtypes without adding a fifth, independent copy of the resolver table
already used elsewhere, and without repeating the historic
0-true/2088-false `hasattr` trap against a bare base-interface object.

**What was delivered (T6):** `MSAOperations.py` gained
`GetSyncableProperties` / `ApplySyncableProperties`, ClassName-
discriminated with an explicit cast, routed entirely through the
existing C5 helpers (`_ResolveFeatureStrucOwner`, `_GetFeatureStruc`,
`_ApplyFeatureStruc`, `_ResolveFsByGuid`). No new resolver table was
added. Commits: 04b50407, 941a29eb, 23227b64, f7ab3a69, e356670e,
e022a783. Gated at f062a460.

**The central question -- answered yes:** does ClassName discrimination
hold against a genuine base-interface view, not just a cast handle? Live
tests fetch via `sandbox.Object(hvo)` -- a bare `ICmObject` from the
service locator -- before calling `GetSyncableProperties`, and round-trip
successfully. `hasattr` on that bare object returns `False` for the
feature-struct properties, confirming it is not a decorated wrapper.
Zero `hasattr` gates exist on feature-struct properties anywhere in the
new code (AST-checked, non-vacuous).

**Honest coverage statement:** the direct-cast, mutation-resistant test
added in T6b covers 2 of the 4 C1 MSA rows -- `MoStemMsa`/`MsFeaturesOA`
and `MoInflAffMsa`/`InflFeatsOA`. `MoDerivAffMsa`'s two slots
(`FromMsFeaturesOA` via `slot="From"`, `ToMsFeaturesOA` via `slot="To"`)
are exercised through the resolver but NOT by this direct-cast pattern,
and `MoUnclassifiedAffixMsa` has no feature-struct member to read at
all. Every mutation run against this pattern in the T6b gate was
KILLED; nothing was left NOT-KILLED. One previously un-run "reasoned
kill" claim was independently mutation-run by the gate this cycle and
killed cleanly -- logged as an informational process note, not a
coverage gap.

**Why there's a T6b at all:** T6's own follow-up gate found the direct
cast's advertised coverage was decorative rather than falsifiable; the
claim was corrected and real mutation-resistant coverage was added in
its place. Full findings:
`specs/feature-structure-sync-gap/reviews/cycle12-verification-T6b-gate.md`
(verdict: CHECKPOINT 3b: PASS).

---

This comment is a prepared draft. #251 stays open until the user
authorizes posting/closing it.
