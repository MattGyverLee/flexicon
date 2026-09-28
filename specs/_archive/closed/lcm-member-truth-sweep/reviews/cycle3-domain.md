# Domain Expert Ruling: #283 Duplicate/Delete reference semantics (C7/C8)

**Campaign:** lcm-member-truth-sweep, cycle 3 (checkpoint 3)
**Issue:** #283
**Date:** 2026-09-18
**Status:** RULING DELIVERED — Q-A PASS, Q-B PASS (with documentation gap), Q-C PASS

> Provenance note: produced by the `lex-domain` subagent, which has no
> Write/Edit tools in its agent definition. Persisted to this path verbatim
> by the main session on its behalf. Content is unmodified.

Domain Expert Review — cycle 3, EnvironmentOperations Duplicate/Delete (C7/C8)

Q-A. PASS. IPhEnvironment.LeftContextRA/RightContextRA are Reference Atomic — LCM's own semantics say the environment does not own the context, IPhPhonData.ContextsOS does. A "duplicate environment" command that tried to deep-clone the context would be inventing ownership the model doesn't have, and would silently orphan the clone from ContextsOS bookkeeping. Pointing the duplicate at the same IPhPhonContext is the only semantics consistent with FLEx's own object model — FLEx's UI treats an environment's context pattern as a shared, referenced pattern (the same phonological rule/context can legitimately be reused across environments), so a copy sharing the context matches how a user would read "Left Context: [existing pattern]" showing up unchanged, just re-anchored to a new environment name/string-rep. The stated consequence — editing the shared context afterwards changes both environments — is correct and acceptable: it mirrors editing a shared list item or shared phoneme referenced from two rules, a pattern FLEx users already encounter (e.g. two rules pointing at the same natural class). If independent contexts were wanted, the user would need an explicit "clone context" action FLEx does not offer today. C7 stands as written; no flip warranted.

Q-B. PASS, with a documentation gap. EnvironmentOperations.Delete (`:195-233`) only does `phon_data.EnvironmentsOS.Remove(env)` — it never touches `ContextsOS`, so deleting the duplicate cannot cascade-delete a context still referenced by the source, and there are no orphaning side effects on that path. The risk is real but not realized in this diff: nothing in Delete's diff or history adds ContextsOS cleanup. One gap: no live regression test actually deletes the duplicate afterward and re-reads the source's LeftContextRA to confirm survival — `test_2d_...` cleans up manually via `ContextsOS.Remove` rather than exercising `envs.Delete(duplicate)` against a still-referenced-by-source context. Recommend a follow-up test (not blocking): delete duplicate, re-fetch source by HVO, assert `source.LeftContextRA` still resolves.

Q-C. PASS. The kept assertion (`:327-337`) is honestly re-justified — same conclusion (`None`), now for the true reason (never-set context) rather than the old wrong-property-name bug, and the docstring explains the pivot. The new `test_left_context_returns_seeded_context_by_reference` (`:340-419`) seeds a real `IPhSimpleContextSeg` into `ContextsOS`, assigns it to `LeftContextRA`, re-reads by fresh HVO lookup, and asserts non-None plus HVO equality — this is a genuine anchor that goes red against the unfixed (`LeftContextOA`) code. Not a tautology.
