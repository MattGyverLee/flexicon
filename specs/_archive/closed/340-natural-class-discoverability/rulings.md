# Issue #340 -- lex-lead ruling

**Date:** 2026-09-23  
**Issue:** #340 (P2) -- AddPhoneme on feature-based natural class with no pre-check

## RULING

1. **Canonical kind API** -- `GetType()` (landed with the feature-based natural-class
   work) is the canonical string discriminator (`"segments"` / `"features"`). Do not
   add a parallel `GetKind()` name.

2. **Boolean discoverability** -- Add `IsFeatureBased()` and `IsSegmentBased()` as thin
   wrappers over `GetType()` so callers can branch before `AddPhoneme`/`RemovePhoneme`
   without catching `FP_ParameterError`. This closes the log-scan gap (#340) without
   changing successful write semantics.

3. **AddPhoneme / RemovePhoneme** -- Route the segment-vs-feature guard through
   `IsSegmentBased()` (same truth as the old `hasattr(nc, "SegmentsRC")` gate for
   normal LCM objects). Upgrade the error message to name `IsFeatureBased()` /
   `GetType()` explicitly.

4. **Documentation** -- Extend `AddPhoneme` / `RemovePhoneme` docstrings with a
   pre-check example using `IsSegmentBased()`.

5. **Pattern audit** -- No sibling sweep: `GetPhonemes` already returns `[]` for
   feature-based classes (non-throwing read path). Other mutators (`SetFeatures`) already
   document feature-only use.

6. **Live verification** -- Write-path touch on `AddPhoneme`/`RemovePhoneme` guard only;
   live LCM run required on Windows FieldWorks. Cloud agent: **FAIL: unverified** (no
   SIL.LCModel on Linux pod).
