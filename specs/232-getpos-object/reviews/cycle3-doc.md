# Doc Agent Note - cycle 3

**Date:** 2026-08-13
**Scope:** CHANGELOG.md only

Replaced the `[Unreleased]` placeholder line ("_Nothing yet. ..._") with a
`### Fixed` entry for issue #232, matching the bold-lead-in-plus-prose style
of the `[4.3.1]` entry immediately below it.

Entry documents: `GetPartOfSpeechObject()` previously read
`PartOfSpeechRA` off the base `IMoMorphSynAnalysis` interface (undeclared
there) and always returned `None`; it now delegates to `get_pos_from_msa()`,
which casts to the concrete MSA subtype first, fixing all four POS-bearing
subtypes (MoStemMsa, MoInflAffMsa, MoDerivAffMsa, MoUnclassifiedAffixMsa).
Noted the `MoDerivAffMsa` output-category behavior (matches `SetPartOfSpeech`,
#87 precedent), the unchanged no-MSA-returns-`None` contract, the new
warning log for unrecognized `ClassName`, and that `GetPartOfSpeech()`
(string getter via `InterlinearAbbr`) is unaffected.

No other files touched. No commit made.
