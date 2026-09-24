# Issue #202 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/202-basic-ipa-skip-tones from origin/main

## RULING (binding)

BasicIPAInfo.xml ships seven tone entries at the head of the catalog with
empty ``<Features/>``. FW treats tones as suprasegmentals (boundary markers /
tone-feature contexts), not as segmental ``IPhPhoneme`` inventory members.
Materializing them as featureless phonemes pollutes ``PhonemeSegmentsOC`` and
makes them eligible for natural-class membership incorrectly.

**Correct behaviour:**

1. ``PhonemeOperations.ImportCatalog`` gains ``skip_tones=True`` (default).
   When True, any parsed segment with ``feature_pairs == []`` is **not**
   created; it increments ``CatalogImportResult.skipped_count`` and appends an
   explanatory warning.
2. ``skip_tones=False`` preserves the legacy path (create featureless phonemes
   for those entries) for callers that explicitly opt in.
3. Detection lives in ``Shared.catalog.basic_ipa_segment_is_suprasegmental_tone``
   (empty feature list == tone row in the stock catalog shape).

**Out of scope:** routing tones to ``IPhBdryMarker`` or mirroring LexImport's
internal loader -- needs a separate design pass if FW's reference importer
does something other than filter.

## Verification plan

- Offline: unit tests on the detector + ``ImportCatalog`` signature; extend
  ``test_basic_ipa.py`` static contract for ``skip_tones`` default.
- Live: optional end-to-end import on ``target_sandbox`` when LCM is available
  (cloud agent: FAIL: unverified).
